"""
FastAPI 应用入口
作者: 程浩鑫
日期: 2026-03-27
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import articles, update, keywords, cleanup, logs

app = FastAPI(
    title="Tech Trend Tracker API",
    description="学术文献追踪系统 API",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(articles.router, prefix="/api", tags=["articles"])
app.include_router(update.router, prefix="/api", tags=["update"])
app.include_router(keywords.router, prefix="/api", tags=["keywords"])
app.include_router(cleanup.router, prefix="/api", tags=["cleanup"])
app.include_router(logs.router, prefix="/api", tags=["logs"])


@app.get("/api/stats")
async def get_stats():
    """数据库统计"""
    from core.storage import ArticleStorage
    from datetime import datetime
    
    storage = ArticleStorage()
    
    # 获取总论文数
    import sqlite3
    conn = sqlite3.connect(storage.db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM articles")
    total_count = cursor.fetchone()[0]
    
    # 获取日期范围
    cursor.execute("SELECT MIN(date(processed_at)), MAX(date(processed_at)) FROM articles")
    date_range = cursor.fetchone()
    
    # 获取各日期统计
    date_stats = storage.get_date_statistics()
    
    # 获取今日文章数
    today_str = datetime.now().strftime('%Y-%m-%d')
    cursor.execute("SELECT COUNT(*) FROM articles WHERE date(processed_at) = ?", (today_str,))
    today_count = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total_articles": total_count,
        "today_count": today_count,
        "date_range": {
            "earliest": date_range[0] if date_range[0] else None,
            "latest": date_range[1] if date_range[1] else None
        },
        "daily_counts": [{"date": d[0], "count": d[1]} for d in date_stats],
        "database_size": storage.get_database_size()
    }
