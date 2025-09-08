"""
对话记忆管理器

基于RAG系统V3的向量数据库机制，实现多轮对话记忆管理功能
"""

import logging
import sqlite3
import json
import time
import os
import math
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

# 用于三层检索策略的导入
try:
    import jieba
    import jieba.posseg as pseg
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False
    logger.warning("jieba或sklearn未安装，将使用简化的关键词提取")

from .models import ConversationSession, MemoryChunk, MemoryQuery, CompressionRequest
from .exceptions import (
    MemoryError, SessionNotFoundError, MemoryRetrievalError, 
    MemoryStorageError, DatabaseError, ValidationError
)
# PathManager通过依赖注入传入，避免跨包导入
from .memory_config_manager import MemoryConfigManager
from .memory_compression_engine import MemoryCompressionEngine

logger = logging.getLogger(__name__)


class ConversationMemoryManager:
    """
    对话记忆管理器
    
    基于现有向量数据库机制，实现多轮对话记忆管理
    """
    
    def __init__(self, config_manager: MemoryConfigManager, 
                 vector_db_integration=None, llm_caller=None, path_manager=None):
        """
        初始化对话记忆管理器
        
        Args:
            config_manager: 记忆配置管理器实例
            vector_db_integration: 向量数据库集成实例（可选）
            llm_caller: LLM调用器实例（可选）
            path_manager: 路径管理器实例（可选）
        """
        self.config_manager = config_manager
        self.vector_db_integration = vector_db_integration
        self.llm_caller = llm_caller
        self.path_manager = path_manager
        
        # 获取配置
        self.database_path = config_manager.get_database_path()
        self.retrieval_config = config_manager.get_retrieval_config()
        self.session_config = config_manager.get_session_config()
        
        # 初始化压缩引擎
        self.compression_engine = MemoryCompressionEngine(config_manager, llm_caller)
        
        # 初始化数据库
        self._initialize_database()
        
        # 记忆统计
        self.memory_stats = {
            'total_sessions': 0,
            'total_memories': 0,
            'total_queries': 0,
            'avg_memories_per_session': 0.0,
            'last_activity': None
        }
        
        logger.info("对话记忆管理器初始化完成")
    
    def _initialize_database(self) -> None:
        """
        初始化记忆数据库
        
        Raises:
            DatabaseError: 数据库初始化失败
        """
        try:
            # 处理数据库路径
            if self.path_manager:
                # 使用路径管理器将相对路径转换为绝对路径（基于项目根目录）
                self.database_path = self.path_manager.get_absolute_path(self.database_path)
            else:
                # 如果没有路径管理器，使用当前工作目录作为基准
                if not os.path.isabs(self.database_path):
                    self.database_path = os.path.abspath(self.database_path)
            
            # 确保数据库目录存在
            db_path = Path(self.database_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 连接数据库
            self.conn = sqlite3.connect(self.database_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            
            # 创建表
            self._create_tables()
            
            logger.info(f"记忆数据库初始化完成: {self.database_path}")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise DatabaseError(f"数据库初始化失败: {e}") from e
    
    def _create_tables(self) -> None:
        """
        创建数据库表
        """
        cursor = self.conn.cursor()
        
        # 创建会话表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                metadata TEXT,
                memory_count INTEGER DEFAULT 0,
                last_query TEXT
            )
        """)
        
        # 创建记忆表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_chunks (
                chunk_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                content TEXT NOT NULL,
                content_type TEXT NOT NULL DEFAULT 'text',
                relevance_score REAL DEFAULT 0.0,
                importance_score REAL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                metadata TEXT,
                vector_embedding TEXT,
                FOREIGN KEY (session_id) REFERENCES conversation_sessions (session_id)
            )
        """)
        
        # 创建压缩记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compression_records (
                record_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                original_count INTEGER NOT NULL,
                compressed_count INTEGER NOT NULL,
                compression_ratio REAL NOT NULL,
                strategy TEXT NOT NULL,
                created_at TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY (session_id) REFERENCES conversation_sessions (session_id)
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON conversation_sessions (user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_status ON conversation_sessions (status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_session_id ON memory_chunks (session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_content_type ON memory_chunks (content_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_created_at ON memory_chunks (created_at)")
        
        self.conn.commit()
    
    def create_session(self, user_id: str, metadata: Dict[str, Any] = None) -> ConversationSession:
        """
        创建新的对话会话
        
        Args:
            user_id: 用户标识
            metadata: 会话元数据
            
        Returns:
            ConversationSession: 创建的会话对象
            
        Raises:
            MemoryError: 会话创建失败
        """
        try:
            # 检查用户会话数量限制
            if not self._check_session_limit(user_id):
                raise MemoryError(f"用户 {user_id} 的会话数量已达到上限")
            
            # 创建会话对象
            session = ConversationSession(
                user_id=user_id,
                metadata=metadata or {},
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # 保存到数据库
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO conversation_sessions 
                (session_id, user_id, created_at, updated_at, status, metadata, memory_count, last_query)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session.session_id,
                session.user_id,
                session.created_at.isoformat(),
                session.updated_at.isoformat(),
                session.status,
                json.dumps(session.metadata),
                session.memory_count,
                session.last_query
            ))
            
            self.conn.commit()
            
            # 更新统计
            self.memory_stats['total_sessions'] += 1
            self.memory_stats['last_activity'] = datetime.now()
            
            logger.info(f"会话创建成功: {session.session_id} (用户: {user_id})")
            return session
            
        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            raise MemoryError(f"创建会话失败: {e}") from e
    
    def get_session(self, session_id: str) -> ConversationSession:
        """
        获取会话信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            ConversationSession: 会话对象
            
        Raises:
            SessionNotFoundError: 会话不存在
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM conversation_sessions WHERE session_id = ?
            """, (session_id,))
            
            row = cursor.fetchone()
            if not row:
                raise SessionNotFoundError(session_id)
            
            # 构建会话对象
            session = ConversationSession(
                session_id=row['session_id'],
                user_id=row['user_id'],
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at']),
                status=row['status'],
                metadata=json.loads(row['metadata']) if row['metadata'] and row['metadata'].strip() else {},
                memory_count=row['memory_count'],
                last_query=row['last_query'] or ''
            )
            
            return session
            
        except SessionNotFoundError:
            raise
        except Exception as e:
            logger.error(f"获取会话失败: {e}")
            raise MemoryError(f"获取会话失败: {e}") from e
    
    def list_sessions(self, user_id: str = None, status: str = "active", 
                     limit: int = 100) -> List[ConversationSession]:
        """
        列出会话
        
        Args:
            user_id: 用户ID（可选）
            status: 会话状态
            limit: 返回数量限制
            
        Returns:
            List[ConversationSession]: 会话列表
        """
        try:
            cursor = self.conn.cursor()
            
            if user_id:
                cursor.execute("""
                    SELECT * FROM conversation_sessions 
                    WHERE user_id = ? AND status = ?
                    ORDER BY updated_at DESC
                    LIMIT ?
                """, (user_id, status, limit))
            else:
                cursor.execute("""
                    SELECT * FROM conversation_sessions 
                    WHERE status = ?
                    ORDER BY updated_at DESC
                    LIMIT ?
                """, (status, limit))
            
            rows = cursor.fetchall()
            sessions = []
            
            for row in rows:
                session = ConversationSession(
                    session_id=row['session_id'],
                    user_id=row['user_id'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at']),
                    status=row['status'],
                    metadata=json.loads(row['metadata']) if row['metadata'] and row['metadata'].strip() else {},
                    memory_count=row['memory_count'],
                    last_query=row['last_query'] or ''
                )
                sessions.append(session)
            
            return sessions
            
        except Exception as e:
            logger.error(f"列出会话失败: {e}")
            raise MemoryError(f"列出会话失败: {e}") from e
    
    def delete_session(self, session_id: str) -> bool:
        """
        删除会话及其所有记忆
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 删除是否成功
            
        Raises:
            SessionNotFoundError: 会话不存在
            MemoryError: 删除失败
        """
        try:
            # 验证会话存在
            self.get_session(session_id)
            
            cursor = self.conn.cursor()
            
            # 删除会话的所有记忆
            cursor.execute("DELETE FROM memory_chunks WHERE session_id = ?", (session_id,))
            deleted_memories = cursor.rowcount
            
            # 删除会话
            cursor.execute("DELETE FROM conversation_sessions WHERE session_id = ?", (session_id,))
            deleted_sessions = cursor.rowcount
            
            self.conn.commit()
            
            # 更新统计
            self.memory_stats['total_sessions'] = max(0, self.memory_stats['total_sessions'] - deleted_sessions)
            self.memory_stats['total_memories'] = max(0, self.memory_stats['total_memories'] - deleted_memories)
            self.memory_stats['last_activity'] = datetime.now()
            
            logger.info(f"会话删除成功: {session_id}, 删除记忆: {deleted_memories} 条")
            return True
            
        except SessionNotFoundError:
            raise
        except Exception as e:
            logger.error(f"删除会话失败: {e}")
            raise MemoryError(f"删除会话失败: {e}") from e
    
    def add_memory(self, session_id: str, content: str, content_type: str = "text",
                   relevance_score: float = 0.0, importance_score: float = 0.0,
                   metadata: Dict[str, Any] = None) -> MemoryChunk:
        """
        添加记忆
        
        Args:
            session_id: 会话ID
            content: 记忆内容
            content_type: 内容类型
            relevance_score: 相关性分数
            importance_score: 重要性分数
            metadata: 记忆元数据
            
        Returns:
            MemoryChunk: 创建的记忆对象
            
        Raises:
            SessionNotFoundError: 会话不存在
            MemoryStorageError: 记忆存储失败
        """
        try:
            # 验证会话存在
            self.get_session(session_id)
            
            # 创建记忆对象
            memory = MemoryChunk(
                session_id=session_id,
                content=content,
                content_type=content_type,
                relevance_score=relevance_score,
                importance_score=importance_score,
                created_at=datetime.now(),
                metadata=metadata or {}
            )
            
            # 保存到数据库
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO memory_chunks 
                (chunk_id, session_id, content, content_type, relevance_score, 
                 importance_score, created_at, metadata, vector_embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                memory.chunk_id,
                memory.session_id,
                memory.content,
                memory.content_type,
                memory.relevance_score,
                memory.importance_score,
                memory.created_at.isoformat(),
                json.dumps(memory.metadata),
                json.dumps(memory.vector_embedding) if memory.vector_embedding else None
            ))
            
            # 更新会话记忆数量
            cursor.execute("""
                UPDATE conversation_sessions 
                SET memory_count = memory_count + 1, updated_at = ?
                WHERE session_id = ?
            """, (datetime.now().isoformat(), session_id))
            
            self.conn.commit()
            
            # 更新统计
            self.memory_stats['total_memories'] += 1
            self.memory_stats['last_activity'] = datetime.now()
            
            logger.info(f"记忆添加成功: {memory.chunk_id} (会话: {session_id})")
            return memory
            
        except SessionNotFoundError:
            raise
        except Exception as e:
            logger.error(f"添加记忆失败: {e}")
            raise MemoryStorageError(f"添加记忆失败: {e}") from e
    
    def retrieve_memories(self, query: MemoryQuery) -> List[MemoryChunk]:
        """
        检索相关记忆
        
        Args:
            query: 记忆查询对象
            
        Returns:
            List[MemoryChunk]: 相关记忆列表
            
        Raises:
            MemoryRetrievalError: 记忆检索失败
        """
        try:
            # 优先使用文本检索，因为记忆存储在SQLite中
            # 向量检索需要记忆内容也存储在向量数据库中，目前没有实现
            logger.info(f"使用文本检索记忆: session_id={query.session_id}, query_text={query.query_text[:50]}...")
            return self._text_retrieve_memories(query)
                
        except Exception as e:
            logger.error(f"记忆检索失败: {e}")
            raise MemoryRetrievalError(f"记忆检索失败: {e}") from e
    
    def _vector_retrieve_memories(self, query: MemoryQuery) -> List[MemoryChunk]:
        """
        基于向量的记忆检索
        
        Args:
            query: 记忆查询对象
            
        Returns:
            List[MemoryChunk]: 相关记忆列表
        """
        try:
            # 使用现有向量数据库进行检索
            # 这里需要适配现有的向量检索机制
            results = self.vector_db_integration.search_texts(
                query=query.query_text,
                k=query.max_results,
                similarity_threshold=query.similarity_threshold
            )
            
            # 转换为记忆对象
            memories = []
            for result in results:
                # 检查是否属于目标会话
                if result.get('session_id') == query.session_id:
                    memory = MemoryChunk(
                        chunk_id=result.get('chunk_id', ''),
                        session_id=result.get('session_id', ''),
                        content=result.get('content', ''),
                        content_type=result.get('content_type', 'text'),
                        relevance_score=result.get('similarity_score', 0.0),
                        importance_score=result.get('importance_score', 0.0),
                        created_at=datetime.fromisoformat(result.get('created_at', datetime.now().isoformat())),
                        metadata=result.get('metadata', {}),
                        vector_embedding=result.get('vector_embedding')
                    )
                    memories.append(memory)
            
            return memories
            
        except Exception as e:
            logger.error(f"向量记忆检索失败: {e}")
            raise MemoryRetrievalError(f"向量记忆检索失败: {e}") from e
    
    def _text_retrieve_memories(self, query: MemoryQuery) -> List[MemoryChunk]:
        """
        基于文本的记忆检索 - 三层检索策略
        
        Args:
            query: 记忆查询对象
            
        Returns:
            List[MemoryChunk]: 相关记忆列表
        """
        try:
            logger.info(f"🔍 开始三层记忆检索: session_id={query.session_id}, query_text='{query.query_text}'")
            
            # 1. 基础过滤：按session_id和时间范围过滤
            all_memories = self._get_filtered_memories(query)
            
            if not all_memories:
                logger.info("🔍 未找到任何符合基础过滤条件的记忆。")
                return []
            
            logger.info(f"🔍 第一层：时间衰减筛选，候选记忆数量: {len(all_memories)}")
            
            # 2. 关键词匹配 (初步筛选)
            keyword_matched_memories = self._keyword_match_memories(query.query_text, all_memories)
            
            if not keyword_matched_memories:
                logger.info("🔍 关键词匹配未找到相关记忆，返回空结果。")
                return []
            
            logger.info(f"🔍 第二层：关键词匹配，匹配记忆数量: {len(keyword_matched_memories)}")
            
            # 3. 语义相似度计算 (精细排序)
            if keyword_matched_memories:
                logger.info(f"🔍 第三层：语义相似度计算，对 {len(keyword_matched_memories)} 条记忆进行语义相似度计算...")
                scored_memories = self._score_memories_by_relevance(query.query_text, keyword_matched_memories)
                
                # 4. 排序和截断
                sorted_memories = sorted(scored_memories, key=lambda m: m.relevance_score, reverse=True)
                final_memories = sorted_memories[:query.max_results]
                
                # 5. 降级机制：如果结果为空，降低阈值重试
                if not final_memories:
                    logger.warning("🔍 语义相似度计算后无结果，尝试降级检索...")
                    final_memories = self._fallback_retrieval(query, keyword_matched_memories)
                
                logger.info(f"✅ 三层检索完成，返回 {len(final_memories)} 条记忆。")
                return final_memories
            else:
                logger.info("🔍 关键词匹配未找到相关记忆，跳过语义相似度计算。")
                return []
            
        except Exception as e:
            logger.error(f"三层记忆检索失败: {e}")
            raise MemoryRetrievalError(f"三层记忆检索失败: {e}") from e
    
    def _get_filtered_memories(self, query: MemoryQuery) -> List[MemoryChunk]:
        """
        获取基础过滤后的记忆列表（第一层：时间衰减筛选）
        
        Args:
            query: 记忆查询对象
            
        Returns:
            List[MemoryChunk]: 基础过滤后的记忆列表
        """
        try:
            cursor = self.conn.cursor()
            
            # 构建查询条件
            conditions = ["session_id = ?"]
            params = [query.session_id]
            
            # 时间窗口过滤
            time_window_hours = self.config_manager.get_time_window_hours()
            if time_window_hours > 0:
                time_threshold = datetime.now() - timedelta(hours=time_window_hours)
                conditions.append("created_at >= ?")
                params.append(time_threshold.isoformat())
            
            if query.content_types:
                placeholders = ','.join(['?' for _ in query.content_types])
                conditions.append(f"content_type IN ({placeholders})")
                params.extend(query.content_types)
            
            if query.time_range:
                if 'start' in query.time_range:
                    conditions.append("created_at >= ?")
                    params.append(query.time_range['start'].isoformat())
                if 'end' in query.time_range:
                    conditions.append("created_at <= ?")
                    params.append(query.time_range['end'].isoformat())
            
            # 执行查询
            where_clause = " AND ".join(conditions)
            cursor.execute(f"""
                SELECT * FROM memory_chunks 
                WHERE {where_clause}
                ORDER BY created_at DESC
            """, params)
            
            rows = cursor.fetchall()
            memories = []
            
            for row in rows:
                memory = MemoryChunk(
                    chunk_id=row['chunk_id'],
                    session_id=row['session_id'],
                    content=row['content'],
                    content_type=row['content_type'],
                    relevance_score=row['relevance_score'],
                    importance_score=row['importance_score'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    metadata=json.loads(row['metadata']) if row['metadata'] and row['metadata'].strip() else {},
                    vector_embedding=json.loads(row['vector_embedding']) if row['vector_embedding'] else None
                )
                memories.append(memory)
            
            return memories
            
        except Exception as e:
            logger.error(f"基础记忆过滤失败: {e}")
            raise MemoryRetrievalError(f"基础记忆过滤失败: {e}") from e
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        从查询文本中提取关键词 - 支持jieba分词
        
        Args:
            text: 查询文本
            
        Returns:
            List[str]: 关键词列表
        """
        try:
            if not text or not text.strip():
                return []
            
            # 检查是否启用jieba分词
            if JIEBA_AVAILABLE and self.config_manager.is_jieba_enabled():
                return self._extract_keywords_with_jieba(text)
            else:
                return self._extract_keywords_simple(text)
                
        except Exception as e:
            logger.warning(f"关键词提取失败: {e}")
            return []
    
    def _extract_keywords_with_jieba(self, text: str) -> List[str]:
        """
        使用jieba分词提取关键词
        
        Args:
            text: 查询文本
            
        Returns:
            List[str]: 关键词列表
        """
        try:
            # 使用jieba分词和词性标注
            words = pseg.cut(text)
            
            # 停用词集合
            stop_words = {
                '的', '了', '是', '在', '有', '和', '与', '或', '但', '而', 
                '它', '他', '她', '这', '那', '什么', '怎么', '为什么', '如何', 
                '吗', '呢', '吧', '啊', '呀', '哦', '嗯', '就', '都', '也', 
                '还', '要', '会', '能', '可以', '应该', '可能', '已经', '一直'
            }
            
            # 保留的词性
            keep_pos = {'n', 'v', 'a', 'nr', 'ns', 'nt', 'nw', 'nz', 'vn', 'an'}
            
            keywords = []
            for word, pos in words:
                word = word.strip()
                if (len(word) >= 2 and 
                    word not in stop_words and 
                    pos in keep_pos):
                    keywords.append(word)
            
            logger.debug(f"jieba分词结果: {keywords}")
            return keywords
            
        except Exception as e:
            logger.warning(f"jieba分词失败: {e}")
            return self._extract_keywords_simple(text)
    
    def _extract_keywords_simple(self, text: str) -> List[str]:
        """
        简单关键词提取（备用方案）
        
        Args:
            text: 查询文本
            
        Returns:
            List[str]: 关键词列表
        """
        try:
            # 移除标点符号，保留中文字符、英文字母和数字
            cleaned_text = re.sub(r'[^\u4e00-\u9fff\w\s]', ' ', text)
            
            # 按空格分割
            words = cleaned_text.split()
            
            # 过滤停用词和短词
            stop_words = {
                '的', '了', '是', '在', '有', '和', '与', '或', '但', '而', 
                '它', '他', '她', '这', '那', '什么', '怎么', '为什么', '如何', 
                '吗', '呢', '吧', '啊', '呀', '哦', '嗯', '就', '都', '也', 
                '还', '要', '会', '能', '可以', '应该', '可能', '已经', '一直'
            }
            
            keywords = []
            for word in words:
                word = word.strip()
                if len(word) >= 2 and word not in stop_words:
                    keywords.append(word)
            
            logger.debug(f"简单分词结果: {keywords}")
            return keywords
            
        except Exception as e:
            logger.warning(f"简单关键词提取失败: {e}")
            return []
    
    def _keyword_match_memories(self, query_text: str, memories: List[MemoryChunk]) -> List[MemoryChunk]:
        """
        关键词匹配记忆（第二层：关键词匹配）
        
        Args:
            query_text: 查询文本
            memories: 候选记忆列表
            
        Returns:
            List[MemoryChunk]: 关键词匹配的记忆列表
        """
        try:
            if not query_text or not memories:
                return []
            
            query_keywords = set(self._extract_keywords(query_text))
            if not query_keywords:
                logger.warning("查询文本无法提取关键词")
                return []
            
            matched_memories = []
            keyword_threshold = self.config_manager.get_keyword_threshold()
            
            for memory in memories:
                memory_keywords = set(self._extract_keywords(memory.content))
                if not memory_keywords:
                    continue
                
                # 计算Jaccard相似度
                intersection = len(query_keywords & memory_keywords)
                union = len(query_keywords | memory_keywords)
                
                if union > 0:
                    jaccard_similarity = intersection / union
                    
                    # 应用时间衰减
                    time_score = self._calculate_time_decay_score(memory, datetime.now())
                    
                    # 综合评分
                    final_score = jaccard_similarity * 0.7 + time_score * 0.3
                    
                    if final_score >= keyword_threshold:
                        # 更新记忆的相关性分数
                        memory.relevance_score = final_score
                        matched_memories.append(memory)
                        
                        logger.debug(f"关键词匹配: {memory.chunk_id}, 相似度: {jaccard_similarity:.3f}, 时间分数: {time_score:.3f}, 综合分数: {final_score:.3f}")
            
            logger.info(f"关键词匹配完成: {len(matched_memories)}/{len(memories)} 条记忆通过匹配")
            return matched_memories
            
        except Exception as e:
            logger.error(f"关键词匹配失败: {e}")
            return []
    
    def _calculate_time_decay_score(self, memory: MemoryChunk, current_time: datetime) -> float:
        """
        计算时间衰减分数
        
        Args:
            memory: 记忆对象
            current_time: 当前时间
            
        Returns:
            float: 时间衰减分数
        """
        try:
            time_diff = (current_time - memory.created_at).total_seconds() / 3600  # 转换为小时
            decay_factor = self.config_manager.get_time_decay_factor()
            return math.exp(-decay_factor * time_diff)
        except Exception as e:
            logger.warning(f"时间衰减计算失败: {e}")
            return 1.0  # 默认分数
    
    def _score_memories_by_relevance(self, query_text: str, memories: List[MemoryChunk]) -> List[MemoryChunk]:
        """
        基于语义相似度计算记忆相关性分数（第三层：语义相似度计算）
        
        Args:
            query_text: 查询文本
            memories: 候选记忆列表
            
        Returns:
            List[MemoryChunk]: 带相关性分数的记忆列表
        """
        try:
            if not query_text or not memories:
                return []
            
            # 检查是否启用TF-IDF
            if JIEBA_AVAILABLE and self.config_manager.is_tfidf_enabled():
                return self._score_memories_with_tfidf(query_text, memories)
            else:
                return self._score_memories_simple(query_text, memories)
                
        except Exception as e:
            logger.error(f"语义相似度计算失败: {e}")
            return memories  # 返回原始记忆列表
    
    def _score_memories_with_tfidf(self, query_text: str, memories: List[MemoryChunk]) -> List[MemoryChunk]:
        """
        使用TF-IDF计算语义相似度
        
        Args:
            query_text: 查询文本
            memories: 候选记忆列表
            
        Returns:
            List[MemoryChunk]: 带相关性分数的记忆列表
        """
        try:
            # 准备文档集合
            documents = [query_text]
            memory_contents = []
            
            for memory in memories:
                memory_contents.append(memory.content)
                documents.append(memory.content)
            
            # 创建TF-IDF向量化器
            tfidf_vectorizer = TfidfVectorizer(
                tokenizer=self._extract_keywords,
                lowercase=False,
                max_features=1000,
                min_df=1,
                max_df=0.95
            )
            
            # 计算TF-IDF矩阵
            tfidf_matrix = tfidf_vectorizer.fit_transform(documents)
            
            # 计算查询与每个记忆的余弦相似度
            query_vector = tfidf_matrix[0:1]
            memory_vectors = tfidf_matrix[1:]
            
            similarities = cosine_similarity(query_vector, memory_vectors)[0]
            
            # 更新记忆的相关性分数
            semantic_threshold = self.config_manager.get_semantic_threshold()
            
            for i, memory in enumerate(memories):
                semantic_score = similarities[i]
                
                # 应用时间衰减
                time_score = self._calculate_time_decay_score(memory, datetime.now())
                
                # 综合评分：语义相似度 + 时间衰减
                final_score = semantic_score * 0.6 + time_score * 0.4
                
                # 更新记忆的相关性分数
                memory.relevance_score = final_score
                
                logger.debug(f"语义相似度: {memory.chunk_id}, 语义分数: {semantic_score:.3f}, 时间分数: {time_score:.3f}, 综合分数: {final_score:.3f}")
            
            # 过滤低分记忆
            filtered_memories = [m for m in memories if m.relevance_score >= semantic_threshold]
            
            logger.info(f"TF-IDF语义相似度计算完成: {len(filtered_memories)}/{len(memories)} 条记忆通过语义匹配")
            return filtered_memories
            
        except Exception as e:
            logger.warning(f"TF-IDF计算失败: {e}")
            return self._score_memories_simple(query_text, memories)
    
    def _score_memories_simple(self, query_text: str, memories: List[MemoryChunk]) -> List[MemoryChunk]:
        """
        简单语义相似度计算（备用方案）
        
        Args:
            query_text: 查询文本
            memories: 候选记忆列表
            
        Returns:
            List[MemoryChunk]: 带相关性分数的记忆列表
        """
        try:
            query_keywords = set(self._extract_keywords(query_text))
            if not query_keywords:
                return memories
            
            for memory in memories:
                memory_keywords = set(self._extract_keywords(memory.content))
                if not memory_keywords:
                    continue
                
                # 计算关键词重叠度
                intersection = len(query_keywords & memory_keywords)
                union = len(query_keywords | memory_keywords)
                
                if union > 0:
                    keyword_similarity = intersection / union
                    
                    # 应用时间衰减
                    time_score = self._calculate_time_decay_score(memory, datetime.now())
                    
                    # 综合评分
                    final_score = keyword_similarity * 0.7 + time_score * 0.3
                    memory.relevance_score = final_score
                    
                    logger.debug(f"简单语义计算: {memory.chunk_id}, 关键词相似度: {keyword_similarity:.3f}, 时间分数: {time_score:.3f}, 综合分数: {final_score:.3f}")
            
            logger.info(f"简单语义相似度计算完成: {len(memories)} 条记忆")
            return memories
            
        except Exception as e:
            logger.error(f"简单语义相似度计算失败: {e}")
            return memories
    
    def _fallback_retrieval(self, query: MemoryQuery, keyword_matched_memories: List[MemoryChunk]) -> List[MemoryChunk]:
        """
        降级检索机制：当正常检索无结果时，使用更宽松的条件
        
        Args:
            query: 记忆查询对象
            keyword_matched_memories: 关键词匹配的记忆列表
            
        Returns:
            List[MemoryChunk]: 降级检索的记忆列表
        """
        try:
            if not keyword_matched_memories:
                return []
            
            logger.info("🔍 执行降级检索：使用更宽松的语义阈值")
            
            # 使用更宽松的语义阈值
            original_threshold = self.config_manager.get_semantic_threshold()
            fallback_threshold = min(0.1, original_threshold * 0.5)  # 降低到原阈值的50%或0.1
            
            # 临时更新阈值
            self.config_manager.update_config('retrieval.semantic_threshold', fallback_threshold)
            
            try:
                # 重新计算语义相似度
                scored_memories = self._score_memories_by_relevance(query.query_text, keyword_matched_memories)
                
                # 如果还是没有结果，直接返回按时间排序的记忆
                if not scored_memories:
                    logger.warning("🔍 降级检索仍无结果，返回按时间排序的记忆")
                    # 按时间排序，返回最近的记忆
                    sorted_memories = sorted(keyword_matched_memories, key=lambda m: m.created_at, reverse=True)
                    return sorted_memories[:query.max_results]
                
                # 排序和截断
                sorted_memories = sorted(scored_memories, key=lambda m: m.relevance_score, reverse=True)
                return sorted_memories[:query.max_results]
                
            finally:
                # 恢复原始阈值
                self.config_manager.update_config('retrieval.semantic_threshold', original_threshold)
                
        except Exception as e:
            logger.error(f"降级检索失败: {e}")
            # 最后的降级：返回按时间排序的记忆
            sorted_memories = sorted(keyword_matched_memories, key=lambda m: m.created_at, reverse=True)
            return sorted_memories[:query.max_results]
    
    def get_session_memories(self, session_id: str, max_results: int = 100) -> List[MemoryChunk]:
        """
        获取会话的所有记忆（不进行语义搜索）
        
        Args:
            session_id: 会话ID
            max_results: 最大返回结果数
            
        Returns:
            List[MemoryChunk]: 记忆列表
            
        Raises:
            SessionNotFoundError: 会话不存在
            MemoryRetrievalError: 获取记忆失败
        """
        try:
            # 验证会话存在
            self.get_session(session_id)
            
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM memory_chunks 
                WHERE session_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (session_id, max_results))
            
            rows = cursor.fetchall()
            memories = []
            
            for row in rows:
                memory = MemoryChunk(
                    chunk_id=row['chunk_id'],
                    session_id=row['session_id'],
                    content=row['content'],
                    content_type=row['content_type'],
                    relevance_score=row['relevance_score'],
                    importance_score=row['importance_score'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    metadata=json.loads(row['metadata']) if row['metadata'] and row['metadata'].strip() else {},
                    vector_embedding=row['vector_embedding']
                )
                memories.append(memory)
            
            logger.info(f"获取会话 {session_id} 的记忆: {len(memories)} 条")
            return memories
            
        except SessionNotFoundError:
            raise
        except Exception as e:
            logger.error(f"获取会话记忆失败: {e}")
            raise MemoryRetrievalError(f"获取会话记忆失败: {e}") from e
    
    def compress_session_memories(self, session_id: str, 
                                 request: CompressionRequest = None) -> Tuple[List[MemoryChunk], Dict[str, Any]]:
        """
        压缩会话记忆
        
        Args:
            session_id: 会话ID
            request: 压缩请求（可选）
            
        Returns:
            Tuple[List[MemoryChunk], Dict[str, Any]]: 压缩后的记忆列表和压缩信息
        """
        try:
            # 验证会话存在
            self.get_session(session_id)
            
            # 获取会话的所有记忆
            query = MemoryQuery(session_id=session_id, max_results=1000)
            memories = self.retrieve_memories(query)
            
            if not memories:
                logger.info(f"会话 {session_id} 没有记忆需要压缩")
                return [], {}
            
            # 创建压缩请求
            if not request:
                request = CompressionRequest(
                    session_id=session_id,
                    strategy=self.config_manager.get_config_value('compression.strategy', 'semantic'),
                    threshold=self.config_manager.get_config_value('compression.threshold', 20),
                    max_ratio=self.config_manager.get_config_value('compression.max_compression_ratio', 0.3)
                )
            
            # 执行压缩
            compressed_memories, compression_record = self.compression_engine.compress_memories(memories, request)
            
            # 如果压缩成功，更新数据库
            if len(compressed_memories) < len(memories):
                self._update_session_memories(session_id, compressed_memories, compression_record)
            
            # 构建压缩信息
            compression_info = {
                'original_count': len(memories),
                'compressed_count': len(compressed_memories),
                'compression_ratio': compression_record.compression_ratio,
                'strategy': compression_record.strategy,
                'compression_time': compression_record.created_at.isoformat()
            }
            
            logger.info(f"会话记忆压缩完成: {session_id}, 压缩比例: {compression_record.compression_ratio:.2f}")
            return compressed_memories, compression_info
            
        except Exception as e:
            logger.error(f"压缩会话记忆失败: {e}")
            raise MemoryError(f"压缩会话记忆失败: {e}") from e
    
    def _update_session_memories(self, session_id: str, compressed_memories: List[MemoryChunk], 
                                compression_record) -> None:
        """
        更新会话记忆（替换为压缩后的记忆）
        
        Args:
            session_id: 会话ID
            compressed_memories: 压缩后的记忆列表
            compression_record: 压缩记录
        """
        try:
            cursor = self.conn.cursor()
            
            # 删除原有记忆
            cursor.execute("DELETE FROM memory_chunks WHERE session_id = ?", (session_id,))
            
            # 插入压缩后的记忆
            for memory in compressed_memories:
                cursor.execute("""
                    INSERT INTO memory_chunks 
                    (chunk_id, session_id, content, content_type, relevance_score, 
                     importance_score, created_at, metadata, vector_embedding)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    memory.chunk_id,
                    memory.session_id,
                    memory.content,
                    memory.content_type,
                    memory.relevance_score,
                    memory.importance_score,
                    memory.created_at.isoformat(),
                    json.dumps(memory.metadata),
                    json.dumps(memory.vector_embedding) if memory.vector_embedding else None
                ))
            
            # 保存压缩记录
            cursor.execute("""
                INSERT INTO compression_records 
                (record_id, session_id, original_count, compressed_count, 
                 compression_ratio, strategy, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                compression_record.record_id,
                compression_record.session_id,
                compression_record.original_count,
                compression_record.compressed_count,
                compression_record.compression_ratio,
                compression_record.strategy,
                compression_record.created_at.isoformat(),
                json.dumps(compression_record.metadata)
            ))
            
            # 更新会话记忆数量
            cursor.execute("""
                UPDATE conversation_sessions 
                SET memory_count = ?, updated_at = ?
                WHERE session_id = ?
            """, (len(compressed_memories), datetime.now().isoformat(), session_id))
            
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"更新会话记忆失败: {e}")
            raise MemoryError(f"更新会话记忆失败: {e}") from e
    
    def _check_session_limit(self, user_id: str) -> bool:
        """
        检查用户会话数量限制
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否在限制范围内
        """
        try:
            max_sessions = self.session_config.get('max_sessions_per_user', 100)
            
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM conversation_sessions 
                WHERE user_id = ? AND status = 'active'
            """, (user_id,))
            
            current_count = cursor.fetchone()[0]
            return current_count < max_sessions
            
        except Exception as e:
            logger.warning(f"检查会话限制失败: {e}")
            return True  # 出错时允许创建会话
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        获取记忆统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            cursor = self.conn.cursor()
            
            # 获取会话统计
            cursor.execute("SELECT COUNT(*) FROM conversation_sessions WHERE status = 'active'")
            active_sessions = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM memory_chunks")
            total_memories = cursor.fetchone()[0]
            
            # 计算平均记忆数
            avg_memories = total_memories / active_sessions if active_sessions > 0 else 0
            
            stats = self.memory_stats.copy()
            stats.update({
                'active_sessions': active_sessions,
                'total_memories': total_memories,
                'avg_memories_per_session': avg_memories
            })
            
            return stats
            
        except Exception as e:
            logger.error(f"获取记忆统计失败: {e}")
            return self.memory_stats.copy()
    
    def close(self) -> None:
        """
        关闭数据库连接
        """
        try:
            if hasattr(self, 'conn'):
                self.conn.close()
                logger.info("记忆数据库连接已关闭")
        except Exception as e:
            logger.error(f"关闭数据库连接失败: {e}")
