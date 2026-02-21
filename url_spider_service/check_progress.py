import sys
import os
from datetime import datetime

# Ensure we can import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import articles_collection

TARGET_DATE = "2026-02-22"


def check_progress():
    """检查处理进度"""
    print(f"=== 检查批量总结处理进度 (updated_at < {TARGET_DATE}) ===")
    print("=" * 80)

    # 计算目标日期
    target_datetime = datetime.strptime(TARGET_DATE, "%Y-%m-%d")

    # 按评分统计
    total_processed = 0
    total_pending = 0

    print("\n各评分处理情况:")
    print("-" * 80)

    # 从高分到低分检查
    for score in range(10, 2, -1):
        # 已处理数量
        processed_count = articles_collection.count_documents(
            {
                "updated_at": {"$lt": target_datetime},
                "pre_value_score": score,
                "full_content": {"$exists": True, "$ne": ""},
                "llm_summary_processed": True,
            }
        )

        # 未处理数量
        pending_count = articles_collection.count_documents(
            {
                "updated_at": {"$lt": target_datetime},
                "pre_value_score": score,
                "full_content": {"$exists": True, "$ne": ""},
                "llm_summary_processed": {"$ne": True},
            }
        )

        total_processed += processed_count
        total_pending += pending_count

        # 计算百分比
        total_for_score = processed_count + pending_count
        if total_for_score > 0:
            percent = (processed_count / total_for_score) * 100
            print(
                f"评分 {score}: 已处理 {processed_count} 篇, 未处理 {pending_count} 篇, 完成 {percent:.1f}%"
            )
        else:
            print(f"评分 {score}: 无满足条件的文章")

    print("-" * 80)
    print("\n总体处理情况:")
    print(f"已处理: {total_processed} 篇")
    print(f"未处理: {total_pending} 篇")
    print(f"总计: {total_processed + total_pending} 篇")

    if total_processed + total_pending > 0:
        overall_percent = (total_processed / (total_processed + total_pending)) * 100
        print(f"总体完成率: {overall_percent:.1f}%")

    print("\n=== 检查完成 ===")


if __name__ == "__main__":
    check_progress()
