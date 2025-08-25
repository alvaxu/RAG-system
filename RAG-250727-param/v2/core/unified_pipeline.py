'''
程序说明：
## 1. 统一Pipeline模块 - 基于老的成熟实现
## 2. 专门为TextEngine服务，其他引擎继续使用老Pipeline
## 3. 简化流程：只保留LLM生成和源过滤
## 4. 适配TextEngine的输出格式
## 5. 重构字段提取逻辑，使用明确的字段映射关系

## 主要功能：
- LLM生成答案：基于重排序后的文档生成答案
- 源过滤：基于LLM答案内容过滤最终源
- 明确的字段映射：避免猜测式字段提取
- 保持老的成熟逻辑，确保功能稳定
'''

import logging
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# 明确的字段映射表
FIELD_MAPPING = {
    # 通用字段
    'document_name': 'document_name',      # 文档名称
    'page_number': 'page_number',          # 页码
    'chunk_type': 'chunk_type',            # 内容类型
    
    # 图片字段
    'caption': 'img_caption',              # 图片标题（从img_caption获取）
    'footnote': 'img_footnote',            # 图片脚注（从img_footnote获取）
    'enhanced_description': 'enhanced_description',  # 增强描述
    'image_id': 'image_id',                # 图片ID
    'image_path': 'image_path',            # 图片路径
    'image_filename': 'image_filename',    # 图片文件名
    'image_type': 'image_type',            # 图片类型
    'extension': 'extension',              # 文件扩展名
    
    # 表格字段
    'table_id': 'table_id',                # 表格ID
    'table_type': 'table_type',            # 表格类型
    'table_title': 'table_title',          # 表格标题
    'table_summary': 'table_summary',      # 表格摘要
    'table_headers': 'table_headers',      # 表格表头
    'table_row_count': 'table_row_count',  # 表格行数
    'table_column_count': 'table_column_count',  # 表格列数
    'html_content': 'page_content',        # HTML格式内容
    'processed_content': 'processed_table_content',  # 语义化内容
    
    # 文本字段
    'content': 'page_content',             # 文本内容
    'content_preview': 'page_content',     # 内容预览
    'chunk_index': 'chunk_index'           # 分块索引
}

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
        
        # 字段映射配置
        self.field_mapping = FIELD_MAPPING
    
    def process(self, query: str, reranked_results: List[Dict[str, Any]], query_type: str = None, **kwargs) -> Dict[str, Any]:
        """
        执行统一的Pipeline流程 - 输出前端期望的完整格式
        
        :param query: 查询文本
        :param reranked_results: 重排序后的结果（来自TextEngine）
        :param query_type: 查询类型（text/image/table/hybrid/smart）
        :param kwargs: 其他参数
        :return: 前端期望的完整字典格式
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
            
            # 3. 提取来源信息（重构后的方法）
            extracted_sources = self._extract_sources(filtered_sources)
            
            # 4. 构建UnifiedPipelineResult对象
            self.logger.info(f"统一Pipeline处理完成，总耗时: {total_time:.2f}秒")
            self.logger.info(f"LLM答案长度: {len(llm_answer)}, 过滤后源数量: {len(filtered_sources)}")
            
            return UnifiedPipelineResult(
                llm_answer=llm_answer,
                filtered_sources=filtered_sources,
                pipeline_metrics=pipeline_metrics,
                success=True
            )
            
        except Exception as e:
            error_msg = f"统一Pipeline处理失败: {str(e)}"
            self.logger.error(error_msg)
            return UnifiedPipelineResult(
                llm_answer='抱歉，处理过程中出现错误。',
                filtered_sources=[],
                pipeline_metrics={'error': error_msg, 'processing_time': time.time() - start_time},
                success=False,
                error_message=error_msg
            )
    
    def _extract_sources(self, retrieved_docs: List[Any]) -> List[Dict[str, Any]]:
        """
        提取来源信息 - 智能处理三种不同引擎的输出格式
        
        :param retrieved_docs: 检索到的文档列表
        :return: 提取的源信息列表
        """
        sources = []
        
        for doc in retrieved_docs:
            # 跳过无效的文档
            if not doc:
                self.logger.warning("跳过空文档")
                continue
            
            # 智能识别并处理三种不同的数据格式
            doc_metadata = self._extract_metadata_from_doc(doc)
            if not doc_metadata:
                continue
            
            # 构建统一的源信息
            source_info = self._build_unified_source_info(doc, doc_metadata)
            if source_info:
                sources.append(source_info)
                self.logger.debug(f"添加有效源信息: {source_info.get('document_name', 'N/A')} - {source_info.get('chunk_type', 'N/A')}")
        
        self.logger.info(f"源信息提取完成，有效源数量: {len(sources)}")
        return sources
    
    def _extract_metadata_from_doc(self, doc: Any) -> Optional[Dict[str, Any]]:
        """
        从文档对象中提取metadata - 智能识别不同引擎的输出格式
        
        :param doc: 文档对象
        :return: 提取的metadata字典，如果失败返回None
        """
        try:
            # 格式1：TableEngine格式 - 处理后的字段
            # 检查是否包含表格相关字段，这些字段明确表示这是TableEngine的结果
            if isinstance(doc, dict) and any(key in doc for key in ['chunk_type', 'table_id', 'table_type', 'html_content']):
                self.logger.debug("检测到TableEngine格式（处理后字段）")
                
                # 优先使用metadata字段
                if 'metadata' in doc and doc['metadata']:
                    self.logger.debug("TableEngine格式：使用metadata字段")
                    return doc['metadata']
                
                # 如果没有metadata字段，从doc本身构建metadata
                metadata = {}
                # 提取通用字段
                for key in ['document_name', 'page_number', 'chunk_type', 'table_type', 'doc_id']:
                    if key in doc and doc[key]:
                        metadata[key] = doc[key]
                
                # 提取表格特定字段
                for key in ['table_id', 'table_title', 'html_content', 'content', 'page_content']:
                    if key in doc and doc[key]:
                        metadata[key] = doc[key]
                
                # 如果构建的metadata不为空，返回
                if metadata:
                    self.logger.debug(f"TableEngine格式：构建metadata成功，包含字段: {list(metadata.keys())}")
                    return metadata
                else:
                    self.logger.warning("TableEngine格式无法提取有效metadata")
                    return None
            
            # 格式2：TextEngine格式 - 包含 'doc' 键，但不包含表格相关字段
            elif isinstance(doc, dict) and 'doc' in doc and not any(key in doc for key in ['chunk_type', 'table_id', 'table_type', 'html_content']):
                self.logger.debug("检测到TextEngine格式（包含doc键，且不包含表格字段）")
                nested_doc = doc['doc']
                
                # 处理嵌套的doc键结构
                if isinstance(nested_doc, dict) and 'doc' in nested_doc:
                    # 如果nested_doc本身也包含doc键，继续深入
                    actual_doc = nested_doc['doc']
                    if hasattr(actual_doc, 'metadata') and actual_doc.metadata:
                        self.logger.debug("检测到嵌套TextEngine格式，成功提取metadata")
                        return actual_doc.metadata
                    else:
                        self.logger.warning("嵌套TextEngine格式中doc.doc.metadata为空")
                        return None
                else:
                    # 直接处理nested_doc
                    if hasattr(nested_doc, 'metadata') and nested_doc.metadata:
                        return nested_doc.metadata
                    else:
                        self.logger.warning("TextEngine格式中doc.metadata为空")
                        return None
            
            # 格式3：ImageEngine格式 - 直接展开的字段
            elif isinstance(doc, dict) and 'document_name' in doc:
                self.logger.debug("检测到ImageEngine格式（直接展开字段）")
                # 将整个doc作为metadata处理
                return doc
            
            # 格式4：标准Document对象
            elif hasattr(doc, 'metadata') and doc.metadata:
                self.logger.debug("检测到标准Document对象格式")
                return doc.metadata
            
            # 格式5：纯字典格式（可能是其他引擎的变体）
            elif isinstance(doc, dict):
                self.logger.debug("检测到纯字典格式")
                # 检查是否包含必要的字段
                if any(key in doc for key in ['document_name', 'chunk_type', 'page_content', 'content']):
                    return doc
                else:
                    self.logger.warning("纯字典格式缺少必要字段")
                    return None
            
            else:
                self.logger.warning(f"无法识别的文档格式: {type(doc)}")
                return None
                
        except Exception as e:
            self.logger.error(f"提取metadata时出错: {e}")
            return None
    
    def _build_unified_source_info(self, doc: Any, doc_metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        构建统一的源信息 - 输出前端期望的sources格式
        
        :param doc: 原始文档对象
        :param doc_metadata: 提取的metadata
        :return: 统一的源信息字典，如果失败返回None
        """
        try:
            # 构建前端期望的sources格式
            source_info = {
                'title': f"{doc_metadata.get('document_name', '未知文档')} - 第{doc_metadata.get('page_number', '未知页')}页",
                'document_name': doc_metadata.get('document_name', '未知文档'),
                'page_number': doc_metadata.get('page_number', '未知页'),
                'source_type': self._convert_chunk_type(doc_metadata.get('chunk_type', '未知类型')),
                'score': self._extract_score(doc),
                'content_preview': self._build_content_preview(doc, doc_metadata),
                'formatted_source': self._generate_formatted_source({
                    'document_name': doc_metadata.get('document_name', '未知文档'),
                    'page_number': doc_metadata.get('page_number', '未知页'),
                    'chunk_type': doc_metadata.get('chunk_type', '未知类型')
                })
            }
            
            # 验证源信息是否有效
            if source_info and len(source_info) > 0:
                return source_info
            else:
                self.logger.warning("构建的源信息为空")
                return None
                
        except Exception as e:
            self.logger.error(f"构建源信息时出错: {e}")
            return None
    

    
    def _extract_content_from_doc(self, doc: Any) -> str:
        """
        从文档对象中提取内容 - 简化版本，主要用于构建content_preview
        
        :param doc: 文档对象
        :return: 提取的内容字符串
        """
        try:
            # 优先级1：从Document对象获取page_content
            if hasattr(doc, 'page_content') and doc.page_content:
                return doc.page_content
            
            # 优先级2：从TextEngine格式的嵌套doc获取page_content
            elif isinstance(doc, dict) and 'doc' in doc:
                nested_doc = doc['doc']
                if hasattr(nested_doc, 'page_content') and nested_doc.page_content:
                    return nested_doc.page_content
            
            # 优先级3：从字典格式的page_content获取
            elif isinstance(doc, dict) and 'page_content' in doc:
                return doc['page_content']
            
            # 优先级4：从TextEngine的content字段获取
            elif isinstance(doc, dict) and 'content' in doc:
                return doc['content']
            
            return ""
            
        except Exception as e:
            self.logger.warning(f"提取文档内容时出错: {e}")
            return ""
    
    def _generate_formatted_source(self, source_info: Dict[str, Any]) -> str:
        """
        生成格式化的源信息显示
        
        :param source_info: 源信息字典
        :return: 格式化的源信息字符串
        """
        try:
            from ..api.v2_routes import _format_source_display
            return _format_source_display(
                source_info.get('document_name', '未知文档'),
                source_info.get('llm_context', ''),
                source_info.get('page_number', '未知页'),
                source_info.get('chunk_type', '未知类型')
            )
        except ImportError:
            # 如果无法导入，生成简单的格式化字符串
            return f"{source_info.get('document_name', '未知文档')} - 第{source_info.get('page_number', '未知页')}页"
    
    def _convert_chunk_type(self, chunk_type: str) -> str:
        """转换chunk_type为中文显示"""
        type_mapping = {
            'image': '图片',
            'image_text': '图片文本',
            'table': '表格',
            'text': '文本'
        }
        return type_mapping.get(chunk_type, chunk_type)
    
    def _extract_score(self, doc: Any) -> float:
        """提取文档的相关性分数"""
        try:
            if isinstance(doc, dict):
                return doc.get('score', doc.get('vector_score', 0.0))
            elif hasattr(doc, 'score'):
                return getattr(doc, 'score', 0.0)
            return 0.0
        except Exception:
            return 0.0
    
    def _build_content_preview(self, doc: Any, doc_metadata: Dict[str, Any]) -> str:
        """构建内容预览"""
        try:
            content = self._extract_content_from_doc(doc)
            if not content:
                content = doc_metadata.get('page_content', doc_metadata.get('content', ''))
            
            if content:
                return content[:200] + '...' if len(content) > 200 else content
            return ''
        except Exception:
            return ''
    
    def _generate_llm_answer(self, query: str, reranked_results: List[Dict[str, Any]]) -> str:
        """
        生成LLM答案
        
        :param query: 用户查询
        :param reranked_results: 重排序后的结果
        :return: LLM生成的答案
        """
        try:
            # 构建上下文
            context = self._build_context_for_llm(reranked_results)
            
            # 调用LLM引擎
            if hasattr(self.llm_engine, 'generate_answer'):
                answer = self.llm_engine.generate_answer(query, context)
            else:
                # 兼容旧的接口
                answer = self.llm_engine(query, context)
            
            self.logger.info(f"LLM引擎返回结果长度: {len(answer)}")
            return answer
            
        except Exception as e:
            self.logger.error(f"LLM答案生成失败: {e}")
            return f"抱歉，生成答案时出现错误: {str(e)}"
    
    def _build_context_for_llm(self, reranked_results: List[Dict[str, Any]]) -> str:
        """
        为LLM构建上下文
        
        :param reranked_results: 重排序后的结果
        :return: 构建的上下文字符串
        """
        context_parts = []
        
        for i, result in enumerate(reranked_results[:self.max_context_results]):
            if isinstance(result, dict) and 'doc' in result:
                doc = result['doc']
                
                # 🔑 修复：处理不同的doc格式
                if isinstance(doc, dict):
                    # doc是字典格式，直接提取content字段
                    content = doc.get('content', '')
                    if content:
                        context_parts.append(f"文档{i+1}: {content[:self.max_content_length]}")
                        
                elif hasattr(doc, 'page_content') and doc.page_content:
                    # doc是Document对象格式，使用原有逻辑
                    content = doc.page_content[:self.max_content_length]
                    context_parts.append(f"文档{i+1}: {content}")
        
        return "\n\n".join(context_parts)
    
    def _filter_sources(self, llm_answer: str, reranked_results: List[Dict[str, Any]], query: str, query_type: str = None) -> List[Dict[str, Any]]:
        """
        过滤源
        
        :param llm_answer: LLM生成的答案
        :param reranked_results: 重排序后的结果
        :param query: 原始查询
        :param query_type: 查询类型
        :return: 过滤后的结果
        """
        try:
            if hasattr(self.source_filter_engine, 'filter_sources'):
                filtered = self.source_filter_engine.filter_sources(
                    llm_answer, reranked_results, query, query_type
                )
                return filtered[:self.max_context_results]
            else:
                # 兼容旧的接口
                return reranked_results[:self.max_context_results]
            
        except Exception as e:
            self.logger.error(f"源过滤失败: {e}")
            return reranked_results[:self.max_context_results]
    
    def _build_frontend_format(self, query: str, llm_answer: str, sources: List[Dict[str, Any]], 
                              original_results: List[Dict[str, Any]], query_type: str = None, 
                              pipeline_metrics: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        构建前端期望的完整格式
        
        :param query: 查询文本
        :param llm_answer: LLM生成的答案
        :param sources: 提取的源信息
        :param original_results: 原始检索结果
        :param query_type: 查询类型
        :param pipeline_metrics: Pipeline处理指标
        :return: 前端期望的完整字典格式
        """
        try:
            # 构建基础响应
            response = {
                'success': True,
                'query': query,
                'query_type': query_type or 'text',
                'answer': llm_answer,
                'processing_time': pipeline_metrics.get('total_time', 0) if pipeline_metrics else 0,
                'timestamp': time.time(),
                'total_count': len(original_results)
            }
            
            # 添加sources
            response['sources'] = sources
            
            # 按类型分类原始结果
            image_results = []
            table_results = []
            text_results = []
            
            for result in original_results:
                chunk_type = self._get_chunk_type(result)
                
                if chunk_type == 'image':
                    image_result = self._build_image_result(result)
                    if image_result:
                        image_results.append(image_result)
                elif chunk_type == 'table':
                    table_result = self._build_table_result(result)
                    if table_result:
                        table_results.append(table_result)
                elif chunk_type == 'text':
                    text_result = self._build_text_result(result)
                    if text_result:
                        text_results.append(text_result)
            
            # 添加分类结果
            response['image_results'] = image_results
            response['table_results'] = table_results
            response['text_results'] = text_results
            
            # 添加Pipeline元数据
            if pipeline_metrics:
                response['pipeline_metrics'] = pipeline_metrics
            
            self.logger.info(f"前端格式构建完成，包含字段: {list(response.keys())}")
            self.logger.info(f"结果统计: sources={len(sources)}, images={len(image_results)}, tables={len(table_results)}, texts={len(text_results)}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"构建前端格式失败: {e}")
            return {
                'success': False,
                'error_message': f'构建前端格式失败: {str(e)}',
                'answer': '抱歉，格式化结果时出现错误。',
                'sources': [],
                'image_results': [],
                'table_results': [],
                'text_results': [],
                'processing_time': 0
            }
    
    def _get_chunk_type(self, result: Any) -> str:
        """获取结果的内容类型"""
        try:
            if isinstance(result, dict):
                if 'chunk_type' in result:
                    return result['chunk_type']
                elif 'doc' in result and hasattr(result['doc'], 'metadata'):
                    return result['doc'].metadata.get('chunk_type', 'text')
            elif hasattr(result, 'metadata'):
                return result.metadata.get('chunk_type', 'text')
            return 'text'
        except Exception:
            return 'text'
    
    def _build_image_result(self, result: Any) -> Optional[Dict[str, Any]]:
        """构建图片结果格式"""
        try:
            if isinstance(result, dict):
                return {
                    'id': result.get('image_id', result.get('doc_id', 'unknown')),
                    'image_path': result.get('image_path', ''),
                    'caption': result.get('caption', result.get('img_caption', '无标题')),
                    'document_name': result.get('document_name', '未知文档'),
                    'page_number': result.get('page_number', 'N/A'),
                    'score': result.get('score', result.get('vector_score', 0.0))
                }
            elif hasattr(result, 'metadata'):
                metadata = result.metadata
                return {
                    'id': getattr(result, 'doc_id', 'unknown'),
                    'image_path': metadata.get('image_path', ''),
                    'caption': metadata.get('img_caption', '无标题'),
                    'document_name': metadata.get('document_name', '未知文档'),
                    'page_number': metadata.get('page_number', 'N/A'),
                    'score': getattr(result, 'score', 0.0)
                }
            return None
        except Exception as e:
            self.logger.warning(f"构建图片结果失败: {e}")
            return None
    
    def _build_table_result(self, result: Any) -> Optional[Dict[str, Any]]:
        """构建表格结果格式"""
        try:
            if isinstance(result, dict):
                return {
                    'id': result.get('table_id', result.get('doc_id', 'unknown')),
                    'table_html': result.get('html_content', result.get('table_html', '')),
                    'table_content': result.get('processed_content', result.get('table_content', '')),
                    'document_name': result.get('document_name', '未知文档'),
                    'page_number': result.get('page_number', 'N/A'),
                    'score': result.get('score', result.get('vector_score', 0.0))
                }
            elif hasattr(result, 'metadata'):
                metadata = result.metadata
                return {
                    'id': getattr(result, 'doc_id', 'unknown'),
                    'table_html': getattr(result, 'page_content', ''),
                    'table_content': metadata.get('processed_table_content', ''),
                    'document_name': metadata.get('document_name', '未知文档'),
                    'page_number': metadata.get('page_number', 'N/A'),
                    'score': getattr(result, 'score', 0.0)
                }
            return None
        except Exception as e:
            self.logger.warning(f"构建表格结果失败: {e}")
            return None
    
    def _build_text_result(self, result: Any) -> Optional[Dict[str, Any]]:
        """构建文本结果格式"""
        try:
            if isinstance(result, dict):
                return {
                    'id': result.get('doc_id', 'unknown'),
                    'content': result.get('content', ''),
                    'document_name': result.get('document_name', '未知文档'),
                    'page_number': result.get('page_number', 'N/A'),
                    'score': result.get('score', result.get('vector_score', 0.0))
                }
            elif hasattr(result, 'metadata'):
                metadata = result.metadata
                return {
                    'id': getattr(result, 'doc_id', 'unknown'),
                    'content': getattr(result, 'page_content', ''),
                    'document_name': metadata.get('document_name', '未知文档'),
                    'page_number': metadata.get('page_number', 'N/A'),
                    'score': getattr(result, 'score', 0.0)
                }
            return None
        except Exception as e:
            self.logger.warning(f"构建文本结果失败: {e}")
            return None