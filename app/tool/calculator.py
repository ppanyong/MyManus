from typing import Dict, Any
from app.tool.logger_tool import LoggerTool

# 初始化日志工具
logger_tool = LoggerTool()
logger = logger_tool.get_logger("CalculatorTool")

class CalculatorTool:
    """本地计算器工具"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        logger.info(f"初始化CalculatorTool，配置: {config}")
        
    def add(self, a: float, b: float) -> Dict[str, Any]:
        """执行加法运算
        
        Args:
            a: 第一个数字
            b: 第二个数字
            
        Returns:
            Dict[str, Any]: 包含计算结果的字典
            {
                "status": "success" | "error",
                "result": float | None,
                "error": str | None
            }
        """
        try:
            logger.info(f"执行加法运算: {a} + {b}")
            result = float(a) + float(b)
            logger.info(f"计算结果: {result}")
            return {
                "status": "success",
                "result": result,
                "error": None
            }
        except (ValueError, TypeError) as e:
            error_msg = f"计算错误: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "result": None,
                "error": error_msg
            }
    
    def get_tool_description(self) -> Dict[str, Any]:
        """返回工具描述，符合MCP协议"""
        logger.info("获取工具描述")
        return {
            "name": "calculator",
            "description": "一个简单的计算器工具，提供基础的数学运算功能",
            "functions": [
                {
                    "name": "add",
                    "description": "执行两个数字的加法运算",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "a": {
                                "type": "number",
                                "description": "第一个数字"
                            },
                            "b": {
                                "type": "number",
                                "description": "第二个数字"
                            }
                        },
                        "required": ["a", "b"]
                    },
                    "returns": {
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "enum": ["success", "error"]
                            },
                            "result": {
                                "type": "number",
                                "description": "计算结果"
                            },
                            "error": {
                                "type": "string",
                                "description": "错误信息"
                            }
                        }
                    }
                }
            ]
        } 