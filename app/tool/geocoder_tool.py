import googlemaps
from datetime import datetime, timedelta
import sqlite3
import time
from typing import Dict, Tuple, List
import logging

class Geocoder:
    def __init__(self, config: Dict):
        """
        初始化地理编码器
        :param config: 配置字典，包含 Google Maps API key
        """
        api_key = config.get("google_maps", {}).get("api_key", "")
        self.client = googlemaps.Client(key=api_key)
        self.cache_db = "geo_cache.db"
        self._init_cache_db()
        self.logger = logging.getLogger(__name__)

    def get_tool_description(self) -> Dict:
        """
        返回工具的描述信息，符合MCP规范
        :return: 包含工具描述信息的字典
        """
        return {
            "name": "geocoder",
            "description": "将地点名称转换为经纬度坐标的地理编码工具",
            "parameters": {
                "type": "object",
                "properties": {
                    "location_names": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "需要转换的地点名称列表"
                    }
                },
                "required": ["location_names"]
            },
            "returns": {
                "type": "object",
                "description": "地点名称与经纬度坐标的映射字典"
            }
        }

    def _init_cache_db(self):
        """初始化SQLite缓存数据库"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS geocache (
                location_name TEXT PRIMARY KEY,
                latitude REAL,
                longitude REAL,
                timestamp DATETIME
            )
        ''')
        conn.commit()
        conn.close()

    def _get_from_cache(self, location_name: str) -> Tuple[float, float] or None:
        """从缓存中获取位置信息"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT latitude, longitude, timestamp 
            FROM geocache 
            WHERE location_name = ?
        ''', (location_name,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            lat, lng, timestamp = result
            cache_time = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            if datetime.now() - cache_time < timedelta(days=7):
                return (lat, lng)
        return None

    def _save_to_cache(self, location_name: str, coordinates: Tuple[float, float]):
        """将位置信息保存到缓存"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO geocache 
            (location_name, latitude, longitude, timestamp) 
            VALUES (?, ?, ?, ?)
        ''', (location_name, coordinates[0], coordinates[1], datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        conn.commit()
        conn.close()

    def geocode(self, location_names: List[str] = None, addresses: List[str] = None) -> Dict[str, Tuple[float, float]]:
        """
        将地点名称转换为经纬度坐标
        :param location_names: 地点名称列表
        :param addresses: 地址列表（与 location_names 参数二选一）
        :return: 地点名称与经纬度字典
        """
        # 确定使用哪个参数
        if location_names is None and addresses is None:
            raise ValueError("必须提供 location_names 或 addresses 参数")
        if location_names is not None and addresses is not None:
            raise ValueError("不能同时提供 location_names 和 addresses 参数")
            
        # 使用提供的参数
        locations = location_names if location_names is not None else addresses
        results = {}
        
        for location in locations:
            try:
                # 首先检查缓存
                cached_result = self._get_from_cache(location)
                if cached_result:
                    results[location] = cached_result
                    continue
                
                # 调用Google Maps API
                geocode_result = self.client.geocode(location)
                
                if not geocode_result:
                    self.logger.warning(f"未找到位置: {location}")
                    continue
                
                # 提取第一个结果的经纬度
                location_data = geocode_result[0]['geometry']['location']
                coordinates = (location_data['lat'], location_data['lng'])
                
                # 保存到缓存
                self._save_to_cache(location, coordinates)
                results[location] = coordinates
                
                # 添加延迟以避免API限速
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"处理位置 {location} 时出错: {str(e)}")
                continue
        
        return results 