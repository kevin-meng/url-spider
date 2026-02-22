from sqlalchemy import Column, String, Integer, DateTime, Text, Date, UniqueConstraint
from database import Base
from datetime import datetime

class Feed(Base):
    __tablename__ = "feeds"

    id = Column(String, primary_key=True, index=True)
    mp_name = Column(String, index=True)
    mp_cover = Column(String)
    mp_intro = Column(Text)
    status = Column(Integer)
    sync_time = Column(Integer)
    update_time = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    faker_id = Column(String)

class Article(Base):
    __tablename__ = "articles"

    id = Column(String, primary_key=True, index=True)
    mp_id = Column(String, index=True)
    title = Column(String)
    pic_url = Column(String)
    url = Column(String)
    description = Column(Text)
    status = Column(Integer)
    publish_time = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_export = Column(Integer)
    is_read = Column(Integer)
    content = Column(Text)

class DailyStats(Base):
    __tablename__ = "daily_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stat_date = Column(Date, nullable=False, index=True)
    total_feeds = Column(Integer, default=0)
    total_articles = Column(Integer, default=0)
    today_feeds = Column(Integer, default=0)
    today_articles = Column(Integer, default=0)
    today_preprocessed = Column(Integer, default=0)
    today_full_content = Column(Integer, default=0)
    high_score_articles = Column(Integer, default=0)
    today_llm_summary = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('stat_date', name='uk_stat_date'),
    )

class MpMonthlyStats(Base):
    __tablename__ = "mp_monthly_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mp_id = Column(String(100), nullable=False, index=True)
    stat_month = Column(String(7), nullable=False, index=True)
    article_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('mp_id', 'stat_month', name='uk_mp_month'),
    )

class ArticleTypeScoreStats(Base):
    __tablename__ = "article_type_score_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stat_date = Column(Date, nullable=False, index=True)
    score_type = Column(String(50), nullable=False, index=True)
    article_type = Column(String(100), nullable=False, index=True)
    score = Column(Integer, nullable=False)
    count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('stat_date', 'score_type', 'article_type', 'score', name='uk_date_type_score'),
    )
