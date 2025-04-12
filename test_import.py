import os
import sys

print("Python版本:", sys.version)
print("Python路径:", sys.executable)
print("当前工作目录:", os.getcwd())
print("PYTHONPATH:", os.environ.get('PYTHONPATH', '未设置')) 