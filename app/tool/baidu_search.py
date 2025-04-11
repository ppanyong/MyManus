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

class BaiduSearchTool:
    """百度搜索工具"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get("google_api_key")
        self.search_engine_id = config.get("search_engine_id")
        
        # 设置基础请求头
        self.base_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
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
        print(f"创建截图目录: {self.screenshot_dir}")
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
                print("检测到现有浏览器实例，进行清理...")
                try:
                    if self.page:
                        await self.page.close()
                    if self.context:
                        await self.context.close()
                    if self.browser:
                        await self.browser.close()
                except Exception as e:
                    print(f"清理现有浏览器实例时出错: {str(e)}")
                finally:
                    self.browser = None
                    self.context = None
                    self.page = None
            
            # 初始化浏览器
            print("正在初始化 playwright...")
            playwright = await async_playwright().start()
            print("正在启动浏览器...")
            
            # 生成浏览器指纹
            fingerprint = self._get_random_fingerprint()
            print("生成浏览器指纹...")
            
            # 启动浏览器
            browser_args = ['--no-sandbox']
            if self.debug:
                browser_args.append('--remote-debugging-port=9222')
                print("启用远程调试端口: 9222")
            
            print(f"浏览器启动模式: {'无头模式' if self.headless else '有界面模式'}")
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=browser_args
            )
            
            # 创建上下文
            print("创建浏览器上下文...")
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=random.choice(self.user_agents)
            )
            
            # 创建新页面
            print("创建新页面...")
            self.page = await self.context.new_page()
            print("浏览器初始化完成")
            
        except Exception as e:
            print(f"浏览器初始化失败: {str(e)}")
            # 清理资源
            try:
                if self.page:
                    await self.page.close()
                if self.context:
                    await self.context.close()
                if self.browser:
                    await self.browser.close()
            except Exception as cleanup_error:
                print(f"清理资源时出错: {str(cleanup_error)}")
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
                await asyncio.sleep(random.uniform(0.1, 0.3))  # 减少等待时间
                
            # 随机移动鼠标
            for _ in range(random.randint(3, 6)):
                await self.page.mouse.move(
                    random.randint(100, 700),
                    random.randint(100, 600)
                )
                await asyncio.sleep(random.uniform(0.1, 0.2))  # 减少等待时间
        except Exception as e:
            print(f"模拟人类行为时出错: {str(e)}")
            raise
        
    async def _perform_search(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """执行搜索并返回结果"""
        results = []
        try:
            # 确保浏览器已初始化
            await self._ensure_browser_initialized()
            
            # 访问搜索页面
            search_url = f"https://www.baidu.com/s?wd={urllib.parse.quote(query)}&rn={max_results}"
            print(f"正在打开浏览器访问: {search_url}")
            try:
                await self.page.goto(search_url)
            except Exception as e:
                error_msg = str(e)
                if "net::" in error_msg:
                    raise Exception("网络连接失败")
                else:
                    raise
            
            # 等待页面加载
            print("等待页面加载...")
            await self.page.wait_for_load_state("networkidle")
            
            # 等待搜索结果加载
            print("等待搜索结果加载...")
            try:
                await self.page.wait_for_selector('.c-container', timeout=10000)  # 百度搜索结果选择器
            except Exception as e:
                error_msg = str(e)
                if "timeout" in error_msg.lower():
                    raise Exception("页面加载超时")
                else:
                    raise
            
            # 获取搜索结果
            search_results = await self.page.query_selector_all('.c-container')
            print(f"找到 {len(search_results)} 个搜索结果")
            
            # 处理搜索结果
            for result in search_results:
                try:
                    # 提取标题和链接
                    title_elem = await result.query_selector('h3.c-title a')
                    print(f"提取标题和链接: {title_elem}")
                    if not title_elem:
                        continue
                        
                    title = await title_elem.text_content()
                    title = title.strip() if title else ""
                    print(f"提取标题: {title}")
                    link = await title_elem.get_attribute('href')
                    link = link or ""
                    print(f"提取链接: {link}")
                    
                    
                    # 提取摘要
                    snippet = ""
                    # 尝试多种可能的摘要选择器
                    for selector in ['.content-right_1THTn', '.c-abstract', '.c-row', '.c-span-last']:
                        snippet_elem = await result.query_selector(selector)
                        if snippet_elem:
                            snippet = await snippet_elem.text_content()
                            snippet = snippet.strip() if snippet else ""
                            if snippet:
                                break
                    print(f"提取摘要: {snippet}")
                    # 添加结果
                    if title and link:
                        result_item = {
                            "title": title,
                            "link": link,
                            "snippet": snippet or "无摘要"
                        }
                        
                        # 检查是否重复
                        is_duplicate = any(
                            r["title"] == result_item["title"] or 
                            r["link"] == result_item["link"]
                            for r in results
                        )
                        
                        if not is_duplicate:
                            results.append(result_item)
                            print(f"添加搜索结果: {title}")
                            
                except Exception as e:
                    print(f"处理搜索结果时出错: {str(e)}")
                    continue
                    
            if not results:
                raise Exception("未找到有效的搜索结果")
                
            # 保存截图
            await self._save_screenshot_from_page(query)
            
            return results
            
        except Exception as e:
            error_msg = str(e)
            if "timeout" in error_msg.lower():
                raise Exception("页面加载超时")
            elif "net::" in error_msg:
                raise Exception("网络连接失败")
            elif "browser" in error_msg.lower():
                raise Exception("浏览器启动失败")
            else:
                raise
        
    async def _save_screenshot_from_page(self, query: str, max_retries: int = 3) -> None:
        """保存页面截图"""
        retry_count = 0
        while retry_count < max_retries:
            try:
                # 生成文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{query}_{timestamp}.jpg"
                
                # 确保screenshots目录存在
                screenshots_dir = os.path.join(os.getcwd(), "screenshots", "search")
                os.makedirs(screenshots_dir, exist_ok=True)
                
                # 构建完整的文件路径
                filepath = os.path.join(screenshots_dir, filename)
                print(f"准备保存截图 (尝试 {retry_count + 1}/{max_retries})...")
                print(f"当前工作目录: {os.getcwd()}")
                print(f"截图目录: {screenshots_dir}")
                print(f"完整文件路径: {filepath}")
                
                # 等待页面完全加载
                await self.page.wait_for_load_state("networkidle")
                await asyncio.sleep(1)  # 额外等待1秒确保页面渲染完成
                
                # 保存截图
                await self.page.screenshot(path=filepath, full_page=True)
                
                # 验证文件是否创建成功
                if os.path.exists(filepath):
                    file_size = os.path.getsize(filepath)
                    print(f"截图保存成功: {filepath}")
                    print(f"文件大小: {file_size} 字节")
                    
                    if file_size < 1000:  # 如果文件太小，可能是截图失败
                        print(f"警告：截图文件大小异常: {file_size} 字节")
                        # 尝试使用PIL重新保存
                        try:
                            img = Image.open(filepath)
                            img.save(filepath, 'JPEG', quality=90)
                            print(f"使用PIL重新保存截图")
                            
                            # 再次检查文件大小
                            new_size = os.path.getsize(filepath)
                            if new_size < 1000:
                                raise Exception(f"重新保存后文件仍然太小: {new_size} 字节")
                                
                        except ImportError:
                            print("PIL不可用，无法重新保存截图")
                            raise
                        except Exception as e:
                            print(f"使用PIL重新保存截图失败: {str(e)}")
                            raise
                    else:
                        return  # 成功保存，退出函数
                else:
                    print(f"警告：截图文件未创建，文件路径不存在: {filepath}")
                    raise Exception("截图文件未创建")
                    
            except Exception as e:
                print(f"保存截图失败 (尝试 {retry_count + 1}/{max_retries}): {str(e)}")
                print(f"异常类型: {type(e)}")
                import traceback
                print(f"异常堆栈: {traceback.format_exc()}")
                
                retry_count += 1
                if retry_count < max_retries:
                    print("等待后重试...")
                    await asyncio.sleep(2)  # 等待2秒后重试
                else:
                    print("已达到最大重试次数，放弃保存截图")
                    raise Exception(f"保存截图失败，已重试{max_retries}次: {str(e)}")
        
    async def search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """执行百度搜索"""
        try:
            print(f"开始执行搜索: {query}, 最大结果数: {max_results}")
            results = await self._perform_search(query, max_results)
            
            if not results:
                print("未找到搜索结果")
                return {
                    "status": "error",
                    "results": [],
                    "error": "未找到有效的搜索结果"
                }
            
            print(f"搜索成功，找到 {len(results)} 个结果")
            return {
                "status": "success",
                "results": results,
                "error": None
            }
            
        except Exception as e:
            print(f"搜索出错: {str(e)}")
            return {
                "status": "error",
                "results": [],
                "error": str(e)
            }
            
        finally:
            # 清理资源
            print("清理浏览器资源...")
            try:
                # 先关闭页面
                if hasattr(self, 'page') and self.page:
                    try:
                        await self.page.close()
                    except Exception as e:
                        print(f"关闭页面时出错: {str(e)}")
                
                # 再关闭上下文
                if hasattr(self, 'context') and self.context:
                    try:
                        await self.context.close()
                    except Exception as e:
                        print(f"关闭上下文时出错: {str(e)}")
                
                # 最后关闭浏览器
                if hasattr(self, 'browser') and self.browser:
                    try:
                        await self.browser.close()
                    except Exception as e:
                        print(f"关闭浏览器时出错: {str(e)}")
                
                # 重置实例变量
                self.browser = None
                self.context = None
                self.page = None
                print("浏览器资源清理完成")
            except Exception as e:
                print(f"资源清理过程中出错: {str(e)}")
                # 确保实例变量被重置
                self.browser = None
                self.context = None
                self.page = None
                
    def _get_random_fingerprint(self):
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
        """返回工具描述，符合MCP协议"""
        return {
            "name": "baidu_search",
            "description": "百度搜索工具,可以执行网络搜索并返回结果",
            "functions": [
                {
                    "name": "search",
                    "description": "执行百度搜索查询",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "搜索关键词"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "最大返回结果数量",
                                "default": 5
                            }
                        },
                        "required": ["query", "max_results"]
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