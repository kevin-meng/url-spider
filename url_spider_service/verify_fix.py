from database import articles_collection
from bson import ObjectId

# Verify article_type field is now a string
def verify_fix():
    # Check first 5 documents
    documents = articles_collection.find({}, {"_id": 1, "article_type": 1}).limit(5)
    
    print("Sample documents after fix:")
    for doc in documents:
        doc_id = str(doc["_id"])
        article_type = doc.get("article_type")
        type_info = type(article_type).__name__
        print(f"ID: {doc_id}, article_type: {article_type}, type: {type_info}")
    
    # Check if any documents still have array type
    array_count = articles_collection.count_documents({"article_type": {"$type": "array"}})
    print(f"\nNumber of documents with array article_type: {array_count}")
    
    # Check total documents
    total_count = articles_collection.count_documents({})
    print(f"Total documents: {total_count}")

if __name__ == "__main__":
    print("Verifying fix for article_type field...")
    verify_fix()
