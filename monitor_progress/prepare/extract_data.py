import sys
import os
import json
from datetime import datetime
from sqlalchemy import text

# 确保可以导入数据库模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from url_spider_service.database import get_mysql_db, articles_collection

def extract_mysql_structure():
    """提取MySQL表结构"""
    print("正在提取MySQL表结构...")
    db_gen = get_mysql_db()
    mysql_db = next(db_gen)
    
    try:
        # 获取表结构
        query = text("""
            SELECT column_name, data_type, column_default, is_nullable
            FROM information_schema.columns
            WHERE table_schema = DATABASE() AND table_name = 'articles'
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

def extract_mysql_sample():
    """提取MySQL数据样本"""
    print("正在提取MySQL数据样本...")
    db_gen = get_mysql_db()
    mysql_db = next(db_gen)
    
    try:
        # 提取5条数据，优先选择字段不为空的
        query = text("""
            SELECT * FROM articles 
            WHERE title IS NOT NULL AND title != '' 
              AND url IS NOT NULL AND url != ''
            ORDER BY created_at DESC
            LIMIT 5
        """)
        result = mysql_db.execute(query)
        rows = result.fetchall()
        
        # 获取列名
        columns = result.keys()
        
        samples = []
        for row in rows:
            sample = {}
            for i, column in enumerate(columns):
                value = row[i]
                # 处理datetime类型
                if isinstance(value, datetime):
                    sample[column] = value.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    sample[column] = value
            samples.append(sample)
        
        return samples
    finally:
        mysql_db.close()

def extract_mongodb_structure():
    """提取MongoDB集合结构（通过分析样本数据）"""
    print("正在提取MongoDB集合结构...")
    
    # 获取一个文档作为结构参考
    sample_doc = articles_collection.find_one({"full_content": {"$exists": True, "$ne": ""}})
    
    if not sample_doc:
        return {}
    
    structure = {}
    for key, value in sample_doc.items():
        structure[key] = type(value).__name__
    
    return structure

def extract_mongodb_sample():
    """提取MongoDB数据样本"""
    print("正在提取MongoDB数据样本...")
    
    # 提取5条数据，优先选择字段不为空的
    cursor = articles_collection.find(
        {"full_content": {"$exists": True, "$ne": ""}},
        limit=5
    )
    
    samples = []
    for doc in cursor:
        # 处理ObjectId
        doc_copy = doc.copy()
        if "_id" in doc_copy:
            doc_copy["_id"] = str(doc_copy["_id"])
        # 处理datetime类型
        for key, value in doc_copy.items():
            if isinstance(value, datetime):
                doc_copy[key] = value.strftime("%Y-%m-%d %H:%M:%S")
        samples.append(doc_copy)
    
    return samples

def save_results():
    """保存提取的结果"""
    # 提取数据
    mysql_structure = extract_mysql_structure()
    mysql_samples = extract_mysql_sample()
    mongodb_structure = extract_mongodb_structure()
    mongodb_samples = extract_mongodb_sample()
    
    # 保存到文本文件
    output_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data_samples.txt"
    )
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("MySQL 表结构\n")
        f.write("=" * 80 + "\n")
        for column in mysql_structure:
            f.write(f"{column['column_name']}: {column['data_type']} (默认: {column['column_default']}, 可为空: {column['is_nullable']})\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("MySQL 数据样本 (5条)\n")
        f.write("=" * 80 + "\n")
        for i, sample in enumerate(mysql_samples, 1):
            f.write(f"\n样本 {i}:\n")
            for key, value in sample.items():
                f.write(f"  {key}: {value}\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("MongoDB 集合结构\n")
        f.write("=" * 80 + "\n")
        for key, value_type in mongodb_structure.items():
            f.write(f"{key}: {value_type}\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("MongoDB 数据样本 (5条)\n")
        f.write("=" * 80 + "\n")
        for i, sample in enumerate(mongodb_samples, 1):
            f.write(f"\n样本 {i}:\n")
            for key, value in sample.items():
                # 对于长文本，只显示前100个字符
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                f.write(f"  {key}: {value}\n")
    
    print(f"数据已保存到: {output_file}")
    
    # 保存过程文档
    process_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "extract_process.md"
    )
    
    with open(process_file, "w", encoding="utf-8") as f:
        f.write("# 数据提取过程说明\n\n")
        f.write("## 1. 提取内容\n\n")
        f.write("- MySQL 表结构\n")
        f.write("- MySQL 数据样本 (5条)\n")
        f.write("- MongoDB 集合结构\n")
        f.write("- MongoDB 数据样本 (5条)\n\n")
        
        f.write("## 2. 提取方法\n\n")
        f.write("### MySQL 表结构\n")
        f.write("使用 SQL 查询从 information_schema.columns 获取 articles 表的结构信息：\n\n")
        f.write("```sql\n")
        f.write("SELECT column_name, data_type, column_default, is_nullable\n")
        f.write("FROM information_schema.columns\n")
        f.write("WHERE table_schema = DATABASE() AND table_name = 'articles'\n")
        f.write("ORDER BY ordinal_position\n")
        f.write("```\n\n")
        
        f.write("### MySQL 数据样本\n")
        f.write("提取5条字段不为空的数据：\n\n")
        f.write("```sql\n")
        f.write("SELECT * FROM articles WHERE title IS NOT NULL AND title != '' AND url IS NOT NULL AND url != '' ORDER BY created_at DESC LIMIT 5\n")
        f.write("```\n\n")
        
        f.write("### MongoDB 集合结构\n")
        f.write("通过分析一个完整的文档来推断集合结构\n\n")
        
        f.write("### MongoDB 数据样本\n")
        f.write("提取5条有完整内容的文档：\n\n")
        f.write("```python\n")
        f.write("cursor = articles_collection.find(\n")
        f.write("    {\"full_content\": {\"$exists\": True, \"$ne\": \"\"}},\n")
        f.write("    limit=5\n")
        f.write(")\n")
        f.write("```\n\n")
        
        f.write("## 3. 结果文件\n\n")
        f.write("- `data_samples.txt`: 包含表结构和数据样本\n")
        f.write("- `extract_process.md`: 提取过程说明\n\n")
        
        f.write("## 4. 技术细节\n\n")
        f.write("- 使用 SQLAlchemy 连接 MySQL\n")
        f.write("- 使用 PyMongo 连接 MongoDB\n")
        f.write("- 处理 datetime 类型，转换为字符串格式\n")
        f.write("- 对于 MongoDB 的 ObjectId 类型，转换为字符串\n")
        f.write("- 对于长文本字段，只显示前100个字符\n\n")
        
        f.write("## 5. 运行方法\n\n")
        f.write("```bash\n")
        f.write("cd /Users/kevin/obsidian_notes/url_spider/new/monitor_progress/prepare/\n")
        f.write("python extract_data.py\n")
        f.write("```\n")
    
    print(f"过程文档已保存到: {process_file}")

if __name__ == "__main__":
    save_results()
