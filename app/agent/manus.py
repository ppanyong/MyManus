from typing import Dict, Any, List
import os
from jinja2 import Template
from .base import ToolCallAgent
from ..flow.planning import PlanningFlow
from flask_socketio import emit, SocketIO
import asyncio

class ManusAgent(ToolCallAgent):
    """主智能体实现"""
    
    def __init__(self, config: Dict[str, Any], socketio: SocketIO = None):
        super().__init__(config)
        self.socketio = socketio
        self.prompt_template = self._load_prompt_template()
        self.planning_flow = PlanningFlow(config)
        self.memory = []  # 用于存储执行结果
        self.current_task_index = 0
        self.tools = []
        
    def initialize(self):
        """初始化主智能体"""
        # TODO: 实现初始化逻辑
        pass
        
    def _update_task_list(self, tasks: List[Dict[str, Any]]) -> None:
        """更新任务列表"""
        if not self.socketio:
            print("警告: socketio 未初始化，无法发送任务更新")
            return
            
        try:
            # 通过socketio发送任务列表更新事件
            self.socketio.emit('update_tasks', {
                'tasks': tasks
            }, namespace='/manus', broadcast=True)
        except Exception as e:
            print(f"更新任务列表失败: {str(e)}")

    async def execute(self, task: str) -> Dict[str, Any]:
        """异步执行任务，使用模板处理"""
        try:
            # 1. 生成任务计划
            plan = self._generate_task_plan(task, self.tools)
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
            
            # 3. 初始化任务列表
            tasks = [{"description": step, "completed": False} for step in steps]
            self.current_task_index = 0
            
            # 4. 返回初始状态
            response = {
                "status": "success",
                "result": "任务计划已生成，开始执行",
                "tasks": tasks,
                "logs": [{
                    "type": "info",
                    "message": "任务计划已生成，共 {} 个步骤".format(len(steps))
                }]
            }
            
            # 5. 开始异步执行任务链
            await self._execute_task_chain(steps, tasks)
            
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
    
    async def _execute_task_chain(self, steps: List[str], tasks: List[Dict[str, Any]]):
        """异步执行任务链"""
        for i, step in enumerate(steps):
            try:
                # 更新当前任务索引
                self.current_task_index = i
                
                # 将当前步骤对应的工具添加到规划流程中
                self.planning_flow.add_tools(self.tools)
                
                # 异步执行单个步骤
                step_result = await asyncio.to_thread(self.planning_flow.execute, step)
                
                # 更新任务状态和结果
                if step_result.get("status") == "success":
                    tasks[i].update({
                        "result": step_result.get("result"),
                        "task_info": step_result.get("task_info"),
                        "completed": True
                    })
                    
                    # 将结果添加到上下文
                    self.add_memory({
                        "type": "step_result",
                        "step": i + 1,
                        "task": step,
                        "result": step_result.get("result"),
                        "task_info": step_result.get("task_info")
                    })
                
                # 存储执行结果
                self.memory.append({
                    "step": i + 1,
                    "task": step,
                    "result": step_result
                })
                
                # 更新任务列表显示
                self._update_task_list(tasks)
                
                # 添加执行日志
                print({
                    "type": "step",
                    "message": f"步骤 {i+1}: {step}",
                    "status": step_result.get("status"),
                    "result": step_result.get("result")
                })
                
                # 等待一小段时间，让UI有时间更新
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print({
                    "type": "error",
                    "message": f"步骤 {i+1} 执行失败: {str(e)}"
                })
                tasks[i]["completed"] = False
                self._update_task_list(tasks)
                await asyncio.sleep(0.1)
    
    def _generate_task_plan(self, task: str, tools: List[Any]) -> Dict[str, Any]:
        """生成任务计划
        Args:
            task: 任务描述
            tools: 可用工具列表
        """
        try:
            # 获取工具描述
            available_tools = []
            for tool in tools:
                try:
                    tool_desc = tool.get_tool_description()
                    available_tools.append({
                        "function": {
                            "strict": False,
                            "name": tool_desc.get("name", "未知工具"),
                            "description": tool_desc.get("description", "无描述")
                        },
                        "type": "function"
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
                    "tool_count": len(tools),
                    "available_tools": available_tools,
                    "max_steps": 20
                }
            )
            
            # 调用基类的执行方法获取计划，传入工具列表
            return super().execute(prompt, available_tools)
            
        except Exception as e:
            return {
                "status": "error",
                "result": None,
                "error": f"生成任务计划失败: {str(e)}"
            }
    
    def _parse_steps(self, plan_text: Dict[str, Any]) -> List[str]:
        """解析计划文本，提取步骤列表"""
        try:
            # 从 API 响应中提取文本内容
            if isinstance(plan_text, dict):
                # 尝试从不同的响应格式中提取文本
                text = plan_text.get('response', '')  # 对于 Ollama 格式
                if not text:
                    text = plan_text.get('choices', [{}])[0].get('message', {}).get('content', '')  # 对于 OpenAI 格式
                if not text:
                    text = plan_text.get('result', '')  # 对于其他格式
            else:
                text = str(plan_text)
            
            # 解析步骤列表
            steps = [step.strip() for step in text.split('\n') 
                    if step.strip() and not step.startswith('#')]
            
            # 限制最大步骤数
            return steps[:20]
            
        except Exception as e:
            print(f"解析步骤失败: {str(e)}")
            return []
    
    def _load_prompt_template(self) -> Template:
        """加载提示模板"""
        template_path = os.path.join(os.path.dirname(__file__), '..', '..', 'prompt', 'manus.jinja')
        with open(template_path, 'r', encoding='utf-8') as f:
            return Template(f.read())
       