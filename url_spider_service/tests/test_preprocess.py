import re

def preprocess_markdown(content):
    """预处理 markdown 内容，去除图片、链接和元数据，节约 token"""
    if not content:
        return content
    
    # 1. 去除元数据（YAML front matter）
    content = re.sub(r'^---[\s\S]*?---\n', '', content)
    
    # 2. 去除图片（包括复杂的 SVG 图片）
    # 匹配 ![]() 格式的图片，包括包含特殊字符的情况
    content = re.sub(r'!\[.*?\]\([^)]*\)', '', content)
    # 额外处理可能的残留 SVG 内容（包括 URL 编码的情况）
    content = re.sub(r"' fill='[^']*'>.*?</svg>", '', content)
    # 处理 URL 编码的 SVG 残留内容
    content = re.sub(r"' fill='[^']*'%3E.*?%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E\)", '', content)
    
    # 3. 去除链接，保留链接文本
    # 处理有文本的链接 [text](url) -> text
    content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)
    # 处理空文本的链接 []() -> 完全去除
    content = re.sub(r'\[\]\([^)]+\)', '', content)
    
    # 4. 去除多余的空白行
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    return content

# 读取测试文件
with open('/Users/kevin/obsidian_notes/url_spider/new/url_spider_service/test_clip_result.md', 'r', encoding='utf-8') as f:
    content = f.read()

print("原始文件长度:", len(content))
print("\n=== 原始文件前 500 字符 ===")
print(content[:500])
print("\n=== 处理后文件前 500 字符 ===")

# 预处理内容
processed = preprocess_markdown(content)

print(processed[:500])
print("\n处理后文件长度:", len(processed))
print("\n=== 检查是否成功去除 ===")

# 检查是否还有图片
if '![' in processed:
    print("❌ 仍包含图片")
else:
    print("✅ 已去除图片")

# 检查是否还有链接
if '](' in processed:
    print("❌ 仍包含链接")
else:
    print("✅ 已去除链接")

# 检查是否还有元数据
if processed.startswith('---'):
    print("❌ 仍包含元数据")
else:
    print("✅ 已去除元数据")

# 保存处理后的文件
with open('/Users/kevin/obsidian_notes/url_spider/new/url_spider_service/test_clip_result_processed.md', 'w', encoding='utf-8') as f:
    f.write(processed)

print("\n处理后的文件已保存为: test_clip_result_processed.md")
