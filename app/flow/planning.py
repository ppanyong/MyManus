from typing import Dict, Any
import os
from jinja2 import Template
from .base import BaseFlow

class PlanningFlow(BaseFlow):
    """规划流程实现"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.prompt_template = self._load_prompt_template()
        
    def initialize(self):
        """初始化规划流程"""
        # TODO: 实现初始化逻辑
        pass
        
    def execute(self, task: str) -> Dict[str, Any]:
        """执行规划流程，使用模板处理"""
        try:
            # 加载并渲染提示模板
            prompt = self.prompt_template.render(
                task=task,
                context={
                    "flow_type": "planning",
                    "steps": self.get_steps()
                }
            )
            
            # 调用基类的执行方法
            return super().execute(prompt)
            
        except Exception as e:
            error_msg = f"规划流程失败: {str(e)}"
            print(error_msg)
            return {
                "logs": {
                    "status": "error",
                    "result": None,
                    "error": error_msg
                }
            }
            
    def _load_prompt_template(self) -> Template:
        """加载提示模板"""
        template_path = os.path.join("prompt", "planning.jinja")
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                return Template(f.read())
        except Exception as e:
            print(f"加载提示模板失败: {str(e)}")
            # 返回一个基础模板
            return Template("{{ task }}") 