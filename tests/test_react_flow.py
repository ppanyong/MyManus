import unittest
import json
import sys
import os
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.flow.react import ReactFlow

class TestReactFlow(unittest.TestCase):
    """测试ReactFlow类"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.config = {
            "model": "gpt-3.5-turbo",
            "api_key": "test_api_key",
            "temperature": 0.7
        }
        self.flow = ReactFlow(self.config)
        self.flow.initialize()
        
    @patch('app.flow.base.BaseFlow.execute')
    def test_thinking_step_with_string_array(self, mock_execute):
        """测试_thinking_step方法处理字符串形式数组的功能"""
        # 准备测试数据
        task = {"description": "测试任务", "purpose": "测试目的"}
        tools = []
        
        # 模拟API响应
        mock_response = {
            "status": "success",
            "result": {
                "response": [
                    {
                        "tool": "calculator",
                        "function": "add",
                        "parameters": {"a": 234, "b": 234},
                        "description": "执行234与234的加法运算"
                    }
                ]
            }
        }
        mock_execute.return_value = mock_response
        
        # 调用测试方法
        result = self.flow._thinking_step(task, tools)
        
        # 验证结果
        self.assertEqual(result["status"], "success")
        self.assertIsInstance(result["result"], list)
        self.assertEqual(len(result["result"]), 1)
        self.assertEqual(result["result"][0]["tool"], "calculator")
        self.assertEqual(result["result"][0]["function"], "add")
        self.assertEqual(result["result"][0]["parameters"], {"a": 234, "b": 234})
        self.assertEqual(result["result"][0]["description"], "执行234与234的加法运算")
        
    @patch('app.flow.base.BaseFlow.execute')
    def test_thinking_step_with_json_steps(self, mock_execute):
        """测试_thinking_step方法处理JSON格式的steps的功能"""
        # 准备测试数据
        task = {"description": "测试任务", "purpose": "测试目的"}
        tools = []
        
        # 模拟API响应
        steps = [
            {
                "tool": "calculator",
                "function": "add",
                "parameters": {"a": 234, "b": 234},
                "description": "执行234与234的加法运算"
            }
        ]
        mock_response = {
            "status": "success",
            "result": {
                "response": steps
            }
        }
        mock_execute.return_value = mock_response
        
        # 调用测试方法
        result = self.flow._thinking_step(task, tools)
        
        # 验证结果
        self.assertEqual(result["status"], "success")
        self.assertIsInstance(result["result"], list)
        self.assertEqual(len(result["result"]), 1)
        self.assertEqual(result["result"][0]["tool"], "calculator")
        self.assertEqual(result["result"][0]["function"], "add")
        self.assertEqual(result["result"][0]["parameters"], {"a": 234, "b": 234})
        self.assertEqual(result["result"][0]["description"], "执行234与234的加法运算")

if __name__ == '__main__':
    unittest.main() 