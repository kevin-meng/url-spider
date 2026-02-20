import asyncio
import sys
import os
from datetime import datetime
import traceback

# Ensure we can import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import articles_collection
from services.clipper_service import ClipperService

async def task_clip_content():
    print(f"[{datetime.now()}] 开始任务 2: 剪藏内容 (全量模式)")
    try:
        # Initialize Clipper Service
        clipper_service = ClipperService()
        
        # 修改查询条件：移除 pre_value_score 限制，只查无内容的
        cursor = articles_collection.find({
            # "pre_value_score": {"$gt": 4}, # 暂时移除评分限制
            "$or": [
                {"full_content": {"$exists": False}},
                {"full_content": ""}
            ]
        }).limit(20) # 提高单次处理数量
        
        articles = list(cursor)
        
        if not articles:
            print("任务 2: 没有文章需要剪藏。")
            return

        print(f"任务 2: 正在剪藏 {len(articles)} 篇文章...")
        
        for article in articles:
            url = article["url"]
            title = article.get("title", "无标题")
            print(f"任务 2: 正在剪藏 {title} ({url})")
            
            result = await clipper_service.process_url(url)
            
            if "error" in result:
                print(f"任务 2 错误 {title} ({url}): {result['error']}")
                continue
            
            update_data = {
                "full_content": result.get("content", ""),
                "full_markdown": result.get("full_markdown", ""),
                "clipper_metadata": result.get("metadata", {}),
                "updated_at": datetime.now()
            }
            
            articles_collection.update_one(
                {"_id": article["_id"]},
                {"$set": update_data}
            )
            print(f"任务 2: 已更新 {title} ({url})")

    except Exception as e:
        print(f"任务 2 错误: {e}")
        traceback.print_exc()
    print(f"[{datetime.now()}] 任务 2 完成")

if __name__ == "__main__":
    asyncio.run(task_clip_content())
