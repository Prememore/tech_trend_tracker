"""
论文相关 API 路由
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional
from datetime import datetime
import sqlite3
from pathlib import Path

from core.text_utils import clean_latex

router = APIRouter()


def _clean_article_text(article: Dict) -> Dict:
    """清理文章中的 LaTeX 格式标记"""
    if article:
        if 'title' in article and article['title']:
            article['title'] = clean_latex(article['title'])
        if 'summary' in article and article['summary']:
            article['summary'] = clean_latex(article['summary'])
    return article


def _clean_articles_list(articles: List[Dict]) -> List[Dict]:
    """清理文章列表中的 LaTeX 格式标记"""
    return [_clean_article_text(article) for article in articles]


def get_storage():
    """获取 storage 实例，处理路径问题"""
    from core.storage import ArticleStorage
    return ArticleStorage()


@router.get("/articles/today")
async def get_today_articles() -> Dict:
    """获取今日论文列表"""
    storage = get_storage()
    today_str = datetime.now().strftime('%Y-%m-%d')
    articles = storage.get_daily_articles(today_str)
    # 清理 LaTeX 格式标记
    articles = _clean_articles_list(articles)
    return {
        "date": today_str,
        "articles": articles,
        "count": len(articles)
    }


@router.get("/articles/history")
async def get_history_articles(date: str = Query(..., description="日期格式: YYYY-MM-DD")) -> Dict:
    """获取指定日期的论文列表"""
    # 验证日期格式
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，请使用 YYYY-MM-DD 格式")
    
    storage = get_storage()
    articles = storage.get_daily_articles(date)
    # 清理 LaTeX 格式标记
    articles = _clean_articles_list(articles)
    return {
        "date": date,
        "articles": articles,
        "count": len(articles)
    }


@router.get("/articles/dates")
async def get_available_dates() -> Dict:
    """获取有数据的日期列表"""
    storage = get_storage()
    
    conn = sqlite3.connect(storage.db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT date(processed_at) as dt
        FROM articles
        ORDER BY dt DESC
    """)
    dates = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    return {"dates": dates}


@router.get("/articles/{article_id}")
async def get_article_detail(article_id: str) -> Dict:
    """获取单篇论文详情"""
    storage = get_storage()
    article = storage.get_article_by_id(article_id)
    
    if not article:
        raise HTTPException(status_code=404, detail="论文不存在")
    
    # 清理 LaTeX 格式标记
    article = _clean_article_text(article)
    return article
