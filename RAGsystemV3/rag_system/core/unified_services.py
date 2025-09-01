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
from .exceptions import (
    ServiceInitializationError,
    RetrievalError,
    RerankingError,
    LLMServiceError,
    ContentProcessingError
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
            self.retrieval_service = RetrievalEngine(config_integration, None)  # 暂时传入None，后续调整
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
            
            # 根据内容类型进行检索
            all_results = []
            
            if 'text' in content_types:
                text_results = self.retrieval_service.retrieve_texts(query, max_results)
                all_results.extend(text_results)
            
            if 'image' in content_types:
                image_results = self.retrieval_service.retrieve_images(query, max_results)
                all_results.extend(image_results)
            
            if 'table' in content_types:
                table_results = self.retrieval_service.retrieve_tables(query, max_results)
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
    
    async def generate_answer(self, query: str, results: List[Any]) -> str:
        """
        LLM服务 - 复用+适配
        
        :param query: 查询文本
        :param results: 检索结果列表
        :return: 生成的答案
        """
        try:
            if not results:
                return "抱歉，没有找到相关的信息来回答您的问题。"
            
            logger.info("开始生成LLM答案")
            
            # 构建统一上下文
            context = self._build_unified_context(results)
            
            # 构建统一Prompt
            prompt = self._build_unified_prompt(query, context)
            
            # 调用LLM服务
            answer = self.llm_service.generate_answer(query, context)
            
            logger.info(f"LLM答案生成完成，长度: {len(answer)} 字符")
            return answer
            
        except LLMServiceError as e:
            logger.error(f"LLM答案生成失败: {e}")
            return self._generate_fallback_answer(query, results)
        except Exception as e:
            logger.error(f"LLM答案生成失败（未知错误）: {e}")
            return self._generate_fallback_answer(query, results)
    
    def _build_unified_context(self, results: List[Any]) -> str:
        """
        构建统一上下文
        
        :param results: 结果列表
        :return: 格式化的上下文
        """
        try:
            if not results:
                return ""
            
            # 获取配置的最大上下文长度
            max_context_length = self.config.get_rag_config('query_processing.max_context_length', 4000)
            
            # 按分数排序，选择最相关的内容
            sorted_results = sorted(results, key=lambda x: x.get('score', 0.0), reverse=True)
            
            context_parts = []
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
                
                context_parts.append(content)
                current_length += len(content)
                
                # 如果已经达到目标长度，停止添加
                if current_length >= max_context_length:
                    break
            
            unified_context = "\n\n".join(context_parts)
            logger.info(f"统一上下文构建完成，长度: {len(unified_context)} 字符")
            
            return unified_context
            
        except Exception as e:
            logger.error(f"构建统一上下文失败: {e}")
            # 返回前几个结果的简单拼接
            return "\n\n".join([self._extract_content(r) for r in results[:3] if self._extract_content(r)])
    
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
                'fallback_strategies'
            ]
        }
