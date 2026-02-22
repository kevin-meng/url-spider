import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../url_spider_service'))

from database import articles_collection

print("="*60)
print("检查是否有任何文章包含 LLM 字段")
print("="*60)

# 查找所有包含任意 LLM 相关字段的文章
llm_related_fields = ['llm_summary_processed', 'llm_summary', 'reason', 'socre', 'score', 'tags', '概要', '四精练', '原则库']

print("\n正在查找包含 LLM 字段的文章...")

# 先找10篇文章，看看它们的字段
sample_articles = list(articles_collection.find().limit(20))

print(f"\n找到 {len(sample_articles)} 篇样例文章")
print("\n检查它们的字段:")

for i, a in enumerate(sample_articles, 1):
    print(f"\n{i}. 标题: {a.get('title', '无标题')}")
    fields = list(a.keys())
    llm_fields = [f for f in llm_related_fields if f in fields]
    if llm_fields:
        print(f"   ✓ 包含 LLM 字段: {llm_fields}")
        if 'llm_summary_processed' in a:
            print(f"   llm_summary_processed: {a.get('llm_summary_processed')}")
        if 'reason' in a:
            print(f"   reason 长度: {len(str(a.get('reason', '')))}")
    else:
        print(f"   ✗ 不包含 LLM 字段")

# 现在统计有多少文章有这些字段
print("\n" + "="*60)
print("统计有 LLM 字段的文章数量")
print("="*60)

for field in llm_related_fields:
    count = articles_collection.count_documents({field: {"$exists": True}})
    print(f"{field}: {count} 篇")
