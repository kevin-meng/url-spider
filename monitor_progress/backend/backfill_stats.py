#!/usr/bin/env python3
import os
import sys
from datetime import datetime, timedelta

# 添加项目路径，让脚本能够找到 stats_calculator 模块
sys.path.append(os.path.dirname(__file__))

from stats_calculator import (
    create_tables,
    calculate_daily_stats,
    save_daily_stats,
    calculate_heatmap_stats,
    calculate_monthly_stats,
)


def backfill_date_stats(target_date_str):
    """补指定日期的统计数据"""
    try:
        # 解析目标日期
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
        print(f"开始补 {target_date_str} 的统计数据...")

        # 创建表（如果不存在）
        print("创建/检查统计表...")
        create_tables()

        # 计算并保存每日统计
        print(f"计算 {target_date_str} 的每日统计...")
        daily_stats = calculate_daily_stats(target_date)
        save_daily_stats(daily_stats)
        print(f"每日统计已保存: {daily_stats}")

        # 计算热力图统计
        print(f"计算 {target_date_str} 的热力图统计...")
        calculate_heatmap_stats(target_date, "pre_value_score")
        calculate_heatmap_stats(target_date, "score")
        print("热力图统计已保存")

        # 计算月度统计（包含目标日期所在的月份）
        print("计算月度统计...")
        calculate_monthly_stats()
        print("月度统计已保存")

        print(f"{target_date_str} 的统计数据补数完成！")

    except Exception as e:
        print(f"补数失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # 补 2 月 23 号的数据
    backfill_date_stats("2026-02-23")
