import json
from typing import Dict, Any, List
import os
from jinja2 import Template
from .base import ToolCallAgent
from ..flow.planning import PlanningFlow
from ..flow.react import ReactFlow
from flask_socketio import SocketIO
import asyncio
import ast

class ManusAgent(ToolCallAgent):
    """主智能体实现，负责任务规划和执行"""
    
    def __init__(self, config: Dict[str, Any], socketio: SocketIO = None):
        """
        初始化主智能体
        
        Args:
            config: 配置信息
            socketio: SocketIO实例，用于实时更新UI
        """
        super().__init__(config)
        self.socketio = socketio
        self.prompt_template = self._load_prompt_template()
        self.planning_flow = PlanningFlow(config)
        #self.react_flow = ReactFlow(config)
        self.memory = []  # 用于存储执行结果
        self.current_task_index = 0
        self.tools = []
        
    def initialize(self) -> Dict[str, Any]:
        """初始化主智能体"""
        try:
            # 初始化规划流程
            init_result = self.planning_flow.initialize()
            if init_result.get("status") == "error":
                return init_result
                
            # 不再初始化 react_flow，因为它会在需要时创建
            # react_init_result = self.react_flow.initialize()
            # if react_init_result.get("status") == "error":
            #     return react_init_result
                
            return {
                "status": "success",
                "result": "主智能体初始化成功",
                "error": None
            }
        except Exception as e:
            error_msg = f"主智能体初始化失败: {str(e)}"
            print(error_msg)
            return {
                "status": "error",
                "result": None,
                "error": error_msg
            }
        
    def _update_task_list(self, tasks: List[Dict[str, Any]]) -> None:
        """
        更新任务列表到UI
        
        Args:
            tasks: 任务列表
        """
        if not self.socketio:
            print("警告: socketio 未初始化，无法发送任务更新")
            return
        if not tasks:
            print("警告: 任务列表为空，无法发送任务更新")
            return
        try:
            # 通过socketio发送任务列表更新事件
            self.socketio.emit('update_tasks_ui', { 
                'tasks': tasks
            }, namespace='/manus')
        except Exception as e:
            print(f"更新任务列表失败: {str(e)}")
            
    def _append_system_message(self, message: str) -> None:
        """
        追加系统消息到对话
        
        Args:
            message: 系统消息内容
        """
        if not self.socketio:
            print("警告: socketio 未初始化，无法发送系统消息")
            return
            
        try:
            # 同时发送到UI
            self.socketio.emit('append_system_message_ui', {
                'message': message
            }, namespace='/manus')
        except Exception as e:
            print(f"发送系统消息失败: {str(e)}")

    async def execute(self, user_request: str) -> Dict[str, Any]:
        """
        异步执行任务，使用模板处理
        
        Args:
            task: 用户任务描述
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
            # 1. 生成任务计划
            plan = self._generate_task_plan(user_request)
            if not plan.get("status") == "success":
                return {
                    "logs": plan
                }
            
            # 2. 解析计划步骤（最多20步）
            result_str = plan.get("result", "[]")
            try:
                # 尝试将字符串转换为 Python 对象
                tasks = json.loads(result_str)
            except json.JSONDecodeError:
                # 如果解析失败，尝试使用更宽松的方式

                try:
                    # 使用 ast.literal_eval 解析 Python 字面量
                    tasks = ast.literal_eval(result_str)
                except (SyntaxError, ValueError):
                    # 如果仍然失败，返回空列表
                    tasks = []
                    print(f"无法解析任务计划: {result_str}")
            
            if not tasks:
                return {
                    "logs": {
                        "status": "error",
                        "result": None,
                        "error": "无法生成有效的任务计划"
                    }
                }
            
            # 将计划显示到页面
            if self.socketio:
                self.socketio.emit('update_plan_ui', {
                    'plan': tasks
                }, namespace='/manus')
            else:
                print("警告: socketio 未初始化，无法发送计划更新")
            
            # 3. 初始化任务列表
            
            self.current_task_index = 0
            
            # 4. 返回初始状态
            response = {
                "status": "success",
                "result": "任务计划已生成，开始执行",
                "tasks": tasks,
                "logs": [{
                    "type": "info",
                    "message": "任务计划已生成，共 {} 个步骤".format(len(tasks))
                }]
            }
            
            # 发送系统消息
            self._append_system_message(f"系统: 已收到您的请求，正在生成任务计划...")
            self._append_system_message(f"系统: 任务计划已生成，共 {len(tasks)} 个步骤，开始执行...")
            
            # 5. 开始异步执行任务链
            await self._execute_task_chain(tasks)
            
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
    
    async def _execute_task_chain(self, tasks: List[Dict[str, Any]]):
        """
        异步执行任务链，使ReactFlow实例头尾相连
        
        Args:
            tasks: 任务列表
        """
        # 创建一个共享的ReactFlow实例
        react_flow = ReactFlow(self.config)
        react_flow.memory = []  # 明确初始化内存
        
        # 初始化 ReactFlow
        init_result = react_flow.initialize()
        if init_result.get("status") != "success":
            self._append_system_message(f"系统: ReactFlow 初始化失败: {init_result.get('error')}")
            return
            
        self._append_system_message("系统: ReactFlow 初始化成功，开始执行任务链...")
        
        # 用于存储前一个任务的结果
        previous_result = None
        
        for i, task in enumerate(tasks):
            try:
                # 更新当前任务索引
                self.current_task_index = i
                
                # 如果有前一个任务的结果，将其添加到当前任务的上下文中
                if previous_result and previous_result.get("status") == "success":
                    # 将前一个任务的结果添加到当前任务的上下文中
                    if "context" not in task:
                        task["context"] = {}
                    
                    # 添加前一个任务的结果到上下文
                    task["context"]["previous_result"] = previous_result.get("result")
                    task["context"]["previous_task_info"] = previous_result.get("task_info")
                    
                    # 打印详细的过程执行信息
                    self._append_system_message(f"系统: 步骤 {i+1} 将使用前一个步骤的结果作为上下文")
                
                # 使用 ReactFlow 执行任务
                self._append_system_message(f"系统: 开始执行步骤 {i+1}: {task.get('description', '未知任务')}")
                
                # 使用异步线程执行任务
                step_result = await asyncio.to_thread(react_flow.execute, task, self.tools)
                
                # 只存储必要的信息，避免循环引用
                result_copy = {
                    "status": step_result.get("status"),
                    "result": step_result.get("result"),
                    "error": step_result.get("error")
                }
                
                # 更新任务状态和结果
                if step_result.get("status") == "success":
                    tasks[i].update({
                        "result": result_copy.get("result"),
                        "task_info": step_result.get("task_info"),
                        "completed": True
                    })
                    
                    # 将结果添加到上下文，避免存储整个对象
                    self.add_memory({
                        "type": "step_result",
                        "step": i + 1,
                        "task": task,
                        "result": result_copy.get("result"),
                        "task_info": step_result.get("task_info")
                    })
                    
                    # 打印详细的结果信息
                    self._append_system_message(f"系统: 步骤 {i+1} 执行成功")
                    if step_result.get("result"):
                        self._append_system_message(f"系统: 步骤 {i+1} 结果: {json.dumps(step_result.get('result'), ensure_ascii=False)}")
                else:
                    tasks[i].update({
                        "completed": False,
                        "error": step_result.get("error")
                    })
                    
                    # 打印错误信息
                    self._append_system_message(f"系统: 步骤 {i+1} 执行失败: {step_result.get('error')}")
                
                # 存储执行结果，避免存储整个对象
                self.memory.append({
                    "step": i + 1,
                    "task": task,
                    "result": result_copy
                })
                
                # 添加执行日志
                print({
                    "type": "step",
                    "message": f"步骤 {i+1}: {task}",
                    "status": step_result.get("status"),
                    "result": step_result.get("result")
                })
                
                # 保存当前任务的结果，用于下一个任务
                previous_result = step_result
                
                # 等待一小段时间，让UI有时间更新
                await asyncio.sleep(1)
                
            except Exception as e:
                error_msg = f"步骤 {i+1} 执行失败: {str(e)}"
                print({
                    "type": "error",
                    "message": error_msg
                })
                
                tasks[i].update({
                    "completed": False,
                    "error": error_msg
                })
                
                self._append_system_message(f"系统: {error_msg}")
                self._update_task_list(tasks)
                
                # 即使出错，也等待一小段时间
                await asyncio.sleep(1)
                
        # 所有任务执行完成
        self._append_system_message("系统: 所有任务执行完成！")
        
        # 清理 ReactFlow 实例
        del react_flow
    
    def _generate_task_plan(self, task: str) -> Dict[str, Any]:
        """
        生成任务计划
        
        Args:
            task: 任务描述
            
        Returns:
            Dict[str, Any]: 计划生成结果
        """
        try:
            # 获取工具描述
            available_tools = []
            for tool in self.tools:
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
            
            # 调用规划流程生成计划
            return self.planning_flow.execute(task, available_tools)
            
        except Exception as e:
            return {
                "status": "error",
                "result": None,
                "error": f"生成任务计划失败: {str(e)}"
            }
    
    def _load_prompt_template(self) -> Template:
        """
        加载提示模板
        
        Returns:
            Template: Jinja2模板
        """
        template_path = os.path.join(os.path.dirname(__file__), '..', '..', 'prompt', 'manus.jinja')
        with open(template_path, 'r', encoding='utf-8') as f:
            return Template(f.read())
            
    def add_tool(self, tool: Any) -> None:
        """
        添加工具
        
        Args:
            tool: 工具实例
        """
        self.tools.append(tool)
        
    def add_memory(self, memory_item: Dict[str, Any]) -> None:
        """
        添加记忆
        
        Args:
            memory_item: 记忆项
        """
        self.memory.append(memory_item)
       