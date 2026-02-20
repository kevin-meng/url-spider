from database import articles_collection

# 统计每种分数的数量
total = 0
for score in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
    c = len(list(articles_collection.find({'pre_value_score': score})))
    if c > 0:
        print(f'score={score}: {c}')
        total += c

print(f'\n总分>=1: {total}')
print(f'总数据: {articles_collection.count_documents({})}')
