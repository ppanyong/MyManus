from typing import Dict, Any
from datetime import datetime
from app.tool.logger_tool import LoggerTool

# 初始化日志工具
logger_tool = LoggerTool()
logger = logger_tool.get_logger("TimeTool")

class TimeTool:
    """本地时间工具"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        logger.info(f"初始化TimeTool，配置: {config}")
        
    def get_local_time(self) -> Dict[str, Any]:
        """获取本地时间
        
        Returns:
            Dict[str, Any]: 包含时间信息的字典
            {
                "status": "success" | "error",
                "result": {
                    "date": str,  # 年月日
                    "time": str,  # 具体时间
                    "datetime": str  # 完整日期时间
                },
                "error": str | None
            }
        """
        try:
            logger.info("获取本地时间")
            now = datetime.now()
            result = {
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S"),
                "datetime": now.strftime("%Y-%m-%d %H:%M:%S")
            }
            logger.info(f"当前时间: {result['datetime']}")
            return {
                "status": "success",
                "result": result,
                "error": None
            }
        except Exception as e:
            error_msg = f"获取时间错误: {str(e)}"
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
            "name": "time_tool",
            "description": "一个获取本地时间的工具，提供年月日和具体时间信息",
            "functions": [
                {
                    "name": "get_local_time",
                    "description": "获取当前本地时间，包括年月日和具体时间",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    },
                    "returns": {
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "enum": ["success", "error"]
                            },
                            "result": {
                                "type": "object",
                                "properties": {
                                    "date": {
                                        "type": "string",
                                        "description": "年月日，格式：YYYY-MM-DD"
                                    },
                                    "time": {
                                        "type": "string",
                                        "description": "具体时间，格式：HH:MM:SS"
                                    },
                                    "datetime": {
                                        "type": "string",
                                        "description": "完整日期时间，格式：YYYY-MM-DD HH:MM:SS"
                                    }
                                }
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