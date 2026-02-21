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
    
    # 创建测试数据（不同评分的文章）
    test_articles = []
    
    # 评分从 10 到 3
    for score in range(10, 2, -1):
        test_articles.append(
            {
                "url": f"https://example.com/test{score}",
                "title": f"测试文章 (评分: {score})",
                "description": f"测试文章描述 (评分: {score})",
                "created_at": datetime.now() - timedelta(days=1),
                "updated_at": datetime.now() - timedelta(days=1),
                "pre_value_score": score,
                "full_content": f"这是测试文章的完整内容 (评分: {score})",
                "llm_summary_processed": False
            }
        )
    
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
        print(f"[测试] 文章: {article['title']} (评分: {article['pre_value_score']})")
        print(f"[测试] 是否已处理: {article.get('llm_summary_processed', False)}")
        print(f"[测试] 是否有总结: {'llm_summary' in article and article['llm_summary'] != ''}")
        if 'llm_summary' in article:
            print(f"[测试] 总结长度: {len(article['llm_summary'])}")
        print()

async def test_task3_summarize():
    """测试 task3_summarize.py"""
    print(f"[{datetime.now()}] 开始测试 task3_summarize.py")
    
    try:
        # 设置测试数据
        await setup_test_data()
        
        # 运行总结任务
        print("[测试] 运行总结任务...")
        
        # 动态导入 task_summarize_content 函数
        import importlib.util
        import sys
        
        # 导入 task3_summarize 模块
        spec = importlib.util.spec_from_file_location(
            "task3_summarize",
            os.path.join(os.path.dirname(__file__), "task3_summarize.py")
        )
        task3_summarize = importlib.util.module_from_spec(spec)
        sys.modules["task3_summarize"] = task3_summarize
        spec.loader.exec_module(task3_summarize)
        
        # 运行总结任务
        await task3_summarize.task_summarize_content()
        
        # 验证测试结果
        await verify_test_results()
        
        print("[测试] 测试完成！")
        
    except Exception as e:
        print(f"[测试] 测试错误: {e}")
        traceback.print_exc()
    
    print(f"[{datetime.now()}] 测试结束")

if __name__ == "__main__":
    asyncio.run(test_task3_summarize())
