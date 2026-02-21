import asyncio
import sys
import os
import datetime
from sqlalchemy import text

# Ensure we can import from current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_mysql_db, articles_collection

# 配置
TARGET_DATE = "2026-02-20"  # 处理在此日期之前的文章

def check_clip_progress():
    """检查剪藏进度"""
    print(f"=== 检查剪藏处理进度 (created_at < {TARGET_DATE}) ===")
    print("=" * 80)

    try:
        # 1. 统计 MySQL 中的文章总数
        print("\n1. 统计 MySQL 中的文章数量...")
        db_gen = get_mysql_db()
        mysql_db = next(db_gen)
        
        # 统计 MySQL 中满足条件的文章总数
        mysql_query = text(f"""
            SELECT COUNT(*) 
            FROM articles 
            WHERE created_at < '{TARGET_DATE}' 
        """)
        mysql_result = mysql_db.execute(mysql_query)
        mysql_count = mysql_result.scalar()
        
        print(f"MySQL 中待处理文章总数: {mysql_count} 篇")
        
        # 2. 统计 MongoDB 中的状态
        print("\n2. 统计 MongoDB 中的处理状态...")
        
        # 已剪藏（有 full_content）
        clipped_count = articles_collection.count_documents({
            "full_content": {"$exists": True, "$ne": ""}
        })
        
        # 已存在但未剪藏（无 full_content）
        exists_but_not_clipped = articles_collection.count_documents({
            "$or": [
                {"full_content": {"$not": {"$exists": True}}},
                {"full_content": ""}
            ]
        })
        
        # 3. 计算各种统计数据
        print("\n3. 剪藏进度统计:")
        print("-" * 80)
        print(f"MySQL 中总文章数: {mysql_count} 篇")
        print(f"MongoDB 中已剪藏: {clipped_count} 篇")
        print(f"MongoDB 中存在但未剪藏: {exists_but_not_clipped} 篇")
        print(f"MongoDB 中总文章数: {clipped_count + exists_but_not_clipped} 篇")
        
        # 计算剪藏率
        if mysql_count > 0:
            clip_rate = (clipped_count / mysql_count) * 100
            print(f"\n剪藏完成率: {clip_rate:.1f}%")
            print(f"剩余未剪藏: {mysql_count - clipped_count} 篇")
        else:
            print("\nMySQL 中无满足条件的文章")
        
        # 4. 按日期统计（最近7天）
        print("\n4. 最近7天剪藏趋势:")
        print("-" * 80)
        
        for i in range(7, 0, -1):
            date = (datetime.datetime.now() - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            next_date = (datetime.datetime.now() - datetime.timedelta(days=i-1)).strftime("%Y-%m-%d")
            
            # 统计当天剪藏的文章数
            daily_count = articles_collection.count_documents({
                "full_content": {"$exists": True, "$ne": ""},
                "updated_at": {
                    "$gte": datetime.datetime.strptime(date, "%Y-%m-%d"),
                    "$lt": datetime.datetime.strptime(next_date, "%Y-%m-%d")
                }
            })
            
            print(f"{date}: 剪藏 {daily_count} 篇")
        
        # 5. 剪藏失败统计
        print("\n5. 剪藏失败统计:")
        print("-" * 80)
        
        # 统计有错误标记的文章
        failed_count = articles_collection.count_documents({
            "clipper_error": {"$exists": True, "$ne": ""}
        })
        
        print(f"剪藏失败的文章数: {failed_count} 篇")
        
        print("\n" + "=" * 80)
        print("=== 检查完成 ===")
        
    except Exception as e:
        print(f"检查过程中出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'mysql_db' in locals():
            mysql_db.close()

if __name__ == "__main__":
    check_clip_progress()
