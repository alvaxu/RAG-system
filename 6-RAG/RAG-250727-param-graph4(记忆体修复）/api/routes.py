'''
程序说明：
## 1. API路由定义
## 2. 提供问答、记忆管理等接口
## 3. 支持RESTful API设计
## 4. 提供完整的API文档
'''

import logging
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime

# 配置日志
logger = logging.getLogger(__name__)

# 创建蓝图
api_bp = Blueprint('api', __name__)


@api_bp.route('/qa/ask', methods=['POST'])
def ask_question():
    """
    问答接口
    POST /api/qa/ask
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
        
        question = data.get('question', '').strip()
        user_id = data.get('user_id', 'default_user')
        use_memory = data.get('use_memory', True)
        k = data.get('k', 5)
        
        if not question:
            return jsonify({'error': '问题不能为空'}), 400
        
        # 获取问答系统
        qa_system = current_app.config.get('QA_SYSTEM')
        if not qa_system:
            return jsonify({'error': '问答系统未初始化'}), 500
        
        # 执行问答
        if use_memory:
            # 问答开始前重置记忆清除标志，确保新记忆能被保存
            qa_system.set_memory_cleared_flag(False)
            result = qa_system.answer_with_memory(user_id, question, k)
        else:
            result = qa_system.answer_question(question, k)
        
        # 格式化响应
        response = {
            'success': True,
            'question': question,
            'answer': result.get('answer', ''),
            'sources': result.get('sources', []),
            'cost': result.get('cost', 0.0),
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'use_memory': use_memory
        }
        
        if 'error' in result:
            response['error'] = result['error']
            response['success'] = False
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"问答接口错误: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


@api_bp.route('/qa/preset-questions', methods=['GET'])
def get_preset_questions():
    """
    获取预设问题接口
    GET /api/qa/preset-questions
    """
    try:
        # 获取设置
        settings = current_app.config.get('SETTINGS')
        if not settings:
            return jsonify({'error': '配置未初始化'}), 500
        
        # 获取预设问题文件路径
        preset_file = settings.preset_questions_file
        
        # 读取预设问题
        import json
        import os
        
        if os.path.exists(preset_file):
            with open(preset_file, 'r', encoding='utf-8') as f:
                questions = json.load(f)
        else:
            # 如果文件不存在，返回默认问题
            questions = [
                "文档的主要内容是什么？",
                "有哪些重要的数据表格？",
                "文档中的图片展示了什么？",
                "总结一下文档的关键信息",
                "文档的结论是什么？"
            ]
        
        return jsonify({
            'success': True,
            'questions': questions
        })
        
    except Exception as e:
        logger.error(f"获取预设问题失败: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


@api_bp.route('/qa/search', methods=['POST'])
def search_documents():
    """
    文档搜索接口
    POST /api/qa/search
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
        
        query = data.get('query', '').strip()
        k = data.get('k', 5)
        
        if not query:
            return jsonify({'error': '搜索查询不能为空'}), 400
        
        # 获取问答系统
        qa_system = current_app.config.get('QA_SYSTEM')
        if not qa_system:
            return jsonify({'error': '问答系统未初始化'}), 500
        
        # 执行搜索
        results = qa_system.vector_store.similarity_search(query, k=k)
        
        # 格式化结果
        formatted_results = []
        for doc in results:
            formatted_results.append({
                'content': doc.page_content,
                'metadata': doc.metadata,
                'document_name': doc.metadata.get('document_name', '未知文档'),
                'page_number': doc.metadata.get('page_number', 0),
                'chunk_type': doc.metadata.get('chunk_type', 'text')
            })
        
        return jsonify({
            'success': True,
            'query': query,
            'results': formatted_results,
            'count': len(formatted_results)
        })
        
    except Exception as e:
        logger.error(f"搜索接口错误: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


@api_bp.route('/memory/stats', methods=['GET'])
def get_memory_stats():
    """
    获取记忆统计信息
    GET /api/memory/stats?user_id=xxx
    """
    try:
        user_id = request.args.get('user_id')
        
        # 获取记忆管理器
        memory_manager = current_app.config.get('MEMORY_MANAGER')
        if not memory_manager:
            return jsonify({'error': '记忆管理器未初始化'}), 500
        
        # 获取统计信息
        stats = memory_manager.get_memory_stats(user_id)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"记忆统计接口错误: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


@api_bp.route('/memory/clear', methods=['POST'])
def clear_memory():
    """
    清除记忆
    POST /api/memory/clear
    """
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id')
        memory_type = data.get('memory_type', 'all')  # all, session, user
        
        # 获取记忆管理器和问答系统
        memory_manager = current_app.config.get('MEMORY_MANAGER')
        qa_system = current_app.config.get('QA_SYSTEM')
        
        if not memory_manager:
            return jsonify({'error': '记忆管理器未初始化'}), 500
        
        if not qa_system:
            return jsonify({'error': '问答系统未初始化'}), 500
        
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
        
        # 设置记忆清除标志，告诉LLM不要引用历史对话
        qa_system.set_memory_cleared_flag(True)
        
        # 立即重置LLM上下文，确保下次对话不会有历史记忆
        qa_system._reset_conversation_context()
        
        return jsonify({
            'success': True,
            'message': f'已清除{memory_type}记忆',
            'user_id': user_id,
            'memory_type': memory_type
        })
        
    except Exception as e:
        logger.error(f"清除记忆接口错误: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


@api_bp.route('/system/status', methods=['GET'])
def get_system_status():
    """
    获取系统状态
    GET /api/system/status
    """
    try:
        # 获取系统组件状态
        qa_system = current_app.config.get('QA_SYSTEM')
        memory_manager = current_app.config.get('MEMORY_MANAGER')
        settings = current_app.config.get('SETTINGS')
        
        status = {
            'qa_system': qa_system is not None,
            'memory_manager': memory_manager is not None,
            'vector_store_loaded': qa_system and qa_system.vector_store is not None,
            'api_key_configured': bool(settings.dashscope_api_key and settings.dashscope_api_key != '你的APIKEY'),
            'timestamp': datetime.now().isoformat()
        }
        
        # 获取向量存储统计信息
        if qa_system and qa_system.vector_store:
            try:
                stats = qa_system.get_memory_stats()
                status['vector_store_stats'] = stats
            except Exception as e:
                status['vector_store_stats'] = {'error': str(e)}
        
        # 获取记忆统计信息
        if memory_manager:
            try:
                memory_stats = memory_manager.get_memory_stats()
                status['memory_stats'] = memory_stats
            except Exception as e:
                status['memory_stats'] = {'error': str(e)}
        
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        logger.error(f"系统状态接口错误: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


@api_bp.route('/system/config', methods=['GET'])
def get_system_config():
    """
    获取系统配置
    GET /api/system/config
    """
    try:
        settings = current_app.config.get('SETTINGS')
        
        # 返回安全的配置信息（不包含敏感信息）
        config = {
            'paths': {
                'pdf_dir': settings.pdf_dir,
                'md_dir': settings.md_dir,
                'vector_db_dir': settings.vector_db_dir,
                'memory_db_dir': settings.memory_db_dir
            },
            'processing': {
                'chunk_size': settings.chunk_size,
                'chunk_overlap': settings.chunk_overlap,
                'max_table_rows': settings.max_table_rows
            },
            'qa_system': {
                'model_name': settings.model_name,
                'temperature': settings.temperature,
                'max_tokens': settings.max_tokens
            },
            'memory': {
                'memory_enabled': settings.memory_enabled,
                'memory_max_size': settings.memory_max_size
            }
        }
        
        return jsonify({
            'success': True,
            'config': config
        })
        
    except Exception as e:
        logger.error(f"系统配置接口错误: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500 