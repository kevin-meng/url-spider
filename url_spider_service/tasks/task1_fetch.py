import asyncio
import sys
import os
import signal
import time
from sqlalchemy import text
from datetime import datetime, timedelta
import traceback

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_mysql_db, articles_collection
from services.llm_service import LLMService

CONCURRENCY = 5
LLM_BATCH_SIZE = 50
TIMEOUT_HOURS = 1
TIMEOUT_MINUTES = 45

def timeout_handler(signum, frame):
    print(f"\n[超时] 任务运行超过 {TIMEOUT_HOURS}小时{TIMEOUT_MINUTES}分钟，自动终止")
    sys.exit(0)

async def process_batch(batch_data, llm_service, batch_num):
    batch_to_process = batch_data["items"]

    if not batch_to_process:
        return 0

    llm_input = [{"title": item["title"], "description": item["description"][:120]} for item in batch_to_process]

    print(f"[批次{batch_num}] LLM调用 {len(llm_input)} 篇...")
    evaluation_result = await llm_service.evaluate_articles(llm_input)

    evaluated_articles = evaluation_result.get("articles", [])

    saved_count = 0
    for i, eval_item in enumerate(evaluated_articles):
        if i < len(batch_to_process):
            original = batch_to_process[i]

            doc = {
                "url": original["url"],
                "title": eval_item.get("title", original["title"]),
                "description": original["description"],
                "source": original.get("source", ""),  # 添加 source 字段
                "mp_id": original.get("mp_id", ""),  # 添加 mp_id 字段
                "publish_time": original.get("publish_time", ""),  # 添加 publish_time 字段
                "pre_value_score": eval_item.get("pre_value_score", 0),
                "article_type": eval_item.get("article_type", []),
                "pre_value_score_reason": eval_item.get("pre_value_score_reason", ""),
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }

            articles_collection.update_one(
                {"url": original["url"]},
                {"$set": doc},
                upsert=True
            )
            saved_count += 1

    print(f"[批次{batch_num}] 完成 {saved_count} 篇评估")
    return saved_count

async def task_fetch_and_evaluate():
    print(f"[{datetime.now()}] 开始任务 1: 获取并评估文章 (并发模式)")
    print(f"配置: CONCURRENCY={CONCURRENCY}, LLM_BATCH_SIZE={LLM_BATCH_SIZE}, TIMEOUT={TIMEOUT_HOURS}h{TIMEOUT_MINUTES}m")

    start_time = time.time()

    try:
        llm_service = LLMService()

        db_gen = get_mysql_db()
        mysql_db = next(db_gen)

        two_days_ago = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')

        offset = 0
        total_processed = 0
        empty_round_count = 0

        try:
            while True:
                # 1. 准备 CONCURRENCY 个批次
                batches_to_submit = []

                for batch_idx in range(CONCURRENCY):
                    current_batch = []

                    # 每个批次内部：循环拉取直到凑满 50 条
                    while len(current_batch) < LLM_BATCH_SIZE:
                        query = text(f"""
                            SELECT a.url, a.title, a.description, COALESCE(f.mp_name, ''),a.mp_id,a.publish_time
                            FROM articles a
                            LEFT JOIN feeds f ON a.mp_id = f.id
                            WHERE a.updated_at >= '{two_days_ago}'
                            ORDER BY a.updated_at DESC
                            LIMIT 50 OFFSET {offset}
                        """)
                        result = mysql_db.execute(query)
                        rows = result.fetchall()

                        if not rows:
                            break

                        for row in rows:
                            url = row[0]
                            title = row[1]
                            description = row[2]
                            mp_name = row[3] if row[3] else ""  # 从 feeds 表关联来的 mp_name
                            mp_id = row[4] if row[4] else ""  # 从 articles 表关联来的 mp_id
                            publish_time = row[5] if row[5] else ""  # 从 articles 表关联来的 publish_time

                            existing = articles_collection.find_one({"url": url})
                            # 如果已存在记录，需要更新 source 字段（即使已有评分也要更新）
                            if existing:
                                # 检查是否需要更新 source 字段
                                if existing.get("source"):
                                    continue  # 已有 source 字段，跳过
                                # 没有 source 字段，更新它
                                articles_collection.update_one(
                                    {"url": url},
                                    {"$set": {"source": mp_name, "updated_at": datetime.now()}}
                                    ,upsert=True
                                )
                                continue

                            current_batch.append({
                                "title": title or "无标题",
                                "description": (description or ""),
                                "url": url,
                                "source": mp_name,  # 添加 source 字段
                                "mp_id": mp_id,  # 添加 mp_id 字段
                                "publish_time": publish_time
                            })

                            if len(current_batch) >= LLM_BATCH_SIZE:
                                break

                        offset += len(rows)

                        if len(rows) < 50:
                            break

                    if current_batch:
                        batches_to_submit.append({
                            "items": current_batch[:LLM_BATCH_SIZE],
                            "batch_num": batch_idx + 1
                        })

                if not batches_to_submit:
                    empty_round_count += 1
                    print(f"[偏移 {offset}] 连续{empty_round_count}轮为空，任务完成")
                    # if empty_round_count >= 3:
                    #     print("连续3轮无新数据，退出")
                    #     break
                    continue

                empty_round_count = 0

                # 2. 并发提交所有批次到 LLM
                print(f"[并发] 同时提交 {len(batches_to_submit)} 个批次，每个 {LLM_BATCH_SIZE} 条")
                tasks = [
                    process_batch({"items": batch["items"]}, llm_service, batch["batch_num"])
                    for batch in batches_to_submit
                ]
                results = await asyncio.gather(*tasks)

                batch_total = sum(results)
                total_processed += batch_total

                print(f"[进度] 本轮完成 {batch_total} 篇，累计 {total_processed} 条\n")

                # 3. 检查超时
                elapsed = time.time() - start_time
                timeout_seconds = TIMEOUT_HOURS * 3600 + TIMEOUT_MINUTES * 60
                if elapsed > timeout_seconds:
                    print(f"[超时] 已运行 {elapsed/3600:.2f} 小时，终止任务")
                    break

                await asyncio.sleep(1)

        finally:
            mysql_db.close()

    except Exception as e:
        print(f"任务 1 错误: {e}")
        traceback.print_exc()
    print(f"[{datetime.now()}] 任务 1 完成，共处理 {total_processed} 条")

if __name__ == "__main__":
    signal.signal(signal.SIGALRM, timeout_handler)
    timeout_seconds = TIMEOUT_HOURS * 3600 + TIMEOUT_MINUTES * 60
    signal.alarm(timeout_seconds)

    asyncio.run(task_fetch_and_evaluate())
