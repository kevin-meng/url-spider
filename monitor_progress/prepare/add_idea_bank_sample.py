import sys
import os
import datetime

# 确保可以导入数据库模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from url_spider_service.database import articles_collection

def find_idea_bank_record():
    """查找包含点子库有值的MongoDB记录"""
    print("正在查找包含点子库有值的记录...")
    
    # 尝试不同的字段名来查找点子库相关记录
    possible_fields = ["idea_bank", "点子库", "ideas", "创意库"]
    
    for field in possible_fields:
        # 查找该字段存在且不为空的记录
        cursor = articles_collection.find(
            {field: {"$exists": True, "$ne": "", "$ne": []}}
        ).limit(1)
        
        record = next(cursor, None)
        if record:
            print(f"找到包含 '{field}' 字段的记录")
            return record, field
    
    # 如果没有找到，尝试查找包含"idea"或"点子"关键词的记录
    print("尝试查找包含'idea'或'点子'关键词的记录...")
    
    # 查找标题或内容中包含相关关键词的记录
    cursor = articles_collection.find({
        "$or": [
            {"title": {"$regex": "(idea|点子|创意)", "$options": "i"}},
            {"full_content": {"$regex": "(idea|点子|创意)", "$options": "i"}}
        ],
        "full_content": {"$exists": True, "$ne": ""}
    }).limit(1)
    
    record = next(cursor, None)
    if record:
        print("找到包含'idea'或'点子'关键词的记录")
        return record, "title/full_content"
    
    print("未找到包含点子库相关内容的记录")
    return None, None

def add_to_data_sample(record, field_name):
    """将找到的记录添加到data_sample.txt文件末尾"""
    if not record:
        print("无记录可添加")
        return
    
    output_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data_samples.txt"
    )
    
    print(f"正在将记录添加到 {output_file}...")
    
    with open(output_file, "a", encoding="utf-8") as f:
        f.write("\n" + "=" * 80 + "\n")
        f.write("MongoDB 点子库记录样本\n")
        f.write("=" * 80 + "\n")
        f.write(f"\n找到的记录包含 '{field_name}' 字段\n")
        f.write("\n样本详情:\n")
        
        # 处理记录，转换类型
        doc_copy = record.copy()
        if "_id" in doc_copy:
            doc_copy["_id"] = str(doc_copy["_id"])
        
        for key, value in doc_copy.items():
            # 处理datetime类型
            if isinstance(value, datetime.datetime):
                value = value.strftime("%Y-%m-%d %H:%M:%S")
            # 处理长文本
            elif isinstance(value, str) and len(value) > 100:
                value = value[:100] + "..."
            # 处理列表
            elif isinstance(value, list):
                if len(value) > 5:
                    value = value[:5] + ["..."]
                value = str(value)
            # 处理字典
            elif isinstance(value, dict):
                # 只显示前几个键值对
                if len(value) > 5:
                    value = {k: v for k, v in list(value.items())[:5]} 
                    value["..."] = "更多字段"
                value = str(value)
            
            f.write(f"  {key}: {value}\n")
    
    print("记录已成功添加到data_sample.txt文件末尾")

if __name__ == "__main__":
    record, field_name = find_idea_bank_record()
    add_to_data_sample(record, field_name)
