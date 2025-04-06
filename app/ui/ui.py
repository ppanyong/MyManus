from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO
import os
import asyncio
from functools import wraps
from typing import Dict, Any
from app.agent.manus import ManusAgent

class UI:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.app = Flask(__name__, 
                        static_folder='static',
                        template_folder='templates')
        self.socketio = SocketIO(self.app, 
                               async_mode='threading', 
                               cors_allowed_origins="*")
        self.agent = ManusAgent(config, self.socketio)
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
            
        @self.socketio.on('connect', namespace='/manus')
        def handle_connect():
            print("Client connected")
            
        @self.socketio.on('disconnect', namespace='/manus')
        def handle_disconnect():
            print("Client disconnected")
            
    def _setup_socket_events(self):
        # This method is empty as the original setup_socket_events method is now part of the __init__ method
        pass

    def run(self):
        """运行UI服务器"""
        server_config = self.config.get('server', {})
        host = server_config.get('host', '127.0.0.1')
        port = server_config.get('port', 3344)
        debug = server_config.get('debug', False)
        
        print(f"启动服务器: http://{host}:{port}")
        self.socketio.run(self.app, host=host, port=port, debug=debug) 