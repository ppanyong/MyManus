import unittest
from app.tool.travel_budget_calculator import TravelBudgetCalculator

class TestTravelBudgetCalculator(unittest.TestCase):
    def setUp(self):
        """测试前的准备工作"""
        self.config = {}
        self.calculator = TravelBudgetCalculator(self.config)

    def test_calculate_daily_budget_success(self):
        """测试正常情况下的预算计算"""
        result = self.calculator.calculate_daily_budget(
            total_budget_min=1000,
            total_budget_max=2000,
            days=5
        )
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["daily_budget_min"], 200.0)
        self.assertEqual(result["daily_budget_max"], 400.0)
        self.assertIsNone(result["error"])

    def test_calculate_daily_budget_with_currency(self):
        """测试带货币单位的预算计算"""
        result = self.calculator.calculate_daily_budget(
            total_budget_min=1000,
            total_budget_max=2000,
            days=5,
            currency="美元"
        )
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["daily_budget_min"], 200.0)
        self.assertEqual(result["daily_budget_max"], 400.0)

    def test_calculate_daily_budget_invalid_days(self):
        """测试无效天数的错误处理"""
        result = self.calculator.calculate_daily_budget(
            total_budget_min=1000,
            total_budget_max=2000,
            days=0
        )
        
        self.assertEqual(result["status"], "error")
        self.assertIsNone(result["daily_budget_min"])
        self.assertIsNone(result["daily_budget_max"])
        self.assertIn("旅行天数必须大于0", result["error"])

    def test_calculate_daily_budget_invalid_budget(self):
        """测试无效预算的错误处理"""
        result = self.calculator.calculate_daily_budget(
            total_budget_min=-1000,
            total_budget_max=2000,
            days=5
        )
        
        self.assertEqual(result["status"], "error")
        self.assertIsNone(result["daily_budget_min"])
        self.assertIsNone(result["daily_budget_max"])
        self.assertIn("预算金额必须大于0", result["error"])

    def test_calculate_daily_budget_min_greater_than_max(self):
        """测试最小值大于最大值的错误处理"""
        result = self.calculator.calculate_daily_budget(
            total_budget_min=2000,
            total_budget_max=1000,
            days=5
        )
        
        self.assertEqual(result["status"], "error")
        self.assertIsNone(result["daily_budget_min"])
        self.assertIsNone(result["daily_budget_max"])
        self.assertIn("预算最小值不能大于最大值", result["error"])

if __name__ == '__main__':
    unittest.main() 