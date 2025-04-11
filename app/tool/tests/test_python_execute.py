import unittest
from app.tool.python_execute import PythonExecuteTool

class TestPythonExecuteTool(unittest.TestCase):
    def setUp(self):
        self.tool = PythonExecuteTool({})
    
    def test_successful_execution(self):
        """测试成功执行Python代码"""
        code = "print('Hello, World!')"
        result = self.tool.execute(code)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["output"].strip(), "Hello, World!")
        self.assertEqual(result["error"], "")
    
    def test_error_execution(self):
        """测试执行错误的Python代码"""
        code = "print(1/0)"
        result = self.tool.execute(code)
        
        self.assertEqual(result["status"], "error")
        self.assertIsNone(result["output"])
        self.assertIn("ZeroDivisionError", result["error"])
    
    def test_syntax_error(self):
        """测试语法错误的Python代码"""
        code = "print('Hello, World!'"
        result = self.tool.execute(code)
        
        self.assertEqual(result["status"], "error")
        self.assertIsNone(result["output"])
        self.assertIn("SyntaxError", result["error"])
    
    def test_timeout(self):
        """测试执行超时的情况"""
        code = "import time; time.sleep(40)"
        result = self.tool.execute(code)
        
        self.assertEqual(result["status"], "error")
        self.assertIsNone(result["output"])
        self.assertEqual(result["error"], "执行超时")
    
    def test_get_tool_description(self):
        """测试获取工具描述"""
        description = self.tool.get_tool_description()
        
        self.assertEqual(description["name"], "python_execute")
        self.assertEqual(description["functions"][0]["name"], "execute")
        self.assertIn("code", description["functions"][0]["parameters"]["properties"])

if __name__ == '__main__':
    unittest.main() 