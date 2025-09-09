"""
统一服务接口模块

RAG系统的统一服务接口，为所有查询类型提供统一的服务调用
严格按照33.V3_RAG查询处理模块详细设计文档实现
"""

import logging
from typing import Dict, List, Any, Optional
import time

from .config_integration import ConfigIntegration
from .retrieval import RetrievalEngine
from .reranking_enhanced import MultiModelReranker
from .llm_caller import LLMCaller
from .context_manager import ContextChunk
from .exceptions import (
    ServiceInitializationError,
    RetrievalError,
    RerankingError,
    LLMServiceError,
    ContentProcessingError,
    ConfigurationError
)

logger = logging.getLogger(__name__)


class UnifiedServices:
    """统一服务接口 - 所有查询类型复用"""
    
    def __init__(self, config_integration: ConfigIntegration):
        """
        初始化统一服务接口
        
        :param config_integration: 配置集成管理器实例
        """
        self.config = config_integration
        
        try:
            # 初始化各个服务
            # 正确初始化向量数据库集成管理器
            from .vector_db_integration import VectorDBIntegration
            self.vector_db_integration = VectorDBIntegration(config_integration)
            
            self.retrieval_service = RetrievalEngine(config_integration, self.vector_db_integration)
            self.reranking_service = MultiModelReranker(config_integration)
            self.llm_service = LLMCaller(config_integration)
            
            logger.info("统一服务接口初始化完成")
            
        except (ServiceInitializationError, ConfigurationError) as e:
            logger.error(f"统一服务接口初始化失败: {e}")
            raise ServiceInitializationError(f"统一服务接口初始化失败: {e}") from e
        except Exception as e:
            logger.error(f"统一服务接口初始化失败（未知错误）: {e}")
            raise ServiceInitializationError(f"统一服务接口初始化失败: {e}") from e
    
    async def retrieve(self, query: str, content_types: List[str] = None, 
                      options: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        统一检索服务 - 支持多类型内容检索
        
        :param query: 查询文本
        :param content_types: 内容类型列表，None表示所有类型
        :param options: 检索选项
        :return: 检索结果列表
        """
        try:
            if content_types is None:
                content_types = ['text', 'image', 'table']
            
            if options is None:
                options = {}
            
            max_results = options.get('max_results', 10)
            relevance_threshold = options.get('relevance_threshold', 0.5)
            
            # 根据内容类型进行检索
            all_results = []
            
            if 'text' in content_types:
                text_results = self.retrieval_service.retrieve_texts(query, max_results, relevance_threshold)
                all_results.extend(text_results)
            
            if 'image' in content_types:
                image_results = self.retrieval_service.retrieve_images(query, max_results, relevance_threshold)
                all_results.extend(image_results)
            
            if 'table' in content_types:
                table_results = self.retrieval_service.retrieve_tables(query, max_results, relevance_threshold)
                all_results.extend(table_results)
            
            logger.info(f"统一检索完成，查询: {query}，返回结果: {len(all_results)}")
            return all_results
            
        except RetrievalError as e:
            logger.error(f"统一检索失败: {e}")
            return []
        except Exception as e:
            logger.error(f"统一检索失败（未知错误）: {e}")
            return []
    
    async def rerank(self, query: str, results: List[Any]) -> List[Dict[str, Any]]:
        """
        重排序服务 - 完全复用
        
        :param query: 查询文本
        :param results: 待重排序的结果列表
        :return: 重排序后的结果
        """
        try:
            if not results:
                return []
            
            logger.info(f"开始统一重排序，处理 {len(results)} 个结果")
            
            # 调用重排序服务
            reranked_results = self.reranking_service.rerank(query, results)
            
            logger.info(f"统一重排序完成")
            return reranked_results
            
        except RerankingError as e:
            logger.error(f"统一重排序失败: {e}")
            # 如果重排序失败，返回原始排序
            return self._fallback_sort(results)
        except Exception as e:
            logger.error(f"统一重排序失败（未知错误）: {e}")
            # 如果重排序失败，返回原始排序
            return self._fallback_sort(results)
    
    async def generate_answer(self, query: str, results: List[Any], context_memories: List[Dict[str, Any]] = None) -> str:
        """
        LLM服务 - 复用+适配，支持历史记忆上下文
        
        :param query: 查询文本
        :param results: 检索结果列表
        :param context_memories: 历史记忆上下文
        :return: 生成的答案
        """
        try:
            if not results:
                return "抱歉，没有找到相关的信息来回答您的问题。"
            
            logger.info("开始生成LLM答案")
            
            # 构建统一上下文
            context_chunks = self._build_unified_context(results)
            
            # 检查历史记忆集成配置
            context_integration_config = self.config.get('rag_system.memory_module.context_integration', {})
            memory_enabled = context_integration_config.get('enabled', True)
            
            # 如果有历史记忆且配置启用，添加到上下文中
            if context_memories and memory_enabled:
                logger.info(f"🧠 UnifiedServices收到历史记忆:")
                logger.info(f"  - 数量: {len(context_memories)}")
                logger.info(f"  - 内容预览:")
                for i, memory in enumerate(context_memories[:3]):
                    logger.info(f"    {i+1}. {memory.get('content', '')[:50]}...")
                logger.info(f"🔧 添加 {len(context_memories)} 条历史记忆到上下文")
                memory_context = self._build_memory_context(context_memories, context_integration_config)
                logger.info(f"📊 构建的memory_context数量: {len(memory_context)}")
                context_chunks.extend(memory_context)
                logger.info(f"✅ 合并后context_chunks总数: {len(context_chunks)}")
            elif context_memories and not memory_enabled:
                logger.info("⏭️ 历史记忆集成已禁用，跳过记忆上下文")
            else:
                logger.info("❌ UnifiedServices: 没有收到历史记忆")
            
            # 调试：查看传递给LLM的完整上下文
            logger.info("🔍 传递给LLM的完整上下文:")
            for i, chunk in enumerate(context_chunks):
                logger.info(f"  - 上下文{i+1}: 类型={chunk.content_type}, 来源={chunk.source}, 内容={chunk.content[:200]}...")
            
            # 调用LLM服务，传递ContextChunk列表
            llm_response = self.llm_service.generate_answer(query, context_chunks)
            
            logger.info(f"LLM答案生成完成，长度: {len(llm_response.answer)} 字符")
            return llm_response.answer
            
        except LLMServiceError as e:
            logger.error(f"LLM答案生成失败: {e}")
            return self._generate_fallback_answer(query, results)
        except Exception as e:
            logger.error(f"LLM答案生成失败（未知错误）: {e}")
            return self._generate_fallback_answer(query, results)
    
    def _build_unified_context(self, results: List[Any]) -> List[ContextChunk]:
        """
        构建统一上下文
        
        :param results: 结果列表
        :return: ContextChunk对象列表
        """
        try:
            if not results:
                return []
            
            # 获取配置的最大上下文长度
            max_context_length = self.config.get_rag_config('query_processing.max_context_length', 4000)
            
            # 按分数排序，选择最相关的内容
            sorted_results = sorted(results, key=lambda x: x.get('similarity_score', 0.0), reverse=True)
            
            context_chunks = []
            current_length = 0
            
            for result in sorted_results:
                # 提取内容
                content = self._extract_content(result)
                if not content:
                    continue
                
                # 检查是否超出长度限制
                if current_length + len(content) > max_context_length:
                    # 截断内容以适应长度限制
                    remaining_length = max_context_length - current_length
                    if remaining_length > 100:  # 至少保留100字符
                        content = content[:remaining_length] + "..."
                    else:
                        break
                
                # 创建ContextChunk对象
                context_chunk = self._dict_to_context_chunk(result, content)
                context_chunks.append(context_chunk)
                current_length += len(content)
                
                # 如果已经达到目标长度，停止添加
                if current_length >= max_context_length:
                    break
            
            logger.info(f"统一上下文构建完成，ContextChunk数量: {len(context_chunks)}")
            
            return context_chunks
            
        except Exception as e:
            logger.error(f"构建统一上下文失败: {e}")
            # 返回前几个结果的ContextChunk对象
            fallback_chunks = []
            for r in results[:3]:
                content = self._extract_content(r)
                if content:
                    chunk = self._dict_to_context_chunk(r, content)
                    fallback_chunks.append(chunk)
            return fallback_chunks
    
    def _build_unified_prompt(self, query: str, context: str) -> str:
        """
        构建统一Prompt
        
        :param query: 查询文本
        :param context: 上下文信息
        :return: 完整的Prompt
        """
        try:
            # 获取系统提示词
            system_prompt = self.config.get_rag_config('models.llm.system_prompt', 
                '你是一个专业的AI助手，能够基于提供的上下文信息生成准确、相关、完整的答案。')
            
            # 构建完整的提示词
            prompt = f"""
{system_prompt}

基于以下上下文信息回答问题：

上下文：
{context}

问题：
{query}

请提供准确、详细的答案：
"""
            return prompt.strip()
            
        except Exception as e:
            logger.error(f"构建统一Prompt失败: {e}")
            # 返回简单的提示词
            return f"基于以下上下文信息回答问题：\n\n上下文：{context}\n\n问题：{query}"
    
    def _dict_to_context_chunk(self, result: Dict[str, Any], content: str) -> ContextChunk:
        """
        安全地将字典转换为ContextChunk对象
        
        :param result: 原始结果字典
        :param content: 提取的内容
        :return: ContextChunk对象
        """
        try:
            return ContextChunk(
                content=content,
                chunk_id=result.get('chunk_id', ''),
                content_type=result.get('chunk_type', 'text'),
                relevance_score=float(result.get('similarity_score', 0.0)),
                source=result.get('document_name', ''),
                metadata=result
            )
        except Exception as e:
            logger.warning(f"转换ContextChunk失败: {e}")
            # 返回默认值
            return ContextChunk(
                content=content,
                chunk_id='',
                content_type='text',
                relevance_score=0.0,
                source='',
                metadata={}
            )
    
    def _extract_content(self, result: Any) -> str:
        """
        从结果中提取内容
        
        :param result: 检索结果
        :return: 提取的内容
        """
        try:
            # 尝试不同的内容字段
            if hasattr(result, 'content') and result.content:
                return str(result.content)
            elif hasattr(result, 'text') and result.text:
                return str(result.text)
            elif hasattr(result, 'page_content') and result.page_content:
                return str(result.page_content)
            elif hasattr(result, 'description') and result.description:
                return str(result.description)
            elif isinstance(result, dict):
                # 如果是字典类型
                if 'content' in result:
                    return str(result['content'])
                elif 'text' in result:
                    return str(result['text'])
                elif 'page_content' in result:
                    return str(result['page_content'])
                elif 'description' in result:
                    return str(result['description'])
            else:
                return str(result)
        except Exception:
            return ""
    
    def _fallback_sort(self, results: List[Any]) -> List[Dict[str, Any]]:
        """
        重排序失败时的回退策略
        
        :param results: 原始结果列表
        :return: 排序后的结果
        """
        try:
            # 按分数排序
            sorted_results = sorted(results, key=lambda x: x.get('score', 0.0), reverse=True)
            return sorted_results
        except Exception as e:
            logger.error(f"回退排序失败: {e}")
            return results
    
    def _generate_fallback_answer(self, query: str, results: List[Any]) -> str:
        """
        LLM服务失败时的回退策略
        
        :param query: 查询文本
        :param results: 检索结果列表
        :return: 回退答案
        """
        try:
            if not results:
                return "抱歉，没有找到相关的信息。"
            
            # 简单的答案生成，不依赖LLM
            top_results = results[:3]
            summary = f"找到{len(results)}个相关结果，其中：\n"
            
            for i, result in enumerate(top_results, 1):
                content_type = result.get('chunk_type', 'unknown')
                score = result.get('score', 0.0)
                summary += f"{i}. {content_type}类型结果（相关性：{score:.2f}）\n"
            
            return summary
            
        except Exception as e:
            logger.error(f"生成回退答案失败: {e}")
            return "抱歉，系统暂时无法处理您的查询，请稍后重试。"
    
    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态信息"""
        return {
            'status': 'ready',
            'service_type': 'UnifiedServices',
            'services': {
                'retrieval_service': self.retrieval_service is not None,
                'reranking_service': self.reranking_service is not None,
                'llm_service': self.llm_service is not None
            },
            'features': [
                'unified_retrieval',
                'unified_reranking',
                'unified_llm',
                'context_building',
                'prompt_building',
                'fallback_strategies',
                'memory_context_integration'
            ]
        }
    
    def _build_memory_context(self, context_memories: List[Dict[str, Any]], config: Dict[str, Any] = None) -> List[ContextChunk]:
        """
        构建历史记忆上下文
        
        :param context_memories: 历史记忆列表
        :param config: 上下文集成配置
        :return: ContextChunk对象列表
        """
        try:
            if not config:
                config = {}
            
            # 从配置中获取参数
            max_memories = config.get('max_memories_in_prompt', 5)
            min_relevance = config.get('min_relevance_score', 0.1)
            max_length = config.get('max_memory_length', 1000)
            include_metadata = config.get('include_memory_metadata', True)
            
            logger.info(f"🔧 开始构建历史记忆上下文，输入记忆数量: {len(context_memories)}")
            logger.info(f"🔧 配置参数: max_memories={max_memories}, min_relevance={min_relevance}, max_length={max_length}")
            
            if context_memories:
                logger.info(f"🔧 输入记忆内容预览:")
                for i, memory in enumerate(context_memories[:2]):
                    logger.info(f"  - 记忆{i+1}: {memory}")
            
            memory_chunks = []
            
            # 按相关性排序并限制数量
            sorted_memories = sorted(context_memories, key=lambda x: x.get('relevance_score', 0.0), reverse=True)
            filtered_memories = []
            
            for memory in sorted_memories[:max_memories]:
                # 检查相关性阈值
                relevance_score = memory.get('relevance_score', 0.0)
                if relevance_score >= min_relevance:
                    # 检查长度限制
                    content = memory.get('content', '')
                    if len(content) <= max_length:
                        filtered_memories.append(memory)
                    else:
                        # 截断过长的记忆
                        memory['content'] = content[:max_length-3] + "..."
                        filtered_memories.append(memory)
            
            logger.info(f"🔧 过滤后记忆数量: {len(filtered_memories)} (原始: {len(context_memories)})")
            
            for memory in filtered_memories:
                # 构建元数据
                metadata = {
                    'importance_score': memory.get('importance_score', 0.0),
                    'created_at': memory.get('created_at', ''),
                    'memory_id': memory.get('chunk_id', '')
                }
                
                # 如果配置要求包含更多元数据
                if include_metadata:
                    metadata.update({
                        'relevance_score': memory.get('relevance_score', 0.0),
                        'content_type': memory.get('content_type', 'text'),
                        'user_query': memory.get('user_query', '')
                    })
                
                # 创建ContextChunk对象
                memory_chunk = ContextChunk(
                    content=memory['content'],
                    chunk_id=memory.get('chunk_id', ''),
                    content_type='memory',
                    relevance_score=memory.get('relevance_score', 0.0),
                    source='conversation_memory',
                    metadata=metadata
                )
                memory_chunks.append(memory_chunk)
            
            logger.info(f"构建历史记忆上下文完成，ContextChunk数量: {len(memory_chunks)}")
            return memory_chunks
            
        except Exception as e:
            logger.error(f"构建历史记忆上下文失败: {e}")
            return []
