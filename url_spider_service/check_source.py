from database import articles_collection

docs = list(articles_collection.find().sort('updated_at', -1).limit(5))

for doc in docs:
    print('=' * 50)
    print(f"URL: {doc.get('url', '')[:60]}...")
    print(f"title: {doc.get('title', '')}")
    print(f"source: {doc.get('source', '【无】')}")
    print(f"pre_value_score: {doc.get('pre_value_score')}")
