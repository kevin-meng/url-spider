import asyncio
import sys
import os
import signal
import time
from datetime import datetime, timedelta
import traceback

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_mysql_db, articles_collection
from services.feishu_writer import save_articles_batch

TIMEOUT_HOURS = 1
TIMEOUT_MINUTES = 30


def timeout_handler(signum, frame):
    print(f"\n[超时] 任务运行超过 {TIMEOUT_HOURS}小时{TIMEOUT_MINUTES}分钟，自动终止")
    sys.exit(0)


async def task_sync_to_feishu():
    print(f"[{datetime.now()}] 开始任务 5: 同步文章到飞书多维表格")

    start_time = time.time()

    try:
        # 获取昨天的日期
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)

        yesterday_start = int(yesterday.timestamp())
        yesterday_end = int(today.timestamp())

        print(
            f"查询日期范围: {yesterday.strftime('%Y-%m-%d')} - {today.strftime('%Y-%m-%d')}"
        )
        print(f"时间戳范围: {yesterday_start} - {yesterday_end}")

        # 查询昨天的所有评分8-10的文章
        query = {
            "socre": {"$in": ["8", "9", "10"]},
            "publish_time": {"$gte": yesterday_start, "$lt": yesterday_end},
        }

        projection = {
            "_id": 0,
            "url": 1,
            "title": 1,
            "article_type": 1,
            "socre": 1,
            "reason": 1,
            "相关问题": 1,
            "publish_time": 1,
            "created_at": 1,
            "source": 1,
        }

        articles = list(articles_collection.find(query, projection))

        if not articles:
            print(f"未找到符合条件的文章")
            return 0

        # 按文章类型排序
        articles.sort(
            key=lambda x: (
                x.get("article_type", [""])[0]
                if isinstance(x.get("article_type"), list) and x.get("article_type")
                else x.get("article_type", "")
            )
        )

        print(f"找到 {len(articles)} 篇评分8-10的文章")

        # 格式化时间
        for article in articles:
            if article.get("publish_time"):
                publish_time = article.get("publish_time")
                if isinstance(publish_time, int):
                    article["publish_time"] = datetime.fromtimestamp(
                        publish_time
                    ).strftime("%Y-%m-%d %H:%M:%S")
                elif isinstance(publish_time, datetime):
                    article["publish_time"] = publish_time.strftime("%Y-%m-%d %H:%M:%S")
            if article.get("created_at"):
                created_at = article.get("created_at")
                if isinstance(created_at, int):
                    article["created_at"] = datetime.fromtimestamp(created_at).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                elif isinstance(created_at, datetime):
                    article["created_at"] = created_at.strftime("%Y-%m-%d %H:%M:%S")

        # 批量写入飞书
        print(f"开始写入飞书多维表格...")
        result = save_articles_batch(articles)

        print(
            f"[{datetime.now()}] 任务 5 完成，成功 {result['success']}, 失败 {result['fail']}"
        )
        return result["success"]

    except Exception as e:
        print(f"任务 5 错误: {e}")
        traceback.print_exc()
        return 0


if __name__ == "__main__":
    signal.signal(signal.SIGALRM, timeout_handler)
    timeout_seconds = TIMEOUT_HOURS * 3600 + TIMEOUT_MINUTES * 60
    signal.alarm(timeout_seconds)

    asyncio.run(task_sync_to_feishu())
