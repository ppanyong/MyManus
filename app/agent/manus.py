import json
from typing import Dict, Any, List
import os
from jinja2 import Template
from .base import ToolCallAgent
from ..flow.planning import PlanningFlow
from ..flow.react import ReactFlow
import asyncio
import ast
import uuid
from app.tool.logger_tool import LoggerTool

# 初始化日志工具
logger_tool = LoggerTool()
logger = logger_tool.get_logger("ManusAgent")

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
        self.current_request_id = None
        logger.info(f"初始化ManusAgent，配置: {config}")
        
    def _generate_request_id(self) -> str:
        """
        生成唯一的请求ID
        
        Returns:
            str: 请求ID
        """
        return str(uuid.uuid4())
        
    def initialize(self) -> Dict[str, Any]:
        """初始化主智能体"""
        try:
            logger.info("开始初始化ManusAgent")
            # 使用planning_flow初始化 
            init_result = self.planning_flow.initialize()
            if init_result.get("status") == "error":
                logger.error(f"PlanningFlow初始化失败: {init_result}")
                return init_result
                
            # 初始化react_flow
            react_init_result = self.react_flow.initialize()
            if react_init_result.get("status") == "error":
                logger.error(f"ReactFlow初始化失败: {react_init_result}")
                return react_init_result
                
            logger.info("ManusAgent初始化成功")
            return {
                "status": "success",
                "result": "主智能体初始化成功",
                "error": None
            }
        except Exception as e:
            error_msg = f"主智能体初始化失败: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "result": None,
                "error": error_msg
            }
        
            
    def _append_system_message(self, message: str) -> None:
        """
        追加系统消息到对话
        
        Args:
            message: 系统消息内容
        """
        if not self.ui:
            logger.warning("UI 未初始化，无法发送系统消息")
            return
            
        try:
            # 通过UI实例发送系统消息
            self.ui.append_system_message_ui(message)
            logger.info(f"成功发送系统消息: {message}")
        except Exception as e:
            logger.error(f"发送系统消息失败: {str(e)}")

    def _update_result_ui(self, memory: List[Dict[str, Any]]) -> None:
        """
        更新结果UI
        
        Args:
            memory: 执行结果记忆列表
        """
        if not self.ui:
            logger.warning("UI 未初始化，无法更新结果UI")
            return
            
        try:
            # 通过UI实例更新结果UI
            self.ui.update_result_ui(memory)
            logger.info(f"成功更新结果UI，记忆数量: {len(memory)}")
        except Exception as e:
            logger.error(f"更新结果UI失败: {str(e)}")

    async def execute(self, user_request: str) -> Dict[str, Any]:
        """
        主任务启动方法
        
        Args:
            task: 用户任务描述
            
        Returns:
            Dict[str, Any]: 主任务第一次同步执行结果
        """
        try:
            # 重置 memory
            self.memory = []
            logger.info(f"已重置 memory，开始新的请求处理")
            
            # 生成新的请求ID
            self.current_request_id = self._generate_request_id()
            logger.info(f"[RequestID: {self.current_request_id}] 开始执行用户请求: {user_request}")
            
            # 1. 生成任务计划
            plan = self._generate_task_plan(user_request)
            if not plan.get("status") == "success":
                logger.error(f"[RequestID: {self.current_request_id}] 生成任务计划失败: {plan}")
                return {
                    "logs": plan
                }
            
            # 2. 解析计划步骤
            tasks = self._parse_planning_result(plan)
            
            if not tasks:
                logger.error(f"[RequestID: {self.current_request_id}] 无法生成有效的任务计划")
                return {
                    "logs": {
                        "status": "error",
                        "result": None,
                        "error": "无法生成有效的任务计划"
                    }
                }
            logger.info(f"[RequestID: {self.current_request_id}] 生成的有效任务计划: {tasks}")
            
            # 将计划显示到页面
            if self.ui:
                self.ui.update_plan_ui(tasks)
                self.ui.update_tasks_ui(tasks)
                logger.info(f"[RequestID: {self.current_request_id}] 更新计划UI，任务数量: {len(tasks)}")
            else:
                logger.error(f"[RequestID: {self.current_request_id}] UI 未初始化，无法发送计划更新")
            
            # 3. 初始化任务列表
            self.current_task_index = 0
            
            # 4. 返回初始状态
            response = {
                "status": "success",
                "result": "任务计划已生成，开始执行",
                "tasks": tasks,
                "request_id": self.current_request_id,
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
            
            
            response["result"] = f"任务:{self.current_request_id}执行完成，请查看任务结果的报告"

            return response
            
        except Exception as e:
            error_msg = f"处理任务失败: {str(e)}"
            logger.error(f"[RequestID: {self.current_request_id}] {error_msg}")
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
            logger.info(f"[RequestID: {self.current_request_id}] 开始执行任务链，任务数量: {len(tasks)}")
            for i, task in enumerate(tasks):
                # 更新当前任务索引
                self.current_task_index = i
                logger.info(f"[RequestID: {self.current_request_id}] 开始执行第 {i+1} 个任务: {task.get('description', '未知任务')}")
                
                # 获取依赖任务的结果
                dependencies = task.get("dependencies", [])
                if dependencies:
                    # 从memory中获取所有依赖任务的结果
                    previous_results = {}  # 改为字典格式
                    for dep in dependencies:
                        # 解析依赖步骤ID
                        if isinstance(dep, str) and dep.startswith("step_"):
                            try:
                                dep_step_id = int(dep.split("_")[1])
                                # 查找依赖任务的结果
                                for memory_item in self.memory:
                                    if memory_item.get("step") == dep_step_id:
                                        result = str(memory_item.get("result", ""))  # 使用空字符串作为默认值，并确保转换为字符串
                                        previous_results[f"step_{dep_step_id}_result"] = result
                                        # logger.info(f"[RequestID: {self.current_request_id}] 找到依赖步骤 {dep} 的结果")
                                        break
                            except (ValueError, IndexError):
                                logger.error(f"[RequestID: {self.current_request_id}] 无法解析依赖步骤ID: {dep}")
                        else:
                            logger.error(f"[RequestID: {self.current_request_id}] 无效的依赖步骤格式: {dep}")
                    
                    if previous_results:
                        # 将字典转换为JSON字符串
                        previous_results_str = json.dumps(previous_results, ensure_ascii=False)
                        # 合并所有依赖任务的结果
                        task["previous_result"] = previous_results_str
                        # logger.info(f"[RequestID: {self.current_request_id}] 添加依赖任务结果到任务 {i+1}: {previous_results_str}")
                
                # 执行任务
                step_result = await self.react_flow.execute(task, self.tools, self.current_request_id)
                logger.info(f"[RequestID: {self.current_request_id}] 任务 {i+1} 执行结果: {step_result.get('status')}")
                
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
                memory_item = {
                    "step": i + 1,
                    "task": task.get("description", "未知任务"),
                    "status": result_copy.get("status"),
                    "error": result_copy.get("error"),
                    "result": result_copy.get("result")
                }
                logger.info(f"[RequestID: {self.current_request_id}] 在memory中存储执行结果: {memory_item}")
                self._update_or_append_memory(memory_item)
                
                
                # 更新UI
                if self.ui:
                    try:
                        self.ui.update_plan_ui(tasks)
                        self.ui.update_tasks_ui(tasks)
                            
                        # 将结果转换为markdown格式
                        markdown_result = f"### 任务:{self.current_request_id}执行进度\n\n"
                        for memory_item in self.memory:
                            step = memory_item.get("step", "未知步骤")
                            task_desc = memory_item.get("task", "未知任务")
                            status = memory_item.get("status", "未知状态")
                            result = memory_item.get("result", "无结果")
                            
                            markdown_result += f"### 步骤 {step}: {task_desc}\n"
                            markdown_result += f"- 状态: {status}\n"
                            if isinstance(result, dict):
                                result = result.get("result", result)
                            markdown_result += f"- 结果: {result}\n\n"
                        
                        logger.info(f"[RequestID: {self.current_request_id}] 更新阶段性任务结果 Markdown格式: {markdown_result}")
                        # 更新结果UI
                        self._update_result_ui(markdown_result)
                    except Exception as e:
                        logger.error(f"[RequestID: {self.current_request_id}] 更新任务列表失败: {str(e)}")
                
        except Exception as e:
            logger.error(f"[RequestID: {self.current_request_id}] 执行任务链失败: {str(e)}")
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
            logger.info(f"[RequestID: {self.current_request_id}] 开始生成任务计划: {task}")
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
                    logger.error(f"[RequestID: {self.current_request_id}] 获取工具描述失败: {str(e)}")
                    continue
            
            # 调用规划流程生成计划
            plan_result = self.planning_flow.execute(task, available_tools, self.current_request_id)
            logger.info(f"[RequestID: {self.current_request_id}] 任务计划生成结果: {plan_result.get('status')}")
            return plan_result
            
        except Exception as e:
            error_msg = f"生成任务计划失败: {str(e)}"
            logger.error(f"[RequestID: {self.current_request_id}] {error_msg}")
            return {
                "status": "error",
                "result": None,
                "error": error_msg
            }
    
    def _load_prompt_template(self) -> Template:
        """
        加载提示模板
        
        Returns:
            Template: Jinja2模板
        """
        try:
            template_path = os.path.join(os.path.dirname(__file__), '..', '..', 'prompt', 'manus.jinja')
            logger.info(f"加载提示模板: {template_path}")
            with open(template_path, 'r', encoding='utf-8') as f:
                return Template(f.read())
        except Exception as e:
            logger.error(f"加载提示模板失败: {str(e)}")
            raise
            
    def add_tool(self, tool: Any) -> None:
        """
        添加工具
        
        Args:
            tool: 工具实例
        """
        try:
            self.tools.append(tool)
            logger.info(f"添加工具: {tool.__class__.__name__}")
        except Exception as e:
            logger.error(f"添加工具失败: {str(e)}")
        
    def add_memory(self, memory_item: Dict[str, Any]) -> None:
        """
        添加记忆
        
        Args:
            memory_item: 记忆项
        """
        try:
            self.memory.append(memory_item)
            logger.info(f"添加记忆: {memory_item.get('type', '未知类型')}")
        except Exception as e:
            logger.error(f"添加记忆失败: {str(e)}")
        
    def set_ui(self, ui):
        """
        设置UI实例
        
        Args:
            ui: UI实例
        """
        try:
            self.ui = ui
            logger.info("设置UI实例成功")
            return True
        except Exception as e:
            logger.error(f"设置UI实例失败: {str(e)}")
            return False
    
    def _parse_planning_result(self, plan_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        解析任务规划结果，将JSON格式的规划结果转换为任务列表
        
        Args:
            plan_result: 规划流程返回的结果
            
        Returns:
            List[Dict[str, Any]]: 解析后的任务列表
        """
        try:
            logger.info("开始解析任务规划结果")
            # 检查规划结果状态
            if plan_result.get("status") != "success":
                logger.error(f"规划结果状态错误: {plan_result.get('status')}")
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
                        logger.error(f"无法解析任务计划: {result_str}")
                        return []
                    
            # 验证任务列表格式
            if not isinstance(tasks, list):
                logger.error(f"任务计划格式错误，应为列表: {type(tasks)}")
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
                    logger.error(f"任务 {i+1} 格式错误，应为字典或字符串: {type(task)}")
                    continue
                    
                # 确保任务包含必要的字段
                if "description" not in task:
                    logger.error(f"任务 {i+1} 缺少description字段")
                    continue
                    
                # 添加任务ID和完成状态
                task["id"] = i + 1
                task["completed"] = False
                
                valid_tasks.append(task)
                
            logger.info(f"成功解析任务计划，共 {len(valid_tasks)} 个有效任务")
            return valid_tasks
            
        except Exception as e:
            logger.error(f"解析任务规划结果失败: {str(e)}")
            return []
    
    def _update_or_append_memory(self, memory_item: Dict[str, Any]) -> None:
        """
        更新或追加memory项
        
        Args:
            memory_item: 要存储的memory项
        """
        try:
            # 查找是否存在相同步骤的memory项
            for i, existing_item in enumerate(self.memory):
                if existing_item.get("step") == memory_item.get("step"):
                    # 更新已存在的项
                    self.memory[i] = memory_item
                    logger.info(f"[RequestID: {self.current_request_id}] 更新步骤 {memory_item.get('step')} 的执行结果")
                    return
            
            # 如果没有找到相同步骤的项，则追加
            self.memory.append(memory_item)
            logger.info(f"[RequestID: {self.current_request_id}] 追加步骤 {memory_item.get('step')} 的执行结果")
            
        except Exception as e:
            logger.error(f"[RequestID: {self.current_request_id}] 更新或追加memory失败: {str(e)}")
       