"""
关键词管理器：支持自定义论文主题关键词
作者: 程浩鑫
日期: 2026-03-24
"""

import yaml
from pathlib import Path
from typing import List, Dict, Optional
import json


class KeywordManager:
    """关键词管理器 - 支持动态添加/删除/管理论文主题关键词"""
    
    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "sources.yaml"
        self.config_path = config_path
        self.keywords_file = Path(__file__).parent.parent / "config" / "keywords.json"
        self._load_keywords()
    
    def _load_keywords(self):
        """加载关键词配置"""
        # 首先尝试从 keywords.json 加载（用户自定义关键词）
        if self.keywords_file.exists():
            try:
                with open(self.keywords_file, 'r', encoding='utf-8') as f:
                    self.custom_keywords = json.load(f)
            except Exception as e:
                print(f"⚠️  自定义关键词文件加载失败: {e}")
                self.custom_keywords = {}
        else:
            self.custom_keywords = {}
        
        # 如果没有自定义关键词，则从 sources.yaml 加载默认关键词
        if not self.custom_keywords:
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                default_keywords = config.get('keywords', {})
                self.custom_keywords = {
                    'primary': default_keywords.get('primary', []),
                    'secondary': default_keywords.get('secondary', []),
                    'created_at': 'default',
                    'description': '默认关键词配置'
                }
            except Exception as e:
                print(f"⚠️  配置文件加载失败: {e}")
                self.custom_keywords = {
                    'primary': ['reinforcement learning', 'chaos synchronization'],
                    'secondary': ['control'],
                    'created_at': 'default',
                    'description': '系统默认'
                }
    
    def _save_keywords(self):
        """保存关键词到文件"""
        try:
            # 确保目录存在
            self.keywords_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存自定义关键词
            with open(self.keywords_file, 'w', encoding='utf-8') as f:
                json.dump(self.custom_keywords, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 关键词配置已保存到: {self.keywords_file}")
            return True
        except Exception as e:
            print(f"❌ 关键词保存失败: {e}")
            return False
    
    def get_keywords(self) -> Dict[str, List[str]]:
        """获取当前使用的关键词"""
        return {
            'primary': self.custom_keywords.get('primary', []),
            'secondary': self.custom_keywords.get('secondary', [])
        }
    
    def add_primary_keyword(self, keyword: str) -> bool:
        """添加主关键词"""
        if not keyword or not keyword.strip():
            print("❌ 关键词不能为空")
            return False
        
        keyword = keyword.strip().lower()
        primary_list = self.custom_keywords.get('primary', [])
        
        if keyword in primary_list:
            print(f"⚠️  关键词 '{keyword}' 已存在")
            return False
        
        primary_list.append(keyword)
        self.custom_keywords['primary'] = primary_list
        return self._save_keywords()
    
    def add_secondary_keyword(self, keyword: str) -> bool:
        """添加次要关键词"""
        if not keyword or not keyword.strip():
            print("❌ 关键词不能为空")
            return False
        
        keyword = keyword.strip().lower()
        secondary_list = self.custom_keywords.get('secondary', [])
        
        if keyword in secondary_list:
            print(f"⚠️  关键词 '{keyword}' 已存在")
            return False
        
        secondary_list.append(keyword)
        self.custom_keywords['secondary'] = secondary_list
        return self._save_keywords()
    
    def remove_primary_keyword(self, keyword: str) -> bool:
        """删除主关键词"""
        keyword = keyword.strip().lower()
        primary_list = self.custom_keywords.get('primary', [])
        
        if keyword not in primary_list:
            print(f"❌ 关键词 '{keyword}' 不存在")
            return False
        
        primary_list.remove(keyword)
        self.custom_keywords['primary'] = primary_list
        return self._save_keywords()
    
    def remove_secondary_keyword(self, keyword: str) -> bool:
        """删除次要关键词"""
        keyword = keyword.strip().lower()
        secondary_list = self.custom_keywords.get('secondary', [])
        
        if keyword not in secondary_list:
            print(f"❌ 关键词 '{keyword}' 不存在")
            return False
        
        secondary_list.remove(keyword)
        self.custom_keywords['secondary'] = secondary_list
        return self._save_keywords()
    
    def list_keywords(self) -> Dict:
        """列出所有关键词信息"""
        return {
            'primary': self.custom_keywords.get('primary', []),
            'secondary': self.custom_keywords.get('secondary', []),
            'description': self.custom_keywords.get('description', ''),
            'created_at': self.custom_keywords.get('created_at', ''),
            'total_primary': len(self.custom_keywords.get('primary', [])),
            'total_secondary': len(self.custom_keywords.get('secondary', []))
        }
    
    def set_description(self, description: str) -> bool:
        """设置关键词配置描述"""
        self.custom_keywords['description'] = description.strip()
        return self._save_keywords()
    
    def reset_to_default(self) -> bool:
        """重置为默认关键词配置"""
        # 从 sources.yaml 读取默认配置
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            default_keywords = config.get('keywords', {})
            
            self.custom_keywords = {
                'primary': default_keywords.get('primary', []),
                'secondary': default_keywords.get('secondary', []),
                'created_at': 'default_reset',
                'description': '重置为默认配置'
            }
            
            # 删除自定义关键词文件，让系统回到默认状态
            if self.keywords_file.exists():
                self.keywords_file.unlink()
                print("✅ 已删除自定义关键词配置，恢复默认设置")
            
            return True
        except Exception as e:
            print(f"❌ 重置失败: {e}")
            return False
    
    def export_keywords(self, filepath: str) -> bool:
        """导出关键词配置到文件"""
        try:
            export_path = Path(filepath)
            export_path.parent.mkdir(parents=True, exist_ok=True)
            
            export_data = {
                'keywords': self.custom_keywords,
                'exported_at': self._get_current_time(),
                'version': '1.0'
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 关键词配置已导出到: {export_path}")
            return True
        except Exception as e:
            print(f"❌ 导出失败: {e}")
            return False
    
    def import_keywords(self, filepath: str) -> bool:
        """从文件导入关键词配置"""
        try:
            import_path = Path(filepath)
            if not import_path.exists():
                print(f"❌ 文件不存在: {filepath}")
                return False
            
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # 验证数据格式
            if 'keywords' not in import_data:
                print("❌ 无效的关键词配置文件格式")
                return False
            
            self.custom_keywords = import_data['keywords']
            self.custom_keywords['created_at'] = self._get_current_time()
            
            return self._save_keywords()
        except Exception as e:
            print(f"❌ 导入失败: {e}")
            return False
    
    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
