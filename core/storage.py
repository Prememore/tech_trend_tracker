"""
存储模块：SQLite 数据库操作 + 数据清理功能
作者: 程浩鑫
日期: 2026-02-15
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
import os
import yaml


class ArticleStorage:
    """文章存储类 - 支持数据持久化与清理"""

    def __init__(self):
        # 动态计算项目根目录（相对于当前文件）
        self.root_dir = Path(__file__).parent.parent
        self.db_path = self.root_dir / "data" / "trends.db"
        self._init_db()

    def _init_db(self):
        """初始化数据库表结构"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 文章表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                link TEXT NOT NULL,
                source TEXT NOT NULL,
                published_at TIMESTAMP,
                tags TEXT,
                relevance_score REAL,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 清理日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cleanup_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation TEXT NOT NULL,
                target TEXT NOT NULL,
                count INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建索引加速查询
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_processed ON articles(date(processed_at))")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_score ON articles(relevance_score DESC)")
        
        conn.commit()
        conn.close()

    def save_articles(self, articles: List[Dict]) -> int:
        """保存文章列表（自动去重）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        inserted = 0
        
        for art in articles:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO articles 
                    (id, title, summary, link, source, published_at, tags, relevance_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    art['id'],
                    art['title'],
                    art['summary'],
                    art['link'],
                    art['source'],
                    art['published_at'],
                    art.get('tags', ''),
                    art.get('relevance_score', 0.0)
                ))
                if cursor.rowcount > 0:
                    inserted += 1
            except Exception as e:
                print(f"⚠️  保存失败: {art.get('title', 'N/A')[:30]} | {e}")
        
        conn.commit()
        conn.close()
        return inserted

    def get_daily_articles(self, date_str: str = None) -> List[Dict]:
        """获取指定日期的文章（✅ 使用配置化阈值）"""
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        # 从配置读取阈值（与 filter.py 保持一致）
        threshold = 0.45
        try:
            config_path = Path(__file__).parent.parent / "config" / "sources.yaml"
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            threshold = float(config.get('settings', {}).get('relevance_threshold', 0.45))
        except:
            pass
        print(f"阈值: {threshold:.2f}")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # ✅ 关键修改：SQL 中使用配置的阈值
        cursor.execute("""
            SELECT id, title, summary, link, source, relevance_score, tags
            FROM articles
            WHERE date(processed_at) = ? AND relevance_score >= ?
            ORDER BY relevance_score DESC, published_at DESC
        """, (date_str, threshold))  # ← 传入阈值参数
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'id': row[0],
            'title': row[1],
            'summary': row[2],
            'link': row[3],
            'source': row[4],
            'relevance_score': row[5],
            'tags': row[6]
        } for row in rows]

    def get_article_by_id(self, article_id: str) -> Dict:
        """根据ID获取单篇文章详情（含完整摘要）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT title, summary, link, source, published_at, relevance_score
            FROM articles WHERE id = ?
        """, (article_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        return {
            'title': row[0],
            'summary': row[1],
            'link': row[2],
            'source': row[3],
            'published_at': row[4],
            'relevance_score': row[5]
        }

    # ==================== 清理功能 API ====================

    def get_date_statistics(self) -> List[Tuple[str, int]]:
        """获取各日期的文章数量统计（按日期降序）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date(processed_at) as dt, COUNT(*) as cnt
            FROM articles
            GROUP BY dt
            ORDER BY dt DESC
        """)
        stats = cursor.fetchall()
        conn.close()
        return stats

    def get_database_size(self) -> str:
        """获取数据库文件大小（人类可读格式）"""
        if not self.db_path.exists():
            return "0 B"
        size_bytes = self.db_path.stat().st_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def delete_by_date(self, date_str: str) -> int:
        """删除指定日期的所有文章"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM articles WHERE date(processed_at) = ?
        """, (date_str,))
        count = cursor.rowcount
        conn.commit()
        conn.close()
        self._log_cleanup('delete_by_date', date_str, count)
        return count

    def delete_before_date(self, date_str: str) -> int:
        """删除指定日期之前的所有文章"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM articles WHERE date(processed_at) < ?
        """, (date_str,))
        count = cursor.rowcount
        conn.commit()
        conn.close()
        self._log_cleanup('delete_before', date_str, count)
        return count

    def delete_older_than_days(self, days: int) -> int:
        """删除 N 天前的所有文章（自动清理核心方法）"""
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        return self.delete_before_date(cutoff_date)

    def delete_all(self) -> int:
        """清空所有文章（谨慎使用）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM articles")
        count = cursor.rowcount
        conn.commit()
        conn.close()
        self._log_cleanup('delete_all', 'all', count)
        return count

    def get_cleanup_log(self, limit: int = 10) -> List[Dict]:
        """获取最近的清理操作日志"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, operation, target, count, timestamp
            FROM cleanup_log
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        logs = []
        for row in rows:
            logs.append({
                'id': row[0],
                'operation': row[1],
                'target': row[2],
                'count': row[3],
                'timestamp': row[4][:16]
            })
        return logs

    def _log_cleanup(self, operation: str, target: str, count: int):
        """记录清理操作到日志表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO cleanup_log (operation, target, count)
            VALUES (?, ?, ?)
        """, (operation, target, count))
        conn.commit()
        conn.close()

    def delete_log(self, log_id: int) -> bool:
        """删除单条日志记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cleanup_log WHERE id = ?", (log_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    def delete_logs(self, log_ids: List[int]) -> int:
        """批量删除日志记录"""
        if not log_ids:
            return 0
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        placeholders = ','.join(['?' for _ in log_ids])
        cursor.execute(f"DELETE FROM cleanup_log WHERE id IN ({placeholders})", log_ids)
        count = cursor.rowcount
        conn.commit()
        conn.close()
        return count

    def clear_logs(self) -> int:
        """清空所有日志记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cleanup_log")
        count = cursor.rowcount
        conn.commit()
        conn.close()
        return count
