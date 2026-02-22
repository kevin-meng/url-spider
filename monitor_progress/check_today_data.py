import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), '../url_spider_service'))

from database import engine, articles_collection
from sqlalchemy import text

def check_today_data():
    print("="*60)
    print("检查今天的数据情况")
    print("="*60)
    
    today = datetime.now()
    start_of_day = datetime(today.year, today.month, today.day)
    end_of_day = start_of_day + timedelta(days=1)
    
    print(f"\n检查日期范围: {start_of_day} 到 {end_of_day}")
    
    # MySQL 数据
    print("\n" + "="*60)
    print("MySQL 数据")
    print("="*60)
    
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
        print(f"今日更新账号数: {today_feeds}")
        print(f"今日新增文章数: {today_articles}")
    
    # MongoDB 数据
    print("\n" + "="*60)
    print("MongoDB 数据")
    print("="*60)
    
    mongo_articles = list(articles_collection.find({
        "created_at": {"$gte": start_of_day, "$lt": end_of_day}
    }))
    
    print(f"今日MongoDB文章数: {len(mongo_articles)}")
    
    if mongo_articles:
        preprocessed = len([a for a in mongo_articles if a.get("pre_value_score", 0) >= 1])
        full_content = len([a for a in mongo_articles if a.get("full_content")])
        llm_summary = len([a for a in mongo_articles if a.get("pre_value_score", 0) >= 3 and a.get("llm_summary_processed", False)])
        
        print(f"预加工文章数 (pre_value_score>=1): {preprocessed}")
        print(f"获取全文文章数: {full_content}")
        print(f"大模型总结文章数: {llm_summary}")
        
        # 显示前3条数据样本
        print("\n数据样本 (前3条):")
        for i, a in enumerate(mongo_articles[:3], 1):
            print(f"\n{i}. 标题: {a.get('title', '无标题')}")
            print(f"   评分: {a.get('pre_value_score')}")
            print(f"   类型: {a.get('article_type')}")
            print(f"   全文长度: {len(str(a.get('full_content', '')))}")
            print(f"   LLM处理: {a.get('llm_summary_processed')}")

if __name__ == "__main__":
    check_today_data()
