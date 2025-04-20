from typing import Dict, Any, Optional
from app.tool.base import BaseTool
import logging
import json
import requests
from app.tool.logger_tool import LoggerTool
from jinja2 import Environment, FileSystemLoader
import os

# 初始化日志工具
logger_tool = LoggerTool()
logger = logger_tool.get_logger("ContentSummaryTool")

class ContentSummaryTool(BaseTool):
    """内容小结工具类，用于处理JSON结构化数据并生成Markdown格式的小结"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        # 初始化日志工具
        logger.info(f"初始化ContentSummaryTool，配置: {config}")
        # 初始化jinja2环境
        template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'prompt')
        logger.info(f"模板目录: {template_dir}")
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.template = self.env.get_template('content_summary_tool.jinja')
    
    def get_tool_description(self) -> Dict[str, Any]:
        """返回工具描述，符合MCP协议"""
        return {
            "name": "content_summary",
            "description": "内容小结工具，只能处理文本内容，根据文本数据生成Markdown格式的小结，注意不能处理url链接类内容，适合于html_parser的工具配合使用。",
            "functions": [
                {
                    "name": "generate_summary",
                    "description": "将文本内进行汇总，生成Markdown格式小结",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "文本内容，注意不能时url链接类内容"
                            }
                        },
                        "required": ["content"]
                    },
                    "returns": {
                        "status": "error",
                        "result": "Markdown格式的小结内容",
                        "error": "大模型返回的内容为空"
                    }
                }
            ]
        }
    
    def generate_summary(self, content: str) -> Dict[str, Any]:
        """
        内容小结工具，可以处理文本数据并生成Markdown格式的小结
        
        Args:
            content: 文本内容
            
        Returns:
            Dict[str, Any]: 包含status、result和error字段的字典
        """
        try:
            # 使用模板生成提示词
            prompt = self.template.render(content=content)
            
            # 调用大模型生成小结
            response = self._call_summary_api(prompt)
            
            if response.get("status") == "error":
                logger.error(f"生成小结失败: {response.get('error')}")
                return {
                    "status": "error",
                    "result": None,
                    "error": f"生成小结失败: {response.get('error')}"
                }
            
            # 从大模型返回中提取实际内容
            result = response.get("result", {})
            choices = result.get("choices", [{}])
            if not choices:
                logger.error("无法从大模型返回中提取内容")
                return {
                    "status": "error",
                    "result": None,
                    "error": "无法从大模型返回中提取内容"
                }
                
            summary = choices[0].get("message", {}).get("content", "")
            if not summary:
                logger.error("大模型返回的内容为空")
                return {
                    "status": "error",
                    "result": None,
                    "error": "大模型返回的内容为空"
                }
                
            return {
                "status": "success",
                "result": summary,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"生成小结时发生错误: {str(e)}")
            return {
                "status": "error",
                "result": None,
                "error": f"生成小结时发生错误: {str(e)}"
            }
    
    def _call_summary_api(self, prompt: str) -> Dict[str, Any]:
        """
        调用大模型API生成小结
        
        Args:
            prompt: 提示词
            
        Returns:
            Dict[str, Any]: 包含status、result和error字段的字典
        """
        try:
            # 从配置中获取 API 设置
            api_config = self.config.get('summary_api', {})
            
            if not api_config:
                return {
                    "status": "error",
                    "result": None,
                    "error": "API配置未找到"
                }
            
            api_url = api_config.get('url')
            api_key = api_config.get('api_key')
            model = api_config.get('model')
            
            if not all([api_url, api_key, model]):
                return {
                    "status": "error",
                    "result": None,
                    "error": "API配置不完整，需要url、api_key和model"
                }
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # 构建请求体
            request_body = {
                "model": model,
                "prompt": prompt,
                "stream": api_config.get('stream', False),
                "options": {
                    "temperature": api_config.get('temperature', 0.3),
                    "max_tokens": api_config.get('max_tokens', 4000)
                },
                "messages": [
                    {
                        "content": prompt,
                        "role": "user"
                    }
                ]
            }
            
            # 发送请求
            response = requests.post(
                api_url,
                headers=headers,
                json=request_body,
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    "status": "success",
                    "result": response.json(),
                    "error": None
                }
            else:
                return {
                    "status": "error",
                    "result": None,
                    "error": f"API请求失败: HTTP {response.status_code} - {response.text}"
                }
                
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "result": None,
                "error": "API请求超时"
            }
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "result": None,
                "error": f"API请求异常: {str(e)}"
            }
        except Exception as e:
            return {
                "status": "error",
                "result": None,
                "error": f"执行异常: {str(e)}"
            } 