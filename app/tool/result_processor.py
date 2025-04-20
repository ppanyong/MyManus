import json
import re
from typing import Any, Dict, Optional
from app.tool.logger_tool import LoggerTool

logger = LoggerTool().get_logger("ResultProcessor")

class ResultProcessor:
    """结果处理工具类，用于统一处理各种格式的结果数据"""
    
    @staticmethod
    def normalize_json_string(json_str: str) -> str:
        """标准化JSON字符串
        
        Args:
            json_str: 需要标准化的JSON字符串
            
        Returns:
            str: 标准化后的JSON字符串
        """
        if not json_str or not json_str.strip():
            return "{}"
            
        # 预处理：替换单引号为双引号
        json_str = json_str.replace("'", '"')
        
        # 处理Python字典格式
        if json_str.startswith('{') and json_str.endswith('}'):
            # 确保键名使用双引号
            json_str = re.sub(r'(\w+):', r'"\1":', json_str)
            # 标准化null值
            json_str = re.sub(r':\s*None\b', ': null', json_str)
            # 转义特殊字符
            json_str = json_str.replace('...', '\\u2026')
            json_str = json_str.replace('…', '\\u2026')
            # 转义其他特殊字符
            json_str = json_str.replace('\\', '\\\\')
            json_str = json_str.replace('\n', '\\n')
            json_str = json_str.replace('\r', '\\r')
            json_str = json_str.replace('\t', '\\t')
            
        return json_str
    
    @staticmethod
    def parse_result(result: Any, request_id: Optional[str] = None) -> Dict[str, Any]:
        """解析结果数据
        
        Args:
            result: 需要解析的结果数据
            request_id: 请求ID，用于日志记录
            
        Returns:
            Dict[str, Any]: 解析后的结果字典
        """
        try:
            # 如果已经是字典类型，直接返回
            if isinstance(result, dict):
                return result
                
            # 如果是字符串，尝试解析为JSON
            if isinstance(result, str):
                # 尝试直接解析
                try:
                    return json.loads(result)
                except json.JSONDecodeError:
                    # 如果直接解析失败，尝试标准化后解析
                    normalized_str = ResultProcessor.normalize_json_string(result)
                    try:
                        return json.loads(normalized_str)
                    except json.JSONDecodeError:
                        # 如果还是失败，尝试提取可能的JSON部分
                        match = re.search(r'\{.*\}', normalized_str)
                        if match:
                            try:
                                return json.loads(match.group())
                            except json.JSONDecodeError:
                                pass
                        logger.warning(f"[RequestID: {request_id}] 无法解析JSON字符串: {result}")
                        return {"result": result}
                    
            # 如果是列表，处理每个元素
            if isinstance(result, list):
                processed_results = []
                for item in result:
                    if isinstance(item, dict):
                        processed_results.append(item)
                    elif isinstance(item, str):
                        try:
                            processed_item = json.loads(item)
                            processed_results.append(processed_item)
                        except json.JSONDecodeError:
                            processed_results.append({"result": item})
                    else:
                        processed_results.append({"result": item})
                return {"results": processed_results}
                
            # 其他类型，直接包装为字典
            return {"result": result}
            
        except Exception as e:
            logger.error(f"[RequestID: {request_id}] 解析结果失败: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def extract_result_value(result: Dict[str, Any], key: str = "result") -> Any:
        """从结果字典中提取指定键的值
        
        Args:
            result: 结果字典
            key: 要提取的键名
            
        Returns:
            Any: 提取的值
        """
        if not isinstance(result, dict):
            return result
            
        # 如果是标准响应格式（包含 status, result, error）
        if all(k in result for k in ["status", "result", "error"]):
            if result["status"] == "success":
                return result["result"]
            else:
                return result
                
        # 如果有 results 键且是列表
        if "results" in result and isinstance(result["results"], list):
            # 如果列表只有一个元素，返回该元素
            if len(result["results"]) == 1:
                return result["results"][0]
            return result["results"]
            
        # 优先返回指定键的值
        if key in result:
            return result[key]
            
        # 如果没有指定键，返回整个字典
        return result 