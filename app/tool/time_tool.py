from typing import Dict, Any
from datetime import datetime, timedelta
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
    
    def get_current_year(self) -> Dict[str, Any]:
        """获取当前年份（4位数字）
        
        Returns:
            Dict[str, Any]: 包含年份信息的字典
            {
                "status": "success" | "error",
                "result": str,  # 4位数字年份
                "error": str | None
            }
        """
        try:
            logger.info("获取当前年份")
            year = datetime.now().strftime("%Y")
            logger.info(f"当前年份: {year}")
            return {
                "status": "success",
                "result": year,
                "error": None
            }
        except Exception as e:
            error_msg = f"获取年份错误: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "result": None,
                "error": error_msg
            }

    def get_current_month(self) -> Dict[str, Any]:
        """获取当前月份（2位数字）
        
        Returns:
            Dict[str, Any]: 包含月份信息的字典
            {
                "status": "success" | "error",
                "result": str,  # 2位数字月份
                "error": str | None
            }
        """
        try:
            logger.info("获取当前月份")
            month = datetime.now().strftime("%m")
            logger.info(f"当前月份: {month}")
            return {
                "status": "success",
                "result": month,
                "error": None
            }
        except Exception as e:
            error_msg = f"获取月份错误: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "result": None,
                "error": error_msg
            }

    def get_current_day(self) -> Dict[str, Any]:
        """获取当前日期（2位数字）
        
        Returns:
            Dict[str, Any]: 包含日期信息的字典
            {
                "status": "success" | "error",
                "result": str,  # 2位数字日期
                "error": str | None
            }
        """
        try:
            logger.info("获取当前日期")
            day = datetime.now().strftime("%d")
            logger.info(f"当前日期: {day}")
            return {
                "status": "success",
                "result": day,
                "error": None
            }
        except Exception as e:
            error_msg = f"获取日期错误: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "result": None,
                "error": error_msg
            }

    def extract_year_from_date(self, date_str: str) -> Dict[str, Any]:
        """从日期字符串中提取年份（4位数字）
        
        Args:
            date_str (str): 日期字符串，格式为 YYYY-MM-DD
            
        Returns:
            Dict[str, Any]: 包含年份信息的字典
            {
                "status": "success" | "error",
                "result": str,  # 4位数字年份
                "error": str | None
            }
        """
        try:
            logger.info(f"从日期 {date_str} 中提取年份")
            # 验证日期格式
            datetime.strptime(date_str, "%Y-%m-%d")
            year = date_str.split("-")[0]
            logger.info(f"提取的年份: {year}")
            return {
                "status": "success",
                "result": year,
                "error": None
            }
        except ValueError:
            error_msg = f"日期格式错误，应为 YYYY-MM-DD 格式"
            logger.error(error_msg)
            return {
                "status": "error",
                "result": None,
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"提取年份错误: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "result": None,
                "error": error_msg
            }

    def add_days(self, date_str: str, days: int) -> Dict[str, Any]:
        """在指定日期上增加天数
        
        Args:
            date_str (str): 日期字符串，支持以下格式：
                - YYYY-MM-DD
                - MM-DD-YYYY
                - YYYY-MM (默认为当月第一天)
                - YYYY (默认为当年第一天)
            days (int): 要增加的天数
            
        Returns:
            Dict[str, Any]: 包含新日期信息的字典
            {
                "status": "success" | "error",
                "result": str,  # 新日期，格式为 YYYY-MM-DD
                "error": str | None
            }
        """
        try:
            logger.info(f"在日期 {date_str} 上增加 {days} 天")
            
            # 处理不完整的日期格式
            if len(date_str) == 4:  # 只有年份
                date_str = f"{date_str}-01-01"
            elif len(date_str) == 7:  # 只有年份和月份
                date_str = f"{date_str}-01"
            
            # 尝试解析 YYYY-MM-DD 格式
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                # 如果失败，尝试解析 MM-DD-YYYY 格式
                try:
                    date = datetime.strptime(date_str, "%m-%d-%Y")
                except ValueError:
                    error_msg = f"日期格式错误，应为 YYYY-MM-DD 或 MM-DD-YYYY 格式"
                    logger.error(error_msg)
                    return {
                        "status": "error",
                        "result": None,
                        "error": error_msg
                    }
            
            new_date = date + timedelta(days=days)
            result = new_date.strftime("%Y-%m-%d")
            logger.info(f"新日期: {result}")
            return {
                "status": "success",
                "result": result,
                "error": None
            }
        except Exception as e:
            error_msg = f"日期计算错误: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "result": None,
                "error": error_msg
            }

    def subtract_days(self, date_str: str, days: int) -> Dict[str, Any]:
        """在指定日期上减少天数
        
        Args:
            date_str (str): 日期字符串，格式为 YYYY-MM-DD
            days (int): 要减少的天数
            
        Returns:
            Dict[str, Any]: 包含新日期信息的字典
            {
                "status": "success" | "error",
                "result": str,  # 新日期，格式为 YYYY-MM-DD
                "error": str | None
            }
        """
        try:
            logger.info(f"在日期 {date_str} 上减少 {days} 天")
            date = datetime.strptime(date_str, "%Y-%m-%d")
            new_date = date - timedelta(days=days)
            result = new_date.strftime("%Y-%m-%d")
            logger.info(f"新日期: {result}")
            return {
                "status": "success",
                "result": result,
                "error": None
            }
        except ValueError:
            error_msg = f"日期格式错误，应为 YYYY-MM-DD 格式"
            logger.error(error_msg)
            return {
                "status": "error",
                "result": None,
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"日期计算错误: {str(e)}"
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
            "description": "一个获取本地时间的工具，提供年月日和具体时间信息，支持日期的加减操作",
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
                },
                {
                    "name": "get_current_year",
                    "description": "获取当前年份（4位数字）",
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
                                "type": "string",
                                "description": "4位数字年份，格式：YYYY"
                            },
                            "error": {
                                "type": "string",
                                "description": "错误信息"
                            }
                        }
                    }
                },
                {
                    "name": "get_current_month",
                    "description": "获取当前月份（2位数字）",
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
                                "type": "string",
                                "description": "2位数字月份，格式：MM"
                            },
                            "error": {
                                "type": "string",
                                "description": "错误信息"
                            }
                        }
                    }
                },
                {
                    "name": "get_current_day",
                    "description": "获取当前日期（2位数字）",
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
                                "type": "string",
                                "description": "2位数字日期，格式：DD"
                            },
                            "error": {
                                "type": "string",
                                "description": "错误信息"
                            }
                        }
                    }
                },
                {
                    "name": "extract_year_from_date",
                    "description": "从日期字符串中提取年份（4位数字）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date_str": {
                                "type": "string",
                                "description": "日期字符串，格式为 YYYY-MM-DD"
                            }
                        },
                        "required": ["date_str"]
                    },
                    "returns": {
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "enum": ["success", "error"]
                            },
                            "result": {
                                "type": "string",
                                "description": "4位数字年份，格式：YYYY"
                            },
                            "error": {
                                "type": "string",
                                "description": "错误信息"
                            }
                        }
                    }
                },
                {
                    "name": "add_days",
                    "description": "在指定日期上增加天数",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date_str": {
                                "type": "string",
                                "description": "日期字符串，格式为 YYYY-MM-DD 或 MM-DD-YYYY"
                            },
                            "days": {
                                "type": "integer",
                                "description": "要增加的天数"
                            }
                        },
                        "required": ["date_str", "days"]
                    },
                    "returns": {
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "enum": ["success", "error"]
                            },
                            "result": {
                                "type": "string",
                                "description": "新日期，格式：YYYY-MM-DD"
                            },
                            "error": {
                                "type": "string",
                                "description": "错误信息"
                            }
                        }
                    }
                },
                {
                    "name": "subtract_days",
                    "description": "在指定日期上减少天数",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date_str": {
                                "type": "string",
                                "description": "日期字符串，格式为 YYYY-MM-DD"
                            },
                            "days": {
                                "type": "integer",
                                "description": "要减少的天数"
                            }
                        },
                        "required": ["date_str", "days"]
                    },
                    "returns": {
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "enum": ["success", "error"]
                            },
                            "result": {
                                "type": "string",
                                "description": "新日期，格式：YYYY-MM-DD"
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