from typing import Dict, Any, List
from abc import ABC, abstractmethod
import requests
from json_repair import repair_json
import json
import re
import logging

logger = logging.getLogger(__name__)

class BaseFlow(ABC):
    """基础流程框架"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.steps = []
        
    @abstractmethod
    def initialize(self):
        """初始化流程"""
        pass
        
    @abstractmethod
    def execute(self, prompt: str, tools: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行流程
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
            
            response = requests.post(
                api_config.get('url'),
                headers=headers,
                json=request_body
            )
            
            if response.status_code == 200:
                return {
                    "status": "success",
                    "result": response.json()
                }
            else:
                return {
                    "status": "error",
                    "error": f"API请求失败: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
        
    def add_step(self, step: Dict[str, Any]):
        """添加流程步骤"""
        self.steps.append(step)
        
    def get_steps(self) -> List[Dict[str, Any]]:
        """获取所有流程步骤"""
        return self.steps 

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """
        解析LLM响应文本，尝试提取JSON数据
        
        Args:
            response_text: LLM返回的原始响应文本
            
        Returns:
            Dict[str, Any]: 解析后的JSON数据
        """
        try:
            # 使用 json_repair 修复和解析JSON
            repaired_json = repair_json(response_text)
            return json.loads(repaired_json)
        except Exception as e:
            print(f"JSON解析失败: {str(e)}")
            return {
                "status": "error",
                "result": response_text,
                "error": "JSON解析失败"
            }
    
    def _parse_steps(self, response: Dict[str, Any]) -> List[str]:
        """解析API响应，提取步骤列表
        
        Args:
            response: API响应数据
            
        Returns:
            List[str]: 解析后的步骤列表
        """
        try:
            # 从 API 响应中提取文本内容
            if isinstance(response, dict):
                # 尝试从不同的响应格式中提取文本
                text = response.get('response', '')  # 对于 Ollama 格式
                if not text:
                    text = response.get('choices', [{}])[0].get('message', {}).get('content', '')  # 对于 OpenAI 格式
                if not text:
                    text = response.get('result', '')  # 对于其他格式
            else:
                text = str(response)
            
            # 首先尝试直接解析整个文本为JSON
            try:
                json_data = json.loads(text)
                if isinstance(json_data, dict) and "steps" in json_data:
                    return json_data["steps"]
            except json.JSONDecodeError:
                pass
            
            # 如果直接解析失败，尝试提取JSON部分
            json_pattern = r'```json\s*([\s\S]*?)\s*```'
            json_match = re.search(json_pattern, text)
            
            if json_match:
                json_str = json_match.group(1).strip()
                try:
                    json_data = json.loads(json_str)
                    if isinstance(json_data, dict) and "steps" in json_data:
                        return json_data["steps"]
                except json.JSONDecodeError:
                    pass
            
            # 如果JSON解析都失败，尝试使用json_repair修复
            try:
                repaired_json = repair_json(text)
                json_data = json.loads(repaired_json)
                if isinstance(json_data, dict) and "steps" in json_data:
                    return json_data["steps"]
            except Exception:
                pass
            
            # 如果所有JSON解析都失败，返回空列表
            logger.warning(f"无法解析JSON格式的步骤，返回空列表。原文text: {text}")
            return []
            
        except Exception as e:
            logger.error(f"解析步骤失败: {str(e)}")
            return []
    
    def format_tools(self, tools: List[Any]) -> List[Dict[str, Any]]:
        """格式化工具列表为统一格式
        
        Args:
            tools: 工具列表，每个工具对象应实现 get_tool_description 方法
            
        Returns:
            List[Dict[str, Any]]: 格式化后的工具列表
        """
        formatted_tools = []
        for tool in tools:
            try:
                tool_desc = tool.get_tool_description()
                formatted_tools.append({
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
        return formatted_tools
    
   