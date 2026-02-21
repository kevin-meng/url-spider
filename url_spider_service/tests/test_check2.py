import asyncio
from database import get_mysql_db, articles_collection
from sqlalchemy import text

db_gen = get_mysql_db()
mysql_db = next(db_gen)

# 查找没有评分的URL
scored_urls = set()
for doc in articles_collection.find({"pre_value_score": {"$gt": 0}}):
    scored_urls.add(doc.get("url"))

print(f"MongoDB 已评分 URL 数量: {len(scored_urls)}")

# 检查 MySQL 中 created_at < 2026-02-19 的数据有多少不在已评分列表中
query = text("""
    SELECT url, title, created_at
    FROM articles
    WHERE created_at < '2026-02-19'
    ORDER BY created_at DESC
    LIMIT 1000
""")
result = mysql_db.execute(query)
rows = result.fetchall()

unscored = 0
for row in rows:
    if row[0] not in scored_urls:
        unscored += 1

print(f"MySQL created_at < 2026-02-19 前1000条中，未评分: {unscored}")

# 找最早的未评分
query2 = text("""
    SELECT url, title, created_at
    FROM articles
    ORDER BY created_at ASC
    LIMIT 10
""")
result2 = mysql_db.execute(query2)
print("\n最早的10条数据:")
for row in result2:
    scored = "已评分" if row[0] in scored_urls else "未评分"
    print(f"  {row[2]} - {scored}")

mysql_db.close()
