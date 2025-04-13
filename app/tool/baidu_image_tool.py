from typing import Dict, Any, List
from app.tool.base import BaseTool
import logging
import requests
from bs4 import BeautifulSoup
import re
import random
import time
import asyncio
import os
from urllib.parse import quote
from playwright.async_api import async_playwright
from app.tool.logger_tool import LoggerTool

# 初始化日志工具
logger_tool = LoggerTool()
logger = logger_tool.get_logger("BaiduImageTool")

class BaiduImageTool(BaseTool):
    """百度图片搜索工具类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
        }
        self.browser = None
        self.context = None
        self.page = None
        logger.info(f"初始化BaiduImageTool，配置: {config}")
    
    async def _ensure_browser_initialized(self):
        """确保浏览器已初始化"""
        try:
            if not self.browser:
                logger.info("正在初始化playwright...")
                playwright = await async_playwright().start()
                self.browser = await playwright.chromium.launch(
                    headless=False,  # 使用可见浏览器
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-features=IsolateOrigins,site-per-process',
                        '--disable-site-isolation-trials'
                    ]
                )
                
                # 创建上下文
                self.context = await self.browser.new_context(
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
                    accept_downloads=True  # 允许下载
                )
                
                # 创建新页面
                self.page = await self.context.new_page()
                self.page.set_default_timeout(30000)  # 设置30秒超时
                
                logger.info("浏览器初始化完成")
        except Exception as e:
            logger.error(f"浏览器初始化失败: {str(e)}")
            raise
    
    async def _close_browser(self):
        """关闭浏览器资源"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            self.page = None
            self.context = None
            self.browser = None
            logger.info("浏览器资源已关闭")
        except Exception as e:
            logger.error(f"关闭浏览器资源时发生错误: {str(e)}")
    
    def get_tool_description(self) -> Dict[str, Any]:
        """返回工具描述"""
        logger.info("获取工具描述")
        return {
            "name": "baidu_image_search",
            "description": "百度图片搜索工具，可以搜索并获取图片下载链接",
            "functions": [
                {
                    "name": "search_images",
                    "description": "搜索图片并返回下载链接",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keyword": {
                                "type": "string",
                                "description": "搜索关键词"
                            },
                            "count": {
                                "type": "integer",
                                "description": "需要获取的图片数量",
                                "default": 10
                            }
                        },
                        "required": ["keyword"]
                    },
                    "returns": {
                        "type": "object",
                        "properties": {
                            "image_urls": {
                                "type": "array",
                                "description": "图片下载链接列表"
                            }
                        }
                    }
                }
            ]
        }
    
    async def search_images(self, keyword: str, count: int = 10) -> Dict[str, Any]:
        """
        搜索图片并返回下载链接
        
        Args:
            keyword: 搜索关键词
            count: 需要获取的图片数量
            
        Returns:
            包含图片下载链接的字典
        """
        try:
            logger.info(f"开始搜索图片，关键词: {keyword}，数量: {count}")
            
            # 确保浏览器已初始化
            await self._ensure_browser_initialized()
            
            # 构建搜索URL
            encoded_keyword = quote(keyword)
            search_url = f"https://image.baidu.com/search/index?tn=baiduimage&word={encoded_keyword}"
            logger.debug(f"构建的搜索URL: {search_url}")
            
            # 访问搜索页面
            logger.info("正在访问搜索页面...")
            await self.page.goto(search_url, wait_until='networkidle')
            
            # 模拟人类行为：随机滚动页面
            for _ in range(random.randint(2, 5)):
                await self.page.evaluate("window.scrollBy(0, window.innerHeight * 0.5)")
                await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # 等待页面加载完成
            await asyncio.sleep(1)
            
            # 获取页面内容
            html_content = await self.page.content()
            
            # 解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取图片URL
            image_urls = []
            logger.info("开始提取图片URL...")
            
            # 从页面中提取图片数据
            pattern = re.compile(r'"objURL":"(.*?)"')
            matches = pattern.findall(html_content)
            logger.info(f"从JavaScript数据中找到{len(matches)}个可能的图片URL")
            
            for url in matches:
                if len(image_urls) >= count:
                    break
                if url.startswith('http'):
                    image_urls.append(url)
                    logger.info(f"找到图片URL: {url}")
            
            logger.info(f"搜索完成，共找到{len(image_urls)}个图片URL")
            return {
                "image_urls": image_urls[:count]
            }
            
        except Exception as e:
            error_msg = f"搜索图片失败: {str(e)}"
            logger.error(error_msg)
            return {
                "error": error_msg
            }
        finally:
            # 关闭浏览器资源
            await self._close_browser()
    
    async def execute(self, prompt: str) -> Dict[str, Any]:
        """执行工具"""
        # 解析提示词
        try:
            logger.info(f"开始执行工具，提示词: {prompt}")
            
            # 从提示词中提取关键词和数量
            keyword_match = re.search(r'搜索关键词[:：]\s*([^\n]+)', prompt)
            count_match = re.search(r'数量[:：]\s*(\d+)', prompt)
            
            keyword = keyword_match.group(1).strip() if keyword_match else ""
            count = int(count_match.group(1)) if count_match else 10
            
            logger.info(f"解析结果 - 关键词: {keyword}, 数量: {count}")
            
            if not keyword:
                error_msg = "未找到搜索关键词"
                logger.error(error_msg)
                return {
                    "error": error_msg
                }
            
            return await self.search_images(keyword, count)
            
        except Exception as e:
            error_msg = f"执行失败: {str(e)}"
            logger.error(error_msg)
            return {
                "error": error_msg
            } 