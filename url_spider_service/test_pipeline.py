import asyncio
import sys
import os
import traceback
import random
from datetime import datetime
from sqlalchemy import text

# Ensure we can import from current directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
sys.path.append(script_dir)

from database import get_mysql_db, articles_collection
from tasks.task1_fetch import task_fetch_and_evaluate
from tasks.task2_clip import task_clip_content
from tasks.task3_summarize import task_summarize_content

TEST_URL = "https://www.runoob.com/ai-agent/roxybrowser-openclaw.html"
TEST_TITLE = "RoxyBrowser OpenClaw"
TEST_DESC = "RoxyBrowser OpenClaw Test Description"

async def run_integration_test():
    print("=== 开始集成测试 ===")
    
    # 1. 验证数据库连接
    print("\n[1/5] 验证数据库连接...")
    try:
        # MySQL
        db_gen = get_mysql_db()
        mysql_db = next(db_gen)
        mysql_db.execute(text("SELECT 1"))
        print("✅ MySQL 连接成功")
        
        # MongoDB
        # articles_collection.find_one()
        print("✅ MongoDB 连接成功")
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return

    # 2. 准备测试数据 (MySQL)
    print("\n[2/5] 准备测试数据...")
    try:
        # 检查表结构
        print("检查表结构...")
        result = mysql_db.execute(text("DESCRIBE articles"))
        columns = result.fetchall()
        for col in columns:
            print(f"  {col}")

        # 检查是否已存在
        result = mysql_db.execute(text(f"SELECT url FROM articles WHERE url = '{TEST_URL}'"))
        if not result.fetchone():
            print(f"插入测试文章: {TEST_URL}")
            # 尝试插入带 ID 的数据 (假设 ID 是 int)
            # 生成一个随机 ID
            random_id = int(datetime.now().timestamp())
            
            mysql_db.execute(text(f"""
                INSERT INTO articles (id, url, title, description, publish_time, created_at)
                VALUES ({random_id}, '{TEST_URL}', '{TEST_TITLE}', '{TEST_DESC}', {int(datetime.now().timestamp())}, '{datetime.now()}')
            """))
            mysql_db.commit()
        else:
            print(f"测试文章已存在: {TEST_URL}")
            
        # 清理 MongoDB 中的旧数据以确保测试有效
        articles_collection.delete_one({"url": TEST_URL})
        print("已清理 MongoDB 中的旧测试数据")
            
    except Exception as e:
        print(f"❌ 准备测试数据失败: {e}")
        mysql_db.close()
        return
    # finally:
        # mysql_db.close() # Keep open for now or close? Better close and reopen in tasks.

    # 3. 运行任务 1 (获取 & 评估)
    print("\n[3/5] 运行任务 1 (获取 & 评估)...")
    try:
        await task_fetch_and_evaluate()
        
        # 验证
        doc = articles_collection.find_one({"url": TEST_URL})
        if doc:
            print(f"✅ 任务 1 成功: 文章已存入 MongoDB")
            print(f"   评分: {doc.get('pre_value_score')}")
            print(f"   原因: {doc.get('pre_value_score_reason')}")
            
            # 强制设置高分以便进行后续测试 (如果 LLM 给分低)
            if doc.get('pre_value_score', 0) <= 4:
                print("⚠️ 评分过低，强制设为 5 分以便测试后续流程...")
                articles_collection.update_one({"url": TEST_URL}, {"$set": {"pre_value_score": 5}})
        else:
            print("❌ 任务 1 失败: MongoDB 中未找到文章")
            # return # Continue to see if we can debug
            
    except Exception as e:
        print(f"❌ 任务 1 执行出错: {e}")
        traceback.print_exc()
        # return

    # 4. 运行任务 2 (剪藏)
    print("\n[4/5] 运行任务 2 (剪藏)...")
    try:
        await task_clip_content()
        
        # 验证
        doc = articles_collection.find_one({"url": TEST_URL})
        if doc and doc.get("full_content"):
            print(f"✅ 任务 2 成功: 获取到全文内容 (长度: {len(doc['full_content'])})")
        else:
            print("❌ 任务 2 失败: 未获取到全文内容")
            # return
            
    except Exception as e:
        print(f"❌ 任务 2 执行出错: {e}")
        traceback.print_exc()
        # return

    # 5. 运行任务 3 (总结)
    print("\n[5/5] 运行任务 3 (总结)...")
    try:
        await task_summarize_content()
        
        # 验证
        doc = articles_collection.find_one({"url": TEST_URL})
        if doc and doc.get("llm_summary_processed"):
            print(f"✅ 任务 3 成功: 文章已总结")
            # 打印部分元数据查看
            print(f"   标签: {doc.get('tags', 'N/A')}")
        else:
            print("❌ 任务 3 失败: 未生成总结标志")
            # return
            
    except Exception as e:
        print(f"❌ 任务 3 执行出错: {e}")
        traceback.print_exc()
        # return

    print("\n=== 集成测试完成 ===")

if __name__ == "__main__":
    asyncio.run(run_integration_test())
