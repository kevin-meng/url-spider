import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pymongo import MongoClient

# Environment variables (with defaults matching PRD)
MYSQL_HOST = os.getenv("MYSQL_HOST", "192.168.2.18")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3307))
MYSQL_USER = os.getenv("MYSQL_USER", "rss_user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "pass123456")
MYSQL_DB = os.getenv("MYSQL_DB", "we_mp_rss")

MONGO_HOST = os.getenv("MONGO_HOST", "192.168.2.18")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
MONGO_USER = os.getenv("MONGO_USER", "admin")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "password123")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "url_spider_db") # Assuming a DB name for mongo

# MySQL Setup
DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_mysql_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# MongoDB Setup
MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/"
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client[MONGO_DB_NAME]
articles_collection = mongo_db["articles"]

def get_mongo_db():
    return mongo_db
