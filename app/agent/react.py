from typing import Dict, Any, Optional, List
from .base import ToolCallAgent

class ReactAgent(ToolCallAgent):
    """反应式代理，负责单个任务的思考和执行"""
    
    def __init__(self, task: str, tools: List[Any], step_index: int, memory: List[Dict] = None):
        """
        初始化反应式代理
        
        Args:
            task: 当前需要执行的任务
            tools: 可用的工具列表
            step_index: 当前步骤索引
            memory: 上下文记忆
        """
        super().__init__()
        self.task = task
        self.tools = tools
        self.step_index = step_index
        self.memory = memory or []
        self.next_agent: Optional[ReactAgent] = None
        self.result: Optional[Dict] = None
        self.selected_tool: Optional[Dict] = None
        
    def think(self, previous_result: Dict = None) -> Dict[str, Any]:
        """
        思考阶段：分析任务并选择合适的工具
        
        Args:
            previous_result: 上一步骤的执行结果
            
        Returns:
            Dict: 思考的结果，包含选择的工具信息
        """
        # 构建思考提示
        prompt = self._build_thinking_prompt(previous_result)
        
        try:
            # 调用大模型进行思考
            response = super().execute(prompt)
            
            if response.get("status") == "success":
                self.selected_tool = response.get("result")
                return {
                    "status": "success",
                    "thought": response.get("message"),
                    "tool_selection": self.selected_tool
                }
            else:
                return {
                    "status": "error",
                    "error": response.get("error"),
                    "thought": response.get("message")
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "thought": f"思考过程出现错误: {str(e)}"
            }
    
    def act(self) -> Dict[str, Any]:
        """
        执行阶段：使用选定的工具执行任务
        
        Returns:
            Dict: 执行结果
        """
        if not self.selected_tool:
            return {
                "status": "error",
                "error": "未选择执行工具",
                "result": None
            }
            
        try:
            # 查找并执行工具
            tool_name = self.selected_tool.get("tool")
            function_name = self.selected_tool.get("function")
            parameters = self.selected_tool.get("parameters", {})
            
            # 查找工具实例
            tool = self._find_tool(tool_name)
            if not tool:
                return {
                    "status": "error",
                    "error": f"找不到工具: {tool_name}",
                    "result": None
                }
            
            # 执行工具函数
            func = getattr(tool, function_name)
            result = func(**parameters)
            
            # 存储执行结果
            self.result = {
                "status": "success",
                "result": result,
                "task_info": {
                    "tool": tool_name,
                    "function": function_name,
                    "parameters": parameters
                }
            }
            
            # 更新记忆
            self.memory.append({
                "step": self.step_index,
                "task": self.task,
                "thought": self.selected_tool.get("message"),
                "action": f"使用 {tool_name}.{function_name}",
                "result": result
            })
            
            return self.result
            
        except Exception as e:
            error_result = {
                "status": "error",
                "error": str(e),
                "result": None
            }
            self.result = error_result
            return error_result
    
    def set_next_agent(self, agent: 'ReactAgent') -> None:
        """设置下一个代理实例"""
        self.next_agent = agent
        
    def execute_chain(self) -> Dict[str, Any]:
        """
        执行当前代理及其后续链条
        
        Returns:
            Dict: 包含所有执行结果的字典
        """
        # 思考阶段
        think_result = self.think()
        if think_result.get("status") == "error":
            return think_result
            
        # 执行阶段
        act_result = self.act()
        if act_result.get("status") == "error":
            return act_result
            
        # 如果有下一个代理，继续执行
        if self.next_agent:
            return self.next_agent.execute_chain()
            
        return act_result
    
    def _build_thinking_prompt(self, previous_result: Dict = None) -> str:
        """构建思考阶段的提示词"""
        prompt = f"""作为一个智能助手，请分析当前任务并选择合适的工具来执行。

当前任务: {self.task}
步骤编号: {self.step_index}

可用工具:
{self._format_tools_description()}

"""
        if previous_result:
            prompt += f"\n上一步骤的执行结果: {previous_result}\n"
            
        prompt += """
请分析任务并返回执行计划，格式如下:
{
    "tool": "选择的工具名称",
    "function": "选择的函数名称",
    "parameters": {
        "参数名": "参数值"
    }
}
"""
        return prompt
    
    def _find_tool(self, tool_name: str) -> Optional[Any]:
        """查找指定名称的工具"""
        for tool in self.tools:
            try:
                desc = tool.get_tool_description()
                if desc.get("name") == tool_name:
                    return tool
            except:
                continue
        return None
    
    def _format_tools_description(self) -> str:
        """格式化工具描述信息"""
        descriptions = []
        for tool in self.tools:
            try:
                desc = tool.get_tool_description()
                tool_desc = f"- {desc['name']}: {desc['description']}\n"
                tool_desc += "  函数:\n"
                for func in desc.get('functions', []):
                    tool_desc += f"  * {func['name']}: {func['description']}\n"
                    tool_desc += f"    参数: {func['parameters']}\n"
                descriptions.append(tool_desc)
            except:
                continue
        return "\n".join(descriptions) 