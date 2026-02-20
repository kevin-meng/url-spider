import asyncio
import sys
import os
from sqlalchemy import text
from datetime import datetime
import traceback

# Ensure we can import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_mysql_db, articles_collection
# from services.llm_service import LLMService # 暂时禁用 LLM

async def task_fetch_and_evaluate():
    print(f"[{datetime.now()}] 开始任务 1: 获取文章 (同步模式 - 跳过评估)")
    try:
        # Initialize LLM Service
        # llm_service = LLMService()
        
        # 1. Fetch from MySQL
        db_gen = get_mysql_db()
        mysql_db = next(db_gen)
        
        try:
            # Using raw SQL
            print("正在从 MySQL 获取最新文章...")
            result = mysql_db.execute(text("SELECT url, title, description FROM articles ORDER BY publish_time DESC LIMIT 200"))
            rows = result.fetchall()
            
            batch_to_process = []
            
            for row in rows:
                url = row[0]
                title = row[1]
                description = row[2]
                
                # Check Mongo
                if articles_collection.find_one({"url": url}):
                    continue
                
                batch_to_process.append({
                    "title": title or "无标题",
                    "description": (description or "")[:120],
                    "url": url
                })
                
                if len(batch_to_process) >= 20:
                    break
            
            if not batch_to_process:
                print("任务 1: 没有新文章需要处理。")
                return

            print(f"任务 1: 正在同步 {len(batch_to_process)} 篇文章...")
            
            # Skip LLM Evaluation, just insert into Mongo
            for item in batch_to_process:
                url = item["url"]
                title = item["title"]
                description = item["description"]
                
                doc = {
                    "url": url,
                    "title": title,
                    "description": description,
                    "pre_value_score": 0, # 默认 0 分
                    "article_type": [],
                    "pre_value_score_reason": "未评估 (同步模式)",
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
                
                articles_collection.update_one(
                    {"url": url},
                    {"$set": doc},
                    upsert=True
                )
                print(f"任务 1: 已同步 {title} ({url})")

        finally:
            mysql_db.close()
            
    except Exception as e:
        print(f"任务 1 错误: {e}")
        traceback.print_exc()
    print(f"[{datetime.now()}] 任务 1 完成")

if __name__ == "__main__":
    asyncio.run(task_fetch_and_evaluate())
