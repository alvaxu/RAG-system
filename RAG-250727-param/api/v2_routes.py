'''
程序说明：
## 1. V2.0.0 API路由 - 实现图表文查询分离
## 2. 专门的图片、文本、表格查询接口
## 3. 混合查询和智能路由
## 4. 向后兼容现有API
'''

import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from flask import Blueprint, request, jsonify, current_app
from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置日志
logger = logging.getLogger(__name__)

# 创建V2.0蓝图
v2_api_bp = Blueprint('v2_api', __name__, url_prefix='/api/v2')

# 线程池执行器
executor = ThreadPoolExecutor(max_workers=5)


@v2_api_bp.route('/status', methods=['GET'])
def get_v2_status():
    """
    获取V2.0系统状态
    GET /api/v2/status
    """
    try:
        # 获取V2.0配置管理器
        v2_config = current_app.config.get('V2_CONFIG_MANAGER')
        if not v2_config:
            return jsonify({'error': 'V2.0配置未初始化'}), 500
        
        status = v2_config.get_system_status()
        return jsonify({
            'success': True,
            'status': status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取V2.0状态失败: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


@v2_api_bp.route('/query/image', methods=['POST'])
def query_images():
    """
    专门的图片查询接口
    POST /api/v2/query/image
    
    请求体:
    {
        "query": "图4",
        "max_results": 10,
        "user_id": "user123"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
        
        query = data.get('query', '').strip()
        max_results = data.get('max_results', 10)
        user_id = data.get('user_id', 'default_user')
        
        if not query:
            return jsonify({'error': '查询内容不能为空'}), 400
        
        # 获取图片引擎
        image_engine = current_app.config.get('IMAGE_ENGINE')
        if not image_engine:
            return jsonify({'error': '图片引擎未初始化'}), 500
        
        # 执行图片查询
        start_time = time.time()
        result = image_engine.process_query(query, max_results=max_results)
        processing_time = time.time() - start_time
        
        # 格式化响应
        response = {
            'success': True,
            'query': query,
            'query_type': 'image',
            'results': [],
            'total_count': result.total_count,
            'processing_time': processing_time,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        }
        
        # 处理查询结果
        if result.success:
            for doc in result.results:
                doc_info = {
                    'id': getattr(doc, 'doc_id', 'unknown'),
                    'title': doc.metadata.get('img_caption', ['无标题']),
                    'document_name': doc.metadata.get('document_name', 'N/A'),
                    'page_number': doc.metadata.get('page_number', 'N/A'),
                    'image_path': doc.metadata.get('img_path', ''),
                    'image_type': doc.metadata.get('img_type', 'unknown'),
                    'enhanced_description': doc.metadata.get('enhanced_description', ''),
                    'score': getattr(doc, 'score', 0.0)
                }
                response['results'].append(doc_info)
        else:
            response['success'] = False
            response['error'] = result.error_message
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"图片查询失败: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


@v2_api_bp.route('/query/text', methods=['POST'])
def query_texts():
    """
    专门的文本查询接口
    POST /api/v2/query/text
    
    请求体:
    {
        "query": "中芯国际业绩",
        "max_results": 10,
        "user_id": "user123"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
        
        query = data.get('query', '').strip()
        max_results = data.get('max_results', 10)
        user_id = data.get('user_id', 'default_user')
        
        if not query:
            return jsonify({'error': '查询内容不能为空'}), 400
        
        # 获取文本引擎
        text_engine = current_app.config.get('TEXT_ENGINE')
        if not text_engine:
            return jsonify({'error': '文本引擎未初始化'}), 500
        
        # 执行文本查询
        start_time = time.time()
        result = text_engine.process_query(query, max_results=max_results)
        processing_time = time.time() - start_time
        
        # 格式化响应
        response = {
            'success': True,
            'query': query,
            'query_type': 'text',
            'results': [],
            'total_count': result.total_count,
            'processing_time': processing_time,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        }
        
        # 处理查询结果
        if result.success:
            for doc in result.results:
                doc_info = {
                    'id': getattr(doc, 'doc_id', 'unknown'),
                    'content': doc.page_content[:200] + '...' if len(doc.page_content) > 200 else doc.page_content,
                    'document_name': doc.metadata.get('document_name', 'N/A'),
                    'page_number': doc.metadata.get('page_number', 'N/A'),
                    'chunk_type': doc.metadata.get('chunk_type', 'text'),
                    'score': getattr(doc, 'score', 0.0)
                }
                response['results'].append(doc_info)
        else:
            response['success'] = False
            response['error'] = result.error_message
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"文本查询失败: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


@v2_api_bp.route('/query/table', methods=['POST'])
def query_tables():
    """
    专门的表格查询接口
    POST /api/v2/query/table
    
    请求体:
    {
        "query": "财务数据表格",
        "max_results": 10,
        "user_id": "user123"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
        
        query = data.get('query', '').strip()
        max_results = data.get('max_results', 10)
        user_id = data.get('user_id', 'default_user')
        
        if not query:
            return jsonify({'error': '查询内容不能为空'}), 400
        
        # 获取表格引擎
        table_engine = current_app.config.get('TABLE_ENGINE')
        if not table_engine:
            return jsonify({'error': '表格引擎未初始化'}), 500
        
        # 执行表格查询
        start_time = time.time()
        result = table_engine.process_query(query, max_results=max_results)
        processing_time = time.time() - start_time
        
        # 格式化响应
        response = {
            'success': True,
            'query': query,
            'query_type': 'table',
            'results': [],
            'total_count': result.total_count,
            'processing_time': processing_time,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        }
        
        # 处理查询结果
        if result.success:
            for doc in result.results:
                doc_info = {
                    'id': getattr(doc, 'doc_id', 'unknown'),
                    'table_content': doc.page_content[:300] + '...' if len(doc.page_content) > 300 else doc.page_content,
                    'document_name': doc.metadata.get('document_name', 'N/A'),
                    'page_number': doc.metadata.get('page_number', 'N/A'),
                    'chunk_type': doc.metadata.get('chunk_type', 'table'),
                    'table_structure': doc.metadata.get('table_structure', {}),
                    'score': getattr(doc, 'score', 0.0)
                }
                response['results'].append(doc_info)
        else:
            response['success'] = False
            response['error'] = result.error_message
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"表格查询失败: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


@v2_api_bp.route('/query/hybrid', methods=['POST'])
def query_hybrid():
    """
    混合查询接口 - 同时查询图片、文本、表格
    POST /api/v2/query/hybrid
    
    请求体:
    {
        "query": "中芯国际",
        "max_results": 15,
        "user_id": "user123",
        "include_types": ["image", "text", "table"]
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
        
        query = data.get('query', '').strip()
        max_results = data.get('max_results', 15)
        user_id = data.get('user_id', 'default_user')
        include_types = data.get('include_types', ['image', 'text', 'table'])
        
        if not query:
            return jsonify({'error': '查询内容不能为空'}), 400
        
        # 获取所有引擎
        engines = {}
        if 'image' in include_types:
            engines['image'] = current_app.config.get('IMAGE_ENGINE')
        if 'text' in include_types:
            engines['text'] = current_app.config.get('TEXT_ENGINE')
        if 'table' in include_types:
            engines['table'] = current_app.config.get('TABLE_ENGINE')
        
        if not engines:
            return jsonify({'error': '没有可用的查询引擎'}), 500
        
        # 并行执行查询
        start_time = time.time()
        results = {}
        
        def execute_query(engine_type, engine):
            try:
                if engine:
                    result = engine.process_query(query, max_results=max_results//len(engines))
                    return engine_type, result
                return engine_type, None
            except Exception as e:
                logger.error(f"{engine_type}引擎查询失败: {e}")
                return engine_type, None
        
        # 使用线程池并行执行
        futures = []
        for engine_type, engine in engines.items():
            future = executor.submit(execute_query, engine_type, engine)
            futures.append(future)
        
        # 收集结果
        for future in as_completed(futures):
            engine_type, result = future.result()
            if result:
                results[engine_type] = result
        
        processing_time = time.time() - start_time
        
        # 格式化响应
        response = {
            'success': True,
            'query': query,
            'query_type': 'hybrid',
            'results': {},
            'total_count': 0,
            'processing_time': processing_time,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        }
        
        # 处理混合结果
        for engine_type, result in results.items():
            if result and result.success:
                response['results'][engine_type] = {
                    'total_count': result.total_count,
                    'items': []
                }
                response['total_count'] += result.total_count
                
                # 处理不同类型的结果
                for doc in result.results:
                    if engine_type == 'image':
                        doc_info = {
                            'id': getattr(doc, 'doc_id', 'unknown'),
                            'title': doc.metadata.get('img_caption', ['无标题']),
                            'document_name': doc.metadata.get('document_name', 'N/A'),
                            'image_path': doc.metadata.get('img_path', ''),
                            'score': getattr(doc, 'score', 0.0)
                        }
                    elif engine_type == 'text':
                        doc_info = {
                            'id': getattr(doc, 'doc_id', 'unknown'),
                            'content': doc.page_content[:200] + '...' if len(doc.page_content) > 200 else doc.page_content,
                            'document_name': doc.metadata.get('document_name', 'N/A'),
                            'score': getattr(doc, 'score', 0.0)
                        }
                    elif engine_type == 'table':
                        doc_info = {
                            'id': getattr(doc, 'doc_id', 'unknown'),
                            'table_content': doc.page_content[:300] + '...' if len(doc.page_content) > 300 else doc.page_content,
                            'document_name': doc.metadata.get('document_name', 'N/A'),
                            'score': getattr(doc, 'score', 0.0)
                        }
                    else:
                        continue
                    
                    response['results'][engine_type]['items'].append(doc_info)
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"混合查询失败: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


@v2_api_bp.route('/query/smart', methods=['POST'])
def query_smart():
    """
    智能查询接口 - 自动判断查询类型并路由
    POST /api/v2/query/smart
    
    请求体:
    {
        "query": "图4 中芯国际业绩",
        "max_results": 10,
        "user_id": "user123"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
        
        query = data.get('query', '').strip()
        max_results = data.get('max_results', 10)
        user_id = data.get('user_id', 'default_user')
        
        if not query:
            return jsonify({'error': '查询内容不能为空'}), 400
        
        # 智能判断查询类型
        query_type = _analyze_query_type(query)
        
        # 根据查询类型路由到相应的接口
        if query_type == 'image':
            return query_images()
        elif query_type == 'table':
            return query_tables()
        elif query_type == 'text':
            return query_texts()
        else:
            # 默认使用混合查询
            return query_hybrid()
        
    except Exception as e:
        logger.error(f"智能查询失败: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


def _analyze_query_type(query: str) -> str:
    """
    分析查询类型
    
    :param query: 查询文本
    :return: 查询类型 ('image', 'text', 'table', 'hybrid')
    """
    query_lower = query.lower()
    
    # 图片查询关键词
    image_keywords = ['图', '图片', '图表', 'figure', 'chart', 'image', 'photo']
    if any(keyword in query_lower for keyword in image_keywords):
        return 'image'
    
    # 表格查询关键词
    table_keywords = ['表', '表格', '数据表', 'table', 'data', '财务数据', '业绩数据']
    if any(keyword in query_lower for keyword in table_keywords):
        return 'table'
    
    # 文本查询（默认）
    return 'text'


@v2_api_bp.route('/engines/status', methods=['GET'])
def get_engines_status():
    """
    获取所有引擎状态
    GET /api/v2/engines/status
    """
    try:
        engines_status = {}
        
        # 检查图片引擎
        image_engine = current_app.config.get('IMAGE_ENGINE')
        engines_status['image'] = {
            'enabled': image_engine is not None,
            'status': image_engine.get_status() if image_engine else None
        }
        
        # 检查文本引擎
        text_engine = current_app.config.get('TEXT_ENGINE')
        engines_status['text'] = {
            'enabled': text_engine is not None,
            'status': text_engine.get_status() if text_engine else None
        }
        
        # 检查表格引擎
        table_engine = current_app.config.get('TABLE_ENGINE')
        engines_status['table'] = {
            'enabled': table_engine is not None,
            'status': table_engine.get_status() if table_engine else None
        }
        
        return jsonify({
            'success': True,
            'engines': engines_status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取引擎状态失败: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


@v2_api_bp.route('/engines/refresh', methods=['POST'])
def refresh_engines():
    """
    刷新所有引擎
    POST /api/v2/engines/refresh
    """
    try:
        refreshed_engines = []
        
        # 刷新图片引擎
        image_engine = current_app.config.get('IMAGE_ENGINE')
        if image_engine:
            try:
                image_engine.refresh_image_cache()
                refreshed_engines.append('image')
            except Exception as e:
                logger.error(f"刷新图片引擎失败: {e}")
        
        # 刷新文本引擎
        text_engine = current_app.config.get('TEXT_ENGINE')
        if text_engine:
            try:
                text_engine.refresh_text_cache()
                refreshed_engines.append('text')
            except Exception as e:
                logger.error(f"刷新文本引擎失败: {e}")
        
        # 刷新表格引擎
        table_engine = current_app.config.get('TABLE_ENGINE')
        if table_engine:
            try:
                table_engine.refresh_table_cache()
                refreshed_engines.append('table')
            except Exception as e:
                logger.error(f"刷新表格引擎失败: {e}")
        
        return jsonify({
            'success': True,
            'refreshed_engines': refreshed_engines,
            'message': f'成功刷新 {len(refreshed_engines)} 个引擎',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"刷新引擎失败: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


# 注册蓝图到主应用
def register_v2_blueprint(app):
    """
    注册V2.0蓝图到Flask应用
    
    :param app: Flask应用实例
    """
    app.register_blueprint(v2_api_bp)
    logger.info("V2.0 API蓝图注册成功")
