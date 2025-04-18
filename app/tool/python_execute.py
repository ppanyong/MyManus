from typing import Dict, Any
import subprocess
import sys
import os
import tempfile
from app.tool.logger_tool import LoggerTool

# 初始化日志工具
logger_tool = LoggerTool()
logger = logger_tool.get_logger("PythonExecuteTool")

class PythonExecuteTool:
    """Python代码执行工具"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        logger.info(f"初始化PythonExecuteTool，配置: {config}")
        
    def execute(self, code: str) -> Dict[str, Any]:
        """执行Python代码"""
        temp_file = None
        try:
            logger.info("开始执行Python代码")
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                temp_file = f.name
                f.write(code)
                logger.info(f"创建临时文件: {temp_file}")
            
            # 执行Python文件
            logger.info("执行Python文件")
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=30  # 设置30秒超时
            )
            
            # 检查是否有错误输出
            if result.stderr:
                error_msg = f"执行出错: {result.stderr}"
                logger.error(error_msg)
                return {
                    "status": "error",
                    "result": None,
                    "error": error_msg
                }
            
            logger.info(f"执行成功，输出: {result.stdout}")
            return {
                "status": "success",
                "result": result.stdout,
                "error": ""
            }
            
        except subprocess.TimeoutExpired:
            error_msg = "执行超时"
            logger.error(error_msg)
            return {
                "status": "error",
                "result": None,
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"执行异常: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "result": None,
                "error": error_msg
            }
        finally:
            # 清理临时文件
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                    logger.info(f"清理临时文件: {temp_file}")
                except Exception as e:
                    logger.error(f"清理临时文件失败: {str(e)}")
    
    def get_tool_description(self) -> Dict[str, Any]:
        """返回工具描述，符合MCP协议"""
        logger.info("获取工具描述")
        return {
            "name": "python_execute",
            "description": "Python代码执行工具,可以执行Python代码并返回结果",
            "functions": [
                {
                    "name": "execute",
                    "description": "执行Python代码",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "要执行的Python代码"
                            }
                        },
                        "required": ["code"]
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
                                "description": "代码执行的输出结果"
                            },
                            "error": {
                                "type": "string", 
                                "description": "错误信息"
                            }
                        }
                    }
                }
            ]}