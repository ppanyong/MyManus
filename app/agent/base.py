"""
基础智能体框架
版本: 1.0.0
作者: MyManus
最后更新: 2024-03-21

本模块提供了一个基础智能体框架，支持工具调用、状态管理和错误处理。
主要功能包括：
1. 任务执行和状态跟踪
2. 工具管理和调用
3. 记忆存储和检索
4. 错误处理和重试机制
"""

from typing import List, Dict, Any
import requests
from abc import ABC, abstractmethod
import time
from ..tool.logger_tool import LoggerTool

# 初始化日志工具
logger_tool = LoggerTool()
logger = logger_tool.get_logger(__name__)

class ToolCallAgent(ABC):
    """基础智能体框架
    
    这是一个抽象基类，定义了智能体的基本行为和接口。
    子类需要实现initialize方法来初始化特定的智能体。
    
    状态说明：
    - idle: 空闲状态，可以接受新任务
    - busy: 正在执行任务
    - error: 发生错误，需要处理
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化智能体
        
        Args:
            config: 配置字典，包含API设置和其他必要参数
        """
        self.config = config
        self.tools = []  # 存储可用的工具列表
        self.memory = []  # 用于存储任务执行上下文
        self.state = {
            "status": "idle",  # 当前状态: idle/busy/error
            "current_task": None,  # 当前执行的任务
            "last_error": None,  # 最近一次错误信息
            "last_result": None  # 最近一次执行结果
        }
        logger.info("智能体初始化完成，配置信息: %s", config)
    
    @abstractmethod
    def initialize(self):
        """初始化智能体
        
        这是一个抽象方法，子类必须实现。
        用于执行特定智能体所需的初始化操作。
        """
        pass
        
    def add_memory(self, memory_item: Dict[str, Any]):
        """添加记忆项
        
        Args:
            memory_item: 需要记录的记忆项，包含任务信息、执行结果等
        """
        self.memory.append(memory_item)
        logger.debug("添加新的记忆项: %s", memory_item)
        
    def get_memory(self) -> List[Dict[str, Any]]:
        """获取所有历史记忆
        
        Returns:
            包含所有历史记忆的列表
        """
        logger.debug("获取历史记忆，当前记忆数量: %d", len(self.memory))
        return self.memory
        
    def update_state(self, status: str, task: str = None, error: str = None, result: Any = None):
        """更新智能体状态
        
        Args:
            status: 状态标识 (idle/busy/error)
            task: 当前任务描述
            error: 错误信息
            result: 执行结果
            
        状态更新会触发日志记录，便于调试和监控。
        """
        old_status = self.state["status"]
        self.state.update({
            "status": status,
            "current_task": task,
            "last_error": error,
            "last_result": result
        })
        logger.info("状态更新: %s -> %s, 当前任务: %s", old_status, status, task)
        if error:
            logger.error("发生错误: %s", error)
        
    def get_state(self) -> Dict[str, Any]:
        """获取当前状态
        
        Returns:
            包含当前状态信息的字典
        """
        logger.debug("获取当前状态: %s", self.state)
        return self.state
        
    def execute(self, task: str, tools: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行任务
        
        执行任务的主要方法，包含完整的错误处理和重试机制。
        
        Args:
            task: 任务描述
            tools: 可选，工具列表
            
        Returns:
            包含执行结果的字典，格式为:
            {
                "status": "success/error",
                "result": 执行结果,
                "error": 错误信息（如果有）
            }
            
        错误处理：
        1. 配置错误：检查API配置是否完整
        2. 网络错误：自动重试最多3次
        3. 超时错误：30秒超时限制
        4. 其他异常：记录并返回错误信息
        """
        logger.info("开始执行任务: %s", task)
        try:
            # 从配置中获取 API 设置
            api_config = self.config.get('api', {})
            
            # 记录调试信息
            logger.debug("API配置: %s", api_config)
            
            if not api_config.get('url'):
                logger.error("API URL未配置")
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
                logger.debug("添加工具到请求: %s", tools)
            
            # 添加重试机制
            max_retries = 3
            retry_delay = 2  # 秒
            
            for attempt in range(max_retries):
                try:
                    logger.info("开始执行任务 (尝试 %d/%d)", attempt + 1, max_retries)
                    response = requests.post(
                        api_config.get('url'),
                        headers=headers,
                        json=request_body,
                        timeout=30  # 添加超时设置
                    )
                    
                    if response.status_code == 200:
                        logger.info("任务执行成功")
                        return {
                            "status": "success",
                            "result": response.json()
                        }
                    else:
                        logger.warning("API请求失败 (尝试 %d/%d): %d", attempt + 1, max_retries, response.status_code)
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            continue
                        return {
                            "status": "error",
                            "error": f"API请求失败: {response.status_code}"
                        }
                        
                except requests.exceptions.ConnectionError as e:
                    logger.error("连接错误 (尝试 %d/%d): %s", attempt + 1, max_retries, str(e))
                    if attempt < max_retries - 1:
                        logger.info("等待 %d 秒后重试...", retry_delay)
                        time.sleep(retry_delay)
                        continue
                    return {
                        "status": "error",
                        "error": f"无法连接到API服务: {str(e)}"
                    }
                except requests.exceptions.Timeout:
                    logger.error("请求超时 (尝试 %d/%d)", attempt + 1, max_retries)
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    return {
                        "status": "error",
                        "error": "API请求超时"
                    }
                except Exception as e:
                    logger.error("请求异常 (尝试 %d/%d): %s", attempt + 1, max_retries, str(e))
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    return {
                        "status": "error",
                        "error": f"API请求异常: {str(e)}"
                    }
                    
        except Exception as e:
            logger.error("执行任务时发生异常: %s", str(e))
            return {
                "status": "error",
                "error": str(e)
            }
        
    def add_tool(self, tool: Any):
        """添加工具
        
        Args:
            tool: 要添加的工具对象
        """
        self.tools.append(tool)
        logger.info("添加新工具: %s", tool)
        
    def get_tools(self) -> List[Any]:
        """获取所有可用工具
        
        Returns:
            工具列表
        """
        logger.debug("获取工具列表，当前工具数量: %d", len(self.tools))
        return self.tools 

    