from typing import Dict, Any, List
import os
from jinja2 import Template
from .base import ToolCallAgent
from ..flow.planning import PlanningFlow

class ManusAgent(ToolCallAgent):
    """主智能体实现"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.prompt_template = self._load_prompt_template()
        self.planning_flow = PlanningFlow(config)
        self.memory = []  # 用于存储执行结果
        
    def initialize(self):
        """初始化主智能体"""
        # TODO: 实现初始化逻辑
        pass
        
    def execute(self, task: str) -> Dict[str, Any]:
        """执行任务，使用模板处理"""
        try:
            # 1. 生成任务计划
            plan = self._generate_task_plan(task)
            if not plan.get("status") == "success":
                return {
                    "logs": plan
                }
            
            # 2. 解析计划步骤（最多20步）
            steps = self._parse_steps(plan.get("result", ""))
            if not steps:
                return {
                    "logs": {
                        "status": "error",
                        "result": None,
                        "error": "无法生成有效的任务计划"
                    }
                }
            
            # 3. 返回计划和初始状态
            response = {
                "status": "success",
                "result": "任务计划已生成，开始执行",
                "tasks": [{"description": step, "completed": False} for step in steps],
                "logs": [{
                    "type": "info",
                    "message": "任务计划已生成，共 {} 个步骤".format(len(steps))
                }]
            }
            
            # 4. 逐步执行计划
            for i, step in enumerate(steps):
                try:
                    # 将当前步骤对应的工具添加到规划流程中
                    # 注意:这里假设tools列表中的工具顺序与步骤顺序一致
                    self.planning_flow.add_tools(self.tools)
                    # 执行单个步骤
                    step_result = self.planning_flow.execute(step)
                    # 将单步执行结果回填到上下文中
                    if step_result.get("status") == "success":
                        # 更新当前步骤的执行结果
                        response["tasks"][i].update({
                            "result": step_result.get("result"),
                            "task_info": step_result.get("task_info")
                        })
                        
                        # 将结果添加到上下文
                        self.add_memory({
                            "type": "step_result",
                            "step": i + 1,
                            "task": step,
                            "result": step_result.get("result"),
                            "task_info": step_result.get("task_info")
                        })
                    # 更新任务状态
                    response["tasks"][i]["completed"] = (step_result.get("status") == "success")
                    
                    # 存储执行结果
                    self.memory.append({
                        "step": i + 1,
                        "task": step,
                        "result": step_result
                    })
                    
                    # 添加执行日志
                    response["logs"].append({
                        "type": "step",
                        "message": f"步骤 {i+1}: {step}",
                        "status": step_result.get("status"),
                        "result": step_result.get("result")
                    })
                    
                    # 更新当前任务
                    response["current_task"] = step
                    

                except Exception as e:
                    response["logs"].append({
                        "type": "error",
                        "message": f"步骤 {i+1} 执行失败: {str(e)}"
                    })
            
            #将最终结果通过对话的方式反馈给用户
            print(response)
            return response
            
        except Exception as e:
            error_msg = f"处理任务失败: {str(e)}"
            print(error_msg)
            return {
                "logs": {
                    "status": "error",
                    "result": None,
                    "error": error_msg
                }
            }
    
    def _generate_task_plan(self, task: str) -> Dict[str, Any]:
        """生成任务计划"""
        try:
            # 获取工具描述
            available_tools = []
            for tool in self.tools:
                try:
                    tool_desc = tool.get_tool_description()
                    available_tools.append({
                        "name": tool_desc.get("name", "未知工具"),
                        "description": tool_desc.get("description", "无描述"),
                        "functions": tool_desc.get("functions", []),
                        "type": tool_desc.get("type", "unknown")
                    })
                except Exception as e:
                    print(f"获取工具描述失败: {str(e)}")
                    continue
            
            # 渲染计划生成提示
            prompt = self.prompt_template.render(
                task=task,
                tools=available_tools,
                context={
                    "agent_type": "manus",
                    "tool_count": len(self.tools),
                    "available_tools": available_tools,
                    "max_steps": 20
                }
            )
            
            # 调用基类的执行方法获取计划
            return super().execute(prompt)
            
        except Exception as e:
            return {
                "status": "error",
                "result": None,
                "error": f"生成任务计划失败: {str(e)}"
            }
    
    def _parse_steps(self, plan_text: str) -> List[str]:
        """解析计划文本，提取步骤列表"""
        try:
            # 这里需要根据实际的模型输出格式进行解析
            # 假设模型输出的是换行分隔的步骤列表
            steps = [step.strip() for step in plan_text.split('\n') 
                    if step.strip() and not step.startswith('#')]
            
            # 限制最大步骤数
            return steps[:20]
            
        except Exception as e:
            print(f"解析步骤失败: {str(e)}")
            return []
    
    def _load_prompt_template(self) -> Template:
        """加载提示模板"""
        template_path = os.path.join("prompt", "manus.jinja")
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                return Template(f.read())
        except Exception as e:
            print(f"加载提示模板失败: {str(e)}")
            return Template("{{ task }}")
       