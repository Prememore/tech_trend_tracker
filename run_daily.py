#!/usr/bin/env python3
"""
每日更新脚本：通过 arXiv API 抓取目标文献（精简可靠版）
作者: 程浩鑫
日期: 2026-02-15
"""

import sys
from pathlib import Path
import yaml
import json
from datetime import datetime


# ============ 路径与配置 ============

PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

def load_config():
    """加载关键词配置（优先使用自定义关键词）"""
    config_path = PROJECT_ROOT / "config" / "sources.yaml"
    keywords_path = PROJECT_ROOT / "config" / "keywords.json"
    
    if not config_path.exists():
        print(f"❌ 配置文件不存在: {config_path}")
        sys.exit(1)
    
    try:
        # 优先加载自定义关键词配置
        if keywords_path.exists():
            try:
                with open(keywords_path, 'r', encoding='utf-8') as f:
                    custom_config = json.load(f)
                keywords = {
                    'primary': custom_config.get('primary', []),
                    'secondary': custom_config.get('secondary', [])
                }
                print(f"✅ 使用自定义关键词配置 ({len(keywords['primary'])}个主关键词, {len(keywords['secondary'])}个次要关键词)")
                return keywords
            except Exception as e:
                print(f"⚠️  自定义关键词加载失败: {e}，回退到默认配置")
        
        # 回退到默认配置
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        keywords = config.get('keywords', {})
        if not keywords.get('primary'):
            print("⚠️  未检测到关键词库，使用默认关键词")
            keywords = {
                'primary': ['reinforcement learning', 'chaos synchronization'],
                'secondary': ['control']
            }
        
        print(f"✅ 使用默认关键词配置 ({len(keywords['primary'])}个主关键词, {len(keywords['secondary'])}个次要关键词)")
        return keywords
    
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        sys.exit(1)


# ============ 主流程 ============

def main():
    print("\n" + "="*70)
    print("⏰ 启动技术趋势更新（arXiv API 模式）")
    print("="*70 + "\n")
    
    # 1. 加载配置
    keywords = load_config()
    
    # 2. 初始化采集器
    try:
        from core.collector import ArxivCollector
        collector = ArxivCollector()
    except Exception as e:
        print(f"❌ 采集器初始化失败: {e}")
        sys.exit(1)
    
    # 3. 初始化过滤器
    try:
        from core.filter import RelevanceFilter
        filter_ = RelevanceFilter(keywords)
    except Exception as e:
        print(f"❌ 过滤器初始化失败: {e}")
        sys.exit(1)
    
    # 4. 初始化存储
    try:
        from core.storage import ArticleStorage
        storage = ArticleStorage()
    except Exception as e:
        print(f"❌ 存储初始化失败: {e}")
        sys.exit(1)
    
    # 5. 抓取文献（核心：调用新接口 fetch_articles）
    print("📡 开始抓取 arXiv 文献（HTTPS API）...\n")
    try:
        # 默认抓取最多1000篇（支持分页）
        raw_articles = collector.fetch_articles(keywords, max_results=1000)
    except Exception as e:
        print(f"\n❌ 抓取过程异常: {e}")
        sys.exit(1)
    
    if not raw_articles:
        print("\n⚠️  未抓取到任何文献")
        print("💡 可能原因及解决方案:")
        print("   • 网络问题: 测试 'curl -I \"https://export.arxiv.org/api/query?search_query=cat:cs.SY&max_results=1\"'")
        print("   • 关键词过严: 检查 config/sources.yaml → keywords.primary 必须为英文")
        print("   • 时间范围过小: 临时修改 config/sources.yaml → search_days: 30")
        return
    
    # 6. 过滤
    print("\n🔍 进行相关性过滤...")
    filtered = filter_.filter(raw_articles)
    
    if not filtered:
        print("⚠️  所有文献相关度 < 阈值，保留前10篇供参考")
        filtered = raw_articles[:10]
    
    # 7. 保存
    print("\n💾 保存到本地数据库...")
    inserted = storage.save_articles(filtered)
    
    # 8. 统计输出
    total_in_db = sum(cnt for _, cnt in storage.get_date_statistics())
    
    print("\n" + "="*70)
    print("📊 更新完成")
    print("="*70)
    print(f"   原始抓取:    {len(raw_articles)} 篇")
    print(f"   相关度过滤:  {len(filtered)} 篇 ({len(filtered)/len(raw_articles)*100:.1f}%)")
    print(f"   新增入库:    {inserted} 篇")
    print(f"   数据库总量:  {total_in_db} 篇")
    print(f"   数据库大小:  {storage.get_database_size()}")
    print("="*70)
    
    print("\n💡 下一步:")
    print("   • 启动 Web 服务: python main.py")
    print("   • 清理旧数据: 通过 Web 界面或 API /api/cleanup\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  用户中断，更新已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 未预期错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)