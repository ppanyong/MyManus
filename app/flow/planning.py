from typing import Dict, Any, List
import os
from jinja2 import Template
from .base import BaseFlow

class PlanningFlow(BaseFlow):
    """规划流程实现，负责将用户任务分解为具体的执行步骤"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.prompt_template = self._load_prompt_template()
        
    def initialize(self):
        """初始化规划流程"""
        try:
            # 初始化必要的资源
            self._load_prompt_template()
            return {
                "status": "success",
                "result": "规划流程初始化成功",
                "error": None
            }
        except Exception as e:
            error_msg = f"规划流程初始化失败: {str(e)}"
            print(error_msg)
            return {
                "status": "error",
                "result": None,
                "error": error_msg
            }
        
    def execute(self, task: str) -> Dict[str, Any]:
        """
        执行规划流程，将用户任务分解为具体步骤
        
        Args:
            task: 用户任务描述
            
        Returns:
            Dict[str, Any]: 包含执行计划的字典
        """
        print(f"开始规划任务: {task}")
        try:
            # 构建提示信息
            context = {
                "task": task,
                "max_steps": 20  # 限制最大步骤数
            }
            prompt = self.prompt_template.render(**context)
            
            # 调用大模型生成计划
            response = self._call_llm(prompt)
            
            if response.get("status") == "success":
                # 解析计划步骤
                plan = response.get("result", {})
                steps = []
                
                # 确保返回的计划包含必要的步骤信息
                if isinstance(plan, dict) and "steps" in plan:
                    steps = [
                        {
                            "task": step,
                            "completed": False,
                            "result": None
                        } 
                        for step in plan["steps"][:20]  # 限制最大步骤数
                    ]
                
                return {
                    "status": "success",
                    "tasks": steps,
                    "error": None,
                    "original_task": task
                }
            else:
                return {
                    "status": "error",
                    "tasks": [],
                    "error": response.get("error", "规划失败"),
                    "original_task": task
                }
            
        except Exception as e:
            error_msg = f"规划流程失败: {str(e)}"
            print(error_msg)
            return {
                "status": "error",
                "tasks": [],
                "error": error_msg,
                "original_task": task
            }
    
    def _load_prompt_template(self) -> Template:
        """加载提示模板"""
        template_path = os.path.join("prompt", "planning.jinja")
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                return Template(f.read())
        except Exception as e:
            print(f"加载提示模板失败: {str(e)}")
            return Template("{{ task }}")