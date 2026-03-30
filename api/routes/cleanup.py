"""
数据清理 API 路由
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, List, Literal
from datetime import datetime
import sqlite3

router = APIRouter()


def get_storage():
    """获取 storage 实例"""
    from core.storage import ArticleStorage
    return ArticleStorage()


class CleanupRequest(BaseModel):
    mode: Literal["days", "date", "before", "all"]
    value: str = ""


@router.post("/cleanup")
async def perform_cleanup(request: CleanupRequest) -> Dict:
    """执行数据清理"""
    storage = get_storage()
    
    try:
        if request.mode == "days":
            # 删除 N 天前的数据
            days = int(request.value)
            count = storage.delete_older_than_days(days)
            return {
                "message": f"已删除 {count} 条记录",
                "mode": request.mode,
                "value": request.value,
                "deleted_count": count
            }
        
        elif request.mode == "date":
            # 删除指定日期的数据
            date_str = request.value
            # 验证日期格式
            datetime.strptime(date_str, '%Y-%m-%d')
            count = storage.delete_by_date(date_str)
            return {
                "message": f"已删除 {count} 条记录",
                "mode": request.mode,
                "value": request.value,
                "deleted_count": count
            }
        
        elif request.mode == "before":
            # 删除指定日期之前的数据
            date_str = request.value
            datetime.strptime(date_str, '%Y-%m-%d')
            count = storage.delete_before_date(date_str)
            return {
                "message": f"已删除 {count} 条记录",
                "mode": request.mode,
                "value": request.value,
                "deleted_count": count
            }
        
        elif request.mode == "all":
            # 清空所有数据
            count = storage.delete_all()
            return {
                "message": f"已清空所有数据，共 {count} 条记录",
                "mode": request.mode,
                "value": request.value,
                "deleted_count": count
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"不支持的清理模式: {request.mode}")
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"参数格式错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理失败: {str(e)}")


@router.get("/cleanup/preview")
async def preview_cleanup(
    mode: str = Query(..., description="清理模式: days/date/before/all"),
    value: str = Query(..., description="清理参数值")
) -> Dict:
    """预览待清理数据"""
    storage = get_storage()
    
    try:
        conn = sqlite3.connect(storage.db_path)
        cursor = conn.cursor()
        
        if mode == "days":
            days = int(value)
            cutoff_date = (datetime.now() - __import__('datetime').timedelta(days=days)).strftime('%Y-%m-%d')
            cursor.execute("""
                SELECT date(processed_at) as dt, COUNT(*) as cnt
                FROM articles
                WHERE date(processed_at) < ?
                GROUP BY dt
                ORDER BY dt DESC
            """, (cutoff_date,))
        
        elif mode == "date":
            datetime.strptime(value, '%Y-%m-%d')
            cursor.execute("""
                SELECT date(processed_at) as dt, COUNT(*) as cnt
                FROM articles
                WHERE date(processed_at) = ?
                GROUP BY dt
            """, (value,))
        
        elif mode == "before":
            datetime.strptime(value, '%Y-%m-%d')
            cursor.execute("""
                SELECT date(processed_at) as dt, COUNT(*) as cnt
                FROM articles
                WHERE date(processed_at) < ?
                GROUP BY dt
                ORDER BY dt DESC
            """, (value,))
        
        elif mode == "all":
            cursor.execute("""
                SELECT date(processed_at) as dt, COUNT(*) as cnt
                FROM articles
                GROUP BY dt
                ORDER BY dt DESC
            """)
        
        else:
            conn.close()
            raise HTTPException(status_code=400, detail=f"不支持的清理模式: {mode}")
        
        preview_data = cursor.fetchall()
        total_count = sum(row[1] for row in preview_data)
        conn.close()
        
        return {
            "mode": mode,
            "value": value,
            "total_count": total_count,
            "affected_dates": [{"date": row[0], "count": row[1]} for row in preview_data]
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"参数格式错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")
