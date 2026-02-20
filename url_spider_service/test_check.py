import asyncio
import sys
import os
from datetime import datetime
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_mysql_db, articles_collection
from services.llm_service import LLMService

BATCH_SIZE = 20
CONCURRENCY = 2
TARGET_DATE = "2026-02-19"

async def test():
    print(f"=== 测试前几批数据 ===")
    db_gen = get_mysql_db()
    mysql_db = next(db_gen)

    for offset in [0, 50, 100, 150]:
        query = text(f"""
            SELECT url, title, description, created_at
            FROM articles
            WHERE created_at < '{TARGET_DATE}'
            ORDER BY created_at DESC
            LIMIT {BATCH_SIZE} OFFSET {offset}
        """)

        result = mysql_db.execute(query)
        rows = result.fetchall()

        if not rows:
            print(f"offset {offset}: 无数据")
            continue

        need_process = 0
        for row in rows:
            url = row[0]
            title = row[1]
            existing = articles_collection.find_one({"url": url})
            if existing and existing.get("pre_value_score", 0) > 0:
                continue
            need_process += 1

        print(f"offset {offset}: 总数 {len(rows)}, 需要处理 {need_process}")

    mysql_db.close()

asyncio.run(test())
