#!/usr/bin/env python3
from database import engine
from sqlalchemy import text

def recreate_table():
    print("删除旧的daily_stats表...")
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS daily_stats"))
        conn.commit()
    
    print("重新创建所有表...")
    from models import Base
    Base.metadata.create_all(bind=engine)
    
    print("表重新创建完成！")

if __name__ == "__main__":
    recreate_table()
