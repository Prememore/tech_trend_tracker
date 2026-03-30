"""
过滤模块：支持配置化匹配范围（标题/摘要/两者）
作者: 程浩鑫
日期: 2026-02-15
"""

import re
from typing import List, Dict
from pathlib import Path
import yaml


class RelevanceFilter:
    """相关性过滤器 - 支持配置化匹配范围"""

    def __init__(self, keywords: Dict[str, List[str]]):
        self.primary = [kw.lower() for kw in keywords.get('primary', [])]
        self.secondary = [kw.lower() for kw in keywords.get('secondary', [])]
        
        # 从配置读取匹配范围（默认"both"保持兼容）
        self.match_scope = "title"  # ✅ 默认仅标题（按你的需求）
        try:
            config_path = Path(__file__).parent.parent / "config" / "sources.yaml"
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            self.match_scope = config.get('settings', {}).get('match_scope', 'title')
            print(f"⚙️  匹配范围: {self.match_scope} (title/summary/both)")
        except:
            pass

    def _match_keywords(self, text: str, keywords: List[str]) -> List[str]:
        text_lower = text.lower()
        matched = []
        for kw in keywords:
            if " " in kw:
                pattern = re.escape(kw)
            else:
                pattern = r'\b' + re.escape(kw) + r'\b'
            if re.search(pattern, text_lower):
                matched.append(kw)
        return matched

    def score(self, title: str, summary: str = "") -> float:
        """
        根据配置的 match_scope 计算相关性分数
        """
        # ✅ 核心逻辑：按配置选择匹配文本
        if self.match_scope == "title":
            text_to_match = title
        elif self.match_scope == "summary":
            text_to_match = summary
        else:  # "both" (default fallback)
            text_to_match = f"{title} {summary}"
        
        score = 0.0
        primary_matches = self._match_keywords(text_to_match, self.primary)
        if primary_matches:
            score += 0.6
        
        secondary_matches = self._match_keywords(text_to_match, self.secondary)
        secondary_score = min(0.4, len(secondary_matches) * 0.15)
        score = min(1.0, score + secondary_score)
        
        return round(score, 2)

    def filter(self, articles: List[Dict]) -> List[Dict]:
        scored = []
        try:
            config_path = Path(__file__).parent.parent / "config" / "sources.yaml"
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            self.threshold = float(config.get('settings', {}).get('relevance_threshold', 0.45))
            print(f"⚙️  相关度阈值: {self.threshold:.2f}")
        except Exception as e:
            print(f"⚠️  阈值配置加载失败，使用默认 0.45 | 错误: {e}")
        for art in articles:
            score = self.score(art['title'], art.get('summary', ''))
            if score >= self.threshold:
                art['relevance_score'] = score
                scored.append(art)
        scored.sort(key=lambda x: x['relevance_score'], reverse=True)
        return scored