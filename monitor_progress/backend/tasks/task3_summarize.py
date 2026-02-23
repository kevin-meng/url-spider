import asyncio
from sre_parse import MAX_UNTIL
import sys
import os
import signal
import time
from datetime import datetime, timedelta
import traceback

# Ensure we can import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import articles_collection
from services.llm_service import LLMService

# 配置
CONCURRENCY_SUMMARIZE = 5  # 总结并发数
TIMEOUT_HOURS = 1
TIMEOUT_MINUTES = 45
MAX_LENGTH = 10000


def timeout_handler(signum, frame):
    print(f"\n[超时] 任务运行超过 {TIMEOUT_HOURS}小时{TIMEOUT_MINUTES}分钟，自动终止")
    sys.exit(0)


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


async def process_article(article, llm_service, sem):
    url = article["url"]
    title = article.get("title", "无标题")
    score = article.get("pre_value_score", 0)

    try:
        print(f"任务 3: 正在总结 (评分: {score}) {title} ({url})")

        async with sem:
            full_markdown = article.get("full_markdown", "")
            if not full_markdown:
                full_markdown = article.get("full_content", "")

            if not full_markdown:
                print(f"任务 3: 跳过 {url} (无内容)")
                return

            # 预处理 markdown 内容，去除图片、链接和元数据
            processed_content = preprocess_markdown(full_markdown)

            # 限制内容长度，进一步节约 token
            max_length = MAX_LENGTH  # 可根据实际情况调整
            if len(processed_content) > max_length:
                processed_content = (
                    processed_content[:max_length] + "..."
                )  # 截断并添加省略号
                print(f"任务 3: 内容过长，已截断至 {max_length} 字符")

            result = await llm_service.process_content(processed_content)

            update_data = result
            update_data["llm_summary_processed"] = True
            update_data["updated_at"] = datetime.now()

            articles_collection.update_one(
                {"_id": article["_id"]}, {"$set": update_data}, upsert=True
            )
            print(f"任务 3: 已更新 (评分: {score}) {title} ({url})")

    except Exception as e:
        print(f"任务 3 处理 {url} 时出错: {e}")


async def task_summarize_content():
    print(f"[{datetime.now()}] 开始任务 3: 总结内容 (最近2天)")
    print(
        f"配置: CONCURRENCY_SUMMARIZE={CONCURRENCY_SUMMARIZE}, TIMEOUT={TIMEOUT_HOURS}h{TIMEOUT_MINUTES}m"
    )

    start_time = time.time()

    try:
        # Initialize LLM Service
        llm_service = LLMService()

        # Calculate date 2 days ago
        two_days_ago = datetime.now() - timedelta(days=2)

        # 信号量控制并发
        sem = asyncio.Semaphore(CONCURRENCY_SUMMARIZE)

        # 按评分从高到低处理 (10 到 3)
        for score in range(10, 2, -1):
            print(f"\n[评分优先级] 开始处理评分 {score} 的文章...")

            # 只处理过去2天内有内容的文章
            cursor = articles_collection.find(
                {
                    "updated_at": {"$gte": two_days_ago},
                    "pre_value_score": score,
                    "full_content": {"$exists": True, "$ne": ""},
                    "llm_summary_processed": {"$ne": True},
                }
            )

            articles = list(cursor)

            if not articles:
                print(f"任务 3: 没有评分 {score} 的文章需要总结。")
                continue

            print(f"任务 3: 正在总结 {len(articles)} 篇评分 {score} 的文章...")

            # 创建任务列表
            tasks = []
            for article in articles:
                tasks.append(process_article(article, llm_service, sem))

            # 并发执行
            await asyncio.gather(*tasks)

            # 检查超时
            elapsed = time.time() - start_time
            timeout_seconds = TIMEOUT_HOURS * 3600 + TIMEOUT_MINUTES * 60
            if elapsed > timeout_seconds:
                print(f"[超时] 已运行 {elapsed/3600:.2f} 小时，终止任务")
                return

    except Exception as e:
        print(f"任务 3 错误: {e}")
        traceback.print_exc()
    print(f"[{datetime.now()}] 任务 3 完成")


if __name__ == "__main__":
    # 设置超时处理
    signal.signal(signal.SIGALRM, timeout_handler)
    timeout_seconds = TIMEOUT_HOURS * 3600 + TIMEOUT_MINUTES * 60
    signal.alarm(timeout_seconds)

    asyncio.run(task_summarize_content())
