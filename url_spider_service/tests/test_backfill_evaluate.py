import asyncio
import sys
import os
import traceback
from datetime import datetime
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_mysql_db, articles_collection
from services.llm_service import LLMService

BATCH_SIZE = 20


async def test_single_batch():
    print(f"=== 测试批次: 从MySQL获取 {BATCH_SIZE} 条未评估文章 ===\n")

    llm_service = LLMService()

    db_gen = get_mysql_db()
    mysql_db = next(db_gen)

    try:
        # 从MySQL获取不在MongoDB中的文章
        query = text(
            """
            SELECT url, title, description, created_at
            FROM articles
            ORDER BY publish_time DESC
            LIMIT :limit
        """
        )
        result = mysql_db.execute(query, {"limit": BATCH_SIZE * 2})
        rows = result.fetchall()

        batch_to_process = []
        for row in rows:
            url = row[0]
            title = row[1] or "无标题"
            description = (row[2] or "")[:120]
            created_at = row[3]

            existing = articles_collection.find_one({"url": url})
            if existing and existing.get("pre_value_score", 0) > 0:
                continue

            batch_to_process.append(
                {
                    "url": url,
                    "title": title,
                    "description": description,
                    "created_at": created_at,
                }
            )

            if len(batch_to_process) >= BATCH_SIZE:
                break

        print(f"从MySQL获取到 {len(batch_to_process)} 条待评估文章\n")

        if not batch_to_process:
            print("没有需要评估的文章")
            return

        print(f"本批次: 待评估 {len(batch_to_process)} 篇\n")

        llm_input = [
            {"title": item["title"], "description": item["description"]}
            for item in batch_to_process
        ]

        print("=== 待评估的文章 ===")
        for i, item in enumerate(llm_input):
            print(f"{i+1}. {item['title'][:50]}...")
            print(f"   描述: {item['description'][:80]}...")
        print()

        print(f"[调用 LLM] 正在评估 {len(llm_input)} 篇文章...\n")
        evaluation_result = await llm_service.evaluate_articles(llm_input)

        print("=== LLM 返回结果 ===")
        print(evaluation_result)
        print()

        evaluated_articles = evaluation_result.get("articles", [])

        print("=== 评估结果详情 ===")
        for i, item in enumerate(batch_to_process):
            if i < len(evaluated_articles):
                eval_item = evaluated_articles[i]
                print(f"\n{i+1}. {item['title'][:40]}...")
                print(f"   评分: {eval_item.get('pre_value_score', 0)}")
                print(f"   类型: {eval_item.get('article_type', '')}")
                print(f"   原因: {eval_item.get('pre_value_score_reason', '')[:60]}...")

                update_data = {
                    "title": eval_item.get("title", item["title"]),
                    "pre_value_score": eval_item.get("pre_value_score", 0),
                    "article_type": eval_item.get("article_type", ""),
                    "pre_value_score_reason": eval_item.get(
                        "pre_value_score_reason", ""
                    ),
                    "updated_at": datetime.now(),
                }
                articles_collection.update_one(
                    {"url": item["url"]}, {"$set": update_data}, upsert=True
                )

        print("\n=== 测试完成 ===")

    except Exception as e:
        print(f"出错: {e}")
        traceback.print_exc()
    finally:
        mysql_db.close()


if __name__ == "__main__":
    asyncio.run(test_single_batch())
