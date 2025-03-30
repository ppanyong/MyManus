import os
import toml
from app.agent.manus import ManusAgent
from app.tool.python_execute import PythonExecuteTool
from app.tool.google_search import GoogleSearchTool
from app.ui import UI

def load_config():
    """加载配置文件"""
    config_path = os.path.join("config", "config.toml")
    with open(config_path, "r", encoding="utf-8") as f:
        return toml.load(f)

def main():
    """主函数"""
    # 加载配置
    config = load_config()
    
    # 初始化主智能体
    agent = ManusAgent(config)
    
    # 添加工具
    agent.add_tool(PythonExecuteTool(config))
    agent.add_tool(GoogleSearchTool(config))
    
    # 初始化智能体
    agent.initialize()
    
    # 启动UI界面
    ui = UI(agent)
    ui.run()
    # TODO: 实现命令行交互逻辑
    print("MyManus AI Assistant is ready!")

if __name__ == "__main__":
    main()
