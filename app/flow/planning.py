from typing import Dict, Any, List, Optional, Tuple
import os
from jinja2 import Template
from .base import BaseFlow
from app.tool.logger_tool import LoggerTool

# 初始化日志工具
logger_tool = LoggerTool()
logger = logger_tool.get_logger("PlanningFlow")

class PlanningFlow(BaseFlow):
    """规划流程实现，负责将用户任务分解为具体的执行步骤"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.prompt_template = self._load_prompt_template()
        self.step_results = {}  # 存储步骤执行结果
        logger.info(f"初始化PlanningFlow，配置: {config}")
        
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
        
    def execute(self, task: str, tools: List[Dict[str, Any]] = None, request_id: str = None) -> Dict[str, Any]:
        """执行规划流程
        Args:
            task: 任务描述
            tools: 可选，工具列表
            request_id: 请求ID
        """
        try:
            # 构建提示信息，在这一步就加入tools的信息
            context = {
                "task": task,
                "tools": tools or [],
                "max_steps": 20,
                "request_id": request_id,
                "base_dir": self.config.get("workspace", {}).get("base_dir", "")
            }
            
            # 渲染提示模板
            prompt = self.prompt_template.render(**context)
            
            # 记录提示信息
            logger.info(f"[RequestID: {request_id}] 规划提示: {prompt}")
            
            # 调用基类的 execute 方法
            response = super().execute(prompt, tools)
            logger.info(f"[RequestID: {request_id}] 规划结果: {response}")
            
            if response.get("status") == "success":
                try:
                    content = response.get("result", {})
                    # 解析 JSON 格式的步骤
                    steps = super()._parse_steps(content)
                    
                    # 分析步骤依赖关系
                    self._analyze_dependencies(steps)
                    
                    return {
                        "status": "success",
                        "result": steps,
                        "error": None
                    }
                except Exception as e:
                    error_msg = f"解析规划步骤失败: {str(e)}"
                    logger.error(f"[RequestID: {request_id}] {error_msg}")
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
            logger.error(f"[RequestID: {request_id}] {error_msg}")
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
    
    def _analyze_dependencies(self, steps: List[Dict[str, Any]]) -> None:
        """分析步骤间的依赖关系
        
        Args:
            steps: 步骤列表
        """
        try:
            # 创建依赖图
            dependency_graph = {}
            
            for step in steps:
                step_id = step.get("step_id")
                dependencies = step.get("dependencies", [])
                
                # 解析依赖关系
                for dep in dependencies:
                    if dep.startswith("step_"):
                        dep_step_id = int(dep.split("_")[1])
                        if dep_step_id not in dependency_graph:
                            dependency_graph[dep_step_id] = []
                        dependency_graph[dep_step_id].append(step_id)
            
            # 存储依赖关系
            self.dependency_graph = dependency_graph
            logger.info(f"分析完成依赖关系图: {dependency_graph}")
            
        except Exception as e:
            logger.error(f"分析依赖关系失败: {str(e)}")
            self.dependency_graph = {}
    
    def get_step_dependencies(self, step_id: int) -> List[int]:
        """获取指定步骤的依赖步骤
        
        Args:
            step_id: 步骤ID
            
        Returns:
            List[int]: 依赖的步骤ID列表
        """
        return self.dependency_graph.get(step_id, [])
    
    def update_step_result(self, step_id: int, result: Any) -> None:
        """更新步骤执行结果
        
        Args:
            step_id: 步骤ID
            result: 执行结果
        """
        self.step_results[step_id] = result
        logger.info(f"更新步骤 {step_id} 的执行结果")
    
    def get_step_result(self, step_id: int) -> Any:
        """获取步骤执行结果
        
        Args:
            step_id: 步骤ID
            
        Returns:
            Any: 执行结果
        """
        return self.step_results.get(step_id) 