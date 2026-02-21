from database import articles_collection, get_mysql_db
from sqlalchemy import text
from datetime import datetime, timedelta
import json

db_gen = get_mysql_db()
mysql_db = next(db_gen)

two_days_ago = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')

query = text(f"""
    SELECT a.url, a.title, COALESCE(f.mp_name, '') as mp_name
    FROM articles a
    LEFT JOIN feeds f ON a.mp_id = f.id
    WHERE a.updated_at >= '{two_days_ago}'
    ORDER BY a.updated_at DESC
    LIMIT 5
""")
result = mysql_db.execute(query)
rows = result.fetchall()

print(f"SQL 返回 {len(rows)} 条")

updated_count = 0
for row in rows:
    url = row[0]
    title = row[1]
    mp_name = row[2]
    
    existing = articles_collection.find_one({"url": url})
    
    print(f"\n处理: {title[:30]}...")
    print(f"  URL: {url[:40]}...")
    print(f"  SQL mp_name: [{mp_name}]")
    
    if not existing:
        print(f"  -> MongoDB 中不存在，创建新记录")
        # 创建新记录
        doc = {
            "url": url,
            "title": title,
            "source": mp_name,
            "pre_value_score": 0,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        articles_collection.insert_one(doc)
        updated_count += 1
    else:
        print(f"  -> MongoDB 中已存在")
        print(f"     当前 source: [{existing.get('source')}]")
        
        if not existing.get("source") and mp_name:
            # 更新 source 字段
            articles_collection.update_one(
                {"url": url},
                {"$set": {"source": mp_name, "updated_at": datetime.now()}}
            )
            print(f"     -> 已更新 source 为: [{mp_name}]")
            updated_count += 1
        else:
            print(f"     -> 跳过")

mysql_db.close()

print(f"\n\n=== 更新了 {updated_count} 条记录 ===")

# 验证
with_source = articles_collection.count_documents({'source': {'$exists': True, '$ne': ''}})
print(f"有 source 的记录总数: {with_source}")
