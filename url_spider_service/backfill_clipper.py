import asyncio
import sys
import os
import traceback
from datetime import datetime
from sqlalchemy import text

# Ensure we can import from current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_mysql_db, articles_collection
from services.clipper_service import ClipperService

# 配置
CONCURRENCY_CLIPPER = 10  # 剪藏并发数
BATCH_SIZE = 50  # 每次从 MySQL 获取的文章数量
TARGET_DATE = "2026-02-24"  # 处理在此日期之前的文章


async def process_article(article, clipper_service, clip_sem):
    url = article["url"]
    title = article["title"]
    description = article["description"]

    try:
        # 1. 检查 MongoDB 是否已存在且有内容
        # 注意：这里的逻辑是 "只要有 url 且 full_content 不为空"，就认为已处理，可以跳过
        existing = articles_collection.find_one({"url": url})

        has_content = False
        if existing and existing.get("full_content"):
            has_content = True
            # print(f"[跳过] {title} ({url}) - 已有完整内容")
            return

        # 2. 如果不存在或无内容，准备处理
        if not existing:
            # 不存在，先插入基础信息
            doc = {
                "url": url,
                "title": title,
                "description": description,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }
            articles_collection.update_one({"url": url}, {"$set": doc}, upsert=True)
            # print(f"[同步] {title} ({url}) - 已存入 MongoDB")

        # 3. 执行剪藏
        print(f"[开始剪藏] {title} ({url})...")
        async with clip_sem:
            result = await clipper_service.process_url(url)
            if "error" in result:
                print(f"[剪藏失败] {title} ({url}): {result['error']}")
            else:
                update_data = {
                    "full_content": result.get("content", ""),
                    "full_markdown": result.get("full_markdown", ""),
                    "clipper_metadata": result.get("metadata", {}),
                    "updated_at": datetime.now(),
                }
                articles_collection.update_one({"url": url}, {"$set": update_data})
                print(f"[剪藏成功] {title} ({url})")

    except Exception as e:
        print(f"[错误] 处理 {title} ({url}) 时出错: {e}")


async def backfill_loop():
    print(f"=== 开始处理存量数据 (created_at < {TARGET_DATE}) - 仅剪藏，无评估 ===")

    # 初始化服务
    clipper_service = ClipperService()

    # 信号量控制并发
    clip_sem = asyncio.Semaphore(CONCURRENCY_CLIPPER)

    # 数据库连接
    db_gen = get_mysql_db()
    mysql_db = next(db_gen)

    offset = 0
    total_processed = 0

    try:
        while True:
            print(f"\n[批次] 获取第 {offset} - {offset + BATCH_SIZE} 条数据...")

            query = text(
                f"""
                SELECT url, title, description 
                FROM articles 
                WHERE created_at < '{TARGET_DATE}' 
                ORDER BY created_at  DESC
                LIMIT {BATCH_SIZE} OFFSET {offset}
            """
            )

            result = mysql_db.execute(query)
            rows = result.fetchall()

            if not rows:
                print("没有更多数据了，处理完成！")
                break

            tasks = []
            for row in rows:
                article = {
                    "url": row[0],
                    "title": row[1] or "无标题",
                    "description": (row[2] or "")[:120],
                }
                tasks.append(process_article(article, clipper_service, clip_sem))

            # 并发执行本批次
            await asyncio.gather(*tasks)

            processed_count = len(rows)
            total_processed += processed_count
            offset += processed_count

            print(f"本批次完成 {processed_count} 条，累计处理 {total_processed} 条。")

            # 简单的防封策略
            await asyncio.sleep(1)

            # if total_processed >= 50: # DEBUG LIMIT: Only run 1 batch for verification
            #     print("DEBUG: Reached limit of 50 items. Stopping backfill.")
            #     break

    except Exception as e:
        print(f"主循环出错: {e}")
        traceback.print_exc()
    finally:
        mysql_db.close()


if __name__ == "__main__":
    asyncio.run(backfill_loop())
