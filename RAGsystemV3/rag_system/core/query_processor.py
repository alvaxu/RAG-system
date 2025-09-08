"""
查询处理器模块 - 重构版

RAG系统的查询处理器，严格按照33.V3_RAG查询处理模块详细设计文档重构
采用新的架构设计：查询路由器 + 统一服务接口 + 智能处理器
"""

import logging
import time
from typing import Dict, List, Optional, Any

from .config_integration import ConfigIntegration
from .query_router import SimpleQueryRouter
from .common_models import QueryOptions, QueryResult, QueryType
from .spacy_query_rewriter import get_query_rewriter
from .exceptions import (
    ServiceInitializationError,
    QueryProcessingError,
    ConfigurationError
)

logger = logging.getLogger(__name__)


class QueryProcessor:
    """查询处理器 - 重构版，严格按照设计文档实现"""
    
    def __init__(self, config_integration: ConfigIntegration, 
                 retrieval_engine=None, llm_caller=None, 
                 reranking_service=None, attribution_service=None, 
                 display_service=None, metadata_manager=None, memory_manager=None):
        """
        初始化查询处理器
        
        :param config_integration: 配置集成管理器实例
        :param retrieval_engine: 召回引擎实例（可选）
        :param llm_caller: LLM调用器实例（可选）
        :param reranking_service: 重排序服务实例（可选）
        :param attribution_service: 溯源服务实例（可选）
        :param display_service: 展示服务实例（可选）
        :param metadata_manager: 元数据管理器实例（可选）
        :param memory_manager: 记忆管理器实例（可选）
        """
        self.config = config_integration
        
        # 存储传入的服务实例（如果提供）
        self.retrieval_engine = retrieval_engine
        self.llm_caller = llm_caller
        self.reranking_service = reranking_service
        self.attribution_service = attribution_service
        self.display_service = display_service
        self.metadata_manager = metadata_manager
        self.memory_manager = memory_manager
        
        try:
            # 初始化查询路由器
            self.query_router = SimpleQueryRouter(config_integration)
            
            logger.info("查询处理器重构版初始化完成")
            
        except (ServiceInitializationError, ConfigurationError) as e:
            logger.error(f"查询处理器重构版初始化失败: {e}")
            raise ServiceInitializationError(f"查询处理器重构版初始化失败: {e}") from e
        except Exception as e:
            logger.error(f"查询处理器重构版初始化失败（未知错误）: {e}")
            raise ServiceInitializationError(f"查询处理器重构版初始化失败: {e}") from e
    
    def get_service_instance(self, service_name: str):
        """
        获取指定的服务实例
        
        :param service_name: 服务名称
        :return: 服务实例或None
        """
        service_map = {
            'retrieval_engine': self.retrieval_engine,
            'llm_caller': self.llm_caller,
            'reranking_service': self.reranking_service,
            'attribution_service': self.attribution_service,
            'display_service': self.display_service,
            'metadata_manager': self.metadata_manager
        }
        return service_map.get(service_name)
    
    def has_service(self, service_name: str) -> bool:
        """
        检查是否提供了指定的服务
        
        :param service_name: 服务名称
        :return: 是否可用
        """
        return self.get_service_instance(service_name) is not None
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        获取服务状态信息
        
        :return: 服务状态字典
        """
        return {
            'status': 'ready',
            'service_type': 'QueryProcessor',
            'config_integration': self.config is not None,
            'query_router': self.query_router is not None,
            'services': {
                'retrieval_engine': self.has_service('retrieval_engine'),
                'llm_caller': self.has_service('llm_caller'),
                'reranking_service': self.has_service('reranking_service'),
                'attribution_service': self.has_service('attribution_service'),
                'display_service': self.has_service('display_service'),
                'metadata_manager': self.has_service('metadata_manager')
            },
            'features': [
                'query_routing',
                'smart_processing',
                'hybrid_processing',
                'service_integration'
            ]
        }
    
    async def process_query(self, query: str, query_type: str = "auto", 
                          options: Dict[str, Any] = None) -> QueryResult:
        """
        查询处理主入口 - 重构版，严格按照设计文档实现
        
        :param query: 查询文本
        :param query_type: 查询类型，默认为"auto"自动检测
        :param options: 查询选项
        :return: 查询结果
        """
        start_time = time.time()
        
        try:
            logger.info(f"开始查询处理: {query[:50]}...，类型: {query_type}")
            
            # 1. 检索相关历史记忆（如果可用）
            context_memories = []
            logger.info(f"🔍 记忆检索条件检查:")
            logger.info(f"  - memory_manager存在: {self.memory_manager is not None}")
            logger.info(f"  - options存在: {options is not None}")
            logger.info(f"  - session_id: {options.get('session_id') if options else None}")
            logger.info(f"  - user_id: {options.get('user_id') if options else None}")
            logger.info(f"  - 完整options: {options}")
            
            # 如果没有session_id但有user_id，先创建会话
            if self.memory_manager and options and not options.get('session_id') and options.get('user_id'):
                try:
                    logger.info(f"🆕 为记忆检索创建会话: user_id={options.get('user_id')}")
                    session = self.memory_manager.create_session(user_id=options.get('user_id'))
                    options['session_id'] = session.session_id
                    logger.info(f"✅ 创建会话成功: {session.session_id}")
                except Exception as e:
                    logger.warning(f"❌ 创建会话失败: {e}")
            
            # 2. 查询重写：先进行查询重写，再检索历史记忆
            rewritten_query = query
            context_memories = []
            
            if self.memory_manager and options and options.get('session_id'):
                try:
                    # 2.1 先快速检索少量历史记忆用于查询重写
                    logger.info(f"🔍 开始快速检索历史记忆用于查询重写:")
                    logger.info(f"  - 当前查询: '{query}'")
                    logger.info(f"  - 会话ID: {options.get('session_id')}")
                    logger.info(f"  - 用户ID: {options.get('user_id')}")
                    
                    temp_memories = await self._retrieve_context_memories_for_rewrite(query, options)
                    if temp_memories:
                        logger.info(f"✅ 检索到 {len(temp_memories)} 条历史记忆用于查询重写")
                        
                        # 2.2 基于历史记忆进行查询重写
                        try:
                            logger.info(f"🔄 开始查询重写: 原始查询='{query}'")
                            rewritten_query = self._rewrite_query_with_context(query, temp_memories)
                            if rewritten_query != query:
                                logger.info(f"✅ 查询重写成功: '{query}' -> '{rewritten_query}'")
                                # 保存重写信息到options中
                                if options:
                                    options['original_query'] = query
                                    options['rewritten_query'] = rewritten_query
                                    options['query_rewritten'] = True
                            else:
                                logger.info(f"⏭️ 查询无需重写: '{query}'")
                        except Exception as e:
                            logger.warning(f"❌ 查询重写失败: {e}")
                            import traceback
                            logger.warning(f"❌ 错误详情: {traceback.format_exc()}")
                    
                    # 2.3 使用重写后的查询检索相关历史记忆
                    logger.info(f"🔍 使用重写后的查询检索历史记忆: '{rewritten_query}'")
                    context_memories = await self._retrieve_context_memories(rewritten_query, options)
                    if context_memories:
                        logger.info(f"✅ 检索到 {len(context_memories)} 条相关历史记忆")
                        for i, memory in enumerate(context_memories[:3]):
                            logger.info(f"  - 记忆{i+1}: {memory.get('content', '')[:100]}...")
                    else:
                        logger.info("❌ 未找到相关历史记忆")
                        
                except Exception as e:
                    logger.warning(f"❌ 历史记忆处理失败: {e}")
                    import traceback
                    logger.warning(f"❌ 错误详情: {traceback.format_exc()}")
            else:
                logger.info(f"⏭️ 跳过历史记忆处理:")
                logger.info(f"  - memory_manager存在: {self.memory_manager is not None}")
                logger.info(f"  - options存在: {options is not None}")
                logger.info(f"  - session_id存在: {options.get('session_id') if options else None}")
                logger.info(f"  - 条件不满足，跳过记忆处理")
            
            # 3. 构建查询选项（包含历史记忆和重写后的查询）
            query_options = self._build_query_options(options, context_memories, rewritten_query)
            
            # 4. 通过查询路由器处理查询（使用重写后的查询）
            result = await self.query_router.route_query(rewritten_query, query_type, query_options)
            
            # 4.1. 将查询选项的元数据复制到结果中
            if hasattr(query_options, 'metadata') and query_options.metadata:
                result.metadata = query_options.metadata.copy()
                logger.info(f"复制查询重写元数据到结果: {result.metadata}")
            
            # 4. 如果有历史记忆，更新结果中的上下文信息
            if context_memories:
                result.processing_metadata = result.processing_metadata or {}
                result.processing_metadata['context_memories_count'] = len(context_memories)
                result.processing_metadata['memory_enhanced'] = True
                logger.info(f"设置记忆增强: {len(context_memories)} 条历史记忆")
            
            # 3. 更新处理元数据
            processing_time = time.time() - start_time
            if result.processing_metadata is None:
                result.processing_metadata = {}
            
            result.processing_metadata.update({
                'total_processing_time': processing_time,
                'query_processor_version': 'refactored_v2',
                'query_router_used': True
            })
            
            # 4. 记录对话到记忆模块（如果可用）
            if self.memory_manager and result.success:
                try:
                    logger.info(f"开始记录对话到记忆模块: query={query[:50]}..., success={result.success}")
                    await self._record_conversation_to_memory(query, result, options)
                    logger.info("对话记录到记忆模块成功")
                except Exception as e:
                    logger.error(f"记录对话到记忆模块失败: {e}", exc_info=True)
            else:
                logger.warning(f"跳过记忆记录: memory_manager={self.memory_manager is not None}, result.success={result.success}")
            
            logger.info(f"查询处理完成，类型: {query_type}，结果状态: {result.success}，耗时: {processing_time:.2f}秒")
            
            return result
            
        except (QueryProcessingError, ServiceInitializationError) as e:
            processing_time = time.time() - start_time
            error_msg = f"查询处理失败: {str(e)}"
            logger.error(error_msg)
            
            result = QueryResult()
            result.success = False
            result.error_message = error_msg
            result.processing_metadata = {
                'total_processing_time': processing_time,
                'error': str(e),
                'query_processor_version': 'refactored_v2'
            }
            return result
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"查询处理失败（未知错误）: {str(e)}"
            logger.error(error_msg)
            
            result = QueryResult()
            result.success = False
            result.error_message = error_msg
            result.processing_metadata = {
                'total_processing_time': processing_time,
                'error': str(e),
                'query_processor_version': 'refactored_v2'
            }
            return result
    
    def _build_query_options(self, options: Dict[str, Any] = None, context_memories: List[Dict[str, Any]] = None, rewritten_query: str = None) -> QueryOptions:
        """
        构建查询选项
        
        :param options: 原始选项字典
        :return: 查询选项对象
        """
        try:
            if options is None:
                options = {}
            
            # 从配置获取默认值
            default_max_results = self.config.get_rag_config('query_processing.max_results', 10)
            default_relevance_threshold = self.config.get_rag_config('query_processing.relevance_threshold', 0.5)
            default_context_length_limit = self.config.get_rag_config('query_processing.max_context_length', 4000)
            default_enable_streaming = self.config.get_rag_config('query_processing.enable_streaming', True)
            
            # 构建查询选项
            context_memories = context_memories or []
            logger.info(f"🔧 构建QueryOptions:")
            logger.info(f"  - context_memories数量: {len(context_memories)}")
            logger.info(f"  - rewritten_query: '{rewritten_query}'")
            if context_memories:
                logger.info(f"  - 历史记忆内容预览:")
                for i, memory in enumerate(context_memories[:3]):
                    logger.info(f"    {i+1}. {memory.get('content', '')[:50]}...")
            else:
                logger.info(f"  - 没有历史记忆")
            
            # 准备metadata
            metadata = {}
            if rewritten_query and rewritten_query != options.get('original_query', ''):
                metadata['original_query'] = options.get('original_query', '')
                metadata['rewritten_query'] = rewritten_query
                metadata['query_rewritten'] = True
            
            query_options = QueryOptions(
                max_results=options.get('max_results', default_max_results),
                relevance_threshold=options.get('relevance_threshold', default_relevance_threshold),
                context_length_limit=options.get('context_length_limit', default_context_length_limit),
                enable_streaming=options.get('enable_streaming', default_enable_streaming),
                context_memories=context_memories,
                metadata=metadata
            )
            
            
            logger.info(f"✅ QueryOptions构建完成，context_memories={len(query_options.context_memories)}条")
            
            return query_options
            
        except Exception as e:
            logger.warning(f"构建查询选项失败: {e}，使用默认选项")
            return QueryOptions()
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        try:
            return {
                'processor_type': 'QueryProcessor_Refactored',
                'architecture': 'router_based',
                'components': {
                    'query_router': 'SimpleQueryRouter',
                    'smart_processor': 'SimpleSmartProcessor',
                    'hybrid_processor': 'SimpleHybridProcessor',
                    'unified_services': 'UnifiedServices'
                },
                'processing_flow': [
                    'query_input',
                    'router_dispatch',
                    'type_detection',
                    'content_retrieval',
                    'reranking',
                    'llm_generation',
                    'result_integration'
                ]
            }
            
        except Exception as e:
            logger.error(f"获取处理统计信息失败: {e}")
            return {
                'processor_type': 'QueryProcessor_Refactored',
                'error': str(e)
            }
    
    async def _record_conversation_to_memory(self, query: str, result: QueryResult, options: Dict[str, Any] = None):
        """
        记录对话到记忆模块
        
        :param query: 用户查询
        :param result: 查询结果
        :param options: 查询选项
        """
        try:
            if not self.memory_manager:
                logger.warning("记忆管理器不可用，跳过记忆记录")
                return
            
            # 获取会话ID，如果没有则创建默认会话
            session_id = options.get('session_id') if options else None
            user_id = options.get('user_id', 'web_user') if options else 'web_user'
            
            logger.info(f"记忆记录参数: session_id={session_id}, user_id={user_id}")
            
            if not session_id:
                # 创建默认会话
                logger.info(f"创建新会话，user_id={user_id}")
                session = self.memory_manager.create_session(user_id=user_id)
                session_id = session.session_id
                logger.info(f"为记忆模块创建新会话: {session_id}")
                # 更新options中的session_id，这样API响应中会包含它
                if options:
                    options['session_id'] = session_id
            
            # 构建记忆内容
            memory_content = f"用户询问: {query}"
            if result.answer:
                memory_content += f"\n系统回答: {result.answer}"
            
            logger.info(f"记忆内容长度: {len(memory_content)}")
            
            # 计算相关性和重要性分数
            relevance_score = 0.8  # 默认相关性
            importance_score = 0.7  # 默认重要性
            
            # 如果有检索结果，根据结果数量调整重要性
            if result.results:
                importance_score = min(0.9, 0.5 + len(result.results) * 0.1)
            
            # 添加记忆
            memory_chunk = self.memory_manager.add_memory(
                session_id=session_id,
                content=memory_content,
                content_type="text",
                relevance_score=relevance_score,
                importance_score=importance_score,
                metadata={
                    'query_type': options.get('query_type', 'auto') if options else 'auto',
                    'processing_time': result.processing_metadata.get('total_processing_time', 0) if result.processing_metadata else 0,
                    'retrieved_chunks_count': len(result.results) if result.results else 0,
                    'source': 'rag_query',
                    'user_query': query  # 添加用户查询字段
                }
            )
            
            logger.info(f"对话已记录到记忆模块: 会话={session_id}, 记忆ID={memory_chunk.chunk_id}")
            
        except Exception as e:
            logger.error(f"记录对话到记忆模块失败: {e}")
            raise
    
    async def _retrieve_context_memories(self, query: str, options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        检索相关历史记忆用于上下文增强
        
        :param query: 当前查询
        :param options: 查询选项
        :return: 相关记忆列表
        """
        try:
            session_id = options.get('session_id')
            if not session_id:
                return []
            
            # 构建记忆查询
            from .memory.models import MemoryQuery
            memory_query = MemoryQuery(
                query_text=query,
                session_id=session_id,
                max_results=5,  # 获取多条历史记录
                similarity_threshold=0.1,  # 最低相似度阈值
                content_types=["text"]  # 只检索文本记忆
            )
            
            logger.info(f"🔍 记忆查询参数:")
            logger.info(f"  - query_text: '{query}'")
            logger.info(f"  - session_id: '{session_id}'")
            logger.info(f"  - max_results: 5")
            logger.info(f"  - similarity_threshold: 0.1")
            logger.info(f"  - content_types: ['text']")
            
            # 检索相关记忆
            logger.info(f"🔍 调用memory_manager.retrieve_memories...")
            memories = self.memory_manager.retrieve_memories(memory_query)
            logger.info(f"📊 记忆检索结果: 找到 {len(memories)} 条记忆")
            
            # 详细记录检索到的记忆
            for i, memory in enumerate(memories):
                logger.info(f"  - 记忆{i+1}: ID={memory.chunk_id}, 内容={memory.content[:100]}...")
            
            # 转换为字典格式，便于后续处理
            context_memories = []
            for memory in memories:
                context_memory = {
                    'content': memory.content,
                    'chunk_id': memory.chunk_id,
                    'content_type': memory.content_type,
                    'relevance_score': memory.relevance_score,
                    'importance_score': memory.importance_score,
                    'created_at': memory.created_at.isoformat() if memory.created_at else '',
                    'metadata': memory.metadata,
                    'user_query': memory.metadata.get('user_query') if memory.metadata else None  # 添加用户查询字段
                }
                context_memories.append(context_memory)
            
            # 使用spaCy增强记忆排序
            enhanced_memories = self._enhance_memory_ranking_with_spacy(query, context_memories)
            
            logger.info(f"检索到 {len(enhanced_memories)} 条相关历史记忆（spaCy增强后）")
            return enhanced_memories
            
        except Exception as e:
            logger.error(f"检索历史记忆失败: {e}")
            return []
    
    async def _retrieve_context_memories_for_rewrite(self, query: str, options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        快速检索历史记忆用于查询重写（只检索少量记忆）
        
        :param query: 当前查询
        :param options: 查询选项
        :return: 相关记忆列表
        """
        try:
            session_id = options.get('session_id')
            if not session_id:
                return []
            
            # 构建记忆查询（只获取少量记忆用于重写）
            from .memory.models import MemoryQuery
            memory_query = MemoryQuery(
                query_text=query,
                session_id=session_id,
                max_results=3,  # 只获取3条记忆用于重写
                similarity_threshold=0.1,
                content_types=["text"]
            )
            
            # 检索相关记忆
            memories = self.memory_manager.retrieve_memories(memory_query)
            
            # 转换为字典格式
            context_memories = []
            for memory in memories:
                context_memory = {
                    'content': memory.content,
                    'chunk_id': memory.chunk_id,
                    'content_type': memory.content_type,
                    'relevance_score': memory.relevance_score,
                    'importance_score': memory.importance_score,
                    'created_at': memory.created_at.isoformat() if memory.created_at else '',
                    'metadata': memory.metadata,
                    'user_query': memory.metadata.get('user_query') if memory.metadata else None
                }
                context_memories.append(context_memory)
            
            logger.info(f"快速检索到 {len(context_memories)} 条历史记忆用于查询重写")
            return context_memories
            
        except Exception as e:
            logger.error(f"快速检索历史记忆失败: {e}")
            return []
    
    def _enhance_memory_ranking_with_spacy(self, query: str, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        使用spaCy增强记忆排序
        
        :param query: 当前查询
        :param memories: 记忆列表
        :return: 增强排序后的记忆列表
        """
        try:
            # 获取spaCy查询重写器
            from .spacy_query_rewriter import get_query_rewriter
            rewriter = get_query_rewriter(self.config)
            
            if not rewriter.nlp or not rewriter.spacy_available:
                logger.info("spaCy不可用，使用原始记忆排序")
                return memories
            
            enhanced_memories = []
            
            for memory in memories:
                # 基础TF-IDF相似度（现有）
                tfidf_score = memory.get('relevance_score', 0.0)
                
                # spaCy语义相似度（新增）
                semantic_score = self._calculate_semantic_similarity(query, memory['content'], rewriter.nlp)
                
                # 实体匹配度（新增）
                entity_score = self._calculate_entity_similarity(query, memory['content'], rewriter.nlp)
                
                # 时间衰减（保持现有逻辑）
                time_decay = self._calculate_time_decay(memory.get('created_at'))
                
                # 综合评分
                final_score = (
                    0.4 * tfidf_score +      # 保持现有TF-IDF权重
                    0.3 * semantic_score +   # 新增语义相似度
                    0.2 * entity_score +     # 新增实体匹配度
                    0.1 * time_decay         # 时间衰减
                )
                
                # 添加增强评分到记忆数据
                enhanced_memory = memory.copy()
                enhanced_memory['enhanced_score'] = final_score
                enhanced_memory['tfidf_score'] = tfidf_score
                enhanced_memory['semantic_score'] = semantic_score
                enhanced_memory['entity_score'] = entity_score
                enhanced_memory['time_decay'] = time_decay
                
                enhanced_memories.append(enhanced_memory)
            
            # 按综合评分排序
            enhanced_memories.sort(key=lambda x: x['enhanced_score'], reverse=True)
            
            # 选择最佳记忆（确保最低分数阈值）
            selected_memories = []
            for memory in enhanced_memories:
                if memory['enhanced_score'] >= 0.3:  # 最低相似度阈值
                    selected_memories.append(memory)
            
            logger.info(f"spaCy增强排序: 原始{len(memories)}条 -> 增强{len(selected_memories)}条")
            return selected_memories
            
        except Exception as e:
            logger.error(f"spaCy增强记忆排序失败: {e}")
            return memories
    
    def _calculate_semantic_similarity(self, query: str, memory_content: str, nlp) -> float:
        """计算spaCy语义相似度"""
        try:
            query_doc = nlp(query)
            memory_doc = nlp(memory_content)
            return query_doc.similarity(memory_doc)
        except Exception as e:
            logger.warning(f"spaCy语义相似度计算失败: {e}")
            return 0.0
    
    def _calculate_entity_similarity(self, query: str, memory_content: str, nlp) -> float:
        """计算实体匹配度"""
        try:
            query_doc = nlp(query)
            memory_doc = nlp(memory_content)
            
            # 提取实体
            query_entities = [ent.text for ent in query_doc.ents]
            memory_entities = [ent.text for ent in memory_doc.ents]
            
            # 计算实体重叠度
            if not query_entities or not memory_entities:
                return 0.0
            
            overlap = len(set(query_entities) & set(memory_entities))
            total = len(set(query_entities) | set(memory_entities))
            
            return overlap / total if total > 0 else 0.0
        except Exception as e:
            logger.warning(f"实体相似度计算失败: {e}")
            return 0.0
    
    def _calculate_time_decay(self, created_at_str: str) -> float:
        """计算时间衰减"""
        try:
            if not created_at_str:
                return 0.5  # 默认值
            
            from datetime import datetime, timezone
            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            
            # 计算时间差（小时）
            time_diff = (now - created_at).total_seconds() / 3600
            
            # 指数衰减：越新权重越高
            decay_factor = 0.1
            return max(0.1, 1.0 / (1.0 + decay_factor * time_diff))
        except Exception as e:
            logger.warning(f"时间衰减计算失败: {e}")
            return 0.5
    
    def _rewrite_query_with_context(self, query: str, context_memories: List[Dict[str, Any]]) -> str:
        """
        基于历史记忆重写查询，解析代词指代（使用spaCy）
        
        :param query: 原始查询
        :param context_memories: 历史记忆列表
        :return: 重写后的查询
        """
        try:
            logger.info(f"🔄 开始spaCy查询重写分析: '{query}'")
            
            # 使用spaCy查询重写器
            query_rewriter = get_query_rewriter(self.config)
            rewritten_query = query_rewriter.rewrite_query_with_context(query, context_memories)
            
            if rewritten_query != query:
                logger.info(f"✅ spaCy查询重写成功: '{query}' -> '{rewritten_query}'")
            else:
                logger.info(f"⏭️ 查询无需重写: '{query}'")
            
            return rewritten_query
            
        except Exception as e:
            logger.error(f"spaCy查询重写失败: {e}")
            # 如果spaCy失败，回退到简单版本
            return self._simple_rewrite_query_with_context(query, context_memories)
    
    def _simple_rewrite_query_with_context(self, query: str, context_memories: List[Dict[str, Any]]) -> str:
        """
        简单版本的查询重写（spaCy不可用时的备选方案）
        
        :param query: 原始查询
        :param context_memories: 历史记忆列表
        :return: 重写后的查询
        """
        try:
            logger.info(f"🔄 开始简单查询重写分析: '{query}'")
            
            # 检查是否包含代词
            pronouns = ['它', '他', '她', '这', '那', '这家', '那家', '这个', '那个', '这些', '那些']
            has_pronoun = any(pronoun in query for pronoun in pronouns)
            
            if not has_pronoun:
                logger.info(f"⏭️ 查询不包含代词，无需重写: '{query}'")
                return query
            
            logger.info(f"🔍 检测到代词，开始实体提取: {[p for p in pronouns if p in query]}")
            
            # 从历史记忆中提取实体
            entities = self._extract_entities_from_memories(context_memories)
            logger.info(f"📊 从历史记忆中提取到实体: {entities}")
            
            if not entities:
                logger.info(f"❌ 未找到相关实体，保持原始查询: '{query}'")
                return query
            
            # 重写查询
            rewritten_query = self._replace_pronouns_with_entities(query, entities)
            logger.info(f"✅ 简单查询重写完成: '{query}' -> '{rewritten_query}'")
            
            return rewritten_query
            
        except Exception as e:
            logger.error(f"简单查询重写失败: {e}")
            return query
    
    def _extract_entities_from_memories(self, context_memories: List[Dict[str, Any]]) -> List[str]:
        """
        从历史记忆中提取实体
        
        :param context_memories: 历史记忆列表
        :return: 实体列表
        """
        try:
            entities = []
            
            for memory in context_memories:
                content = memory.get('content', '')
                if not content:
                    continue
                
                # 简单的实体提取规则
                # 1. 提取公司名称（包含"公司"、"集团"、"企业"等）
                import re
                company_patterns = [
                    r'([^，。！？\s]{2,10}(?:公司|集团|企业|科技|股份|有限|控股))',
                    r'([^，。！？\s]{2,10}(?:国际|银行|保险|基金|证券))',
                ]
                
                for pattern in company_patterns:
                    matches = re.findall(pattern, content)
                    entities.extend(matches)
                
                # 2. 提取人名（简单规则）
                name_patterns = [
                    r'([^，。！？\s]{2,4}(?:先生|女士|博士|教授|老师))',
                ]
                
                for pattern in name_patterns:
                    matches = re.findall(pattern, content)
                    entities.extend(matches)
                
                # 3. 提取产品名称（包含"产品"、"服务"等）
                product_patterns = [
                    r'([^，。！？\s]{2,10}(?:产品|服务|技术|系统|平台))',
                ]
                
                for pattern in product_patterns:
                    matches = re.findall(pattern, content)
                    entities.extend(matches)
            
            # 去重并排序
            entities = list(set(entities))
            entities.sort(key=len, reverse=True)  # 按长度排序，优先匹配长实体
            
            logger.info(f"📊 提取到实体: {entities}")
            return entities
            
        except Exception as e:
            logger.error(f"实体提取失败: {e}")
            return []
    
    def _replace_pronouns_with_entities(self, query: str, entities: List[str]) -> str:
        """
        将查询中的代词替换为实体
        
        :param query: 原始查询
        :param entities: 实体列表
        :return: 替换后的查询
        """
        try:
            if not entities:
                return query
            
            rewritten_query = query
            
            # 代词替换规则
            pronoun_replacements = {
                '它': entities[0],  # 使用第一个（最相关的）实体
                '他': entities[0],
                '她': entities[0],
                '这': entities[0],
                '那': entities[0],
                '这家': entities[0],
                '那家': entities[0],
                '这个': entities[0],
                '那个': entities[0],
                '这些': entities[0],
                '那些': entities[0],
            }
            
            # 执行替换
            for pronoun, entity in pronoun_replacements.items():
                if pronoun in rewritten_query:
                    rewritten_query = rewritten_query.replace(pronoun, entity)
                    logger.info(f"🔄 代词替换: '{pronoun}' -> '{entity}'")
            
            return rewritten_query
            
        except Exception as e:
            logger.error(f"代词替换失败: {e}")
            return query
