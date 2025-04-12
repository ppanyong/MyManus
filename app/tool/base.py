from typing import Dict, Any
from abc import ABC, abstractmethod

class BaseTool(ABC):
    """工具基类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化工具
        
        Args:
            config: 工具配置
        """
        self.config = config or {}
    
    @abstractmethod
    def get_tool_description(self) -> Dict[str, Any]:
        """
        获取工具描述
        
        Returns:
            Dict[str, Any]: 工具描述
        """
        pass 