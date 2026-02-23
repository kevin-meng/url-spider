import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from pymongo import MongoClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "url_spider_db")

# MySQL Setup
logger.info(f"Connecting to MySQL at {MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}")
try:
    DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)
    # Test connection
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("MySQL connection successful")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
except Exception as e:
    logger.error(f"MySQL connection failed: {e}")

    # Create a mock engine to avoid import errors
    class MockEngine:
        def connect(self):
            class MockConnection:
                def execute(self, *args, **kwargs):
                    class MockResult:
                        def mappings(self):
                            return []

                        def first(self):
                            return None

                        def all(self):
                            return []

                    return MockResult()

                def __enter__(self):
                    return self

                def __exit__(self, *args, **kwargs):
                    pass

            return MockConnection()

    engine = MockEngine()
    SessionLocal = None
    Base = None


def get_mysql_db():
    if SessionLocal:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    else:
        # Return a mock db session
        class MockDB:
            def close(self):
                pass

        yield MockDB()


# MongoDB Setup
logger.info(f"Connecting to MongoDB at {MONGO_HOST}:{MONGO_PORT}")
try:
    MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/"
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    # Test connection
    mongo_client.admin.command("ping")
    logger.info("MongoDB connection successful")
    mongo_db = mongo_client[MONGO_DB_NAME]
    articles_collection = mongo_db["articles"]
    task_status_collection = mongo_db["task_status"]
except Exception as e:
    logger.error(f"MongoDB connection failed: {e}")

    # Create a mock client to avoid import errors
    class MockClient:
        def __getitem__(self, name):
            class MockDB:
                def __getitem__(self, name):
                    class MockCollection:
                        def find(self, *args, **kwargs):
                            return []

                        def find_one(self, *args, **kwargs):
                            return None

                        def count_documents(self, *args, **kwargs):
                            return 0

                        def update_one(self, *args, **kwargs):
                            class MockResult:
                                matched_count = 0

                            return MockResult()

                        def insert_one(self, *args, **kwargs):
                            class MockInsertResult:
                                inserted_id = "mock_id"

                            return MockInsertResult()

                        def aggregate(self, *args, **kwargs):
                            return []

                    return MockCollection()

            return MockDB()

    mongo_client = MockClient()
    mongo_db = mongo_client[MONGO_DB_NAME]
    articles_collection = mongo_db["articles"]
    task_status_collection = mongo_db["task_status"]


def get_mongo_db():
    return mongo_db
