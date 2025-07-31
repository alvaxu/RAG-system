'''
程序说明：
## 1. 该模块实现了基于Flask的Web后端服务，提供问答功能的REST API接口
## 2. 集成了V303_vector_store_qa_with_cost.py模块，支持通义千问API的成本计算功能
## 3. 提供了获取预设问题和问答接口的API端点
## 4. 提供静态文件服务，支持Web前端界面
## 5. 相比V302版本，新增了准确的成本计算功能，能够显示LLM查询的详细成本信息
'''

import os
import sys

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# 添加项目根目录到Python路径，以便导入项目模块
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
# 同时添加web_app目录到Python路径，以便在项目根目录中运行时也能正确导入
web_app_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(web_app_path)

# 导入V303版本的向量存储问答系统模块
from V303_vector_store_qa_with_cost import VectorStoreManager, QuestionAnsweringSystem

# 创建Flask应用
app = Flask(__name__)
# 启用CORS支持
CORS(app)

# 加载环境变量
load_dotenv()

# 从环境变量中获取API密钥
DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY', '你的APIKEY')

# 初始化向量存储管理器和问答系统
# 确保使用正确的向量数据库路径
# 当在web_app目录下运行时，使用相对路径"../vector_db"
# 当在项目根目录下运行时，使用相对路径"vector_db"
vector_db_path = "../vector_db"
if not os.path.exists(vector_db_path):
    vector_db_path = "vector_db"

vector_manager = VectorStoreManager(DASHSCOPE_API_KEY)
vector_store = vector_manager.load_vector_store(vector_db_path)
qa_system = QuestionAnsweringSystem(vector_store, DASHSCOPE_API_KEY)

# 预设问题列表
preset_questions = [
    "个金客户经理被投诉了，投诉一次扣多少分？",
    "个金客户经理每年评聘申报时间是怎样的？",
    "个金客户经理的职责是什么？",
    "个金客户经理的职位设置有哪些？",
    "个金客户经理的准入条件是什么？",
    "个金客户经理的个人业绩考核标准是什么？",
    "个金客户经理的工作质量考核标准是什么？",
    "如何聘任个金客户经理？",
    "个金客户经理的考核待遇如何构成？",
    "个金客户经理的收入由哪些部分组成？",
    "个金客户经理的管理机构是什么？",
    "个金客户经理的奖惩措施有哪些？"
]

@app.route('/api/preset-questions', methods=['GET'])
def get_preset_questions():
    """
    获取预设问题列表的API端点
    :return: 预设问题列表的JSON响应
    """
    return jsonify({
        'questions': preset_questions
    })

@app.route('/api/ask', methods=['POST'])
def ask_question():
    """
    问答API端点
    :return: 问答结果的JSON响应
    """
    try:
        # 从请求中获取问题
        data = request.get_json()
        question = data.get('question', '').strip()
        
        # 检查问题是否为空
        if not question:
            return jsonify({
                'error': '问题不能为空'
            }), 400
        
        # 使用问答系统回答问题
        result = qa_system.answer_question(question)
        
        # 返回结果
        return jsonify(result)
    
    except Exception as e:
        # 处理异常
        return jsonify({
            'error': f'处理问题时发生错误: {str(e)}'
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """
    健康检查端点
    :return: 健康状态的JSON响应
    """
    return jsonify({
        'status': 'healthy',
        'message': '问答系统后端服务运行正常（V303版本，支持成本计算）'
    })


@app.route('/')
def index():
    """
    主页路由，提供前端界面
    :return: index.html文件内容
    """
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'index.html')


@app.route('/<path:filename>')
def static_files(filename):
    """
    静态文件服务路由
    :param filename: 文件名
    :return: 静态文件内容
    """
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), filename)

if __name__ == '__main__':
    # 启动Flask应用
    print("启动V303版本的Web问答系统（支持成本计算）...")
    print("访问地址: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True) 