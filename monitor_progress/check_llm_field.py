import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), '../url_spider_service'))

from database import articles_collection

print("="*60)
print("检查 LLM 字段")
print("="*60)

today = datetime.now()
start_of_day = datetime(today.year, today.month, today.day)
end_of_day = start_of_day + timedelta(days=1)

mongo_articles = list(articles_collection.find({
    "created_at": {"$gte": start_of_day, "$lt": end_of_day}
}).limit(10))

print(f"\n找到 {len(mongo_articles)} 篇文章")
print("\n前3篇文章的所有字段:")

for i, a in enumerate(mongo_articles[:3], 1):
    print(f"\n{i}. 标题: {a.get('title', '无标题')}")
    print(f"   所有字段: {list(a.keys())}")
    print(f"   pre_value_score: {a.get('pre_value_score')}")
    print(f"   llm_summary_processed: {a.get('llm_summary_processed')}")
    print(f"   是否有'socre'字段: {'socre' in a}")
    print(f"   是否有'score'字段: {'score' in a}")
    
    # 检查 pre_value_score >=3 的文章
    if a.get('pre_value_score', 0) >= 3:
        print(f"   ✓ pre_value_score >=3")
        print(f"   llm_summary_processed 值: {a.get('llm_summary_processed')}")
