#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../url_spider_service"))

from database import engine
from sqlalchemy import text


def add_fields():
    """添加新字段"""
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE daily_stats ADD COLUMN today_mongo_articles_count INT DEFAULT 0"))
            conn.commit()
            print("✓ today_mongo_articles_count字段添加成功")
        except Exception as e:
            print(f"today_mongo_articles_count字段可能已存在: {e}")
            conn.rollback()
        
        try:
            conn.execute(text("ALTER TABLE daily_stats ADD COLUMN high_score_articles INT DEFAULT 0"))
            conn.commit()
            print("✓ high_score_articles字段添加成功")
        except Exception as e:
            print(f"high_score_articles字段可能已存在: {e}")
            conn.rollback()
    
    print("\n字段检查完成！")


if __name__ == "__main__":
    add_fields()
