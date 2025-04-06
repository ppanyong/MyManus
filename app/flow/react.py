import ast
from typing import Dict, Any, List, Optional, Tuple
import os
from jinja2 import Template
from .base import BaseFlow
import requests
import time
import json
import re

class ReactFlow(BaseFlow):
    """反应流程类，负责执行具体任务"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化反应流程
        
        Args:
            config: 配置信息
        """
        super().__init__(config)
        self.prompt_template = None
        
    def initialize(self) -> Dict[str, Any]:
        """
        初始化反应流程
        
        Returns:
            Dict[str, Any]: 初始化结果
        """
        try:
            # 加载提示模板
            self.prompt_template = self._load_prompt_template()
            
            return {
                "status": "success",
                "result": "反应流程初始化成功",
                "error": None
            }
        except Exception as e:
            error_msg = f"反应流程初始化失败: {str(e)}"
            print(error_msg)
            return {
                "status": "error",
                "result": None,
                "error": error_msg
            }
    
    def execute(self, task: Dict[str, Any], tools: List[Any]) -> Dict[str, Any]:
        """
        执行任务，分为thinking和act两个步骤
        
        Args:
            task: 任务信息
            tools: 可用工具列表
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
            # 打印任务信息
            print(f"开始执行任务: {task.get('description', '未知任务')}")
            
            # 1. Thinking 步骤：分析任务并生成执行计划
            print("开始思考步骤...")
            thinking_result = self._thinking_step(task, tools)
            if thinking_result.get("status") == "error":
                print(f"思考步骤失败: {thinking_result.get('error')}")
                return thinking_result
                
            print(f"思考步骤完成，生成执行计划: {thinking_result.get('result')}")
                
            # 2. Act 步骤：执行具体工具
            print("开始执行步骤...")
            act_result = self._act_step(thinking_result.get("result", []), tools)
            
            print(f"执行步骤完成，结果: {act_result.get('result')}")
            
            # 3. 合并结果
            return {
                "status": "success",
                "result": act_result.get("result"),
                "task_info": {
                    "task": task,
                    "thinking_result": thinking_result.get("result"),
                    "act_result": act_result.get("result")
                }
            }
        
            
        except Exception as e:
            error_msg = f"执行任务失败: {str(e)}"
            print(error_msg)
            return {
                "status": "error",
                "result": None,
                "error": error_msg
            }
    
    def _thinking_step(self, task: Dict[str, Any], tools: List[Any]) -> Dict[str, Any]:
        """
        Thinking 步骤：分析任务并生成执行计划
        
        Args:
            task: 任务信息
            tools: 可用工具列表
            
        Returns:
            Dict[str, Any]: 思考结果
        """
        try:
            # 获取工具描述
            available_tools = []
            for tool in tools:
                try:
                    tool_desc = tool.get_tool_description()
                    available_tools.append({
                        "name": tool_desc.get("name", "未知工具"),
                        "description": tool_desc.get("description", "无描述"),
                        "functions": tool_desc.get("functions", [])
                    })
                except Exception as e:
                    print(f"获取工具描述失败: {str(e)}")
                    continue
            
            # 准备上下文
            context_temp = {
                "task": task,
                "tools": available_tools,
                "memory": self.memory if hasattr(self, "memory") else [],
                "step": "thinking",
                "debug": True  # 添加调试标志
            }
            
            # 如果任务中包含上下文信息，添加到提示模板中
            if "context" in task:
                context_temp["context"] = task["context"]
                print(f"使用上下文信息: {task['context']}")
            
            # 渲染提示模板 - 使用**context将字典解包为关键字参数
            prompt = self.prompt_template.render(**context_temp)
            
            # 调用大模型
            response = super().execute(prompt)
            
            if response.get("status") == "error":
                return response
                
            # 解析响应
            content = super()._parse_steps(response.get("result", {}))
            
            # 如果content是字符串，尝试解析为JSON
            if isinstance(content, str):
                try:
                    # 尝试将字符串转换为 Python 对象
                    steps = json.loads(content)
                except json.JSONDecodeError:
                # 如果解析失败，尝试使用更宽松的方式

                    try:
                        # 使用 ast.literal_eval 解析 Python 字面量
                        steps = ast.literal_eval(content)
                    except (SyntaxError, ValueError):
                        # 如果仍然失败，返回空列表
                        steps = []
                        print(f"无法React任务: {content}")
            else:
                # 如果content不是字符串，直接使用
                steps = content
                
            print(f"解析后的步骤: {steps}")
            # 确保返回的是列表格式
            if isinstance(steps, dict):
                # 如果steps是字典，尝试提取列表
                if "response" in steps and isinstance(steps["response"], list):
                    steps = steps["response"]
                elif "steps" in steps and isinstance(steps["steps"], list):
                    steps = steps["steps"]
                else:
                    # 如果没有找到列表，返回空列表
                    steps = []
            elif not isinstance(steps, list):
                # 如果不是字典也不是列表，返回空列表
                steps = []

            
            return {
                "status": "success",
                "result": steps
            }
                
        except Exception as e:
            error_msg = f"思考步骤失败: {str(e)}"
            print(error_msg)
            return {
                "status": "error",
                "result": None,
                "error": error_msg
            }
        
    def _parse_steps(self, response: Dict[str, Any]) -> List[str]:
        """解析API响应，提取步骤列表
        
        Args:
            response: API响应数据
            
        Returns:
            List[str]: 解析后的步骤列表
        """
        try:
            # 从 API 响应中提取文本内容
            if isinstance(response, dict):
                # 尝试从不同的响应格式中提取文本
                text = response.get('response', '')  # 对于 Ollama 格式
                if not text:
                    text = response.get('choices', [{}])[0].get('message', {}).get('content', '')  # 对于 OpenAI 格式
                if not text:
                    text = response.get('result', '')  # 对于其他格式
            else:
                text = str(response)
            
            # 使用正则表达式匹配 JSON 部分
            # 匹配 ```json 和 ``` 之间的内容
            json_pattern = r'```json\s*([\s\S]*?)\s*```'
            json_match = re.search(json_pattern, text)
            
            if json_match:
                json_str = json_match.group(1).strip()
                # 解析 JSON 字符串
                json_data = json.loads(json_str)
                # 获取步骤列表
                steps = json_data.get("steps", [])
                return str(steps)
            else:
                # 如果没有找到 JSON 结构，则使用原来的方法解析
                steps = [step.strip() for step in text.split('\n') 
                        if step.strip() and not step.startswith('#')]
                return steps[:20]
            
        except Exception as e:
            print(f"解析步骤失败: {str(e)}")
            return []
        

    def _act_step(self, steps: List[Dict[str, Any]], tools: List[Any]) -> Dict[str, Any]:
        """
        Act 步骤：执行具体工具
        
        Args:
            steps: 执行步骤列表
            tools: 可用工具列表
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
            results = []
            
            # 确保 steps 是列表
            if not isinstance(steps, list):
                steps = [steps]
            
            print(f"准备执行 {len(steps)} 个步骤")
            
            for i, step in enumerate(steps):
                print(f"执行步骤 {i+1}/{len(steps)}: {step}")
                
                # 确保 step 是字典
                if not isinstance(step, dict):
                    error_msg = f"步骤格式错误: {step}"
                    print(error_msg)
                    results.append({
                        "status": "error",
                        "result": None,
                        "error": error_msg
                    })
                    continue
                
                # 查找对应的工具
                tool_name = step.get("tool")
                if not tool_name:
                    error_msg = "步骤中缺少工具名称"
                    print(error_msg)
                    results.append({
                        "status": "error",
                        "result": None,
                        "error": error_msg
                    })
                    continue
                
                print(f"查找工具: {tool_name}")
                tool = self._find_tool(tool_name, tools)
                
                if not tool:
                    error_msg = f"未找到工具: {tool_name}"
                    print(error_msg)
                    results.append({
                        "status": "error",
                        "result": None,
                        "error": error_msg
                    })
                    continue
                
                # 执行工具
                try:
                    # 获取工具函数
                    function_name = step.get("function")
                    if not function_name:
                        error_msg = "步骤中缺少函数名称"
                        print(error_msg)
                        results.append({
                            "status": "error",
                            "result": None,
                            "error": error_msg
                        })
                        continue
                    
                    if not hasattr(tool, function_name):
                        error_msg = f"工具 {tool_name} 没有函数 {function_name}"
                        print(error_msg)
                        results.append({
                            "status": "error",
                            "result": None,
                            "error": error_msg
                        })
                        continue
                    
                    # 获取函数参数
                    params = step.get("parameters", {})
                    if not isinstance(params, dict):
                        params = {}
                    
                    print(f"调用函数: {tool_name}.{function_name}，参数: {params}")
                    
                    # 调用函数
                    function = getattr(tool, function_name)
                    result = function(**params)
                    
                    print(f"函数调用成功，结果: {result}")
                    
                    results.append({
                        "status": "success",
                        "result": result,
                        "error": None
                    })
                    
                except Exception as e:
                    error_msg = f"执行工具 {tool_name}.{function_name} 失败: {str(e)}"
                    print(error_msg)
                    results.append({
                        "status": "error",
                        "result": None,
                        "error": error_msg
                    })
            
            print(f"所有步骤执行完成，结果: {results}")
            
            return {
                "status": "success",
                "result": results
            }
            
        except Exception as e:
            error_msg = f"执行步骤失败: {str(e)}"
            print(error_msg)
            return {
                "status": "error",
                "result": None,
                "error": error_msg
            }
    
    def _find_tool(self, tool_name: str, tools: List[Any]) -> Optional[Any]:
        """
        查找工具
        
        Args:
            tool_name: 工具名称
            tools: 工具列表
            
        Returns:
            Optional[Any]: 找到的工具或None
        """
        for tool in tools:
            try:
                tool_desc = tool.get_tool_description()
                if tool_desc.get("name") == tool_name:
                    return tool
            except Exception:
                continue
        return None
    
    def _parse_steps(self, result_str: str) -> List[Dict[str, Any]]:
        """
        解析步骤
        
        Args:
            result_str: 结果字符串
            
        Returns:
            List[Dict[str, Any]]: 步骤列表
        """
        try:
            # 如果 result_str 不是字符串，直接返回
            if not isinstance(result_str, str):
                print(f"解析步骤失败: result_str 不是字符串: {result_str}")
                return []
            
            # 尝试解析JSON
            try:
                steps = json.loads(result_str)
            except json.JSONDecodeError:
                print(f"解析步骤失败: 无法解析JSON: {result_str}")
                return []
            
            # 确保是列表
            if not isinstance(steps, list):
                if isinstance(steps, dict) and "steps" in steps:
                    steps = steps["steps"]
                else:
                    steps = [steps]
            
            # 验证每个步骤
            validated_steps = []
            for step in steps:
                if isinstance(step, dict):
                    # 确保必要字段存在
                    if "tool" in step and "function" in step:
                        # 确保parameters字段存在且为字典类型
                        if "parameters" not in step:
                            step["parameters"] = {}
                        elif not isinstance(step["parameters"], dict):
                            step["parameters"] = {}
                            
                        validated_steps.append(step)
            
            return validated_steps
            
        except Exception as e:
            print(f"解析步骤失败: {str(e)}")
            return []
    
    def _load_prompt_template(self) -> Template:
        """
        加载提示模板
        
        Returns:
            Template: Jinja2模板
        """
        template_path = os.path.join(os.path.dirname(__file__), '..', '..', 'prompt', 'react.jinja')
        with open(template_path, 'r', encoding='utf-8') as f:
            return Template(f.read())
    