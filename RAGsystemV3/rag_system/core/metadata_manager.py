"""
RAG元数据管理模块

RAG系统的数据基础模块，负责查询过程元数据的生成、存储、查询和更新
与V3系统的内容元数据管理形成互补，为整个RAG系统提供标准化的查询过程元数据管理服务
"""

import logging
import time
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class QuerySession:
    """查询会话元数据"""
    session_id: str                    # 会话唯一标识
    user_id: str                       # 用户标识
    query_type: str                    # 查询类型：text/image/table/hybrid
    query_text: str                    # 用户查询文本
    timestamp: datetime                # 查询时间
    session_context: Dict[str, Any]    # 会话上下文（历史查询等）
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（确保类型一致性）"""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'query_type': self.query_type,
            'query_text': self.query_text,
            'timestamp': self.timestamp.isoformat(),
            'session_context': self.session_context
        }


@dataclass
class RetrievalResult:
    """检索结果元数据"""
    query_id: str                      # 查询ID
    retrieval_strategy: str            # 检索策略：vector_similarity/hybrid/smart
    content_id: str                    # 内容ID（对应V3的chunk_id）
    source_document: str               # 源文档名称
    content_type: str                  # 内容类型：text/image/table
    similarity_score: float            # 相似度分数
    retrieval_rank: int                # 检索排名
    content_preview: str               # 内容预览
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（确保类型一致性）"""
        return {
            'query_id': self.query_id,
            'retrieval_strategy': self.retrieval_strategy,
            'content_id': self.content_id,
            'source_document': self.source_document,
            'content_type': self.content_type,
            'similarity_score': self.similarity_score,
            'retrieval_rank': self.retrieval_rank,
            'content_preview': self.content_preview
        }


@dataclass
class LLMCall:
    """LLM调用元数据"""
    llm_call_id: str                   # LLM调用ID
    model_name: str                    # 模型名称：qwen-turbo等
    input_tokens: int                  # 输入token数
    output_tokens: int                 # 输出token数
    processing_time: float             # 处理时间（秒）
    temperature: float                 # 温度参数
    max_tokens: int                    # 最大token数
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（确保类型一致性）"""
        return {
            'llm_call_id': self.llm_call_id,
            'model_name': self.model_name,
            'input_tokens': self.input_tokens,
            'output_tokens': self.output_tokens,
            'processing_time': self.processing_time,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens
        }


@dataclass
class AnswerGeneration:
    """答案生成元数据"""
    answer_id: str                     # 答案ID
    generated_answer: str              # 生成的答案文本
    sources_used: List[str]            # 使用的来源（V3的chunk_id列表）
    answer_type: str                   # 答案类型：summary/analysis/comparison
    confidence_level: str              # 置信度：low/medium/high
    estimated_accuracy: float          # 预估准确率
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（确保类型一致性）"""
        return {
            'answer_id': self.answer_id,
            'generated_answer': self.generated_answer,
            'sources_used': self.sources_used,  # 保持list类型，这是RAG特有的
            'answer_type': self.answer_type,
            'confidence_level': self.confidence_level,
            'estimated_accuracy': self.estimated_accuracy
        }


class RAGMetadataManager:
    """RAG元数据管理器（独立于V3系统）"""
    
    def __init__(self, v3_metadata_manager):
        """
        初始化RAG元数据管理器
        
        :param v3_metadata_manager: V3元数据管理器实例
        """
        self.v3_metadata_manager = v3_metadata_manager
        
        # 独立的RAG元数据库，不影响V3系统
        self.rag_db = self._initialize_rag_database()
        
        # 元数据统计
        self.metadata_statistics = {
            'total_queries': 0,
            'total_llm_calls': 0,
            'total_answers': 0,
            'average_response_time': 0.0,
            'last_update': None
        }
        
        logger.info("元数据管理器初始化完成")
    
    def _initialize_rag_database(self):
        """初始化RAG元数据库"""
        try:
            db_path = Path("rag_metadata.db")
            
            # 创建数据库和表结构
            conn = sqlite3.connect(db_path)
            self._create_tables(conn)
            
            logger.info(f"RAG元数据库初始化完成: {db_path}")
            return conn
            
        except Exception as e:
            logger.error(f"RAG元数据库初始化失败: {e}")
            raise
    
    def _create_tables(self, conn):
        """创建数据库表结构"""
        try:
            cursor = conn.cursor()
            
            # RAG查询会话表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rag_query_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    query_type TEXT NOT NULL,
                    query_text TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    session_context TEXT
                )
            ''')
            
            # RAG检索结果表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rag_retrieval_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_id TEXT NOT NULL,
                    retrieval_strategy TEXT NOT NULL,
                    content_id TEXT NOT NULL,
                    source_document TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    similarity_score REAL NOT NULL,
                    retrieval_rank INTEGER NOT NULL,
                    content_preview TEXT
                )
            ''')
            
            # RAG LLM调用表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rag_llm_calls (
                    llm_call_id TEXT PRIMARY KEY,
                    model_name TEXT NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    processing_time REAL NOT NULL,
                    temperature REAL NOT NULL,
                    max_tokens INTEGER NOT NULL
                )
            ''')
            
            # RAG答案生成表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rag_answer_generations (
                    answer_id TEXT PRIMARY KEY,
                    generated_answer TEXT NOT NULL,
                    sources_used TEXT NOT NULL,
                    answer_type TEXT NOT NULL,
                    confidence_level TEXT NOT NULL,
                    estimated_accuracy REAL NOT NULL
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_query_sessions_user_id ON rag_query_sessions(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_query_sessions_timestamp ON rag_query_sessions(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_retrieval_results_query_id ON rag_retrieval_results(query_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_retrieval_results_content_id ON rag_retrieval_results(content_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_llm_calls_timestamp ON rag_llm_calls(llm_call_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_answer_generations_timestamp ON rag_answer_generations(answer_id)')
            
            conn.commit()
            logger.info("RAG元数据库表结构创建完成")
            
        except Exception as e:
            logger.error(f"创建数据库表结构失败: {e}")
            raise
    
    def store_query_session(self, session: QuerySession) -> bool:
        """
        存储查询会话元数据
        
        :param session: 查询会话对象
        :return: 存储是否成功
        """
        try:
            cursor = self.rag_db.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO rag_query_sessions 
                (session_id, user_id, query_type, query_text, timestamp, session_context)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session.session_id,
                session.user_id,
                session.query_type,
                session.query_text,
                session.timestamp.isoformat(),
                json.dumps(session.session_context)
            ))
            
            self.rag_db.commit()
            
            # 更新统计信息
            self.metadata_statistics['total_queries'] += 1
            self.metadata_statistics['last_update'] = datetime.now()
            
            logger.info(f"查询会话元数据存储成功: {session.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"存储查询会话元数据失败: {e}")
            return False
    
    def store_retrieval_result(self, result: RetrievalResult) -> bool:
        """
        存储检索结果元数据
        
        :param result: 检索结果对象
        :return: 存储是否成功
        """
        try:
            cursor = self.rag_db.cursor()
            
            cursor.execute('''
                INSERT INTO rag_retrieval_results 
                (query_id, retrieval_strategy, content_id, source_document, content_type, 
                 similarity_score, retrieval_rank, content_preview)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.query_id,
                result.retrieval_strategy,
                result.content_id,
                result.source_document,
                result.content_type,
                result.similarity_score,
                result.retrieval_rank,
                result.content_preview
            ))
            
            self.rag_db.commit()
            logger.info(f"检索结果元数据存储成功: {result.content_id}")
            return True
            
        except Exception as e:
            logger.error(f"存储检索结果元数据失败: {e}")
            return False
    
    def store_llm_call(self, llm_call: LLMCall) -> bool:
        """
        存储LLM调用元数据
        
        :param llm_call: LLM调用对象
        :return: 存储是否成功
        """
        try:
            cursor = self.rag_db.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO rag_llm_calls 
                (llm_call_id, model_name, input_tokens, output_tokens, processing_time, 
                 temperature, max_tokens)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                llm_call.llm_call_id,
                llm_call.model_name,
                llm_call.input_tokens,
                llm_call.output_tokens,
                llm_call.processing_time,
                llm_call.temperature,
                llm_call.max_tokens
            ))
            
            self.rag_db.commit()
            
            # 更新统计信息
            self.metadata_statistics['total_llm_calls'] += 1
            self.metadata_statistics['last_update'] = datetime.now()
            
            logger.info(f"LLM调用元数据存储成功: {llm_call.llm_call_id}")
            return True
            
        except Exception as e:
            logger.error(f"存储LLM调用元数据失败: {e}")
            return False
    
    def store_answer_generation(self, answer: AnswerGeneration) -> bool:
        """
        存储答案生成元数据
        
        :param answer: 答案生成对象
        :return: 存储是否成功
        """
        try:
            cursor = self.rag_db.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO rag_answer_generations 
                (answer_id, generated_answer, sources_used, answer_type, confidence_level, estimated_accuracy)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                answer.answer_id,
                answer.generated_answer,
                json.dumps(answer.sources_used),
                answer.answer_type,
                answer.confidence_level,
                answer.estimated_accuracy
            ))
            
            self.rag_db.commit()
            
            # 更新统计信息
            self.metadata_statistics['total_answers'] += 1
            self.metadata_statistics['last_update'] = datetime.now()
            
            logger.info(f"答案生成元数据存储成功: {answer.answer_id}")
            return True
            
        except Exception as e:
            logger.error(f"存储答案生成元数据失败: {e}")
            return False
    
    def get_query_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取用户查询历史
        
        :param user_id: 用户ID
        :param limit: 限制数量
        :return: 查询历史列表
        """
        try:
            cursor = self.rag_db.cursor()
            
            cursor.execute('''
                SELECT session_id, query_type, query_text, timestamp
                FROM rag_query_sessions 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (user_id, limit))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'session_id': row[0],
                    'query_type': row[1],
                    'query_text': row[2],
                    'timestamp': row[3]
                })
            
            logger.info(f"获取用户查询历史成功: {user_id}, 数量: {len(results)}")
            return results
            
        except Exception as e:
            logger.error(f"获取用户查询历史失败: {e}")
            return []
    
    def get_performance_metrics(self, time_range: str = '24h') -> Dict[str, Any]:
        """
        获取性能指标
        
        :param time_range: 时间范围
        :return: 性能统计字典
        """
        try:
            end_time = datetime.now()
            
            if time_range == '1h':
                start_time = end_time - timedelta(hours=1)
            elif time_range == '24h':
                start_time = end_time - timedelta(days=1)
            elif time_range == '7d':
                start_time = end_time - timedelta(days=7)
            elif time_range == '30d':
                start_time = end_time - timedelta(days=30)
            else:
                start_time = end_time - timedelta(hours=24)
            
            # 查询数据库获取性能数据
            metrics = self._query_performance_data(start_time, end_time)
            
            return {
                'time_range': time_range,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'total_queries': metrics.get('total_queries', 0),
                'average_response_time': metrics.get('avg_response_time', 0.0),
                'llm_call_success_rate': metrics.get('llm_success_rate', 0.0),
                'top_query_types': metrics.get('top_query_types', []),
                'performance_trends': metrics.get('trends', {})
            }
            
        except Exception as e:
            logger.error(f"获取性能指标失败: {e}")
            return {}
    
    def _query_performance_data(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """查询性能数据"""
        try:
            cursor = self.rag_db.cursor()
            
            # 查询时间范围内的数据
            start_str = start_time.isoformat()
            end_str = end_time.isoformat()
            
            # 查询总数
            cursor.execute('''
                SELECT COUNT(*) FROM rag_query_sessions 
                WHERE timestamp BETWEEN ? AND ?
            ''', (start_str, end_str))
            total_queries = cursor.fetchone()[0]
            
            # 查询类型分布
            cursor.execute('''
                SELECT query_type, COUNT(*) as count
                FROM rag_query_sessions 
                WHERE timestamp BETWEEN ? AND ?
                GROUP BY query_type
                ORDER BY count DESC
            ''', (start_str, end_str))
            query_types = [{'type': row[0], 'count': row[1]} for row in cursor.fetchall()]
            
            # 计算平均响应时间
            avg_response_time = 0.0
            if total_queries > 0:
                try:
                    cursor = self.conn.cursor()
                    cursor.execute("""
                        SELECT AVG(response_time) 
                        FROM query_logs 
                        WHERE response_time IS NOT NULL
                    """)
                    result = cursor.fetchone()
                    if result and result[0] is not None:
                        avg_response_time = round(result[0], 3)
                except Exception as e:
                    logger.warning(f"计算平均响应时间失败: {e}")
            
            # 计算LLM成功率
            llm_success_rate = 1.0
            if total_queries > 0:
                try:
                    cursor = self.conn.cursor()
                    cursor.execute("""
                        SELECT COUNT(*) as success_count
                        FROM query_logs 
                        WHERE success = 1
                    """)
                    result = cursor.fetchone()
                    if result and result[0] is not None:
                        success_count = result[0]
                        llm_success_rate = round(success_count / total_queries, 3)
                except Exception as e:
                    logger.warning(f"计算LLM成功率失败: {e}")
            
            return {
                'total_queries': total_queries,
                'top_query_types': query_types,
                'avg_response_time': avg_response_time,
                'llm_success_rate': llm_success_rate,
                'trends': {}
            }
            
        except Exception as e:
            logger.error(f"查询性能数据失败: {e}")
            return {}
    
    def export_metadata(self, export_format: str = 'json') -> str:
        """
        导出RAG元数据
        
        :param export_format: 导出格式
        :return: 导出文件路径
        """
        try:
            if export_format.lower() == 'json':
                return self._export_to_json()
            else:
                logger.warning(f"不支持的导出格式: {export_format}")
                return ""
                
        except Exception as e:
            logger.error(f"导出元数据失败: {e}")
            return ""
    
    def _export_to_json(self) -> str:
        """导出为JSON格式"""
        try:
            cursor = self.rag_db.cursor()
            
            # 查询所有数据
            export_data = {
                'export_time': datetime.now().isoformat(),
                'query_sessions': [],
                'retrieval_results': [],
                'llm_calls': [],
                'answer_generations': []
            }
            
            # 查询会话数据
            cursor.execute('SELECT * FROM rag_query_sessions')
            for row in cursor.fetchall():
                export_data['query_sessions'].append({
                    'session_id': row[0],
                    'user_id': row[1],
                    'query_type': row[2],
                    'query_text': row[3],
                    'timestamp': row[4],
                    'session_context': json.loads(row[5]) if row[5] else {}
                })
            
            # 检索结果数据
            cursor.execute('SELECT * FROM rag_retrieval_results')
            for row in cursor.fetchall():
                export_data['retrieval_results'].append({
                    'id': row[0],
                    'query_id': row[1],
                    'retrieval_strategy': row[2],
                    'content_id': row[3],
                    'source_document': row[4],
                    'content_type': row[5],
                    'similarity_score': row[6],
                    'retrieval_rank': row[7],
                    'content_preview': row[8]
                })
            
            # LLM调用数据
            cursor.execute('SELECT * FROM rag_llm_calls')
            for row in cursor.fetchall():
                export_data['llm_calls'].append({
                    'llm_call_id': row[0],
                    'model_name': row[1],
                    'input_tokens': row[2],
                    'output_tokens': row[3],
                    'processing_time': row[4],
                    'temperature': row[5],
                    'max_tokens': row[6]
                })
            
            # 答案生成数据
            cursor.execute('SELECT * FROM rag_answer_generations')
            for row in cursor.fetchall():
                export_data['answer_generations'].append({
                    'answer_id': row[0],
                    'generated_answer': row[1],
                    'sources_used': json.loads(row[2]) if row[2] else [],
                    'answer_type': row[3],
                    'confidence_level': row[4],
                    'estimated_accuracy': row[5]
                })
            
            # 写入文件
            export_path = f"rag_metadata_export_{int(time.time())}.json"
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"RAG元数据导出成功: {export_path}")
            return export_path
            
        except Exception as e:
            logger.error(f"导出JSON失败: {e}")
            return ""
    
    def cleanup_old_metadata(self, retention_days: int = 90) -> int:
        """
        清理过期的RAG元数据
        
        :param retention_days: 保留天数
        :return: 清理的记录数
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            cutoff_str = cutoff_date.isoformat()
            
            cursor = self.rag_db.cursor()
            
            # 清理查询会话
            cursor.execute('DELETE FROM rag_query_sessions WHERE timestamp < ?', (cutoff_str,))
            sessions_deleted = cursor.rowcount
            
            # 清理检索结果（通过关联查询）
            cursor.execute('''
                DELETE FROM rag_retrieval_results 
                WHERE query_id NOT IN (
                    SELECT session_id FROM rag_query_sessions
                )
            ''')
            results_deleted = cursor.rowcount
            
            # 清理LLM调用
            cursor.execute('DELETE FROM rag_llm_calls WHERE llm_call_id < ?', (cutoff_str,))
            llm_deleted = cursor.rowcount
            
            # 清理答案生成
            cursor.execute('DELETE FROM rag_answer_generations WHERE answer_id < ?', (cutoff_str,))
            answers_deleted = cursor.rowcount
            
            self.rag_db.commit()
            
            total_deleted = sessions_deleted + results_deleted + llm_deleted + answers_deleted
            logger.info(f"清理过期元数据完成，共删除 {total_deleted} 条记录")
            
            return total_deleted
            
        except Exception as e:
            logger.error(f"清理过期元数据失败: {e}")
            return 0
    
    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态信息"""
        try:
            cursor = self.rag_db.cursor()
            
            # 获取各表的记录数
            cursor.execute('SELECT COUNT(*) FROM rag_query_sessions')
            query_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM rag_retrieval_results')
            retrieval_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM rag_llm_calls')
            llm_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM rag_answer_generations')
            answer_count = cursor.fetchone()[0]
            
            return {
                'status': 'ready',
                'database': 'rag_metadata.db',
                'statistics': {
                    'total_queries': query_count,
                    'total_retrieval_results': retrieval_count,
                    'total_llm_calls': llm_count,
                    'total_answers': answer_count
                },
                'last_update': self.metadata_statistics['last_update'].isoformat() if self.metadata_statistics['last_update'] else None
            }
            
        except Exception as e:
            logger.error(f"获取服务状态失败: {e}")
            return {'status': 'error', 'error': str(e)}


class MetadataReader:
    """元数据读取器（与V3系统集成）"""
    
    def __init__(self, v3_metadata_manager):
        """
        初始化RAG元数据读取器
        
        :param v3_metadata_manager: V3元数据管理器实例
        """
        self.v3_metadata_manager = v3_metadata_manager
        logger.info("RAG元数据读取器初始化完成")
    
    def read_metadata(self, chunk_id: str) -> Dict[str, Any]:
        """
        读取V3系统的元数据
        
        :param chunk_id: 块ID
        :return: 标准化元数据字典
        """
        try:
            # 使用V3的现有接口
            metadata = self.v3_metadata_manager.get_metadata_by_id(chunk_id)
            
            if not metadata:
                return {}
            
            # 确保返回的是dict类型
            if not isinstance(metadata, dict):
                logger.warning(f"V3元数据不是dict类型: {type(metadata)}")
                return {}
            
            # 标准化字段访问（避免V2的混乱）
            return {
                'chunk_id': metadata.get('chunk_id', ''),
                'chunk_type': metadata.get('chunk_type', ''),
                'document_name': metadata.get('document_name', ''),
                'page_number': metadata.get('page_number', 0),
                'content': self._extract_content(metadata),
                'source_type': metadata.get('source_type', ''),
                'created_timestamp': metadata.get('created_timestamp', 0)
            }
            
        except Exception as e:
            logger.error(f"读取V3元数据失败: {e}")
            return {}
    
    def _extract_content(self, metadata: Dict[str, Any]) -> str:
        """根据内容类型提取内容"""
        chunk_type = metadata.get('chunk_type', '')
        
        if chunk_type == 'text':
            return metadata.get('text', '')
        elif chunk_type == 'image':
            return metadata.get('enhanced_description', '')
        elif chunk_type == 'table':
            return metadata.get('table_content', '')
        else:
            return ''
    
    def get_document_info(self, chunk_id: str) -> Dict[str, Any]:
        """
        获取文档信息用于溯源
        
        :param chunk_id: 块ID
        :return: 文档信息字典
        """
        try:
            metadata = self.read_metadata(chunk_id)
            
            if not metadata:
                return {}
            
            return {
                'document_name': metadata.get('document_name', 'Unknown'),
                'page_number': metadata.get('page_number', 0),
                'content_type': metadata.get('chunk_type', 'unknown'),
                'content_preview': metadata.get('content', '')[:200] + "..." if len(metadata.get('content', '')) > 200 else metadata.get('content', ''),
                'source_type': metadata.get('source_type', 'unknown')
            }
            
        except Exception as e:
            logger.error(f"获取文档信息失败: {e}")
            return {}
