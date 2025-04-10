import unittest
import asyncio
from unittest.mock import MagicMock, patch
import json
import os
import toml
from app.agent.manus import ManusAgent
from app.flow.planning import PlanningFlow
from app.flow.react import ReactFlow

class TestManusAgent(unittest.TestCase):
    """测试ManusAgent类的主要功能"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 从config.toml中读取配置
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.toml')
        self.config = toml.load(config_path)
        
        # 创建ManusAgent实例
        self.agent = ManusAgent(self.config)
        
        # 创建模拟的UI对象
        self.mock_ui = MagicMock()
        # 使用set_ui方法设置UI实例
        self.agent.set_ui(self.mock_ui)
        
    def test_initialization(self):
        """测试初始化方法"""
        # 使用patch模拟PlanningFlow的initialize方法
        with patch.object(PlanningFlow, 'initialize', return_value={
            "status": "success",
            "result": "规划流程初始化成功",
            "error": None
        }):
            # 调用初始化方法
            result = self.agent.initialize()
            
            # 验证结果
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["result"], "主智能体初始化成功")
            self.assertIsNone(result["error"])
            
    def test_initialization_failure(self):
        """测试初始化失败的情况"""
        # 使用patch模拟PlanningFlow的initialize方法返回错误
        with patch.object(PlanningFlow, 'initialize', return_value={
            "status": "error",
            "result": None,
            "error": "规划流程初始化失败"
        }):
            # 调用初始化方法
            result = self.agent.initialize()
            
            # 验证结果
            self.assertEqual(result["status"], "error")
            self.assertIsNone(result["result"])
            self.assertEqual(result["error"], "规划流程初始化失败")
            
    def test_update_task_list(self):
        """测试更新任务列表方法"""
        # 创建测试任务列表
        tasks = [
            {"id": 1, "description": "任务1"},
            {"id": 2, "description": "任务2"}
        ]
        
        # 调用更新任务列表方法
        self.agent._update_task_list(tasks)
        
        # 验证UI实例的update_tasks_ui方法被调用
        self.mock_ui.update_tasks_ui.assert_called_once_with(tasks)
        
    def test_append_system_message(self):
        """测试追加系统消息方法"""
        # 创建测试消息
        message = "测试系统消息"
        
        # 调用追加系统消息方法
        self.agent._append_system_message(message)
        
        # 验证UI实例的append_system_message_ui方法被调用
        self.mock_ui.append_system_message_ui.assert_called_once_with(message)
        
    def test_generate_task_plan(self):
        """测试生成任务计划方法"""
        # 创建测试任务
        task = "测试任务"
        
        # 创建模拟工具
        mock_tool = MagicMock()
        mock_tool.get_tool_description.return_value = {
            "name": "测试工具",
            "description": "这是一个测试工具"
        }
        self.agent.tools = [mock_tool]
        
        # 使用patch模拟PlanningFlow的execute方法
        with patch.object(PlanningFlow, 'execute', return_value={
            "status": "success",
            "result": json.dumps([
                {"id": 1, "description": "步骤1"},
                {"id": 2, "description": "步骤2"}
            ]),
            "error": None
        }):
            # 调用生成任务计划方法
            result = self.agent._generate_task_plan(task)
            
            # 验证结果
            self.assertEqual(result["status"], "success")
            self.assertIsNotNone(result["result"])
            self.assertIsNone(result["error"])
            
            # 验证PlanningFlow.execute被调用
            self.agent.planning_flow.execute.assert_called_once()
            
    def test_generate_task_plan_failure(self):
        """测试生成任务计划失败的情况"""
        # 创建测试任务
        task = "测试任务"
        
        # 使用patch模拟PlanningFlow的execute方法返回错误
        with patch.object(PlanningFlow, 'execute', return_value={
            "status": "error",
            "result": None,
            "error": "生成任务计划失败"
        }):
            # 调用生成任务计划方法
            result = self.agent._generate_task_plan(task)
            
            # 验证结果
            self.assertEqual(result["status"], "error")
            self.assertIsNone(result["result"])
            self.assertEqual(result["error"], "生成任务计划失败")
            
    def test_add_tool(self):
        """测试添加工具方法"""
        # 创建模拟工具
        mock_tool = MagicMock()
        
        # 调用添加工具方法
        self.agent.add_tool(mock_tool)
        
        # 验证工具被添加到列表中
        self.assertIn(mock_tool, self.agent.tools)
        
    def test_add_memory(self):
        """测试添加记忆方法"""
        # 创建测试记忆项
        memory_item = {
            "type": "step_result",
            "step": 1,
            "task": "测试任务",
            "result": "测试结果"
        }
        
        # 调用添加记忆方法
        self.agent.add_memory(memory_item)
        
        # 验证记忆项被添加到列表中
        self.assertIn(memory_item, self.agent.memory)
        
    @patch('asyncio.to_thread')
    @patch('app.flow.react.ReactFlow')
    async def test_execute_task_chain(self, mock_react_flow_class, mock_to_thread):
        """测试执行任务链方法"""
        # 创建模拟的ReactFlow实例
        mock_react_flow = MagicMock()
        mock_react_flow_class.return_value = mock_react_flow
        mock_react_flow.initialize.return_value = {
            "status": "success",
            "result": "反应流程初始化成功",
            "error": None
        }
        
        # 创建模拟的异步执行结果
        mock_to_thread.return_value = {
            "status": "success",
            "result": "任务执行成功",
            "task_info": {"task": "测试任务"}
        }
        
        # 创建测试任务列表
        tasks = [
            {"id": 1, "description": "任务1"},
            {"id": 2, "description": "任务2"}
        ]
        
        # 调用执行任务链方法
        await self.agent._execute_task_chain(tasks)
        
        # 验证ReactFlow被正确初始化和使用
        self.assertEqual(mock_react_flow.initialize.call_count, 2)  # 每个任务调用一次
        self.assertEqual(mock_to_thread.call_count, 2)  # 每个任务调用一次
        
        # 验证任务状态被更新
        self.assertTrue(tasks[0]["completed"])
        self.assertTrue(tasks[1]["completed"])
        
        # 验证记忆被添加
        self.assertEqual(len(self.agent.memory), 2)  # 每个任务添加一次记忆
        
    @patch('asyncio.to_thread')
    @patch('app.flow.react.ReactFlow')
    async def test_execute_task_chain_with_error(self, mock_react_flow_class, mock_to_thread):
        """测试执行任务链时出现错误的情况"""
        # 创建模拟的ReactFlow实例
        mock_react_flow = MagicMock()
        mock_react_flow_class.return_value = mock_react_flow
        mock_react_flow.initialize.return_value = {
            "status": "success",
            "result": "反应流程初始化成功",
            "error": None
        }
        
        # 创建模拟的异步执行结果，第一个任务成功，第二个任务失败
        mock_to_thread.side_effect = [
            {
                "status": "success",
                "result": "任务1执行成功",
                "task_info": {"task": "任务1"}
            },
            Exception("任务2执行失败")
        ]
        
        # 创建测试任务列表
        tasks = [
            {"id": 1, "description": "任务1"},
            {"id": 2, "description": "任务2"}
        ]
        
        # 调用执行任务链方法
        await self.agent._execute_task_chain(tasks)
        
        # 验证ReactFlow被正确初始化和使用
        self.assertEqual(mock_react_flow.initialize.call_count, 2)  # 每个任务调用一次
        self.assertEqual(mock_to_thread.call_count, 2)  # 每个任务调用一次
        
        # 验证任务状态被更新
        self.assertTrue(tasks[0]["completed"])
        self.assertFalse(tasks[1]["completed"])
        
        # 验证记忆被添加
        self.assertEqual(len(self.agent.memory), 2)  # 每个任务添加一次记忆
        
    @patch('app.agent.manus.ManusAgent._generate_task_plan')
    @patch('app.agent.manus.ManusAgent._execute_task_chain')
    async def test_execute(self, mock_execute_task_chain, mock_generate_task_plan):
        """测试执行方法"""
        # 设置模拟的生成任务计划结果
        mock_generate_task_plan.return_value = {
            "status": "success",
            "result": json.dumps([
                {"id": 1, "description": "步骤1"},
                {"id": 2, "description": "步骤2"}
            ]),
            "error": None
        }
        
        # 设置模拟的执行任务链方法
        mock_execute_task_chain.return_value = None
        
        # 创建测试用户请求
        user_request = "测试用户请求"
        
        # 调用执行方法
        result = await self.agent.execute(user_request)
        
        # 验证结果
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["result"], "任务计划已生成，开始执行")
        self.assertIsNotNone(result["tasks"])
        self.assertEqual(len(result["logs"]), 1)
        
        # 验证方法被调用
        mock_generate_task_plan.assert_called_once_with(user_request)
        mock_execute_task_chain.assert_called_once()
        
    @patch('app.agent.manus.ManusAgent._generate_task_plan')
    async def test_execute_with_planning_failure(self, mock_generate_task_plan):
        """测试执行方法在规划失败时的情况"""
        # 设置模拟的生成任务计划结果返回错误
        mock_generate_task_plan.return_value = {
            "status": "error",
            "result": None,
            "error": "生成任务计划失败"
        }
        
        # 创建测试用户请求
        user_request = "测试用户请求"
        
        # 调用执行方法
        result = await self.agent.execute(user_request)
        
        # 验证结果
        self.assertEqual(result["logs"]["status"], "error")
        self.assertIsNone(result["logs"]["result"])
        self.assertEqual(result["logs"]["error"], "生成任务计划失败")
        
        # 验证方法被调用
        mock_generate_task_plan.assert_called_once_with(user_request)
        
    @patch('app.agent.manus.ManusAgent._generate_task_plan')
    async def test_execute_with_invalid_plan(self, mock_generate_task_plan):
        """测试执行方法在计划无效时的情况"""
        # 设置模拟的生成任务计划结果返回无效的计划
        mock_generate_task_plan.return_value = {
            "status": "success",
            "result": "无效的计划格式",
            "error": None
        }
        
        # 创建测试用户请求
        user_request = "测试用户请求"
        
        # 调用执行方法
        result = await self.agent.execute(user_request)
        
        # 验证结果
        self.assertEqual(result["logs"]["status"], "error")
        self.assertIsNone(result["logs"]["result"])
        self.assertEqual(result["logs"]["error"], "无法生成有效的任务计划")
        
        # 验证方法被调用
        mock_generate_task_plan.assert_called_once_with(user_request)

    def test_update_result_ui(self):
        """测试更新结果UI方法"""
        # 创建测试记忆列表
        memory = [
            {
                "type": "step_result",
                "step": 1,
                "task": {"description": "任务1"},
                "result": "结果1"
            },
            {
                "type": "step_result",
                "step": 2,
                "task": {"description": "任务2"},
                "result": "结果2"
            }
        ]
        
        # 调用更新结果UI方法
        self.agent._update_result_ui(memory)
        
        # 验证UI实例的update_result_ui方法被调用
        self.mock_ui.update_result_ui.assert_called_once_with(memory)

if __name__ == '__main__':
    unittest.main() 