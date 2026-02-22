import sys
import os
from datetime import datetime
from sqlalchemy import text

# 确保可以导入数据库模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from url_spider_service.database import get_mysql_db

def extract_feeds_sample():
    """提取MySQL feeds表数据样本"""
    print("正在提取MySQL feeds表数据样本...")
    db_gen = get_mysql_db()
    mysql_db = next(db_gen)
    
    try:
        # 先查询feeds表的列名
        query = text("""
            SELECT column_name 
            FROM information_schema.columns
            WHERE table_schema = DATABASE() AND table_name = 'feeds'
            ORDER BY ordinal_position
        """)
        result = mysql_db.execute(query)
        columns = [row[0] for row in result.fetchall()]
        
        print(f"feeds表的列名: {columns}")
        
        # 直接提取最新的一条数据
        query = text("""
            SELECT * FROM feeds 
            ORDER BY created_at DESC
            LIMIT 1
        """)
        result = mysql_db.execute(query)
        row = result.fetchone()
        
        if not row:
            print("feeds表中无数据")
            return None
        
        # 获取列名
        columns = result.keys()
        
        # 构建样本数据
        sample = {}
        for i, column in enumerate(columns):
            value = row[i]
            # 处理datetime类型
            if isinstance(value, datetime):
                sample[column] = value.strftime("%Y-%m-%d %H:%M:%S")
            else:
                sample[column] = value
        
        return sample
    finally:
        mysql_db.close()

def add_to_data_sample(sample):
    """将feeds表数据样本添加到data_sample.txt文件中feeds表结构后面"""
    if not sample:
        print("无样本数据可添加")
        return
    
    output_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data_samples.txt"
    )
    
    print(f"正在读取 {output_file}...")
    
    # 读取现有文件内容
    with open(output_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    print("正在查找feeds表结构位置...")
    
    # 查找feeds表结构结束的位置
    insert_position = 0
    for i, line in enumerate(lines):
        if "MySQL feeds 表结构" in line:
            # 找到feeds表结构标题，从这里开始查找结束位置
            for j in range(i, len(lines)):
                if line.strip() == "=" * 80 and j > i:
                    insert_position = j + 1
                    break
            break
    
    if insert_position == 0:
        # 如果没找到，就添加到文件最前面
        insert_position = 0
    
    print(f"找到插入位置: 第 {insert_position} 行")
    print("正在添加feeds表数据样本...")
    
    # 构建feeds表数据样本内容
    feeds_sample_content = [
        "\nMySQL feeds 表数据样本 (1条)\n",
        "=" * 80 + "\n",
        "\n样本 1:\n"
    ]
    
    for key, value in sample.items():
        feeds_sample_content.append(f"  {key}: {value}\n")
    
    feeds_sample_content.append("\n")
    
    # 在找到的位置插入内容
    new_lines = lines[:insert_position] + feeds_sample_content + lines[insert_position:]
    
    # 写回文件
    with open(output_file, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    
    print("feeds表数据样本已成功添加到data_sample.txt文件中")

if __name__ == "__main__":
    sample = extract_feeds_sample()
    add_to_data_sample(sample)
