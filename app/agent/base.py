from typing import List, Dict, Any
import requests
from abc import ABC, abstractmethod

class ToolCallAgent(ABC):
    """基础智能体框架"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.tools = []
        
    @abstractmethod
    def initialize(self):
        """初始化智能体"""
        pass
        
    def execute(self, task: str) -> Dict[str, Any]:
        """执行任务的基础方法"""
        try:
            # 调用本地Ollama服务
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