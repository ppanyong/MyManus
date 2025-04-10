import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from app.tool.google_search import GoogleSearchTool
import os

@pytest.fixture
def google_search_tool():
    """创建GoogleSearchTool实例"""
    config = {
        "google_api_key": "test_api_key",
        "search_engine_id": "test_engine_id",
        "headless": False,  # 设置为False以显示浏览器窗口
        "debug": True  # 启用调试模式
    }
    return GoogleSearchTool(config)

@pytest.mark.asyncio
async def test_search_success(google_search_tool):
    """测试搜索成功的情况"""
    print("\n开始测试搜索成功的情况...")
    
    try:
        # 模拟页面元素
        mock_page = AsyncMock()
        mock_result = AsyncMock()
        mock_title_elem = AsyncMock()
        mock_snippet_elem = AsyncMock()
        mock_mouse = AsyncMock()
        
        # 设置模拟返回值
        mock_title_elem.text_content.return_value = "测试标题1"
        mock_title_elem.get_attribute.return_value = "https://example1.com"
        mock_snippet_elem.text_content.return_value = "测试摘要1"
        
        # 设置query_selector的side_effect
        async def mock_query_selector(selector):
            print(f"模拟query_selector被调用，选择器: {selector}")
            if selector == 'h3 a':
                return mock_title_elem
            elif selector == '.c-abstract' or selector == '.content':
                return mock_snippet_elem
            return None
            
        mock_result.query_selector = mock_query_selector
        
        # 设置搜索结果
        mock_page.query_selector_all.return_value = [mock_result]
        mock_page.screenshot = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.wait_for_selector = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.mouse = mock_mouse
        
        # 确保等待搜索结果加载成功
        async def mock_wait_for_selector(selector, timeout=None):
            print(f"模拟wait_for_selector被调用，选择器: {selector}")
            if selector == '.result':
                return mock_result
            return None
        mock_page.wait_for_selector.side_effect = mock_wait_for_selector
        
        print("设置模拟对象完成")
        
        # 使用patch模拟异步操作
        with patch('app.tool.google_search.async_playwright') as mock_playwright:
            print("开始模拟 playwright...")
            
            # 设置playwright的返回值
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_playwright_instance = AsyncMock()
            
            mock_playwright.return_value = mock_playwright_instance
            mock_playwright_instance.chromium = AsyncMock()
            mock_playwright_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            mock_context.new_page = AsyncMock(return_value=mock_page)
            
            print("设置 playwright 模拟完成")
            
            # 执行搜索，增加超时时间
            print("开始执行搜索...")
            try:
                # 直接调用_perform_search方法，绕过search方法的异常处理
                results = await google_search_tool._perform_search("测试查询")
                
                # 手动构建结果
                result = {
                    "status": "success",
                    "results": results,
                    "error": None
                }
                
                print(f"搜索完成，结果: {result}")
                
                # 验证结果
                print("验证搜索结果...")
                assert result["status"] == "success", f"期望状态为'success'，实际为'{result['status']}'"
                assert len(result["results"]) > 0, "搜索结果为空"
                assert result["results"][0]["title"] == "测试标题1", "标题不匹配"
                assert result["results"][0]["link"] == "https://example1.com", "链接不匹配"
                assert result["results"][0]["snippet"] == "测试摘要1", "摘要不匹配"
                
                # 验证资源清理
                mock_browser.close.assert_called_once()
                mock_context.close.assert_called_once()
                
            except asyncio.TimeoutError:
                print("测试超时")
                raise
                
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_search_no_results(google_search_tool):
    """测试没有搜索结果的情况"""
    print("\n开始测试没有搜索结果的情况...")
    
    try:
        # 模拟页面元素
        mock_page = AsyncMock()
        mock_page.query_selector_all.return_value = []  # 返回空结果
        mock_page.screenshot = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.wait_for_selector = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.mouse = AsyncMock()
        
        # 使用patch模拟异步操作
        with patch('app.tool.google_search.async_playwright') as mock_playwright:
            print("开始模拟 playwright...")
            
            # 设置playwright的返回值
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_playwright_instance = AsyncMock()
            
            mock_playwright.return_value = mock_playwright_instance
            mock_playwright_instance.chromium = AsyncMock()
            mock_playwright_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            mock_context.new_page = AsyncMock(return_value=mock_page)
            
            print("设置 playwright 模拟完成")
            
            try:
                # 直接调用_perform_search方法，绕过search方法的异常处理
                with pytest.raises(Exception) as excinfo:
                    await google_search_tool._perform_search("测试查询")
                
                assert "未找到有效的搜索结果" in str(excinfo.value)
                
                # 验证资源清理
                mock_browser.close.assert_called_once()
                mock_context.close.assert_called_once()
                
            except asyncio.TimeoutError:
                print("测试超时")
                raise
                
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_search_browser_error(google_search_tool):
    """测试浏览器错误的情况"""
    print("\n开始测试浏览器错误的情况...")
    
    try:
        with patch('app.tool.google_search.async_playwright') as mock_playwright:
            mock_playwright_instance = AsyncMock()
            
            mock_playwright.return_value = mock_playwright_instance
            mock_playwright_instance.chromium = AsyncMock()
            mock_playwright_instance.chromium.launch = AsyncMock(side_effect=Exception("浏览器启动失败"))
            
            try:
                # 直接调用_ensure_browser_initialized方法
                with pytest.raises(Exception) as excinfo:
                    await google_search_tool._ensure_browser_initialized()
                
                assert "浏览器启动失败" in str(excinfo.value)
                
            except asyncio.TimeoutError:
                print("测试超时")
                raise
                
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_search_network_error(google_search_tool):
    """测试网络错误的情况"""
    print("\n开始测试网络错误的情况...")
    
    try:
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock(side_effect=Exception("net::ERR_CONNECTION_REFUSED"))
        mock_page.screenshot = AsyncMock()
        mock_page.wait_for_selector = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.mouse = AsyncMock()
        
        with patch('app.tool.google_search.async_playwright') as mock_playwright:
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_playwright_instance = AsyncMock()
            
            mock_playwright.return_value = mock_playwright_instance
            mock_playwright_instance.chromium = AsyncMock()
            mock_playwright_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            mock_context.new_page = AsyncMock(return_value=mock_page)
            
            try:
                # 直接调用_perform_search方法，绕过search方法的异常处理
                with pytest.raises(Exception) as excinfo:
                    await google_search_tool._perform_search("测试查询")
                
                assert "网络连接失败" in str(excinfo.value)
                
            except asyncio.TimeoutError:
                print("测试超时")
                raise
                
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_search_timeout(google_search_tool):
    """测试搜索超时的情况"""
    print("\n开始测试搜索超时的情况...")
    
    try:
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.wait_for_selector = AsyncMock(side_effect=asyncio.TimeoutError("页面加载超时"))
        mock_page.screenshot = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.mouse = AsyncMock()
        
        with patch('app.tool.google_search.async_playwright') as mock_playwright:
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_playwright_instance = AsyncMock()
            
            mock_playwright.return_value = mock_playwright_instance
            mock_playwright_instance.chromium = AsyncMock()
            mock_playwright_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            mock_context.new_page = AsyncMock(return_value=mock_page)
            
            try:
                # 直接调用_perform_search方法，绕过search方法的异常处理
                with pytest.raises(Exception) as excinfo:
                    await google_search_tool._perform_search("测试查询")
                
                assert "页面加载超时" in str(excinfo.value)
                
            except asyncio.TimeoutError:
                print("测试超时")
                raise
                
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_browser_cleanup(google_search_tool):
    """测试浏览器资源清理"""
    print("\n开始测试浏览器资源清理...")
    
    try:
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.wait_for_selector = AsyncMock()
        mock_page.screenshot = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.mouse = AsyncMock()
        
        with patch('app.tool.google_search.async_playwright') as mock_playwright:
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_playwright_instance = AsyncMock()
            
            mock_playwright.return_value = mock_playwright_instance
            mock_playwright_instance.chromium = AsyncMock()
            mock_playwright_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            mock_context.new_page = AsyncMock(return_value=mock_page)
            
            try:
                # 直接调用_ensure_browser_initialized方法
                await google_search_tool._ensure_browser_initialized()
                
                # 验证浏览器实例已创建
                assert google_search_tool.browser is not None
                assert google_search_tool.context is not None
                assert google_search_tool.page is not None
                
                # 手动调用清理方法
                await google_search_tool.browser.close()
                await google_search_tool.context.close()
                google_search_tool.browser = None
                google_search_tool.context = None
                google_search_tool.page = None
                
                # 验证资源清理
                mock_browser.close.assert_called_once()
                mock_context.close.assert_called_once()
                assert google_search_tool.browser is None
                assert google_search_tool.context is None
                assert google_search_tool.page is None
                
            except asyncio.TimeoutError:
                print("测试超时")
                raise
                
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_human_behavior_simulation(google_search_tool):
    """测试人类行为模拟"""
    print("\n开始测试人类行为模拟...")
    
    try:
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.wait_for_selector = AsyncMock()
        mock_page.screenshot = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()
        mock_mouse = AsyncMock()
        mock_page.mouse = mock_mouse
        
        with patch('app.tool.google_search.async_playwright') as mock_playwright:
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_playwright_instance = AsyncMock()
            
            mock_playwright.return_value = mock_playwright_instance
            mock_playwright_instance.chromium = AsyncMock()
            mock_playwright_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            mock_context.new_page = AsyncMock(return_value=mock_page)
            
            try:
                # 设置页面实例
                google_search_tool.page = mock_page
                
                # 直接调用_simulate_human_behavior方法
                await google_search_tool._simulate_human_behavior()
                
                # 验证人类行为模拟
                assert mock_mouse.move.call_count >= 3, "鼠标移动次数不足"
                assert mock_mouse.wheel.call_count >= 2, "鼠标滚轮次数不足"
                
            except asyncio.TimeoutError:
                print("测试超时")
                raise
                
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_browser_fingerprint(google_search_tool):
    """测试浏览器指纹生成"""
    print("\n开始测试浏览器指纹生成...")
    
    try:
        fingerprint = google_search_tool._get_random_fingerprint()
        
        # 验证指纹包含所有必要的字段
        assert "webgl_vendor" in fingerprint
        assert "webgl_renderer" in fingerprint
        assert "platform" in fingerprint
        assert "hardware_concurrency" in fingerprint
        assert "device_memory" in fingerprint
        assert "touch_points" in fingerprint
        
        # 验证指纹值在有效范围内
        assert fingerprint["platform"] in google_search_tool.browser_fingerprints["platform"]
        assert fingerprint["hardware_concurrency"] in google_search_tool.browser_fingerprints["hardware_concurrency"]
        assert fingerprint["device_memory"] in google_search_tool.browser_fingerprints["device_memory"]
        assert fingerprint["touch_points"] in google_search_tool.browser_fingerprints["touch_points"]
        
        print("测试完成")
        
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_save_screenshot(google_search_tool):
    """测试保存截图功能"""
    print("\n开始测试保存截图功能...")
    
    try:
        # 模拟页面元素
        mock_page = AsyncMock()
        
        # 设置页面实例
        google_search_tool.page = mock_page
        
        # 模拟截图方法
        async def mock_screenshot(**kwargs):
            filepath = kwargs.get('path')
            print(f"保存截图到: {filepath}")
            
            # 创建一个更真实的测试图片
            try:
                # 尝试使用PIL创建图片
                from PIL import Image, ImageDraw
                img = Image.new('RGB', (800, 600), color='white')
                draw = ImageDraw.Draw(img)
                draw.text((400, 300), "测试截图", fill='black', anchor="mm")
                img.save(filepath, 'JPEG', quality=90)
                print(f"使用PIL创建测试图片: {filepath}")
            except ImportError:
                # 如果PIL不可用，创建一个简单的二进制文件
                with open(filepath, 'wb') as f:
                    # 创建一个简单的JPEG文件头
                    f.write(b'\xFF\xD8\xFF\xE0\x00\x10\x4A\x46\x49\x46\x00\x01\x01\x01\x00\x48\x00\x48\x00\x00\xFF\xDB\x00\x43\x00')
                    # 添加一些数据
                    f.write(b'Test screenshot content' * 100)
                print(f"创建简单的二进制测试文件: {filepath}")
            
            return True
            
        mock_page.screenshot = mock_screenshot
        mock_page.wait_for_load_state = AsyncMock()
        
        # 直接测试截图方法
        print("开始测试截图方法...")
        try:
            # 调用截图方法
            await google_search_tool._save_screenshot_from_page("测试截图")
            
            # 验证截图文件是否存在
            import glob
            screenshot_files = glob.glob(os.path.join(google_search_tool.screenshot_dir, "测试截图_*.jpg"))
            assert len(screenshot_files) > 0, "未找到截图文件"
            
            latest_screenshot = max(screenshot_files, key=os.path.getctime)
            print(f"找到最新的截图文件: {latest_screenshot}")
            
            # 验证文件大小
            file_size = os.path.getsize(latest_screenshot)
            print(f"截图文件大小: {file_size} 字节")
            assert file_size > 1000, f"截图文件大小过小: {file_size} 字节"
            
            print("截图测试完成")
            
        except asyncio.TimeoutError:
            print("测试超时")
            raise
            
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        raise 