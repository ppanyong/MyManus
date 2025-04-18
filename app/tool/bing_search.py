from typing import Dict, Any, List
import requests
from bs4 import BeautifulSoup
import time
import random
import urllib.parse
import os
from datetime import datetime
import json
import asyncio
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from PIL import Image
from app.tool.logger_tool import LoggerTool

# 初始化日志工具
logger_tool = LoggerTool()
logger = logger_tool.get_logger("BingSearchTool")

class BingSearchTool:
    """Bing搜索工具"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get("bing_api_key")
        
        
        # 设置基础请求头
        self.base_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }
        
        # 常用User-Agent列表
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        # 创建截图目录
        self.screenshot_dir = os.path.join(os.getcwd(), "screenshots", "search")
        logger.info(f"创建截图目录: {self.screenshot_dir}")
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
        # 浏览器指纹配置
        self.browser_fingerprints = {
            "webgl_vendor": ["Google Inc.", "Intel Inc.", "NVIDIA Corporation"],
            "webgl_renderer": ["ANGLE (Intel, Intel(R) UHD Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)", 
                             "ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 Direct3D11 vs_5_0 ps_5_0, D3D11)"],
            "platform": ["Win32", "MacIntel", "Linux x86_64"],
            "hardware_concurrency": [4, 8, 12, 16],
            "device_memory": [4, 8, 16],
            "touch_points": [0, 5, 10]
        }
        
        # 浏览器实例
        self.browser = None
        self.context = None
        self.page = None
        
        # 浏览器配置
        self.headless = config.get("headless", False)  # 默认显示浏览器窗口
        self.debug = config.get("debug", False)  # 调试模式
        
    async def _ensure_browser_initialized(self):
        """确保浏览器已初始化"""
        try:
            # 如果已经有浏览器实例，先尝试清理
            if self.browser or self.context or self.page:
                logger.info("检测到现有浏览器实例，进行清理...")
                try:
                    if self.page:
                        await self.page.close()
                    if self.context:
                        await self.context.close()
                    if self.browser:
                        await self.browser.close()
                except Exception as e:
                    logger.error(f"清理现有浏览器实例时出错: {str(e)}")
                finally:
                    self.browser = None
                    self.context = None
                    self.page = None
            
            # 初始化浏览器
            logger.info("正在初始化 playwright...")
            playwright = await async_playwright().start()
            logger.info("正在启动浏览器...")
            
            # 生成浏览器指纹
            fingerprint = self._get_random_fingerprint()
            logger.info("生成浏览器指纹...")
            
            # 启动浏览器
            browser_args = ['--no-sandbox']
            if self.debug:
                browser_args.append('--remote-debugging-port=9222')
                logger.info("启用远程调试端口: 9222")
            
            logger.info(f"浏览器启动模式: {'无头模式' if self.headless else '有界面模式'}")
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=browser_args
            )
            
            # 创建上下文
            logger.info("创建浏览器上下文...")
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=random.choice(self.user_agents)
            )
            
            # 创建新页面
            logger.info("创建新页面...")
            self.page = await self.context.new_page()
            logger.info("浏览器初始化完成")
            
        except Exception as e:
            logger.error(f"浏览器初始化失败: {str(e)}")
            # 清理资源
            try:
                if self.page:
                    await self.page.close()
                if self.context:
                    await self.context.close()
                if self.browser:
                    await self.browser.close()
            except Exception as cleanup_error:
                logger.error(f"清理资源时出错: {str(cleanup_error)}")
            finally:
                self.browser = None
                self.context = None
                self.page = None
            raise
        
    async def _simulate_human_behavior(self):
        """模拟人类行为"""
        try:
            # 随机滚动
            for _ in range(random.randint(2, 4)):
                await self.page.mouse.wheel(0, random.randint(100, 300))
                await asyncio.sleep(random.uniform(0.1, 0.3))
                
            # 随机移动鼠标
            for _ in range(random.randint(3, 6)):
                await self.page.mouse.move(
                    random.randint(100, 700),
                    random.randint(100, 600)
                )
                await asyncio.sleep(random.uniform(0.1, 0.2))
        except Exception as e:
            logger.error(f"模拟人类行为时出错: {str(e)}")
            raise
        
    async def _perform_search(self, query: str, max_results: int = 5, category: str = None) -> List[Dict[str, str]]:
        """执行搜索并返回结果
        
        Args:
            query (str): 搜索关键词
            max_results (int, optional): 最大结果数量. 默认为 5.
            category (str, optional): 搜索类别. 默认为 None.
        """
        results = []
        try:
            # 确保浏览器已初始化
            await self._ensure_browser_initialized()
            
            # 构建搜索URL
            search_params = {
                'q': query,
                'count': max_results
            }
            
            # 如果指定了类别，添加到搜索参数中
            if category:
                search_params['category'] = category
                
            search_url = f"https://www.bing.com/search?{urllib.parse.urlencode(search_params)}"
            logger.info(f"正在打开浏览器访问: {search_url}")
            try:
                await self.page.goto(search_url)
            except Exception as e:
                error_msg = str(e)
                if "net::" in error_msg:
                    raise Exception("网络连接失败")
                else:
                    raise
            
            # 等待页面加载
            logger.info("等待页面加载...")
            await self.page.wait_for_load_state("networkidle")
            
            # 等待搜索结果加载
            logger.info("等待搜索结果加载...")
            try:
                await self.page.wait_for_selector('.b_algo', timeout=10000)  # Bing搜索结果选择器
            except Exception as e:
                error_msg = str(e)
                if "timeout" in error_msg.lower():
                    raise Exception("页面加载超时")
                else:
                    raise
            
            # 获取搜索结果
            search_results = await self.page.query_selector_all('.b_algo')
            logger.info(f"找到 {len(search_results)} 个搜索结果")
            
            # 处理搜索结果
            for result in search_results:
                try:
                    # 提取标题和链接
                    title_elem = await result.query_selector('h2 a')
                    if not title_elem:
                        continue
                        
                    title = await title_elem.text_content()
                    title = title.strip() if title else ""
                    link = await title_elem.get_attribute('href')
                    link = link or ""
                    
                    # 提取摘要
                    snippet = ""
                    snippet_elem = await result.query_selector('.b_caption p')
                    if snippet_elem:
                        snippet = await snippet_elem.text_content()
                        snippet = snippet.strip() if snippet else ""
                    
                    # 添加结果
                    if title and link:
                        result_item = {
                            "title": title,
                            "link": link
                            # "snippet": snippet or "无摘要" 暂时移除摘要
                        }
                        
                        # 检查是否重复
                        is_duplicate = any(
                            r["title"] == result_item["title"] or 
                            r["link"] == result_item["link"]
                            for r in results
                        )
                        
                        if not is_duplicate:
                            results.append(result_item)
                            if len(results) >= max_results:
                                break
                                
                except Exception as e:
                    logger.error(f"处理搜索结果时出错: {str(e)}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"执行搜索时出错: {str(e)}")
            raise
            
    async def _save_screenshot_from_page(self, query: str, max_retries: int = 3) -> None:
        """保存搜索结果页面截图"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bing_search_{query}_{timestamp}.png"
            filepath = os.path.join(self.screenshot_dir, filename)
            
            for attempt in range(max_retries):
                try:
                    await self.page.screenshot(path=filepath, full_page=True)
                    logger.info(f"截图已保存: {filepath}")
                    return
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"截图失败，重试中... ({attempt + 1}/{max_retries})")
                        await asyncio.sleep(1)
                    else:
                        raise
        except Exception as e:
            logger.error(f"保存截图时出错: {str(e)}")
            raise
            
    async def search(self, query: str, max_results: int = 5, category: str = None) -> Dict[str, Any]:
        """执行搜索并返回结果
        
        Args:
            query (str): 搜索关键词
            max_results (int, optional): 最大结果数量. 默认为 5.
            category (str, optional): 搜索类别. 默认为 None.
            
        Returns:
            Dict[str, Any]: 包含搜索结果的字典，格式为:
                {
                    "status": "success" | "error",
                    "results": List[Dict[str, str]],  # 搜索结果列表
                    "error": str | None  # 错误信息
                }
        """
        try:
            if not query:
                raise ValueError("必须提供query参数")
            
            # 执行搜索
            results = await self._perform_search(query, max_results, category)
            if not results:
                logger.info("未找到搜索结果")
                return {
                    "status": "error",
                    "results": [],
                    "error": "未找到有效的搜索结果"
                }
            
            logger.info(f"搜索成功，找到 {len(results)} 个结果")
            
            # 保存截图
            # await self._save_screenshot_from_page(search_query)
            
            # 返回结果
            return {
                "status": "success",
                "results": results,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"搜索出错: {str(e)}")
            return {
                "status": "error",
                "results": [],
                "error": str(e)
            }
        finally:
            # 清理资源
            logger.info("清理浏览器资源...")
            try:
                # 先关闭页面
                if hasattr(self, 'page') and self.page:
                    try:
                        await self.page.close()
                    except Exception as e:
                        logger.error(f"关闭页面时出错: {str(e)}")
                
                # 再关闭上下文
                if hasattr(self, 'context') and self.context:
                    try:
                        await self.context.close()
                    except Exception as e:
                        logger.error(f"关闭上下文时出错: {str(e)}")
                
                # 最后关闭浏览器
                if hasattr(self, 'browser') and self.browser:
                    try:
                        await self.browser.close()
                    except Exception as e:
                        logger.error(f"关闭浏览器时出错: {str(e)}")
                
                # 重置实例变量
                self.browser = None
                self.context = None
                self.page = None
                logger.info("浏览器资源清理完成")
            except Exception as e:
                logger.error(f"资源清理过程中出错: {str(e)}")
                # 确保实例变量被重置
                self.browser = None
                self.context = None
                self.page = None
            
    def _get_random_fingerprint(self) -> Dict[str, Any]:
        """生成随机浏览器指纹"""
        return {
            "webgl_vendor": random.choice(self.browser_fingerprints["webgl_vendor"]),
            "webgl_renderer": random.choice(self.browser_fingerprints["webgl_renderer"]),
            "platform": random.choice(self.browser_fingerprints["platform"]),
            "hardware_concurrency": random.choice(self.browser_fingerprints["hardware_concurrency"]),
            "device_memory": random.choice(self.browser_fingerprints["device_memory"]),
            "touch_points": random.choice(self.browser_fingerprints["touch_points"])
        }
        
    def get_tool_description(self) -> Dict[str, Any]:
        """获取工具描述"""
        return {
            "name": "BingSearchTool",
            "description": "使用Bing搜索引擎进行网页搜索的工具",
            "functions": [
                {
                    "name": "search",
                    "description": "执行Bing搜索并返回结果",
                    "parameters": {
                        "query": {
                            "type": "string",
                            "description": "搜索关键词"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "最大结果数量",
                            "default": 5
                        },
                        "category": {
                            "type": "string",
                            "description": "搜索类别",
                            "default": None
                        }
                    },
                    "returns": {
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "enum": ["success", "error"]
                            },
                            "results": {
                                "type": "array",
                                "description": "搜索结果列表"
                            },
                            "error": {
                                "type": "string",
                                "description": "错误信息"
                            }
                        }
                    }
                }
            ]
        } 