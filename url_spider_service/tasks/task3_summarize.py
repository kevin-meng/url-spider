import asyncio
import sys
import os
from datetime import datetime
import traceback

# Ensure we can import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import articles_collection
from services.llm_service import LLMService

async def task_summarize_content():
    print(f"[{datetime.now()}] 开始任务 3: 总结内容")
    try:
        # Initialize LLM Service
        llm_service = LLMService()
        
        cursor = articles_collection.find({
            "pre_value_score": {"$gt": 4},
            "full_content": {"$exists": True, "$ne": ""},
            "llm_summary_processed": {"$ne": True}
        }).limit(20) # 提高单次处理数量
        
        articles = list(cursor)
        
        if not articles:
            print("任务 3: 没有文章需要总结。")
            return

        print(f"任务 3: 正在总结 {len(articles)} 篇文章...")
        
        for article in articles:
            url = article["url"]
            print(f"任务 3: 正在总结 {url}")
            
            full_markdown = article.get("full_markdown", "")
            if not full_markdown:
                full_markdown = article.get("full_content", "")
            
            if not full_markdown:
                continue

            result = await llm_service.process_content(full_markdown)
            
            update_data = result
            update_data["llm_summary_processed"] = True
            update_data["updated_at"] = datetime.now()
            
            articles_collection.update_one(
                {"_id": article["_id"]},
                {"$set": update_data}
            )
            print(f"任务 3: 已更新 {url}")

    except Exception as e:
        print(f"任务 3 错误: {e}")
        traceback.print_exc()
    print(f"[{datetime.now()}] 任务 3 完成")

if __name__ == "__main__":
    asyncio.run(task_summarize_content())
