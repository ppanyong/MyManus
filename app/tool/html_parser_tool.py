from typing import Dict, Any, Optional, List, Tuple
from app.utils.html_fetcher import HTMLFetcher
from app.tool.base import BaseTool
import logging
import re
from collections import Counter
import jieba
import jieba.analyse
import json
import requests

logger = logging.getLogger(__name__)

class HTMLParserTool(BaseTool):
    """HTML解析工具类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.fetcher = HTMLFetcher()
        # 初始化jieba分词
        jieba.initialize()
    
    def get_tool_description(self) -> Dict[str, Any]:
        """返回工具描述，符合MCP协议"""
        return {
            "name": "html_parser",
            "description": "HTML解析工具，可以读取URL内容并生成小结",
            "functions": [
                {
                    "name": "parse_url",
                    "description": "解析URL内容并生成小结",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "要解析的URL地址"
                            }
                        },
                        "required": ["url"]
                    },
                    "returns": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "页面标题"
                            },
                            "summary": {
                                "type": "string",
                                "description": "内容小结"
                            },
                            "keywords": {
                                "type": "array",
                                "description": "关键词列表"
                            }
                        }
                    }
                }
            ]
        }
    
    def parse_url(self, url: str) -> Dict[str, Any]:
        """
        解析URL内容并生成小结
        
        Args:
            url: 要解析的URL地址
            
        Returns:
            包含解析结果的字典
        """
        try:
            # 获取URL内容
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            html_content = response.text
            
            # 解析HTML
            soup = self.fetcher.parse_html(html_content)
            if not soup:
                return {"error": "无法解析HTML内容"}
            
            # 获取标题
            title = self.fetcher.get_title(soup) or ""
            
            # 获取主要内容
            main_content = self._extract_main_content(soup)
            
            # 生成摘要
            summary = self._generate_summary(main_content)
            
            # 提取关键词
            keywords = self._extract_keywords(main_content)
            
            return {
                "title": title,
                "summary": summary,
                "keywords": keywords
            }
            
        except requests.RequestException as e:
            logger.error(f"获取URL内容失败: {str(e)}")
            return {"error": f"获取URL内容失败: {str(e)}"}
        except Exception as e:
            logger.error(f"解析失败: {str(e)}")
            return {"error": f"解析失败: {str(e)}"}
    
    def _extract_main_content(self, soup) -> str:
        """
        提取页面的主要内容
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            主要内容文本
        """
        # 尝试找到主要内容区域
        main_content = ""
        
        # 1. 尝试找到article标签
        article = soup.find('article')
        if article:
            main_content = article.get_text(strip=True)
        
        # 2. 如果没有article标签，尝试找到main标签
        if not main_content:
            main = soup.find('main')
            if main:
                main_content = main.get_text(strip=True)
        
        # 3. 如果还是没有，尝试找到body标签
        if not main_content:
            body = soup.find('body')
            if body:
                main_content = body.get_text(strip=True)
        
        # 4. 如果还是没有，尝试找到包含最多文本的div
        if not main_content:
            divs = soup.find_all('div')
            max_text_length = 0
            for div in divs:
                text = div.get_text(strip=True)
                if len(text) > max_text_length:
                    max_text_length = len(text)
                    main_content = text
        
        # 5. 如果还是没有内容，返回所有文本
        if not main_content:
            main_content = soup.get_text(strip=True)
        
        return main_content
    
    def _generate_summary(self, content: str, max_length: int = 200) -> str:
        """
        生成内容摘要
        
        Args:
            content: 原始内容
            max_length: 摘要最大长度
            
        Returns:
            生成的摘要
        """
        if not content:
            return ""
        
        # 简单的摘要生成：取前max_length个字符
        if len(content) <= max_length:
            return content
        
        # 找到最近的句子结束位置
        end_index = content.rfind('。', 0, max_length)
        if end_index == -1:
            end_index = content.rfind('.', 0, max_length)
        if end_index == -1:
            end_index = max_length
        
        return content[:end_index + 1] + "..."
    
    def _extract_keywords(self, content: str, top_k: int = 10) -> List[str]:
        """
        提取关键词
        
        Args:
            content: 文本内容
            top_k: 返回关键词数量
            
        Returns:
            关键词列表
        """
        if not content:
            return []
        
        # 使用jieba提取关键词
        keywords = jieba.analyse.extract_tags(content, topK=top_k)
        return keywords
    
    def _classify_content(self, content: str) -> str:
        """
        内容分类
        
        Args:
            content: 文本内容
            
        Returns:
            内容类别
        """
        if not content:
            return "未知"
        
        # 简单的基于关键词的分类
        categories = {
            "新闻": ["新闻", "报道", "记者", "消息"],
            "科技": ["科技", "技术", "创新", "研发"],
            "教育": ["教育", "学习", "学校", "课程"],
            "娱乐": ["娱乐", "明星", "电影", "音乐"],
            "体育": ["体育", "比赛", "运动员", "赛事"]
        }
        
        # 统计关键词出现次数
        word_counts = Counter(jieba.lcut(content))
        category_scores = {}
        
        for category, keywords in categories.items():
            score = sum(word_counts.get(word, 0) for word in keywords)
            category_scores[category] = score
        
        # 返回得分最高的类别
        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]
        return "其他"
    
    def _analyze_sentiment(self, content: str) -> Dict[str, float]:
        """
        情感分析
        
        Args:
            content: 文本内容
            
        Returns:
            情感分析结果
        """
        if not content:
            return {"positive": 0.0, "negative": 0.0, "neutral": 1.0}
        
        # 简单的情感词统计
        positive_words = ["好", "优秀", "喜欢", "高兴", "满意"]
        negative_words = ["差", "糟糕", "讨厌", "生气", "失望"]
        
        words = jieba.lcut(content)
        total_words = len(words)
        
        if total_words == 0:
            return {"positive": 0.0, "negative": 0.0, "neutral": 1.0}
        
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        return {
            "positive": positive_count / total_words,
            "negative": negative_count / total_words,
            "neutral": 1 - (positive_count + negative_count) / total_words
        }
    
    def _extract_paragraphs(self, content: str) -> List[Dict[str, Any]]:
        """
        提取段落
        
        Args:
            content: 文本内容
            
        Returns:
            段落列表，每个段落包含内容和情感分析
        """
        if not content:
            return []
        
        # 按句号、感叹号、问号分割段落
        paragraphs = re.split(r'[。！？\n]', content)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        result = []
        for p in paragraphs:
            if len(p) > 0:  # 只添加非空段落
                result.append({
                    "content": p,
                    "sentiment": self._analyze_sentiment(p)
                })
        
        return result
    
    def _convert_search_results_to_html(self, results: List[Dict[str, Any]]) -> str:
        """
        将搜索结果列表转换为HTML格式
        
        Args:
            results: 搜索结果列表
            
        Returns:
            HTML格式的字符串
        """
        html = """
        <html>
            <head>
                <title>搜索结果</title>
                <meta name="description" content="搜索结果摘要">
            </head>
            <body>
                <div class="search-results">
        """
        
        for result in results:
            html += f"""
                    <div class="result-item">
                        <h2>{result.get('title', '')}</h2>
                        <p class="snippet">{result.get('snippet', '')}</p>
                        <a href="{result.get('link', '')}">查看详情</a>
                    </div>
            """
        
        html += """
                </div>
            </body>
        </html>
        """
        
        return html 