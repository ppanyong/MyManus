import json
from typing import Dict, Any, List
import os
from jinja2 import Template
from .base import ToolCallAgent
from ..flow.planning import PlanningFlow
from ..flow.react import ReactFlow
import asyncio
import ast

class ManusAgent(ToolCallAgent):
    """主智能体实现，负责任务规划和执行"""
    
    def __init__(self, config: Dict[str, Any], ui=None):
        """
        初始化主智能体
        
        Args:
            config: 配置信息
            ui: UI实例，用于实时更新UI
        """
        super().__init__(config)
        self.ui = ui
        self.prompt_template = self._load_prompt_template()
        self.planning_flow = PlanningFlow(config)
        self.react_flow = ReactFlow(config)
        self.memory = []  # 用于存储执行结果
        self.current_task_index = 0
        self.tools = []
        
    def initialize(self) -> Dict[str, Any]:
        """初始化主智能体"""
        try:
            # 使用planning_flow初始化 
            init_result = self.planning_flow.initialize()
            if init_result.get("status") == "error":
                return init_result
                
            # 初始化react_flow
            react_init_result = self.react_flow.initialize()
            if react_init_result.get("status") == "error":
                return react_init_result
                
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
        if not self.ui:
            print("警告: UI 未初始化，无法发送任务更新")
            return
        if not tasks:
            print("警告: 任务列表为空，无法发送任务更新")
            return
        try:
            # 通过UI实例发送任务列表更新
            self.ui.update_tasks_ui(tasks)
        except Exception as e:
            print(f"调用UI的update_tasks_ui方法，更新任务列表失败，原因是: {str(e)}")
            
    def _append_system_message(self, message: str) -> None:
        """
        追加系统消息到对话
        
        Args:
            message: 系统消息内容
        """
        if not self.ui:
            print("警告: UI 未初始化，无法发送系统消息")
            return
            
        try:
            # 通过UI实例发送系统消息
            self.ui.append_system_message_ui(message)
        except Exception as e:
            print(f"发送系统消息失败: {str(e)}")

    def _update_result_ui(self, memory: List[Dict[str, Any]]) -> None:
        """
        更新结果UI
        
        Args:
            memory: 执行结果记忆列表
        """
        if not self.ui:
            print("警告: UI 未初始化，无法更新结果UI")
            return
            
        try:
            # 通过UI实例更新结果UI
            self.ui.update_result_ui(memory)
        except Exception as e:
            print(f"更新结果UI失败: {str(e)}")

    async def execute(self, user_request: str) -> Dict[str, Any]:
        """
        主任务启动方法
        
        Args:
            task: 用户任务描述
            
        Returns:
            Dict[str, Any]: 主任务第一次同步执行结果
        """
        try:
            # 1. 生成任务计划
            plan = self._generate_task_plan(user_request)
            if not plan.get("status") == "success":
                return {
                    "logs": plan
                }
            
            # 2. 解析计划步骤
            tasks = self._parse_planning_result(plan)
            
            if not tasks:
                return {
                    "logs": {
                        "status": "error",
                        "result": None,
                        "error": "无法生成有效的任务计划"
                    }
                }
            
            # 将计划显示到页面
            if self.ui:
                self.ui.update_plan_ui(tasks)
            else:
                print("警告: UI 未初始化，无法发送计划更新")
            
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
    
    async def _execute_task_chain(self, tasks: List[Dict[str, Any]]) -> None:
        """
        执行任务链
        
        Args:
            tasks: 任务列表
        """
        try:
            for i, task in enumerate(tasks):
                # 更新当前任务索引
                self.current_task_index = i
                
                # 执行任务
                step_result = await self.react_flow.execute(task, self.tools)
                
                # 复制结果，避免修改原始对象
                result_copy = step_result.copy()
                
                # 更新任务状态和结果
                if step_result.get("status") == "success":
                    # 只存储必要的信息
                    tasks[i].update({
                        "completed": True,
                        "status": "success"
                    })
                    
                    # 将结果添加到上下文，只存储必要的信息
                    self.add_memory({
                        "type": "step_result",
                        "step": i + 1,
                        "task": task.get("description", "未知任务"),
                        "status": "success"
                    })
                    
                    # 打印详细的结果信息
                    self._append_system_message(f"系统: 步骤 {i+1} 执行成功")
                    if step_result.get("result"):
                        try:
                            # 尝试将结果转换为字符串
                            result_str = str(step_result.get("result"))
                            self._append_system_message(f"系统: 步骤 {i+1} 结果: {result_str}")
                        except Exception as e:
                            self._append_system_message(f"系统: 步骤 {i+1} 结果无法序列化: {str(e)}")
                else:
                    tasks[i].update({
                        "completed": False,
                        "status": "error",
                        "error": step_result.get("error")
                    })
                    
                    # 打印错误信息
                    self._append_system_message(f"系统: 步骤 {i+1} 执行失败: {step_result.get('error')}")
                
                # 存储执行结果，只存储必要的信息
                self.memory.append({
                    "step": i + 1,
                    "task": task.get("description", "未知任务"),
                    "status": result_copy.get("status"),
                    "error": result_copy.get("error")
                })
                
                # 更新UI
                if self.ui:
                    try:
                        # 只在任务状态发生变化时更新UI
                        if tasks[i].get("completed") != task.get("completed") or \
                           tasks[i].get("error") != task.get("error"):
                            self.ui.update_plan_ui(tasks)
                    except Exception as e:
                        print(f"更新任务列表失败: {str(e)}")
                
        except Exception as e:
            print(f"执行任务链失败: {str(e)}")
            self._append_system_message(f"系统: 执行任务链失败: {str(e)}")
    
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
        
    def set_ui(self, ui):
        """
        设置UI实例
        
        Args:
            ui: UI实例
        """
        self.ui = ui
        return True
    
    def _parse_planning_result(self, plan_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        解析任务规划结果，将JSON格式的规划结果转换为任务列表
        
        Args:
            plan_result: 规划流程返回的结果
            
        Returns:
            List[Dict[str, Any]]: 解析后的任务列表
        """
        try:
            # 检查规划结果状态
            if plan_result.get("status") != "success":
                print(f"规划结果状态错误: {plan_result.get('status')}")
                return []
                
            # 获取规划结果
            result = plan_result.get("result", [])
            
            # 如果result已经是列表，直接使用
            if isinstance(result, list):
                tasks = result
            else:
                # 如果result是字符串，尝试解析JSON格式
                result_str = str(result)
                try:
                    tasks = json.loads(result_str)
                except json.JSONDecodeError:
                    # 如果JSON解析失败，尝试使用ast.literal_eval解析Python字面量
                    try:
                        tasks = ast.literal_eval(result_str)
                    except (SyntaxError, ValueError):
                        print(f"无法解析任务计划: {result_str}")
                        return []
                    
            # 验证任务列表格式
            if not isinstance(tasks, list):
                print(f"任务计划格式错误，应为列表: {type(tasks)}")
                return []
                
            # 验证每个任务的格式并转换为字典
            valid_tasks = []
            for i, task in enumerate(tasks):
                # 如果任务是字符串，将其转换为字典
                if isinstance(task, str):
                    task_dict = {
                        "description": task,
                        "id": i + 1,
                        "completed": False
                    }
                    valid_tasks.append(task_dict)
                    continue
                    
                # 如果任务已经是字典，验证其格式
                if not isinstance(task, dict):
                    print(f"任务 {i+1} 格式错误，应为字典或字符串: {type(task)}")
                    continue
                    
                # 确保任务包含必要的字段
                if "description" not in task:
                    print(f"任务 {i+1} 缺少description字段")
                    continue
                    
                # 添加任务ID和完成状态
                task["id"] = i + 1
                task["completed"] = False
                
                valid_tasks.append(task)
                
            print(f"成功解析任务计划，共 {len(valid_tasks)} 个有效任务")
            return valid_tasks
            
        except Exception as e:
            print(f"解析任务规划结果失败: {str(e)}")
            return []
       