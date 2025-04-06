from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO
import os
import asyncio
from functools import wraps
from typing import Dict, Any
from app.agent.manus import ManusAgent

class UI:
    def __init__(self, config: Dict[str, Any],agent:ManusAgent):
        self.config = config
        self.app = Flask(__name__, 
                        static_folder='static',
                        template_folder='templates')
        self.socketio = SocketIO(self.app, 
                               async_mode='threading', 
                               cors_allowed_origins="*")
        self.agent=agent
        self.agent.socketio=self.socketio
        self._setup_routes()
        self._setup_socket_events()
        
    def _setup_routes(self):
        @self.app.route('/')
        def home():
            return render_template('index.html')
            
        @self.app.route('/static/<path:filename>')
        def serve_static(filename):
            return send_from_directory(self.app.static_folder, filename)
            
        @self.app.route('/api/chat', methods=['POST'])
        def chat():
            try:
                data = request.json
                user_message = data.get('message', '')
                
                if not user_message:
                    return jsonify({
                        'status': 'error',
                        'message': '消息不能为空'
                    })
                
                # 使用 asyncio.run 在同步上下文中运行异步函数
                result = asyncio.run(self.agent.execute(user_message))
                
                return jsonify({
                    'status': 'success',
                    'response': result
                })
                
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                })
                
        @self.app.route('/api/status')
        def status():
            return jsonify({
                'status': 'running',
                'agent_initialized': self.agent is not None,
                'tools_count': len(self.agent.get_tools()) if self.agent else 0
            })
            
       
            
    def _setup_socket_events(self):
        @self.socketio.on('connect', namespace='/manus')
        def handle_connect():
            print("Client connected")
            
        @self.socketio.on('disconnect', namespace='/manus')
        def handle_disconnect():
            print("Client disconnected")

        @self.socketio.on(' ', namespace='/manus')
        def handle_update_plan(data):
            """处理计划更新事件
            
            Args:
                data: 包含计划数据的字典，data的结构是 {[{'step_id': 1, 'purpose': '计算两个数字的和', 'description': '使用Calculator.add执行计算1+1', 'parameters': {'a': 1, 'b': 1}, 'dependencies': [], 'expected_output': '计算结果（数字类型）'}]}
            """
            try:
                plan = data
                if not plan:
                    print("警告: 收到的计划为空")
                    return
                    
                # 更新任务列表
                tasks = [{"description": step, "completed": False} for step in plan]
                
                # 发送更新后的任务列表到客户端
                self.socketio.emit('update_plan_ui', {
                    'tasks': tasks
                }, namespace='/manus')
                
                print(f"计划已更新，共 {len(plan)} 个步骤")
                
            except Exception as e:
                print(f"处理计划更新失败: {str(e)}")
                
        @self.socketio.on('append_system_message', namespace='/manus')
        def handle_append_system_message(data):
            """处理系统消息追加事件
            
            Args:
                data: 包含系统消息的字典，data的结构是 {'message': '系统消息内容'}
            """
            try:
                message = data.get('message', '')
                if not message:
                    print("警告: 收到的系统消息为空")
                    return
                    
                # 发送系统消息到客户端
                self.socketio.emit('append_system_message_ui', {
                    'message': message
                }, namespace='/manus')
                
                print(f"系统消息已追加: {message[:50]}...")
                
            except Exception as e:
                print(f"处理系统消息追加失败: {str(e)}")

    def run(self):
        """运行UI服务器"""
        server_config = self.config.get('server', {})
        host = server_config.get('host', '127.0.0.1')
        port = server_config.get('port', 3344)
        debug = server_config.get('debug', False)
        
        print(f"启动服务器: http://{host}:{port}")
        self.socketio.run(self.app, host=host, port=port, debug=debug) 