#!/usr/bin/env python3
import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from pymongo import MongoClient
import pandas as pd

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), "../../url_spider_service"))

from database import (
    MYSQL_HOST,
    MYSQL_PORT,
    MYSQL_USER,
    MYSQL_PASSWORD,
    MYSQL_DB,
    MONGO_HOST,
    MONGO_PORT,
    MONGO_USER,
    MONGO_PASSWORD,
    MONGO_DB_NAME,
)

# MySQL连接
DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
mysql_engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)

# MongoDB连接
MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/"
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client[MONGO_DB_NAME]
articles_collection = mongo_db["articles"]


def create_tables():
    """创建统计相关的表"""
    with open(os.path.join(os.path.dirname(__file__), "create_tables.sql"), "r") as f:
        sql = f.read()

    with mysql_engine.connect() as conn:
        for statement in sql.split(";"):
            if statement.strip():
                conn.execute(text(statement))
        conn.commit()


def calculate_daily_stats(target_date):
    """计算每日统计"""
    start_of_day = datetime(target_date.year, target_date.month, target_date.day)
    end_of_day = start_of_day + timedelta(days=1)
    start_timestamp = int(start_of_day.timestamp())
    end_timestamp = int(end_of_day.timestamp())

    with mysql_engine.connect() as conn:
        total_feeds = conn.execute(text("SELECT COUNT(*) FROM feeds")).scalar() or 0
        total_articles = (
            conn.execute(text("SELECT COUNT(*) FROM articles")).scalar() or 0
        )

        today_feeds = (
            conn.execute(
                text(
                    "SELECT COUNT(*) FROM feeds WHERE update_time >= :start AND update_time < :end"
                ),
                {"start": start_timestamp, "end": end_timestamp},
            ).scalar()
            or 0
        )

        today_articles = (
            conn.execute(
                text(
                    "SELECT COUNT(*) FROM articles WHERE updated_at >= :start AND updated_at < :end"
                ),
                {"start": start_of_day, "end": end_of_day},
            ).scalar()
            or 0
        )

    mongo_articles = list(
        articles_collection.find(
            {"updated_at": {"$gte": start_of_day, "$lt": end_of_day}}
        )
    )
    today_mongo_articles_count = len(mongo_articles)

    today_preprocessed = len(
        [a for a in mongo_articles if a.get("pre_value_score", 0) >= 1]
    )
    today_full_content = len([a for a in mongo_articles if a.get("full_content")])

    high_score_articles = [
        a for a in mongo_articles if a.get("pre_value_score", 0) >= 3
    ]
    high_score_count = len(high_score_articles)
    today_llm_summary = len(
        [
            a
            for a in high_score_articles
            if a.get(
                "llm_summary_processed", False
            )  # or a.get("reason") or a.get("概要")
        ]
    )

    return {
        "stat_date": target_date.date(),
        "total_feeds": total_feeds,
        "total_articles": total_articles,
        "today_feeds": today_feeds,
        "today_articles": today_articles,
        "today_mongo_articles_count": today_mongo_articles_count,
        "today_preprocessed": today_preprocessed,
        "today_full_content": today_full_content,
        "high_score_articles": high_score_count,
        "today_llm_summary": today_llm_summary,
    }


def save_daily_stats(stats_data):
    """保存每日统计到数据库"""
    with mysql_engine.connect() as conn:
        insert_sql = text(
            """
            INSERT INTO daily_stats (stat_date, total_feeds, total_articles, today_feeds, 
                today_articles, today_mongo_articles_count, today_preprocessed, today_full_content, 
                high_score_articles, today_llm_summary)
            VALUES (:stat_date, :total_feeds, :total_articles, :today_feeds, 
                :today_articles, :today_mongo_articles_count, :today_preprocessed, :today_full_content, 
                :high_score_articles, :today_llm_summary)
            ON DUPLICATE KEY UPDATE
                total_feeds = VALUES(total_feeds),
                total_articles = VALUES(total_articles),
                today_feeds = VALUES(today_feeds),
                today_articles = VALUES(today_articles),
                today_mongo_articles_count = VALUES(today_mongo_articles_count),
                today_preprocessed = VALUES(today_preprocessed),
                today_full_content = VALUES(today_full_content),
                high_score_articles = VALUES(high_score_articles),
                today_llm_summary = VALUES(today_llm_summary),
                updated_at = CURRENT_TIMESTAMP
        """
        )
        conn.execute(insert_sql, stats_data)
        conn.commit()


def calculate_monthly_stats():
    """计算公众号月度统计"""
    now = datetime.now()

    # 先获取所有公众号
    with mysql_engine.connect() as conn:
        feeds = pd.read_sql(text("SELECT id as mp_id, mp_name FROM feeds"), conn)

    # 生成近24个月的月份列表
    months = []
    for i in range(24):
        month_date = now - timedelta(days=i * 30)
        months.append(f"{month_date.year}-{month_date.month:02d}")
    months = sorted(list(set(months)), reverse=True)[:24]

    # 为每个月统计
    for month in months:
        year, month_num = map(int, month.split("-"))
        start_of_month = datetime(year, month_num, 1)
        if month_num == 12:
            end_of_month = datetime(year + 1, 1, 1)
        else:
            end_of_month = datetime(year, month_num + 1, 1)

        start_timestamp = int(start_of_month.timestamp())
        end_timestamp = int(end_of_month.timestamp())

        # 使用聚合查询
        pipeline = [
            {
                "$match": {
                    "publish_time": {"$gte": start_timestamp, "$lt": end_timestamp}
                }
            },
            {"$group": {"_id": "$mp_id", "count": {"$sum": 1}}},
        ]
        results = list(articles_collection.aggregate(pipeline))

        # 保存到数据库
        with mysql_engine.connect() as conn:
            for r in results:
                mp_id = r["_id"]
                if mp_id is None:
                    continue
                count = r["count"]
                insert_sql = text(
                    """
                    INSERT INTO mp_monthly_stats (mp_id, stat_month, article_count)
                    VALUES (:mp_id, :stat_month, :article_count)
                    ON DUPLICATE KEY UPDATE
                        article_count = VALUES(article_count),
                        updated_at = CURRENT_TIMESTAMP
                """
                )
                conn.execute(
                    insert_sql,
                    {"mp_id": mp_id, "stat_month": month, "article_count": count},
                )
            conn.commit()


def calculate_heatmap_stats(target_date, score_type):
    """计算热力图统计"""
    start_of_day = datetime(target_date.year, target_date.month, target_date.day)
    end_of_day = start_of_day + timedelta(days=1)

    mongo_articles = list(
        articles_collection.find(
            {"updated_at": {"$gte": start_of_day, "$lt": end_of_day}}
        )
    )

    score_distribution = {}
    for article in mongo_articles:
        score = min(10, max(0, int(article.get(score_type, 0))))
        article_type = article.get("article_type", "")

        # 处理 article_type 可能是列表的情况
        if isinstance(article_type, list):
            # 如果是列表，先排序，然后取最后一个元素
            if article_type:
                # 排序列表
                sorted_types = sorted(article_type)
                # 取最后一个元素
                article_type = sorted_types[-1]
            else:
                article_type = ""

        if article_type:
            key = (article_type, score)
            score_distribution[key] = score_distribution.get(key, 0) + 1

    # 保存到数据库
    with mysql_engine.connect() as conn:
        for (atype, score), count in score_distribution.items():
            insert_sql = text(
                """
                INSERT INTO article_type_score_stats (stat_date, score_type, article_type, score, count)
                VALUES (:stat_date, :score_type, :article_type, :score, :count)
                ON DUPLICATE KEY UPDATE
                    count = VALUES(count),
                    updated_at = CURRENT_TIMESTAMP
            """
            )
            conn.execute(
                insert_sql,
                {
                    "stat_date": target_date.date(),
                    "score_type": score_type,
                    "article_type": atype,
                    "score": score,
                    "count": count,
                },
            )
        conn.commit()


def main():
    """主函数"""
    print("开始计算统计数据...")

    # 创建表
    print("创建/检查统计表...")
    create_tables()

    # 计算今天和昨天的统计
    today = datetime.now()
    yesterday = today - timedelta(days=1)

    for date in [yesterday, today]:
        print(f"计算 {date.date()} 的每日统计...")
        daily_stats = calculate_daily_stats(date)
        save_daily_stats(daily_stats)

        print(f"计算 {date.date()} 的热力图统计...")
        calculate_heatmap_stats(date, "pre_value_score")
        calculate_heatmap_stats(date, "score")

    # 计算月度统计
    print("计算月度统计...")
    calculate_monthly_stats()

    print("统计计算完成！")


if __name__ == "__main__":
    main()
