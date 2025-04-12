import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.tool.html_parser_tool import HTMLParserTool
from bs4 import BeautifulSoup

class TestHTMLParserTool(unittest.TestCase):
    """HTML解析工具测试类"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.parser = HTMLParserTool()
        self.test_url = "https://example.com"
        self.test_html = """
        <html>
            <head>
                <title>测试页面</title>
                <meta name="description" content="这是一个测试页面">
            </head>
            <body>
                <article>
                    <h1>测试标题</h1>
                    <p>这是一个测试段落。它包含了一些测试内容。</p>
                    <p>这是另一个测试段落。它包含了一些不同的内容。</p>
                </article>
                <div>
                    <a href="https://example.com/link1">链接1</a>
                    <a href="https://example.com/link2">链接2</a>
                </div>
                <div>
                    <img src="https://example.com/image1.jpg" alt="图片1">
                    <img src="https://example.com/image2.jpg" alt="图片2">
                </div>
            </body>
        </html>
        """
    
    @patch('app.tool.html_parser_tool.HTMLFetcher')
    def test_parse_success(self, mock_fetcher):
        """测试成功解析HTML页面"""
        # 设置mock
        mock_fetcher_instance = mock_fetcher.return_value
        mock_fetcher_instance.fetch_page.return_value = self.test_html
        mock_fetcher_instance.parse_html.return_value = BeautifulSoup(self.test_html, 'html.parser')
        mock_fetcher_instance.get_title.return_value = "测试页面"
        mock_fetcher_instance.get_meta_description.return_value = "这是一个测试页面"
        mock_fetcher_instance.get_all_links.return_value = [
            "https://example.com/link1",
            "https://example.com/link2"
        ]
        mock_fetcher_instance.get_images.return_value = [
            "https://example.com/image1.jpg",
            "https://example.com/image2.jpg"
        ]
        
        # 执行测试
        result = self.parser.parse(self.test_url)
        
        # 验证结果
        self.assertEqual(result["url"], self.test_url)
        self.assertEqual(result["title"], "测试页面")
        self.assertEqual(result["description"], "这是一个测试页面")
        self.assertIn("测试标题", result["main_content"])
        self.assertIn("测试段落", result["main_content"])
        self.assertEqual(len(result["links"]), 2)
        self.assertEqual(len(result["images"]), 2)
        self.assertGreater(len(result["keywords"]), 0)
        self.assertIn("测试", result["keywords"])
        self.assertIn("sentiment", result)
        self.assertIn("paragraphs", result)
        self.assertGreater(len(result["paragraphs"]), 0)
    
    @patch('app.tool.html_parser_tool.HTMLFetcher')
    def test_parse_fetch_failed(self, mock_fetcher):
        """测试获取页面内容失败"""
        # 设置mock
        mock_fetcher_instance = mock_fetcher.return_value
        mock_fetcher_instance.fetch_page.return_value = None
        
        # 执行测试
        result = self.parser.parse(self.test_url)
        
        # 验证结果
        self.assertEqual(result["error"], "无法获取页面内容")
    
    @patch('app.tool.html_parser_tool.HTMLFetcher')
    def test_parse_parse_failed(self, mock_fetcher):
        """测试解析HTML失败"""
        # 设置mock
        mock_fetcher_instance = mock_fetcher.return_value
        mock_fetcher_instance.fetch_page.return_value = self.test_html
        mock_fetcher_instance.parse_html.return_value = None
        
        # 执行测试
        result = self.parser.parse(self.test_url)
        
        # 验证结果
        self.assertEqual(result["error"], "无法解析HTML内容")
    
    def test_get_tool_description(self):
        """测试获取工具描述"""
        description = self.parser.get_tool_description()
        
        # 验证描述内容
        self.assertEqual(description["name"], "html_parser")
        self.assertEqual(description["description"], "HTML解析工具，可以解析网页内容并提取关键信息")
        self.assertEqual(len(description["functions"]), 1)
        self.assertEqual(description["functions"][0]["name"], "parse")
        self.assertIn("url", description["functions"][0]["parameters"]["properties"])
        self.assertIn("wait_time", description["functions"][0]["parameters"]["properties"])
        self.assertIn("use_js", description["functions"][0]["parameters"]["properties"])

if __name__ == "__main__":
    unittest.main() 