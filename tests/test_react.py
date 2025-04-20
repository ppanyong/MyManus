import unittest
from app.flow.react import ReactFlow

class TestReactFlow(unittest.TestCase):
    def setUp(self):
        self.flow = ReactFlow({})
        
    def test_process_step_reference(self):
        # 测试用例1：基本步骤引用
        step_results = {
            "step_1_result": {"status": "success", "result": {"name": "test", "value": 123}, "error": None}
        }
        value = "{step_1_result}"
        expected = str(step_results["step_1_result"])
        result = self.flow._process_step_reference(value, step_results, "test_request")
        self.assertEqual(result, expected)
        
        # 测试用例2：带方括号的引用
        value = "{step_1_result['result']['name']}"
        expected = "test"
        result = self.flow._process_step_reference(value, step_results, "test_request")
        self.assertEqual(result, expected)
        
        # 测试用例3：带点号的引用
        value = "{step_1_result.result.value}"
        expected = "123"
        result = self.flow._process_step_reference(value, step_results, "test_request")
        self.assertEqual(result, expected)
        
        # 测试用例4：嵌套引用
        step_results = {
            "step_1_result": {
                "status": "success",
                "result": {
                    "data": {
                        "info": {
                            "name": "nested"
                        }
                    }
                },
                "error": None
            }
        }
        value = "{step_1_result.result.data.info.name}"
        expected = "nested"
        result = self.flow._process_step_reference(value, step_results, "test_request")
        self.assertEqual(result, expected)
        
        # 测试用例5：不存在的步骤引用
        value = "{step_2_result}"
        expected = "{step_2_result}"
        result = self.flow._process_step_reference(value, step_results, "test_request")
        self.assertEqual(result, expected)
        
        # 测试用例6：多层嵌套键值（日期相关）
        step_results = {
            "step_1_result": {
                "status": "success",
                "result": {
                    "date": {
                        "year": "2025",
                        "month": "04",
                        "day": "19"
                    }
                },
                "error": None
            }
        }
        value = "{step_1_result.result.date.year}"
        expected = "2025"
        result = self.flow._process_step_reference(value, step_results, "test_request")
        self.assertEqual(result, expected)
        
        # 测试用例7：多层嵌套键值（列表中的字典）
        step_results = {
            "step_1_result": {
                "status": "success",
                "result": [
                    {
                        "date": {
                            "year": "2025",
                            "month": "04"
                        }
                    }
                ],
                "error": None
            }
        }
        value = "{step_1_result.result[0].date.year}"
        expected = "2025"
        result = self.flow._process_step_reference(value, step_results, "test_request")
        self.assertEqual(result, expected)
        
        # 测试用例8：多层嵌套键值（带数组索引）
        step_results = {
            "step_1_result": {
                "status": "success",
                "result": {
                    "dates": [
                        {"year": "2024"},
                        {"year": "2025"}
                    ]
                },
                "error": None
            }
        }
        value = "{step_1_result.result.dates[1].year}"
        expected = "2025"
        result = self.flow._process_step_reference(value, step_results, "test_request")
        self.assertEqual(result, expected)
        
        # 测试用例9：多层嵌套键值（复杂结构）
        step_results = {
            "step_1_result": {
                "status": "success",
                "result": {
                    "data": {
                        "dates": [
                            {
                                "info": {
                                    "year": "2025",
                                    "month": "04"
                                }
                            }
                        ]
                    }
                },
                "error": None
            }
        }
        value = "{step_1_result.result.data.dates[0].info.year}"
        expected = "2025"
        result = self.flow._process_step_reference(value, step_results, "test_request")
        self.assertEqual(result, expected)

    def test_process_step_reference_date(self):
        # 测试用例：多层嵌套键值（日期相关）
        step_results = {
            "step_1_result": {
                "status": "success",
                "result": {
                    "date": {
                        "year": "2025",
                        "month": "04",
                        "day": "19"
                    }
                },
                "error": None
            }
        }
        value = "{step_1_result.result.date.year}"
        expected = "2025"
        result = self.flow._process_step_reference(value, step_results, "test_request")
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main() 