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
from v2.core.base_engine import QueryType

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
            'intelligent_post_processing_engine_ready': hybrid_engine.intelligent_post_processing_engine is not None if hybrid_engine else False,
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


@v2_api_bp.route('/system/shutdown', methods=['POST'])
def shutdown_system():
    """
    优雅关闭V2.0系统
    POST /api/v2/system/shutdown
    
    请求体:
    {
        "reason": "用户主动关闭",
        "cleanup_memory": true,
        "save_state": true
    }
    """
    try:
        data = request.get_json() or {}
        reason = data.get('reason', '用户主动关闭')
        cleanup_memory = data.get('cleanup_memory', True)
        save_state = data.get('save_state', True)
        
        logger.info(f"收到系统关闭请求: {reason}")
        
        # 获取混合引擎实例
        hybrid_engine = current_app.config.get('HYBRID_ENGINE')
        
        # 执行清理工作
        if hybrid_engine and cleanup_memory:
            try:
                # 清理记忆管理器
                if hasattr(hybrid_engine, 'memory_manager') and hybrid_engine.memory_manager:
                    logger.info("正在清理记忆管理器...")
                    hybrid_engine.memory_manager.clear_all_memories()
                    logger.info("记忆管理器清理完成")
                
                # 清理文档缓存
                if hasattr(hybrid_engine, 'document_loader') and hybrid_engine.document_loader:
                    logger.info("正在清理文档缓存...")
                    hybrid_engine.document_loader.clear_cache()
                    logger.info("文档缓存清理完成")
                
                # 清理各引擎缓存
                for engine_name in ['text_engine', 'image_engine', 'table_engine']:
                    if hasattr(hybrid_engine, engine_name) and getattr(hybrid_engine, engine_name):
                        engine = getattr(hybrid_engine, engine_name)
                        if hasattr(engine, 'clear_cache'):
                            logger.info(f"正在清理{engine_name}缓存...")
                            engine.clear_cache()
                            logger.info(f"{engine_name}缓存清理完成")
                
            except Exception as e:
                logger.warning(f"清理过程中出现警告: {e}")
        
        # 保存系统状态
        if save_state:
            try:
                logger.info("正在保存系统状态...")
                # 这里可以添加保存系统状态的逻辑
                logger.info("系统状态保存完成")
            except Exception as e:
                logger.warning(f"保存系统状态时出现警告: {e}")
        
        # 记录关闭日志
        logger.info(f"V2.0系统优雅关闭完成: {reason}")
        
        # 返回成功响应
        return jsonify({
            'success': True,
            'message': '系统关闭请求已处理',
            'cleanup_completed': cleanup_memory,
            'state_saved': save_state,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"系统关闭处理失败: {e}")
        return jsonify({
            'success': False,
            'error': f'系统关闭失败: {str(e)}'
        }), 500


@v2_api_bp.route('/system/exit', methods=['POST'])
def exit_system():
    """
    真正退出V2.0系统（关闭Web服务）
    POST /api/v2/system/exit
    
    请求体:
    {
        "reason": "用户主动退出",
        "cleanup_memory": true,
        "save_state": true
    }
    """
    try:
        data = request.get_json() or {}
        reason = data.get('reason', '用户主动退出')
        cleanup_memory = data.get('cleanup_memory', True)
        save_state = data.get('save_state', True)
        
        logger.info(f"收到系统退出请求: {reason}")
        
        # 获取混合引擎实例
        hybrid_engine = current_app.config.get('HYBRID_ENGINE')
        
        # 执行清理工作
        if hybrid_engine and cleanup_memory:
            try:
                # 清理记忆管理器
                if hasattr(hybrid_engine, 'memory_manager') and hybrid_engine.memory_manager:
                    logger.info("正在清理记忆管理器...")
                    hybrid_engine.memory_manager.clear_all_memories()
                    logger.info("记忆管理器清理完成")
                
                # 清理文档缓存
                if hasattr(hybrid_engine, 'document_loader') and hybrid_engine.document_loader:
                    logger.info("正在清理文档缓存...")
                    hybrid_engine.document_loader.clear_cache()
                    logger.info("文档缓存清理完成")
                
                # 清理各引擎缓存
                for engine_name in ['text_engine', 'image_engine', 'table_engine']:
                    if hasattr(hybrid_engine, engine_name) and getattr(hybrid_engine, engine_name):
                        engine = getattr(hybrid_engine, engine_name)
                        if hasattr(engine, 'clear_cache'):
                            logger.info(f"正在清理{engine_name}缓存...")
                            engine.clear_cache()
                            logger.info(f"{engine_name}缓存清理完成")
                
            except Exception as e:
                logger.warning(f"清理过程中出现警告: {e}")
        
        # 保存系统状态
        if save_state:
            try:
                logger.info("正在保存系统状态...")
                # 这里可以添加保存系统状态的逻辑
                logger.info("系统状态保存完成")
            except Exception as e:
                logger.warning(f"保存系统状态时出现警告: {e}")
        
        # 记录退出日志
        logger.info(f"V2.0系统准备退出: {reason}")
        
        # 启动后台任务来关闭Flask应用
        import threading
        import time
        
        # 获取真实的Flask应用实例
        app_instance = current_app._get_current_object()
        
        def delayed_shutdown(app):
            """延迟关闭Flask应用"""
            time.sleep(1)  # 等待1秒，确保响应能够返回给客户端
            logger.info("正在关闭Flask Web服务...")
            
            # 在新线程中推入应用上下文
            with app.app_context():
                func = app.config.get('SHUTDOWN_FUNC')
                if func:
                    func()
                else:
                    logger.warning("未找到关闭函数，尝试强制退出")
                    import os
                    os._exit(0)
        
        # 启动后台关闭任务，并传入app_instance
        shutdown_thread = threading.Thread(target=delayed_shutdown, args=(app_instance,), daemon=True)
        shutdown_thread.start()
        
        # 返回成功响应
        return jsonify({
            'success': True,
            'message': '系统退出请求已处理，Web服务将在1秒后关闭',
            'cleanup_completed': cleanup_memory,
            'state_saved': save_state,
            'shutdown_scheduled': True,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"系统退出处理失败: {e}")
        return jsonify({
            'success': False,
            'error': f'系统退出失败: {str(e)}'
        }), 500


@v2_api_bp.route('/system/restart', methods=['POST'])
def restart_system():
    """
    重启V2.0系统
    POST /api/v2/system/restart
    
    请求体:
    {
        "reason": "用户主动重启",
        "cleanup_before_restart": true
    }
    """
    try:
        data = request.get_json() or {}
        reason = data.get('reason', '用户主动重启')
        cleanup_before_restart = data.get('cleanup_before_restart', True)
        
        logger.info(f"收到系统重启请求: {reason}")
        
        # 获取混合引擎实例
        hybrid_engine = current_app.config.get('HYBRID_ENGINE')
        
        # 重启前清理
        if hybrid_engine and cleanup_before_restart:
            try:
                # 清理记忆管理器
                if hasattr(hybrid_engine, 'memory_manager') and hybrid_engine.memory_manager:
                    logger.info("重启前清理记忆管理器...")
                    hybrid_engine.memory_manager.clear_all_memories()
                    logger.info("记忆管理器清理完成")
                
                # 清理文档缓存
                if hasattr(hybrid_engine, 'document_loader') and hybrid_engine.document_loader:
                    logger.info("重启前清理文档缓存...")
                    hybrid_engine.document_loader.clear_cache()
                    logger.info("文档缓存清理完成")
                
            except Exception as e:
                logger.warning(f"重启前清理过程中出现警告: {e}")
        
        # 记录重启日志
        logger.info(f"V2.0系统重启请求已处理: {reason}")
        
        # 返回成功响应
        return jsonify({
            'success': True,
            'message': '系统重启请求已处理',
            'cleanup_completed': cleanup_before_restart,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"系统重启处理失败: {e}")
        return jsonify({
            'success': False,
            'error': f'系统重启失败: {str(e)}'
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
        
        # 获取混合引擎
        hybrid_engine = current_app.config.get('HYBRID_ENGINE')
        if not hybrid_engine:
            return jsonify({'error': '混合引擎未初始化'}), 500
        
        # 通过混合引擎执行图片查询，确保经过优化管道处理
        start_time = time.time()
        result = hybrid_engine.process_query(
            query, 
            query_type=QueryType.IMAGE,
            max_results=max_results
        )
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
            # 从混合引擎结果中提取图片相关的结果
            for doc in result.results:
                # 检查是否是图片类型的结果
                chunk_type = doc.get('chunk_type', '')
                if chunk_type == 'image' or 'enhanced_description' in doc:
                    # 构建图片结果
                    image_result = {
                        'image_path': doc.get('image_path', ''),
                        'caption': doc.get('caption', ['无标题']),
                        'enhanced_description': doc.get('enhanced_description', ''),
                        'document_name': doc.get('document_name', '未知文档'),  # 使用正确的文档名称
                        'page_number': doc.get('page_number', 'N/A'),
                        'score': doc.get('score', 0.0),
                        'doc_id': doc.get('doc_id', ''),
                        'title': doc.get('title', '无标题')
                    }
                    response['results'].append(image_result)
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
        
        # 获取混合引擎
        hybrid_engine = current_app.config.get('HYBRID_ENGINE')
        if not hybrid_engine:
            return jsonify({'error': '混合引擎未初始化'}), 500
        
        # 通过混合引擎执行文本查询，确保经过优化管道处理
        start_time = time.time()
        result = hybrid_engine.process_query(
            query, 
            query_type=QueryType.TEXT,
            max_results=max_results
        )
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
            # 从混合引擎结果中提取文本相关的结果
            for doc in result.results:
                # 检查是否是文本类型的结果
                if isinstance(doc, dict):
                    # 处理嵌套文档结构
                    if 'doc' in doc and isinstance(doc['doc'], dict):
                        actual_doc = doc['doc']
                        chunk_type = actual_doc.get('chunk_type', 'text')
                        if chunk_type == 'text':  # 只处理文本类型
                            doc_info = {
                                'id': doc.get('doc_id', 'unknown'),
                                'content': actual_doc.get('page_content', '')[:200] + '...' if len(actual_doc.get('page_content', '')) > 200 else actual_doc.get('page_content', ''),
                                'document_name': actual_doc.get('document_name', 'N/A'),
                                'page_number': actual_doc.get('page_number', 'N/A'),
                                'chunk_type': chunk_type,
                                'score': doc.get('score', 0.0)
                            }
                            response['results'].append(doc_info)
                    else:
                        # 直接处理文档
                        chunk_type = doc.get('chunk_type', 'text')
                        if chunk_type == 'text':  # 只处理文本类型
                            doc_info = {
                                'id': doc.get('doc_id', 'unknown'),
                                'content': doc.get('page_content', '')[:200] + '...' if len(doc.get('page_content', '')) > 200 else doc.get('page_content', ''),
                                'document_name': doc.get('document_name', 'N/A'),
                                'page_number': doc.get('page_number', 'N/A'),
                                'chunk_type': chunk_type,
                                'score': doc.get('score', 0.0)
                            }
                            response['results'].append(doc_info)
                elif hasattr(doc, 'metadata'):
                    # Document对象
                    chunk_type = doc.metadata.get('chunk_type', 'text')
                    if chunk_type == 'text':  # 只处理文本类型
                        doc_info = {
                            'id': getattr(doc, 'doc_id', 'unknown'),
                            'content': doc.page_content[:200] + '...' if len(doc.page_content) > 200 else doc.page_content,
                            'document_name': doc.metadata.get('document_name', 'N/A'),
                            'page_number': doc.metadata.get('page_number', 'N/A'),
                            'chunk_type': chunk_type,
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
        
        # 获取混合引擎
        hybrid_engine = current_app.config.get('HYBRID_ENGINE')
        if not hybrid_engine:
            return jsonify({'error': '混合引擎未初始化'}), 500
        
        # 通过混合引擎执行表格查询，确保经过优化管道处理
        start_time = time.time()
        result = hybrid_engine.process_query(
            query, 
            query_type=QueryType.TABLE,
            max_results=max_results
        )
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
            # 从混合引擎结果中提取表格相关的结果
            for doc in result.results:
                # 检查是否是表格类型的结果
                if isinstance(doc, dict):
                    # 处理嵌套文档结构
                    if 'doc' in doc and isinstance(doc['doc'], dict):
                        actual_doc = doc['doc']
                        chunk_type = actual_doc.get('chunk_type', 'table')
                        if chunk_type == 'table':  # 只处理表格类型
                            doc_info = {
                                'id': doc.get('doc_id', 'unknown'),
                                'table_content': actual_doc.get('page_content', '')[:300] + '...' if len(actual_doc.get('page_content', '')) > 300 else actual_doc.get('page_content', ''),
                                'document_name': actual_doc.get('document_name', 'N/A'),
                                'page_number': actual_doc.get('page_number', 'N/A'),
                                'chunk_type': chunk_type,
                                'table_type': actual_doc.get('table_type', '数据表格'),
                                'score': doc.get('score', 0.0)
                            }
                            response['results'].append(doc_info)
                    else:
                        # 直接处理文档
                        chunk_type = doc.get('chunk_type', 'table')
                        if chunk_type == 'table':  # 只处理表格类型
                            doc_info = {
                                'id': doc.get('doc_id', 'unknown'),
                                'table_content': doc.get('page_content', '')[:300] + '...' if len(doc.get('page_content', '')) > 300 else doc.get('page_content', ''),
                                'document_name': doc.get('document_name', 'N/A'),
                                'page_number': doc.get('page_number', 'N/A'),
                                'chunk_type': chunk_type,
                                'table_type': doc.get('table_type', '数据表格'),
                                'score': doc.get('score', 0.0)
                            }
                            response['results'].append(doc_info)
                elif hasattr(doc, 'metadata'):
                    # Document对象
                    chunk_type = doc.metadata.get('chunk_type', 'table')
                    if chunk_type == 'table':  # 只处理表格类型
                        doc_info = {
                            'id': getattr(doc, 'doc_id', 'unknown'),
                            'table_content': doc.page_content[:300] + '...' if len(doc.page_content) > 300 else doc.page_content,
                            'document_name': doc.metadata.get('document_name', 'N/A'),
                            'page_number': doc.metadata.get('page_number', 'N/A'),
                            'chunk_type': chunk_type,
                            'table_type': doc.metadata.get('table_type', '数据表格'),
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
        
        # 获取所有引擎 - 从混合引擎中获取子引擎
        engines = {}
        hybrid_engine = current_app.config.get('HYBRID_ENGINE')
        
        if not hybrid_engine:
            return jsonify({'error': '混合引擎未初始化'}), 500
        
        if 'image' in include_types:
            engines['image'] = hybrid_engine.image_engine
        if 'text' in include_types:
            engines['text'] = hybrid_engine.text_engine
        if 'table' in include_types:
            engines['table'] = hybrid_engine.table_engine
        
        if not engines:
            return jsonify({'error': '没有可用的查询引擎'}), 500
        
        # 并行执行查询
        start_time = time.time()
        results = {}
        
        def execute_query(engine_type, engine):
            try:
                if engine:
                    # 为Image Engine传递真实的引擎实例
                    kwargs = {}
                    if engine_type == 'image':
                        # 从混合引擎获取LLM引擎和源过滤引擎
                        if hasattr(hybrid_engine, 'llm_engine'):
                            kwargs['llm_engine'] = hybrid_engine.llm_engine
                        if hasattr(hybrid_engine, 'source_filter_engine'):
                            kwargs['source_filter_engine'] = hybrid_engine.source_filter_engine
                    
                    result = engine.process_query(query, max_results=max_results//len(engines), **kwargs)
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
            result = hybrid_engine.process_query(question, query_type='hybrid', max_results=max_results)
        elif query_type == 'image':
            # 通过混合引擎执行图片查询，确保经过优化管道处理
            result = hybrid_engine.process_query(question, query_type=QueryType.IMAGE, max_results=max_results)
        elif query_type == 'text':
            # 通过混合引擎执行文本查询，确保经过优化管道处理
            result = hybrid_engine.process_query(question, query_type=QueryType.TEXT, max_results=max_results)
        elif query_type == 'table':
            # 通过混合引擎执行表格查询，确保经过优化管道处理
            result = hybrid_engine.process_query(question, query_type=QueryType.TABLE, max_results=max_results)
        elif query_type == 'smart':
            try:
                # 使用 QueryIntentAnalyzer 进行智能意图分析
                from v2.core.hybrid_engine import QueryIntentAnalyzer
                intent_analyzer = QueryIntentAnalyzer()
                
                # 分析查询意图，获取最佳查询类型
                intent_result = intent_analyzer.analyze_intent_with_confidence(question)
                detected_type = intent_result['primary_intent']
                
                logger.info(f"智能查询检测到类型: {detected_type}")
                
                # 根据检测到的类型执行查询
                if detected_type == 'image':
                    result = hybrid_engine.process_query(question, query_type=QueryType.IMAGE, max_results=max_results)
                elif detected_type == 'table':
                    result = hybrid_engine.process_query(question, query_type=QueryType.TABLE, max_results=max_results)
                elif detected_type == 'text':
                    result = hybrid_engine.process_query(question, query_type=QueryType.TEXT, max_results=max_results)
                else:
                    # 默认使用混合查询
                    result = hybrid_engine.process_query(question, query_type=QueryType.HYBRID, max_results=max_results)
                    
            except Exception as e:
                logger.error(f"智能查询处理失败: {e}")
                # 降级策略：使用混合查询
                result = hybrid_engine.process_query(question, query_type=QueryType.HYBRID, max_results=max_results)
        else:
            return jsonify({'error': f'不支持的查询类型: {query_type}'}), 400
        
        processing_time = time.time() - start_time
        
        # 格式化响应
        response = {
            'success': True,
            'question': question,
            'query_type': query_type,
            'answer': _generate_answer_from_result(result, question, query_type, result.metadata if hasattr(result, 'metadata') else None),
            'sources': _extract_sources_from_result(result),
            'total_count': result.total_count if hasattr(result, 'total_count') else 0,
            'processing_time': processing_time,
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'use_memory': use_memory
        }
        
        # 添加图片结果到响应中，用于前端显示
        if hasattr(result, 'results') and result.results:
            image_results = []
            for doc in result.results:
                if isinstance(doc, dict):
                    # 检查是否是图片类型的结果
                    chunk_type = doc.get('chunk_type', '')
                    if chunk_type == 'image' or 'enhanced_description' in doc:
                        # 构建图片结果
                        image_result = {
                            'image_path': doc.get('image_path', ''),
                            'caption': doc.get('img_caption', ['无标题']),  # 修复：使用正确的字段名img_caption
                            'enhanced_description': doc.get('enhanced_description', ''),
                            'document_name': doc.get('document_name', '未知文档'),  # 使用正确的文档名称
                            'page_number': doc.get('page_number', 'N/A'),
                            'score': doc.get('score', 0.0),
                            'doc_id': doc.get('doc_id', ''),
                            'title': doc.get('title', '无标题')
                        }
                        image_results.append(image_result)
                    # 检查嵌套的doc结构
                    elif 'doc' in doc and isinstance(doc['doc'], dict):
                        actual_doc = doc['doc']
                        chunk_type = actual_doc.get('chunk_type', '')
                        if chunk_type == 'image' or 'enhanced_description' in actual_doc:
                            image_result = {
                                'image_path': actual_doc.get('image_path', ''),
                                'caption': actual_doc.get('img_caption', ['无标题']),  # 修复：使用正确的字段名img_caption
                                'enhanced_description': actual_doc.get('enhanced_description', ''),
                                'title': actual_doc.get('title', ''),
                                'document_name': actual_doc.get('document_name', '未知文档'),  # 使用正确的文档名称
                                'page_number': actual_doc.get('page_number', 'N/A'),
                                'score': doc.get('score', 0.0),
                                'doc_id': actual_doc.get('doc_id', ''),
                                'title': actual_doc.get('title', '无标题')
                            }
                            image_results.append(image_result)
            
            if image_results:
                response['image_results'] = image_results
                logger.info(f"添加了 {len(image_results)} 个图片结果到响应中")
        
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


def _generate_answer_from_result(result, question, query_type, metadata=None):
    """
    从QueryResult生成可读的答案文本
    
    :param result: QueryResult对象
    :param question: 用户问题
    :param query_type: 查询类型
    :param metadata: 结果元数据，包含LLM答案等信息
    :return: 生成的答案文本
    """
    if not result or not hasattr(result, 'results'):
        return "抱歉，未能找到相关答案。"
    
    if not result.results:
        return "抱歉，没有找到与您问题相关的内容。"
    
    # 首先尝试从result.metadata中获取LLM答案
    if hasattr(result, 'metadata') and result.metadata:
        llm_answer = result.metadata.get('llm_answer', '')
        if llm_answer:
            logger.info(f"从result.metadata中找到LLM答案，长度: {len(llm_answer)}")
            return llm_answer
    
    # 然后尝试从传入的metadata参数中获取
    if metadata and isinstance(metadata, dict):
        llm_answer = metadata.get('llm_answer', '')
        if llm_answer:
            logger.info(f"从传入的metadata中找到LLM答案，长度: {len(llm_answer)}")
            return llm_answer
    
    # 根据查询类型生成不同的答案
    if query_type == 'image':
        return _generate_image_answer(result.results, question)
    elif query_type == 'text':
        return _generate_text_answer(result.results, question)
    elif query_type == 'table':
        return _generate_table_answer(result.results, question)
    else:  # hybrid
        return _generate_hybrid_answer(result.results, question, metadata)


def _generate_image_answer(results, question):
    """生成图片查询的答案"""
    if not results:
        return "抱歉，没有找到相关图片。"
    
    # 获取第一个结果
    first_result = results[0]
    
    # 构建简洁的答案，不包含详细图片信息
    answer = f"根据您的问题，我找到了 {len(results)} 张相关图片。\n\n"
    
    # 检查结果结构，只添加基本信息
    if isinstance(first_result, dict):
        # 直接是字典结构
        caption = first_result.get('caption', [])
        
        if caption:
            if isinstance(caption, list):
                answer += f"主要图片：{caption[0]}\n\n"
            else:
                answer += f"主要图片：{caption}\n\n"
        
        # 添加基础描述，但不包含详细信息
        answer += "图片内容已在下方的图片展示区显示，您可以查看具体的图表内容和详细信息。"
    
    elif hasattr(first_result, 'content'):
        # 有content属性的对象
        content = first_result.content
        if isinstance(content, dict):
            caption = content.get('caption', [])
            
            if caption:
                answer += f"主要图片：{caption[0] if isinstance(caption, list) else caption}\n\n"
            
            # 添加基础描述，但不包含详细信息
            answer += "图片内容已在下方的图片展示区显示，您可以查看具体的图表内容和详细信息。"
    
    return answer


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


def _generate_hybrid_answer(results, question, result_metadata=None):
    """生成混合查询的答案"""
    if not results:
        return "抱歉，没有找到相关内容。"
    
    # 检查是否有LLM生成的答案（优化管道的输出）
    llm_answer = ""
    
    # 首先从元数据中获取LLM答案
    if result_metadata and isinstance(result_metadata, dict):
        llm_answer = result_metadata.get('llm_answer', '')
        if llm_answer:
            logger.info(f"从元数据中找到LLM答案，长度: {len(llm_answer)}")
            return llm_answer
    
    # 然后检查结果中是否有LLM答案
    for result in results:
        if isinstance(result, dict) and result.get('type') == 'llm_answer':
            llm_answer = result.get('content', '')
            break
        elif hasattr(result, 'type') and getattr(result, 'type') == 'llm_answer':
            llm_answer = getattr(result, 'content', '')
            break
    
    # 如果有LLM答案，优先使用它
    if llm_answer:
        logger.info(f"从结果中找到LLM答案，长度: {len(llm_answer)}")
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
    
    # 显示最相关的结果，但不包含详细的图片信息
    if results:
        best_result = results[0]
        if hasattr(best_result, 'content'):
            content = best_result.content
            if isinstance(content, dict):
                if 'enhanced_description' in content:
                    # 图片结果 - 只显示基本信息，详细内容通过image_results显示
                    answer += "**主要发现**: 相关图片内容已在下方的图片展示区显示，您可以查看具体的图表内容和详细信息。\n\n"
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
        logger.debug(f"处理文档: {type(doc)}, 内容: {str(doc)[:100]}")
        
        if isinstance(doc, dict):
            # 直接是字典结构
            if 'enhanced_description' in doc:
                # 图片文档
                # 尝试获取真实的文档名称
                document_name = doc.get('document_name', 'N/A')
                if document_name == 'N/A' or document_name == '未知文档':
                    document_name = doc.get('source', '') or doc.get('doc_id', '') or '未知文档'
                
                sources.append({
                    'title': doc.get('img_caption', ['无标题'])[0] if doc.get('img_caption') else '无标题',
                    'document_name': document_name,
                    'page_number': doc.get('page_number', 'N/A'),
                    'source_type': 'image',
                    'score': doc.get('score', 0.0),
                    'image_path': doc.get('image_path', ''),
                    'formatted_source': _format_source_display(document_name, doc.get('img_caption', ['无标题'])[0] if doc.get('img_caption') else '无标题', doc.get('page_number', 'N/A'), 'image')
                })
            elif 'page_content' in doc:
                # 文本或表格文档
                chunk_type = doc.get('chunk_type', 'text')
                # 尝试获取真实的文档名称
                document_name = doc.get('document_name', 'N/A')
                if document_name == 'N/A' or document_name == '未知文档':
                    document_name = doc.get('source', '') or doc.get('doc_id', '') or '未知文档'
                
                sources.append({
                    'title': doc.get('title', '文档'),
                    'page_number': doc.get('page_number', 'N/A'),
                    'document_name': document_name,
                    'source_type': chunk_type,
                    'score': doc.get('score', 0.0),
                    'content_preview': doc.get('page_content', '')[:200] + '...' if len(doc.get('page_content', '')) > 200 else doc.get('page_content', ''),
                    'formatted_source': _format_source_display(document_name, doc.get('page_content', '')[:100], doc.get('page_number', 'N/A'), chunk_type)
                })
            elif 'content' in doc:
                # 文本或表格文档（修复后的格式）
                chunk_type = doc.get('chunk_type', 'text')
                # 尝试获取真实的文档名称
                document_name = doc.get('document_name', 'N/A')
                if document_name == 'N/A' or document_name == '未知文档':
                    document_name = doc.get('source', '') or doc.get('doc_id', '') or '未知文档'
                
                sources.append({
                    'title': doc.get('title', '文档'),
                    'page_number': doc.get('page_number', 'N/A'),
                    'document_name': document_name,
                    'source_type': chunk_type,
                    'score': doc.get('score', 0.0),
                    'content_preview': doc.get('content', '')[:200] + '...' if len(doc.get('content', '')) > 200 else doc.get('content', ''),
                    'formatted_source': _format_source_display(document_name, doc.get('content', '')[:100], doc.get('page_number', 'N/A'), chunk_type)
                })
            else:
                # 尝试从其他字段获取信息
                # 处理 dict_keys(['doc_id', 'doc', 'score', 'match_type']) 这种结构
                if 'doc' in doc and isinstance(doc['doc'], dict):
                    # 从 doc 字段中提取文档信息
                    actual_doc = doc['doc']
                    if 'enhanced_description' in actual_doc:
                        # 图片文档
                        # 尝试获取真实的文档名称
                        document_name = actual_doc.get('document_name', 'N/A')
                        if document_name == 'N/A' or document_name == '未知文档':
                            document_name = actual_doc.get('source', '') or actual_doc.get('doc_id', '') or '未知文档'
                        
                        sources.append({
                            'title': actual_doc.get('img_caption', ['无标题'])[0] if actual_doc.get('img_caption') else '图片',
                            'page_number': actual_doc.get('page_number', 'N/A'),
                            'document_name': document_name,
                            'source_type': 'image',
                            'score': doc.get('score', 0.0),
                            'image_path': actual_doc.get('image_path', ''),
                            'enhanced_description': actual_doc.get('enhanced_description', '')[:100] + '...' if len(actual_doc.get('enhanced_description', '')) > 100 else actual_doc.get('enhanced_description', ''),
                            'formatted_source': _format_source_display(document_name, actual_doc.get('img_caption', ['无标题'])[0] if actual_doc.get('img_caption') else '无标题', actual_doc.get('page_number', 'N/A'), 'image')
                        })
                    elif 'page_content' in actual_doc:
                        # 文本或表格文档
                        chunk_type = actual_doc.get('chunk_type', 'text')
                        # 尝试获取真实的文档名称
                        document_name = actual_doc.get('document_name', 'N/A')
                        if document_name == 'N/A' or document_name == '未知文档':
                            document_name = actual_doc.get('source', '') or actual_doc.get('doc_id', '') or '未知文档'
                        
                        sources.append({
                            'title': actual_doc.get('img_caption', ['无标题'])[0] if actual_doc.get('img_caption') else '无标题',
                            'page_number': actual_doc.get('page_number', 'N/A'),
                            'document_name': document_name,
                            'source_type': 'image',
                            'score': doc.get('score', 0.0),
                            'image_path': actual_doc.get('image_path', ''),
                            'formatted_source': _format_source_display(document_name, actual_doc.get('img_caption', ['无标题'])[0] if actual_doc.get('img_caption') else '无标题', actual_doc.get('page_number', 'N/A'), 'image')
                        })
                    elif 'content' in actual_doc:
                        # 文本或表格文档（修复后的格式）
                        chunk_type = actual_doc.get('chunk_type', 'text')
                        # 尝试获取真实的文档名称
                        document_name = actual_doc.get('document_name', 'N/A')
                        if document_name == 'N/A' or document_name == '未知文档':
                            document_name = actual_doc.get('source', '') or actual_doc.get('doc_id', '') or '未知文档'
                        
                        sources.append({
                            'title': actual_doc.get('img_caption', ['无标题'])[0] if actual_doc.get('img_caption') else '无标题',
                            'page_number': actual_doc.get('page_number', 'N/A'),
                            'document_name': document_name,
                            'source_type': 'image',
                            'score': doc.get('score', 0.0),
                            'image_path': actual_doc.get('image_path', ''),
                            'formatted_source': _format_source_display(document_name, actual_doc.get('img_caption', ['无标题'])[0] if actual_doc.get('img_caption') else '无标题', actual_doc.get('page_number', 'N/A'), 'image')
                        })
                    else:
                        # 其他结构，尝试从实际文档中提取基本信息
                        chunk_type = actual_doc.get('chunk_type', 'text')
                        # 尝试获取真实的文档名称
                        document_name = actual_doc.get('document_name', 'N/A')
                        if document_name == 'N/A' or document_name == '未知文档':
                            document_name = actual_doc.get('source', '') or actual_doc.get('doc_id', '') or '未知文档'
                        
                        sources.append({
                            'title': actual_doc.get('title', '文档'),
                            'page_number': actual_doc.get('page_number', 'N/A'),
                            'document_name': document_name,
                            'source_type': chunk_type,
                            'score': doc.get('score', 0.0),
                            'content_preview': str(actual_doc)[:200] + '...' if len(str(actual_doc)) > 200 else str(actual_doc),
                            'formatted_source': _format_source_display(document_name, str(actual_doc)[:100], actual_doc.get('page_number', 'N/A'), chunk_type)
                        })
                else:
                    # 其他无法识别的结构
                    logger.warning(f"无法识别的文档结构: {doc.keys()}")
                    sources.append({
                        'title': '未知文档',
                        'page_number': 'N/A',
                        'document_name': 'N/A',
                        'source_type': 'unknown',
                        'score': doc.get('score', 0.0),
                        'formatted_source': '未知来源'
                    })
        elif hasattr(doc, 'metadata'):
            # Document对象，从metadata中提取信息
            metadata = doc.metadata
            chunk_type = metadata.get('chunk_type', 'text')
            document_name = metadata.get('document_name', 'N/A')
            page_number = metadata.get('page_number', 'N/A')
            
            # 尝试获取真实的文档名称
            if document_name == 'N/A':
                document_name = metadata.get('source', '') or metadata.get('doc_id', '') or '未知文档'
            
            # 获取内容预览
            if hasattr(doc, 'page_content'):
                content_preview = doc.page_content[:200] + '...' if len(doc.page_content) > 200 else doc.page_content
            else:
                content_preview = str(doc)[:200] + '...' if len(str(doc)) > 200 else str(doc)
            
            sources.append({
                'title': metadata.get('title', '文档'),
                'page_number': page_number,
                'document_name': document_name,
                'source_type': chunk_type,
                'score': getattr(doc, 'relevance_score', 0.0),
                'content_preview': content_preview,
                'formatted_source': _format_source_display(document_name, content_preview, page_number, chunk_type)
            })
        elif hasattr(doc, 'content'):
            # 有content属性的对象
            content = doc.content
            if isinstance(content, dict):
                if 'enhanced_description' in content:
                    # 图片文档
                    # 尝试获取真实的文档名称
                    document_name = content.get('document_name', 'N/A')
                    if document_name == 'N/A':
                        document_name = content.get('source', '') or content.get('doc_id', '') or '未知文档'
                    
                    sources.append({
                        'title': content.get('img_caption', ['无标题'])[0] if content.get('img_caption') else '无标题',
                        'page_number': content.get('page_number', 'N/A'),
                        'document_name': document_name,
                        'source_type': 'image',
                        'score': content.get('score', 0.0),
                        'image_path': content.get('image_path', ''),
                        'formatted_source': _format_source_display(document_name, content.get('img_caption', ['无标题'])[0] if content.get('img_caption') else '无标题', content.get('page_number', 'N/A'), 'image')
                    })
                elif 'page_content' in content:
                    # 文本或表格文档
                    chunk_type = content.get('chunk_type', 'text')
                    # 尝试获取真实的文档名称
                    document_name = content.get('document_name', 'N/A')
                    if document_name == 'N/A' or document_name == '未知文档':
                        document_name = content.get('source', '') or content.get('doc_id', '') or '未知文档'
                    
                    sources.append({
                        'title': content.get('title', '文档'),
                        'page_number': content.get('page_number', 'N/A'),
                        'page_number': content.get('page_number', 'N/A'),
                        'document_name': document_name,
                        'source_type': chunk_type,
                        'score': content.get('score', 0.0),
                        'content_preview': content.get('page_content', '')[:200] + '...' if len(content.get('page_content', '')) > 200 else content.get('page_content', ''),
                        'formatted_source': _format_source_display(document_name, content.get('page_content', '')[:100], content.get('page_number', 'N/A'), chunk_type)
                    })
                else:
                    # 其他内容类型
                    chunk_type = content.get('chunk_type', 'text')
                    # 尝试获取真实的文档名称
                    document_name = content.get('document_name', 'N/A')
                    if document_name == 'N/A':
                        document_name = content.get('source', '') or content.get('doc_id', '') or '未知文档'
                    
                    sources.append({
                        'title': content.get('title', '文档'),
                        'page_number': content.get('page_number', 'N/A'),
                        'document_name': document_name,
                        'source_type': chunk_type,
                        'score': content.get('score', 0.0),
                        'content_preview': str(content)[:200] + '...' if len(str(content)) > 200 else str(content),
                        'formatted_source': _format_source_display(document_name, str(content)[:100], content.get('page_number', 'N/A'), chunk_type)
                    })
            else:
                # 简单内容
                sources.append({
                    'title': '文档',
                    'page_number': 'N/A',
                    'document_name': '未知文档',
                    'source_type': 'text',
                    'score': content.get('score', 0.0),
                    'content_preview': str(content)[:200] + '...' if len(str(content)) > 200 else str(content),
                    'formatted_source': _format_source_display('未知文档', str(content)[:100], 'N/A', 'text')
                })
        else:
            # 其他类型的对象
            sources.append({
                'title': '文档',
                'page_number': 'N/A',
                'document_name': '未知文档',
                'source_type': 'unknown',
                'score': content.get('score', 0.0),
                'content_preview': str(content)[:200] + '...' if len(str(content)) > 200 else str(content),
                'formatted_source': _format_source_display('未知文档', str(content)[:100], 'N/A', 'unknown')
            })
    
    return sources


def _format_source_display(document_name, content_preview, page_number, chunk_type):
    """
    格式化来源显示信息
    
    :param document_name: 文档名称
    :param content_preview: 内容预览
    :param page_number: 页码
    :param chunk_type: 内容类型 (image, text, table)
    :return: 格式化的来源字符串
    """
    if document_name == 'N/A':
        document_name = '未知文档'
    
    if page_number == 'N/A':
        page_number = '未知页'
    
    # 清理文档名，移除可能的重复方括号和多余空格
    if document_name.startswith('【') and document_name.endswith('】'):
        document_name = document_name[1:-1]  # 移除外层方括号
    
    # 进一步清理文档名，移除内部可能的方括号
    document_name = document_name.replace('【', '').replace('】', '').strip()
    
    # 清理内容预览，移除多余的连字符和特殊字符
    if content_preview:
        # 移除开头和结尾的连字符、空格等
        content_preview = content_preview.strip(' -_')
        # 移除连续的连字符
        content_preview = content_preview.replace('--', '-').replace('---', '-')
        # 移除开头和结尾的连字符
        content_preview = content_preview.strip(' -')
    
    # 根据内容类型生成不同格式
    if chunk_type == 'image':
        # 图片：文档名 - 图片标题 - 第X页 (图片)
        # 提取图片标题（第一行通常是图片标题）
        lines = content_preview.split('\n') if content_preview else ['']
        image_title = lines[0].strip() if lines and lines[0].strip() else '图片'
        return f"{document_name} - {image_title} - 第{page_number}页 (图片)"
    
    elif chunk_type == 'table':
        # 表格：文档名 - 表格标题 - 第X页 (表格)
        # 提取表格标题（第一行通常是表格标题）
        lines = content_preview.split('\n') if content_preview else ['']
        table_title = lines[0].strip() if lines and lines[0].strip() else '表格'
        return f"{document_name} - {table_title} - 第{page_number}页 (表格)"
    
    elif chunk_type == 'text':
        # 文本：文档名 - 第X页 (文本)
        return f"{document_name} - 第{page_number}页 (文本)"
    
    # 移除LLM答案的处理，因为AI生成答案不应该是信息来源
    else:
        # 其他类型：文档名 - 第X页
        return f"{document_name} - 第{page_number}页"


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
    
    # 图片服务
    @app.route('/images/<path:filename>')
    def serve_image(filename):
        """图片服务"""
        try:
            # 使用绝对路径从central/images目录提供图片
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            images_dir = os.path.join(project_root, 'central', 'images')
            
            # 添加调试信息
            logger.debug(f"图片服务请求: {filename}")
            logger.debug(f"当前目录: {current_dir}")
            logger.debug(f"项目根目录: {project_root}")
            logger.debug(f"图片目录: {images_dir}")
            logger.debug(f"图片目录是否存在: {os.path.exists(images_dir)}")
            
            if os.path.exists(images_dir):
                image_path = os.path.join(images_dir, filename)
                logger.debug(f"完整图片路径: {image_path}")
                logger.debug(f"图片文件是否存在: {os.path.exists(image_path)}")
            
            return send_from_directory(images_dir, filename)
        except FileNotFoundError:
            logger.error(f"图片未找到: {filename}")
            return jsonify({'error': f'图片未找到: {filename}'}), 404
        except Exception as e:
            logger.error(f"图片服务错误: {str(e)}")
            return jsonify({'error': f'图片服务错误: {str(e)}'}), 500
    
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
