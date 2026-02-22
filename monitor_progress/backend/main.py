from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from bson.objectid import ObjectId

from database import engine, get_mysql_db, get_mongo_db, articles_collection

app = FastAPI(title="微信公众号数据监控系统")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class StatsResponse(BaseModel):
    total_feeds: int
    total_articles: int
    today_feeds: int
    today_articles: int
    today_mongo_articles_count: int
    today_preprocessed: int
    today_preprocessed_rate: float
    today_full_content: int
    today_full_content_rate: float
    high_score_articles: int
    today_llm_summary: int
    today_llm_summary_rate: float


@app.get("/api/stats", response_model=StatsResponse)
def get_stats(date: Optional[str] = Query(None, description="日期格式: YYYY-MM-DD")):
    if date:
        target_date = datetime.strptime(date, "%Y-%m-%d")
    else:
        target_date = datetime.now()

    with engine.connect() as conn:
        result = (
            conn.execute(
                text("SELECT * FROM daily_stats WHERE stat_date = :stat_date"),
                {"stat_date": target_date.date()},
            )
            .mappings()
            .first()
        )

        if result:
            total_feeds = result["total_feeds"]
            total_articles = result["total_articles"]
            today_feeds = result["today_feeds"]
            today_articles = result["today_articles"]
            today_mongo_articles_count = result.get("today_mongo_articles_count", 0)
            today_preprocessed = result["today_preprocessed"]
            today_full_content = result["today_full_content"]
            high_score_articles = result.get("high_score_articles", 0)
            today_llm_summary = result["today_llm_summary"]
        else:
            total_feeds = 0
            total_articles = 0
            today_feeds = 0
            today_articles = 0
            today_mongo_articles_count = 0
            today_preprocessed = 0
            today_full_content = 0
            high_score_articles = 0
            today_llm_summary = 0

    return StatsResponse(
        total_feeds=total_feeds,
        total_articles=total_articles,
        today_feeds=today_feeds,
        today_articles=today_articles,
        today_mongo_articles_count=today_mongo_articles_count,
        today_preprocessed=today_preprocessed,
        today_preprocessed_rate=(
            round(today_preprocessed / max(today_mongo_articles_count, 1) * 100, 2)
            if today_mongo_articles_count > 0
            else 0
        ),
        today_full_content=today_full_content,
        today_full_content_rate=(
            round(today_full_content / max(today_mongo_articles_count, 1) * 100, 2)
            if today_mongo_articles_count > 0
            else 0
        ),
        high_score_articles=high_score_articles,
        today_llm_summary=today_llm_summary,
        today_llm_summary_rate=(
            round(today_llm_summary / max(high_score_articles, 1) * 100, 2)
            if high_score_articles > 0
            else 0
        ),
    )


@app.get("/api/heatmap")
def get_heatmap(
    date: Optional[str] = Query(None, description="日期格式: YYYY-MM-DD"),
    score_type: str = Query(
        "pre_value_score", description="评分类型: pre_value_score 或 score"
    ),
):
    if date:
        target_date = datetime.strptime(date, "%Y-%m-%d")
    else:
        target_date = datetime.now()

    all_scores = list(range(10, -1, -1))
    all_types = set()

    with engine.connect() as conn:
        results = (
            conn.execute(
                text(
                    """
                SELECT article_type, score, count 
                FROM article_type_score_stats 
                WHERE stat_date = :stat_date AND score_type = :score_type
            """
                ),
                {"stat_date": target_date.date(), "score_type": score_type},
            )
            .mappings()
            .all()
        )

        score_distribution = {}
        for row in results:
            atype = row["article_type"]
            score = row["score"]
            count = row["count"]
            all_types.add(atype)
            key = (score, atype)
            score_distribution[key] = count

    all_types = sorted(list(all_types))

    heatmap_data = []
    for score in all_scores:
        for atype in all_types:
            count = score_distribution.get((score, atype), 0)
            heatmap_data.append(
                [all_scores.index(score), all_types.index(atype), count]
            )

    return {
        "xAxis": [str(s) for s in all_scores],
        "yAxis": all_types,
        "data": heatmap_data,
    }


@app.get("/api/monthly-stats")
def get_monthly_stats(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(30, ge=1, le=100, description="每页数量"),
):
    with engine.connect() as conn:
        feeds = list(conn.execute(text("SELECT id, mp_name FROM feeds")).mappings())

    now = datetime.now()
    months = []
    for i in range(24):
        month_date = now - timedelta(days=i * 30)
        months.append(f"{month_date.year}-{month_date.month:02d}")
    months = sorted(list(set(months)), reverse=True)[:24]

    total_feeds = len(feeds)
    total_pages = (total_feeds + page_size - 1) // page_size
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_feeds = feeds[start_idx:end_idx]

    stats_dict = {}
    with engine.connect() as conn:
        results = (
            conn.execute(
                text(
                    "SELECT mp_id, stat_month, article_count FROM mp_monthly_stats WHERE stat_month IN :months"
                ),
                {"months": tuple(months)},
            )
            .mappings()
            .all()
        )

        for row in results:
            mp_id = row["mp_id"]
            month = row["stat_month"]
            count = row["article_count"]
            if mp_id not in stats_dict:
                stats_dict[mp_id] = {}
            stats_dict[mp_id][month] = count

    result = []
    for feed in paginated_feeds:
        feed_data = {"mp_name": feed["mp_name"], "mp_id": feed["id"]}
        mp_stats = stats_dict.get(feed["id"], {})

        for month in months:
            feed_data[month] = mp_stats.get(month, 0)

        result.append(feed_data)

    return {
        "months": months,
        "data": result,
        "total": total_feeds,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


class ArticleUpdate(BaseModel):
    reason: Optional[str] = None
    socre: Optional[int] = None
    tags: Optional[List[str]] = None
    书籍: Optional[str] = None
    事件: Optional[str] = None
    产品服务: Optional[str] = None
    人物: Optional[str] = None
    原则库: Optional[str] = None
    四精练: Optional[str] = None
    地点: Optional[str] = None
    概念实体: Optional[str] = None
    概要: Optional[str] = None
    点子库: Optional[str] = None
    生命之花: Optional[str] = None
    相关问题: Optional[str] = None
    组织公司: Optional[str] = None
    量化的结论: Optional[List[str]] = None
    问题库: Optional[str] = None
    is_collected: Optional[bool] = None
    is_followed: Optional[bool] = None
    is_enabled: Optional[bool] = None
    is_read: Optional[bool] = None
    梳理点子想法: Optional[str] = None
    备注: Optional[str] = None


@app.get("/api/articles")
def get_articles(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    score_type: str = Query(
        "pre_value_score", description="评分类型: pre_value_score 或 socre"
    ),
    scores: Optional[List[int]] = Query(None, description="评分列表，多个值"),
    tags: Optional[str] = Query(None, description="标签, 多个用逗号分隔"),
    is_collected: Optional[List[bool]] = Query(None, description="是否收藏列表"),
    is_followed: Optional[List[bool]] = Query(None, description="是否关注列表"),
    is_enabled: Optional[List[bool]] = Query(None, description="是否启用列表"),
    is_read: Optional[List[bool]] = Query(None, description="是否已读列表"),
    sort_by: str = Query(
        "publish_time",
        description="排序字段: publish_time, pre_value_score, socre, updated_at",
    ),
    sort_order: str = Query("desc", description="排序方向: asc, desc"),
    start_date: Optional[str] = Query(None, description="开始日期: YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期: YYYY-MM-DD"),
):
    filter_query = {}

    if scores:
        filter_query[score_type] = {"$in": scores}

    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        if tag_list:
            filter_query["article_type"] = {"$in": tag_list}

    if is_collected:
        filter_query["is_collected"] = {"$in": is_collected}
    if is_followed:
        filter_query["is_followed"] = {"$in": is_followed}
    if is_enabled:
        filter_query["is_enabled"] = {"$in": is_enabled}
    if is_read:
        filter_query["is_read"] = {"$in": is_read}

    # 添加时间范围筛选
    if start_date or end_date:
        filter_query["updated_at"] = {}
        if start_date:
            filter_query["updated_at"]["$gte"] = datetime.strptime(
                start_date, "%Y-%m-%d"
            )
        if end_date:
            # 结束日期加上一天，以便包含当天
            end_datetime = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            filter_query["updated_at"]["$lt"] = end_datetime

    sort_direction = -1 if sort_order == "desc" else 1
    sort_field = sort_by

    total = articles_collection.count_documents(filter_query)
    skip = (page - 1) * page_size

    articles = list(
        articles_collection.find(filter_query)
        .sort([(sort_field, sort_direction)])
        .skip(skip)
        .limit(page_size)
    )

    for article in articles:
        article["_id"] = str(article["_id"])

    total_pages = (total + page_size - 1) // page_size

    return {
        "data": articles,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@app.get("/api/articles/{article_id}")
def get_article(article_id: str):
    mongo_db = get_mongo_db()

    try:
        article = articles_collection.find_one({"_id": ObjectId(article_id)})
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        article["_id"] = str(article["_id"])
        return article
    except Exception as e:
        raise HTTPException(status_code=404, detail="Article not found")


@app.put("/api/articles/{article_id}")
def update_article(article_id: str, article_update: ArticleUpdate):
    mongo_db = get_mongo_db()

    try:
        update_data = {k: v for k, v in article_update.dict().items() if v is not None}
        update_data["updated_at"] = datetime.now()

        result = articles_collection.update_one(
            {"_id": ObjectId(article_id)}, {"$set": update_data}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Article not found")

        return {"message": "Article updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail="Article not found")


@app.get("/api/tags")
def get_all_tags(
    start_date: Optional[str] = Query(None, description="开始日期: YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期: YYYY-MM-DD"),
):
    mongo_db = get_mongo_db()

    match_query = {}

    if start_date or end_date:
        match_query["updated_at"] = {}
        if start_date:
            match_query["updated_at"]["$gte"] = datetime.strptime(
                start_date, "%Y-%m-%d"
            )
        if end_date:
            end_datetime = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            match_query["updated_at"]["$lt"] = end_datetime

    pipeline = []
    if match_query:
        pipeline.append({"$match": match_query})

    pipeline.extend(
        [
            {"$unwind": "$article_type"},
            {"$group": {"_id": "$article_type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
    )

    tags = list(articles_collection.aggregate(pipeline))

    return {"tags": [{"name": tag["_id"], "count": tag["count"]} for tag in tags]}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
