import sys
import os

# 确保可以导入数据库模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import articles_collection

# 查询测试文章
print("查询数据库中的测试文章...")

# 查找评分9的已处理文章
articles = list(
    articles_collection.find(
        {"pre_value_score": {"$gt": 3}, "llm_summary_processed": True}
    )
)

print(f"找到 {len(articles)} 篇测试文章:")
print("=" * 100)

for i, article in enumerate(articles):
    print(f"\n文章 {i+1}:")
    print("-" * 80)

    # 打印所有字段键值对
    for key, value in article.items():
        print(f"🤔{key}--->")
        print(f"{value}"[:40])
        print("=" * 80)

    print("-" * 80)

# 检查是否有任何文章被处理过
processed_articles = [
    article for article in articles if article.get("llm_summary_processed", False)
]
print(f"\n已处理的文章数量: {len(processed_articles)}")
print(f"未处理的文章数量: {len(articles) - len(processed_articles)}")
