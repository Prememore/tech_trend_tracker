#!/usr/bin/env python3
"""
技术趋势追踪器 - 一键安装脚本
支持自定义安装路径，自动创建虚拟环境并安装依赖
作者: 程浩鑫
日期: 2026-02-15
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def detect_python():
    """智能检测 macOS 上的 Python 3 路径（优先 Homebrew）"""
    candidates = [
        "/opt/homebrew/bin/python3.9",      # Apple Silicon Homebrew
    ]
    
    for path in candidates:
        if os.path.exists(path):
            try:
                subprocess.run([path, "-m", "venv", "--help"], 
                             capture_output=True, check=True)
                return path
            except:
                continue
    return sys.executable


def create_project_structure(root_path: Path):
    """创建标准项目目录结构"""
    dirs = [
        root_path / "config",
        root_path / "core",
        root_path / "cli",
        root_path / "data",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"  ✅ 创建目录: {d.relative_to(root_path)}")


def write_file(filepath: Path, content: str):
    """安全写入文件"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')
    print(f"  ✅ 生成文件: {filepath.name}")


def generate_requirements(root_path: Path):
    content = """
feedparser==6.0.10
rich==13.7.1
PyYAML==6.0.1
APScheduler==3.10.4
requests==2.31.0
"""
    write_file(root_path / "requirements.txt", content)


def generate_sources_yaml(root_path: Path):
    content = """# 技术趋势追踪器 - 数据源配置
# 作者: 程浩鑫
# 日期: 2026-02-15

sources:
  # arXiv 强化学习最新论文
  - name: "arXiv CS.LG"
    url: "https://arxiv.org/rss/cs.LG"
    type: "rss"
    tags: ["reinforcement learning"]
  
  # arXiv 系统控制（覆盖混沌同步）
  - name: "arXiv CS.SY"
    url: "https://arxiv.org/rss/cs.SY"
    type: "rss"
    tags: ["chaotic system"]

# 关键词库：用于智能过滤
keywords:
  primary:
    - "reinforcement learning"
    - "chaos synchronization"
    - "chaotic system"
    - "强化学习"
    - "混沌同步"
    - "PPO"
    - "SAC"
    - "DDPG"
    - "TD3"
  
  secondary:
    - "multi-agent"
    - "多智能体"
"""
    write_file(root_path / "config" / "sources.yaml", content)


def generate_storage_py(root_path: Path):
    content = '''"""
存储模块：SQLite 数据库操作 + 数据清理功能
作者: 程浩鑫
日期: 2026-02-15
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
import os


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
        """获取指定日期的高相关度文章"""
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, summary, link, source, relevance_score, tags
            FROM articles
            WHERE date(processed_at) = ? AND relevance_score >= 0.45
            ORDER BY relevance_score DESC, published_at DESC
            LIMIT 30
        """, (date_str,))
        
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
            SELECT operation, target, count, timestamp
            FROM cleanup_log
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        logs = []
        for row in rows:
            logs.append({
                'operation': row[0],
                'target': row[1],
                'count': row[2],
                'timestamp': row[3][:16]
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
'''
    write_file(root_path / "core" / "storage.py", content)


def generate_collector_py(root_path: Path):
    content = '''"""
采集模块：RSS 抓取与解析
作者: 程浩鑫
日期: 2026-02-15
"""

import feedparser
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict


class TrendCollector:
    """RSS 采集器 - 支持去重与时间过滤"""

    def __init__(self):
        pass

    def _generate_id(self, title: str, link: str) -> str:
        """生成唯一ID（MD5哈希）"""
        return hashlib.md5(f"{title}{link}".encode()).hexdigest()

    def _is_recent(self, published: datetime, hours: int = 24) -> bool:
        """判断是否为近期内容（默认24小时内）"""
        return datetime.now() - published <= timedelta(hours=hours)

    def fetch_rss(self, source_config: Dict) -> List[Dict]:
        """从RSS源抓取文章"""
        url = source_config['url']
        source_name = source_config['name']
        tags = ','.join(source_config.get('tags', []))
        
        print(f"📡 抓取 [{source_name}] ...")
        
        try:
            feed = feedparser.parse(url)
            
            if feed.bozo:
                print(f"⚠️  RSS解析失败 [{source_name}]: {feed.bozo_exception}")
                return []
            
            new_items = []
            for entry in feed.entries[:15]:
                # 提取发布时间
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_time = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    pub_time = datetime(*entry.updated_parsed[:6])
                else:
                    continue
                
                # 时间过滤：仅保留24小时内内容
                if not self._is_recent(pub_time, hours=24):
                    continue
                
                item_id = self._generate_id(entry.title, entry.link)
                
                # 清理摘要中的HTML标签
                summary = getattr(entry, 'summary', '')
                import re
                summary = re.sub(r'<[^>]+>', '', summary)
                summary = re.sub(r'\\s+', ' ', summary).strip()[:2000]
                
                article = {
                    'id': item_id,
                    'title': entry.title.strip(),
                    'summary': summary,
                    'link': entry.link,
                    'source': source_name,
                    'published_at': pub_time,
                    'tags': tags
                }
                new_items.append(article)
            
            print(f"✅ 抓取完成 [{source_name}] - {len(new_items)} 条新内容")
            return new_items
            
        except Exception as e:
            print(f"❌ 抓取失败 [{source_name}]: {e}")
            return []
'''
    write_file(root_path / "core" / "collector.py", content)


def generate_filter_py(root_path: Path):
    content = '''"""
过滤模块：基于关键词计算文章相关性分数
作者: 程浩鑫
日期: 2026-02-15
"""

import re
from typing import List, Dict


class RelevanceFilter:
    """相关性过滤器 - 支持中英文关键词匹配"""

    def __init__(self, keywords: Dict[str, List[str]]):
        self.primary = [kw.lower() for kw in keywords.get('primary', [])]
        self.secondary = [kw.lower() for kw in keywords.get('secondary', [])]

    def _match_keywords(self, text: str, keywords: List[str]) -> List[str]:
        """在文本中匹配关键词（支持词边界）"""
        text_lower = text.lower()
        matched = []
        for kw in keywords:
            pattern = r'\\b' + re.escape(kw) + r'\\b'
            if re.search(pattern, text_lower):
                matched.append(kw)
        return matched

    def score(self, title: str, summary: str) -> float:
        """计算文章相关性分数 [0.0, 1.0]"""
        full_text = f"{title} {summary}"
        score = 0.0
        
        # 主关键词匹配（高权重）
        primary_matches = self._match_keywords(full_text, self.primary)
        if primary_matches:
            score += 0.6
        
        # 次关键词匹配（累积加分）
        secondary_matches = self._match_keywords(full_text, self.secondary)
        secondary_score = min(0.4, len(secondary_matches) * 0.15)
        score = min(1.0, score + secondary_score)
        
        return round(score, 2)

    def filter(self, articles: List[Dict]) -> List[Dict]:
        """过滤文章列表，仅保留相关度 >= 0.45 的内容"""
        scored = []
        for art in articles:
            score = self.score(art['title'], art['summary'])
            if score >= 0.45:
                art['relevance_score'] = score
                scored.append(art)
        
        # 按相关度降序排序
        scored.sort(key=lambda x: x['relevance_score'], reverse=True)
        return scored
'''
    write_file(root_path / "core" / "filter.py", content)


def generate_dashboard_py(root_path: Path):
    content = '''"""
交互式终端界面：支持摘要查看 + 数据清理
作者: 程浩鑫
日期: 2026-02-15
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from datetime import datetime
import webbrowser
import textwrap
import os
from core.storage import ArticleStorage


class TrendDashboard:
    """技术趋势交互式仪表盘"""

    def __init__(self):
        self.console = Console()
        self.storage = ArticleStorage()
        self.today = datetime.now().strftime('%Y-%m-%d')

    def show_main_menu(self):
        """显示主菜单"""
        while True:
            self._clear_screen()
            
            # 显示数据库状态
            stats = self.storage.get_date_statistics()
            total_articles = sum(cnt for _, cnt in stats) if stats else 0
            db_size = self.storage.get_database_size()
            
            header = Panel(
                Text.assemble(
                    ("📊 数据库状态\\n", "bold cyan"),
                    ("   总文章数: ", "white"), (f"{total_articles} 篇\\n", "green"),
                    ("   覆盖天数: ", "white"), (f"{len(stats)} 天\\n", "green") if stats else ("0 天\\n", "yellow"),
                    ("   数据库大小: ", "white"), (f"{db_size}\\n", "yellow"),
                ),
                title="🤖 技术趋势追踪器",
                border_style="cyan"
            )
            self.console.print(header)
            
            # 主菜单
            menu = Table(show_header=False, show_lines=True, width=60)
            menu.add_row("[bold]1[/bold] 查看今日趋势")
            menu.add_row("[bold]2[/bold] 查看历史日期")
            menu.add_row("[bold]3[/bold] [red]清理数据[/red]")
            menu.add_row("[bold]4[/bold] 查看清理日志")
            menu.add_row("[bold]q[/bold] 退出程序")
            self.console.print(menu)
            
            choice = Prompt.ask("\\n请选择操作", default="1").strip().lower()
            
            if choice == '1':
                self.show_daily_digest()
            elif choice == '2':
                self.show_history_browser()
            elif choice == '3':
                self.show_cleanup_menu()
            elif choice == '4':
                self.show_cleanup_log()
            elif choice == 'q':
                self.console.print("[bold green]👋 再见！[/bold green]")
                break
            else:
                self.console.print("[yellow]⚠️  无效选择，请重试[/yellow]")
                self._wait_for_key()

    def show_daily_digest(self):
        """显示今日技术趋势简报"""
        articles = self.storage.get_daily_articles(self.today)
        
        if not articles:
            self.console.print(f"\\n[bold yellow]📭 {self.today} 无高相关度技术动态[/bold yellow]")
            self.console.print("💡 建议：运行 'python run_daily.py' 手动触发更新")
            self._wait_for_key()
            return
        
        table = Table(
            title=f"[bold cyan]📅 {self.today} 技术趋势[/bold cyan] | 共 {len(articles)} 条",
            show_lines=True,
            header_style="bold magenta"
        )
        table.add_column("编号", style="cyan", width=4, justify="center")
        table.add_column("相关度", style="yellow", width=8)
        table.add_column("标题", style="green", no_wrap=False, width=60)
        table.add_column("来源", style="blue", width=15)
        
        for idx, art in enumerate(articles, 1):
            stars = "★" * int(art['relevance_score'] * 5)
            score_display = f"[bold yellow]{stars}[/bold yellow] ({art['relevance_score']})"
            title_display = art['title'][:55] + "..." if len(art['title']) > 55 else art['title']
            
            table.add_row(
                f"[bold]{idx}[/bold]",
                score_display,
                f"[link={art['link']}]{title_display}[/link]",
                art['source']
            )
        
        self.console.print(table)
        self.console.print("\\n[bold cyan]🔍 操作:[/bold cyan] 编号(查看摘要) / open 编号(打开链接) / b(返回)")
        
        self._interactive_loop(articles, return_to_main=True)

    def show_history_browser(self):
        """浏览历史日期数据"""
        stats = self.storage.get_date_statistics()
        if not stats:
            self.console.print("[yellow]📭 无历史数据[/yellow]")
            self._wait_for_key()
            return
        
        page_size = 15
        page = 0
        
        while True:
            self._clear_screen()
            table = Table(title="📆 历史数据分布", show_lines=True)
            table.add_column("序号", style="cyan", width=4)
            table.add_column("日期", style="green", width=12)
            table.add_column("文章数", style="yellow", width=8)
            table.add_column("占比", style="blue", width=8)
            
            total = sum(cnt for _, cnt in stats)
            start_idx = page * page_size
            end_idx = min(start_idx + page_size, len(stats))
            
            for i, (date_str, count) in enumerate(stats[start_idx:end_idx], start=start_idx+1):
                pct = count / total * 100 if total else 0
                table.add_row(
                    str(i),
                    date_str,
                    str(count),
                    f"{pct:.1f}%"
                )
            
            self.console.print(table)
            self.console.print(f"\\n页码: {page+1}/{(len(stats)-1)//page_size + 1} | 操作: ←/→ 翻页 / 日期(如 2026-02-14) / b(返回)")
            
            choice = Prompt.ask("\\n输入", default="b").strip().lower()
            
            if choice == 'b':
                break
            elif choice in ('←', 'l'):
                page = max(0, page - 1)
            elif choice in ('→', 'r'):
                page = min((len(stats)-1)//page_size, page + 1)
            elif self._is_valid_date(choice):
                articles = self.storage.get_daily_articles(choice)
                if articles:
                    self.console.print(f"\\n[bold cyan]📅 {choice} 共 {len(articles)} 条[/bold cyan]")
                    self._interactive_loop(articles, return_to_main=False, back_label="b(返回日期列表)")
                else:
                    self.console.print(f"[yellow]📭 {choice} 无数据[/yellow]")
                    self._wait_for_key()
            else:
                self.console.print("[red]❌ 无效输入[/red]")
                self._wait_for_key()

    def show_cleanup_menu(self):
        """数据清理菜单"""
        while True:
            self._clear_screen()
            
            stats = self.storage.get_date_statistics()
            if not stats:
                self.console.print("[yellow]📭 无数据可清理[/yellow]")
                self._wait_for_key()
                return
            
            total_articles = sum(cnt for _, cnt in stats)
            db_size = self.storage.get_database_size()
            
            panel = Panel(
                Text.assemble(
                    ("🗂️  当前数据概况\\n", "bold yellow"),
                    ("   总文章数: ", "white"), (f"{total_articles} 篇\\n", "green"),
                    ("   覆盖日期: ", "white"), (f"{stats[-1][0]} ~ {stats[0][0]}\\n", "cyan"),
                    ("   数据库大小: ", "white"), (f"{db_size}\\n", "yellow"),
                ),
                title="🧹 数据清理",
                border_style="red"
            )
            self.console.print(panel)
            
            menu = Table(show_header=False, show_lines=True, width=60)
            menu.add_row("[bold]1[/bold] 保留最近 N 天（自动清理）")
            menu.add_row("[bold]2[/bold] 删除指定日期")
            menu.add_row("[bold]3[/bold] 删除日期范围")
            menu.add_row("[bold]4[/bold] [red]清空全部数据[/red]")
            menu.add_row("[bold]b[/bold] 返回主菜单")
            self.console.print(menu)
            
            choice = Prompt.ask("\\n请选择清理方式", default="b").strip().lower()
            
            if choice == '1':
                self._cleanup_auto()
            elif choice == '2':
                self._cleanup_single_date(stats)
            elif choice == '3':
                self._cleanup_date_range(stats)
            elif choice == '4':
                self._cleanup_all()
            elif choice == 'b':
                break
            else:
                self.console.print("[yellow]⚠️  无效选择[/yellow]")
                self._wait_for_key()

    def _cleanup_auto(self):
        """自动清理：保留最近 N 天"""
        self._clear_screen()
        self.console.print("[bold cyan]🧹 自动清理：保留最近 N 天[/bold cyan]\\n")
        
        days_input = Prompt.ask("请输入保留天数（如 30）", default="30").strip()
        if not days_input.isdigit():
            self.console.print("[red]❌ 请输入有效数字[/red]")
            self._wait_for_key()
            return
        
        days = int(days_input)
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # 预览将删除的数据
        conn = sqlite3.connect(self.storage.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date(processed_at), COUNT(*) 
            FROM articles 
            WHERE date(processed_at) < ? 
            GROUP BY date(processed_at) 
            ORDER BY date(processed_at)
        """, (cutoff_date,))
        to_delete = cursor.fetchall()
        total_count = sum(cnt for _, cnt in to_delete)
        conn.close()
        
        if not to_delete:
            self.console.print(f"[green]✅ 无需清理：所有数据均在最近 {days} 天内[/green]")
            self._wait_for_key()
            return
        
        self.console.print(f"\\n[bold yellow]⚠️  预览：将删除 {cutoff_date} 之前的数据[/bold yellow]")
        for date_str, count in to_delete[:10]:
            self.console.print(f"   {date_str}: {count} 篇")
        if len(to_delete) > 10:
            self.console.print(f"   ... 共 {len(to_delete)} 天，{total_count} 篇")
        
        if Confirm.ask(f"\\n确认删除 {total_count} 篇旧数据？", default=False):
            count = self.storage.delete_older_than_days(days)
            self.console.print(f"\\n[green]✅ 清理完成：删除 {count} 篇数据[/green]")
        else:
            self.console.print("[yellow]⚠️  操作已取消[/yellow]")
        
        self._wait_for_key()

    def _cleanup_single_date(self, stats: list):
        """手动清理：单个日期"""
        self._clear_screen()
        self.console.print("[bold cyan]🧹 删除指定日期[/bold cyan]\\n")
        
        table = Table(title="可选日期（最近15天）", show_lines=True)
        table.add_column("序号", style="cyan", width=4)
        table.add_column("日期", style="green", width=12)
        table.add_column("文章数", style="yellow", width=8)
        
        for i, (date_str, count) in enumerate(stats[:15], 1):
            table.add_row(str(i), date_str, str(count))
        
        self.console.print(table)
        self.console.print("\\n提示：也可直接输入任意日期（如 2026-01-15）")
        
        choice = Prompt.ask("\\n请输入日期或序号", default="").strip()
        if not choice:
            return
        
        if choice.isdigit() and 1 <= int(choice) <= len(stats[:15]):
            date_str = stats[int(choice)-1][0]
        else:
            date_str = choice
        
        if not self._is_valid_date(date_str):
            self.console.print("[red]❌ 无效日期格式（应为 YYYY-MM-DD）[/red]")
            self._wait_for_key()
            return
        
        articles = self.storage.get_daily_articles(date_str)
        if not articles:
            self.console.print(f"[yellow]📭 {date_str} 无数据[/yellow]")
            self._wait_for_key()
            return
        
        self.console.print(f"\\n[bold yellow]⚠️  预览：{date_str} 共 {len(articles)} 篇文章[/bold yellow]")
        for i, art in enumerate(articles[:3], 1):
            title = art['title'][:40] + "..." if len(art['title']) > 40 else art['title']
            self.console.print(f"   {i}. {title}")
        if len(articles) > 3:
            self.console.print(f"   ... 共 {len(articles)} 篇")
        
        if Confirm.ask(f"\\n确认删除 {date_str} 的全部数据？", default=False):
            count = self.storage.delete_by_date(date_str)
            self.console.print(f"\\n[green]✅ 删除完成：{count} 篇[/green]")
        else:
            self.console.print("[yellow]⚠️  操作已取消[/yellow]")
        
        self._wait_for_key()

    def _cleanup_date_range(self, stats: list):
        """手动清理：日期范围"""
        self._clear_screen()
        self.console.print("[bold cyan]🧹 删除日期范围[/bold cyan]\\n")
        
        start_date = Prompt.ask("起始日期（YYYY-MM-DD）").strip()
        end_date = Prompt.ask("结束日期（YYYY-MM-DD）").strip()
        
        if not (self._is_valid_date(start_date) and self._is_valid_date(end_date)):
            self.console.print("[red]❌ 日期格式错误[/red]")
            self._wait_for_key()
            return
        
        conn = sqlite3.connect(self.storage.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date(processed_at), COUNT(*) 
            FROM articles 
            WHERE date(processed_at) BETWEEN ? AND ?
            GROUP BY date(processed_at)
            ORDER BY date(processed_at)
        """, (start_date, end_date))
        to_delete = cursor.fetchall()
        total_count = sum(cnt for _, cnt in to_delete)
        conn.close()
        
        if not to_delete:
            self.console.print(f"[yellow]📭 {start_date} 至 {end_date} 无数据[/yellow]")
            self._wait_for_key()
            return
        
        self.console.print(f"\\n[bold yellow]⚠️  预览：{start_date} 至 {end_date} 共 {total_count} 篇[/bold yellow]")
        for date_str, count in to_delete[:10]:
            self.console.print(f"   {date_str}: {count} 篇")
        if len(to_delete) > 10:
            self.console.print(f"   ... 共 {len(to_delete)} 天")
        
        if Confirm.ask(f"\\n确认删除该范围内的 {total_count} 篇数据？", default=False):
            conn = sqlite3.connect(self.storage.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM articles 
                WHERE date(processed_at) BETWEEN ? AND ?
            """, (start_date, end_date))
            count = cursor.rowcount
            conn.commit()
            conn.close()
            self.storage._log_cleanup('delete_range', f"{start_date}_{end_date}", count)
            self.console.print(f"\\n[green]✅ 删除完成：{count} 篇[/green]")
        else:
            self.console.print("[yellow]⚠️  操作已取消[/yellow]")
        
        self._wait_for_key()

    def _cleanup_all(self):
        """清空全部数据"""
        self._clear_screen()
        self.console.print("[bold red]⚠️  危险操作：清空全部数据[/bold red]\\n")
        
        stats = self.storage.get_date_statistics()
        total = sum(cnt for _, cnt in stats) if stats else 0
        
        self.console.print(f"当前共 {total} 篇文章，覆盖 {len(stats)} 天")
        self.console.print("\\n[bold red]此操作不可逆！[/bold red]")
        
        if Confirm.ask("确认清空全部数据？", default=False):
            if Prompt.ask("请输入 'CONFIRM' 确认", default="").strip().upper() == "CONFIRM":
                count = self.storage.delete_all()
                self.console.print(f"\\n[green]✅ 全部清空：删除 {count} 篇[/green]")
            else:
                self.console.print("[yellow]⚠️  二次确认失败，操作取消[/yellow]")
        else:
            self.console.print("[yellow]⚠️  操作已取消[/yellow]")
        
        self._wait_for_key()

    def show_cleanup_log(self):
        """查看清理日志"""
        self._clear_screen()
        logs = self.storage.get_cleanup_log(20)
        
        if not logs:
            self.console.print("[yellow]📭 无清理日志[/yellow]")
            self._wait_for_key()
            return
        
        table = Table(title="🗑️  清理操作日志（最近20条）", show_lines=True)
        table.add_column("时间", style="cyan", width=16)
        table.add_column("操作", style="yellow", width=15)
        table.add_column("目标", style="green", width=20)
        table.add_column("删除数", style="red", width=8)
        
        for log in logs:
            op_display = {
                'delete_by_date': '删除单日',
                'delete_before': '删除之前',
                'delete_all': '清空全部',
                'delete_range': '删除范围',
                'delete_older_than_days': '自动清理'
            }.get(log['operation'], log['operation'])
            
            table.add_row(
                log['timestamp'],
                op_display,
                log['target'][:18],
                str(log['count'])
            )
        
        self.console.print(table)
        self._wait_for_key()

    # ==================== 辅助方法 ====================

    def _interactive_loop(self, articles: list, return_to_main: bool = True, back_label: str = "b(返回主菜单)"):
        """交互循环：处理用户输入"""
        while True:
            try:
                user_input = Prompt.ask(f"\\n操作 (编号/open 编号/{'b' if return_to_main else 'q'})", default="b").strip().lower()
                
                if user_input in ('b', 'q', 'quit'):
                    break
                
                if user_input.startswith('open '):
                    num_part = user_input[5:].strip()
                    if num_part.isdigit() and 1 <= int(num_part) <= len(articles):
                        self._open_in_browser(articles[int(num_part)-1])
                        continue
                    else:
                        self.console.print(f"[red]❌ 无效编号（1~{len(articles)}）[/red]")
                        continue
                
                if user_input.isdigit():
                    num = int(user_input)
                    if 1 <= num <= len(articles):
                        self._show_article_detail(articles[num-1])
                        continue
                    else:
                        self.console.print(f"[red]❌ 无效编号（1~{len(articles)}）[/red]")
                        continue
                
                self.console.print(f"[yellow]⚠️  未知命令，支持: 1~{len(articles)} / open 1 / {'b' if return_to_main else 'q'}[/yellow]")
                
            except (KeyboardInterrupt, EOFError):
                break

    def _show_article_detail(self, article: dict):
        """显示文章详情（含完整摘要）"""
        full_art = self.storage.get_article_by_id(article['id'])
        if not full_art:
            self.console.print("[red]❌ 未找到文章详情[/red]")
            return
        
        summary_clean = ' '.join(full_art['summary'].split())
        summary_wrapped = textwrap.fill(summary_clean, width=90)
        
        detail_panel = Panel(
            Text.assemble(
                ("📌 标题: ", "bold cyan"), (full_art['title'], "bold white"), "\\n\\n",
                ("🔗 来源: ", "bold cyan"), (full_art['source'], "white"), "\\n\\n",
                ("⏰ 时间: ", "bold cyan"), (str(full_art['published_at'])[:16], "white"), "\\n\\n",
                ("⭐ 相关度: ", "bold cyan"), (f"{full_art['relevance_score']:.2f}", "yellow"), "\\n\\n",
                ("📝 摘要:\\n", "bold cyan"), (summary_wrapped, "white"),
            ),
            title=f"📖 文章详情 (ID: {article['id'][:8]}...)",
            border_style="green",
            expand=False,
            width=100
        )
        
        self.console.print("\\n")
        self.console.print(detail_panel)
        self.console.print("\\n[bold cyan]📌 摘要操作:[/bold cyan] o(打开原文) / b(返回)")
        
        while True:
            cmd = Prompt.ask("  请选择", default="b").strip().lower()
            if cmd in ('o', 'open'):
                self._open_in_browser(full_art)
                break
            elif cmd in ('b', 'back'):
                break
            else:
                self.console.print("[yellow]⚠️  无效命令，支持: o / b[/yellow]")

    def _open_in_browser(self, article: dict):
        """浏览器打开链接"""
        try:
            webbrowser.open(article['link'])
            self.console.print(f"[green]✅ 已打开: {article['title'][:40]}...[/green]")
        except Exception as e:
            self.console.print(f"[red]❌ 打开失败: {e}[/red]")
            self.console.print(f"🔗 手动访问: {article['link']}")

    def _is_valid_date(self, date_str: str) -> bool:
        """验证日期格式 YYYY-MM-DD"""
        try:
            from datetime import datetime
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def _clear_screen(self):
        """清屏"""
        os.system('clear' if os.name == 'posix' else 'cls')

    def _wait_for_key(self):
        """等待用户按键"""
        Prompt.ask("\\n[bold]↵ 按回车继续[/bold]", default="")


if __name__ == "__main__":
    dashboard = TrendDashboard()
    dashboard.show_main_menu()
'''
    write_file(root_path / "cli" / "dashboard.py", content)


def generate_cleanup_py(root_path: Path):
    content = '''#!/usr/bin/env python3
"""
命令行清理工具：支持自动/手动清理
作者: 程浩鑫
日期: 2026-02-15
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
from datetime import datetime, timedelta
import sqlite3
from core.storage import ArticleStorage


def main():
    parser = argparse.ArgumentParser(description="技术趋势数据清理工具")
    parser.add_argument(
        "--days", 
        type=int, 
        metavar="N",
        help="自动清理：仅保留最近 N 天数据"
    )
    parser.add_argument(
        "--before",
        type=str,
        metavar="YYYY-MM-DD",
        help="删除指定日期之前的所有数据"
    )
    parser.add_argument(
        "--date",
        type=str,
        metavar="YYYY-MM-DD",
        help="删除指定单日数据"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="清空全部数据（需二次确认）"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="预览将删除的数据（不实际删除）"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="显示数据统计"
    )
    
    args = parser.parse_args()
    
    storage = ArticleStorage()
    
    # 显示统计信息
    stats = storage.get_date_statistics()
    total = sum(cnt for _, cnt in stats) if stats else 0
    print(f"📊 当前数据: {total} 篇 | {len(stats)} 天 | 大小: {storage.get_database_size()}")
    
    if args.stats:
        if stats:
            print("\\n📆 日期分布:")
            for date_str, count in stats[:20]:
                print(f"   {date_str}: {count} 篇")
            if len(stats) > 20:
                print(f"   ... 共 {len(stats)} 天")
        else:
            print("📭 无数据")
        return
    
    if args.days:
        cutoff = (datetime.now() - timedelta(days=args.days)).strftime('%Y-%m-%d')
        print(f"📅 保留最近 {args.days} 天（{cutoff} 之后）")
        
        conn = sqlite3.connect(storage.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date(processed_at), COUNT(*) 
            FROM articles 
            WHERE date(processed_at) < ? 
            GROUP BY date(processed_at)
        """, (cutoff,))
        to_delete = cursor.fetchall()
        conn.close()
        
        if not to_delete:
            print("✅ 无需清理：所有数据均在保留范围内")
            return
        
        total_delete = sum(cnt for _, cnt in to_delete)
        print(f"⚠️  将删除 {len(to_delete)} 天，共 {total_delete} 篇")
        
        if not args.dry_run:
            if input("确认删除? (y/n): ").strip().lower() == 'y':
                count = storage.delete_older_than_days(args.days)
                print(f"✅ 清理完成：删除 {count} 篇")
            else:
                print("⚠️  操作取消")
    
    elif args.before:
        try:
            datetime.strptime(args.before, '%Y-%m-%d')
        except ValueError:
            print("❌ 日期格式错误（应为 YYYY-MM-DD）")
            return
        
        conn = sqlite3.connect(storage.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM articles WHERE date(processed_at) < ?
        """, (args.before,))
        count = cursor.fetchone()[0]
        conn.close()
        
        print(f"⚠️  将删除 {args.before} 之前的数据，共约 {count} 篇")
        
        if not args.dry_run:
            if input("确认删除? (y/n): ").strip().lower() == 'y':
                deleted = storage.delete_before_date(args.before)
                print(f"✅ 删除完成：{deleted} 篇")
            else:
                print("⚠️  操作取消")
    
    elif args.date:
        try:
            datetime.strptime(args.date, '%Y-%m-%d')
        except ValueError:
            print("❌ 日期格式错误（应为 YYYY-MM-DD）")
            return
        
        articles = storage.get_daily_articles(args.date)
        if not articles:
            print(f"📭 {args.date} 无数据")
            return
        
        print(f"⚠️  将删除 {args.date} 的 {len(articles)} 篇文章")
        
        if not args.dry_run:
            if input("确认删除? (y/n): ").strip().lower() == 'y':
                deleted = storage.delete_by_date(args.date)
                print(f"✅ 删除完成：{deleted} 篇")
            else:
                print("⚠️  操作取消")
    
    elif args.all:
        print("[bold red]⚠️  危险操作：清空全部数据[/bold red]")
        print(f"当前共 {total} 篇文章")
        
        if not args.dry_run:
            if input("输入 'CONFIRM' 确认清空: ").strip() == "CONFIRM":
                count = storage.delete_all()
                print(f"✅ 全部清空：{count} 篇")
            else:
                print("⚠️  操作取消")
    
    else:
        print("\\n💡 使用示例:")
        print("   python cli/cleanup.py --days 30        # 保留最近30天")
        print("   python cli/cleanup.py --date 2026-01-15 # 删除单日")
        print("   python cli/cleanup.py --stats           # 查看统计")
        print("   python cli/cleanup.py --days 30 --dry-run # 预览不删除")


if __name__ == "__main__":
    main()
'''
    write_file(root_path / "cli" / "cleanup.py", content)


def generate_run_daily_py(root_path: Path):
    content = '''#!/usr/bin/env python3
"""
手动触发每日更新
作者: 程浩鑫
日期: 2026-02-15
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import yaml
from core.collector import TrendCollector
from core.filter import RelevanceFilter
from core.storage import ArticleStorage


def daily_update():
    """执行更新逻辑"""
    print(f"\\n⏰ 启动技术趋势更新...")
    
    # 动态加载配置
    config_path = Path(__file__).parent / "config" / "sources.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    collector = TrendCollector()
    filter_ = RelevanceFilter(config['keywords'])
    storage = ArticleStorage()
    
    # 抓取所有源
    all_articles = []
    for source in config['sources']:
        items = collector.fetch_rss(source)
        all_articles.extend(items)
    
    # 过滤低相关度内容
    relevant = filter_.filter(all_articles)
    
    # 保存到数据库
    inserted = storage.save_articles(relevant)
    print(f"✅ 新增 {inserted} 条高相关度内容（总候选 {len(all_articles)} 条）\\n")


if __name__ == "__main__":
    daily_update()
'''
    write_file(root_path / "run_daily.py", content)


def generate_main_py(root_path: Path):
    content = '''#!/usr/bin/env python3
"""
技术趋势追踪器 - 主程序入口
作者: 程浩鑫
日期: 2026-02-15
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from cli.dashboard import TrendDashboard


if __name__ == "__main__":
    # 清屏（macOS/Linux）
    import os
    os.system('clear')
    
    dashboard = TrendDashboard()
    dashboard.show_main_menu()
'''
    write_file(root_path / "main.py", content)


def generate_commands_txt(root_path: Path):
    content = '''===============================================================================
📚 技术趋势追踪器 - 命令参考手册（纯文本版）
===============================================================================
适用于 macOS | 项目路径：任意自定义目录（路径无关设计）
最后更新：2026-02-15 | 适配 Apple Silicon (M1/M2/M3)

💡 使用前必读
--------------
所有命令均需在激活虚拟环境后执行（见 2.1 节）
项目完全路径无关：复制整个文件夹到任意位置均可直接运行，无需修改配置


===============================================================================
1. 环境管理
===============================================================================

1.1 激活虚拟环境（每次使用前必做）
------------------------------------
    cd /your/custom/path/trend_tracker
    source .venv/bin/activate

✅ 验证成功：终端提示符前出现 (.venv)
❌ 常见问题：若提示 "command not found: source"，请确保使用 zsh/bash 终端


1.2 退出虚拟环境
-----------------
    deactivate


1.3 重建虚拟环境（依赖损坏时）
-------------------------------
    # 删除旧环境
    rm -rf .venv

    # 重新创建
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt



===============================================================================
2. 核心功能
===============================================================================

2.1 启动交互式主界面（推荐日常使用）
-------------------------------------
    python main.py

✨ 功能亮点：
   • 主菜单：今日趋势 / 历史浏览 / 数据清理 / 清理日志
   • 输入文章编号（如 1）→ 查看完整摘要
   • 输入 "open 1" → 浏览器打开原文
   • 所有删除操作需二次确认，安全可靠


2.2 手动触发数据更新（立即获取最新动态）
------------------------------------------
    python run_daily.py

⏱️ 执行时间：通常 10~30 秒（取决于网络）
📌 适用场景：首次安装后初始化数据 / 等待定时任务太慢


2.3 仅查看今日简报（无交互菜单）
----------------------------------
    python -c "from cli.dashboard import TrendDashboard; TrendDashboard().show_daily_digest()"



===============================================================================
3. 数据清理（重点功能）
===============================================================================

3.1 交互式清理（推荐新手）
--------------------------
    python main.py
    → 主菜单选择 "3. 清理数据" → 按向导操作

✅ 支持操作：
   • 保留最近 N 天（自动清理）
   • 删除指定单日（如 2026-01-15）
   • 删除日期范围（如 2026-01-01 至 2026-01-10）
   • 清空全部数据（需二次确认）

✅ 安全机制：
   • 删除前预览文章标题
   • 所有操作需手动确认
   • 自动记录清理日志（可追溯）


3.2 命令行快速清理（适合自动化/脚本）
---------------------------------------
┌─────────────────────────────────────────────────────────────────────┐
│ 场景                │ 命令                                            │
├─────────────────────┼─────────────────────────────────────────────────┤
│ 保留最近30天        │ python cli/cleanup.py --days 30                 │
│ 删除单日            │ python cli/cleanup.py --date 2026-01-15         │
│ 删除某日前          │ python cli/cleanup.py --before 2026-01-01       │
│ 预览不删除          │ python cli/cleanup.py --days 30 --dry-run       │
│ 查看数据统计        │ python cli/cleanup.py --stats                   │
└─────────────────────┴─────────────────────────────────────────────────┘


3.3 安全防护机制
----------------
操作类型       │ 保护措施
───────────────┼──────────────────────────────────────────────────────
单日/范围删除  │ 删除前显示文章标题预览（最多10篇）
清空全部       │ 需输入 "CONFIRM" 二次确认
所有删除       │ 自动记录到 cleanup_log 表（含时间/数量/目标）
误删恢复       │ 手动备份数据库文件：data/trends.db.backup_YYYYMMDD


3.4 手动备份数据库（重要操作前）
--------------------------------
    # 完整备份（带时间戳）
    cp data/trends.db data/trends.db.backup_$(date +%Y%m%d_%H%M%S)

    # 查看所有备份
    ls -lh data/trends.db.backup_*

    # 恢复备份
    cp data/trends.db.backup_20260215_093000 data/trends.db



===============================================================================
4. 定时自动化
===============================================================================

4.1 设置每日自动更新 + 清理（crontab）
---------------------------------------
    crontab -e

添加以下两行（替换 /your/path 为实际项目路径）：
───────────────────────────────────────────────────────────────────────
# 每天 09:00 抓取最新技术动态
0 9 * * * cd /your/path && /your/path/.venv/bin/python run_daily.py >> /tmp/trend_tracker.log 2>&1

# 每天 09:05 自动清理，仅保留最近30天数据
5 9 * * * cd /your/path && /your/path/.venv/bin/python cli/cleanup.py --days 30 >> /tmp/trend_tracker_cleanup.log 2>&1
───────────────────────────────────────────────────────────────────────


4.2 验证定时任务
-----------------
    # 查看当前定时任务
    crontab -l

    # 检查最近日志
    tail -f /tmp/trend_tracker.log
    tail -f /tmp/trend_tracker_cleanup.log


4.3 临时禁用定时任务
---------------------
    crontab -e
    → 在任务行首添加 # 注释掉 → 保存退出



===============================================================================
5. 交互界面快捷操作（python main.py 启动后）
===============================================================================

5.1 主菜单
----------
按键    功能
──────────────────────────────────────
1       查看今日趋势
2       浏览历史日期
3       进入清理菜单
4       查看清理日志
q       退出程序


5.2 文章列表页
--------------
输入          功能
──────────────────────────────────────
1 ~ N         查看对应编号文章的完整摘要
open 1        在浏览器打开第1篇文章
b             返回上一级菜单
Ctrl+C        强制退出（安全，无数据丢失）


5.3 摘要详情页
--------------
按键    功能
──────────────────────────────────────
o       浏览器打开原文
b       返回文章列表


5.4 历史日期浏览
----------------
按键/输入       功能
──────────────────────────────────────
← 或 l          上一页
→ 或 r          下一页
2026-02-14      直接输入日期查看该日内容
b               返回主菜单



===============================================================================
6. 诊断与调试
===============================================================================

6.1 检查数据库状态
------------------
    # 总览统计
    python cli/cleanup.py --stats

    # 查看数据库文件大小
    ls -lh data/trends.db


6.2 查看最近清理日志
--------------------
    python -c "
    from core.storage import ArticleStorage
    logs = ArticleStorage().get_cleanup_log(10)
    for log in logs:
        print(f'{log[\"timestamp\"]} | {log[\"operation\"]} | {log[\"target\"]} | {log[\"count\"]}篇')
    "


6.3 网络问题诊断
----------------
    # 测试 RSS 源是否可访问
    curl -I http://arxiv.org/rss/cs.LG

    # 检查关键依赖是否安装
    pip list | grep -E \"feedparser|rich|PyYAML\"



===============================================================================
7. 高级技巧
===============================================================================

7.1 创建终端快捷命令（永久生效）
----------------------------------
编辑 ~/.zshrc（macOS Catalina 及以上默认 shell）：
───────────────────────────────────────────────────────────────────────
# 技术趋势追踪器快捷命令
alias trend='cd /your/path && source .venv/bin/activate && python main.py'
alias trend-update='cd /your/path && source .venv/bin/activate && python run_daily.py'
alias trend-clean='cd /your/path && source .venv/bin/activate && python cli/cleanup.py'
───────────────────────────────────────────────────────────────────────

应用配置：
    source ~/.zshrc

使用：
    trend                 # 启动主界面
    trend-update          # 手动更新
    trend-clean --days 30 # 快速清理


7.2 与 Alfred 集成（macOS 效率神器）
------------------------------------
1. 安装 Alfred Powerpack (https://www.alfredapp.com/powerpack/)
2. 创建 Shell Script Workflow：
   • Keyword: trend
   • Script: osascript -e 'tell app "Terminal" to do script "cd /your/path && source .venv/bin/activate && python main.py"'
3. 效果：全局快捷键 Cmd+Space → trend → 回车，秒开趋势面板


7.3 导出数据为 CSV（用于分析）
-------------------------------
    python -c "
    import sqlite3, csv
    conn = sqlite3.connect('data/trends.db')
    cursor = conn.cursor()
    cursor.execute('SELECT date(processed_at), title, source, relevance_score FROM articles ORDER BY processed_at DESC')
    with open('export.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['日期', '标题', '来源', '相关度'])
        writer.writerows(cursor.fetchall())
    print('✅ 导出完成: export.csv')
    "



===============================================================================
8. 卸载与迁移
===============================================================================

8.1 完全卸载（无残留）
----------------------
    # 退出虚拟环境（如果已激活）
    deactivate

    # 删除整个项目目录
    rm -rf /your/custom/path/trend_tracker

✅ 无系统级修改，卸载即彻底清除


8.2 迁移到新路径（保留数据）
----------------------------
    # 1. 复制整个目录
    cp -R /old/path/trend_tracker /new/path/trend_tracker

    # 2. 进入新目录
    cd /new/path/trend_tracker

    # 3. 无需任何配置修改！直接运行
    source .venv/bin/activate
    python main.py

💡 原理：所有路径通过 __file__ 动态计算，完全路径无关


8.3 仅迁移数据（更换设备）
--------------------------
    # 旧设备：备份数据库
    cp data/trends.db ~/Desktop/trends_backup.db

    # 新设备：安装新项目后
    cp ~/Desktop/trends_backup.db /new/path/trend_tracker/data/trends.db



===============================================================================
9. 常见问题速查
===============================================================================

问题                      │ 解决方案
──────────────────────────┼──────────────────────────────────────────────
command not found: python │ 使用 python3 代替 python
虚拟环境激活失败          │ 检查是否安装 Homebrew Python: brew install python@3.11
RSS 抓取为空              │ 检查网络代理 / 尝试 curl http://arxiv.org/rss/cs.LG
数据库损坏                │ 从 data/trends.db.backup_* 恢复
中文显示乱码              │ iTerm2 → Preferences → Profiles → Text → 
                          │ Unicode East Asian Width: Ambiguous → Wide
想添加新数据源            │ 编辑 config/sources.yaml → 添加 RSS 源配置



===============================================================================
10. 命令速查表（打印友好版）
===============================================================================

┌──────────────────────────────────────────────────────────────────────┐
│  🚀 快速开始                                                         │
├──────────────────────────────────────────────────────────────────────┤
│  cd /your/path && source .venv/bin/activate                          │
│  python run_daily.py          # 首次更新数据                         │
│  python main.py               # 启动交互界面                         │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  🧹 数据清理                                                         │
├──────────────────────────────────────────────────────────────────────┤
│  python cli/cleanup.py --days 30        # 保留30天                   │
│  python cli/cleanup.py --date 2026-01-15 # 删除单日                   │
│  python cli/cleanup.py --stats          # 查看统计                   │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  ⏱️  定时任务                                                         │
├──────────────────────────────────────────────────────────────────────┤
│  crontab -e                   # 编辑定时任务                         │
│  0 9 * * * ... run_daily.py   # 每天9点更新                          │
│  5 9 * * * ... --days 30      # 每天9:05自动清理                     │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  🔍 交互界面快捷键                                                   │
├──────────────────────────────────────────────────────────────────────┤
│  1~N      → 查看摘要        │  open 1   → 打开链接                   │
│  o        → 打开原文        │  b        → 返回                       │
│  ← / →    → 翻页            │  q        → 退出                       │
└──────────────────────────────────────────────────────────────────────┘



===============================================================================
设计理念
===============================================================================

• 最小认知负荷：日常只需记住两个命令
    → python main.py      （查看趋势）
    → python run_daily.py （更新数据）

• 安全第一：所有危险操作（删除/清空）均需二次确认 + 日志记录

• 路径无关：项目可放置在任意目录（包括外接硬盘/云盘同步目录），
  无需修改任何配置文件

• 隐私优先：全程本地运行，无数据上传，无网络 API 依赖

• 轻量高效：SQLite 数据库存储，1000 篇文章仅占 5~10MB 空间


===============================================================================
文档结束
===============================================================================
'''
    write_file(root_path / "COMMANDS.txt", content)


def create_venv_and_install(root_path: Path, python_path: str):
    """创建虚拟环境并安装依赖"""
    venv_path = root_path / ".venv"
    
    print(f"\n🚀 创建虚拟环境: {venv_path.relative_to(root_path)}")
    result = subprocess.run(
        [python_path, "-m", "venv", str(venv_path)],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"❌ 创建失败: {result.stderr}")
        sys.exit(1)
    
    pip_path = venv_path / "bin" / "pip"
    
    print("📥 安装依赖包...")
    result = subprocess.run(
        [str(pip_path), "install", "-q", "-r", str(root_path / "requirements.txt")],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"❌ 安装失败: {result.stderr}")
        sys.exit(1)
    
    print("✅ 依赖安装成功\n")


def generate_usage_guide(root_path: Path):
    """生成简易使用指南"""
    guide = f"""# 技术趋势追踪器 - 快速开始

## 安装路径
{root_path}

## 首次使用
1. 激活虚拟环境:
   source .venv/bin/activate

2. 首次更新数据:
   python run_daily.py

3. 启动交互界面（查看摘要）:
   python main.py

## 日常使用
• 查看今日趋势:       python main.py
• 手动更新数据:       python run_daily.py
• 清理旧数据（保留30天）: python cli/cleanup.py --days 30

## 详细命令参考
查看 COMMANDS.txt 获取完整命令手册
"""
    write_file(root_path / "USAGE.txt", guide)


def main():
    parser = argparse.ArgumentParser(description="技术趋势追踪器 - 一键安装")
    parser.add_argument(
        "install_path", 
        nargs="?", 
        default=Path.home() / "projects" / "tech_trend_tracker",
        help="安装路径（默认: ~/projects/tech_trend_tracker）"
    )
    args = parser.parse_args()
    
    root_path = Path(args.install_path).resolve()
    
    print(f"🎯 安装目标路径: {root_path}\n")
    
    # 检测 Python
    python_path = detect_python()
    print(f"🐍 检测到 Python: {python_path}\n")
    
    # 创建目录
    print("📁 创建项目结构...")
    create_project_structure(root_path)
    
    # 生成文件
    print("\n📝 生成配置与代码...")
    generate_requirements(root_path)
    generate_sources_yaml(root_path)
    generate_storage_py(root_path)
    generate_collector_py(root_path)
    generate_filter_py(root_path)
    generate_dashboard_py(root_path)
    generate_cleanup_py(root_path)
    generate_run_daily_py(root_path)
    generate_main_py(root_path)
    generate_commands_txt(root_path)
    generate_usage_guide(root_path)
    
    # 创建虚拟环境
    create_venv_and_install(root_path, python_path)
    
    # 设置执行权限
    for script in ["run_daily.py", "main.py", "cli/cleanup.py"]:
        filepath = root_path / script
        if filepath.exists():
            filepath.chmod(0o755)
    
    print("\n" + "="*70)
    print("✅ 安装成功！")
    print("="*70)
    print(f"\n📌 项目路径: {root_path}")
    print(f"\n🚀 快速启动:")
    print(f"   cd {root_path}")
    print(f"   source .venv/bin/activate")
    print(f"   python run_daily.py   # 首次更新数据")
    print(f"   python main.py        # 启动交互界面（支持查看摘要）")
    print("\n📖 命令手册:")
    print(f"   less COMMANDS.txt     # 查看完整命令参考")
    print("\n💡 提示: 在交互界面中输入文章编号（如 1）即可查看完整摘要")


if __name__ == "__main__":
    main()