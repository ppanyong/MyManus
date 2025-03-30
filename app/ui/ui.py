from flask import Flask, render_template, request, jsonify
import os

class UI:
    def __init__(self, agent):
        self.app = Flask(__name__)
        self.agent = agent
        self.setup_routes()
        
    def setup_routes(self):
        @self.app.route('/')
        def home():
            return render_template('index.html')
            
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
                
                result = self.agent.execute(user_message)
                
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
            
    def run(self):
        print("MyManus AI Assistant Web UI 已启动！")
        print("访问 http://localhost:3344 查看界面")
        self.app.run(host='0.0.0.0', port=3344) 