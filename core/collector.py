"""
采集模块：arXiv API 抓取器（完整修复版）
✅ 正确命名空间处理（默认命名空间 xmlns="..."）
✅ 国内稳定镜像源（清华/azure/official 三选一）
✅ 宽松 User-Agent（避免防火墙拦截）
✅ 配置化时间范围（search_days）
✅ 完整错误处理 + 调试输出
作者: 程浩鑫
日期: 2026-02-15
"""

import requests
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import List, Dict
import hashlib
from pathlib import Path
import yaml
import re

from core.text_utils import clean_latex


class ArxivCollector:
    """
    arXiv API 采集器 - 专为国内网络环境优化
    核心特性:
      • 使用清华镜像（https://arxiv.org/api/query）提升国内访问稳定性
      • 正确处理 Atom 默认命名空间（关键修复！）
      • 配置化时间范围（7天/30天一键切换）
      • 自动标签推断（中文展示）
    """

    def __init__(self):
        # Atom 命名空间（arXiv XML 使用默认命名空间 xmlns="..."）
        self.ns = 'http://www.w3.org/2005/Atom'
        
        # 默认配置：清华镜像 + 7天范围
        self.api_url = "https://arxiv.org/api/query"
        self.days_back = 7
        self.mirror_name = "tsinghua"
        
        # 从配置文件加载（可覆盖默认值）
        config_path = Path(__file__).parent.parent / "config" / "sources.yaml"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 读取镜像源配置
            mirror = config.get('settings', {}).get('arxiv_mirror', 'tsinghua').lower()
            if mirror == 'official':
                self.api_url = "https://export.arxiv.org/api/query"
                self.mirror_name = "official"
            elif mirror == 'azure':
                self.api_url = "https://arxiv-export1.eastus2.cloudapp.azure.com/api/query"
                self.mirror_name = "azure"
            else:  # 'tsinghua' (default)
                self.api_url = "https://arxiv.org/api/query"
                self.mirror_name = "tsinghua"
            
            # 读取搜索时间范围
            self.days_back = config.get('settings', {}).get('search_days', 7)
            
            # 验证时间范围配置
            if not isinstance(self.days_back, int) or self.days_back <= 0:
                print(f"⚠️  时间范围配置无效 ({self.days_back})，使用默认值 7 天")
                self.days_back = 7
            elif self.days_back > 365:
                print(f"⚠️  时间范围过大 ({self.days_back}天)，建议不超过365天")
            
            print(f"⚙️  API 镜像源: {self.mirror_name} ({self.api_url})")
            print(f"⚙️  搜索时间范围: 截止检索当天往前 {self.days_back} 天")
        
        except FileNotFoundError:
            print(f"⚠️  配置文件未找到，使用默认设置")
        except Exception as e:
            print(f"⚠️  配置加载异常，使用默认设置 | 错误: {e}")
        
        # arXiv API 速率限制：官方要求 ≤ 1 次/3秒，我们保守设置 3.5秒/次
        self.min_interval = 3.5
        self.last_request_time = 0

    def _wait_for_rate_limit(self):
        """遵守 arXiv API 速率限制（3.5秒/次）"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()

    def _build_query(self, keywords: Dict[str, List[str]]) -> str:
        """
        构建 arXiv 搜索查询字符串
        查询结构: (分类过滤) AND (关键词过滤) AND (时间范围)
        """
        # 分类过滤：覆盖强化学习 + 混沌同步控制核心领域
        categories = [
            "cs.LG",    # Machine Learning (RL 算法)
            "cs.SY",    # Systems and Control (混沌同步主战场！)
            "nlin.CD",  # Chaotic Dynamics (混沌理论)
            "cs.RO",    # Robotics (RL 控制应用)
            "eess.SY"   # Electrical Engineering Systems (控制工程)
        ]
        cat_query = " OR ".join([f"cat:{c}" for c in categories])
        
        # 关键词过滤：仅使用前6个主关键词（避免 URL 过长被截断）
        primary_kws = keywords.get('primary', [])
        if not primary_kws:
            # 无配置时使用安全默认值
            primary_kws = ["reinforcement learning", "chaos synchronization"]
        
        # 限制数量 + 清理特殊字符（避免 XML 转义问题）
        primary_kws = primary_kws[:6]
        kw_terms = []
        for kw in primary_kws:
            # 移除可能干扰查询的特殊字符
            safe_kw = re.sub(r'[^\w\s\-]', '', kw)
            kw_terms.append(f'abs:"{safe_kw}"')
        
        kw_query = " OR ".join(kw_terms)
        
        # 时间范围过滤：截止检索当天往前 N 天
        # 使用 UTC 时间确保全球一致性
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=self.days_back)
        
        # 格式化日期为 arXiv API 要求的格式
        start_date_str = start_date.strftime('%Y%m%d')
        end_date_str = end_date.strftime('%Y%m%d')
        date_query = f"submittedDate:[{start_date_str} TO {end_date_str}]"
        
        # 调试信息：显示实际的时间范围
        if self.days_back <= 1:
            range_desc = f"{start_date_str} (仅当天)"
        else:
            range_desc = f"{start_date_str} 至 {end_date_str} ({self.days_back}天)"
        print(f"   时间范围: {range_desc}")
        
        # 组合完整查询（括号确保逻辑优先级）
        full_query = f"({cat_query}) AND ({kw_query}) AND {date_query}"
        return full_query

    def _parse_entry(self, entry) -> Dict:
        """
        ✅ 修复版：正确解析默认命名空间下的 XML 元素
        关键：arXiv 使用 xmlns="http://www.w3.org/2005/Atom"（默认命名空间）
              必须使用 f'{{{NS}}}element' 语法，不能用 'atom:element'
        """
        try:
            NS = self.ns
            
            # ✅ 正确方式：使用 {namespace} 语法
            # ❌ 错误方式：entry.find('atom:title', {'atom': NS}) → 永远返回 None
            
            title_elem = entry.find(f'{{{NS}}}title')
            summary_elem = entry.find(f'{{{NS}}}summary')
            id_elem = entry.find(f'{{{NS}}}id')
            published_elem = entry.find(f'{{{NS}}}published')
            
            # 安全提取文本（防御性编程：处理 None 或空文本）
            title = title_elem.text.strip() if title_elem is not None and title_elem.text else "Untitled"
            summary = summary_elem.text.strip() if summary_elem is not None and summary_elem.text else "No abstract available"
            
            # 清理 LaTeX 格式标记
            title = clean_latex(title)
            summary = clean_latex(summary)
            link = id_elem.text.strip() if id_elem is not None and id_elem.text else ""
            published_str = published_elem.text.strip() if published_elem is not None and published_elem.text else "1970-01-01T00:00:00Z"
            
            # 提取分类标签（取第一个 category 的 term 属性）
            categories = entry.findall(f'{{{NS}}}category')
            cat_term = categories[0].get('term') if categories else "unknown"
            
            # 生成唯一ID（基于 arXiv ID 的 MD5 哈希）
            arxiv_id = link.split('/')[-1] if '/abs/' in link else hashlib.md5(title.encode()).hexdigest()[:10]
            item_id = hashlib.md5(arxiv_id.encode()).hexdigest()
            
            # 推断中文标签（仅用于界面展示，不影响过滤）
            # text_lower = (title + " " + summary).lower() #这里是从标题和摘要中去匹配关键词
            text_lower = (title).lower() #当前是仅从标题中匹配关键词
            if any(kw in text_lower for kw in ["chaos", "chaotic synchronization", "chaotic control"]):
                tags = "混沌控制"
            elif any(kw in text_lower for kw in ["reinforcement learning", "ppo", "sac", "ddpg", "td3", "q learning", "RL"]):
                tags = "强化学习"
            elif "robot" in text_lower or "robotic" in text_lower:
                tags = "机器人,控制"
            else:
                # 根据分类推断
                cat_map = {
                    "cs.LG": "机器学习",
                    "cs.AI": "人工智能",
                    "cs.SY": "控制系统",
                    "nlin.CD": "混沌动力学",
                    "cs.RO": "机器人",
                    "eess.SY": "电气控制"
                }
                tags = cat_map.get(cat_term, "其他")
            
            # 解析发布时间
            try:
                published_dt = datetime.strptime(published_str, '%Y-%m-%dT%H:%M:%SZ')
            except ValueError:
                published_dt = datetime.now(timezone.utc).replace(tzinfo=None)
            
            return {
                'id': item_id,
                'title': title,
                'summary': summary,
                'link': link,
                'source': f"arXiv {cat_term}",
                'published_at': published_dt,
                'tags': tags
            }
            
        except Exception as e:
            # 调试输出：显示原始 XML 片段（帮助定位问题）
            try:
                xml_snippet = ET.tostring(entry, encoding='unicode', method='xml')[:300]
                print(f"⚠️  条目解析失败 | 错误: {e}")
                print(f"   XML 片段: {xml_snippet}")
            except:
                print(f"⚠️  条目解析失败（无法显示XML）| 错误: {e}")
            raise

    def fetch_articles(self, keywords: Dict[str, List[str]], max_results: int = 1000) -> List[Dict]:
        """
        主入口：通过 arXiv API 抓取文献（支持分页抓取，突破100篇限制）
        :param keywords: {'primary': [...], 'secondary': [...]}
        :param max_results: 最大返回结果数（默认1000，可自动分页获取更多）
        :return: 文章列表（字典格式）
        """
        # 构建查询字符串
        query = self._build_query(keywords)
        print(f"\n🔍 arXiv API 搜索:")
        print(f"   镜像: {self.mirror_name}")
        print(f"   范围: 最近 {self.days_back} 天")
        print(f"   查询: {query[:70]}...")
        print(f"   目标数量: {max_results} 篇 (将自动分页获取)")
        
        # 宽松 User-Agent（避免被国内防火墙拦截）
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/atom+xml, text/xml"
        }
        
        # 分页抓取：每次最多100篇（arXiv API 限制），直到达到 max_results
        articles = []
        start = 0
        batch_size = 100  # arXiv 单次请求最大限制
        max_batches = (max_results + batch_size - 1) // batch_size  # 向上取整计算批次数
        
        for batch_num in range(max_batches):
            # 如果已经收集够了所需数量，则停止
            if len(articles) >= max_results:
                break
            
            # 遵守速率限制（除了第一批，后续批次都需要等待）
            if batch_num > 0:
                self._wait_for_rate_limit()
            
            current_batch_size = min(batch_size, max_results - len(articles))
            print(f"\n📄 第 {batch_num + 1} 批次 (起始位置: {start}, 获取数量: {current_batch_size})")
            
            try:
                # 执行 API 请求
                response = requests.get(
                    self.api_url,
                    params={
                        "search_query": query,
                        "sortBy": "submittedDate",
                        "sortOrder": "descending",
                        "start": start,
                        "max_results": current_batch_size
                    },
                    headers=headers,
                    timeout=25,  # 延长超时至25秒（国内网络波动）
                    verify=True   # 验证 SSL 证书
                )
                
                # 调试输出：状态码 + 响应长度
                print(f"   ↳ HTTP 状态: {response.status_code} | 响应大小: {len(response.content)} 字节")
                
                # 处理非200响应
                if response.status_code != 200:
                    print(f"   ↳ 错误响应: {response.text[:200]}")
                    if response.status_code == 403:
                        print("   💡 提示: 403 Forbidden - 可能 User-Agent 被拦截，已使用宽松 UA")
                    elif response.status_code == 503:
                        print("   💡 提示: 503 Service Unavailable - 镜像过载，建议切换镜像源")
                    break  # 出错则停止抓取
                
                # 检查响应是否为 XML（防御性：避免被劫持返回 HTML）
                content_type = response.headers.get('content-type', '').lower()
                if 'xml' not in content_type:
                    print(f"⚠️  响应非 XML 格式 (Content-Type: {content_type})")
                    print(f"   前100字符: {response.text[:100]}")
                    break
                
                # 解析 XML
                try:
                    root = ET.fromstring(response.content)
                except ET.ParseError as e:
                    print(f"❌ XML 解析失败: {e}")
                    print(f"   响应前200字符: {response.text[:200]}")
                    break
                
                # ✅ 正确方式：使用命名空间查找所有 <entry> 元素
                entries = root.findall(f'.//{{{self.ns}}}entry')
                print(f"   ↳ XML 解析: 成功提取 {len(entries)} 个 <entry> 元素")
                
                # 如果该批次没有返回任何条目，说明已到达末尾
                if not entries:
                    print("   ↳ 该批次无更多数据，抓取结束")
                    break
                
                # 解析该批次的文章
                batch_articles = []
                for i, entry in enumerate(entries, 1):
                    try:
                        article = self._parse_entry(entry)
                        batch_articles.append(article)
                        
                        # 调试：显示前3篇标题（确认抓取成功）
                        if i <= 3 and batch_num == 0:  # 只在第一批显示详细信息
                            title_preview = article['title'][:55] + "..." if len(article['title']) > 55 else article['title']
                            print(f"   ↳ [{i:2d}] {title_preview} ({article['source']})")
                    
                    except Exception as e:
                        print(f"   ↳ 跳过条目 {i}: {e}")
                        continue  # 跳过异常条目，继续处理其余
                
                # 将该批次结果加入总结果
                articles.extend(batch_articles)
                print(f"   ↳ 本批次新增: {len(batch_articles)} 篇 | 累计总数: {len(articles)} 篇")
                
                # 更新下一批次的起始位置
                start += len(entries)
                
            except requests.exceptions.SSLError as e:
                print(f"❌ SSL 证书错误: {e}")
                print("💡 解决方案: 运行 'pip install --upgrade certifi' 更新证书库")
                break
                
            except requests.exceptions.Timeout:
                print("❌ API 超时（25秒）- 可能网络不稳定或镜像不可用")
                print(f"💡 建议: ")
                print(f"   1. 切换镜像源: config/sources.yaml → arxiv_mirror: azure")
                print(f"   2. 测试连通性: curl -I 'https://arxiv.org/api/query?search_query=cat:cs.SY&max_results=1'")
                break
                
            except requests.exceptions.ConnectionError as e:
                print(f"❌ 连接错误: {e}")
                print("💡 可能原因: 网络断开 / 防火墙拦截 / DNS 污染")
                break
                
            except Exception as e:
                print(f"❌ 未预期错误: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                break
        
        print(f"\n✅ 抓取完成: 共 {len(articles)} 篇文献（时间范围: 最近 {self.days_back} 天）")
        if len(articles) >= max_results:
            print(f"💡 提示: 已达到最大数量限制 {max_results} 篇")
        return articles

    def _check_total_results(self, query: str) -> int:
        """
        检查符合条件的文献总数（不返回具体内容，仅获取数量）
        用于预估抓取规模
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/atom+xml"
            }
            
            response = requests.get(
                self.api_url,
                params={
                    "search_query": query,
                    "max_results": 0  # 不返回实际内容，只获取opensearch:totalResults
                },
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                # 查找 opensearch:totalResults
                total_elem = root.find('.//{http://a9.com/-/spec/opensearch/1.1/}totalResults')
                if total_elem is not None and total_elem.text:
                    return int(total_elem.text)
            
            return 0
        except:
            return 0