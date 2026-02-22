#!/usr/bin/env python3
from database import engine, Base
from models import Feed, Article, DailyStats, MpMonthlyStats, ArticleTypeScoreStats

def init_database():
    print("开始创建数据库表...")
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    print("数据库表创建完成！")
    print("已创建的表：")
    print("- feeds")
    print("- articles")
    print("- daily_stats")
    print("- mp_monthly_stats")
    print("- article_type_score_stats")

if __name__ == "__main__":
    init_database()
