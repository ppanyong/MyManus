from typing import Dict, Any, Optional, List, Tuple
from app.utils.html_fetcher import HTMLFetcher
from app.tool.base import BaseTool
import logging
import re
from collections import Counter
import jieba
import jieba.analyse
import json
import asyncio
from playwright.async_api import async_playwright
import time
import random
import requests
import os
from jinja2 import Environment, FileSystemLoader
from bs4 import BeautifulSoup
from app.tool.logger_tool import LoggerTool

logger = logging.getLogger(__name__)

class HTMLParserTool(BaseTool):
    """HTML解析工具类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.fetcher = HTMLFetcher()
        # 初始化jieba分词
        jieba.initialize()
        # 加载提示词模板
        self._load_prompts()
        # 初始化日志工具
        logger_tool = LoggerTool(log_dir=os.path.join("logs", "tools"))
        self.logger = logger_tool.get_logger(self.__class__.__name__)
    
    def _load_prompts(self):
        """加载提示词模板"""
        try:
            prompt_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'prompt')
            env = Environment(loader=FileSystemLoader(prompt_dir))
            self.web_summary_template = env.get_template('web_summary_prompt.jinja')
        except Exception as e:
            logger.error(f"加载提示词模板失败: {str(e)}")
            # 如果加载失败，使用默认提示词
            self.web_summary_template = None
    
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
    
    async def parse_url(self, url: str) -> Dict[str, Any]:
        """
        解析URL内容并生成小结
        
        Args:
            url: 要解析的URL地址
            
        Returns:
            包含解析结果的字典
        """
        max_retries = 3
        retry_count = 0
        browser = None
        context = None
        page = None
        
        while retry_count < max_retries:
            try:
                async with async_playwright() as p:
                    try:
                        # 启动浏览器，使用非无头模式
                        browser = await p.chromium.launch(
                            headless=False,  # 使用可见浏览器
                            args=[
                                '--disable-blink-features=AutomationControlled',
                                '--disable-features=IsolateOrigins,site-per-process',
                                '--disable-site-isolation-trials'
                            ]
                        )
                        
                        # 创建上下文，添加更多浏览器指纹
                        context = await browser.new_context(
                            viewport={'width': 1920, 'height': 1080},
                            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                            locale='zh-CN',
                            timezone_id='Asia/Shanghai',
                            geolocation={'latitude': 39.9042, 'longitude': 116.4074},  # 北京坐标
                            permissions=['geolocation'],
                            color_scheme='light',
                            device_scale_factor=1,
                            is_mobile=False,
                            has_touch=False,
                            java_script_enabled=True,
                            accept_downloads=False
                        )
                        
                        # 创建新页面
                        page = await context.new_page()
                        
                        # 设置超时时间
                        page.set_default_timeout(30000)
                        
                        # 注入随机延迟
                        await asyncio.sleep(random.uniform(1, 3))
                        
                        try:
                            # 访问页面
                            await page.goto(url, wait_until='networkidle')
                            
                            # 模拟人类行为：随机滚动页面
                            for _ in range(random.randint(2, 5)):
                                await page.evaluate("window.scrollBy(0, window.innerHeight * 0.5)")
                                await asyncio.sleep(random.uniform(0.5, 1.5))
                            
                            # 等待页面加载完成，减少等待时间
                            await asyncio.sleep(1)
                            
                            # 获取页面内容
                            html_content = await page.content()
                            
                            # 解析HTML
                            soup = self.fetcher.parse_html(html_content)
                            if not soup:
                                logger.warning("解析HTML失败，继续尝试")
                                continue        
                            
                            # 获取标题
                            title = self.fetcher.get_title(soup) or ""
                            
                            # 获取主要内容
                            main_content = self._extract_main_content(soup)
                            
                            # 使用大模型生成摘要
                            if self.web_summary_template:
                                prompt = self.web_summary_template.render(content=main_content)
                            else:
                                prompt = f"""请对以下网页内容生成一个简洁的摘要，要求：
1. 摘要长度在200字以内
2. 突出主要内容
3. 保持客观性
4. 使用中文输出

网页内容：
{main_content}"""
                            
                            logger.info(f"生成摘要提示: {prompt}")
                            response = self.execute(prompt)
                            logger.info(f"生成摘要结果: {response}")
                            if response.get("status") == "error":
                                logger.error(f"生成摘要失败: {response.get('error')}")
                                summary = "生成摘要失败"
                            else:
                                # 从大模型返回中提取实际内容
                                content = response.get("result", {}).get("choices", [{}])[0].get("message", {}).get("content", "")
                                if not content:
                                    logger.error("无法从大模型返回中提取内容")
                                    summary = "生成摘要失败"
                                else:
                                    summary = content
                            
                            # 提取关键词
                            keywords = self._extract_keywords(main_content)
                            
                            return {
                                "title": title,
                                "summary": summary,
                                "keywords": keywords
                            }
                        except Exception as e:
                            logger.warning(f"页面处理失败: {str(e)}")
                            return {"error": f"页面处理失败: {str(e)}"}
                    finally:
                        # 确保资源被正确关闭
                        try:
                            if page:
                                await page.close()
                            if context:
                                await context.close()
                            if browser:
                                await browser.close()
                        except Exception as e:
                            logger.error(f"关闭浏览器资源时发生错误: {str(e)}")
                            
            except Exception as e:
                logger.warning(f"第{retry_count + 1}次尝试解析失败: {str(e)}")
                retry_count += 1
                if retry_count >= max_retries:
                    return {"error": f"解析失败: {str(e)}"}
                await asyncio.sleep(random.uniform(2, 4))  # 随机等待重试
        
        return {"error": "解析失败: 达到最大重试次数"}
    
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
        self.logger.info(f"提取的主要内容: {main_content}")
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
    
    def execute(self, prompt: str) -> Dict[str, Any]:
        """
        执行大模型请求
        
        Args:
            prompt: 提示词
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
            # 从配置中获取 API 设置
            api_config = self.config.get('api', {})
            
            if not api_config:
                return {
                    "status": "error",
                    "error": "API配置未找到"
                }
            
            api_url = api_config.get('url')
            api_key = api_config.get('api_key')
            model = api_config.get('model')
            
            if not all([api_url, api_key, model]):
                return {
                    "status": "error",
                    "error": "API配置不完整，需要url、api_key和model"
                }
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # 构建请求体
            request_body = {
                "model": model,
                "prompt": prompt,
                "stream": api_config.get('stream', False),
                "options": {
                    "temperature": api_config.get('temperature', 0.7),
                    "max_tokens": api_config.get('max_tokens', 4096)
                },
                "messages": [
                    {
                        "content": prompt,
                        "role": "user"
                    }
                ]
            }
            
            # 发送请求
            response = requests.post(
                api_url,
                headers=headers,
                json=request_body,
                timeout=30  # 添加超时设置
            )
            
            if response.status_code == 200:
                return {
                    "status": "success",
                    "result": response.json()
                }
            else:
                return {
                    "status": "error",
                    "error": f"API请求失败: HTTP {response.status_code} - {response.text}"
                }
                
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "error": "API请求超时"
            }
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "error": f"API请求异常: {str(e)}"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"执行异常: {str(e)}"
            } 

    def parse(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            self.logger.info(f"成功解析URL: {url}")
            return soup
        except Exception as e:
            self.logger.error(f"解析URL失败: {url}, 错误: {str(e)}")
            return None
            
    def extract_text(self, soup, selector):
        try:
            elements = soup.select(selector)
            text = [elem.get_text(strip=True) for elem in elements]
            self.logger.info(f"成功提取文本，选择器: {selector}")
            return text
        except Exception as e:
            self.logger.error(f"提取文本失败，选择器: {selector}, 错误: {str(e)}")
            return []
            
    def extract_links(self, soup, base_url=None):
        try:
            links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                if base_url and not href.startswith(('http://', 'https://')):
                    href = base_url.rstrip('/') + '/' + href.lstrip('/')
                links.append(href)
            self.logger.info(f"成功提取链接，数量: {len(links)}")
            return links
        except Exception as e:
            self.logger.error(f"提取链接失败，错误: {str(e)}")
            return []
            
    def extract_images(self, soup, base_url=None):
        try:
            images = []
            for img in soup.find_all('img'):
                src = img.get('src')
                if src:
                    if base_url and not src.startswith(('http://', 'https://')):
                        src = base_url.rstrip('/') + '/' + src.lstrip('/')
                    images.append(src)
            self.logger.info(f"成功提取图片，数量: {len(images)}")
            return images
        except Exception as e:
            self.logger.error(f"提取图片失败，错误: {str(e)}")
            return []
            
    def extract_metadata(self, soup):
        try:
            metadata = {}
            # 提取标题
            title = soup.title.string if soup.title else None
            if title:
                metadata['title'] = title.strip()
                
            # 提取meta标签
            for meta in soup.find_all('meta'):
                name = meta.get('name') or meta.get('property')
                content = meta.get('content')
                if name and content:
                    metadata[name] = content
                    
            self.logger.info(f"成功提取元数据: {metadata}")
            return metadata
        except Exception as e:
            self.logger.error(f"提取元数据失败，错误: {str(e)}")
            return {} 