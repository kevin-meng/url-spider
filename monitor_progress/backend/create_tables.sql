-- 创建统计结果表
-- 用于存储每日统计结果
CREATE TABLE IF NOT EXISTS daily_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stat_date DATE NOT NULL,
    total_feeds INT DEFAULT 0,
    total_articles INT DEFAULT 0,
    today_feeds INT DEFAULT 0,
    today_articles INT DEFAULT 0,
    today_mongo_articles_count INT DEFAULT 0,
    today_preprocessed INT DEFAULT 0,
    today_full_content INT DEFAULT 0,
    high_score_articles INT DEFAULT 0,
    today_llm_summary INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stat_date (stat_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建公众号月度统计表
-- 用于存储每个公众号每月文章数量
CREATE TABLE IF NOT EXISTS mp_monthly_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mp_id VARCHAR(100) NOT NULL,
    stat_month VARCHAR(7) NOT NULL,
    article_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_mp_month (mp_id, stat_month)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建文章类型评分分布统计表
-- 用于存储热力图数据
CREATE TABLE IF NOT EXISTS article_type_score_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stat_date DATE NOT NULL,
    score_type VARCHAR(50) NOT NULL,
    article_type VARCHAR(100) NOT NULL,
    score INT NOT NULL,
    count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_date_type_score (stat_date, score_type, article_type, score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
