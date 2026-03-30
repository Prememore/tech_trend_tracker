"""
文献更新 API 路由
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional, List
from datetime import datetime
from pathlib import Path
import sys

router = APIRouter()

# 模块级变量存储更新状态
update_status = {
    "status": "idle",  # idle, running, completed, failed
    "started_at": None,
    "completed_at": None,
    "progress": {
        "current": 0,
        "total": 0,
        "stage": ""  # fetching, filtering, saving
    },
    "result": {
        "fetched": 0,
        "filtered": 0,
        "saved": 0,
        "errors": []
    }
}


class UpdateRequest(BaseModel):
    days: int = 30


def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).parent.parent.parent


def run_update_task(days: int):
    """后台执行文献更新任务"""
    global update_status
    
    # 重置状态
    update_status["status"] = "running"
    update_status["started_at"] = datetime.now().isoformat()
    update_status["completed_at"] = None
    update_status["progress"] = {"current": 0, "total": 0, "stage": "initializing"}
    update_status["result"] = {"fetched": 0, "filtered": 0, "saved": 0, "errors": []}
    
    try:
        # 添加项目根目录到路径
        project_root = get_project_root()
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        from core.collector import ArxivCollector
        from core.filter import RelevanceFilter
        from core.storage import ArticleStorage
        from core.keyword_manager import KeywordManager
        
        # 获取关键词
        keyword_manager = KeywordManager()
        keywords = keyword_manager.get_keywords()
        
        # 1. 抓取文献
        update_status["progress"]["stage"] = "fetching"
        collector = ArxivCollector()
        # 临时修改 days_back
        collector.days_back = days
        
        articles = collector.fetch_articles(keywords, max_results=1000)
        update_status["result"]["fetched"] = len(articles)
        update_status["progress"]["current"] = len(articles)
        
        # 2. 过滤文献
        update_status["progress"]["stage"] = "filtering"
        filter_obj = RelevanceFilter(keywords)
        filtered_articles = filter_obj.filter(articles)
        update_status["result"]["filtered"] = len(filtered_articles)
        
        # 3. 保存文献
        update_status["progress"]["stage"] = "saving"
        storage = ArticleStorage()
        saved_count = storage.save_articles(filtered_articles)
        update_status["result"]["saved"] = saved_count
        
        # 完成
        update_status["status"] = "completed"
        update_status["completed_at"] = datetime.now().isoformat()
        update_status["progress"]["stage"] = "done"
        
    except Exception as e:
        update_status["status"] = "failed"
        update_status["completed_at"] = datetime.now().isoformat()
        update_status["result"]["errors"].append(str(e))
        update_status["progress"]["stage"] = "error"


@router.post("/update")
async def trigger_update(background_tasks: BackgroundTasks, request: UpdateRequest) -> Dict:
    """触发文献更新（异步执行）"""
    global update_status
    
    # 检查是否已有运行中的任务
    if update_status["status"] == "running":
        raise HTTPException(status_code=409, detail="已有更新任务正在运行")
    
    # 启动后台任务
    background_tasks.add_task(run_update_task, request.days)
    
    return {
        "message": "更新任务已启动",
        "days": request.days,
        "status": "running"
    }


@router.get("/update/status")
async def get_update_status() -> Dict:
    """查询更新任务状态"""
    return update_status
