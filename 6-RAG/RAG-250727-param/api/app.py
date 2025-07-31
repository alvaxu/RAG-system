'''
程序说明：
## 1. Flask应用主文件
## 2. 整合问答系统和记忆管理
## 3. 提供Web API服务
## 4. 支持配置管理和错误处理
'''

import os
import sys
import logging
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 导入相关模块
from core.enhanced_qa_system import load_enhanced_qa_system
from core.memory_manager import MemoryManager
from config.settings import Settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _validate_app_config(config):
    """
    验证应用配置
    :param config: 配置对象
    """
    try:
        # 检查API密钥
        if not config.dashscope_api_key or config.dashscope_api_key == '你的DashScope API密钥':
            logger.warning("DashScope API密钥未配置，问答功能可能受限")
        
        if not config.mineru_api_key or config.mineru_api_key == '你的minerU API密钥':
            logger.warning("minerU API密钥未配置，PDF处理功能可能受限")
        
        # 检查路径配置
        required_paths = ['web_app_dir', 'images_dir', 'memory_db_dir']
        for path_name in required_paths:
            path_value = getattr(config, path_name, None)
            if not path_value:
                logger.warning(f"缺少路径配置: {path_name}")
        
        logger.info("应用配置验证完成")
        
    except Exception as e:
        logger.error(f"应用配置验证失败: {e}")


def create_app(config=None):
    """
    创建Flask应用
    :param config: 配置对象
    :return: Flask应用实例
    """
    app = Flask(__name__)
    
    # 启用CORS
    CORS(app)
    
    # 统一配置管理
    if config is None:
        # 从配置文件加载设置
        config = Settings.load_from_file('config.json')
    elif isinstance(config, dict):
        # 如果是字典，使用统一配置管理
        config = Settings.load_from_file('config.json')
    
    # 验证配置
    _validate_app_config(config)
    
    app.config['SETTINGS'] = config
    
    # 初始化全局对象
    initialize_globals(app)
    
    # 注册蓝图
    from .routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # 错误处理
    register_error_handlers(app)
    
    # 健康检查
    @app.route('/health')
    def health_check():
        """健康检查接口"""
        return jsonify({
            'status': 'healthy',
            'message': 'RAG系统运行正常'
        })
    
    # 根路径 - 提供前端页面
    @app.route('/')
    def index():
        """提供前端页面"""
        web_app_dir = config.web_app_dir if config else './web_app_test'
        return send_from_directory(web_app_dir, 'index.html')
    
    # 静态文件服务
    @app.route('/<path:filename>')
    def static_files(filename):
        """提供静态文件服务"""
        web_app_dir = config.web_app_dir if config else './web_app_test'
        return send_from_directory(web_app_dir, filename)
    
    # 图片文件服务
    @app.route('/md_test/images/<path:filename>')
    def image_files(filename):
        """提供图片文件服务"""
        images_dir = config.images_dir if config else './md_test/images'
        return send_from_directory(images_dir, filename)
    
    return app


def initialize_globals(app):
    """
    初始化全局对象
    :param app: Flask应用实例
    """
    try:
        config = app.config['SETTINGS']
        
        # 初始化记忆管理器
        logger.info("正在初始化记忆管理器...")
        memory_manager = MemoryManager(config.memory_db_dir)
        app.config['MEMORY_MANAGER'] = memory_manager
        logger.info("记忆管理器初始化成功")
        
        # 初始化问答系统
        api_key = config.dashscope_api_key
        vector_db_path = config.vector_db_dir
        
        logger.info("正在加载问答系统...")
        qa_system = load_enhanced_qa_system(vector_db_path, api_key, memory_manager, config.to_dict())
        
        if qa_system:
            app.config['QA_SYSTEM'] = qa_system
            logger.info("问答系统加载成功")
        else:
            logger.warning("问答系统加载失败")
            app.config['QA_SYSTEM'] = None
        
    except Exception as e:
        logger.error(f"初始化全局对象失败: {e}")
        app.config['QA_SYSTEM'] = None
        app.config['MEMORY_MANAGER'] = None


def register_error_handlers(app):
    """
    注册错误处理器
    :param app: Flask应用实例
    """
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': '请求的资源不存在'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'error': 'Internal Server Error',
            'message': '服务器内部错误'
        }), 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        logger.error(f"未处理的异常: {error}")
        return jsonify({
            'error': 'Unexpected Error',
            'message': '发生未预期的错误'
        }), 500


def get_qa_system(app):
    """
    获取问答系统实例
    :param app: Flask应用实例
    :return: 问答系统实例
    """
    return app.config.get('QA_SYSTEM')


def get_memory_manager(app):
    """
    获取记忆管理器实例
    :param app: Flask应用实例
    :return: 记忆管理器实例
    """
    return app.config.get('MEMORY_MANAGER')


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000) 