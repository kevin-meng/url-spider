import asyncio
import sys
import os
import traceback
from datetime import datetime, timedelta
import time

# Ensure we can import from parent directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import articles_collection
from services.llm_service import LLMService

# 配置
CONCURRENCY = 20  # 并发数（提高并发以加快处理速度）
TARGET_DATE = "2026-02-20"  # 处理在此日期之前的文章
MAX_LENGTH = 10000  # 内容最大长度

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
    """处理单篇文章"""
    url = article["url"]
    title = article.get("title", "无标题")
    score = article.get("pre_value_score", 0)

    try:
        print(f"[处理] 正在总结 (评分: {score}) {title} ({url})")

        async with sem:
            full_markdown = article.get("full_markdown", "")
            if not full_markdown:
                full_markdown = article.get("full_content", "")

            if not full_markdown:
                print(f"[跳过] {url} (无内容)")
                return False

            # 预处理 markdown 内容，去除图片、链接和元数据
            processed_content = preprocess_markdown(full_markdown)

            # 限制内容长度，进一步节约 token
            if len(processed_content) > MAX_LENGTH:
                processed_content = (
                    processed_content[:MAX_LENGTH] + "..."
                )  # 截断并添加省略号
                print(f"[截断] 内容过长，已截断至 {MAX_LENGTH} 字符")

            result = await llm_service.process_content(processed_content)

            update_data = result
            update_data["llm_summary_processed"] = True
            update_data["updated_at"] = datetime.now()

            articles_collection.update_one(
                {"_id": article["_id"]}, {"$set": update_data}, upsert=True
            )
            print(f"[完成] 已更新 (评分: {score}) {title} ({url})")
            return True

    except Exception as e:
        print(f"[错误] 处理 {url} 时出错: {e}")
        return False


async def process_articles(score, articles, llm_service, sem):
    """处理多篇文章"""
    if not articles:
        return 0

    print(f"[处理] 开始处理评分 {score} 的 {len(articles)} 篇文章...")

    tasks = []
    for article in articles:
        tasks.append(process_article(article, llm_service, sem))

    results = await asyncio.gather(*tasks)

    success_count = sum(results)
    print(f"[处理] 完成评分 {score} 的 {success_count} 篇文章")
    return success_count


async def backfill_summarize():
    """批量回刷历史数据"""
    print(f"=== 开始批量总结存量文章 (created_at < {TARGET_DATE}) ===")
    print(f"配置: CONCURRENCY={CONCURRENCY}\n")

    start_time = time.time()

    try:
        # Initialize LLM Service
        llm_service = LLMService()

        # 信号量控制并发
        sem = asyncio.Semaphore(CONCURRENCY)

        # 按评分从高到低处理 (10 到 3)
        for score in range(10, 2, -1):
            print(f"\n[评分优先级] 开始处理评分 {score} 的文章...")

            # 计算当前评分的总待处理数量
            target_datetime = datetime.strptime(TARGET_DATE, "%Y-%m-%d")
            total_pending = articles_collection.count_documents(
                {
                    "updated_at": {"$lt": target_datetime},  # 改成更新时间updated_at
                    "pre_value_score": score,
                    "full_content": {"$exists": True, "$ne": ""},
                    "llm_summary_processed": {"$ne": True},
                }
            )

            if total_pending == 0:
                print(f"[评分{score}] 没有需要处理的文章")
                continue

            print(f"[评分{score}] 总计需要处理 {total_pending} 篇文章")

            # 循环处理当前评分的所有文章
            total_processed = 0
            while True:
                # 查找评分等于当前分数且未处理的文章
                cursor = articles_collection.find(
                    {
                        "created_at": {"$lt": target_datetime},
                        "pre_value_score": score,
                        "full_content": {"$exists": True, "$ne": ""},
                        "llm_summary_processed": {"$ne": True},
                    }
                ).limit(
                    CONCURRENCY
                )  # 每次查询并发数篇文章

                articles = list(cursor)

                if not articles:
                    print(f"[评分{score}] 处理完成！")
                    break

                batch_size = len(articles)
                print(
                    f"[评分{score}] 处理批次: {total_processed + 1}-{min(total_processed + batch_size, total_pending)}/{total_pending}"
                )

                # 直接处理所有文章（每篇单独处理，并发执行）
                processed_count = await process_articles(
                    score, articles, llm_service, sem
                )
                total_processed += processed_count

                print(
                    f"[评分{score}] 进度: {total_processed}/{total_pending} ({(total_processed/total_pending*100):.1f}%)"
                )

                # 简单的防封策略
                await asyncio.sleep(1)

    except Exception as e:
        print(f"[错误] 主循环出错: {e}")
        traceback.print_exc()

    print(f"=== 全部完成 ===")


if __name__ == "__main__":
    asyncio.run(backfill_summarize())
