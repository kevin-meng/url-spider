from fastapi import FastAPI, Depends, Query, HTTPException, Request
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
def get_articles(request: Request):
    # 获取所有查询参数
    query_params = dict(request.query_params)

    # 打印原始查询参数
    print(f"原始查询参数: {query_params}")

    # 手动解析参数
    page = int(query_params.get("page", 1))
    page_size = int(query_params.get("page_size", 10))
    score_type = query_params.get("score_type", "pre_value_score")

    # 处理scores参数
    scores = None
    if "scores" in query_params:
        scores = query_params["scores"]
        if isinstance(scores, list):
            scores = [int(s) for s in scores]
        else:
            scores = [int(s) for s in scores.split(",")]

    # 处理tags参数
    tags = query_params.get("tags")

    # 处理布尔类型参数
    def parse_bool(param_name):
        if param_name in query_params:
            value = query_params[param_name]
            if isinstance(value, list):
                # 如果是列表，取第一个值
                return value[0].lower() == "true"
            else:
                return value.lower() == "true"
        return None

    is_collected = parse_bool("is_collected")
    is_followed = parse_bool("is_followed")
    is_enabled = parse_bool("is_enabled")
    is_read = parse_bool("is_read")

    # 处理其他参数
    sort_by = query_params.get("sort_by", "publish_time")
    sort_order = query_params.get("sort_order", "desc")
    start_date = query_params.get("start_date")
    end_date = query_params.get("end_date")

    # 打印解析后的参数
    print(
        f"解析后的参数: page={page}, page_size={page_size}, score_type={score_type}, scores={scores}, tags={tags}, is_collected={is_collected}, is_followed={is_followed}, is_enabled={is_enabled}, is_read={is_read}, sort_by={sort_by}, sort_order={sort_order}, start_date={start_date}, end_date={end_date}"
    )

    filter_query = {}

    if scores:
        filter_query[score_type] = {"$in": scores}

    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        if tag_list:
            filter_query["article_type"] = {"$in": tag_list}

    if is_collected is not None:
        filter_query["is_collected"] = is_collected
    if is_followed is not None:
        filter_query["is_followed"] = is_followed
    if is_enabled is not None:
        filter_query["is_enabled"] = is_enabled
    if is_read is not None:
        filter_query["is_read"] = is_read

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

    # 打印数据库查询条件
    print(f"数据库查询条件: {filter_query}")

    sort_direction = -1 if sort_order == "desc" else 1
    sort_field = sort_by

    total = articles_collection.count_documents(filter_query)
    # 打印数据库查询数量
    print(f"数据库查询数量: {total}")

    skip = (page - 1) * page_size

    articles = list(
        articles_collection.find(
            filter_query,
            {"mp_id": 0, "clipper_metadata": 0, "full_content": 0, "full_markdown": 0},
        )
        .sort([(sort_field, sort_direction)])
        .skip(skip)
        .limit(page_size)
    )

    for article in articles:
        article["_id"] = str(article["_id"])

    total_pages = (total + page_size - 1) // page_size

    # 打印接口返回数量
    print(f"接口返回数量: {len(articles)}, 总数量: {total}")

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
        # 获取完整的文章数据，包括所有字段
        article = articles_collection.find_one({"_id": ObjectId(article_id)})
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        article["_id"] = str(article["_id"])
        return article
    except Exception as e:
        raise HTTPException(status_code=404, detail="Article not found")


@app.get("/api/check-url")
def check_url(url: str = Query(..., description="要检查的URL")):
    """检查URL是否存在于MongoDB数据库中"""
    try:
        # 检查URL是否存在
        existing_article = articles_collection.find_one({"url": url})

        if existing_article:
            # 检查llm_summary_processed字段
            llm_summary_processed = existing_article.get("llm_summary_processed", False)

            # 根据llm_summary_processed字段值返回不同的状态
            if llm_summary_processed:
                return {
                    "exists": True,
                    "message": "URL已存在于数据库中，且已处理摘要",
                    "article_id": str(existing_article["_id"]),
                    "llm_summary_processed": True,
                }
            else:
                return {
                    "exists": True,
                    "message": "URL已存在于数据库中，但未处理摘要",
                    "article_id": str(existing_article["_id"]),
                    "llm_summary_processed": False,
                }
        else:
            return {
                "exists": False,
                "message": "URL不存在于数据库中",
                "llm_summary_processed": False,
            }
    except Exception as e:
        return {
            "exists": False,
            "message": f"检查失败: {str(e)}",
            "llm_summary_processed": False,
        }


# 预处理markdown内容


import re


def preprocess_markdown(content):
    """预处理 markdown 内容，去除图片、链接和元数据，节约 token"""
    if not content:
        return content

    # 1. 去除元数据（YAML front matter）
    content = re.sub(r"^---[\s\S]*?---\n", "", content)

    # 2. 去除图片（包括复杂的 SVG 图片）
    # 匹配 ![]() 格式的图片，包括包含特殊字符的情况
    content = re.sub(r"!\[.*?\]\([^)]*\)", "", content)
    # 额外处理可能的残留 SVG 内容（包括 URL 编码的情况）
    content = re.sub(r"' fill='[^']*'>.*?</svg>", "", content)
    # 处理 URL 编码的 SVG 残留内容
    content = re.sub(
        r"' fill='[^']*'%3E.*?%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E\)", "", content
    )

    # 3. 去除链接，保留链接文本
    # 处理有文本的链接 [text](url) -> text
    content = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", content)
    # 处理空文本的链接 []() -> 完全去除
    content = re.sub(r"\[\]\([^)]+\)", "", content)

    # 4. 去除多余的空白行
    content = re.sub(r"\n{3,}", "\n\n", content)

    return content


class ProcessUrlRequest(BaseModel):
    url: str
    use_llm_summary: bool = False


class BatchProcessUrlsRequest(BaseModel):
    urls: List[str]
    use_llm_summary: bool = False
    priority: str = "normal"  # high, normal, low
    max_concurrency: int = 2


# 任务状态管理
from bson import ObjectId
import asyncio
from typing import Dict, Optional, List, Deque
from collections import deque
import threading
import time

# 全局任务队列和管理变量
task_queue = deque()  # 任务队列
task_queue_lock = threading.Lock()  # 队列锁
running_tasks = set()  # 正在运行的任务
MAX_CONCURRENT_TASKS = 2  # 最大并发任务数
task_scheduler_running = False  # 任务调度器运行状态

# 任务优先级映射
PRIORITY_MAP = {"high": 0, "normal": 1, "low": 2}


# 获取任务状态集合
def get_task_collection():
    from database import get_mongo_db

    db = get_mongo_db()
    return db.task_status


async def task_scheduler():
    """任务调度器，负责从队列中取出任务并执行"""
    global task_scheduler_running, running_tasks
    task_scheduler_running = True

    print("任务调度器已启动")

    while task_scheduler_running:
        try:
            # 检查当前运行的任务数
            with task_queue_lock:
                current_running = len(running_tasks)

                # 如果有空闲槽位且队列不为空
                if current_running < MAX_CONCURRENT_TASKS and task_queue:
                    # 按优先级取出任务
                    # 简单实现：遍历队列找到优先级最高的任务
                    highest_priority = float("inf")
                    highest_priority_task = None

                    for i, task_info in enumerate(task_queue):
                        priority = PRIORITY_MAP.get(task_info["priority"], 1)
                        if priority < highest_priority:
                            highest_priority = priority
                            highest_priority_task = (i, task_info)

                    if highest_priority_task:
                        i, task_info = highest_priority_task
                        # 从队列中移除任务
                        task_queue.remove(task_info)

                        # 添加到运行任务集合
                        running_tasks.add(task_info["task_id"])

                        # 启动任务
                        asyncio.create_task(process_task_from_queue(task_info))

            # 短暂休眠，避免忙等
            await asyncio.sleep(1)

        except Exception as e:
            print(f"任务调度器错误: {e}")
            await asyncio.sleep(1)


async def process_task_from_queue(task_info):
    """处理从队列中取出的任务"""
    try:
        task_id = task_info["task_id"]
        url = task_info["url"]
        use_llm_summary = task_info["use_llm_summary"]
        batch_task_id = task_info.get("batch_task_id")

        # 执行任务
        await process_url_async(task_id, url, use_llm_summary, batch_task_id)

    except Exception as e:
        print(f"处理队列任务错误: {e}")
    finally:
        # 从运行任务集合中移除
        with task_queue_lock:
            if task_info["task_id"] in running_tasks:
                running_tasks.remove(task_info["task_id"])


def update_batch_task_status(batch_task_id: str, sub_task_id: str, status: str):
    """更新批次任务的状态"""
    task_collection = get_task_collection()

    try:
        # 获取批次任务信息
        batch_task = task_collection.find_one({"task_id": batch_task_id})
        if not batch_task:
            return

        batch_info = batch_task.get("batch_info", {})
        total_urls = batch_info.get("total_urls", 0)
        processed_urls = batch_info.get("processed_urls", 0)
        success_count = batch_info.get("success_count", 0)
        failed_count = batch_info.get("failed_count", 0)
        sub_tasks = batch_info.get("sub_tasks", [])

        # 更新计数
        processed_urls += 1
        if status == "completed":
            success_count += 1
        elif status == "failed":
            failed_count += 1

        # 计算进度
        progress = int((processed_urls / total_urls) * 100) if total_urls > 0 else 0

        # 检查是否所有任务都已完成
        if processed_urls >= total_urls:
            batch_status = "completed"
            message = f"批次任务已完成，成功: {success_count}, 失败: {failed_count}"
        else:
            batch_status = "processing"
            message = f"批次任务处理中，已完成 {processed_urls}/{total_urls}"

        # 更新批次任务状态
        task_collection.update_one(
            {"task_id": batch_task_id},
            {
                "$set": {
                    "status": batch_status,
                    "progress": progress,
                    "current_stage": (
                        "处理中" if processed_urls < total_urls else "完成"
                    ),
                    "message": message,
                    "batch_info": {
                        "total_urls": total_urls,
                        "processed_urls": processed_urls,
                        "success_count": success_count,
                        "failed_count": failed_count,
                        "sub_tasks": sub_tasks,
                    },
                    "updated_at": datetime.now(),
                }
            },
        )

    except Exception as e:
        print(f"更新批次任务状态错误: {e}")


# 启动任务调度器
def start_task_scheduler():
    """启动任务调度器"""
    asyncio.create_task(task_scheduler())


@app.post("/api/process-url")
async def process_url(request: ProcessUrlRequest):
    """处理单条URL链接，包括检查数据库、抓取文章、生成摘要等完整流程"""
    try:
        url = request.url
        use_llm_summary = request.use_llm_summary

        # 创建任务记录
        task_id = str(ObjectId())
        task_collection = get_task_collection()

        task_collection.insert_one(
            {
                "_id": ObjectId(task_id),
                "task_id": task_id,
                "url": url,
                "use_llm_summary": use_llm_summary,
                "status": "queued",  # 改为排队状态
                "progress": 0,
                "current_stage": "排队中",
                "message": "任务已加入队列，等待处理",
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }
        )

        # 将任务添加到队列
        task_info = {
            "task_id": task_id,
            "url": url,
            "use_llm_summary": use_llm_summary,
            "priority": "normal",
        }

        with task_queue_lock:
            task_queue.append(task_info)

        # 返回任务ID，让前端轮询状态
        return {
            "task_id": task_id,
            "status": "queued",
            "message": "任务已加入队列，等待处理",
            "progress_url": f"/api/task-status/{task_id}",
        }

    except Exception as e:
        return {"status": "error", "message": f"任务启动失败: {str(e)}", "data": None}


@app.post("/api/batch-process-urls")
async def batch_process_urls(request: BatchProcessUrlsRequest):
    """批量处理URL链接"""
    try:
        urls = request.urls
        use_llm_summary = request.use_llm_summary
        priority = request.priority
        max_concurrency = min(request.max_concurrency, 5)  # 限制最大并发数

        # 创建批次任务记录
        batch_task_id = str(ObjectId())
        task_collection = get_task_collection()

        # 为批次创建主任务
        task_collection.insert_one(
            {
                "_id": ObjectId(batch_task_id),
                "task_id": batch_task_id,
                "url": "batch",
                "use_llm_summary": use_llm_summary,
                "status": "queued",
                "progress": 0,
                "current_stage": "排队中",
                "message": f"批次任务已加入队列，包含 {len(urls)} 个URL",
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "batch_info": {
                    "total_urls": len(urls),
                    "processed_urls": 0,
                    "success_count": 0,
                    "failed_count": 0,
                    "sub_tasks": [],
                },
            }
        )

        # 为每个URL创建子任务并添加到队列
        sub_task_ids = []
        for url in urls:
            sub_task_id = str(ObjectId())
            sub_task_ids.append(sub_task_id)

            # 创建子任务记录
            task_collection.insert_one(
                {
                    "_id": ObjectId(sub_task_id),
                    "task_id": sub_task_id,
                    "url": url,
                    "use_llm_summary": use_llm_summary,
                    "status": "queued",
                    "progress": 0,
                    "current_stage": "排队中",
                    "message": "任务已加入队列，等待处理",
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "batch_task_id": batch_task_id,  # 关联到批次任务
                }
            )

            # 将任务添加到队列
            task_info = {
                "task_id": sub_task_id,
                "url": url,
                "use_llm_summary": use_llm_summary,
                "priority": priority,
                "batch_task_id": batch_task_id,
            }

            with task_queue_lock:
                task_queue.append(task_info)

        # 更新批次任务的子任务列表
        task_collection.update_one(
            {"task_id": batch_task_id},
            {
                "$set": {
                    "batch_info.sub_tasks": sub_task_ids,
                    "updated_at": datetime.now(),
                }
            },
        )

        # 返回批次任务ID，让前端轮询状态
        return {
            "task_id": batch_task_id,
            "status": "queued",
            "message": f"批次任务已加入队列，包含 {len(urls)} 个URL",
            "progress_url": f"/api/task-status/{batch_task_id}",
            "total_urls": len(urls),
            "sub_task_ids": sub_task_ids,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"批次任务启动失败: {str(e)}",
            "data": None,
        }


async def process_url_async(
    task_id: str, url: str, use_llm_summary: bool, batch_task_id: Optional[str] = None
):
    """异步处理URL链接"""
    task_collection = get_task_collection()

    try:
        # 更新任务状态：开始处理
        task_collection.update_one(
            {"task_id": task_id},
            {
                "$set": {
                    "status": "processing",
                    "progress": 10,
                    "current_stage": "检查URL",
                    "message": "检查URL是否已存在",
                    "updated_at": datetime.now(),
                }
            },
        )

        # 1. 使用check_url函数检查URL是否已存在
        check_result = check_url(url)

        # 更新任务状态：处理URL存在的情况
        task_collection.update_one(
            {"task_id": task_id},
            {
                "$set": {
                    "progress": 20,
                    "current_stage": "处理URL",
                    "message": f"URL状态: {check_result['message']}",
                    "updated_at": datetime.now(),
                }
            },
        )

        # 2. 如果URL已存在
        if check_result["exists"]:
            # 获取完整的文章数据
            existing_article = articles_collection.find_one({"url": url})

            # 检查是否需要生成摘要
            if use_llm_summary and not check_result.get("llm_summary_processed", False):
                # 更新任务状态：生成摘要
                task_collection.update_one(
                    {"task_id": task_id},
                    {
                        "$set": {
                            "progress": 30,
                            "current_stage": "生成摘要",
                            "message": "正在生成文章摘要",
                            "updated_at": datetime.now(),
                        }
                    },
                )

                # 从数据库中获取full_markdown
                full_markdown = existing_article.get("full_markdown", "")
                if full_markdown:
                    # 更新任务状态：预处理markdown
                    task_collection.update_one(
                        {"task_id": task_id},
                        {
                            "$set": {
                                "progress": 40,
                                "current_stage": "预处理",
                                "message": "正在预处理markdown内容",
                                "updated_at": datetime.now(),
                            }
                        },
                    )

                    # 预处理markdown
                    processed_markdown = preprocess_markdown(full_markdown)

                    # 更新任务状态：调用摘要接口
                    task_collection.update_one(
                        {"task_id": task_id},
                        {
                            "$set": {
                                "progress": 60,
                                "current_stage": "调用接口",
                                "message": "正在调用大模型摘要接口",
                                "updated_at": datetime.now(),
                            }
                        },
                    )

                    # 调用摘要接口
                    import requests

                    summary_api_url = "http://192.168.2.18:8013/api/summarize"
                    summary_response = requests.post(
                        summary_api_url, json={"markdown_content": processed_markdown}
                    )
                    summary_response.raise_for_status()
                    summary_result = summary_response.json()

                    # 更新任务状态：更新数据库
                    task_collection.update_one(
                        {"task_id": task_id},
                        {
                            "$set": {
                                "progress": 80,
                                "current_stage": "更新数据库",
                                "message": "正在更新数据库",
                                "updated_at": datetime.now(),
                            }
                        },
                    )

                    # 更新到数据库
                    update_data = summary_result
                    update_data["llm_summary_processed"] = True
                    update_data["updated_at"] = datetime.now()
                    articles_collection.update_one(
                        {"_id": existing_article["_id"]}, {"$set": update_data}
                    )

                    # 更新现有文章数据
                    existing_article.update(update_data)
                    existing_article["_id"] = str(existing_article["_id"])

                    # 更新任务状态：完成
                    task_collection.update_one(
                        {"task_id": task_id},
                        {
                            "$set": {
                                "status": "completed",
                                "progress": 100,
                                "current_stage": "完成",
                                "message": "处理完成",
                                "result": {
                                    "status": "updated",
                                    "message": "URL已存在，已更新摘要",
                                    "article_id": str(existing_article["_id"]),
                                    "data": existing_article,
                                },
                                "updated_at": datetime.now(),
                            }
                        },
                    )

                    # 更新批次任务状态
                    if batch_task_id:
                        update_batch_task_status(batch_task_id, task_id, "completed")

                    return

            # 如果不需要生成摘要或已处理过摘要
            existing_article["_id"] = str(existing_article["_id"])

            # 更新任务状态：完成
            task_collection.update_one(
                {"task_id": task_id},
                {
                    "$set": {
                        "status": "completed",
                        "progress": 100,
                        "current_stage": "完成",
                        "message": "处理完成",
                        "result": {
                            "status": "exists",
                            "message": check_result["message"],
                            "article_id": str(existing_article["_id"]),
                            "data": existing_article,
                        },
                        "updated_at": datetime.now(),
                    }
                },
            )

            # 更新批次任务状态
            if batch_task_id:
                update_batch_task_status(batch_task_id, task_id, "completed")

            return

        # 3. 如果URL不存在，调用clip接口抓取文章
        task_collection.update_one(
            {"task_id": task_id},
            {
                "$set": {
                    "progress": 30,
                    "current_stage": "抓取文章",
                    "message": "正在抓取文章内容",
                    "updated_at": datetime.now(),
                }
            },
        )

        import requests

        clip_api_url = "http://192.168.2.18:8013/api/clip"
        clip_response = requests.post(clip_api_url, json={"url": url})
        clip_response.raise_for_status()
        clip_result = clip_response.json()

        # 4. 如果需要，调用摘要接口
        summary_result = None
        if use_llm_summary and clip_result.get("full_markdown"):
            # 更新任务状态：预处理markdown
            task_collection.update_one(
                {"task_id": task_id},
                {
                    "$set": {
                        "progress": 50,
                        "current_stage": "预处理",
                        "message": "正在预处理markdown内容",
                        "updated_at": datetime.now(),
                    }
                },
            )

            # 预处理markdown
            processed_markdown = preprocess_markdown(clip_result["full_markdown"])

            # 更新任务状态：生成摘要
            task_collection.update_one(
                {"task_id": task_id},
                {
                    "$set": {
                        "progress": 70,
                        "current_stage": "生成摘要",
                        "message": "正在调用大模型摘要接口",
                        "updated_at": datetime.now(),
                    }
                },
            )

            # 调用摘要接口
            summary_api_url = "http://192.168.2.18:8013/api/summarize"
            summary_response = requests.post(
                summary_api_url, json={"markdown_content": processed_markdown}
            )
            summary_response.raise_for_status()
            summary_result = summary_response.json()

        # 5. 构建文章数据
        task_collection.update_one(
            {"task_id": task_id},
            {
                "$set": {
                    "progress": 80,
                    "current_stage": "构建数据",
                    "message": "正在构建文章数据",
                    "updated_at": datetime.now(),
                }
            },
        )

        article_data = {
            "url": url,
            "title": clip_result["metadata"].get("title", ""),
            "source": clip_result["metadata"].get("source", ""),
            "created_at": clip_result["metadata"].get("created", datetime.now()),
            "updated_at": datetime.now(),
            "full_markdown": clip_result.get("full_markdown", ""),
            "content": clip_result.get("content", ""),
            "metadata": clip_result.get("metadata", {}),
            "llm_summary_processed": False,
        }

        # 添加摘要（如果有）
        if summary_result:
            article_data.update(summary_result)
            article_data["llm_summary_processed"] = True

        # 6. 保存到MongoDB
        task_collection.update_one(
            {"task_id": task_id},
            {
                "$set": {
                    "progress": 90,
                    "current_stage": "保存数据",
                    "message": "正在保存到数据库",
                    "updated_at": datetime.now(),
                }
            },
        )

        inserted_result = articles_collection.insert_one(article_data)
        article_data["_id"] = str(inserted_result.inserted_id)

        # 更新任务状态：完成
        task_collection.update_one(
            {"task_id": task_id},
            {
                "$set": {
                    "status": "completed",
                    "progress": 100,
                    "current_stage": "完成",
                    "message": "处理完成",
                    "result": {
                        "status": "success",
                        "message": "处理成功",
                        "article_id": str(inserted_result.inserted_id),
                        "data": article_data,
                    },
                    "updated_at": datetime.now(),
                }
            },
        )

        # 更新批次任务状态
        if batch_task_id:
            update_batch_task_status(batch_task_id, task_id, "completed")

    except requests.exceptions.RequestException as e:
        task_collection.update_one(
            {"task_id": task_id},
            {
                "$set": {
                    "status": "failed",
                    "progress": 100,
                    "current_stage": "失败",
                    "message": f"外部接口调用失败: {str(e)}",
                    "result": {
                        "status": "error",
                        "message": f"外部接口调用失败: {str(e)}",
                        "data": None,
                    },
                    "updated_at": datetime.now(),
                }
            },
        )

        # 更新批次任务状态
        if batch_task_id:
            update_batch_task_status(batch_task_id, task_id, "failed")
    except Exception as e:
        task_collection.update_one(
            {"task_id": task_id},
            {
                "$set": {
                    "status": "failed",
                    "progress": 100,
                    "current_stage": "失败",
                    "message": f"处理失败: {str(e)}",
                    "result": {
                        "status": "error",
                        "message": f"处理失败: {str(e)}",
                        "data": None,
                    },
                    "updated_at": datetime.now(),
                }
            },
        )

        # 更新批次任务状态
        if batch_task_id:
            update_batch_task_status(batch_task_id, task_id, "failed")


@app.get("/api/task-status/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    try:
        task_collection = get_task_collection()
        task = task_collection.find_one({"task_id": task_id})

        if not task:
            return {"status": "error", "message": "任务不存在"}

        # 转换ObjectId为字符串
        task_data = {
            "task_id": task.get("task_id"),
            "url": task.get("url"),
            "status": task.get("status"),
            "progress": task.get("progress"),
            "current_stage": task.get("current_stage"),
            "message": task.get("message"),
            "result": task.get("result"),
            "created_at": task.get("created_at"),
            "updated_at": task.get("updated_at"),
        }

        # 检查是否是批次任务
        batch_info = task.get("batch_info")
        if batch_info:
            # 添加批次任务信息
            task_data["batch_info"] = batch_info

            # 获取子任务状态
            sub_tasks = batch_info.get("sub_tasks", [])
            if sub_tasks:
                sub_task_statuses = []
                for sub_task_id in sub_tasks:
                    sub_task = task_collection.find_one({"task_id": sub_task_id})
                    if sub_task:
                        sub_task_statuses.append(
                            {
                                "task_id": sub_task.get("task_id"),
                                "url": sub_task.get("url"),
                                "status": sub_task.get("status"),
                                "progress": sub_task.get("progress"),
                                "current_stage": sub_task.get("current_stage"),
                                "message": sub_task.get("message"),
                                "result": sub_task.get("result"),
                                "updated_at": sub_task.get("updated_at"),
                            }
                        )
                task_data["sub_task_statuses"] = sub_task_statuses

        return task_data

    except Exception as e:
        return {"status": "error", "message": f"获取任务状态失败: {str(e)}"}


# 保留原有的同步处理接口，用于兼容
@app.post("/api/process-url-sync")
def process_url_sync(request: ProcessUrlRequest):
    """处理单条URL链接，包括检查数据库、抓取文章、生成摘要等完整流程"""
    try:
        url = request.url
        use_llm_summary = request.use_llm_summary

        # 1. 使用check_url函数检查URL是否已存在
        check_result = check_url(url)

        # 2. 如果URL已存在
        if check_result["exists"]:
            # 获取完整的文章数据
            existing_article = articles_collection.find_one({"url": url})

            # 检查是否需要生成摘要
            if use_llm_summary and not check_result.get("llm_summary_processed", False):
                # 从数据库中获取full_markdown
                full_markdown = existing_article.get("full_markdown", "")
                if full_markdown:
                    # 预处理markdown
                    processed_markdown = preprocess_markdown(full_markdown)

                    # 调用摘要接口
                    import requests

                    summary_api_url = "http://192.168.2.18:8013/api/summarize"
                    summary_response = requests.post(
                        summary_api_url, json={"markdown_content": processed_markdown}
                    )
                    summary_response.raise_for_status()
                    summary_result = summary_response.json()

                    # 更新到数据库
                    update_data = summary_result
                    update_data["llm_summary_processed"] = True
                    update_data["updated_at"] = datetime.now()
                    articles_collection.update_one(
                        {"_id": existing_article["_id"]}, {"$set": update_data}
                    )

                    # 更新现有文章数据
                    existing_article.update(update_data)
                    existing_article["_id"] = str(existing_article["_id"])

                    return {
                        "status": "updated",
                        "message": "URL已存在，已更新摘要",
                        "article_id": str(existing_article["_id"]),
                        "data": existing_article,
                    }

            # 如果不需要生成摘要或已处理过摘要
            existing_article["_id"] = str(existing_article["_id"])
            return {
                "status": "exists",
                "message": check_result["message"],
                "article_id": str(existing_article["_id"]),
                "data": existing_article,
            }

        # 3. 如果URL不存在，调用clip接口抓取文章
        import requests

        clip_api_url = "http://192.168.2.18:8013/api/clip"
        clip_response = requests.post(clip_api_url, json={"url": url})
        clip_response.raise_for_status()
        clip_result = clip_response.json()

        # 4. 如果需要，调用摘要接口
        summary_result = None
        if use_llm_summary and clip_result.get("full_markdown"):
            # 预处理markdown
            processed_markdown = preprocess_markdown(clip_result["full_markdown"])

            # 调用摘要接口
            summary_api_url = "http://192.168.2.18:8013/api/summarize"
            summary_response = requests.post(
                summary_api_url, json={"markdown_content": processed_markdown}
            )
            summary_response.raise_for_status()
            summary_result = summary_response.json()

        # 5. 构建文章数据
        article_data = {
            "url": url,
            "title": clip_result["metadata"].get("title", ""),
            "source": clip_result["metadata"].get("source", ""),
            "created_at": clip_result["metadata"].get("created", datetime.now()),
            "updated_at": datetime.now(),
            "full_markdown": clip_result.get("full_markdown", ""),
            "content": clip_result.get("content", ""),
            "metadata": clip_result.get("metadata", {}),
            "llm_summary_processed": False,
        }

        # 添加摘要（如果有）
        if summary_result:
            article_data.update(summary_result)
            article_data["llm_summary_processed"] = True

        # 6. 保存到MongoDB
        inserted_result = articles_collection.insert_one(article_data)
        article_data["_id"] = str(inserted_result.inserted_id)

        return {
            "status": "success",
            "message": "处理成功",
            "article_id": str(inserted_result.inserted_id),
            "data": article_data,
        }

    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": f"外部接口调用失败: {str(e)}",
            "data": None,
        }
    except Exception as e:
        return {"status": "error", "message": f"处理失败: {str(e)}", "data": None}


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


# 启动任务调度器
import threading


def start_scheduler_in_thread():
    """在后台线程中启动任务调度器"""
    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(task_scheduler())


# 启动后台线程运行任务调度器
scheduler_thread = threading.Thread(target=start_scheduler_in_thread, daemon=True)
scheduler_thread.start()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
