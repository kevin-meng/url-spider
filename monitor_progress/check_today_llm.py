import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), '../url_spider_service'))

from database import articles_collection

print("="*60)
print("检查今天创建的文章的 LLM 处理情况")
print("="*60)

today = datetime.now()
start_of_day = datetime(today.year, today.month, today.day)
end_of_day = start_of_day + timedelta(days=1)

print(f"\n日期范围: {start_of_day} 到 {end_of_day}")

# 查找今天创建的文章
today_articles = list(articles_collection.find({
    "created_at": {"$gte": start_of_day, "$lt": end_of_day}
}))

print(f"\n今日创建的文章总数: {len(today_articles)}")

# 统计今天创建的文章中，有 LLM 字段的数量
llm_processed_today = [a for a in today_articles if a.get("llm_summary_processed") is True]
has_llm_field_today = [a for a in today_articles if "llm_summary_processed" in a]
high_score_today = [a for a in today_articles if a.get("pre_value_score", 0) >= 3]

print(f"\n今日文章统计:")
print(f"  pre_value_score >=3: {len(high_score_today)} 篇")
print(f"  有 llm_summary_processed 字段: {len(has_llm_field_today)} 篇")
print(f"  llm_summary_processed = True: {len(llm_processed_today)} 篇")

if len(high_score_today) > 0:
    print(f"\n前5篇高评分的今日文章:")
    for i, a in enumerate(high_score_today[:5], 1):
        print(f"\n{i}. 标题: {a.get('title', '无标题')}")
        print(f"   pre_value_score: {a.get('pre_value_score')}")
        print(f"   created_at: {a.get('created_at')}")
        print(f"   有 llm_summary_processed 字段: {'llm_summary_processed' in a}")
        if 'llm_summary_processed' in a:
            print(f"   llm_summary_processed 值: {a.get('llm_summary_processed')}")
