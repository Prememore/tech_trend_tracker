"""
操作日志 API 路由
"""

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from pathlib import Path
import os

router = APIRouter()


class DeleteLogsRequest(BaseModel):
    ids: Optional[List[int]] = None


def get_storage():
    """获取 storage 实例"""
    from core.storage import ArticleStorage
    return ArticleStorage()


def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).parent.parent.parent


@router.get("/logs")
async def get_logs(
    limit: int = Query(50, description="返回日志条数限制"),
    log_type: str = Query("cleanup", description="日志类型: cleanup/update/all")
) -> Dict:
    """获取操作日志"""
    
    logs = []
    
    # 1. 从数据库获取清理日志
    if log_type in ["cleanup", "all"]:
        try:
            storage = get_storage()
            cleanup_logs = storage.get_cleanup_log(limit=limit)
            for log in cleanup_logs:
                logs.append({
                    "id": log.get("id"),
                    "type": "cleanup",
                    "operation": log.get("operation", ""),
                    "target": log.get("target", ""),
                    "count": log.get("count", 0),
                    "timestamp": log.get("timestamp", "")
                })
        except Exception:
            pass
    
    # 2. 从日志文件读取更新日志
    if log_type in ["update", "all"]:
        logs_dir = get_project_root() / "logs"
        if logs_dir.exists():
            # 获取所有日志文件并按修改时间排序
            log_files = sorted(
                [f for f in logs_dir.glob("*.log")],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            for log_file in log_files[:5]:  # 只读最近5个日志文件
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        # 读取最后 N 行
                        for line in lines[-limit:]:
                            line = line.strip()
                            if line:
                                logs.append({
                                    "type": "update",
                                    "source": log_file.name,
                                    "message": line,
                                    "timestamp": log_file.stem.replace("update_", "").replace(".log", "")
                                })
                except Exception:
                    continue
    
    # 按时间戳排序（最新的在前）
    logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    # 限制返回数量
    logs = logs[:limit]
    
    return {
        "total": len(logs),
        "logs": logs
    }


@router.delete("/logs/{log_id}")
async def delete_log(log_id: int) -> Dict:
    """删除单条日志"""
    try:
        storage = get_storage()
        deleted = storage.delete_log(log_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"日志 ID {log_id} 不存在")
        return {"success": True, "message": f"日志 {log_id} 已删除"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.delete("/logs")
async def delete_logs(request: DeleteLogsRequest) -> Dict:
    """批量删除日志，如果 ids 为空则清空全部"""
    try:
        storage = get_storage()
        
        # 如果 ids 为空或不传，则清空全部
        if not request.ids:
            count = storage.clear_logs()
            return {"success": True, "message": f"已清空全部 {count} 条日志", "count": count}
        
        # 批量删除指定 ID
        count = storage.delete_logs(request.ids)
        return {"success": True, "message": f"已删除 {count} 条日志", "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
