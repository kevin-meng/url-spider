from database import articles_collection, get_mysql_db
from sqlalchemy import text
from datetime import datetime, timedelta

db_gen = get_mysql_db()
mysql_db = next(db_gen)

two_days_ago = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')

query = text(f"""
    SELECT a.url, a.title, a.description, COALESCE(f.mp_name, '') as mp_name
    FROM articles a
    LEFT JOIN feeds f ON a.mp_id = f.id
    WHERE a.updated_at >= '{two_days_ago}'
    ORDER BY a.updated_at DESC
    LIMIT 10
""")
result = mysql_db.execute(query)
rows = result.fetchall()

print(f"SQL 返回 {len(rows)} 条")
for row in rows:
    url = row[0]
    mp_name = row[3]
    
    existing = articles_collection.find_one({"url": url})
    
    print(f"\nURL: {url[:40]}...")
    print(f"  mp_name from SQL: [{mp_name}]")
    print(f"  existing in Mongo: {existing is not None}")
    if existing:
        print(f"  existing source: [{existing.get('source')}]")
        
        # 测试更新
        if not existing.get("source") and mp_name:
            articles_collection.update_one(
                {"url": url},
                {"$set": {"source": mp_name, "updated_at": datetime.now()}}
            )
            print(f"  -> Updated source to: [{mp_name}]")
        else:
            print(f"  -> Skipped (already has source or mp_name empty)")

mysql_db.close()

# 检查结果
print("\n\n=== 验证更新结果 ===")
docs = list(articles_collection.find({'source': {'$exists': True, '$ne': ''}}).limit(5))
print(f"有 source 的记录: {len(docs)} 条")
