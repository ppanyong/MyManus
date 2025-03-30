from typing import List, Dict, Any
import requests
from abc import ABC, abstractmethod

class ToolCallAgent(ABC):
    """基础智能体框架"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.tools = []
        self.memory = []  # 用于存储任务执行上下文
        self.state = {
            "status": "idle",  # 当前状态: idle/busy/error
            "current_task": None,  # 当前执行的任务
            "last_error": None,  # 最近一次错误信息
            "last_result": None  # 最近一次执行结果
        }
    
        
    @abstractmethod
    def initialize(self):
        """初始化智能体"""
        pass
        
    def add_memory(self, memory_item: Dict[str, Any]):
        """添加记忆项
        
        Args:
            memory_item: 需要记录的记忆项,包含任务信息、执行结果等
        """
        self.memory.append(memory_item)
        
    def get_memory(self) -> List[Dict[str, Any]]:
        """获取所有历史记忆"""
        return self.memory
        
    def update_state(self, status: str, task: str = None, error: str = None, result: Any = None):
        """更新智能体状态
        
        Args:
            status: 状态标识
            task: 当前任务
            error: 错误信息
            result: 执行结果
        """
        self.state.update({
            "status": status,
            "current_task": task,
            "last_error": error,
            "last_result": result
        })
        
    def get_state(self) -> Dict[str, Any]:
        """获取当前状态"""
        return self.state
        
    def execute(self, task: str) -> Dict[str, Any]:
        """执行任务的基础方法"""
        try:
            # 调用本地Ollama服务
            print(f"执行任务: {task}")
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "qwen2.5-coder:14b",
                    "prompt": task,
                    "stream": False,
                    "options": {
                        "temperature": 0.0,
                        "max_tokens": 4096
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")
                print(f"模型响应: {response_text}")
                return {
                    "status": "success", 
                    "result": response_text,
                    "error": None
                }
            else:
                error_msg = f"调用模型失败: {response.status_code}"
                print(error_msg)
                return {
                    "logs": {
                        "status": "error",
                        "result": None, 
                        "error": error_msg
                    }
                }
        except Exception as e:
            error_msg = f"执行任务出错: {str(e)}"
            print(error_msg)
            return {
                "logs": {
                    "status": "error",
                    "result": None,
                    "error": error_msg
                }
            }
        
    def add_tool(self, tool: Any):
        """添加工具"""
        self.tools.append(tool)
        
    def get_tools(self) -> List[Any]:
        """获取所有可用工具"""
        return self.tools 

    def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """调用大语言模型"""
        try:
            # 调用本地Ollama服务
            print(f"发送提示词到LLM: {prompt}")
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "qwen2.5-coder:14b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.0,
                        "max_tokens": 4096
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")
                print(f"LLM响应: {response_text}")
                
                # 解析响应文本中的JSON
                parsed_response = self._parse_llm_response(response_text)
                
                # 格式化为对话消息
                message = self._format_response_message(parsed_response)
                print(f"对话响应: {message}")
                
                # 在返回结果中添加对话消息
                parsed_response["message"] = message
                return parsed_response
                
            else:
                error_msg = f"调用模型失败: {response.status_code}"
                print(error_msg)
                return {
                    "status": "error",
                    "result": None,
                    "error": error_msg,
                    "message": f"抱歉，调用服务时出现错误：{error_msg}"
                }
                
        except Exception as e:
            error_msg = f"调用LLM出错: {str(e)}"
            print(error_msg)
            return {
                "status": "error",
                "result": None,
                "error": error_msg,
                "message": f"抱歉，服务出现异常：{error_msg}"
            }
            
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """解析LLM响应文本中的JSON数据"""
        try:
            # 使用正则表达式查找JSON内容
            import re
            json_pattern = r'\{(?:[^{}]|(?R))*\}'
            matches = re.finditer(json_pattern, response_text)
            
            # 获取最后一个匹配的JSON（通常是最完整的）
            json_str = None
            for match in matches:
                json_str = match.group()
                
            if json_str:
                import json
                return json.loads(json_str)
            
            return {
                "status": "error",
                "result": response_text,
                "error": "未找到有效的JSON数据"
            }
            
        except Exception as e:
            print(f"JSON解析失败: {str(e)}")
            return {
                "status": "error",
                "result": response_text,
                "error": "JSON解析失败"
            }
            
    def _format_response_message(self, response: Dict[str, Any]) -> str:
        """格式化响应消息"""
        if response.get("status") == "error":
            return f"抱歉，执行过程中遇到了问题：{response.get('error')}"
            
        tool_info = response.get("result", {})
        if isinstance(tool_info, dict):
            tool_name = tool_info.get("tool")
            function_name = tool_info.get("function")
            parameters = tool_info.get("parameters", {})
            
            message = f"我理解了您的需求，我会使用 {tool_name} 工具的 {function_name} 功能来完成任务。"
            if parameters:
                message += f"\n使用的参数是：{parameters}"
            return message
        
        return f"收到的响应：{tool_info}" 