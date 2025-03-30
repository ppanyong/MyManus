from typing import Dict, Any, List
from abc import ABC, abstractmethod
import requests
from json_repair import repair_json
import json

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
    def execute(self) -> Dict[str, Any]:
        """执行流程"""
        pass
        
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
    
    def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """调用大语言模型"""
        try:
            # 调用本地Ollama服务
            print(f"发送提示词到LLM: {prompt}")
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "qwen2.5-coder:14b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.0,
                        "max_tokens": 4096
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")
                print(f"LLM响应: {response_text}")
                
                # 解析响应文本中的JSON
                parsed_response = self._parse_llm_response(response_text)
                return parsed_response
                
            else:
                error_msg = f"调用模型失败: {response.status_code}"
                print(error_msg)
                return {
                    "status": "error",
                    "result": None,
                    "error": error_msg
                }
                
        except Exception as e:
            error_msg = f"调用LLM出错: {str(e)}"
            print(error_msg)
            return {
                "status": "error",
                "result": None,
                "error": error_msg
            } 