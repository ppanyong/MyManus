import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any, List
import logging
from urllib.parse import urljoin
import time
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

class HTMLFetcher:
    """HTML页面内容获取工具类"""
    
    def __init__(self, headers: Optional[Dict[str, str]] = None, proxy: Optional[Dict[str, str]] = None):
        """
        初始化HTML获取器
        
        Args:
            headers: 可选的请求头信息
            proxy: 可选的代理设置
        """
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.proxy = proxy
        self.session = requests.Session()
        if proxy:
            self.session.proxies.update(proxy)
    
    def fetch_page(self, url: str, timeout: int = 10) -> Optional[str]:
        """
        获取网页内容
        
        Args:
            url: 目标网页URL
            timeout: 请求超时时间（秒）
            
        Returns:
            网页HTML内容，如果获取失败则返回None
        """
        try:
            response = self.session.get(url, headers=self.headers, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"获取网页内容失败: {url}, 错误: {str(e)}")
            return None
    
    def parse_html(self, html_content: str) -> Optional[BeautifulSoup]:
        """
        解析HTML内容
        
        Args:
            html_content: HTML内容字符串
            
        Returns:
            BeautifulSoup对象，如果解析失败则返回None
        """
        try:
            return BeautifulSoup(html_content, 'html.parser')
        except Exception as e:
            logger.error(f"解析HTML内容失败: {str(e)}")
            return None
    
    def get_title(self, soup: BeautifulSoup) -> Optional[str]:
        """
        获取网页标题
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            网页标题，如果获取失败则返回None
        """
        try:
            return soup.title.string.strip() if soup.title else None
        except Exception as e:
            logger.error(f"获取标题失败: {str(e)}")
            return None
    
    def get_meta_description(self, soup: BeautifulSoup) -> Optional[str]:
        """
        获取网页meta描述
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            meta描述内容，如果获取失败则返回None
        """
        try:
            meta = soup.find('meta', attrs={'name': 'description'})
            return meta.get('content') if meta else None
        except Exception as e:
            logger.error(f"获取meta描述失败: {str(e)}")
            return None
    
    def get_all_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        获取网页中所有链接
        
        Args:
            soup: BeautifulSoup对象
            base_url: 基础URL，用于处理相对路径
            
        Returns:
            链接列表
        """
        try:
            links = []
            for a in soup.find_all('a', href=True):
                href = a.get('href')
                if href:
                    absolute_url = urljoin(base_url, href)
                    links.append(absolute_url)
            return links
        except Exception as e:
            logger.error(f"获取链接失败: {str(e)}")
            return []
    
    def get_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """
        获取网页中所有图片
        
        Args:
            soup: BeautifulSoup对象
            base_url: 基础URL，用于处理相对路径
            
        Returns:
            图片信息列表，每个图片包含src和alt属性
        """
        try:
            images = []
            for img in soup.find_all('img'):
                src = img.get('src')
                if src:
                    absolute_src = urljoin(base_url, src)
                    images.append({
                        'src': absolute_src,
                        'alt': img.get('alt', ''),
                        'title': img.get('title', '')
                    })
            return images
        except Exception as e:
            logger.error(f"获取图片失败: {str(e)}")
            return []
    
    def get_rendered_page(self, url: str, wait_time: int = 2) -> Optional[str]:
        """
        获取JavaScript渲染后的页面内容
        
        Args:
            url: 目标网页URL
            wait_time: 等待页面加载的时间（秒）
            
        Returns:
            渲染后的HTML内容，如果获取失败则返回None
        """
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                page.goto(url)
                time.sleep(wait_time)  # 等待JavaScript执行
                content = page.content()
                browser.close()
                return content
        except Exception as e:
            logger.error(f"获取渲染页面失败: {str(e)}")
            return None 