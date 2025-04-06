from typing import Dict, Any, List, Optional, Tuple
import os
from jinja2 import Template
from .base import BaseFlow
import logging

# 配置日志记录器
logger = logging.getLogger(__name__)

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
            logger.error(error_msg)
            return {
                "status": "error",
                "result": None,
                "error": error_msg
            }
        
    def execute(self, task: str, tools: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行规划流程
        Args:
            task: 任务描述
            tools: 可选，工具列表，格式为:
                [
                    {
                        "function": {
                            "strict": False,
                            "name": "工具名称",
                            "description": "工具描述"
                        },
                        "type": "function"
                    }
                ]
        """
        try:
            # 构建提示信息，在这一步就加入tools的信息
            context = {
                "task": task,
                "tools": tools or [],
                "max_steps": 20
            }
            
            # 渲染提示模板
            prompt = self.prompt_template.render(**context)
            
            # 打印并记录提示信息
            print(f"规划提示: {prompt}")
            logger.info(f"规划提示: {prompt}")
            
            # 调用基类的 execute 方法
            response = super().execute(prompt, tools)
            logger.info(f"规划结果: {response}")
            if response.get("status") == "success":
                try:
                    content = response.get("result", {})
                    # 解析 JSON 格式的步骤
                    steps = super()._parse_steps(content)
                    return {
                        "status": "success",
                        "result": steps,
                        "error": None
                    }
                except Exception as e:
                    error_msg = f"解析规划步骤失败: {str(e)}"
                    logger.error(error_msg)
                    return {
                        "status": "error",
                        "result": None,
                        "error": error_msg
                    }
            else:
                return {
                    "status": "error",
                    "result": None,
                    "error": response.get("error", "未知错误")
                }
                    
        except Exception as e:
            error_msg = f"规划流程失败: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "result": None,
                "error": str(e)
            }
    
    def _load_prompt_template(self) -> Template:
        """加载提示模板"""
        template_path = os.path.join("prompt", "planning.jinja")
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                return Template(f.read())
        except Exception as e:
            logger.error(f"加载提示模板失败: {str(e)}")
            return Template("{{ task }}") 