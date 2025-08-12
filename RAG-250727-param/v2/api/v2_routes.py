'''
程序说明：
## 1. V2.0.0 API路由 - 实现图表文查询分离
## 2. 专门的图片、文本、表格查询接口
## 3. 混合查询和智能路由
## 4. 向后兼容现有API
## 5. 新增优化引擎功能接口
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
            'table_engine_ready': hybrid_engine.table_engine is not None if hybrid_engine else False,
            # 新增：优化引擎状态
            'reranking_engine_ready': hybrid_engine.reranking_engine is not None if hybrid_engine else False,
            'llm_engine_ready': hybrid_engine.llm_engine is not None if hybrid_engine else False,
            'smart_filter_engine_ready': hybrid_engine.smart_filter_engine is not None if hybrid_engine else False,
            'source_filter_engine_ready': hybrid_engine.source_filter_engine is not None if hybrid_engine else False,
            'optimization_pipeline_enabled': hybrid_engine.hybrid_config.enable_optimization_pipeline if hybrid_engine and hybrid_engine.hybrid_config else False
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


@v2_api_bp.route('/query/optimized', methods=['POST'])
def query_optimized():
    """
    优化查询接口 - 使用完整的优化管道
    POST /api/v2/query/optimized
    
    请求体:
    {
        "query": "请介绍一下中芯国际的技术发展情况",
        "max_results": 20,
        "user_id": "user123",
        "enable_reranking": true,
        "enable_llm_generation": true,
        "enable_smart_filtering": true,
        "enable_source_filtering": true
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
        
        query = data.get('query', '').strip()
        max_results = data.get('max_results', 20)
        user_id = data.get('user_id', 'default_user')
        
        # 优化管道配置
        enable_reranking = data.get('enable_reranking', True)
        enable_llm_generation = data.get('enable_llm_generation', True)
        enable_smart_filtering = data.get('enable_smart_filtering', True)
        enable_source_filtering = data.get('enable_source_filtering', True)
        
        if not query:
            return jsonify({'error': '查询内容不能为空'}), 400
        
        # 获取混合引擎
        hybrid_engine = current_app.config.get('HYBRID_ENGINE')
        if not hybrid_engine:
            return jsonify({'error': '混合引擎未初始化'}), 500
        
        # 检查优化管道是否启用
        if not hybrid_engine.hybrid_config.enable_optimization_pipeline:
            return jsonify({'error': '优化管道未启用'}), 400
        
        # 执行优化查询
        start_time = time.time()
        result = hybrid_engine.process_query(query, max_results=max_results)
        processing_time = time.time() - start_time
        
        if result.status.value == 'ERROR':
            return jsonify({
                'success': False,
                'error': result.error_message or '查询执行失败'
            }), 500
        
        # 构建响应
        response = {
            'success': True,
            'query': query,
            'results': result.results,
            'total_count': len(result.results),
            'processing_time': processing_time,
            'query_type': result.query_type.value,
            'optimization_enabled': True,
            'optimization_details': result.metadata.get('optimization_details', {}),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"优化查询失败: {e}")
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
        hybrid_engine = current_app.config.get('HYBRID_ENGINE')
        if not hybrid_engine:
            return jsonify({'error': '混合引擎未初始化'}), 500
        
        # 获取混合引擎状态
        hybrid_status = hybrid_engine.get_hybrid_status()
        
        # 构建详细的引擎状态信息
        engines_status = {
            'hybrid_engine': {
                'name': hybrid_status.get('engine_name', 'hybrid_engine'),
                'version': hybrid_status.get('version', '2.0.0'),
                'status': hybrid_status.get('status', 'unknown'),
                'enabled': hybrid_status.get('enabled', False),
                'config': hybrid_status.get('config', {}),
                'optimization_pipeline': hybrid_status.get('config', {}).get('enable_optimization_pipeline', False)
            }
        }
        
        # 添加各子引擎状态
        if 'engines' in hybrid_status:
            for engine_type, engine_status in hybrid_status['engines'].items():
                engines_status[engine_type] = {
                    'name': engine_status.get('name', engine_type),
                    'version': engine_status.get('version', '2.0.0'),
                    'enabled': engine_status.get('enabled', True),
                    'config': engine_status.get('config', {}),
                    'status': 'ready' if engine_status.get('enabled', True) else 'disabled'
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


@v2_api_bp.route('/engines/optimization', methods=['GET'])
def get_optimization_status():
    """
    获取优化引擎状态
    GET /api/v2/engines/optimization
    """
    try:
        hybrid_engine = current_app.config.get('HYBRID_ENGINE')
        if not hybrid_engine:
            return jsonify({'error': '混合引擎未初始化'}), 500
        
        # 检查优化引擎状态
        optimization_status = {
            'reranking_engine': {
                'enabled': hybrid_engine.reranking_engine is not None,
                'status': 'ready' if hybrid_engine.reranking_engine else 'disabled',
                'config': hybrid_engine.reranking_engine.get_engine_status() if hybrid_engine.reranking_engine else {}
            },
            'llm_engine': {
                'enabled': hybrid_engine.llm_engine is not None,
                'status': 'ready' if hybrid_engine.llm_engine else 'disabled',
                'config': hybrid_engine.llm_engine.get_engine_status() if hybrid_engine.llm_engine else {}
            },
            'smart_filter_engine': {
                'enabled': hybrid_engine.smart_filter_engine is not None,
                'status': 'ready' if hybrid_engine.smart_filter_engine else 'disabled',
                'config': hybrid_engine.smart_filter_engine.get_engine_status() if hybrid_engine.smart_filter_engine else {}
            },
            'source_filter_engine': {
                'enabled': hybrid_engine.source_filter_engine is not None,
                'status': 'ready' if hybrid_engine.source_filter_engine else 'disabled',
                'config': hybrid_engine.source_filter_engine.get_engine_status() if hybrid_engine.source_filter_engine else {}
            }
        }
        
        # 检查优化管道配置
        pipeline_config = hybrid_engine.hybrid_config.optimization_pipeline if hybrid_engine.hybrid_config else None
        if pipeline_config:
            optimization_status['pipeline_config'] = {
                'enable_reranking': pipeline_config.enable_reranking,
                'enable_llm_generation': pipeline_config.enable_llm_generation,
                'enable_smart_filtering': pipeline_config.enable_smart_filtering,
                'enable_source_filtering': pipeline_config.enable_source_filtering,
                'pipeline_order': pipeline_config.pipeline_order
            }
        
        return jsonify({
            'success': True,
            'optimization_status': optimization_status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取优化引擎状态失败: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


@v2_api_bp.route('/engines/optimization/config', methods=['POST'])
def update_optimization_config():
    """
    更新优化引擎配置
    POST /api/v2/engines/optimization/config
    
    请求体:
    {
        "enable_reranking": true,
        "enable_llm_generation": true,
        "enable_smart_filtering": true,
        "enable_source_filtering": true,
        "reranking_config": {
            "similarity_threshold": 0.7,
            "top_k": 10
        },
        "llm_config": {
            "temperature": 0.7,
            "max_tokens": 2000
        }
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
        
        hybrid_engine = current_app.config.get('HYBRID_ENGINE')
        if not hybrid_engine:
            return jsonify({'error': '混合引擎未初始化'}), 500
        
        # 更新优化管道配置
        if 'enable_reranking' in data:
            hybrid_engine.hybrid_config.optimization_pipeline.enable_reranking = data['enable_reranking']
        
        if 'enable_llm_generation' in data:
            hybrid_engine.hybrid_config.optimization_pipeline.enable_llm_generation = data['enable_llm_generation']
        
        if 'enable_smart_filtering' in data:
            hybrid_engine.hybrid_config.optimization_pipeline.enable_smart_filtering = data['enable_smart_filtering']
        
        if 'enable_source_filtering' in data:
            hybrid_engine.hybrid_config.optimization_pipeline.enable_source_filtering = data['enable_source_filtering']
        
        # 更新重排序引擎配置
        if 'reranking_config' in data and hybrid_engine.reranking_engine:
            reranking_config = data['reranking_config']
            if 'similarity_threshold' in reranking_config:
                hybrid_engine.reranking_engine.config.similarity_threshold = reranking_config['similarity_threshold']
            if 'top_k' in reranking_config:
                hybrid_engine.reranking_engine.config.top_k = reranking_config['top_k']
        
        # 更新LLM引擎配置
        if 'llm_config' in data and hybrid_engine.llm_engine:
            llm_config = data['llm_config']
            if 'temperature' in llm_config:
                hybrid_engine.llm_engine.config.temperature = llm_config['temperature']
            if 'max_tokens' in llm_config:
                hybrid_engine.llm_engine.config.max_tokens = llm_config['max_tokens']
        
        return jsonify({
            'success': True,
            'message': '优化引擎配置更新成功',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"更新优化引擎配置失败: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


@v2_api_bp.route('/query/benchmark', methods=['POST'])
def benchmark_query():
    """
    查询性能基准测试接口
    POST /api/v2/query/benchmark
    
    请求体:
    {
        "query": "测试查询",
        "test_type": "optimized",  # "optimized", "standard", "hybrid"
        "iterations": 3
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
        
        query = data.get('query', '').strip()
        test_type = data.get('test_type', 'optimized')
        iterations = data.get('iterations', 3)
        
        if not query:
            return jsonify({'error': '查询内容不能为空'}), 400
        
        hybrid_engine = current_app.config.get('HYBRID_ENGINE')
        if not hybrid_engine:
            return jsonify({'error': '混合引擎未初始化'}), 500
        
        # 执行基准测试
        benchmark_results = []
        
        for i in range(iterations):
            start_time = time.time()
            
            if test_type == 'optimized':
                # 使用优化管道
                result = hybrid_engine.process_query(query, max_results=20)
            elif test_type == 'standard':
                # 使用标准混合查询
                result = hybrid_engine.process_query(query, max_results=20)
            else:
                # 使用混合查询
                result = hybrid_engine.process_query(query, max_results=20)
            
            processing_time = time.time() - start_time
            
            benchmark_results.append({
                'iteration': i + 1,
                'processing_time': processing_time,
                'result_count': len(result.results) if result.results else 0,
                'status': result.status.value if hasattr(result, 'status') else 'unknown'
            })
        
        # 计算统计信息
        processing_times = [r['processing_time'] for r in benchmark_results]
        avg_time = sum(processing_times) / len(processing_times)
        min_time = min(processing_times)
        max_time = max(processing_times)
        
        benchmark_summary = {
            'test_type': test_type,
            'iterations': iterations,
            'average_time': avg_time,
            'min_time': min_time,
            'max_time': max_time,
            'total_time': sum(processing_times),
            'results': benchmark_results
        }
        
        return jsonify({
            'success': True,
            'benchmark': benchmark_summary,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"基准测试失败: {e}")
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
            memory_manager.clear_context(user_id)
        elif memory_type == 'session':
            memory_manager.clear_context(user_id)
        elif memory_type == 'user':
            memory_manager.clear_context(user_id)
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
        
        question = data.get('question', data.get('query', '')).strip()
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
        
        # 根据查询类型执行查询
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
            'answer': _generate_answer_from_result(result, question, query_type),
            'sources': _extract_sources_from_result(result),
            'total_count': result.total_count if hasattr(result, 'total_count') else 0,
            'processing_time': processing_time,
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'use_memory': use_memory
        }
        
        # 添加优化管道的详细信息
        if hasattr(result, 'metadata') and result.metadata:
            response['metadata'] = result.metadata
            logger.info(f"添加优化管道元数据: {result.metadata}")
        else:
            logger.warning("QueryResult中没有metadata字段")
        
        if hasattr(result, 'error_message') and result.error_message:
            response['error'] = result.error_message
            response['success'] = False
        
        # 如果启用记忆功能，保存对话到记忆中
        if use_memory and hasattr(hybrid_engine, 'memory_manager'):
            try:
                answer_text = response.get('answer', '')
                if answer_text and not response.get('error'):
                    # 简化的记忆管理：只更新对话上下文
                    hybrid_engine.memory_manager.update_context(
                        user_id, question, answer_text
                    )
                    logger.info(f"对话上下文已更新")
                    
            except Exception as e:
                logger.warning(f"更新对话上下文失败: {e}")
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"V2问答接口错误: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


def _generate_answer_from_result(result, question, query_type):
    """
    从QueryResult生成可读的答案文本
    
    :param result: QueryResult对象
    :param question: 用户问题
    :param query_type: 查询类型
    :return: 生成的答案文本
    """
    if not result or not hasattr(result, 'results'):
        return "抱歉，未能找到相关答案。"
    
    if not result.results:
        return "抱歉，没有找到与您问题相关的内容。"
    
    # 根据查询类型生成不同的答案
    if query_type == 'image':
        return _generate_image_answer(result.results, question)
    elif query_type == 'text':
        return _generate_text_answer(result.results, question)
    elif query_type == 'table':
        return _generate_table_answer(result.results, question)
    else:  # hybrid
        return _generate_hybrid_answer(result.results, question)


def _generate_image_answer(results, question):
    """生成图片查询的答案"""
    if not results:
        return "抱歉，没有找到相关图片。"
    
    # 获取第一个结果
    first_result = results[0]
    
    # 构建答案
    answer = f"根据您的问题，我找到了以下图片信息：\n\n"
    
    # 检查结果结构
    if isinstance(first_result, dict):
        # 直接是字典结构
        caption = first_result.get('caption', [])
        enhanced_description = first_result.get('enhanced_description', '')
        image_path = first_result.get('image_path', '')
        
        if caption:
            if isinstance(caption, list):
                answer += f"**图片标题**: {caption[0]}\n\n"
            else:
                answer += f"**图片标题**: {caption}\n\n"
        
        if enhanced_description:
            # 提取关键信息
            lines = enhanced_description.split('\n')
            key_info = []
            for line in lines:
                if '|' in line and any(keyword in line for keyword in ['图表类型', '数据趋势', '语义特征']):
                    key_info.append(line.strip())
            
            if key_info:
                answer += "**关键信息**:\n"
                for info in key_info[:3]:  # 只显示前3条关键信息
                    answer += f"- {info}\n"
                answer += "\n"
            
            # 添加基础描述
            basic_desc = ""
            for line in lines:
                if "基础视觉描述" in line:
                    basic_desc = line.split(":", 1)[1].strip() if ":" in line else ""
                    break
            
            if basic_desc:
                answer += f"**图片描述**: {basic_desc}\n\n"
        
        answer += f"总共找到 {len(results)} 张相关图片。"
        return answer
    
    elif hasattr(first_result, 'content'):
        # 有content属性的对象
        content = first_result.content
        if isinstance(content, dict):
            caption = content.get('caption', [])
            enhanced_description = content.get('enhanced_description', '')
            
            if caption:
                answer += f"**图片标题**: {caption[0] if isinstance(caption, list) else caption}\n\n"
            
            if enhanced_description:
                # 提取关键信息
                lines = enhanced_description.split('\n')
                key_info = []
                for line in lines:
                    if '|' in line and any(keyword in line for keyword in ['图表类型', '数据趋势', '语义特征']):
                        key_info.append(line.strip())
                
                if key_info:
                    answer += "**关键信息**:\n"
                    for info in key_info[:3]:  # 只显示前3条关键信息
                        answer += f"- {info}\n"
                    answer += "\n"
                
                # 添加基础描述
                basic_desc = ""
                for line in lines:
                    if "基础视觉描述" in line:
                        basic_desc = line.split(":", 1)[1].strip() if ":" in line else ""
                        break
                
                if basic_desc:
                    answer += f"**图片描述**: {basic_desc}\n\n"
            
            answer += f"总共找到 {len(results)} 张相关图片。"
            return answer
    
    return f"找到 {len(results)} 张相关图片，但无法提取详细信息。"


def _generate_text_answer(results, question):
    """生成文本查询的答案"""
    if not results:
        return "抱歉，没有找到相关文本内容。"
    
    answer = f"根据您的问题，我找到了以下相关内容：\n\n"
    
    for i, result in enumerate(results[:3], 1):  # 只显示前3个结果
        if hasattr(result, 'content'):
            content = result.content
            if isinstance(content, dict):
                text_content = content.get('page_content', '')
                if text_content:
                    # 截取前200个字符
                    preview = text_content[:200] + "..." if len(text_content) > 200 else text_content
                    answer += f"**结果 {i}**:\n{preview}\n\n"
    
    answer += f"总共找到 {len(results)} 条相关文本内容。"
    return answer


def _generate_table_answer(results, question):
    """生成表格查询的答案"""
    if not results:
        return "抱歉，没有找到相关表格内容。"
    
    answer = f"根据您的问题，我找到了以下相关表格：\n\n"
    
    for i, result in enumerate(results[:2], 1):  # 只显示前2个结果
        if hasattr(result, 'content'):
            content = result.content
            if isinstance(content, dict):
                table_content = content.get('page_content', '')
                if table_content:
                    # 截取前300个字符
                    preview = table_content[:300] + "..." if len(table_content) > 300 else table_content
                    answer += f"**表格 {i}**:\n{preview}\n\n"
    
    answer += f"总共找到 {len(results)} 个相关表格。"
    return answer


def _generate_hybrid_answer(results, question):
    """生成混合查询的答案"""
    if not results:
        return "抱歉，没有找到相关内容。"
    
    # 检查是否有LLM生成的答案（优化管道的输出）
    llm_answer = ""
    for result in results:
        if isinstance(result, dict) and result.get('type') == 'llm_answer':
            llm_answer = result.get('content', '')
            break
        elif hasattr(result, 'type') and getattr(result, 'type') == 'llm_answer':
            llm_answer = getattr(result, 'content', '')
            break
    
    # 如果有LLM答案，优先使用它
    if llm_answer:
        return llm_answer
    
    # 统计不同类型的结果
    image_count = sum(1 for r in results if getattr(r, 'type', '') == 'image')
    text_count = sum(1 for r in results if getattr(r, 'type', '') == 'text')
    table_count = sum(1 for r in results if getattr(r, 'type', '') == 'table')
    
    answer = f"根据您的问题，我进行了综合分析，找到了以下内容：\n\n"
    
    if image_count > 0:
        answer += f"📊 **图片内容**: {image_count} 张相关图片\n"
    if text_count > 0:
        answer += f"📝 **文本内容**: {text_count} 条相关文本\n"
    if table_count > 0:
        answer += f"📋 **表格内容**: {table_count} 个相关表格\n"
    
    answer += "\n"
    
    # 显示最相关的结果
    if results:
        best_result = results[0]
        if hasattr(best_result, 'content'):
            content = best_result.content
            if isinstance(content, dict):
                if 'enhanced_description' in content:
                    # 图片结果
                    desc = content['enhanced_description']
                    lines = desc.split('\n')
                    for line in lines:
                        if "基础视觉描述" in line:
                            basic_desc = line.split(":", 1)[1].strip() if ":" in line else ""
                            if basic_desc:
                                answer += f"**主要发现**: {basic_desc}\n\n"
                                break
                elif 'page_content' in content:
                    # 文本或表格结果
                    text_content = content['page_content']
                    preview = text_content[:200] + "..." if len(text_content) > 200 else text_content
                    answer += f"📝 **主要内容**: {preview}\n\n"
    
    answer += f"总共找到 {len(results)} 条相关内容，建议您查看详细结果获取更多信息。"
    return answer


def _extract_sources_from_result(result):
    """
    从QueryResult提取来源信息
    
    :param result: QueryResult对象
    :return: 来源信息列表
    """
    if not result or not hasattr(result, 'results'):
        return []
    
    sources = []
    for doc in result.results:
        if isinstance(doc, dict):
            # 直接是字典结构（图片引擎返回的结果）
            if 'enhanced_description' in doc:
                # 图片文档
                sources.append({
                    'title': doc.get('caption', ['无标题'])[0] if doc.get('caption') else '图片',
                    'page_number': doc.get('page_number', 'N/A'),
                    'document_name': doc.get('document_name', 'N/A'),
                    'source_type': 'image',
                    'score': doc.get('score', 0.0),
                    'image_path': doc.get('image_path', ''),
                    'enhanced_description': doc.get('enhanced_description', '')[:100] + '...' if len(doc.get('enhanced_description', '')) > 100 else doc.get('enhanced_description', '')
                })
            elif 'page_content' in doc:
                # 文本或表格文档
                sources.append({
                    'title': doc.get('title', '文档'),
                    'page_number': doc.get('page_number', 'N/A'),
                    'document_name': doc.get('document_name', 'N/A'),
                    'source_type': doc.get('chunk_type', 'text'),
                    'score': doc.get('score', 0.0),
                    'content_preview': doc.get('page_content', '')[:200] + '...' if len(doc.get('page_content', '')) > 200 else doc.get('page_content', '')
                })
            elif 'content' in doc:
                # 文本或表格文档（修复后的格式）
                sources.append({
                    'title': doc.get('title', '文档'),
                    'page_number': doc.get('page_number', 'N/A'),
                    'document_name': doc.get('document_name', 'N/A'),
                    'source_type': doc.get('chunk_type', 'text'),
                    'score': doc.get('score', 0.0),
                    'content_preview': doc.get('content', '')[:200] + '...' if len(doc.get('content', '')) > 200 else doc.get('content', '')
                })
            else:
                sources.append({
                    'title': '未知文档',
                    'page_number': 'N/A',
                    'document_name': 'N/A',
                    'source_type': 'unknown',
                    'score': doc.get('score', 0.0)
                })
        elif hasattr(doc, 'content'):
            # 有content属性的对象
            content = doc.content
            if isinstance(content, dict):
                if 'enhanced_description' in content:
                    # 图片文档
                    sources.append({
                        'title': content.get('caption', ['无标题'])[0] if content.get('caption') else '图片',
                        'page_number': content.get('page_number', 'N/A'),
                        'document_name': content.get('document_name', 'N/A'),
                        'source_type': 'image',
                        'score': getattr(doc, 'relevance_score', 0.0),
                        'image_path': content.get('image_path', ''),
                        'enhanced_description': content.get('enhanced_description', '')[:100] + '...' if len(content.get('enhanced_description', '')) > 100 else content.get('enhanced_description', '')
                    })
                elif 'page_content' in content:
                    # 文本或表格文档
                    sources.append({
                        'title': content.get('title', '文档'),
                        'page_number': content.get('page_number', 'N/A'),
                        'document_name': content.get('document_name', 'N/A'),
                        'source_type': content.get('chunk_type', 'text'),
                        'score': getattr(doc, 'relevance_score', 0.0),
                        'content_preview': content.get('page_content', '')[:200] + '...' if len(content.get('page_content', '')) > 200 else content.get('page_content', '')
                    })
                else:
                    sources.append({
                        'title': '未知文档',
                        'page_number': 'N/A',
                        'document_name': 'N/A',
                        'source_type': 'unknown',
                        'score': getattr(doc, 'relevance_score', 0.0)
                    })
            else:
                sources.append({
                    'title': '未知文档',
                    'page_number': 'N/A',
                    'document_name': 'N/A',
                    'source_type': 'unknown',
                    'score': getattr(doc, 'relevance_score', 0.0)
                })
        else:
            sources.append({
                'title': '未知文档',
                'page_number': 'N/A',
                'document_name': 'N/A',
                'source_type': 'unknown',
                'score': getattr(doc, 'relevance_score', 0.0)
            })
    
    return sources


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
