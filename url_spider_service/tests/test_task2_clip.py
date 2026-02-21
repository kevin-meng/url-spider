import asyncio
import sys
import os
from datetime import datetime, timedelta
import traceback

# Ensure we can import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import articles_collection

async def setup_test_data():
    """设置测试数据"""
    print("[测试] 设置测试数据...")
    
    # 清除现有的测试数据
    await asyncio.to_thread(
        articles_collection.delete_many,
        {"title": {"$regex": "^测试文章"}}
    )
    
    # 创建测试数据（过去两天内的文章，无完整内容）
    test_articles = [
        {
            "url": "https://example.com/test1",
            "title": "测试文章 1",
            "description": "测试文章描述 1",
            "created_at": datetime.now() - timedelta(days=1),
            "updated_at": datetime.now() - timedelta(days=1)
        },
        {
            "url": "https://example.com/test2",
            "title": "测试文章 2",
            "description": "测试文章描述 2",
            "created_at": datetime.now() - timedelta(days=1.5),
            "updated_at": datetime.now() - timedelta(days=1.5)
        },
        {
            "url": "https://example.com/test3",
            "title": "测试文章 3",
            "description": "测试文章描述 3",
            "created_at": datetime.now() - timedelta(days=0.5),
            "updated_at": datetime.now() - timedelta(days=0.5)
        }
    ]
    
    # 插入测试数据
    for article in test_articles:
        await asyncio.to_thread(
            articles_collection.update_one,
            {"url": article["url"]},
            {"$set": article},
            upsert=True
        )
    
    print("[测试] 测试数据设置完成")

async def verify_test_results():
    """验证测试结果"""
    print("[测试] 验证测试结果...")
    
    # 查询测试文章
    test_articles = await asyncio.to_thread(
        articles_collection.find,
        {"title": {"$regex": "^测试文章"}}
    )
    
    articles_list = await asyncio.to_thread(list, test_articles)
    
    print(f"[测试] 找到 {len(articles_list)} 篇测试文章")
    
    for article in articles_list:
        print(f"[测试] 文章: {article['title']} ({article['url']})")
        print(f"[测试] 创建时间: {article['created_at']}")
        print(f"[测试] 是否有完整内容: {'full_content' in article and article['full_content'] != ''}")
        if 'full_content' in article:
            print(f"[测试] 完整内容长度: {len(article['full_content'])}")
        print()

async def test_task2_clip():
    """测试 task2_clip.py"""
    print(f"[{datetime.now()}] 开始测试 task2_clip.py")
    
    try:
        # 设置测试数据
        await setup_test_data()
        
        # 运行剪藏任务
        print("[测试] 运行剪藏任务...")
        
        # 动态导入 task_clip_content 函数
        import importlib.util
        import sys
        
        # 导入 task2_clip 模块
        spec = importlib.util.spec_from_file_location(
            "task2_clip",
            os.path.join(os.path.dirname(__file__), "task2_clip.py")
        )
        task2_clip = importlib.util.module_from_spec(spec)
        sys.modules["task2_clip"] = task2_clip
        spec.loader.exec_module(task2_clip)
        
        # 运行剪藏任务
        await task2_clip.task_clip_content()
        
        # 验证测试结果
        await verify_test_results()
        
        print("[测试] 测试完成！")
        
    except Exception as e:
        print(f"[测试] 测试错误: {e}")
        traceback.print_exc()
    
    print(f"[{datetime.now()}] 测试结束")

if __name__ == "__main__":
    asyncio.run(test_task2_clip())
