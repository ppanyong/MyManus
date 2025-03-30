from typing import Dict, Any, List
import os
from jinja2 import Template
from .base import ToolCallAgent
from ..flow.planning import PlanningFlow
from .react import ReactAgent

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
        """执行任务"""
        try:
            # 生成执行计划
            response = self.planning_flow.execute(task)
            if response.get("status") == "error":
                return response
                
            steps = response.get("tasks", [])
            if not steps:
                return {
                    "status": "error",
                    "error": "未生成有效的执行步骤"
                }
            # 将执行步骤写入任务记录
            task_steps = []
            for i, step in enumerate(steps):
                task_steps.append({
                    "step_id": i + 1,
                    "description": step["task"],
                    "status": "pending"
                })
                
            response["task_steps"] = task_steps
                
            # 创建ReactAgent链
            prev_agent = None
            first_agent = None
            
            # 为每个步骤创建ReactAgent实例
            for i, step in enumerate(steps):
                current_agent = ReactAgent(
                    task=step["task"],
                    tools=self.tools,
                    step_index=i+1,
                    memory=self.memory
                )
                
                if prev_agent:
                    prev_agent.set_next_agent(current_agent)
                else:
                    first_agent = current_agent
                    
                prev_agent = current_agent
                
            # 执行整个链条
            if first_agent:
                chain_result = first_agent.execute_chain()
                
                # 更新响应信息
                response.update({
                    "status": chain_result.get("status"),
                    "final_result": chain_result.get("result"),
                    "memory": self.memory
                })
                
            return response
            
        except Exception as e:
            error_msg = f"处理任务失败: {str(e)}"
            print(error_msg)
            return {
                "status": "error",
                "error": error_msg
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
       