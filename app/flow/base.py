from typing import Dict, Any, List
from abc import ABC, abstractmethod

class BaseFlow(ABC):
    """基础流程框架"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.steps = []
        
    @abstractmethod
    def initialize(self):
        """初始化流程"""
        pass
        
    @abstractmethod
    def execute(self) -> Dict[str, Any]:
        """执行流程"""
        pass
        
    def add_step(self, step: Dict[str, Any]):
        """添加流程步骤"""
        self.steps.append(step)
        
    def get_steps(self) -> List[Dict[str, Any]]:
        """获取所有流程步骤"""
        return self.steps 