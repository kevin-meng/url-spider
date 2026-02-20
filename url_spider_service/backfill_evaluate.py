import asyncio
import sys
import os
import traceback
from datetime import datetime
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_mysql_db, articles_collection
from services.llm_service import LLMService

BATCH_SIZE = 50
TARGET_DATE = "2026-02-20"
CONCURRENCY = 5

async def process_batch(batch_data, llm_service, batch_num):
    batch_to_process = batch_data["items"]

    if not batch_to_process:
        return 0

    llm_input = [{"title": item["title"], "description": item["description"]} for item in batch_to_process]

    print(f"[批次{batch_num}] 调用LLM评估 {len(llm_input)} 篇文章...")
    evaluation_result = await llm_service.evaluate_articles(llm_input)

    evaluated_articles = evaluation_result.get("articles", [])

    for i, item in enumerate(batch_to_process):
        if i < len(evaluated_articles):
            eval_item = evaluated_articles[i]
            update_data = {
                "title": eval_item.get("title", item["title"]),
                "pre_value_score": eval_item.get("pre_value_score", 0),
                "article_type": eval_item.get("article_type", []),
                "pre_value_score_reason": eval_item.get("pre_value_score_reason", ""),
                "updated_at": datetime.now(),
            }
            articles_collection.update_one(
                {"url": item["url"]},
                {"$set": update_data},
                upsert=True
            )

    print(f"[批次{batch_num}] 完成 {len(batch_to_process)} 篇评估")
    return len(batch_to_process)

async def backfill_evaluate_parallel():
    print(f"=== 开始并行批量评估存量文章 (created_at < {TARGET_DATE}) ===")
    print(f"配置: BATCH_SIZE={BATCH_SIZE}, CONCURRENCY={CONCURRENCY}\n")

    llm_service = LLMService()

    db_gen = get_mysql_db()
    mysql_db = next(db_gen)

    offset = 0
    total_processed = 0
    empty_batch_count = 0

    try:
        while empty_batch_count < 5:
            batch_tasks = []
            batch_infos = []

            for i in range(CONCURRENCY):
                query = text(f"""
                    SELECT url, title, description, created_at
                    FROM articles
                    WHERE created_at < '{TARGET_DATE}'
                    ORDER BY created_at DESC
                    LIMIT {BATCH_SIZE} OFFSET {offset + i * BATCH_SIZE}
                """)

                result = mysql_db.execute(query)
                rows = result.fetchall()

                if not rows:
                    continue

                batch_to_process = []
                skip_count = 0
                for row in rows:
                    url = row[0]
                    title = row[1] or "无标题"
                    description = (row[2] or "")[:120]
                    created_at = row[3]

                    existing = articles_collection.find_one({"url": url})
                    if existing and existing.get("pre_value_score", 0) > 0:
                        skip_count += 1
                        continue

                    batch_to_process.append({
                        "url": url,
                        "title": title,
                        "description": description,
                        "created_at": created_at,
                    })

                if batch_to_process:
                    batch_tasks.append(process_batch({"items": batch_to_process}, llm_service, i + 1))
                    batch_infos.append((i + 1, len(batch_to_process), skip_count))
                else:
                    batch_infos.append((i + 1, 0, len(rows)))

            if not batch_tasks:
                empty_batch_count += 1
                offset += CONCURRENCY * BATCH_SIZE
                print(f"[偏移 {offset}] 连续{empty_batch_count}个批次为空，继续...")
                if empty_batch_count >= 5:
                    print("连续5个批次为空，可能没有更多数据了")
                    break
                continue

            empty_batch_count = 0

            for info in batch_infos:
                print(f"[批次{info[0]}] 待处理 {info[1]} 篇，跳过 {info[2]} 篇")

            results = await asyncio.gather(*batch_tasks)

            batch_total = sum(results)
            total_processed += batch_total
            offset += CONCURRENCY * BATCH_SIZE

            print(f"本轮完成 {batch_total} 篇，累计 {total_processed} 条\n")
            await asyncio.sleep(1)

    except Exception as e:
        print(f"主循环出错: {e}")
        traceback.print_exc()
    finally:
        mysql_db.close()

    print(f"=== 全部完成，共处理 {total_processed} 条 ===")

if __name__ == "__main__":
    asyncio.run(backfill_evaluate_parallel())
