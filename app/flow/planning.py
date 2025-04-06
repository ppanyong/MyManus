from typing import Dict, Any, List
import os
from jinja2 import Template
from .base import BaseFlow
import requests
import time

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
            print(error_msg)
            return {
                "status": "error",
                "result": None,
                "error": error_msg
            }
        
    def execute(self, task: str) -> Dict[str, Any]:
        """
        执行规划流程，将用户任务分解为具体步骤
        
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
        
    def execute(self, prompt: str, tools: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行规划流程
        Args:
            prompt: 提示词
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
            # 从配置中获取 API 设置
            api_config = self.config.get('api', {})
            
            headers = {
                "Authorization": f"Bearer {api_config.get('api_key')}",
                "Content-Type": "application/json"
            }
            
            # 构建请求体
            request_body = {
                "model": api_config.get('model'),
                "prompt": prompt,
                "stream": api_config.get('stream', False),
                "options": {
                    "temperature": api_config.get('temperature', 0.7),
                    "max_tokens": api_config.get('max_tokens', 4096)
                },
                "messages": [
                    {
                        "content": prompt,
                        "role": "user"
                    }
                ]
            }
            
            # 如果提供了 tools，添加到请求体中
            if tools:
                request_body["tools"] = tools
            
            # 添加重试机制
            max_retries = 3
            retry_delay = 2  # 秒
            
            for attempt in range(max_retries):
                try:
                    response = requests.post(
                        api_config.get('url'),
                        headers=headers,
                        json=request_body,
                        timeout=30  # 添加超时设置
                    )
                    
                    if response.status_code == 200:
                        return {
                            "status": "success",
                            "result": response.json()
                        }
                    else:
                        print(f"API请求失败 (尝试 {attempt + 1}/{max_retries}): {response.status_code}")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            continue
                        return {
                            "status": "error",
                            "error": f"API请求失败: {response.status_code}"
                        }
                        
                except requests.exceptions.ConnectionError as e:
                    print(f"连接错误 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                    if attempt < max_retries - 1:
                        print(f"等待 {retry_delay} 秒后重试...")
                        time.sleep(retry_delay)
                        continue
                    return {
                        "status": "error",
                        "error": f"无法连接到API服务: {str(e)}"
                    }
                except requests.exceptions.Timeout:
                    print(f"请求超时 (尝试 {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    return {
                        "status": "error",
                        "error": "API请求超时"
                    }
                except Exception as e:
                    print(f"请求异常 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    return {
                        "status": "error",
                        "error": f"API请求异常: {str(e)}"
                    }
                    
        except Exception as e:
            error_msg = f"规划流程失败: {str(e)}"
            print(error_msg)
            return {
                "status": "error",
                "error": str(e)
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
            response = super().execute(prompt)
            
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