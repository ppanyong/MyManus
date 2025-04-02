from typing import List, Dict, Any
import requests
from abc import ABC, abstractmethod
import time

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
        
    def execute(self, task: str, tools: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行任务
        Args:
            task: 任务描述
            tools: 可选，工具列表
        """
        try:
            # 从配置中获取 API 设置
            api_config = self.config.get('api', {})
            
            # 打印调试信息
            print(f"API配置: {api_config}")
            
            if not api_config.get('url'):
                return {
                    "status": "error",
                    "error": "API URL未配置"
                }
            
            headers = {
                "Authorization": f"Bearer {api_config.get('api_key')}",
                "Content-Type": "application/json"
            }
            
            # 构建请求体
            request_body = {
                "model": api_config.get('model'),
                "prompt": task,
                "stream": api_config.get('stream', False),
                "options": {
                    "temperature": api_config.get('temperature', 0.7),
                    "max_tokens": api_config.get('max_tokens', 4096)
                },
                "messages": [
                    {
                        "content": task,
                        "role": "user"
                    }
                ]
            }
            
            # 如果提供了 tools，添加到请求体中
            if tools:
                request_body["tools"] = tools
            
            # 添加重试机制
            max_retries = 3
            retry_delay = 2  # 秒
            
            for attempt in range(max_retries):
                try:
                    response = requests.post(
                        api_config.get('url'),
                        headers=headers,
                        json=request_body,
                        timeout=30  # 添加超时设置
                    )
                    
                    if response.status_code == 200:
                        return {
                            "status": "success",
                            "result": response.json()
                        }
                    else:
                        print(f"API请求失败 (尝试 {attempt + 1}/{max_retries}): {response.status_code}")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            continue
                        return {
                            "status": "error",
                            "error": f"API请求失败: {response.status_code}"
                        }
                        
                except requests.exceptions.ConnectionError as e:
                    print(f"连接错误 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                    if attempt < max_retries - 1:
                        print(f"等待 {retry_delay} 秒后重试...")
                        time.sleep(retry_delay)
                        continue
                    return {
                        "status": "error",
                        "error": f"无法连接到API服务: {str(e)}"
                    }
                except requests.exceptions.Timeout:
                    print(f"请求超时 (尝试 {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    return {
                        "status": "error",
                        "error": "API请求超时"
                    }
                except Exception as e:
                    print(f"请求异常 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    return {
                        "status": "error",
                        "error": f"API请求异常: {str(e)}"
                    }
                    
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
        
    def add_tool(self, tool: Any):
        """添加工具"""
        self.tools.append(tool)
        
    def get_tools(self) -> List[Any]:
        """获取所有可用工具"""
        return self.tools 