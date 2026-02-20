from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
from contextlib import asynccontextmanager

from services.clipper_service import ClipperService
from services.llm_service import LLMService

# Import tasks for manual triggering
from tasks.task1_fetch import task_fetch_and_evaluate
from tasks.task2_clip import task_clip_content
from tasks.task3_summarize import task_summarize_content

# 如果需要内部调度器，可以取消注释
# from tasks.scheduler import start_scheduler, stop_scheduler

app = FastAPI(title="URL Spider Service")

# Global services
clipper_service: Optional[ClipperService] = None
llm_service: Optional[LLMService] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global clipper_service, llm_service
    try:
        clipper_service = ClipperService()
        llm_service = LLMService()
        print("服务初始化完成。")
        
        # 启动调度器 (可选)
        # start_scheduler(clipper_service, llm_service)
        # print("调度器已启动。")
        
    except Exception as e:
        print(f"服务初始化失败: {e}")
    
    yield
    
    # Shutdown
    # stop_scheduler()
    # print("调度器已停止。")

app = FastAPI(lifespan=lifespan)

# Pydantic Models
class ClipRequest(BaseModel):
    url: str

class SummarizeRequest(BaseModel):
    markdown_content: str

class ArticleItem(BaseModel):
    title: str
    description: str

class EvaluateRequest(BaseModel):
    articles: List[ArticleItem]

# Endpoints

@app.post("/api/clip")
async def clip_url(request: ClipRequest):
    if not clipper_service:
        raise HTTPException(status_code=503, detail="Clipper 服务未初始化")
    
    result = await clipper_service.process_url(request.url)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@app.post("/api/summarize")
async def summarize_content(request: SummarizeRequest):
    if not llm_service:
        raise HTTPException(status_code=503, detail="LLM 服务未初始化")
    
    result = await llm_service.process_content(request.markdown_content)
    return result

@app.post("/api/evaluate")
async def evaluate_articles(request: EvaluateRequest):
    if not llm_service:
        raise HTTPException(status_code=503, detail="LLM 服务未初始化")
    
    # Convert Pydantic models to dicts
    articles_data = [article.model_dump() for article in request.articles]
    result = await llm_service.evaluate_articles(articles_data)
    return result

@app.get("/health")
def health_check():
    return {"status": "ok"}

# --- Trigger Endpoints for QingLong ---

@app.post("/api/trigger/task1")
async def trigger_task1(background_tasks: BackgroundTasks):
    """手动触发任务 1：获取并评估文章"""
    background_tasks.add_task(task_fetch_and_evaluate)
    return {"status": "triggered", "task": "fetch_and_evaluate", "message": "任务已在后台启动"}

@app.post("/api/trigger/task2")
async def trigger_task2(background_tasks: BackgroundTasks):
    """手动触发任务 2：剪藏内容"""
    background_tasks.add_task(task_clip_content)
    return {"status": "triggered", "task": "clip_content", "message": "任务已在后台启动"}

@app.post("/api/trigger/task3")
async def trigger_task3(background_tasks: BackgroundTasks):
    """手动触发任务 3：总结内容"""
    background_tasks.add_task(task_summarize_content)
    return {"status": "triggered", "task": "summarize_content", "message": "任务已在后台启动"}
