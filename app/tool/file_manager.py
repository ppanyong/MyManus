import os
from typing import Dict, Any, Optional
import requests
from app.tool.logger_tool import LoggerTool

# 初始化日志工具
logger_tool = LoggerTool()
logger = logger_tool.get_logger("FileManager")

class FileManager:
    """文件管理工具类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化文件管理工具
        
        Args:
            config: 配置参数，可选
        """
        self.config = config or {}
        self.base_dir = self.config.get('base_dir', '')
        logger.info(f"初始化FileManager，配置: {config}")
    
    @staticmethod
    def get_tool_description() -> Dict[str, Any]:
        """获取工具描述"""
        logger.info("获取工具描述")
        return {
            "name": "FileManager",
            "description": "文件管理工具，用于创建、读取、写入和删除文件",
            "functions": [
                {
                    "name": "create_file",
                    "description": "创建一个新文件",
                    "parameters": {
                        "path": {
                            "type": "string",
                            "description": "文件所在的目录路径，必须明确指定"
                        },
                        "filename": {
                            "type": "string",
                            "description": "要创建的文件名"
                        }
                    },
                    "returns": {
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "enum": ["success", "error"]
                            },
                            "result": {
                                "type": "string",
                                "description": "操作结果描述"
                            },
                            "error": {
                                "type": "string",
                                "description": "错误信息"
                            }
                        }
                    }
                },
                {
                    "name": "read_file",
                    "description": "读取文件内容",
                    "parameters": {
                        "path": {
                            "type": "string",
                            "description": "文件所在的目录路径，必须明确指定"
                        },
                        "filename": {
                            "type": "string",
                            "description": "要读取的文件名"
                        }
                    },
                    "returns": {
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "enum": ["success", "error"]
                            },
                            "result": {
                                "type": "string",
                                "description": "文件内容"
                            },
                            "error": {
                                "type": "string",
                                "description": "错误信息"
                            }
                        }
                    }
                },
                {
                    "name": "write_file",
                    "description": "写入内容到文件",
                    "parameters": {
                        "path": {
                            "type": "string",
                            "description": "文件所在的目录路径，必须明确指定"
                        },
                        "filename": {
                            "type": "string",
                            "description": "要写入的文件名"
                        },
                        "content": {
                            "type": "string",
                            "description": "要写入的内容"
                        }
                    },
                    "returns": {
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "enum": ["success", "error"]
                            },
                            "result": {
                                "type": "string",
                                "description": "操作结果描述"
                            },
                            "error": {
                                "type": "string",
                                "description": "错误信息"
                            }
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
                    },
                    "returns": {
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "enum": ["success", "error"]
                            },
                            "result": {
                                "type": "string",
                                "description": "操作结果描述"
                            },
                            "error": {
                                "type": "string",
                                "description": "错误信息"
                            }
                        }
                    }
                },
                {
                    "name": "download",
                    "description": "下载文件",
                    "parameters": {
                        "url": {
                            "type": "string",
                            "description": "要下载的文件URL"
                        },
                        "save_path": {
                            "type": "string",
                            "description": "文件保存路径"
                        }
                    },
                    "returns": {
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "enum": ["success", "error"]
                            },
                            "result": {
                                "type": "string",
                                "description": "操作结果描述"
                            },
                            "error": {
                                "type": "string",
                                "description": "错误信息"
                            }
                        }
                    }
                },
                {
                    "name": "create_directory",
                    "description": "创建一个新目录",
                    "parameters": {
                        "directory": {
                            "type": "string",
                            "description": "要创建的目录路径，如果不指定则在项目根目录的temp目录下创建"
                        }
                    },
                    "returns": {
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "enum": ["success", "error"]
                            },
                            "result": {
                                "type": "string",
                                "description": "操作结果描述"
                            },
                            "error": {
                                "type": "string",
                                "description": "错误信息"
                            }
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
    
    def create_file(self, path: str, filename: str) -> Dict[str, Any]:
        """创建新文件
        
        Args:
            path: 文件所在的目录路径
            filename: 文件名
            
        Returns:
            Dict[str, Any]: 操作结果
        """
        try:
            # 组合完整路径
            full_path = os.path.join(path, filename)
            full_path = self._get_full_path(full_path)
            logger.info(f"尝试创建文件: {full_path}")
            
            # 检查文件是否已存在
            if os.path.exists(full_path):
                error_msg = f"文件已存在: {full_path}"
                logger.warning(error_msg)
                return {
                    "status": "error",
                    "error": error_msg
                }
            
            # 确保目录存在
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # 创建文件
            with open(full_path, 'w', encoding='utf-8') as f:
                pass
                
            logger.info(f"文件创建成功: {full_path}")
            return {
                "status": "success",
                "result": f"文件创建成功: {full_path}"
            }
        except Exception as e:
            error_msg = f"创建文件失败: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg
            }
    
    def read_file(self, path: str, filename: str) -> Dict[str, Any]:
        """读取文件内容
        
        Args:
            path: 文件所在的目录路径
            filename: 要读取的文件名
            
        Returns:
            Dict[str, Any]: 操作结果
        """
        try:
            full_path = os.path.join(path, filename)
            full_path = self._get_full_path(full_path)
            logger.info(f"尝试读取文件: {full_path}")
            
            if not os.path.exists(full_path):
                error_msg = f"文件不存在: {full_path}"
                logger.warning(error_msg)
                return {
                    "status": "error",
                    "error": error_msg
                }
                
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            logger.info(f"文件读取成功: {full_path}")
            return {
                "status": "success",
                "result": content
            }
        except Exception as e:
            error_msg = f"读取文件失败: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg
            }
    
    def write_file(self, path: str, filename: str, content: str) -> Dict[str, Any]:
        """写入内容到文件
        
        Args:
            path: 文件所在的目录路径
            filename: 文件名
            content: 要写入的内容
            
        Returns:
            Dict[str, Any]: 操作结果
        """
        try:
            # 组合完整路径
            full_path = os.path.join(path, filename)
            full_path = self._get_full_path(full_path)
            logger.info(f"尝试写入文件: {full_path}")
            
            # 确保目录存在
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            logger.info(f"文件写入成功: {full_path}")
            return {
                "status": "success",
                "result": f"文件写入成功: {full_path}"
            }
        except Exception as e:
            error_msg = f"写入文件失败: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg
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
            logger.info(f"尝试删除文件: {full_path}")
            
            if not os.path.exists(full_path):
                error_msg = f"文件不存在: {full_path}"
                logger.warning(error_msg)
                return {
                    "status": "error",
                    "error": error_msg
                }
                
            os.remove(full_path)
            logger.info(f"文件删除成功: {full_path}")
            return {
                "status": "success",
                "result": f"文件删除成功: {full_path}"
            }
        except Exception as e:
            error_msg = f"删除文件失败: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg
            }
    
    def download(self, url: str, save_path: str) -> Dict[str, Any]:
        """下载文件
        
        Args:
            url: 文件URL
            save_path: 文件保存路径
            
        Returns:
            Dict[str, Any]: 操作结果
        """
        try:
            full_path = self._get_full_path(save_path)
            logger.info(f"尝试下载文件: {url} 到 {full_path}")
            
            # 确保目录存在
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # 下载文件
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # 写入文件
            with open(full_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        
            logger.info(f"文件下载成功: {full_path}")
            return {
                "status": "success",
                "result": f"文件下载成功: {full_path}"
            }
        except requests.exceptions.RequestException as e:
            error_msg = f"下载文件失败: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"下载文件失败: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg
            }
    
    def create_directory(self, directory: Optional[str] = None) -> Dict[str, Any]:
        """创建新目录
        
        Args:
            directory: 目录路径，如果不指定则在项目根目录的temp目录下创建
            
        Returns:
            Dict[str, Any]: 操作结果
        """
        try:
            if directory is None:
                directory = os.path.join(self.base_dir, 'temp')
            
            full_path = self._get_full_path(directory)
            logger.info(f"尝试创建目录: {full_path}")
            
            # 检查目录是否已存在
            if os.path.exists(full_path):
                error_msg = f"目录已存在: {full_path}"
                logger.warning(error_msg)
                return {
                    "status": "error",
                    "error": error_msg
                }
            
            # 创建目录
            os.makedirs(full_path)
                
            logger.info(f"目录创建成功: {full_path}")
            return {
                "status": "success",
                "result": f"目录创建成功: {full_path}"
            }
        except Exception as e:
            error_msg = f"创建目录失败: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg
            } 