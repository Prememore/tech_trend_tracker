"""
关键词管理 API 路由
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List
from pathlib import Path

router = APIRouter()


def get_keyword_manager():
    """获取 KeywordManager 实例"""
    from core.keyword_manager import KeywordManager
    return KeywordManager()


class KeywordsUpdateRequest(BaseModel):
    primary: List[str]
    secondary: List[str]
    description: str = ""


@router.get("/keywords")
async def get_keywords() -> Dict:
    """获取当前关键词配置"""
    manager = get_keyword_manager()
    return manager.list_keywords()


@router.put("/keywords")
async def update_keywords(request: KeywordsUpdateRequest) -> Dict:
    """更新关键词配置"""
    manager = get_keyword_manager()
    
    # 构建新的关键词配置
    new_keywords = {
        'primary': request.primary,
        'secondary': request.secondary,
        'description': request.description,
        'created_at': manager._get_current_time()
    }
    
    # 保存到文件
    try:
        manager.keywords_file.parent.mkdir(parents=True, exist_ok=True)
        import json
        with open(manager.keywords_file, 'w', encoding='utf-8') as f:
            json.dump(new_keywords, f, ensure_ascii=False, indent=2)
        
        # 重新加载
        manager._load_keywords()
        
        return {
            "message": "关键词配置已更新",
            "keywords": manager.list_keywords()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")


@router.post("/keywords/reset")
async def reset_keywords() -> Dict:
    """重置为默认关键词"""
    manager = get_keyword_manager()
    success = manager.reset_to_default()
    
    if success:
        return {
            "message": "已重置为默认关键词",
            "keywords": manager.list_keywords()
        }
    else:
        raise HTTPException(status_code=500, detail="重置失败")
