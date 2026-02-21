import sys
import os
from sqlalchemy import text
from datetime import datetime
import traceback

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_mysql_db, articles_collection

BATCH_SIZE = 100

def update_mongo_from_mysql():
    print(f"[{datetime.now()}] 开始从MySQL同步数据到MongoDB")
    
    db_gen = get_mysql_db()
    mysql_db = next(db_gen)
    
    total_updated = 0
    offset = 0
    
    try:
        while True:
            query = text(f"""
                SELECT a.url, a.mp_id, COALESCE(f.mp_name, '') as source, a.publish_time
                FROM articles a
                LEFT JOIN feeds f ON a.mp_id = f.id
                ORDER BY a.id
                LIMIT {BATCH_SIZE} OFFSET {offset}
            """)
            result = mysql_db.execute(query)
            rows = result.fetchall()
            
            if not rows:
                print(f"[完成] 共更新 {total_updated} 条记录")
                break
            
            updated_count = 0
            for row in rows:
                url = row[0]
                mp_id = row[1]
                source = row[2] if row[2] else ""
                publish_time = row[3]
                
                if not url:
                    continue
                
                update_data = {
                    "mp_id": mp_id,
                    "source": source,
                    "updated_at": datetime.now()
                }
                
                if publish_time:
                    update_data["publish_time"] = publish_time
                
                result = articles_collection.update_one(
                    {"url": url},
                    {"$set": update_data}
                    ,upsert=True
                )
                
                if result.modified_count > 0:
                    updated_count += 1
            
            total_updated += updated_count
            offset += len(rows)
            
            print(f"[进度] 已处理 {offset} 条，更新 {updated_count} 条，累计 {total_updated} 条")
            
    except Exception as e:
        print(f"错误: {e}")
        traceback.print_exc()
    finally:
        mysql_db.close()
    
    print(f"[{datetime.now()}] 同步完成，共更新 {total_updated} 条记录")

if __name__ == "__main__":
    update_mongo_from_mysql()
