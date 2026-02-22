import sys
import os
from sqlalchemy import text

# 确保可以导入数据库模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from url_spider_service.database import get_mysql_db

def extract_feeds_structure():
    """提取MySQL feeds表结构"""
    print("正在提取MySQL feeds表结构...")
    db_gen = get_mysql_db()
    mysql_db = next(db_gen)
    
    try:
        # 获取表结构
        query = text("""
            SELECT column_name, data_type, column_default, is_nullable
            FROM information_schema.columns
            WHERE table_schema = DATABASE() AND table_name = 'feeds'
            ORDER BY ordinal_position
        """)
        result = mysql_db.execute(query)
        columns = result.fetchall()
        
        structure = []
        for column in columns:
            structure.append({
                "column_name": column[0],
                "data_type": column[1],
                "column_default": column[2],
                "is_nullable": column[3]
            })
        
        return structure
    finally:
        mysql_db.close()

def add_to_data_sample(structure):
    """将feeds表结构添加到data_sample.txt文件最前面"""
    if not structure:
        print("无表结构可添加")
        return
    
    output_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data_samples.txt"
    )
    
    print(f"正在读取 {output_file}...")
    
    # 读取现有文件内容
    with open(output_file, "r", encoding="utf-8") as f:
        existing_content = f.read()
    
    print("正在将feeds表结构添加到文件最前面...")
    
    # 构建feeds表结构内容
    feeds_content = "=" * 80 + "\n"
    feeds_content += "MySQL feeds 表结构\n"
    feeds_content += "=" * 80 + "\n"
    
    for column in structure:
        feeds_content += f"{column['column_name']}: {column['data_type']} (默认: {column['column_default']}, 可为空: {column['is_nullable']})\n"
    
    feeds_content += "\n"
    
    # 将feeds表结构添加到最前面
    new_content = feeds_content + existing_content
    
    # 写回文件
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print("feeds表结构已成功添加到data_sample.txt文件最前面")

if __name__ == "__main__":
    structure = extract_feeds_structure()
    add_to_data_sample(structure)
