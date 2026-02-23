#!/usr/bin/env python3
"""
任务4：计算统计数据
功能：计算每日统计、月度统计和热力图统计
"""

import os
import sys
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stats_calculator import (
    create_tables,
    calculate_daily_stats,
    save_daily_stats,
    calculate_monthly_stats,
    calculate_heatmap_stats
)


def task_calculate_stats():
    """计算统计数据任务"""
    print(f"[{datetime.now()}] 开始执行统计数据计算任务...")
    
    try:
        # 创建表
        print(f"[{datetime.now()}] 创建/检查统计表...")
        create_tables()
        
        # 计算今天和昨天的统计
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        
        for date in [yesterday, today]:
            print(f"[{datetime.now()}] 计算 {date.date()} 的每日统计...")
            daily_stats = calculate_daily_stats(date)
            save_daily_stats(daily_stats)
            
            print(f"[{datetime.now()}] 计算 {date.date()} 的热力图统计...")
            calculate_heatmap_stats(date, "pre_value_score")
            calculate_heatmap_stats(date, "score")
        
        # 计算月度统计
        print(f"[{datetime.now()}] 计算月度统计...")
        calculate_monthly_stats()
        
        print(f"[{datetime.now()}] 统计数据计算任务执行完成！")
        return True
        
    except Exception as e:
        print(f"[{datetime.now()}] 统计数据计算任务执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    task_calculate_stats()
