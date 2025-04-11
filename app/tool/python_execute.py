from typing import Dict, Any
import subprocess
import sys
import os
import tempfile

class PythonExecuteTool:
    """Python代码执行工具"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
    def execute(self, code: str) -> Dict[str, Any]:
        """执行Python代码"""
        temp_file = None
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                temp_file = f.name
                f.write(code)
            
            # 执行Python文件
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=30  # 设置30秒超时
            )
            
            # 检查是否有错误输出
            if result.stderr:
                return {
                    "status": "error",
                    "output": None,
                    "error": result.stderr
                }
            
            return {
                "status": "success",
                "output": result.stdout,
                "error": ""
            }
            
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "output": None,
                "error": "执行超时"
            }
        except Exception as e:
            return {
                "status": "error",
                "output": None,
                "error": str(e)
            }
        finally:
            # 清理临时文件
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass
    
    def get_tool_description(self) -> Dict[str, Any]:
        """返回工具描述，符合MCP协议"""
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
                            "output": {
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