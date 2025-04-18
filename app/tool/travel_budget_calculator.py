from typing import Dict, Any
from app.tool.logger_tool import LoggerTool

# 初始化日志工具
logger_tool = LoggerTool()
logger = logger_tool.get_logger("TravelBudgetCalculator")

class TravelBudgetCalculator:
    """旅行预算计算工具"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        logger.info(f"初始化TravelBudgetCalculator，配置: {config}")
        
    def calculate_daily_budget(self, total_budget_min: float, total_budget_max: float, days: int, currency: str = "元") -> Dict[str, Any]:
        """计算每日旅行预算
        
        Args:
            total_budget_min: 总预算最小值
            total_budget_max: 总预算最大值
            days: 旅行天数
            currency: 货币单位，默认为"元"
            
        Returns:
            Dict[str, Any]: 包含计算结果的字典
            {
                "status": "success" | "error",
                "result": {
                    "daily_budget_min": float | None,  # 每日预算最小值
                    "daily_budget_max": float | None,  # 每日预算最大值
                },
                "error": str | None
            }
        """
        try:
            logger.info(f"计算旅行预算: 总预算范围 {currency}{total_budget_min}-{currency}{total_budget_max}, {days}天")
            
            if days <= 0:
                raise ValueError("旅行天数必须大于0")
            if total_budget_min <= 0 or total_budget_max <= 0:
                raise ValueError("预算金额必须大于0")
            if total_budget_min > total_budget_max:
                raise ValueError("预算最小值不能大于最大值")
                
            daily_budget_min = total_budget_min / days
            daily_budget_max = total_budget_max / days
            
            logger.info(f"计算结果: 每日预算范围 {currency}{daily_budget_min:.2f}-{currency}{daily_budget_max:.2f}")
            
            return {
                "status": "success",
                "result": {
                    "daily_budget_min": round(daily_budget_min, 2),
                    "daily_budget_max": round(daily_budget_max, 2)
                },
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
            "name": "travel_budget_calculator",
            "description": "旅行预算计算工具，用于计算每日旅行预算范围",
            "functions": [
                {
                    "name": "calculate_daily_budget",
                    "description": "根据总预算范围和旅行天数计算每日预算范围",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "total_budget_min": {
                                "type": "number",
                                "description": "总预算最小值"
                            },
                            "total_budget_max": {
                                "type": "number",
                                "description": "总预算最大值"
                            },
                            "days": {
                                "type": "integer",
                                "description": "旅行天数"
                            },
                            "currency": {
                                "type": "string",
                                "description": "货币单位",
                                "default": "元"
                            }
                        },
                        "required": ["total_budget_min", "total_budget_max", "days"]
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
                                    "daily_budget_min": {
                                        "type": "number",
                                        "description": "每日预算最小值"
                                    },
                                    "daily_budget_max": {
                                        "type": "number",
                                        "description": "每日预算最大值"
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