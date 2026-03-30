#!/usr/bin/env python3
"""
技术趋势追踪器 - Web 服务启动入口
作者: 程浩鑫
日期: 2026-03-27
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from api.app import app


# 前端构建产物目录
FRONTEND_DIST = Path(__file__).parent / "frontend" / "dist"


# 如果前端构建产物存在，挂载静态文件服务
if FRONTEND_DIST.exists():
    # 挂载静态文件到根路径
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")
    app.mount("/icons", StaticFiles(directory=str(FRONTEND_DIST), check_dir=False), name="icons")
    
    # SPA catch-all 路由：非 /api 开头的路由返回 index.html
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """为 SPA 提供前端路由支持"""
        # 排除 API 路径
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
            return {"detail": "Not Found"}
        
        index_path = FRONTEND_DIST / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        return {"detail": "Frontend not built"}


def main():
    parser = argparse.ArgumentParser(description="Tech Trend Tracker Web Server")
    parser.add_argument("--host", default="0.0.0.0", help="监听主机地址 (默认: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="监听端口 (默认: 8000)")
    parser.add_argument("--reload", action="store_true", help="启用开发模式热重载")
    
    args = parser.parse_args()
    
    print(f"🚀 启动 Tech Trend Tracker Web 服务器")
    print(f"   地址: http://{args.host}:{args.port}")
    if FRONTEND_DIST.exists():
        print(f"   前端: 已挂载 (frontend/dist)")
    else:
        print(f"   前端: 未构建 (frontend/dist 不存在)")
    print(f"   模式: {'开发 (热重载)' if args.reload else '生产'}")
    print(f"   API文档: http://{args.host}:{args.port}/docs")
    print()
    
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )


if __name__ == "__main__":
    main()
