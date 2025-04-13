import os
import logging
import json
from logging.handlers import TimedRotatingFileHandler
from typing import Optional

class JSONFormatter(logging.Formatter):
    """自定义格式化器，用于美化JSON字符串的显示"""
    
    def format(self, record):
        # 获取原始消息
        message = record.getMessage()
        
        try:
            # 尝试将消息解析为JSON
            json_obj = json.loads(message)
            # 将JSON对象格式化为美观的字符串
            formatted_json = json.dumps(json_obj, indent=2, ensure_ascii=False)
            # 替换原始消息
            record.msg = formatted_json
        except (json.JSONDecodeError, TypeError):
            # 如果不是JSON字符串，保持原样
            pass
            
        return super().format(record)

class LoggerTool:
    """通用日志工具类，用于创建和管理日志记录器"""
    
    def __init__(self, log_dir: str = "logs", backup_count: int = 30):
        """
        初始化日志工具类
        
        Args:
            log_dir: 日志文件存储目录
            backup_count: 保留的日志文件数量
        """
        self.log_dir = log_dir
        self.backup_count = backup_count
        self._ensure_log_dir()
    
    def _ensure_log_dir(self):
        """确保日志目录存在"""
        os.makedirs(self.log_dir, exist_ok=True)
    
    def get_logger(self, name: str, level: int = logging.INFO) -> logging.Logger:
        """
        获取指定名称的日志记录器
        
        Args:
            name: 日志记录器名称，通常使用类名
            level: 日志级别，默认为INFO
            
        Returns:
            logging.Logger: 配置好的日志记录器
        """
        logger = logging.getLogger(name)
        
        # 如果已经配置过处理器，直接返回
        if logger.handlers:
            return logger
            
        # 设置日志级别
        logger.setLevel(level)
        
        # 配置日志文件路径
        log_file = os.path.join(self.log_dir, f"{name}.log")
        
        # 创建文件处理器
        file_handler = TimedRotatingFileHandler(
            log_file,
            when="midnight",
            interval=1,
            backupCount=self.backup_count,
            encoding="utf-8"
        )
        
        # 设置日志格式
        formatter = JSONFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        
        # 添加处理器到日志记录器
        logger.addHandler(file_handler)
        
        return logger 