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
    
    def process(self, query: str, reranked_results: List[Dict[str, Any]], query_type: str = None, **kwargs) -> UnifiedPipelineResult:
        # 只保留关键调试信息
        self.logger.info(f"🔍 UNIFIED_PIPELINE: 接收到 {len(reranked_results)} 个结果")
        """
        执行统一的Pipeline流程
        
        :param query: 查询文本
        :param reranked_results: 重排序后的结果（来自TextEngine）
        :param query_type: 查询类型（text/image/table/hybrid/smart）
        :param kwargs: 其他参数
        :return: 统一Pipeline结果
        """
        start_time = time.time()
        pipeline_metrics = {}
        
        try:
            self.logger.info(f"开始统一Pipeline处理，输入结果数量: {len(reranked_results)}")
            if query_type:
                self.logger.info(f"查询类型: {query_type}")
            
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
                filtered_sources = self._filter_sources(llm_answer, reranked_results, query, query_type)
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
    
    def _generate_llm_answer(self, query: str, context: str, **kwargs) -> str:
        """生成LLM答案"""
        try:
            start_time = time.time()
            
            # 直接调用LLM引擎，传递query和context
            # LLM引擎内部会处理prompt构建
            self.logger.info(f"开始调用LLM引擎，query长度: {len(query)}, context长度: {len(context)}")
            llm_response = self.llm_engine.generate_answer(query, context, **kwargs)
            self.logger.info(f"LLM引擎返回结果长度: {len(llm_response) if llm_response else 0}")
            
            llm_time = time.time() - start_time
            self.logger.info(f"LLM答案生成完成，耗时: {llm_time:.2f}秒")
            
            return llm_response
            
        except Exception as e:
            self.logger.error(f"LLM答案生成失败: {e}")
            self.logger.error(f"错误类型: {type(e)}")
            self.logger.error(f"错误详情: {str(e)}")
            return "抱歉，生成答案时发生错误。"
    
    def _filter_sources(self, llm_answer: str, results: List[Dict[str, Any]], query: str, query_type: str) -> List[Dict[str, Any]]:
        """过滤和排序来源"""
        if not results:
            return []
        
        try:
            # 首先提取完整的源信息，确保文档元数据不丢失
            enhanced_results = []
            for result in results:
                if isinstance(result, dict):
                    # 提取内容
                    content = result.get('content', result.get('page_content', ''))
                    metadata = result.get('metadata', {})
                    
                    # 使用_extract_complete_source_info提取完整信息
                    enhanced_result = self._extract_complete_source_info(result, content, metadata)
                    enhanced_results.append(enhanced_result)
                else:
                    enhanced_results.append(result)
            
            # 使用源过滤引擎
            if self.source_filter_engine:
                filtered_results = self.source_filter_engine.filter_sources(
                    llm_answer, enhanced_results, query, query_type
                )
                self.logger.info(f"源过滤完成，结果数量: {len(filtered_results)}")
                return filtered_results
            else:
                self.logger.warning("源过滤引擎不可用，返回增强后的结果")
                return enhanced_results[:self.max_context_results]
                
        except Exception as e:
            self.logger.error(f"源过滤失败: {e}")
            return results[:self.max_context_results]
    
    def _extract_complete_source_info(self, result: Dict[str, Any], content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        反向溯源：从doc对象中提取完整的源信息
        
        :param result: 搜索结果
        :param content: 内容
        :param metadata: 元数据
        :return: 完整的源信息
        """
        try:
            # 基础信息
            source_info = {
                'content': content,
                'metadata': metadata,
                'original_result': result
            }
            
            # 1. 从result本身提取字段
            for field in ['document_name', 'page_number', 'chunk_type', 'enhanced_description', 'image_path', 'caption']:
                if field in result:
                    source_info[field] = result[field]
            
            # 2. 从metadata中提取字段
            if metadata:
                for field in ['document_name', 'page_number', 'chunk_type', 'enhanced_description', 'image_path', 'img_caption']:
                    if field in metadata:
                        source_info[field] = metadata[field]
            
            # 3. 反向溯源：从doc对象中提取字段
            doc = result.get('doc')
            if doc and hasattr(doc, 'metadata') and doc.metadata:
                doc_metadata = doc.metadata
                
                # 提取文档基本信息
                for field in ['document_name', 'page_number', 'chunk_type', 'enhanced_description']:
                    if field not in source_info and field in doc_metadata:
                        source_info[field] = doc_metadata[field]
                
                # 提取图片相关字段（增强版）
                if 'image_path' not in source_info:
                    # 尝试多个可能的字段名
                    for path_field in ['image_path', 'image_file_path', 'file_path', 'path']:
                        if path_field in doc_metadata and doc_metadata[path_field]:
                            source_info['image_path'] = doc_metadata[path_field]
                            break
                
                if 'caption' not in source_info:
                    # 尝试多个可能的标题字段名
                    for caption_field in ['img_caption', 'caption', 'title', 'image_title', 'description']:
                        if caption_field in doc_metadata and doc_metadata[caption_field]:
                            caption_value = doc_metadata[caption_field]
                            # 确保caption是列表格式
                            if isinstance(caption_value, list):
                                source_info['caption'] = caption_value
                            else:
                                source_info['caption'] = [str(caption_value)]
                            break
                
                # 构建LLM上下文（修复版）
                llm_context_parts = []
                
                # 优先使用enhanced_description（图片的详细描述）
                enhanced_desc = doc_metadata.get('enhanced_description', '')
                if enhanced_desc:
                    llm_context_parts.append(enhanced_desc)
                
                # 如果没有enhanced_description，再使用page_content
                if hasattr(doc, 'page_content') and doc.page_content:
                    llm_context_parts.append(doc.page_content)
                
                # 最后才使用图片标题作为补充
                if not llm_context_parts:
                    img_caption = doc_metadata.get('img_caption', [])
                    if img_caption:
                        source_info['llm_context'] = ' '.join(img_caption)
                    else:
                        # 尝试其他可能的描述字段
                        for desc_field in ['description', 'title', 'image_title']:
                            if desc_field in doc_metadata and doc_metadata[desc_field]:
                                source_info['llm_context'] = str(doc_metadata[desc_field])
                                break
                        else:
                            source_info['llm_context'] = "无可用内容"
                else:
                    source_info['llm_context'] = "\n\n".join(llm_context_parts)
            
            # 4. 确保关键字段有默认值
            if 'document_name' not in source_info:
                source_info['document_name'] = '未知文档'
            if 'page_number' not in source_info:
                source_info['page_number'] = '未知页'
            if 'chunk_type' not in source_info:
                source_info['chunk_type'] = '未知类型'
            if 'image_path' not in source_info:
                source_info['image_path'] = ''
            if 'caption' not in source_info:
                source_info['caption'] = []
            if 'llm_context' not in source_info:
                source_info['llm_context'] = content or "无可用内容"
            
            # 5. 生成formatted_source字段（与v2_routes.py保持一致）
            if 'formatted_source' not in source_info:
                try:
                    from ..api.v2_routes import _format_source_display
                    source_info['formatted_source'] = _format_source_display(
                        source_info.get('document_name', '未知文档'),
                        source_info.get('llm_context', ''),
                        source_info.get('page_number', '未知页'),
                        source_info.get('chunk_type', '未知类型')
                    )
                except ImportError:
                    # 如果无法导入，生成简单的格式化字符串
                    source_info['formatted_source'] = f"{source_info.get('document_name', '未知文档')} - 第{source_info.get('page_number', '未知页')}页"
            
            return source_info
            
        except Exception as e:
            self.logger.warning(f"提取源信息失败: {e}")
            # 返回基础信息
            return {
                'content': content,
                'metadata': metadata,
                'original_result': result,
                'document_name': '未知文档',
                'page_number': '未知页',
                'chunk_type': '未知类型',
                'image_path': '',
                'caption': [],
                'llm_context': content or "无可用内容"
            }
    
    def _build_llm_prompt(self, query: str, context: str) -> str:
        """
        构建LLM提示词
        
        :param query: 用户查询
        :param context: 上下文内容
        :return: 构建好的提示词
        """
        try:
            # 构建提示词模板
            prompt_template = f"""
基于以下上下文信息，请回答用户的问题。请确保答案准确、完整，并基于提供的上下文内容。

用户问题：{query}

上下文信息：
{context}

请提供详细、准确的答案：
"""
            return prompt_template.strip()
            
        except Exception as e:
            self.logger.error(f"构建LLM提示词失败: {e}")
            # 返回简单的提示词
            return f"请基于以下信息回答问题：{query}\n\n信息：{context}"