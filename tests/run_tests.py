import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入测试模块
from tests.test_manus import TestManusAgent
from tests.test_react_flow import TestReactFlow

def run_tests():
    """运行所有测试"""
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 创建测试加载器
    loader = unittest.TestLoader()
    
    # 添加测试类
    test_suite.addTest(loader.loadTestsFromTestCase(TestManusAgent))
    test_suite.addTest(loader.loadTestsFromTestCase(TestReactFlow))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 返回测试结果
    return result.wasSuccessful()

if __name__ == '__main__':
    # 运行测试并设置退出码
    success = run_tests()
    sys.exit(0 if success else 1) 