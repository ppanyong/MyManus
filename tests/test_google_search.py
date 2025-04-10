import unittest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from app.tool.google_search import GoogleSearchTool

class AsyncContextManagerMock:
    """异步上下文管理器的模拟类"""
    def __init__(self, mock_return):
        self.mock_return = mock_return
        
    async def __aenter__(self):
        return self.mock_return
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

class TestGoogleSearchTool(unittest.TestCase):
    """测试Google搜索工具"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.config = {
            "google_api_key": "test_api_key",
            "search_engine_id": "test_engine_id",
            "headless": False,  # 设置为False以显示浏览器窗口
            "debug": True  # 启用调试模式
        }
        self.tool = GoogleSearchTool(self.config)
    
    @patch('app.tool.google_search.async_playwright')
    def test_search_with_playwright(self, mock_playwright):
        """测试使用Playwright执行搜索"""
        # 模拟Playwright的异步上下文管理器
        mock_playwright_instance = AsyncMock()
        
        # 模拟浏览器和上下文
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_playwright_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        
        # 模拟页面
        mock_page = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        
        # 模拟搜索结果元素
        mock_result1 = AsyncMock()
        mock_result2 = AsyncMock()
        mock_page.query_selector_all = AsyncMock(return_value=[mock_result1, mock_result2])
        
        # 模拟标题元素
        mock_title_element1 = AsyncMock()
        mock_title_element2 = AsyncMock()
        mock_result1.query_selector = AsyncMock(return_value=mock_title_element1)
        mock_result2.query_selector = AsyncMock(return_value=mock_title_element2)
        mock_title_element1.inner_text = AsyncMock(return_value="美丽的花朵图片")
        mock_title_element2.inner_text = AsyncMock(return_value="花园中的花朵")
        
        # 模拟链接元素
        mock_link_element1 = AsyncMock()
        mock_link_element2 = AsyncMock()
        mock_link_element1.get_attribute = AsyncMock(return_value="https://example.com/flowers1")
        mock_link_element2.get_attribute = AsyncMock(return_value="https://example.com/flowers2")
        
        # 模拟摘要元素
        mock_snippet_element1 = AsyncMock()
        mock_snippet_element2 = AsyncMock()
        mock_snippet_element1.inner_text = AsyncMock(return_value="这是一些美丽的花朵图片")
        mock_snippet_element2.inner_text = AsyncMock(return_value="花园中盛开的鲜花")
        
        # 设置query_selector的side_effect
        mock_result1.query_selector = AsyncMock(side_effect=[
            mock_title_element1,
            mock_link_element1,
            mock_snippet_element1
        ])
        mock_result2.query_selector = AsyncMock(side_effect=[
            mock_title_element2,
            mock_link_element2,
            mock_snippet_element2
        ])
        
        # 设置Playwright的返回值
        mock_playwright.return_value = AsyncContextManagerMock(mock_playwright_instance)
        
        # 执行搜索
        result = self.tool.search("花朵图片", max_results=2)
        
        # 验证结果
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["results"]), 2)
        self.assertIsNone(result["error"])
        
        # 验证第一个结果
        self.assertEqual(result["results"][0]["title"], "美丽的花朵图片")
        self.assertEqual(result["results"][0]["link"], "https://example.com/flowers1")
        self.assertEqual(result["results"][0]["snippet"], "这是一些美丽的花朵图片")
        
        # 验证第二个结果
        self.assertEqual(result["results"][1]["title"], "花园中的花朵")
        self.assertEqual(result["results"][1]["link"], "https://example.com/flowers2")
        self.assertEqual(result["results"][1]["snippet"], "花园中盛开的鲜花")
        
        # 验证Playwright的调用
        mock_playwright_instance.chromium.launch.assert_called_once_with(headless=False)
        mock_browser.new_context.assert_called_once()
        mock_page.goto.assert_called_once_with("https://www.google.com/search?q=%E8%8A%B1%E6%9C%B5%E5%9B%BE%E7%89%87")
        mock_browser.close.assert_called_once()
    
    def test_tool_description(self):
        """测试工具描述"""
        description = self.tool.get_tool_description()
        
        self.assertEqual(description["name"], "google_search")
        self.assertEqual(description["description"], "Google搜索工具,可以执行网络搜索并返回结果")
        self.assertEqual(len(description["functions"]), 1)
        
        search_function = description["functions"][0]
        self.assertEqual(search_function["name"], "search")
        self.assertEqual(search_function["description"], "执行Google搜索查询")
        
        # 验证参数
        self.assertEqual(search_function["parameters"]["required"], ["query"])
        self.assertEqual(search_function["parameters"]["properties"]["query"]["type"], "string")
        self.assertEqual(search_function["parameters"]["properties"]["max_results"]["type"], "integer")
        self.assertEqual(search_function["parameters"]["properties"]["max_results"]["default"], 5)
        
        # 验证返回值
        self.assertEqual(search_function["returns"]["properties"]["status"]["type"], "string")
        self.assertEqual(search_function["returns"]["properties"]["results"]["type"], "array")
        self.assertEqual(search_function["returns"]["properties"]["error"]["type"], "string")

if __name__ == "__main__":
    unittest.main() 