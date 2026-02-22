import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../url_spider_service'))

from datetime import datetime, timedelta
from database import engine, articles_collection
from sqlalchemy import text

print("="*60)
print("测试 API 数据查询")
print("="*60)

today = datetime.now()
start_of_day = datetime(today.year, today.month, today.day)
end_of_day = start_of_day + timedelta(days=1)

print(f"\n日期范围: {start_of_day} 到 {end_of_day}")

# 测试 MySQL 查询
print("\n--- MySQL 查询 ---")
with engine.connect() as conn:
    total_feeds = conn.execute(text("SELECT COUNT(*) FROM feeds")).scalar()
    total_articles = conn.execute(text("SELECT COUNT(*) FROM articles")).scalar()
    
    today_feeds = conn.execute(
        text("SELECT COUNT(*) FROM feeds WHERE update_time >= :start AND update_time < :end"),
        {"start": int(start_of_day.timestamp()), "end": int(end_of_day.timestamp())}
    ).scalar()
    
    today_articles = conn.execute(
        text("SELECT COUNT(*) FROM articles WHERE created_at >= :start AND created_at < :end"),
        {"start": start_of_day, "end": end_of_day}
    ).scalar()
    
    print(f"总账号数: {total_feeds}")
    print(f"总文章数: {total_articles}")
    print(f"今日更新账号: {today_feeds}")
    print(f"今日新增文章: {today_articles}")

# 测试 MongoDB 查询
print("\n--- MongoDB 查询 ---")
mongo_articles = list(articles_collection.find({
    "created_at": {"$gte": start_of_day, "$lt": end_of_day}
}))

print(f"今日 MongoDB 文章数: {len(mongo_articles)}")

if mongo_articles:
    preprocessed = len([a for a in mongo_articles if a.get("pre_value_score", 0) >= 1])
    full_content = len([a for a in mongo_articles if a.get("full_content")])
    llm_summary = len([a for a in mongo_articles if a.get("pre_value_score", 0) >= 3 and a.get("llm_summary_processed", False)])
    
    print(f"预加工: {preprocessed}")
    print(f"全文: {full_content}")
    print(f"LLM总结: {llm_summary}")
