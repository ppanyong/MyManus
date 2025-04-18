import unittest
from unittest.mock import patch, MagicMock
import json
from datetime import datetime, timedelta
import sys
import os
import requests

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.tool.weather_fetcher import WeatherFetcher

class TestWeatherFetcher(unittest.TestCase):
    def setUp(self):
        """测试前的准备工作"""
        self.config = {
            "test_mode": True  # 启用测试模式，使用内存数据库
        }
        self.fetcher = WeatherFetcher(self.config)
        
        # 测试数据
        self.test_locations = [
            {"name": "京都", "coordinates": (35.0116, 135.768)},
            {"name": "奈良公园", "coordinates": (34.6851, 135.805)}
        ]
        self.test_date_range = ("2024-04-20", "2024-04-21")
        
        # 模拟API响应数据
        self.mock_api_response = {
            "daily": {
                "weathercode": [0],
                "temperature_2m_max": [22.5],
                "temperature_2m_min": [15.2],
                "precipitation_probability_max": [15],
                "uv_index_max": [4]
            }
        }
        
    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.fetcher)
        self.assertEqual(self.fetcher.base_url, "https://api.open-meteo.com/v1/forecast")
        self.assertEqual(self.fetcher.cache_db, ":memory:")  # 测试模式下使用内存数据库
        self.assertEqual(self.fetcher.max_retries, 3)
        
    def test_weather_codes(self):
        """测试天气代码转换"""
        self.assertEqual(self.fetcher.weather_codes[0], "晴")
        self.assertEqual(self.fetcher.weather_codes[61], "小雨")
        self.assertEqual(self.fetcher.weather_codes[95], "雷雨")
        
    def test_uv_index_levels(self):
        """测试紫外线指数等级"""
        self.assertEqual(self.fetcher.uv_index_levels[(0, 2)], "低")
        self.assertEqual(self.fetcher.uv_index_levels[(3, 5)], "中")
        self.assertEqual(self.fetcher.uv_index_levels[(6, 7)], "高")
        self.assertEqual(self.fetcher.uv_index_levels[(8, 10)], "极高")
        
    @patch('requests.get')
    def test_get_weather_data(self, mock_get):
        """测试获取天气数据"""
        # 设置模拟响应
        mock_response = MagicMock()
        mock_response.json.return_value = self.mock_api_response
        mock_get.return_value = mock_response
        
        # 测试获取天气数据
        weather_data = self.fetcher._get_weather_data(
            self.test_locations[0],
            self.test_date_range[0]
        )
        
        # 验证结果
        self.assertIsNotNone(weather_data)
        self.assertEqual(weather_data["temp"], (15.2, 22.5))
        self.assertEqual(weather_data["condition"], "晴")
        self.assertEqual(weather_data["rain_prob"], 0.15)
        self.assertEqual(weather_data["uv_index"], 4)
        
    def test_get_sunrise_sunset(self):
        """测试日出日落时间计算"""
        sunrise, sunset = self.fetcher._get_sunrise_sunset(
            self.test_locations[0]["coordinates"],
            self.test_date_range[0]
        )
        
        # 验证时间格式
        self.assertRegex(sunrise, r"^\d{2}:\d{2}$")
        self.assertRegex(sunset, r"^\d{2}:\d{2}$")
        
    def test_generate_weather_summary(self):
        """测试天气简报生成"""
        # 创建测试数据
        test_data = {
            "京都": {
                "2024-04-20": {
                    "temp": (15, 22),
                    "condition": "晴",
                    "rain_prob": 0.15,
                    "uv_index": 4
                }
            }
        }
        
        summary = self.fetcher.generate_weather_summary(test_data)
        
        # 验证简报格式
        self.assertIn("☀️", summary)
        self.assertIn("2024-04-20", summary)
        self.assertIn("晴", summary)
        self.assertIn("22℃", summary)
        self.assertIn("15%", summary)
        
    def test_get_tool_description(self):
        """测试工具描述"""
        description = self.fetcher.get_tool_description()
        
        # 验证描述格式
        self.assertEqual(description["name"], "weather_fetcher")
        self.assertIn("获取指定地点", description["description"])
        self.assertIn("locations", description["parameters"]["properties"])
        self.assertIn("date_range", description["parameters"]["properties"])
        
    @patch('requests.get')
    def test_retry_mechanism(self, mock_get):
        """测试重试机制"""
        # 设置模拟响应，前两次失败，第三次成功
        mock_success_response = MagicMock()
        mock_success_response.json.return_value = self.mock_api_response
        mock_success_response.raise_for_status.return_value = None
        
        mock_get.side_effect = [
            requests.exceptions.RequestException("网络错误"),
            requests.exceptions.RequestException("超时"),
            mock_success_response
        ]
        
        # 测试获取天气数据
        weather_data = self.fetcher._get_weather_data(
            self.test_locations[0]["name"],
            self.test_date_range[0]
        )
        
        # 验证重试次数
        self.assertEqual(mock_get.call_count, 3)
        self.assertIsNotNone(weather_data)
        self.assertEqual(weather_data["condition"], "晴")
        
    def test_cache_mechanism(self):
        """测试缓存机制"""
        # 准备测试数据
        test_data = {
            "temp": (15, 22),
            "condition": "晴",
            "rain_prob": 0.15,
            "uv_index": 4
        }
        
        location_name = self.test_locations[0]["name"]
        test_date = self.test_date_range[0]
        
        # 保存到缓存
        self.fetcher._save_to_cache(
            location_name,
            test_date,
            test_data
        )
        
        # 从缓存获取
        cached_data = self.fetcher._get_cached_data(
            location_name,
            test_date
        )
        
        # 验证缓存数据
        self.assertIsNotNone(cached_data)
        self.assertEqual(cached_data["temp"], test_data["temp"])
        self.assertEqual(cached_data["condition"], test_data["condition"])
        
if __name__ == '__main__':
    unittest.main() 