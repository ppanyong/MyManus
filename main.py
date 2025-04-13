import os
import toml
from app.agent.manus import ManusAgent
from app.tool.file_manager import FileManager
from app.tool.html_parser_tool import HTMLParserTool
from app.tool.python_execute import PythonExecuteTool
from app.tool.google_search import GoogleSearchTool
from app.tool.baidu_search import BaiduSearchTool
from app.tool.baidu_image_tool import BaiduImageTool
from app.tool.time_tool import TimeTool
from app.ui.ui import UI
from app.tool.calculator import CalculatorTool
from app.tool.logger_tool import LoggerTool
import logging

# 初始化日志工具
logger_tool = LoggerTool(log_dir=os.path.join("logs", "manus"))
logger = logger_tool.get_logger(__name__)

def load_config() -> dict:
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'myconfig.toml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return toml.load(f)
    except Exception as e:
        logger.error(f"加载配置文件失败: {str(e)}")
        return {}

def main():
    """主函数"""
    # 加载配置
    config = load_config()
    
    # 初始化主智能体
    agent = ManusAgent(config)
    logger.info(f"初始化主智能体: {agent}")
    # 添加工具
    agent.add_tool(CalculatorTool(config))  # 先添加计算器工具
    agent.add_tool(PythonExecuteTool(config))
    agent.add_tool(BaiduSearchTool(config))
    agent.add_tool(FileManager(config))
    agent.add_tool(HTMLParserTool(config))
    agent.add_tool(TimeTool(config))
    agent.add_tool(BaiduImageTool(config))
    
    # 初始化智能体
    agent.initialize()
    
    # 创建UI实例并运行
    ui = UI(config,agent)
    ui.run()

if __name__ == "__main__":
    main()
