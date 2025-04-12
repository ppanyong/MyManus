import unittest
from app.tool.html_parser_tool import HTMLParserTool
from unittest.mock import patch, MagicMock, AsyncMock
from playwright.async_api import async_playwright
import asyncio
import pytest

@pytest.fixture
def parser():
    return HTMLParserTool({
        'api': {
            'url': 'http://test-api',
            'api_key': 'test-key',
            'model': 'test-model'
        }
    })

@pytest.mark.asyncio
async def test_baidu_link(parser):
    """测试百度链接解析"""
    url = "http://www.baidu.com/link?url=a2V5pzDLCrZMDq3l4REGi-TIl9G_G1eEepFYNP_0wUwViwoAc9_xI0X19Fn0nSGqPg7a9fZqci_j1MhSsfmeHpRgQjsdWavsISYhP1YNAi7"
    
    # 使用mock来模拟playwright
    with patch('playwright.async_api.async_playwright') as mock_playwright:
        # 设置mock对象
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_link = AsyncMock()
        
        # 配置mock返回值
        mock_playwright.return_value = AsyncMock()
        mock_playwright.return_value.__aenter__ = AsyncMock()
        mock_playwright.return_value.__aenter__.return_value = AsyncMock()
        mock_playwright.return_value.__aenter__.return_value.chromium = AsyncMock()
        mock_playwright.return_value.__aenter__.return_value.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        
        # 模拟链接选择器
        mock_page.wait_for_selector = AsyncMock(return_value=mock_link)
        mock_page.query_selector_all = AsyncMock(return_value=[mock_link])
        mock_link.get_attribute = AsyncMock(side_effect=["https://example.com", "https://example.com"])
        mock_link.hover = AsyncMock()
        
        # 模拟页面内容
        mock_page.content = AsyncMock(return_value="""
        <html>
            <head>
                <title>测试页面标题</title>
            </head>
            <body>
                <article>
                    <h1>测试文章标题</h1>
                    <p>这是一个测试文章的内容。它包含了一些重要的信息。</p>
                    <p>这是另一个段落，用于测试摘要生成功能。</p>
                </article>
            </body>
        </html>
        """)
        
        # 模拟页面方法
        mock_page.goto = AsyncMock()
        mock_page.evaluate = AsyncMock()
        mock_page.set_default_timeout = MagicMock()
        
        # 模拟大模型响应
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "content": "这是一个测试文章的摘要。它包含了重要的信息。"
            }
            mock_post.return_value = mock_response
            
            # 测试链接解析
            result = await parser.parse_url(url)
            
            # 验证返回结果
            assert isinstance(result, dict)
            assert 'title' in result
            assert 'summary' in result
            assert 'keywords' in result
            
            # 验证内容不为空
            assert result['title'], "标题不应为空"
            assert result['summary'], "摘要不应为空"
            assert result['keywords'], "关键词不应为空"
            
            # 验证摘要内容
            assert "测试文章" in result['summary'], "摘要应包含文章内容"
            assert "重要" in result['summary'], "摘要应包含重要信息"
            
            # 验证没有触发安全验证
            assert 'error' not in result, "不应触发安全验证"
            
            # 验证浏览器被正确关闭
            mock_browser.close.assert_awaited_once()
            
            # 验证链接处理
            mock_page.wait_for_selector.assert_awaited_with('a', timeout=5000)
            mock_link.hover.assert_awaited_once()
            mock_page.goto.assert_awaited_with("https://example.com", wait_until='domcontentloaded', timeout=10000)

@pytest.mark.asyncio
async def test_browser_close_on_error(parser):
    """测试在发生错误时浏览器是否正确关闭"""
    url = "http://www.baidu.com/link?url=invalid"
    
    with patch('playwright.async_api.async_playwright') as mock_playwright:
        # 设置mock对象
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        # 配置mock返回值
        mock_playwright.return_value = AsyncMock()
        mock_playwright.return_value.__aenter__ = AsyncMock()
        mock_playwright.return_value.__aenter__.return_value = AsyncMock()
        mock_playwright.return_value.__aenter__.return_value.chromium = AsyncMock()
        mock_playwright.return_value.__aenter__.return_value.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        
        # 模拟页面访问错误
        mock_page.goto = AsyncMock(side_effect=Exception("页面访问失败"))
        mock_page.set_default_timeout = MagicMock()
        
        # 测试链接解析
        result = await parser.parse_url(url)
        
        # 验证错误处理
        assert 'error' in result
        assert '页面处理失败' in result['error']
        
        # 验证浏览器被正确关闭
        mock_browser.close.assert_awaited_once()

if __name__ == '__main__':
    unittest.main() 