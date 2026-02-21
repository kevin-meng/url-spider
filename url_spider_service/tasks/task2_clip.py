import asyncio
import sys
import os
import signal
import time
from datetime import datetime, timedelta
import traceback

# Ensure we can import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import articles_collection
from services.clipper_service import ClipperService

# 配置
CONCURRENCY_CLIPPER = 4  # 剪藏并发数
TIMEOUT_HOURS = 1
TIMEOUT_MINUTES = 45


def timeout_handler(signum, frame):
    print(f"\n[超时] 任务运行超过 {TIMEOUT_HOURS}小时{TIMEOUT_MINUTES}分钟，自动终止")
    sys.exit(0)


async def process_article(article, clipper_service, clip_sem):
    url = article["url"]
    title = article.get("title", "无标题")

    try:
        print(f"任务 2: 正在剪藏 {title} ({url})")

        async with clip_sem:
            result = await clipper_service.process_url(url)

            if "error" in result:
                print(f"任务 2 错误 {title} ({url}): {result['error']}")
                return

            update_data = {
                "full_content": result.get("content", ""),
                "full_markdown": result.get("full_markdown", ""),
                "clipper_metadata": result.get("metadata", {}),
                "updated_at": datetime.now(),
            }

            articles_collection.update_one(
                {"_id": article["_id"]}, {"$set": update_data}, upsert=True
            )
            print(f"任务 2: 已更新 {title} ({url})")

    except Exception as e:
        print(f"任务 2 处理 {title} ({url}) 时出错: {e}")


async def task_clip_content():
    print(f"[{datetime.now()}] 开始任务 2: 剪藏内容 (最近2天)")
    print(
        f"配置: CONCURRENCY_CLIPPER={CONCURRENCY_CLIPPER}, TIMEOUT={TIMEOUT_HOURS}h{TIMEOUT_MINUTES}m"
    )

    start_time = time.time()

    try:
        # Initialize Clipper Service
        clipper_service = ClipperService()

        # Calculate date 2 days ago
        two_days_ago = datetime.now() - timedelta(days=2)

        # 修改查询条件：只处理过去2天内创建的记录
        cursor = articles_collection.find(
            {
                "created_at": {"$gte": two_days_ago},
                "$or": [{"full_content": {"$exists": False}}, {"full_content": ""}],
            }
        )

        articles = list(cursor)

        if not articles:
            print("任务 2: 没有文章需要剪藏。")
            return

        print(f"任务 2: 正在剪藏 {len(articles)} 篇文章...")

        # 信号量控制并发
        clip_sem = asyncio.Semaphore(CONCURRENCY_CLIPPER)

        # 创建任务列表
        tasks = []
        for article in articles:
            tasks.append(process_article(article, clipper_service, clip_sem))

        # 并发执行
        await asyncio.gather(*tasks)

        # 检查超时
        elapsed = time.time() - start_time
        timeout_seconds = TIMEOUT_HOURS * 3600 + TIMEOUT_MINUTES * 60
        if elapsed > timeout_seconds:
            print(f"[超时] 已运行 {elapsed/3600:.2f} 小时，终止任务")
            return

    except Exception as e:
        print(f"任务 2 错误: {e}")
        traceback.print_exc()
    print(f"[{datetime.now()}] 任务 2 完成")


if __name__ == "__main__":
    # 设置超时处理
    signal.signal(signal.SIGALRM, timeout_handler)
    timeout_seconds = TIMEOUT_HOURS * 3600 + TIMEOUT_MINUTES * 60
    signal.alarm(timeout_seconds)

    asyncio.run(task_clip_content())
