from database import articles_collection

count = articles_collection.count_documents({'source': {'$exists': True, '$ne': ''}})
print('有 source 的记录:', count)

doc = articles_collection.find_one({'source': {'$exists': True, '$ne': ''}})
if doc:
    print('有 source 的记录:', doc.get('url')[:50], 'source:', doc.get('source'))
else:
    print('没有找到有 source 的记录')
