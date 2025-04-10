import unittest
import asyncio
import time
from app.tool.google_search import GoogleSearchTool

class IntegrationTestGoogleSearchTool(unittest.TestCase):
    """百度搜索工具的集成测试"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.config = {
            "google_api_key": "AIzaSyDummyKeyForTesting",  # 测试用的假API密钥
            "search_engine_id": "012345678901234567890:abcdefghijk",  # 测试用的假搜索引擎ID
            "headless": False,  # 设置为False以显示浏览器窗口
            "debug": True  # 启用调试模式
        }
        self.tool = GoogleSearchTool(self.config)
    
    def test_real_search(self):
        """测试实际执行百度搜索"""
        # 执行搜索
        start_time = time.time()
        result = self.tool.search("中国新闻", max_results=3)
        end_time = time.time()
        
        # 打印执行时间
        print(f"搜索执行时间: {end_time - start_time:.2f} 秒")
        
        # 验证结果
        self.assertEqual(result["status"], "success")
        self.assertIsNone(result["error"])
        
        # 验证结果数量
        self.assertLessEqual(len(result["results"]), 3)
        
        # 验证结果结构
        for item in result["results"]:
            self.assertIn("title", item)
            self.assertIn("link", item)
            self.assertIn("snippet", item)
            
            # 打印结果
            print(f"标题: {item['title']}")
            print(f"链接: {item['link']}")
            print(f"摘要: {item['snippet']}")
            print("-" * 50)
        
        # 验证结果内容与花朵相关
        for item in result["results"]:
            self.assertTrue(
                "花" in item["title"] or 
                "花" in item["snippet"] or 
                "flower" in item["title"].lower() or 
                "flower" in item["snippet"].lower()
            )

if __name__ == "__main__":
    unittest.main() 