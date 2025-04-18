from typing import Dict, List, Tuple, Any, Union
import requests
import sqlite3
from datetime import datetime, timedelta
import time
from astral import LocationInfo
from astral.sun import sun
import json
import os
from app.tool.logger_tool import LoggerTool

# 初始化日志工具
logger_tool = LoggerTool()
logger = logger_tool.get_logger("WeatherFetcher")

class WeatherFetcher:
    """天气数据获取工具
    
    用于获取指定地点在特定日期范围内的天气预报数据，包括温度、天气状况、降水概率、
    紫外线指数以及日出日落时间等信息。
    
    特点:
    - 使用Open-Meteo免费API
    - 支持多地点查询
    - 自动计算日出日落时间
    - 本地SQLite缓存
    - 日语天气描述
    - 网络异常自动重试
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        # 如果是测试环境，使用内存数据库
        self.test_mode = config.get("test_mode", False)
        self.cache_db = ":memory:" if self.test_mode else config.get("cache_db", "weather_cache.db")
        self.max_retries = 3
        self.retry_delay = 1  # 秒
        self.api_key = config.get("api_key", "")  # Open-Meteo 实际上不需要 API key
        
        # 在测试模式下保持同一个数据库连接
        self.db_connection = None if not self.test_mode else sqlite3.connect(self.cache_db)
        
        # 初始化数据库
        self._init_db()
        
        # WMO天气代码转换表（日语版）
        self.weather_codes = {
            0: "晴",
            1: "薄曇",
            2: "曇り",
            3: "薄霧",
            45: "霧",
            48: "霧氷",
            51: "霧雨",
            53: "霧雨",
            55: "霧雨",
            56: "凍る霧雨",
            57: "凍る霧雨",
            61: "小雨",
            63: "雨",
            65: "大雨",
            66: "凍る雨",
            67: "凍る雨",
            71: "小雪",
            73: "雪",
            75: "大雪",
            77: "雪粒",
            80: "にわか雨",
            81: "にわか雨",
            82: "にわか雨",
            85: "にわか雪",
            86: "にわか雪",
            95: "雷雨",
            96: "雷雨",
            99: "雷雨"
        }
        
        # 紫外线指数等级说明
        self.uv_index_levels = {
            (0, 2): "低",
            (3, 5): "中",
            (6, 7): "高",
            (8, 10): "极高"
        }
        
    def _init_db(self):
        """初始化SQLite数据库"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 如果不是内存数据库，确保数据库目录存在
                if not self.test_mode:
                    db_dir = os.path.dirname(os.path.abspath(self.cache_db))
                    if db_dir and not os.path.exists(db_dir):
                        os.makedirs(db_dir)
                        
                    # 如果数据库文件存在且损坏，先删除它
                    if os.path.exists(self.cache_db):
                        try:
                            # 尝试打开数据库文件检查是否损坏
                            test_conn = sqlite3.connect(self.cache_db)
                            test_conn.execute("SELECT 1")
                            test_conn.close()
                        except sqlite3.DatabaseError:
                            try:
                                os.remove(self.cache_db)
                                logger.info("已删除损坏的数据库文件")
                            except Exception as e:
                                logger.error(f"删除损坏的数据库文件失败: {str(e)}")
                                continue
                
                # 创建新的数据库连接
                conn = self._get_db_connection()
                try:
                    conn.execute('''
                        CREATE TABLE IF NOT EXISTS weather_cache (
                            location TEXT,
                            date TEXT,
                            data TEXT,
                            timestamp INTEGER,
                            PRIMARY KEY (location, date)
                        )
                    ''')
                    conn.commit()
                    logger.info("天气缓存数据库初始化成功")
                    return True
                finally:
                    if not self.test_mode:
                        conn.close()
                
            except Exception as e:
                logger.error(f"初始化数据库时出错 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if not self.test_mode:
                    try:
                        if os.path.exists(self.cache_db):
                            os.remove(self.cache_db)
                    except Exception as e2:
                        logger.error(f"删除损坏的数据库文件失败: {str(e2)}")
                        
                if attempt == max_retries - 1:
                    raise sqlite3.DatabaseError("无法初始化数据库")
                    
                time.sleep(0.5)  # 增加重试延迟
                
        return False
            
    def _get_cached_data(self, location: str, date: str) -> Dict[str, Any]:
        """从缓存中获取天气数据"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                logger.debug(f"尝试从缓存获取数据: {location}, {date}")
                cursor.execute(
                    "SELECT data FROM weather_cache WHERE location = ? AND date = ?",
                    (location, date)
                )
                result = cursor.fetchone()
                
            if result:
                logger.debug(f"找到缓存数据: {result[0]}")
                data = json.loads(result[0])
                # 转换回元组
                if "temp" in data and isinstance(data["temp"], list):
                    data["temp"] = tuple(data["temp"])
                return data
            logger.debug("未找到缓存数据")
            return None
        except Exception as e:
            logger.error(f"获取缓存数据时出错: {str(e)}")
            return None
            
    def _save_to_cache(self, location: str, date: str, data: Dict[str, Any]):
        """保存天气数据到缓存"""
        try:
            # 转换数据以确保可以正确序列化
            cache_data = data.copy()
            if "temp" in cache_data and isinstance(cache_data["temp"], tuple):
                cache_data["temp"] = list(cache_data["temp"])
                
            json_data = json.dumps(cache_data)
            logger.debug(f"准备缓存数据: {location}, {date}, {json_data}")
            
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO weather_cache (location, date, data, timestamp) VALUES (?, ?, ?, ?)",
                    (location, date, json_data, int(time.time()))
                )
                conn.commit()
                
                # 验证数据是否成功保存
                cursor.execute(
                    "SELECT data FROM weather_cache WHERE location = ? AND date = ?",
                    (location, date)
                )
                result = cursor.fetchone()
                if result:
                    logger.debug(f"数据成功缓存: {result[0]}")
                else:
                    logger.error("数据缓存失败")
                    
        except Exception as e:
            logger.error(f"保存缓存数据时出错: {str(e)}")
            
    def _get_sunrise_sunset(self, coordinates: Tuple[float, float], date: str) -> Tuple[str, str]:
        """计算指定地点的日出日落时间"""
        try:
            lat, lon = coordinates
            
            # 验证坐标有效性
            if not (-90 <= lat <= 90):
                raise ValueError(f"无效的纬度值: {lat}")
            if not (-180 <= lon <= 180):
                raise ValueError(f"无效的经度值: {lon}")
                
            location = LocationInfo("", "", "Asia/Tokyo", lat, lon)
            s = sun(location.observer, date=datetime.strptime(date, "%Y-%m-%d").date())
            sunrise = s["sunrise"].strftime("%H:%M")
            sunset = s["sunset"].strftime("%H:%M")
            return sunrise, sunset
        except Exception as e:
            logger.error(f"计算日出日落时间时出错: {str(e)}")
            if isinstance(e, ValueError):
                raise
            return "05:00", "18:00"  # 默认值
            
    def _get_weather_data(self, location: str, date: str) -> Dict:
        """获取天气数据，优先使用缓存"""
        # 检查缓存
        cached_data = self._get_cached_data(location, date)
        if cached_data:
            return cached_data
            
        # 如果没有缓存，从API获取
        max_retries = 3
        retry_delay = 1  # 初始重试延迟（秒）
        
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    self.base_url,
                    params={
                        "latitude": "35.0116",  # 默认使用京都坐标
                        "longitude": "135.768",
                        "daily": ["weathercode", "temperature_2m_max", "temperature_2m_min", 
                                 "precipitation_probability_max", "uv_index_max"],
                        "timezone": "Asia/Tokyo"
                    },
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()
                
                # 处理API响应数据
                processed_data = {
                    "temp": (
                        data["daily"]["temperature_2m_min"][0],
                        data["daily"]["temperature_2m_max"][0]
                    ),
                    "condition": self.weather_codes.get(
                        data["daily"]["weathercode"][0], "不明"
                    ),
                    "rain_prob": data["daily"]["precipitation_probability_max"][0] / 100,
                    "uv_index": data["daily"]["uv_index_max"][0]
                }
                
                # 计算日出日落时间
                sunrise, sunset = self._get_sunrise_sunset((35.0116, 135.768), date)
                processed_data["sunrise"] = sunrise
                processed_data["sunset"] = sunset
                
                # 缓存数据
                self._save_to_cache(location, date, processed_data)
                return processed_data
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"获取天气数据失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))  # 指数退避
                else:
                    logger.error(f"获取天气数据失败，已达到最大重试次数: {str(e)}")
                    raise
                    
        raise Exception("获取天气数据失败，已达到最大重试次数")
        
    def get_weather_report(self, locations: List[Union[str, Dict[str, Any]]], date_range: Tuple[str, str]) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """获取指定地点在日期范围内的天气报告
        
        Args:
            locations: 地点列表，可以是字符串列表或包含name和coordinates的字典列表
            date_range: 日期范围 [开始日期, 结束日期]
            
        Returns:
            包含天气数据的字典
        """
        result = {}
        start_date = datetime.strptime(date_range[0], "%Y-%m-%d")
        end_date = datetime.strptime(date_range[1], "%Y-%m-%d")
        
        for location in locations:
            # 处理两种输入格式
            if isinstance(location, str):
                location_name = location
            else:
                location_name = location["name"]
                
            result[location_name] = {}
            
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime("%Y-%m-%d")
                result[location_name][date_str] = self._get_weather_data(location_name, date_str)
                current_date += timedelta(days=1)
                
        return {
            "status": "success",
            "result": result,
            "error": None
        }
        
    def generate_weather_summary(self, weather_data: Dict[str, Dict[str, Dict[str, Any]]]) -> Dict[str, Any]:
        """生成天气简报markdown文本"""
        try:
            # 检查输入数据类型
            if not isinstance(weather_data, dict):
                return {
                    "status": "error",
                    "result": None,
                    "error": f"输入数据类型错误，期望字典类型，实际类型: {type(weather_data)}"
                }
                
            summary = []
            for location, dates in weather_data.items():
                if not isinstance(dates, dict):
                    continue
                for date, data in dates.items():
                    if not isinstance(data, dict):
                        continue
                    # 选择天气emoji
                    emoji = "☀️" if "晴" in data.get("condition", "") else \
                            "⛅" if "曇" in data.get("condition", "") else \
                            "🌧️" if "雨" in data.get("condition", "") else \
                            "❄️" if "雪" in data.get("condition", "") else \
                            "⛈️" if "雷" in data.get("condition", "") else "🌤️"
                            
                    summary.append(
                        f"{emoji} {date} {data.get('condition', '不明')} | "
                        f"最高{data.get('temp', (0, 0))[1]}℃ | "
                        f"降水概率{int(data.get('rain_prob', 0)*100)}%"
                    )
            return {
                "status": "success",
                "result": "\n".join(summary),
                "error": None
            }
        except Exception as e:
            return {
                "status": "error",
                "result": None,
                "error": str(e)
            }
        
    def get_tool_description(self) -> Dict[str, Any]:
        """获取工具描述（符合MCP规范）"""
        return {
            "name": "weather_fetcher",
            "description": "天气数据获取工具，用于获取指定地点在特定日期范围内的天气预报数据，需要明确指明清晰的年月日，不接受模糊的日期，包括温度、天气状况、降水概率、紫外线指数以及日出日落时间等信息。支持多地点查询，使用Open-Meteo API，具有本地缓存功能。",
            "functions": [
                {
                    "name": "get_weather_report",
                    "description": "获取指定地点在日期范围内的天气报告",
                    "parameters": {
                        "locations": {
                            "type": "array",
                            "description": "要查询的地点列表，可以是字符串列表（如 ['东京', '京都']）或包含name和coordinates的字典列表",
                            "items": {
                                "oneOf": [
                                    {
                                        "type": "string",
                                        "description": "地点名称"
                                    },
                                    {
                                        "type": "object",
                                        "properties": {
                                            "name": {
                                                "type": "string",
                                                "description": "地点名称"
                                            },
                                            "coordinates": {
                                                "type": "array",
                                                "description": "经纬度坐标 [纬度, 经度]",
                                                "items": {"type": "number"},
                                                "minItems": 2,
                                                "maxItems": 2
                                            }
                                        },
                                        "required": ["name", "coordinates"]
                                    }
                                ]
                            }
                        },
                        "date_range": {
                            "type": "array",
                            "description": "查询的日期范围 [开始日期, 结束日期]，格式为YYYY-MM-DD",
                            "items": {"type": "string"},
                            "minItems": 2,
                            "maxItems": 2
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
                                "type": "object",
                                "description": "天气数据结果"
                            },
                            "error": {
                                "type": "string",
                                "description": "错误信息"
                            }
                        }
                    }
                },
                {
                    "name": "generate_weather_summary",
                    "description": "生成天气简报markdown文本",
                    "parameters": {
                        "weather_data": {
                            "type": "object",
                            "description": "天气数据字典，包含地点、日期和天气信息"
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
                                "description": "天气简报markdown文本"
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
        
    def __del__(self):
        """析构函数，确保关闭数据库连接"""
        if self.db_connection:
            try:
                self.db_connection.close()
            except Exception:
                pass
                
    def _get_db_connection(self):
        """获取数据库连接"""
        if self.test_mode and self.db_connection:
            return self.db_connection
            
        try:
            conn = sqlite3.connect(self.cache_db)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            logger.error(f"获取数据库连接失败: {str(e)}")
            raise 