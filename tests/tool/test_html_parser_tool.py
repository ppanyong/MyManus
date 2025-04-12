import pytest
from app.tool.html_parser_tool import HTMLParserTool
import requests
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup

def test_html_parser_tool_initialization():
    """测试HTML解析工具初始化"""
    parser = HTMLParserTool()
    assert parser is not None

def test_parse_url_success():
    """测试成功解析URL内容"""
    parser = HTMLParserTool()
    test_url = "https://shcas.shnu.edu.cn/18798/list1.htm"
    
    # 使用mock来模拟requests.get和HTMLFetcher
    with patch('requests.get') as mock_get, \
         patch('app.tool.html_parser_tool.HTMLFetcher') as mock_fetcher:
        
        # 设置mock响应
        mock_response = MagicMock()
        mock_response.text = """
        <html>
            <head>
                <title>非洲时事 - 上海师范大学非洲研究中心</title>
            </head>
            <body>
                <div class="content">
                    <h1>非洲时事</h1>
                    <p>2025-04-09 特朗普对51个非洲国家征收新关税的详情</p>
                    <p>2025-04-02 南非强化水资源管理 推动水安全改革</p>
                    <p>2025-03-25 恩代特瓦就任纳米比亚总统</p>
                </div>
            </body>
        </html>
        """
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # 设置HTMLFetcher的mock
        mock_fetcher_instance = mock_fetcher.return_value
        mock_fetcher_instance.parse_html.return_value = BeautifulSoup(mock_response.text, 'html.parser')
        mock_fetcher_instance.get_title.return_value = "非洲时事 - 上海师范大学非洲研究中心"
        
        # 执行测试
        result = parser.parse_url(test_url)
        
        # 验证结果
        assert result is not None
        assert "error" not in result
        assert "title" in result
        assert "summary" in result
        assert "keywords" in result
        assert "非洲" in result["title"]
        assert "时事" in result["title"]
        assert len(result["keywords"]) > 0
        assert any("非洲" in kw for kw in result["keywords"])

def test_parse_url_failure():
    """测试解析URL失败的情况"""
    parser = HTMLParserTool()
    test_url = "https://invalid-url.com"
    
    # 使用mock来模拟requests.get抛出异常
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.RequestException("连接失败")
        
        # 执行测试
        result = parser.parse_url(test_url)
        
        # 验证结果
        assert "error" in result
        assert "获取URL内容失败" in result["error"]

def test_parse_url_timeout():
    """测试URL请求超时的情况"""
    parser = HTMLParserTool()
    test_url = "https://example.com"
    
    # 使用mock来模拟requests.get超时
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.Timeout("请求超时")
        
        # 执行测试
        result = parser.parse_url(test_url)
        
        # 验证结果
        assert "error" in result
        assert "获取URL内容失败" in result["error"]

def test_parse_url_invalid_html():
    """测试解析无效HTML内容"""
    parser = HTMLParserTool()
    test_url = "https://example.com"
    
    # 使用mock来模拟requests.get返回无效HTML
    with patch('requests.get') as mock_get, \
         patch('app.tool.html_parser_tool.HTMLFetcher') as mock_fetcher:
        
        mock_response = MagicMock()
        mock_response.text = "<html><body>不完整的HTML"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # 设置HTMLFetcher的mock返回None
        mock_fetcher_instance = mock_fetcher.return_value
        mock_fetcher_instance.parse_html.return_value = None
        
        # 执行测试
        result = parser.parse_url(test_url)
        
        # 验证结果
        assert "error" in result
        assert "无法解析HTML内容" in result["error"] 