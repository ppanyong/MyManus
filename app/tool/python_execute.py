from typing import Dict, Any
import subprocess
import sys

class PythonExecuteTool:
    """Python代码执行工具"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
    def execute(self, code: str) -> Dict[str, Any]:
        """执行Python代码"""
        try:
            # 创建一个临时Python文件
            with open("temp.py", "w", encoding="utf-8") as f:
                f.write(code)
                
            # 执行Python文件
            result = subprocess.run(
                [sys.executable, "temp.py"],
                capture_output=True,
                text=True
            )
            
            return {
                "status": "success",
                "output": result.stdout,
                "error": result.stderr
            }
            
        except Exception as e:
            return {
                "status": "error",
                "output": None,
                "error": str(e)
            } 