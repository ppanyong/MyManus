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