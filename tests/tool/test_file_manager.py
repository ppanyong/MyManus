import unittest
import os
import tempfile
import shutil
import sys
print("开始执行测试文件")
print("当前工作目录:", os.getcwd())
print("Python路径:", sys.path)
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
print("添加后的Python路径:", sys.path)
try:
    from app.tool.file_manager import FileManager
    print("成功导入 FileManager")
except Exception as e:
    print("导入 FileManager 失败:", str(e))

class TestFileManager(unittest.TestCase):
    """文件管理工具测试类"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.txt")
        self.file_manager = FileManager()
        self.base_dir = None
        
    def tearDown(self):
        """测试后的清理工作"""
        # 清理基础目录
        if self.base_dir and os.path.exists(self.base_dir):
            shutil.rmtree(self.base_dir)
            
        # 清理测试文件
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
            
        # 清理临时目录
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_create_file(self):
        """测试创建文件"""
        # 测试创建新文件
        result = self.file_manager.create_file(self.test_file)
        self.assertEqual(result["status"], "success")
        self.assertTrue(os.path.exists(self.test_file))
        
        # 测试创建已存在的文件
        result = self.file_manager.create_file(self.test_file)
        self.assertEqual(result["status"], "error")
        self.assertIn("文件已存在", result["error"])
    
    def test_read_file(self):
        """测试读取文件"""
        # 测试读取不存在的文件
        result = self.file_manager.read_file(self.test_file)
        self.assertEqual(result["status"], "error")
        self.assertIn("文件不存在", result["error"])
        
        # 创建并写入测试文件
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write("测试内容")
            
        # 测试读取文件
        result = self.file_manager.read_file(self.test_file)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["content"], "测试内容")
    
    def test_write_file(self):
        """测试写入文件"""
        # 测试写入新文件
        content = "测试写入内容"
        result = self.file_manager.write_file(self.test_file, content)
        self.assertEqual(result["status"], "success")
        
        # 验证文件内容
        with open(self.test_file, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), content)
            
        # 测试覆盖写入
        new_content = "新的测试内容"
        result = self.file_manager.write_file(self.test_file, new_content)
        self.assertEqual(result["status"], "success")
        
        # 验证文件内容
        with open(self.test_file, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), new_content)
    
    def test_delete_file(self):
        """测试删除文件"""
        # 测试删除不存在的文件
        result = self.file_manager.delete_file(self.test_file)
        self.assertEqual(result["status"], "error")
        self.assertIn("文件不存在", result["error"])
        
        # 创建测试文件
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write("测试内容")
            
        # 测试删除文件
        result = self.file_manager.delete_file(self.test_file)
        self.assertEqual(result["status"], "success")
        self.assertFalse(os.path.exists(self.test_file))
    
    def test_base_dir(self):
        """测试基础目录功能"""
        # 创建带基础目录的文件管理器
        self.base_dir = os.path.join(self.temp_dir, "base")
        file_manager = FileManager({"base_dir": self.base_dir})
        
        # 测试创建文件
        result = file_manager.create_file("test.txt")
        self.assertEqual(result["status"], "success")
        
        # 验证文件路径
        expected_path = os.path.join(self.base_dir, "test.txt")
        self.assertTrue(os.path.exists(expected_path))
        
        # 测试写入文件
        content = "测试内容"
        result = file_manager.write_file("test.txt", content)
        self.assertEqual(result["status"], "success")
        
        # 验证文件内容
        with open(expected_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), content)

if __name__ == "__main__":
    unittest.main() 