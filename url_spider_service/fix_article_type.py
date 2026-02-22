from database import articles_collection

# Fix article_type field: convert arrays to sorted strings
def fix_article_type():
    # Find all documents where article_type is an array
    documents = articles_collection.find({"article_type": {"$type": "array"}})
    
    count = 0
    for doc in documents:
        article_type = doc.get("article_type", [])
        if isinstance(article_type, list) and article_type:
            # Sort the array and take the first element
            sorted_type = sorted(article_type)
            new_article_type = sorted_type[0]
            
            # Update the document
            articles_collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {"article_type": new_article_type}}
            )
            count += 1
            if count % 100 == 0:
                print(f"Processed {count} documents")
        elif isinstance(article_type, list) and not article_type:
            # Handle empty arrays
            articles_collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {"article_type": ""}}
            )
            count += 1
    
    print(f"Total documents processed: {count}")

if __name__ == "__main__":
    print("Starting to fix article_type fields...")
    fix_article_type()
    print("Fix completed!")
