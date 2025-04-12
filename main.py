import os
import toml
from app.agent.manus import ManusAgent
from app.tool.file_manager import FileManager
from app.tool.html_parser_tool import HTMLParserTool
from app.tool.python_execute import PythonExecuteTool
from app.tool.google_search import GoogleSearchTool
from app.tool.baidu_search import BaiduSearchTool
from app.ui.ui import UI
from app.tool.calculator import CalculatorTool
import logging
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

# 配置日志记录器
logger = logging.getLogger(__name__)

# 创建日志目录
log_dir = os.path.join("logs", "manus")
os.makedirs(log_dir, exist_ok=True)

# 配置日志文件路径
log_file = os.path.join(log_dir, "manus.log")

# 创建 TimedRotatingFileHandler，按天轮转日志文件
file_handler = TimedRotatingFileHandler(
    log_file,
    when="midnight",
    interval=1,
    backupCount=30,  # 保留30天的日志
    encoding="utf-8"
)

# 设置日志格式
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
file_handler.setFormatter(formatter)

# 添加文件处理器到日志记录器
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)

def load_config() -> dict:
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.toml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return toml.load(f)
    except Exception as e:
        print(f"加载配置文件失败: {str(e)}")
        return {}

def main():
    """主函数"""
    # 加载配置
    config = load_config()
    
    # 初始化主智能体
    agent = ManusAgent(config)
    
    # 添加工具
    agent.add_tool(CalculatorTool(config))  # 先添加计算器工具
    agent.add_tool(PythonExecuteTool(config))
    agent.add_tool(BaiduSearchTool(config))
    agent.add_tool(FileManager(config))
    agent.add_tool(HTMLParserTool(config))
    
    # 初始化智能体
    agent.initialize()
    
    # 创建UI实例并运行
    ui = UI(config,agent)
    ui.run()

if __name__ == "__main__":
    main()
