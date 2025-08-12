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
from flask import Blueprint, request, jsonify, current_app, send_from_directory
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
        # 获取V2.0配置和混合引擎
        v2_config = current_app.config.get('V2_CONFIG')
        hybrid_engine = current_app.config.get('HYBRID_ENGINE')
        
        if not v2_config or not hybrid_engine:
            return jsonify({'error': 'V2.0系统未完全初始化'}), 500
        
        # 构建系统状态
        status = {
            'system_name': 'RAG-System-V2.0.0',
            'version': '2.0.0',
            'config_loaded': v2_config is not None,
            'hybrid_engine_ready': hybrid_engine is not None,
            'image_engine_ready': hybrid_engine.image_engine is not None if hybrid_engine else False,
            'text_engine_ready': hybrid_engine.text_engine is not None if hybrid_engine else False,
            'table_engine_ready': hybrid_engine.table_engine is not None if hybrid_engine else False
        }
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
        hybrid_engine = current_app.config.get('HYBRID_ENGINE')
        if not hybrid_engine or not hybrid_engine.image_engine:
            return jsonify({'error': '图片引擎未初始化'}), 500
        
        image_engine = hybrid_engine.image_engine
        
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
                # 检查doc的类型，可能是字典或Document对象
                if isinstance(doc, dict):
                    doc_info = {
                        'id': doc.get('doc_id', 'unknown'),
                        'title': doc.get('caption', ['无标题']),
                        'document_name': doc.get('document_name', 'N/A'),
                        'page_number': doc.get('page_number', 'N/A'),
                        'image_path': doc.get('image_path', ''),
                        'image_type': doc.get('img_type', 'unknown'),
                        'enhanced_description': doc.get('enhanced_description', ''),
                        'score': doc.get('score', 0.0)
                    }
                else:
                    # 如果是Document对象，尝试获取metadata
                    try:
                        doc_info = {
                            'id': getattr(doc, 'doc_id', 'unknown'),
                            'title': getattr(doc, 'caption', ['无标题']),
                            'document_name': getattr(doc, 'document_name', 'N/A'),
                            'page_number': getattr(doc, 'page_number', 'N/A'),
                            'image_path': getattr(doc, 'image_path', ''),
                            'image_type': getattr(doc, 'img_type', 'unknown'),
                            'enhanced_description': getattr(doc, 'image_description', ''),
                            'score': getattr(doc, 'score', 0.0)
                        }
                    except AttributeError:
                        # 如果都失败了，使用字符串表示
                        doc_info = {
                            'id': str(doc),
                            'title': ['未知'],
                            'document_name': 'N/A',
                            'page_number': 'N/A',
                            'image_path': '',
                            'image_type': 'unknown',
                            'enhanced_description': str(doc),
                            'score': 0.0
                        }
                response['results'].append(doc_info)
        else:
            response['success'] = False
            response['error'] = getattr(result, 'error_message', '未知错误')
        
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
        hybrid_engine = current_app.config.get('HYBRID_ENGINE')
        if not hybrid_engine or not hybrid_engine.text_engine:
            return jsonify({'error': '文本引擎未初始化'}), 500
        
        text_engine = hybrid_engine.text_engine
        
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
        hybrid_engine = current_app.config.get('HYBRID_ENGINE')
        if not hybrid_engine or not hybrid_engine.table_engine:
            return jsonify({'error': '表格引擎未初始化'}), 500
        
        table_engine = hybrid_engine.table_engine
        
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
        hybrid_engine = current_app.config.get('HYBRID_ENGINE')
        if hybrid_engine and hybrid_engine.image_engine:
            engines_status['image'] = {
                'enabled': True,
                'status': hybrid_engine.image_engine.get_status()
            }
        else:
            engines_status['image'] = {
                'enabled': False,
                'status': None
            }
        
        # 检查文本引擎
        if hybrid_engine and hybrid_engine.text_engine:
            engines_status['text'] = {
                'enabled': True,
                'status': hybrid_engine.text_engine.get_status()
            }
        else:
            engines_status['text'] = {
                'enabled': False,
                'status': None
            }
        
        # 检查表格引擎
        if hybrid_engine and hybrid_engine.table_engine:
            engines_status['table'] = {
                'enabled': True,
                'status': hybrid_engine.table_engine.get_status()
            }
        else:
            engines_status['table'] = {
                'enabled': False,
                'status': None
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
        hybrid_engine = current_app.config.get('HYBRID_ENGINE')
        if hybrid_engine and hybrid_engine.image_engine:
            try:
                hybrid_engine.image_engine.refresh_image_cache()
                refreshed_engines.append('image')
            except Exception as e:
                logger.error(f"刷新图片引擎失败: {e}")
        
        # 刷新文本引擎
        if hybrid_engine and hybrid_engine.text_engine:
            try:
                hybrid_engine.text_engine.refresh_text_cache()
                refreshed_engines.append('text')
            except Exception as e:
                logger.error(f"刷新文本引擎失败: {e}")
        
        # 刷新表格引擎
        if hybrid_engine and hybrid_engine.table_engine:
            try:
                hybrid_engine.table_engine.refresh_table_cache()
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


@v2_api_bp.route('/qa/preset-questions', methods=['GET'])
def get_v2_preset_questions():
    """
    获取V2预设问题接口
    GET /api/v2/qa/preset-questions?type=image
    """
    try:
        query_type = request.args.get('type', 'hybrid')
        
        # 读取V2预设问题文件
        import json
        import os
        
        preset_file = 'v2/config/v2_preset_questions.json'
        if os.path.exists(preset_file):
            with open(preset_file, 'r', encoding='utf-8') as f:
                all_questions = json.load(f)
            
            # 根据查询类型返回对应问题
            questions = all_questions.get(query_type, [])
            
            return jsonify({
                'success': True,
                'query_type': query_type,
                'questions': questions,
                'total_count': len(questions)
            })
        else:
            # 如果文件不存在，返回默认问题
            default_questions = {
                'image': ["图4是什么？", "有哪些图表？"],
                'text': ["文档主要内容是什么？", "有哪些关键信息？"],
                'table': ["有哪些数据表格？", "财务数据如何？"],
                'hybrid': ["请综合分析文档内容", "总结关键信息"]
            }
            
            questions = default_questions.get(query_type, default_questions['hybrid'])
            
            return jsonify({
                'success': True,
                'query_type': query_type,
                'questions': questions,
                'total_count': len(questions)
            })
            
    except Exception as e:
        logger.error(f"获取V2预设问题失败: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


@v2_api_bp.route('/memory/stats', methods=['GET'])
def get_v2_memory_stats():
    """
    获取V2记忆统计信息
    GET /api/v2/memory/stats?user_id=xxx
    """
    try:
        user_id = request.args.get('user_id', 'default_user')
        
        # 获取记忆管理器
        hybrid_engine = current_app.config.get('HYBRID_ENGINE')
        if not hybrid_engine or not hasattr(hybrid_engine, 'memory_manager'):
            return jsonify({'error': '记忆管理器未初始化'}), 500
        
        memory_manager = hybrid_engine.memory_manager
        
        # 获取统计信息
        try:
            stats = memory_manager.get_memory_stats(user_id)
        except Exception as e:
            logger.warning(f"获取记忆统计失败，使用默认值: {e}")
            stats = {
                'session_memory_count': 0,
                'user_memory_count': 0,
                'total_memory_count': 0
            }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"V2记忆统计接口错误: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


@v2_api_bp.route('/memory/clear', methods=['POST'])
@v2_api_bp.route('/qa/ask', methods=['POST'])
@v2_api_bp.route('/qa/preset-questions', methods=['GET'])
@v2_api_bp.route('/memory/stats', methods=['GET'])
def get_v2_memory_stats():
    """
    获取V2记忆统计信息
    GET /api/v2/memory/stats?user_id=xxx
    """
    try:
        user_id = request.args.get('user_id', 'default_user')
        
        # 获取记忆管理器
        hybrid_engine = current_app.config.get('HYBRID_ENGINE')
        if not hybrid_engine or not hasattr(hybrid_engine, 'memory_manager'):
            return jsonify({'error': '记忆管理器未初始化'}), 500
        
        memory_manager = hybrid_engine.memory_manager
        
        # 获取统计信息
        try:
            stats = memory_manager.get_memory_stats(user_id)
        except Exception as e:
            logger.warning(f"获取记忆统计失败，使用默认值: {e}")
            stats = {
                'session_memory_count': 0,
                'user_memory_count': 0,
                'total_memory_count': 0
            }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"V2记忆统计接口错误: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


@v2_api_bp.route('/memory/clear', methods=['POST'])
def clear_v2_memory():
    """
    清除V2记忆
    POST /api/v2/memory/clear
    """
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id', 'default_user')
        memory_type = data.get('memory_type', 'session')  # all, session, user
        
        # 获取记忆管理器
        hybrid_engine = current_app.config.get('HYBRID_ENGINE')
        if not hybrid_engine or not hasattr(hybrid_engine, 'memory_manager'):
            return jsonify({'error': '记忆管理器未初始化'}), 500
        
        memory_manager = hybrid_engine.memory_manager
        
        # 清除记忆
        if memory_type == 'all':
            memory_manager.clear_session_memory(user_id)
            memory_manager.clear_user_memory(user_id)
        elif memory_type == 'session':
            memory_manager.clear_session_memory(user_id)
        elif memory_type == 'user':
            memory_manager.clear_user_memory(user_id)
        else:
            return jsonify({'error': '无效的记忆类型'}), 400
        
        return jsonify({
            'success': True,
            'message': f'已清除{memory_type}记忆',
            'user_id': user_id,
            'memory_type': memory_type
        })
        
    except Exception as e:
        logger.error(f"清除V2记忆接口错误: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


@v2_api_bp.route('/qa/ask', methods=['POST'])
def v2_ask_question():
    """
    V2问答接口 - 集成记忆功能
    POST /api/v2/qa/ask
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
        
        question = data.get('query', '').strip()
        user_id = data.get('user_id', 'default_user')
        use_memory = data.get('use_memory', True)
        query_type = data.get('query_type', 'hybrid')
        max_results = data.get('max_results', 10)
        
        if not question:
            return jsonify({'error': '问题不能为空'}), 400
        
        # 获取混合引擎
        hybrid_engine = current_app.config.get('HYBRID_ENGINE')
        if not hybrid_engine:
            return jsonify({'error': 'V2混合引擎未初始化'}), 500
        
        # 执行查询
        start_time = time.time()
        
        if query_type == 'hybrid':
            result = hybrid_engine.process_query(question, max_results=max_results)
        elif query_type == 'image':
            result = hybrid_engine.image_engine.process_query(question, max_results=max_results)
        elif query_type == 'text':
            result = hybrid_engine.text_engine.process_query(question, max_results=max_results)
        elif query_type == 'table':
            result = hybrid_engine.table_engine.process_query(question, max_results=max_results)
        else:
            return jsonify({'error': f'不支持的查询类型: {query_type}'}), 400
        
        processing_time = time.time() - start_time
        
        # 格式化响应
        response = {
            'success': True,
            'question': question,
            'query_type': query_type,
            'answer': result.answer if hasattr(result, 'answer') else str(result),
            'sources': result.sources if hasattr(result, 'sources') else [],
            'total_count': result.total_count if hasattr(result, 'total_count') else 0,
            'processing_time': processing_time,
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'use_memory': use_memory
        }
        
        if hasattr(result, 'error_message') and result.error_message:
            response['error'] = result.error_message
            response['success'] = False
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"V2问答接口错误: {e}")
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


def create_v2_app(config, v2_config, hybrid_engine):
    """
    创建V2版本的Flask应用
    
    :param config: 系统配置
    :param v2_config: V2配置
    :param hybrid_engine: 混合引擎实例
    :return: Flask应用实例
    """
    from flask import Flask
    from flask_cors import CORS
    
    app = Flask(__name__)
    
    # 启用CORS
    CORS(app)
    
    # 配置应用
    app.config['SETTINGS'] = config
    app.config['V2_CONFIG'] = v2_config
    app.config['HYBRID_ENGINE'] = hybrid_engine
    
    # 注册V2 API蓝图
    register_v2_blueprint(app)
    
    # 健康检查
    @app.route('/health')
    def health_check():
        """健康检查接口"""
        return jsonify({
            'status': 'healthy',
            'version': 'V2.0.0',
            'message': 'V2 RAG系统运行正常'
        })
    
    # 根路径 - 重定向到V2前端
    @app.route('/')
    def index():
        """根路径重定向"""
        return jsonify({
            'message': 'V2 RAG系统',
            'version': 'V2.0.0',
            'frontend': '/v2',
            'api_docs': '/api/v2/status'
        })
    
    # V2前端页面
    @app.route('/v2')
    def v2_frontend():
        """V2前端页面"""
        try:
            with open('v2/web/v2_index.html', 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return jsonify({
                'error': 'V2前端页面未找到',
                'path': 'v2/web/v2_index.html'
            }), 404
    
    # 静态文件服务
    @app.route('/v2/static/<path:filename>')
    def v2_static(filename):
        """V2静态文件服务"""
        try:
            return send_from_directory('v2/web/static', filename)
        except FileNotFoundError:
            return jsonify({'error': f'文件未找到: {filename}'}), 404
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        """404错误处理"""
        return jsonify({
            'error': '接口未找到',
            'message': '请检查API路径是否正确',
            'available_endpoints': [
                '/api/v2/status',
                '/api/v2/query/image',
                '/api/v2/query/text',
                '/api/v2/query/table',
                '/api/v2/query/hybrid',
                '/api/v2/query/smart'
            ]
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """500错误处理"""
        return jsonify({
            'error': '服务器内部错误',
            'message': '请稍后重试或联系管理员'
        }), 500
    
    logger.info("V2 Flask应用创建成功")
    return app
