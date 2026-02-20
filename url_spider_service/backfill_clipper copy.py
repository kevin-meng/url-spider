import asyncio
import sys
import os
import traceback
from datetime import datetime
from sqlalchemy import text

# Ensure we can import from current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_mysql_db, articles_collection
from services.clipper_service import ClipperService
from services.llm_service import LLMService

# 配置
CONCURRENCY_CLIPPER = 3      # 剪藏并发数 (Playwright 较重，建议控制)
CONCURRENCY_LLM = 5          # LLM 评估并发数 (API 调用，可稍高)
BATCH_SIZE = 50              # 每次从 MySQL 获取的文章数量
TARGET_DATE = "2026-02-10"   # 处理在此日期之前的文章

async def process_article(article, clipper_service, llm_service, clip_sem, llm_sem):
    url = article['url']
    title = article['title']
    description = article['description']
    
    try:
        # 1. 检查 MongoDB 是否已存在
        existing = articles_collection.find_one({"url": url})
        
        # 如果已存在且有评分，直接判断是否需要剪藏
        if existing and existing.get("pre_value_score") is not None:
            score = existing.get("pre_value_score", 0)
            if score > 4 and not existing.get("full_content"):
                print(f"[剪藏] {url} (评分: {score}) - 开始剪藏...")
                async with clip_sem:
                    result = await clipper_service.process_url(url)
                    if "error" in result:
                        print(f"[剪藏失败] {url}: {result['error']}")
                    else:
                        update_data = {
                            "full_content": result.get("content", ""),
                            "full_markdown": result.get("full_markdown", ""),
                            "clipper_metadata": result.get("metadata", {}),
                            "updated_at": datetime.now()
                        }
                        articles_collection.update_one({"_id": existing["_id"]}, {"$set": update_data})
                        print(f"[剪藏成功] {url}")
            else:
                # 已存在但分数低或已有内容，跳过
                # print(f"[跳过] {url} (已存在, 评分: {score})")
                pass
            return

        # 2. 如果不存在或无评分，先进行评估 (LLM)
        if not existing:
            # print(f"[评估] {url} - 开始评估...")
            async with llm_sem:
                # 构造 LLM 输入
                llm_input = [{"title": title, "description": description}]
                eval_result = await llm_service.evaluate_articles(llm_input)
                
                # 获取结果
                evaluated_items = eval_result.get("articles", [])
                if evaluated_items:
                    eval_item = evaluated_items[0]
                    score = eval_item.get("pre_value_score", 0)
                    
                    # 存入 Mongo
                    doc = {
                        "url": url,
                        "title": eval_item.get("title", title),
                        "description": description,
                        "pre_value_score": score,
                        "article_type": eval_item.get("article_type", []),
                        "pre_value_score_reason": eval_item.get("pre_value_score_reason", ""),
                        "created_at": datetime.now(),
                        "updated_at": datetime.now()
                    }
                    articles_collection.update_one({"url": url}, {"$set": doc}, upsert=True)
                    print(f"[评估完成] {url} (评分: {score})")
                    
                    # 3. 如果分数 > 4，立即剪藏
                    if score > 4:
                        print(f"[剪藏] {url} (高分文章) - 开始剪藏...")
                        async with clip_sem:
                            result = await clipper_service.process_url(url)
                            if "error" in result:
                                print(f"[剪藏失败] {url}: {result['error']}")
                            else:
                                update_data = {
                                    "full_content": result.get("content", ""),
                                    "full_markdown": result.get("full_markdown", ""),
                                    "clipper_metadata": result.get("metadata", {}),
                                    "updated_at": datetime.now()
                                }
                                articles_collection.update_one({"url": url}, {"$set": update_data})
                                print(f"[剪藏成功] {url}")
                else:
                    print(f"[评估失败] {url} - LLM 返回空")

    except Exception as e:
        print(f"[错误] 处理 {url} 时出错: {e}")
        # traceback.print_exc()

async def backfill_loop():
    print(f"=== 开始处理存量数据 (created_at < {TARGET_DATE}) ===")
    
    # 初始化服务
    clipper_service = ClipperService()
    llm_service = LLMService()
    
    # 信号量控制并发
    clip_sem = asyncio.Semaphore(CONCURRENCY_CLIPPER)
    llm_sem = asyncio.Semaphore(CONCURRENCY_LLM)
    
    # 数据库连接
    db_gen = get_mysql_db()
    mysql_db = next(db_gen)
    
    offset = 0
    total_processed = 0
    
    try:
        while True:
            print(f"\n[批次] 获取第 {offset} - {offset + BATCH_SIZE} 条数据...")
            
            # 从 MySQL 分页获取旧数据
            # 注意：这里假设 created_at 是字符串或日期类型，可以直接比较
            # 也可以用 id 排序来遍历，避免 offset 性能问题。但为了简单先用 offset。
            # 或者更好的方式：记录上次处理的 ID？
            # 鉴于用户说是"一次性"处理，offset 简单直接。
            
            query = text(f"""
                SELECT url, title, description 
                FROM articles 
                WHERE created_at < '{TARGET_DATE}' 
                ORDER BY created_at DESC 
                LIMIT {BATCH_SIZE} OFFSET {offset}
            """)
            
            result = mysql_db.execute(query)
            rows = result.fetchall()
            
            if not rows:
                print("没有更多数据了，处理完成！")
                break
            
            tasks = []
            for row in rows:
                article = {
                    "url": row[0],
                    "title": row[1] or "无标题",
                    "description": (row[2] or "")[:120]
                }
                tasks.append(process_article(article, clipper_service, llm_service, clip_sem, llm_sem))
            
            # 并发执行本批次
            await asyncio.gather(*tasks)
            
            processed_count = len(rows)
            total_processed += processed_count
            offset += processed_count
            
            print(f"本批次完成 {processed_count} 条，累计处理 {total_processed} 条。")
            
            # 简单的防封策略：批次间稍微停顿
            # await asyncio.sleep(2)

    except Exception as e:
        print(f"主循环出错: {e}")
        traceback.print_exc()
    finally:
        mysql_db.close()

if __name__ == "__main__":
    asyncio.run(backfill_loop())
