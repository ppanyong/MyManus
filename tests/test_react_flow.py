import unittest
import json
import sys
import os
from unittest.mock import patch, MagicMock
import pytest
from jinja2 import Template
import requests

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.flow.react import ReactFlow
from app.flow.base import BaseFlow

class MockResponse:
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code
        
    def json(self):
        return self.json_data

class MockTemplate:
    def render(self, **kwargs):
        # 返回一个包含两个步骤的JSON字符串
        return json.dumps({
            "steps": [
                {
                    "tool": "tool1",
                    "function": "function1",
                    "parameters": {"param1": "value1"}
                },
                {
                    "tool": "tool2",
                    "function": "function2",
                    "parameters": {"param_from_step1": "{step_1}"}
                }
            ]
        })

class TestReactFlow(unittest.TestCase):
    """测试ReactFlow类"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.config = {
            "model": "gpt-3.5-turbo",
            "api_key": "test_api_key",
            "temperature": 0.7,
            "api": {
                "url": "http://test-api.com",
                "api_key": "test_api_key",
                "model": "gpt-3.5-turbo"
            }
        }
        
        # 模拟requests.post
        self.mock_response = MockResponse({
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "steps": [
                            {
                                "tool": "tool1",
                                "function": "function1",
                                "parameters": {"param1": "value1"}
                            }
                        ]
                    })
                }
            }]
        })
        
        # 使用patch来替换requests.post
        patcher = patch('app.flow.base.requests.post', return_value=self.mock_response)
        patcher.start()
        self.addCleanup(patcher.stop)
        
        self.flow = ReactFlow(self.config)
        self.flow.prompt_template = MockTemplate()
        
    @patch('app.flow.base.requests.post')
    def test_thinking_step_with_string_array(self, mock_post):
        """测试_thinking_step方法处理字符串形式数组的功能"""
        # 准备测试数据
        task = {"description": "测试任务", "purpose": "测试目的"}
        tools = []
        
        # 模拟API响应
        mock_post.return_value = MockResponse({
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "steps": [
                            {
                                "tool": "calculator",
                                "function": "add",
                                "parameters": {"a": 234, "b": 234},
                                "description": "执行234与234的加法运算"
                            }
                        ]
                    })
                }
            }]
        })
        
        # 调用测试方法
        result = self.flow._thinking_step(task, tools)
        
        # 验证结果
        self.assertEqual(result["status"], "success")
        self.assertIsInstance(result["result"], list)
        self.assertEqual(len(result["result"]), 1)
        self.assertEqual(result["result"][0]["tool"], "calculator")
        self.assertEqual(result["result"][0]["function"], "add")
        self.assertEqual(result["result"][0]["parameters"], {"a": 234, "b": 234})

@pytest.fixture
def react_flow():
    config = {
        "model": "test-model",
        "api": {
            "url": "http://test-api.com",
            "api_key": "test_api_key",
            "model": "test-model"
        }
    }
    
    # 模拟requests.post
    mock_response = MockResponse({
        "choices": [{
            "message": {
                "content": json.dumps({
                    "steps": [
                        {
                            "tool": "tool1",
                            "function": "function1",
                            "parameters": {"param1": "value1"}
                        }
                    ]
                })
            }
        }]
    })
    
    # 使用patch来替换requests.post
    with patch('app.flow.base.requests.post', return_value=mock_response):
        flow = ReactFlow(config)
        flow.prompt_template = MockTemplate()
        return flow

@pytest.fixture
def mock_tools():
    return [
        MockTool("tool1", ["function1"]),
        MockTool("tool2", ["function2"])
    ]

class MockTool:
    def __init__(self, name, functions):
        self.name = name
        self.functions = functions
        
    def get_tool_description(self):
        return {
            "name": self.name,
            "description": "Mock tool for testing",
            "functions": self.functions
        }

@pytest.mark.asyncio
@patch('app.flow.base.requests.post')
async def test_single_step_execution(mock_post, react_flow, mock_tools):
    """测试单步执行"""
    # 准备测试数据
    task = {
        "description": "测试单步执行",
        "context": "测试上下文"
    }
    
    # 模拟API响应
    mock_post.return_value = MockResponse({
        "choices": [{
            "message": {
                "content": json.dumps({
                    "steps": [
                        {
                            "tool": "tool1",
                            "function": "function1",
                            "parameters": {"param1": "value1"}
                        }
                    ]
                })
            }
        }]
    })
    
    # 模拟工具执行
    mock_tool = mock_tools[0]
    mock_tool.function1 = MagicMock(return_value={"status": "success", "result": "测试结果"})
    
    # 执行测试
    result = await react_flow.execute(task, [mock_tool])
    
    # 验证结果
    assert result["status"] == "success"
    assert "task_info" in result
    assert result["task_info"]["task"] == task
    assert result["task_info"]["thinking_result"] is not None
    assert result["task_info"]["act_result"] is not None

@pytest.mark.asyncio
@patch('app.flow.base.requests.post')
async def test_multi_step_execution_with_parameter_passing(mock_post, react_flow, mock_tools):
    """测试多步执行时的参数传递"""
    # 准备测试数据
    task = {
        "description": "测试多步执行",
        "context": "测试上下文"
    }
    
    # 模拟API响应
    mock_post.return_value = MockResponse({
        "choices": [{
            "message": {
                "content": json.dumps({
                    "steps": [
                        {
                            "tool": "tool1",
                            "function": "function1",
                            "parameters": {"param1": "value1"}
                        },
                        {
                            "tool": "tool2",
                            "function": "function2",
                            "parameters": {"param_from_step1": "{step_1}"}
                        }
                    ]
                })
            }
        }]
    })
    
    # 模拟工具执行
    mock_tool1 = mock_tools[0]
    mock_tool2 = mock_tools[1]
    
    # 设置第一个工具返回结果
    mock_tool1.function1 = MagicMock(return_value={"status": "success", "result": "第一步结果"})
    
    # 设置第二个工具，验证是否接收到第一个工具的结果
    def verify_parameter_passing(**kwargs):
        assert "param_from_step1" in kwargs
        assert kwargs["param_from_step1"] == "第一步结果"
        return {"status": "success", "result": "最终结果"}
    
    mock_tool2.function2 = MagicMock(side_effect=verify_parameter_passing)
    
    # 执行测试
    result = await react_flow.execute(task, [mock_tool1, mock_tool2])
    
    # 验证结果
    assert result["status"] == "success"
    assert result["task_info"]["act_result"][1]["result"] == "最终结果"  # 验证最后一步的结果
    assert len(result["task_info"]["thinking_result"]) == 2  # 确保生成了两个步骤
    assert result["task_info"]["act_result"] is not None

@pytest.mark.asyncio
@patch('app.flow.base.requests.post')
async def test_error_handling(mock_post, react_flow, mock_tools):
    """测试错误处理"""
    # 准备测试数据
    task = {
        "description": "测试错误处理",
        "context": "测试上下文"
    }
    
    # 模拟API响应
    mock_post.return_value = MockResponse({
        "choices": [{
            "message": {
                "content": json.dumps({
                    "steps": [
                        {
                            "tool": "tool1",
                            "function": "function1",
                            "parameters": {"param1": "value1"}
                        }
                    ]
                })
            }
        }]
    })
    
    # 模拟工具执行抛出异常
    mock_tool = mock_tools[0]
    mock_tool.function1 = MagicMock(side_effect=Exception("测试错误"))
    
    # 执行测试
    result = await react_flow.execute(task, [mock_tool])
    
    # 验证结果
    assert result["status"] == "error"
    assert "error" in result
    assert "测试错误" in result["error"]
    assert result["task_info"]["act_result"][0]["status"] == "error"  # 验证步骤结果的状态
    assert "测试错误" in result["task_info"]["act_result"][0]["error"]  # 验证步骤结果的错误信息

@pytest.mark.asyncio
@patch('app.flow.base.requests.post')
async def test_step_parameter_parsing(mock_post, react_flow, mock_tools):
    """测试步骤参数解析"""
    # 准备测试数据
    task = {
        "description": "测试参数解析",
        "context": "测试上下文"
    }
    
    # 模拟API响应
    mock_post.return_value = MockResponse({
        "choices": [{
            "message": {
                "content": json.dumps({
                    "steps": [
                        {
                            "tool": "tool1",
                            "function": "function1",
                            "parameters": {"param1": "value1"}
                        }
                    ]
                })
            }
        }]
    })
    
    # 模拟工具执行
    mock_tool = mock_tools[0]
    mock_tool.function1 = MagicMock(return_value={"status": "success", "result": "测试结果"})
    
    # 执行测试
    result = await react_flow.execute(task, [mock_tool])
    
    # 验证步骤参数解析
    assert result["status"] == "success"
    assert "task_info" in result
    steps = result["task_info"]["thinking_result"]
    assert isinstance(steps, list)
    for step in steps:
        assert "tool" in step
        assert "function" in step
        assert "parameters" in step
        assert isinstance(step["parameters"], dict)

if __name__ == '__main__':
    unittest.main() 