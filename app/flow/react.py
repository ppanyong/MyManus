import ast
from typing import Dict, Any, List, Optional, Tuple
import os
from jinja2 import Template
from .base import BaseFlow
import requests
import time
import json
import re
from app.tool.logger_tool import LoggerTool

# 初始化日志工具
logger_tool = LoggerTool()
logger = logger_tool.get_logger("ReactFlow")

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
        logger.info(f"初始化ReactFlow，配置: {config}")
        
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
            logger.error(error_msg)
            return {
                "status": "error",
                "result": None,
                "error": error_msg
            }
    
    async def execute(self, task: Dict[str, Any], tools: List[Any], request_id: str = None) -> Dict[str, Any]:
        """
        执行任务，分为thinking和act两个步骤
        
        Args:
            task: 任务信息
            tools: 可用工具列表
            request_id: 请求ID
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
            # 记录任务信息
            logger.info(f"[RequestID: {request_id}] 开始执行任务: {task.get('description', '未知任务')}")
            # 从task中获取上一步的结果
            previous_result = task.get("previous_result")
            if previous_result:
                logger.info(f"[RequestID: {request_id}] 获取到上一步执行结果: {previous_result}")
            else:
                logger.info(f"[RequestID: {request_id}] 未找到上一步执行结果")
                
            # 1. Thinking 步骤：分析任务并生成执行计划
            logger.info(f"[RequestID: {request_id}] 开始思考步骤...")
            thinking_result = self._thinking_step(task, tools, request_id)
            if thinking_result.get("status") == "error":
                logger.error(f"[RequestID: {request_id}] 思考步骤失败: {thinking_result.get('error')}")
                return {
                    "status": "error",
                    "error": thinking_result.get("error"),
                    "task_info": {
                        "task": task,
                        "thinking_result": None,
                        "act_result": None
                    }
                }
                
            logger.info(f"[RequestID: {request_id}] 思考步骤完成，生成执行计划: {thinking_result.get('result')}")
                
            # 2. Act 步骤：执行具体工具
            logger.info(f"[RequestID: {request_id}] 开始执行步骤...")
            act_result = await self._act_step(thinking_result.get("result", []), tools, request_id)
            
            logger.info(f"[RequestID: {request_id}] 执行步骤完成，结果: {act_result.get('result')}")
            
            # 3. 合并结果
            # 如果任何步骤执行失败，整个任务就失败
            if isinstance(act_result.get("result"), list):
                for step_result in act_result["result"]:
                    if step_result.get("status") == "error":
                        return {
                            "status": "error",
                            "error": step_result.get("error"),
                            "task_info": {
                                "task": task,
                                "thinking_result": thinking_result.get("result"),
                                "act_result": act_result.get("result")
                            }
                        }
            elif act_result.get("status") == "error":
                return {
                    "status": "error",
                    "error": act_result.get("error"),
                    "task_info": {
                        "task": task,
                        "thinking_result": thinking_result.get("result"),
                        "act_result": [act_result]
                    }
                }
            
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
            logger.error(f"[RequestID: {request_id}] {error_msg}")
            return {
                "status": "error",
                "error": error_msg,
                "task_info": {
                    "task": task,
                    "thinking_result": None,
                    "act_result": None
                }
            }
    
    def _thinking_step(self, task: Dict[str, Any], tools: List[Any], request_id: str = None) -> Dict[str, Any]:
        """
        Thinking 步骤：分析任务并生成执行计划
        
        Args:
            task: 任务信息
            tools: 可用工具列表
            request_id: 请求ID
            
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
                    logger.error(f"[RequestID: {request_id}] 获取工具描述失败: {str(e)}")
                    continue
            
            # 准备上下文
            context_temp = {
                "task": task,
                "tools": available_tools,
                "memory": self.memory if hasattr(self, "memory") else [],
                "step": "thinking",
                "debug": True,  # 添加调试标志
                "request_id": request_id
            }
            
            # 如果任务中包含上下文信息，添加到提示模板中
            if "context" in task:
                context_temp["context"] = task["context"]
                logger.info(f"[RequestID: {request_id}] 使用上下文信息: {task['context']}")
            
            # 渲染提示模板 - 使用**context将字典解包为关键字参数
            prompt = self.prompt_template.render(**context_temp)
            
            # 调用大模型
            response = super().execute(prompt)
            
            if response.get("status") == "error":
                return response
                
            # 解析响应
            content = super()._parse_steps(response.get("result", {}))
            
            # 初始化步骤结果字典
            step_results = {}
            
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
                        logger.error(f"[RequestID: {request_id}] 无法React任务: {content}")
            else:
                # 如果content不是字符串，直接使用
                steps = content
                
            logger.info(f"[RequestID: {request_id}] 解析后的步骤: {steps}")
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

            # 处理步骤参数
            for step in steps:
                if isinstance(step, dict) and "parameters" in step:
                    # 确保parameters是字典类型
                    if not isinstance(step["parameters"], dict):
                        step["parameters"] = {}
                    # 处理参数中的步骤结果引用
                    for key, value in step["parameters"].items():
                        if isinstance(value, str) and value.startswith("{step_") and value.endswith("}"):
                            step_num = int(value[6:-1].split("_")[0])
                            if step_num in step_results:
                                # 获取步骤结果
                                step_result = step_results[step_num]
                                # 如果结果是字典且包含results字段，则使用results字段的值
                                if isinstance(step_result, dict):
                                    if "results" in step_result and step_result["results"]:
                                        # 如果是搜索结果，直接使用整个结果列表
                                        step["parameters"][key] = step_result["results"]
                                    elif "result" in step_result:
                                        step["parameters"][key] = step_result["result"]
                                    else:
                                        step["parameters"][key] = step_result
                                else:
                                    step["parameters"][key] = step_result
                            else:
                                # 如果步骤结果不存在，保留原始值
                                step["parameters"][key] = value

            return {
                "status": "success",
                "result": steps
            }
                
        except Exception as e:
            error_msg = f"思考步骤失败: {str(e)}"
            logger.error(f"[RequestID: {request_id}] {error_msg}")
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
            logger.error(f"解析步骤失败: {str(e)}")
            return []
        

    async def _act_step(self, steps: List[Dict[str, Any]], tools: List[Any], request_id: str = None) -> Dict[str, Any]:
        """
        Act 步骤：执行具体工具
        
        Args:
            steps: 执行步骤列表
            tools: 可用工具列表
            request_id: 请求ID
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
            results = []
            step_results = {}  # 存储每个步骤的结果
            
            # 确保 steps 是列表
            if not isinstance(steps, list):
                steps = [steps]
            
            logger.info(f"[RequestID: {request_id}] 准备执行 {len(steps)} 个步骤")
            
            for i, step in enumerate(steps):
                logger.info(f"[RequestID: {request_id}] 执行步骤 {i+1}/{len(steps)}: {step}")
                
                # 确保 step 是字典
                if not isinstance(step, dict):
                    error_msg = f"[RequestID: {request_id}] 步骤格式错误: {step}"
                    logger.error(error_msg)
                    results.append({
                        "status": "error",
                        "result": None,
                        "error": error_msg
                    })
                    continue
                
                # 查找对应的工具
                tool_name = step.get("tool")
                if not tool_name:
                    error_msg = "[RequestID: {request_id}] 步骤中缺少工具名称"
                    logger.error(error_msg)
                    results.append({
                        "status": "error",
                        "result": None,
                        "error": error_msg
                    })
                    continue
                
                logger.info(f"[RequestID: {request_id}] 查找工具: {tool_name}")
                tool = self._find_tool(tool_name, tools)
                
                if not tool:
                    error_msg = f"[RequestID: {request_id}] 未找到工具: {tool_name}"
                    logger.error(error_msg)
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
                        error_msg = "[RequestID: {request_id}] 步骤中缺少函数名称"
                        logger.error(error_msg)
                        results.append({
                            "status": "error",
                            "result": None,
                            "error": error_msg
                        })
                        continue
                    
                    if not hasattr(tool, function_name):
                        error_msg = f"[RequestID: {request_id}] 工具 {tool_name} 没有函数 {function_name}"
                        logger.error(error_msg)
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
                    
                    # 处理参数中的步骤结果引用
                    for key, value in params.items():
                        if isinstance(value, str) and value.startswith("{step_") and value.endswith("}"):
                            step_num = int(value[6:-1].split("_")[0])
                            if step_num in step_results:
                                # 获取步骤结果
                                step_result = step_results[step_num]
                                # 如果结果是字典且包含results字段，则使用results字段的值
                                if isinstance(step_result, dict):
                                    if "results" in step_result and step_result["results"]:
                                        params[key] = str(step_result["results"][0].get("title", ""))
                                    elif "result" in step_result:
                                        params[key] = str(step_result["result"])
                                    else:
                                        params[key] = str(step_result)
                                else:
                                    params[key] = str(step_result)
                            else:
                                # 如果步骤结果不存在，保留原始值
                                params[key] = value
                    
                    # 验证参数
                    function = getattr(tool, function_name)
                    if hasattr(function, "__annotations__"):
                        required_params = {k: v for k, v in function.__annotations__.items() 
                                        if k != 'return' and k not in params}
                        if required_params:
                            error_msg = f"[RequestID: {request_id}] 缺少必要参数: {', '.join(required_params.keys())}"
                            logger.error(error_msg)
                            results.append({
                                "status": "error",
                                "result": None,
                                "error": error_msg
                            })
                            continue
                    
                    logger.info(f"[RequestID: {request_id}] 调用函数: {tool_name}.{function_name}，参数: {params}")
                    
                    # 调用函数
                    result = function(**params)
                    
                    # 如果是协程，等待执行
                    if hasattr(result, "__await__"):
                        result = await result
                    
                    logger.info(f"[RequestID: {request_id}] 函数调用成功，结果: {result}")
                    
                    # 存储步骤结果
                    step_results[i + 1] = result
                    
                    # 检查结果状态
                    if isinstance(result, dict):
                        if result.get("status") == "error":
                            results.append({
                                "status": "error",
                                "result": None,
                                "error": result.get("error", "未知错误")
                            })
                            continue
                        elif result.get("status") == "success":
                            results.append({
                                "status": "success",
                                "result": result.get("results") if "results" in result else result.get("result"),
                                "error": None
                            })
                            continue
                    
                    results.append({
                        "status": "success",
                        "result": result,
                        "error": None
                    })
                    
                except Exception as e:
                    error_msg = f"[RequestID: {request_id}] 执行工具 {tool_name}.{function_name} 失败: {str(e)}"
                    logger.error(error_msg)
                    results.append({
                        "status": "error",
                        "result": None,
                        "error": error_msg
                    })
            
            logger.info(f"[RequestID: {request_id}] 当前act_step 步骤执行完成，结果: {results}")
            
            # 检查是否有任何步骤失败
            for result in results:
                if result.get("status") == "error":
                    return {
                        "status": "error",
                        "result": results,
                        "error": result.get("error")
                    }
            
            # 如果所有步骤都成功
            if len(results) == 1:
                return results[0]
            else:
                return {
                    "status": "success",
                    "result": results,
                    "error": None
                }
            
        except Exception as e:
            error_msg = f"执行步骤失败: {str(e)}"
            logger.error(f"[RequestID: {request_id}] {error_msg}")
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
                logger.error(f"解析步骤失败: result_str 不是字符串: {result_str}")
                return []
            
            # 尝试解析JSON
            try:
                steps = json.loads(result_str)
            except json.JSONDecodeError:
                logger.error(f"解析步骤失败: 无法解析JSON: {result_str}")
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
            logger.error(f"解析步骤失败: {str(e)}")
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
    