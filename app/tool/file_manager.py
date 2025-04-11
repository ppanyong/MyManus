import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class FileManager:
    """文件管理工具类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化文件管理工具
        
        Args:
            config: 配置参数，可选
        """
        self.config = config or {}
        self.base_dir = self.config.get('base_dir', '')
    
    @staticmethod
    def get_tool_description() -> Dict[str, Any]:
        """获取工具描述"""
        return {
            "name": "FileManager",
            "description": "文件管理工具，用于创建、读取、写入和删除文件",
            "functions": [
                {
                    "name": "create_file",
                    "description": "创建一个新文件",
                    "parameters": {
                        "filename": {
                            "type": "string",
                            "description": "要创建的文件路径"
                        }
                    }
                },
                {
                    "name": "read_file",
                    "description": "读取文件内容",
                    "parameters": {
                        "filename": {
                            "type": "string",
                            "description": "要读取的文件路径"
                        }
                    }
                },
                {
                    "name": "write_file",
                    "description": "写入内容到文件",
                    "parameters": {
                        "filename": {
                            "type": "string",
                            "description": "要写入的文件路径"
                        },
                        "content": {
                            "type": "string",
                            "description": "要写入的内容"
                        }
                    }
                },
                {
                    "name": "delete_file",
                    "description": "删除文件",
                    "parameters": {
                        "filename": {
                            "type": "string",
                            "description": "要删除的文件路径"
                        }
                    }
                }
            ]
        }
    
    def _get_full_path(self, filename: str) -> str:
        """获取完整的文件路径
        
        Args:
            filename: 相对路径
            
        Returns:
            str: 完整的文件路径
        """
        if self.base_dir:
            return os.path.join(self.base_dir, filename)
        return filename
    
    def create_file(self, filename: str) -> Dict[str, Any]:
        """创建新文件
        
        Args:
            filename: 文件路径
            
        Returns:
            Dict[str, Any]: 操作结果
        """
        try:
            full_path = self._get_full_path(filename)
            
            # 检查文件是否已存在
            if os.path.exists(full_path):
                return {
                    "status": "error",
                    "error": f"文件已存在: {full_path}"
                }
            
            # 确保目录存在
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # 创建文件
            with open(full_path, 'w', encoding='utf-8') as f:
                pass
                
            return {
                "status": "success",
                "message": f"文件创建成功: {full_path}"
            }
        except Exception as e:
            logger.error(f"创建文件失败: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def read_file(self, filename: str) -> Dict[str, Any]:
        """读取文件内容
        
        Args:
            filename: 文件路径
            
        Returns:
            Dict[str, Any]: 操作结果
        """
        try:
            full_path = self._get_full_path(filename)
            
            if not os.path.exists(full_path):
                return {
                    "status": "error",
                    "error": f"文件不存在: {full_path}"
                }
                
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            return {
                "status": "success",
                "content": content
            }
        except Exception as e:
            logger.error(f"读取文件失败: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def write_file(self, filename: str, content: str) -> Dict[str, Any]:
        """写入内容到文件
        
        Args:
            filename: 文件路径
            content: 要写入的内容
            
        Returns:
            Dict[str, Any]: 操作结果
        """
        try:
            full_path = self._get_full_path(filename)
            
            # 确保目录存在
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            return {
                "status": "success",
                "message": f"文件写入成功: {full_path}"
            }
        except Exception as e:
            logger.error(f"写入文件失败: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def delete_file(self, filename: str) -> Dict[str, Any]:
        """删除文件
        
        Args:
            filename: 文件路径
            
        Returns:
            Dict[str, Any]: 操作结果
        """
        try:
            full_path = self._get_full_path(filename)
            
            if not os.path.exists(full_path):
                return {
                    "status": "error",
                    "error": f"文件不存在: {full_path}"
                }
                
            os.remove(full_path)
            return {
                "status": "success",
                "message": f"文件删除成功: {full_path}"
            }
        except Exception as e:
            logger.error(f"删除文件失败: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            } 