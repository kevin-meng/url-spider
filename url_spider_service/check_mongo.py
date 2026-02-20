from database import articles_collection

doc = articles_collection.find_one()
print('type:', type(doc.get('pre_value_score')))
print('value:', doc.get('pre_value_score'))

count1 = articles_collection.count_documents({'pre_value_score': {'$gt': 0}})
print('$gt 0:', count1)

count2 = articles_collection.count_documents({'pre_value_score': {'$exists': True}})
print('$exists True:', count2)

count3 = articles_collection.count_documents({'pre_value_score': '6'})
print('score=6 (string):', count3)

print('\n所有数据的 pre_value_score:')
for doc in articles_collection.find().limit(5):
    print(doc.get('pre_value_score'))
