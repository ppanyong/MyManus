import sys
import os

def check_environment():
    print("检查Python环境...")
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', '未设置')}")
    
    # 检查必要的包
    try:
        import toml
        print("toml包已安装")
    except ImportError:
        print("错误: toml包未安装")
        return False
    
    return True

if __name__ == "__main__":
    if check_environment():
        print("环境检查通过，正在启动主程序...")
        import main
        main.main()
    else:
        print("环境检查失败，请安装必要的依赖") 