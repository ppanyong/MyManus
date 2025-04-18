from typing import Dict, Any
import markdown2
import os
from app.tool.logger_tool import LoggerTool

# 初始化日志工具
logger_tool = LoggerTool()
logger = logger_tool.get_logger("MarkdownToHtmlTool")

class MarkdownToHtmlTool:
    """Markdown转HTML工具"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.css_style = """
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            h1, h2, h3, h4, h5, h6 {
                color: #2c3e50;
                margin-top: 24px;
                margin-bottom: 16px;
                font-weight: 600;
                line-height: 1.25;
            }
            h1 { font-size: 2em; }
            h2 { font-size: 1.5em; }
            h3 { font-size: 1.25em; }
            p { margin-bottom: 16px; }
            code {
                background-color: #f6f8fa;
                padding: 0.2em 0.4em;
                border-radius: 3px;
                font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            }
            pre {
                background-color: #f6f8fa;
                padding: 16px;
                border-radius: 3px;
                overflow: auto;
            }
            blockquote {
                margin: 0;
                padding: 0 1em;
                color: #6a737d;
                border-left: 0.25em solid #dfe2e5;
            }
            table {
                border-collapse: collapse;
                width: 100%;
                margin-bottom: 16px;
            }
            th, td {
                padding: 6px 13px;
                border: 1px solid #dfe2e5;
            }
            th {
                background-color: #f6f8fa;
            }
            img {
                max-width: 100%;
                box-sizing: border-box;
            }
        </style>
        """
        logger.info(f"初始化MarkdownToHtmlTool，配置: {config}")
        
    def convert(self, markdown_content: str, output_path: str = None) -> Dict[str, Any]:
        """将Markdown转换为HTML"""
        try:
            logger.info("开始转换Markdown为HTML")
            
            # 转换Markdown为HTML
            html_content = markdown2.markdown(
                markdown_content,
                extras=['fenced-code-blocks', 'tables', 'header-ids']
            )
            
            # 添加HTML头部和样式
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Markdown Document</title>
                {self.css_style}
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            
            # 如果指定了输出路径，则保存文件
            if output_path:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(full_html)
                logger.info(f"HTML文件已保存到: {output_path}")
            
            return {
                "status": "success",
                "html": full_html,
                "output_path": output_path,
                "error": ""
            }
            
        except Exception as e:
            error_msg = f"转换失败: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "html": None,
                "output_path": None,
                "error": error_msg
            }
    
    def get_tool_description(self) -> Dict[str, Any]:
        """返回工具描述，符合MCP协议"""
        logger.info("获取工具描述")
        return {
            "name": "markdown_to_html",
            "description": "Markdown转HTML工具，可以将Markdown内容转换为HTML并添加样式，需要明确指明输出路径，不接受模糊的路径，如果路径不存在，将存放在当前任务ID的文件夹中。",
            "functions": [
                {
                    "name": "convert",
                    "description": "将Markdown转换为HTML",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "markdown_content": {
                                "type": "string",
                                "description": "要转换的Markdown内容"
                            },
                            "output_path": {
                                "type": "string",
                                "description": "HTML文件的输出路径（可选）"
                            }
                        },
                        "required": ["markdown_content"]
                    },
                    "returns": {
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "enum": ["success", "error"]
                            },
                            "results": {
                                "type": "array",
                                "description": "转换结果列表",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "html": {
                                            "type": "string",
                                            "description": "生成的HTML内容"
                                        },
                                        "output_path": {
                                            "type": "string",
                                            "description": "HTML文件的输出路径"
                                        }
                                    }
                                }
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