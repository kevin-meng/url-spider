# 数据提取过程说明

## 1. 提取内容

- MySQL 表结构
- MySQL 数据样本 (5条)
- MongoDB 集合结构
- MongoDB 数据样本 (5条)

## 2. 提取方法

### MySQL 表结构
使用 SQL 查询从 information_schema.columns 获取 articles 表的结构信息：

```sql
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_schema = DATABASE() AND table_name = 'articles'
ORDER BY ordinal_position
```

### MySQL 数据样本
提取5条字段不为空的数据：

```sql
SELECT * FROM articles WHERE title IS NOT NULL AND title != '' AND url IS NOT NULL AND url != '' ORDER BY created_at DESC LIMIT 5
```

### MongoDB 集合结构
通过分析一个完整的文档来推断集合结构

### MongoDB 数据样本
提取5条有完整内容的文档：

```python
cursor = articles_collection.find(
    {"full_content": {"$exists": True, "$ne": ""}},
    limit=5
)
```

## 3. 结果文件

- `data_samples.txt`: 包含表结构和数据样本
- `extract_process.md`: 提取过程说明

## 4. 技术细节

- 使用 SQLAlchemy 连接 MySQL
- 使用 PyMongo 连接 MongoDB
- 处理 datetime 类型，转换为字符串格式
- 对于 MongoDB 的 ObjectId 类型，转换为字符串
- 对于长文本字段，只显示前100个字符

## 5. 运行方法

```bash
cd /Users/kevin/obsidian_notes/url_spider/new/monitor_progress/prepare/
python extract_data.py
```
