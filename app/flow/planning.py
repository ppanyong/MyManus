from typing import Dict, Any, List, Tuple, Optional
import os
import re
from jinja2 import Template
from .base import BaseFlow

class PlanningFlow(BaseFlow):
    """规划流程实现"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.prompt_template = self._load_prompt_template()
        self.tools = []  # 存储注册的工具
        self._initialized_tools = False  # 标记工具是否已初始化
        self.tool_prompt_template = self._load_tool_prompt_template()
        
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
    
    def add_tool(self, tool: Any) -> None:
        """
        添加工具到规划流程
        
        Args:
            tool: 要添加的工具实例
        """
        if tool not in self.tools:  # 避免重复添加
            self.tools.append(tool)
        self._initialized_tools = True
        
    def add_tools(self, tools: List[Any]) -> None:
        """
        批量添加工具到规划流程
        
        Args:
            tools: 要添加的工具实例列表
        """
        for tool in tools:
            self.add_tool(tool)
        
    def execute(self, task: str) -> Dict[str, Any]:
        """执行规划流程，使用大模型解析并调用合适的工具"""
        if not self._initialized_tools:
            return {
                "status": "error",
                "result": None,
                "error": "工具未初始化，请先添加工具"
            }
            
        print(f"执行规划流程: {task}")
        try:
            # 1. 获取所有工具的描述信息
            tool_descriptions = self._get_all_tool_descriptions()
            
            # 2. 使用大模型解析任务，匹配工具
            tool_call = self._parse_task_with_llm(task, tool_descriptions)
            if not tool_call:
                return {
                    "status": "error",
                    "result": None,
                    "error": "无法理解任务或找到合适的工具"
                }
                
            tool_name, function_name, params = tool_call
            
            # 3. 查找并执行工具
            tool = self._find_tool(tool_name)
            if not tool:
                return {
                    "status": "error",
                    "result": None,
                    "error": f"找不到工具: {tool_name}"
                }
            
            try:
                func = getattr(tool, function_name)
                result = func(**params)
                
                return {
                    "status": "success",
                    "result": result,
                    "error": None,
                    "task_info": {
                        "tool": tool_name,
                        "function": function_name,
                        "params": params
                    }
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "result": None,
                    "error": f"执行失败: {str(e)}",
                    "task_info": {
                        "tool": tool_name,
                        "function": function_name,
                        "params": params
                    }
                }
                
        except Exception as e:
            return {
                "status": "error",
                "result": None,
                "error": f"规划流程失败: {str(e)}"
            }
    
    def _parse_task_with_llm(self, task: str, tool_descriptions: List[Dict]) -> Optional[Tuple[str, str, dict]]:
        """使用大模型解析任务并匹配合适的工具"""
        try:
            # 构建提示信息
            context = {
                "task": task,
                "tools": tool_descriptions
            }
            prompt = self.tool_prompt_template.render(**context)
            
            # 调用大模型获取响应
            response = self._call_llm(prompt)
            
            # 解析大模型的响应
            # 预期响应格式：
            # {
            #    "tool": "工具名称",
            #    "function": "函数名称",
            #    "parameters": {参数字典}
            # }
            
            if isinstance(response, dict):
                return (
                    response.get("tool"),
                    response.get("function"),
                    response.get("parameters", {})
                )
            return None
            
        except Exception as e:
            print(f"解析任务失败: {str(e)}")
            return None
            
    def _get_all_tool_descriptions(self) -> List[Dict]:
        """获取所有工具的描述信息"""
        descriptions = []
        for tool in self.tools:
            try:
                desc = tool.get_tool_description()
                if desc:
                    descriptions.append(desc)
            except:
                continue
        return descriptions
    
    def _find_tool(self, tool_name: str) -> Any:
        """查找指定名称的工具"""
        for tool in self.tools:
            try:
                desc = tool.get_tool_description()
                if desc.get("name") == tool_name:
                    return tool
            except:
                continue
        return None
    
    def _load_prompt_template(self) -> Template:
        """加载提示模板"""
        template_path = os.path.join("prompt", "planning.jinja")
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                return Template(f.read())
        except Exception as e:
            print(f"加载提示模板失败: {str(e)}")
            return Template("{{ task }}")
    
    def _load_tool_prompt_template(self) -> Template:
        """加载工具调用提示模板"""
        template_path = os.path.join("prompt", "tool_matching.jinja")
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                return Template(f.read())
        except Exception as e:
            # 默认模板
            default_template = """
            你是一个智能助手，需要帮助理解用户的任务并选择合适的工具来执行。

            可用的工具有：
            {% for tool in tools %}
            - {{ tool.name }}: {{ tool.description }}
              可用函数：
              {% for func in tool.functions %}
              * {{ func.name }}: {{ func.description }}
                参数: {{ func.parameters }}
              {% endfor %}
            {% endfor %}

            用户任务: {{ task }}

            请分析任务并返回合适的工具调用信息，格式如下：
            {
                "tool": "选择的工具名称",
                "function": "选择的函数名称",
                "parameters": {
                    "参数名": "参数值"
                }
            }
            """
            return Template(default_template) 