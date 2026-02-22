import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), '../url_spider_service'))

from database import articles_collection

print("="*60)
print("检查高评分文章")
print("="*60)

today = datetime.now()
start_of_day = datetime(today.year, today.month, today.day)
end_of_day = start_of_day + timedelta(days=1)

# 先找所有 pre_value_score >=1 的文章
all_articles = list(articles_collection.find({
    "created_at": {"$gte": start_of_day, "$lt": end_of_day}
}))

print(f"\n今日总文章数: {len(all_articles)}")

# 统计不同评分的数量
score_counts = {}
for a in all_articles:
    score = a.get('pre_value_score', 0)
    score_counts[score] = score_counts.get(score, 0) + 1

print("\n评分分布:")
for score in sorted(score_counts.keys(), reverse=True):
    print(f"  {score}分: {score_counts[score]}篇")

# 找 pre_value_score >=3 的文章
high_score_articles = [a for a in all_articles if a.get('pre_value_score', 0) >= 3]
print(f"\npre_value_score >=3 的文章数: {len(high_score_articles)}")

if high_score_articles:
    print("\n前3篇高评分文章:")
    for i, a in enumerate(high_score_articles[:3], 1):
        print(f"\n{i}. 标题: {a.get('title', '无标题')}")
        print(f"   pre_value_score: {a.get('pre_value_score')}")
        print(f"   所有字段: {list(a.keys())}")
        print(f"   llm_summary_processed: {a.get('llm_summary_processed')}")
        print(f"   是否有'llm_summary_processed'字段: {'llm_summary_processed' in a}")
