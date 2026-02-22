import sys
import os
from sqlalchemy import text

# 确保可以导入数据库模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from url_spider_service.database import get_mysql_db

def add_earliest_update_time_field():
    """给feeds表添加earliest_update_time字段"""
    print("正在给feeds表添加earliest_update_time字段...")
    db_gen = get_mysql_db()
    mysql_db = next(db_gen)
    
    try:
        # 执行ALTER TABLE语句添加新字段
        query = text("""
            ALTER TABLE feeds 
            ADD COLUMN earliest_update_time DATETIME DEFAULT NULL COMMENT '账号最早更新时间'
        """)
        mysql_db.execute(query)
        mysql_db.commit()
        
        print("成功添加earliest_update_time字段")
        
        # 验证字段是否添加成功
        verify_query = text("""
            SELECT column_name, data_type, column_default, is_nullable
            FROM information_schema.columns
            WHERE table_schema = DATABASE() AND table_name = 'feeds' AND column_name = 'earliest_update_time'
        """)
        result = mysql_db.execute(verify_query)
        column = result.fetchone()
        
        if column:
            print(f"字段验证成功: {column[0]} - {column[1]} (默认: {column[2]}, 可为空: {column[3]})")
        else:
            print("字段验证失败")
            
    except Exception as e:
        print(f"添加字段时出错: {e}")
        mysql_db.rollback()
    finally:
        mysql_db.close()

def update_data_sample():
    """更新data_sample.txt文件中的feeds表结构"""
    print("正在更新data_sample.txt文件中的feeds表结构...")
    
    # 先提取最新的feeds表结构
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
        
    finally:
        mysql_db.close()
    
    if not structure:
        print("无法获取最新的feeds表结构")
        return
    
    # 读取现有文件内容
    output_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data_samples.txt"
    )
    
    with open(output_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # 查找feeds表结构的开始和结束位置
    start_position = -1
    end_position = -1
    
    for i, line in enumerate(lines):
        if "MySQL feeds 表结构" in line:
            start_position = i
        elif start_position != -1 and "MySQL feeds 表数据样本" in line:
            end_position = i
            break
    
    if start_position == -1:
        print("未找到feeds表结构")
        return
    
    if end_position == -1:
        end_position = len(lines)
    
    # 构建新的feeds表结构内容
    new_feeds_structure = [
        "=" * 80 + "\n",
        "MySQL feeds 表结构\n",
        "=" * 80 + "\n"
    ]
    
    for column in structure:
        new_feeds_structure.append(f"{column['column_name']}: {column['data_type']} (默认: {column['column_default']}, 可为空: {column['is_nullable']})\n")
    
    new_feeds_structure.append("\n")
    
    # 替换旧的feeds表结构
    new_lines = lines[:start_position] + new_feeds_structure + lines[end_position:]
    
    # 写回文件
    with open(output_file, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    
    print("成功更新data_sample.txt文件中的feeds表结构")

if __name__ == "__main__":
    add_earliest_update_time_field()
    update_data_sample()
