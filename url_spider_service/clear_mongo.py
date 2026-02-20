import asyncio
import sys
import os
from pymongo import MongoClient
import traceback

# Ensure we can import from current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import articles_collection

def clear_mongo():
    print("WARNING: Clearing MongoDB 'articles' collection...")
    result = articles_collection.delete_many({})
    print(f"Deleted {result.deleted_count} documents from MongoDB.")

if __name__ == "__main__":
    clear_mongo()
