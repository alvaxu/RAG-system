'''
程序说明：
## 1. 统一Pipeline模块 - 基于老的成熟实现
## 2. 专门为TextEngine服务，其他引擎继续使用老Pipeline
## 3. 简化流程：只保留LLM生成和源过滤
## 4. 适配TextEngine的输出格式

## 主要功能：
- LLM生成答案：基于重排序后的文档生成答案
- 源过滤：基于LLM答案内容过滤最终源
- 保持老的成熟逻辑，确保功能稳定
'''

import logging
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class UnifiedPipelineResult:
    """统一Pipeline结果"""
    llm_answer: str
    filtered_sources: List[Dict[str, Any]]
    pipeline_metrics: Dict[str, Any]
    success: bool
    error_message: str = ""

class UnifiedPipeline:
    """统一Pipeline - 专门为TextEngine服务，只保留LLM生成和源过滤"""
    
    def __init__(self, config: Dict[str, Any], llm_engine, source_filter_engine):
        """
        初始化统一Pipeline
        
        :param config: Pipeline配置
        :param llm_engine: LLM引擎
        :param source_filter_engine: 源过滤引擎
        """
        self.config = config
        self.llm_engine = llm_engine
        self.source_filter_engine = source_filter_engine
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("统一Pipeline初始化完成")
        
        # 配置参数
        self.enable_llm_generation = config.get('enable_llm_generation', True)
        self.enable_source_filtering = config.get('enable_source_filtering', True)
        self.max_context_results = config.get('max_context_results', 10)  # 改进：从5增加到10
        self.max_content_length = config.get('max_content_length', 1000)  # 改进：从500增加到1000
    
    def process(self, query: str, reranked_results: List[Dict[str, Any]], **kwargs) -> UnifiedPipelineResult:
        """
        执行统一的Pipeline流程
        
        :param query: 查询文本
        :param reranked_results: 重排序后的结果（来自TextEngine）
        :param kwargs: 其他参数
        :return: 统一Pipeline结果
        """
        start_time = time.time()
        pipeline_metrics = {}
        
        try:
            self.logger.info(f"开始统一Pipeline处理，输入结果数量: {len(reranked_results)}")
            
            # 1. LLM生成答案（如果启用）
            llm_answer = ""
            if self.enable_llm_generation and self.llm_engine:
                llm_start = time.time()
                llm_answer = self._generate_llm_answer(query, reranked_results)
                llm_time = time.time() - llm_start
                pipeline_metrics['llm_time'] = llm_time
                pipeline_metrics['llm_answer_length'] = len(llm_answer)
                self.logger.info(f"LLM答案生成完成，耗时: {llm_time:.2f}秒")
            else:
                self.logger.warning("LLM生成未启用或引擎不可用")
                llm_answer = "抱歉，LLM生成功能当前不可用。"
            
            # 2. 源过滤（如果启用）
            filtered_sources = reranked_results
            if self.enable_source_filtering and self.source_filter_engine and llm_answer:
                source_filter_start = time.time()
                self.logger.info(f"开始源过滤，输入结果数量: {len(reranked_results)}")
                filtered_sources = self._filter_sources(llm_answer, reranked_results, query)
                source_filter_time = time.time() - source_filter_start
                pipeline_metrics['source_filter_time'] = source_filter_time
                pipeline_metrics['source_filter_count'] = len(filtered_sources)
                self.logger.info(f"源过滤完成，耗时: {source_filter_time:.2f}秒，过滤后数量: {len(filtered_sources)}")
            else:
                self.logger.warning("源过滤未启用或引擎不可用，使用原始结果")
                filtered_sources = reranked_results
            
            # 计算总耗时
            total_time = time.time() - start_time
            pipeline_metrics['total_time'] = total_time
            pipeline_metrics['input_count'] = len(reranked_results)
            pipeline_metrics['output_count'] = len(filtered_sources)
            
            self.logger.info(f"统一Pipeline处理完成，总耗时: {total_time:.2f}秒")
            
            return UnifiedPipelineResult(
                llm_answer=llm_answer,
                filtered_sources=filtered_sources,
                pipeline_metrics=pipeline_metrics,
                success=True
            )
            
        except Exception as e:
            self.logger.error(f"统一Pipeline处理过程中发生错误: {str(e)}")
            # 返回原始结果
            return UnifiedPipelineResult(
                llm_answer="抱歉，Pipeline处理时发生错误。",
                filtered_sources=reranked_results,
                pipeline_metrics={'error': str(e)},
                success=False,
                error_message=str(e)
            )
    
    def _generate_llm_answer(self, query: str, results: List[Dict[str, Any]]) -> str:
        """
        生成LLM答案 - 基于老的实现，但进行了改进
        
        :param query: 查询文本
        :param results: 重排序后的结果
        :return: 生成的答案
        """
        try:
            if not results:
                return "抱歉，我没有找到相关的上下文信息来回答您的问题。"
            
            # 构建上下文 - 改进：增加数量和长度限制
            context_parts = []
            for result in results[:self.max_context_results]:  # 改进：从5增加到10
                if isinstance(result, dict):
                    content = result.get('content', '')
                    if content:
                        # 改进：从500增加到1000字符
                        context_parts.append(content[:self.max_content_length])
                else:
                    context_parts.append(str(result)[:self.max_content_length])
            
            context = "\n\n".join(context_parts)
            
            # 生成答案
            answer = self.llm_engine.generate_answer(query, context)
            
            return answer
            
        except Exception as e:
            self.logger.error(f"LLM答案生成失败: {str(e)}")
            # 改进：提供更友好的错误信息
            return "抱歉，生成答案时发生错误。请稍后重试。"
    
    def _filter_sources(self, llm_answer: str, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        过滤源 - 基于老的实现，保持原有逻辑
        
        :param llm_answer: LLM生成的答案
        :param results: 重排序后的结果
        :param query: 原始查询
        :return: 过滤后的源
        """
        try:
            if not results:
                return results
            
            # 准备源数据 - 确保保留所有原始信息
            sources = []
            for result in results:
                if isinstance(result, dict):
                    content = result.get('content', '')
                    metadata = result.get('metadata', {})
                    
                    # 确保保留所有必要的文档信息
                    source_info = {
                        'content': content,
                        'metadata': metadata,
                        'original_result': result
                    }
                    
                    # 如果result本身有document_name等字段，确保保留
                    if 'document_name' in result:
                        source_info['document_name'] = result['document_name']
                    if 'page_number' in result:
                        source_info['page_number'] = result['page_number']
                    if 'page_content' in result:
                        source_info['page_content'] = result['page_content']
                    if 'chunk_type' in result:
                        source_info['chunk_type'] = result['chunk_type']
                    
                    # 如果metadata中有这些字段，也保留
                    if metadata:
                        if 'document_name' in metadata:
                            source_info['document_name'] = metadata['document_name']
                        if 'page_number' in metadata:
                            source_info['page_number'] = metadata['page_number']
                        if 'page_content' in metadata:
                            source_info['page_content'] = metadata['page_content']
                        if 'chunk_type' in metadata:
                            source_info['chunk_type'] = metadata['chunk_type']
                    
                    sources.append(source_info)
                else:
                    sources.append({
                        'content': str(result),
                        'metadata': {},
                        'original_result': result
                    })
            
            # 执行源过滤
            filtered_sources = self.source_filter_engine.filter_sources(llm_answer, sources, query)
            
            # 恢复原始结果格式 - 确保包含所有必要的文档信息
            filtered_results = []
            for source in filtered_sources:
                original_result = source.get('original_result', source)
                if isinstance(original_result, dict):
                    # 添加相关性分数
                    original_result['source_relevance_score'] = source.get('relevance_score', 0.0)
                    
                    # 确保包含必要字段
                    if 'content' not in original_result:
                        original_result['content'] = source.get('content', '')
                    if 'metadata' not in original_result:
                        original_result['metadata'] = source.get('metadata', {})
                    
                    # 确保包含文档信息字段
                    if 'document_name' not in original_result and 'document_name' in source:
                        original_result['document_name'] = source['document_name']
                    if 'page_number' not in original_result and 'page_number' in source:
                        original_result['page_number'] = source['page_number']
                    if 'page_content' not in original_result and 'page_content' in source:
                        original_result['page_content'] = source['page_content']
                    if 'chunk_type' not in original_result and 'chunk_type' in source:
                        original_result['chunk_type'] = source['chunk_type']
                    
                    # 确保metadata中包含文档信息
                    if 'metadata' in original_result and isinstance(original_result['metadata'], dict):
                        if 'document_name' not in original_result['metadata'] and 'document_name' in source:
                            original_result['metadata']['document_name'] = source['document_name']
                        if 'page_number' not in original_result['metadata'] and 'page_number' in source:
                            original_result['metadata']['page_number'] = source['page_number']
                        if 'page_content' not in original_result['metadata'] and 'page_content' in source:
                            original_result['metadata']['page_content'] = source['page_content']
                        if 'chunk_type' not in original_result['metadata'] and 'chunk_type' in source:
                            original_result['metadata']['chunk_type'] = source['chunk_type']
                
                filtered_results.append(original_result)
            
            self.logger.info(f"源过滤完成，输入 {len(results)} 个结果，输出 {len(filtered_results)} 个结果")
            return filtered_results
            
        except Exception as e:
            self.logger.error(f"源过滤失败: {str(e)}")
            # 改进：失败时返回原始结果，而不是空列表
            return results
