'''
程序说明：
## 1. 混合查询引擎（简化版）- 支持跨类型内容检索
## 2. 智能路由：根据查询类型选择单个引擎或混合引擎
## 3. 混合模式：融合三个引擎的recall结果，进行混合reranking，调用新Pipeline
## 4. 统一流程：所有引擎都使用新Pipeline（LLM + 溯源）
## 5. 大幅简化：从2000+行代码减少到300-500行
'''

import logging
import time
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base_engine import BaseEngine, QueryResult, QueryType, EngineStatus, EngineConfig
from .image_engine import ImageEngine
from .text_engine import TextEngine
from .table_engine import TableEngine
from .unified_pipeline import UnifiedPipeline
from .reranking_services.hybrid_reranking_service import HybridRerankingService
try:
    from ..config.v2_config import HybridEngineConfigV2, V2ConfigManager
except ImportError:
    from config.v2_config import HybridEngineConfigV2, V2ConfigManager


@dataclass
class HybridQueryResult:
    """混合查询结果数据类"""
    combined_results: List[Any]
    query_intent: str
    processing_details: Dict[str, Any]


class HybridEngine(BaseEngine):
    """
    混合查询引擎（简化版）
    
    核心功能：
    1. 智能路由：根据查询类型选择单个引擎或混合引擎
    2. 混合模式：融合三个引擎的recall结果，进行混合reranking，调用新Pipeline
    3. 统一流程：所有引擎都使用新Pipeline（LLM + 溯源）
    """
    
    def __init__(self, config: HybridEngineConfigV2, 
                  image_engine: ImageEngine = None,
                  text_engine: TextEngine = None,
                  table_engine: TableEngine = None,
                  reranking_engine: HybridRerankingService = None,
                  config_manager: V2ConfigManager = None,
                  memory_manager = None,
                  llm_engine = None,
                  smart_filter_engine = None,
                  source_filter_engine = None):
        """
        初始化混合查询引擎
        
        :param config: 混合引擎配置
        :param image_engine: 图片引擎实例
        :param text_engine: 文本引擎实例
        :param table_engine: 表格引擎实例
        :param reranking_engine: 重排序引擎实例
        :param config_manager: 配置管理器实例
        :param memory_manager: 记忆管理器实例
        """
        # 转换为基础配置格式
        base_config = EngineConfig(
            enabled=getattr(config, 'enabled', True),
            name=getattr(config, 'name', 'HybridEngine'),
            version=getattr(config, 'version', '2.0.0'),
            debug=getattr(config, 'debug', False),
            max_results=getattr(config, 'max_results', 10),
            timeout=getattr(config, 'timeout', 30),
            cache_enabled=getattr(config, 'cache_enabled', False),
            cache_ttl=getattr(config, 'cache_ttl', 300)
        )
        
        super().__init__(base_config)
        
        # 保存混合引擎特定配置
        self.hybrid_config = config
        
        # 基础子引擎实例
        self.image_engine = image_engine
        self.text_engine = text_engine
        self.table_engine = table_engine
        
        # 重排序引擎实例
        self.reranking_engine = reranking_engine
        
        # 配置管理器
        self.config_manager = config_manager
        
        # 记忆管理器
        self.memory_manager = memory_manager
        
        # 优化引擎实例
        self.llm_engine = llm_engine
        self.smart_filter_engine = smart_filter_engine
        self.source_filter_engine = source_filter_engine
        
        # 验证子引擎连接状态
        self._validate_engine_connections()
        
        self.logger.info(f"混合查询引擎（简化版）初始化完成: {self.name}")
    
    def _validate_engine_connections(self):
        """验证子引擎连接状态"""
        # 验证基础引擎
        if not self.image_engine:
            self.logger.warning("图片引擎未连接")
        if not self.text_engine:
            self.logger.warning("文本引擎未连接")
        if not self.table_engine:
            self.logger.warning("表格引擎未连接")
        
        # 验证重排序引擎
        if not self.reranking_engine:
            self.logger.warning("重排序引擎未连接")
        
        self.logger.info("子引擎连接状态验证完成")
    
    def process_query(self, query: str, **kwargs) -> QueryResult:
        """
        处理查询请求
        
        :param query: 查询文本
        :param kwargs: 其他参数
        :return: 查询结果
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"开始处理查询: {query}")
            
            # 1. 确定查询类型和路由策略
            query_type = kwargs.get('query_type')
            if query_type:
                self.logger.info(f"检测到明确的查询类型: {query_type}")
                
                # 修复：正确处理QueryType枚举和字符串类型的比较
                if isinstance(query_type, QueryType):
                    # 枚举类型：直接比较
                    if query_type == QueryType.TEXT:
                        self.logger.info("单类型查询 TEXT，直接调用文本引擎完整流程")
                        # 直接调用文本引擎，不经过智能引擎模式
                        if self.text_engine:
                            # 确保传递LLM引擎和源过滤引擎
                            kwargs_with_engines = kwargs.copy()
                            if self.llm_engine:
                                kwargs_with_engines['llm_engine'] = self.llm_engine
                                self.logger.info("传递LLM引擎到文本引擎")
                            if self.source_filter_engine:
                                kwargs_with_engines['source_filter_engine'] = self.source_filter_engine
                                self.logger.info("传递源过滤引擎到文本引擎")
                            
                            result = self.text_engine.process_query(query, **kwargs_with_engines)
                            # 构建最终结果
                            processing_time = time.time() - start_time
                            final_result = QueryResult(
                                success=True,
                                query=query,
                                query_type=QueryType.TEXT,
                                results=result.results if hasattr(result, 'results') else result,
                                total_count=len(result.results) if hasattr(result, 'results') else len(result),
                                processing_time=processing_time,
                                engine_name=f"HybridEngine->TextEngine",
                                metadata={
                                    'query_intent': '基于查询类型 TEXT 的检索',
                                    'engines_used': ['text'],
                                    'total_results': len(result.results) if hasattr(result, 'results') else len(result),
                                    'optimization_enabled': True,
                                    'optimization_details': result.metadata if hasattr(result, 'metadata') else {},
                                    'llm_answer': result.metadata.get('llm_answer', '') if hasattr(result, 'metadata') else '',
                                    'post_processing_metrics': {},
                                    'engine_mode': 'direct_text_engine',
                                    'single_engine_result': True
                                }
                            )
                            self.logger.info(f"文本引擎查询处理完成，结果数量: {final_result.total_count}")
                            return final_result
                        else:
                            raise ValueError("文本引擎不可用")
                    elif query_type == QueryType.IMAGE:
                        self.logger.info("单类型查询 IMAGE，直接调用图片引擎完整流程")
                        if self.image_engine:
                            # 确保传递LLM引擎和源过滤引擎
                            kwargs_with_engines = kwargs.copy()
                            if self.llm_engine:
                                kwargs_with_engines['llm_engine'] = self.llm_engine
                                self.logger.info("传递LLM引擎到图片引擎")
                            if self.source_filter_engine:
                                kwargs_with_engines['source_filter_engine'] = self.source_filter_engine
                                self.logger.info("传递源过滤引擎到图片引擎")
                            
                            result = self.image_engine.process_query(query, **kwargs_with_engines)
                            processing_time = time.time() - start_time
                            final_result = QueryResult(
                                success=True,
                                query=query,
                                query_type=QueryType.IMAGE,
                                results=result.results if hasattr(result, 'results') else result,
                                total_count=len(result.results) if hasattr(result, 'results') else len(result),
                                processing_time=processing_time,
                                engine_name=f"HybridEngine->ImageEngine",
                                metadata={
                                    'query_intent': '基于查询类型 IMAGE 的检索',
                                    'engines_used': ['image'],
                                    'total_results': len(result.results) if hasattr(result, 'results') else len(result),
                                    'optimization_enabled': True,
                                    'optimization_details': result.metadata if hasattr(result, 'metadata') else {},
                                    'llm_answer': result.metadata.get('llm_answer', '') if hasattr(result, 'metadata') else '',
                                    'post_processing_metrics': {},
                                    'engine_mode': 'direct_image_engine',
                                    'single_engine_result': True
                                }
                            )
                            self.logger.info(f"图片引擎查询处理完成，结果数量: {final_result.total_count}")
                            return final_result
                        else:
                            raise ValueError("图片引擎不可用")
                    elif query_type == QueryType.TABLE:
                        self.logger.info("单类型查询 TABLE，直接调用表格引擎完整流程")
                        if self.table_engine:
                            # 确保传递LLM引擎和源过滤引擎
                            kwargs_with_engines = kwargs.copy()
                            if self.llm_engine:
                                kwargs_with_engines['llm_engine'] = self.llm_engine
                                self.logger.info("传递LLM引擎到表格引擎")
                            if self.source_filter_engine:
                                kwargs_with_engines['source_filter_engine'] = self.source_filter_engine
                                self.logger.info("传递源过滤引擎到表格引擎")
                            
                            result = self.table_engine.process_query(query, **kwargs_with_engines)
                            processing_time = time.time() - start_time
                            final_result = QueryResult(
                                success=True,
                                query=query,
                                query_type=QueryType.TABLE,
                                results=result.results if hasattr(result, 'results') else result,
                                total_count=len(result.results) if hasattr(result, 'results') else len(result),
                                processing_time=processing_time,
                                engine_name=f"HybridEngine->TableEngine",
                                metadata={
                                    'query_intent': '基于查询类型 TABLE 的检索',
                                    'engines_used': ['table'],
                                    'total_results': len(result.results) if hasattr(result, 'results') else len(result),
                                    'optimization_enabled': True,
                                    'optimization_details': result.metadata if hasattr(result, 'metadata') else {},
                                    'llm_answer': result.metadata.get('llm_answer', '') if hasattr(result, 'metadata') else '',
                                    'post_processing_metrics': {},
                                    'engine_mode': 'direct_table_engine',
                                    'single_engine_result': True
                                }
                            )
                            self.logger.info(f"表格引擎查询处理完成，结果数量: {final_result.total_count}")
                            return final_result
                        else:
                            raise ValueError("表格引擎不可用")
                    elif query_type == QueryType.HYBRID:
                        self.logger.info("混合查询，混合引擎模式 - 同时执行多个引擎并融合")
                        return self._handle_hybrid_engine_query(query, start_time, **kwargs)
                    else:
                        self.logger.info(f"未知枚举查询类型 {query_type}，默认使用混合引擎模式")
                        return self._handle_hybrid_engine_query(query, start_time, **kwargs)
                else:
                    # 字符串类型：转换为小写比较
                    query_type_str = str(query_type).lower()
                    self.logger.info(f"字符串查询类型: {query_type_str}")
                    
                    if query_type_str in ['text', 'image', 'table']:
                        self.logger.info(f"单类型查询 {query_type_str}，直接调用对应引擎完整流程")
                        # 直接调用对应引擎，不经过智能引擎模式
                        if query_type_str == 'text' and self.text_engine:
                            # 确保传递LLM引擎和源过滤引擎
                            kwargs_with_engines = kwargs.copy()
                            if self.llm_engine:
                                kwargs_with_engines['llm_engine'] = self.llm_engine
                                self.logger.info("传递LLM引擎到文本引擎")
                            if self.source_filter_engine:
                                kwargs_with_engines['source_filter_engine'] = self.source_filter_engine
                                self.logger.info("传递源过滤引擎到文本引擎")
                            
                            result = self.text_engine.process_query(query, **kwargs_with_engines)
                            engine_name = 'text'
                        elif query_type_str == 'image' and self.image_engine:
                            # 确保传递LLM引擎和源过滤引擎
                            kwargs_with_engines = kwargs.copy()
                            if self.llm_engine:
                                kwargs_with_engines['llm_engine'] = self.llm_engine
                                self.logger.info("传递LLM引擎到图片引擎")
                            if self.source_filter_engine:
                                kwargs_with_engines['source_filter_engine'] = self.source_filter_engine
                                self.logger.info("传递源过滤引擎到图片引擎")
                            
                            result = self.image_engine.process_query(query, **kwargs_with_engines)
                            engine_name = 'image'
                        elif query_type_str == 'table' and self.table_engine:
                            # 确保传递LLM引擎和源过滤引擎
                            kwargs_with_engines = kwargs.copy()
                            if self.llm_engine:
                                kwargs_with_engines['llm_engine'] = self.llm_engine
                                self.logger.info("传递LLM引擎到表格引擎")
                            if self.source_filter_engine:
                                kwargs_with_engines['source_filter_engine'] = self.source_filter_engine
                                self.logger.info("传递源过滤引擎到表格引擎")
                            
                            result = self.table_engine.process_query(query, **kwargs_with_engines)
                            engine_name = 'table'
                        else:
                            raise ValueError(f"查询类型 {query_type_str} 对应的引擎不可用")
                        
                        # 构建最终结果
                        processing_time = time.time() - start_time
                        final_result = QueryResult(
                            success=True,
                            query=query,
                            query_type=getattr(QueryType, query_type_str.upper()),
                            results=result.results if hasattr(result, 'results') else result,
                            total_count=len(result.results) if hasattr(result, 'results') else len(result),
                            processing_time=processing_time,
                            engine_name=f"HybridEngine->{engine_name.capitalize()}Engine",
                            metadata={
                                'query_intent': f'基于查询类型 {query_type_str} 的检索',
                                'engines_used': [engine_name],
                                'total_results': len(result.results) if hasattr(result, 'results') else len(result),
                                'optimization_enabled': True,
                                'optimization_details': result.metadata if hasattr(result, 'metadata') else {},
                                'llm_answer': result.metadata.get('llm_answer', '') if hasattr(result, 'metadata') else '',
                                'post_processing_metrics': {},
                                'engine_mode': f'direct_{engine_name}_engine',
                                'single_engine_result': True
                            }
                        )
                        self.logger.info(f"{engine_name}引擎查询处理完成，结果数量: {final_result.total_count}")
                        return final_result
                    elif query_type_str == 'hybrid':
                        self.logger.info("混合查询，混合引擎模式 - 同时执行多个引擎并融合")
                        return self._handle_hybrid_engine_query(query, start_time, **kwargs)
                    else:
                        self.logger.info(f"未知字符串查询类型 {query_type_str}，默认使用混合引擎模式")
                        return self._handle_hybrid_engine_query(query, start_time, **kwargs)
            else:
                # 没有明确类型：智能引擎模式 - 通过语义判断选择引擎
                self.logger.info("未指定查询类型，智能引擎模式 - 通过语义判断选择引擎")
                return self._handle_smart_engine_query(query, start_time, **kwargs)
                
        except Exception as e:
            self.logger.error(f"查询处理过程中发生错误: {str(e)}")
            processing_time = time.time() - start_time
            
            return QueryResult(
                success=False,
                query=query,
                query_type=QueryType.HYBRID,
                results=[],
                total_count=0,
                processing_time=processing_time,
                engine_name=self.name,
                metadata={},
                error_message=str(e)
            )
    
    def _handle_single_engine_query(self, query: str, query_type: str, start_time: float, **kwargs) -> QueryResult:
        """
        智能引擎模式：处理单类型查询 - 选择单个引擎执行
        
        :param query: 查询文本
        :param query_type: 查询类型
        :param start_time: 开始时间
        :param kwargs: 其他参数
        :return: 查询结果
        """
        try:
            # 选择对应引擎
            engine = None
            if query_type == 'text' and self.text_engine:
                engine = self.text_engine
                engine_name = 'text'
            elif query_type == 'image' and self.image_engine:
                engine = self.image_engine
                engine_name = 'image'
            elif query_type == 'table' and self.table_engine:
                engine = self.table_engine
                engine_name = 'table'
            else:
                raise ValueError(f"查询类型 {query_type} 对应的引擎不可用")
            
            self.logger.info(f"智能引擎模式：路由到 {engine_name} 引擎")
            
            # 执行查询 - 直接调用单引擎的完整流程
            result = engine.process_query(query, **kwargs)
            
            # 构建最终结果 - 直接返回单引擎的结果，不做额外处理
            processing_time = time.time() - start_time
            final_result = QueryResult(
                success=True,
                query=query,
                query_type=getattr(QueryType, query_type.upper()),
                results=result.results if hasattr(result, 'results') else result,
                total_count=len(result.results) if hasattr(result, 'results') else len(result),
                processing_time=processing_time,
                engine_name=f"HybridEngine[智能模式]->{engine_name}",
                metadata={
                    'query_intent': f"基于查询类型 {query_type} 的检索",
                    'engines_used': [engine_name],
                    'total_results': len(result.results) if hasattr(result, 'results') else len(result),
                    'optimization_enabled': True,
                    'optimization_details': result.metadata if hasattr(result, 'metadata') else {},
                    'llm_answer': result.metadata.get('llm_answer', '') if hasattr(result, 'metadata') else '',
                    'post_processing_metrics': {},
                    'engine_mode': 'smart_single_engine',
                    'single_engine_result': True  # 标记这是单引擎直接结果
                }
            )
            
            self.logger.info(f"智能引擎模式 {query_type} 查询处理完成，结果数量: {final_result.total_count}")
            return final_result
            
        except Exception as e:
            self.logger.error(f"智能引擎模式查询处理失败: {str(e)}")
            raise
    
    def _handle_smart_engine_query(self, query: str, start_time: float, **kwargs) -> QueryResult:
        """
        智能引擎模式：通过语义判断选择单个引擎
        
        :param query: 查询文本
        :param start_time: 开始时间
        :param kwargs: 其他参数
        :return: 查询结果
        """
        try:
            self.logger.info("开始智能引擎模式：通过语义判断选择引擎")
            
            # 简单的关键词判断逻辑（可以后续优化为更智能的语义分析）
            query_lower = query.lower()
            
            # 图片相关关键词
            image_keywords = ['图片', '照片', '图像', '图表', '截图', 'image', 'photo', 'picture', 'chart', 'graph']
            # 表格相关关键词
            table_keywords = ['表格', '数据', '统计', '数字', 'table', 'data', 'statistics', 'number', 'figure']
            # 文本相关关键词
            text_keywords = ['文档', '报告', '文章', '内容', '文本', 'document', 'report', 'article', 'content', 'text']
            
            # 计算匹配度
            image_score = sum(1 for keyword in image_keywords if keyword in query_lower)
            table_score = sum(1 for keyword in table_keywords if keyword in query_lower)
            text_score = sum(1 for keyword in text_keywords if keyword in query_lower)
            
            # 选择得分最高的引擎类型
            if image_score > table_score and image_score > text_score and self.image_engine:
                selected_type = 'image'
                self.logger.info(f"智能判断选择图片引擎，得分: {image_score}")
            elif table_score > text_score and self.table_engine:
                selected_type = 'table'
                self.logger.info(f"智能判断选择表格引擎，得分: {table_score}")
            elif self.text_engine:
                selected_type = 'text'
                self.logger.info(f"智能判断选择文本引擎，得分: {text_score}")
            else:
                # 无法确定，回退到混合引擎模式
                self.logger.info("智能判断无法确定引擎类型，回退到混合引擎模式")
                return self._handle_hybrid_engine_query(query, start_time, **kwargs)
            
            # 调用单引擎查询
            return self._handle_single_engine_query(query, selected_type, start_time, **kwargs)
            
        except Exception as e:
            self.logger.error(f"智能引擎模式查询处理失败: {str(e)}")
            # 回退到混合引擎模式
            return self._handle_hybrid_engine_query(query, start_time, **kwargs)
    
    def _handle_hybrid_engine_query(self, query: str, start_time: float, **kwargs) -> QueryResult:
        """
        混合引擎模式：同时执行三个引擎，融合结果，进行混合reranking，调用新Pipeline
        
        :param query: 查询文本
        :param start_time: 开始时间
        :param kwargs: 其他参数
        :return: 查询结果
        """
        try:
            self.logger.info("开始混合引擎模式")
            
            # 1. 并行执行三个引擎的recall
            recall_results = self._execute_parallel_recall(query, **kwargs)
            
            # 2. 融合recall结果
            combined_results = self._merge_recall_results(recall_results)
            
            # 3. 调用混合reranking service
            if self.reranking_engine and combined_results:
                reranked_results = self._execute_hybrid_reranking(query, combined_results)
            else:
                reranked_results = combined_results
                self.logger.warning("重排序引擎不可用，跳过reranking步骤")
            
            # 4. 调用新Pipeline（LLM + 溯源）
            if reranked_results:
                pipeline_result = self._execute_new_pipeline(query, reranked_results, **kwargs)
            else:
                pipeline_result = {
                    'filtered_results': [],
                    'llm_answer': '抱歉，没有找到相关的信息。',
                    'pipeline_metrics': {'total_time': 0, 'input_count': 0, 'output_count': 0}
                }
                self.logger.warning("没有reranking结果，跳过Pipeline步骤")
            
            # 5. 构建最终结果
            processing_time = time.time() - start_time
            
            # 检查pipeline_result的类型和格式
            if hasattr(pipeline_result, 'filtered_sources'):
                # UnifiedPipelineResult对象
                filtered_results = pipeline_result.filtered_sources
                llm_answer = pipeline_result.llm_answer
                pipeline_metrics = pipeline_result.pipeline_metrics
            elif isinstance(pipeline_result, dict):
                # 字典格式
                filtered_results = pipeline_result.get('filtered_results', [])
                llm_answer = pipeline_result.get('llm_answer', '抱歉，Pipeline执行失败，返回原始结果。')
                pipeline_metrics = pipeline_result.get('pipeline_metrics', {})
            else:
                # 其他格式，使用默认值
                filtered_results = reranked_results[:5] if reranked_results else []
                llm_answer = '抱歉，Pipeline执行失败，返回原始结果。'
                pipeline_metrics = {'total_time': 0, 'input_count': len(reranked_results), 'output_count': len(filtered_results)}
            
            final_result = QueryResult(
                success=True,
                query=query,
                query_type=QueryType.HYBRID,
                results=filtered_results,
                total_count=len(filtered_results),
                processing_time=processing_time,
                engine_name="HybridEngine[混合模式]",
                metadata={
                    'query_intent': '混合查询模式',
                    'engines_used': ['image', 'text', 'table'],
                    'total_results': len(filtered_results),
                    'optimization_enabled': True,
                    'optimization_details': {
                        'recall_results_count': sum(len(results) for results in recall_results.values()),
                        'combined_results_count': len(combined_results),
                        'reranked_results_count': len(reranked_results),
                        'pipeline_input_count': len(reranked_results),
                        'pipeline_output_count': len(filtered_results),
                        'llm_answer': llm_answer,
                        'pipeline_metrics': pipeline_metrics
                    },
                    'llm_answer': llm_answer,
                    'post_processing_metrics': pipeline_metrics,
                    'engine_mode': 'hybrid_multi_engine'
                }
            )
            
            self.logger.info(f"混合引擎模式完成，结果数量: {final_result.total_count}")
            return final_result
            
        except Exception as e:
            self.logger.error(f"混合引擎模式查询处理失败: {str(e)}")
            raise
    
    def _execute_parallel_recall(self, query: str, **kwargs) -> Dict[str, List[Any]]:
        """
        并行执行三个引擎的recall
        
        :param query: 查询文本
        :param kwargs: 其他参数
        :return: 各引擎的recall结果
        """
        recall_results = {'image': [], 'text': [], 'table': []}
        
        # 并行执行recall
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}
            
            if self.image_engine:
                futures['image'] = executor.submit(self._execute_image_recall, query, **kwargs)
            if self.text_engine:
                futures['text'] = executor.submit(self._execute_text_recall, query, **kwargs)
            if self.table_engine:
                futures['table'] = executor.submit(self._execute_table_recall, query, **kwargs)
            
            # 收集结果
            for engine_type, future in futures.items():
                try:
                    result = future.result(timeout=30)  # 30秒超时
                    recall_results[engine_type] = result
                    self.logger.info(f"{engine_type} 引擎recall完成，结果数量: {len(result)}")
                except Exception as e:
                    self.logger.error(f"{engine_type} 引擎recall失败: {str(e)}")
                    recall_results[engine_type] = []
        
        return recall_results
    
    def _execute_sequential_queries(self, query: str, engines_to_use: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        顺序执行引擎查询
        
        :param query: 查询文本
        :param engines_to_use: 要使用的引擎
        :param kwargs: 其他参数
        :return: 查询结果字典
        """
        query_results = {}
        
        for engine_name, engine in engines_to_use.items():
            try:
                result = self._execute_single_query(engine, query, **kwargs)
                query_results[engine_name] = result
                self.logger.info(f"引擎 {engine_name} 查询完成")
            except Exception as e:
                self.logger.error(f"引擎 {engine_name} 查询失败: {str(e)}")
                query_results[engine_name] = []
        
        return query_results
    
    def _select_engines_by_query_type(self, query_type) -> Dict[str, Any]:
        """
        根据明确的查询类型选择要使用的引擎
        
        :param query_type: 查询类型 (QueryType.TEXT, QueryType.IMAGE, QueryType.TABLE, QueryType.HYBRID 或对应的字符串)
        :return: 引擎字典
        """
        engines_to_use = {}
        
        # 添加调试信息
        self.logger.info(f"开始根据查询类型选择引擎: {query_type}")
        self.logger.info(f"混合配置: enable_hybrid_search={getattr(self.hybrid_config, 'enable_hybrid_search', 'N/A')}")
        self.logger.info(f"图片引擎可用: {self.image_engine is not None}")
        self.logger.info(f"文本引擎可用: {self.text_engine is not None}")
        self.logger.info(f"表格引擎可用: {self.table_engine is not None}")
        
        # 根据查询类型选择对应的引擎
        # 支持字符串和枚举类型的比较
        if query_type == QueryType.TEXT or str(query_type).lower() == 'text':
            if self.text_engine and getattr(self.hybrid_config, 'enable_text_search', True):
                engines_to_use['text'] = self.text_engine
                self.logger.info("根据查询类型选择文本引擎")
        elif query_type == QueryType.IMAGE or str(query_type).lower() == 'image':
            if self.image_engine and getattr(self.hybrid_config, 'enable_image_search', True):
                engines_to_use['image'] = self.image_engine
                self.logger.info("根据查询类型选择图片引擎")
        elif query_type == QueryType.TABLE or str(query_type).lower() == 'table':
            if self.table_engine and getattr(self.hybrid_config, 'enable_table_search', True):
                engines_to_use['table'] = self.table_engine
                self.logger.info("根据查询类型选择表格引擎")
        elif query_type == QueryType.HYBRID or str(query_type).lower() == 'hybrid':
            # 混合查询使用所有引擎
            self.logger.info("检测到混合查询类型，开始选择所有可用引擎")
            if getattr(self.hybrid_config, 'enable_hybrid_search', True):
                self.logger.info("混合搜索已启用，开始添加引擎")
                if self.image_engine and getattr(self.hybrid_config, 'enable_image_search', True):
                    engines_to_use['image'] = self.image_engine
                    self.logger.info("✅ 添加图片引擎")
                if self.text_engine and getattr(self.hybrid_config, 'enable_text_search', True):
                    engines_to_use['text'] = self.text_engine
                    self.logger.info("✅ 添加文本引擎")
                if self.table_engine and getattr(self.hybrid_config, 'enable_table_search', True):
                    engines_to_use['table'] = self.table_engine
                    self.logger.info("✅ 添加表格引擎")
                self.logger.info(f"混合查询最终选择的引擎数量: {len(engines_to_use)}")
            else:
                self.logger.warning("混合搜索功能已禁用")
        
        # 如果没有找到对应引擎，记录警告
        if not engines_to_use:
            self.logger.warning(f"查询类型 {query_type} 没有对应的可用引擎")
            self.logger.warning(f"配置状态: enable_hybrid_search={getattr(self.hybrid_config, 'enable_hybrid_search', 'N/A')}")
            self.logger.warning(f"引擎状态: image={self.image_engine is not None}, text={self.text_engine is not None}, table={self.table_engine is not None}")
        
        return engines_to_use
    
    def _select_engines_by_intent(self, query_intent: str) -> Dict[str, Any]:
        """
        根据查询意图选择要使用的引擎
        
        :param query_intent: 查询意图
        :return: 引擎字典
        """
        engines_to_use = {}
        
        # 根据意图选择引擎
        if 'image' in query_intent.lower() or '图片' in query_intent:
            if self.image_engine and getattr(self.hybrid_config, 'enable_image_search', True):
                engines_to_use['image'] = self.image_engine
        
        if 'text' in query_intent.lower() or '文本' in query_intent or '文档' in query_intent:
            if self.text_engine and getattr(self.hybrid_config, 'enable_text_search', True):
                engines_to_use['text'] = self.text_engine
        
        if 'table' in query_intent.lower() or '表格' in query_intent or '数据' in query_intent:
            if self.table_engine and getattr(self.hybrid_config, 'enable_table_search', True):
                engines_to_use['table'] = self.table_engine
        
        # 如果没有特定意图，使用混合查询
        if not engines_to_use:
            if getattr(self.hybrid_config, 'enable_hybrid_search', True):
                if self.image_engine and getattr(self.hybrid_config, 'enable_image_search', True):
                    engines_to_use['image'] = self.image_engine
                if self.text_engine and getattr(self.hybrid_config, 'enable_text_search', True):
                    engines_to_use['text'] = self.text_engine
                if self.table_engine and getattr(self.hybrid_config, 'enable_table_search', True):
                    engines_to_use['table'] = self.table_engine
        
        return engines_to_use
    
    def _should_skip_fusion(self, engines_to_use: Dict[str, Any], query_results: Dict[str, Any]) -> bool:
        """
        判断是否应该跳过融合
        
        :param engines_to_use: 选择的引擎
        :param query_results: 查询结果
        :return: 是否跳过融合
        """
        # 条件1：只有一个引擎
        if len(engines_to_use) == 1:
            engine_name = list(engines_to_use.keys())[0]
            
            # 条件2：该引擎使用了新Pipeline
            if engine_name in query_results:
                engine_result = query_results[engine_name]
                if hasattr(engine_result, 'metadata'):
                    pipeline_type = engine_result.metadata.get('pipeline', '')
                    if pipeline_type == 'unified_pipeline':
                        self.logger.info(f"检测到单引擎{engine_name}使用新Pipeline，跳过融合处理")
                        return True
        
        return False
    
    def _create_direct_result(self, query_results: Dict[str, Any], query_intent: str):
        """
        为单引擎查询创建直接结果，保持接口一致性
        
        :param query_results: 查询结果
        :param query_intent: 查询意图
        :return: 与融合结果格式一致的对象
        """
        engine_name = list(query_results.keys())[0]
        engine_result = query_results[engine_name]
        
        # 创建与融合结果格式一致的对象
        return HybridQueryResult(
            image_results=query_results.get('image', []),
            text_results=query_results.get('text', []),
            table_results=query_results.get('table', []),
            combined_results=engine_result.results,  # 直接使用引擎结果
            relevance_scores={engine_name: 1.0},   # 单引擎权重1.0
            query_intent=query_intent,
            processing_details={
                'fusion_method': 'direct_bypass',
                'total_input_results': len(engine_result.results),
                'total_output_results': len(engine_result.results),
                'bypass_reason': 'single_engine_new_pipeline'
            },
            optimization_details={}
        )
    
    def _get_available_engines(self) -> Dict[str, Any]:
        """获取可用的引擎列表"""
        available_engines = {}
        
        if self.image_engine and getattr(self.hybrid_config, 'enable_image_search', True):
            available_engines['image'] = self.image_engine
        if self.text_engine and getattr(self.hybrid_config, 'enable_text_search', True):
            available_engines['text'] = self.text_engine
        if self.table_engine and getattr(self.hybrid_config, 'enable_table_search', True):
            available_engines['table'] = self.table_engine
        
        return available_engines
    
    def _is_engine_ready(self, engine: BaseEngine) -> bool:
        """检查引擎是否就绪"""
        try:
            if not engine:
                return False
            
            # 检查引擎是否有基本的查询方法
            if hasattr(engine, 'process_query'):
                return True
            
            # 检查引擎状态
            if hasattr(engine, 'get_status'):
                status = engine.get_status()
                return status.get('enabled', False)
            
            return False
            
        except Exception as e:
            self.logger.error(f"检查引擎状态失败: {str(e)}")
            return False
    
    def _execute_image_recall(self, query: str, **kwargs) -> List[Any]:
        """执行图片引擎recall"""
        try:
            if not self.image_engine:
                return []
            
            # 调用图片引擎的recall方法
            # 注意：这里需要根据ImageEngine的实际接口调整
            # 暂时使用process_query，后续可以优化为专门的recall方法
            result = self.image_engine.process_query(query, **kwargs)
            
            # 提取recall结果
            if hasattr(result, 'results') and result.results:
                return result.results
            elif isinstance(result, list):
                return result
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"图片引擎recall执行失败: {str(e)}")
            return []
    
    def _execute_text_recall(self, query: str, **kwargs) -> List[Any]:
        """执行文本引擎recall"""
        try:
            if not self.text_engine:
                return []
            
            # 调用文本引擎的recall方法
            # 注意：这里需要根据TextEngine的实际接口调整
            # 暂时使用process_query，后续可以优化为专门的recall方法
            result = self.text_engine.process_query(query, **kwargs)
            
            # 提取recall结果
            if hasattr(result, 'results') and result.results:
                return result.results
            elif isinstance(result, list):
                return result
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"文本引擎recall执行失败: {str(e)}")
            return []
    
    def _execute_table_recall(self, query: str, **kwargs) -> List[Any]:
        """执行表格引擎recall"""
        try:
            if not self.table_engine:
                return []
            
            # 调用表格引擎的recall方法
            # 注意：这里需要根据TableEngine的实际接口调整
            # 暂时使用process_query，后续可以优化为专门的recall方法
            result = self.table_engine.process_query(query, **kwargs)
            
            # 提取recall结果
            if hasattr(result, 'results') and result.results:
                return result.results
            elif isinstance(result, list):
                return result
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"表格引擎recall执行失败: {str(e)}")
            return []
    
    def _merge_recall_results(self, recall_results: Dict[str, List[Any]]) -> List[Any]:
        """
        融合三个引擎的recall结果
        
        :param recall_results: 各引擎的recall结果
        :return: 融合后的结果
        """
        combined_results = []
        
        # 简单的结果合并，可以后续优化为更智能的融合策略
        for engine_type, results in recall_results.items():
            if results:
                # 为每个结果添加来源引擎标识
                for result in results:
                    if isinstance(result, dict):
                        result['source_engine'] = engine_type
                    combined_results.append(result)
        
        self.logger.info(f"融合完成，总结果数量: {len(combined_results)}")
        return combined_results
    
    def _execute_hybrid_reranking(self, query: str, combined_results: List[Any]) -> List[Any]:
        """
        执行混合reranking
        
        :param query: 查询文本
        :param combined_results: 融合后的结果
        :return: 重排序后的结果
        """
        try:
            if not self.reranking_engine:
                self.logger.warning("重排序引擎不可用，跳过reranking")
                return combined_results
            
            # 调用重排序引擎 - 修复：使用正确的方法名
            if hasattr(self.reranking_engine, 'rerank_candidates'):
                reranked_results = self.reranking_engine.rerank_candidates(query, combined_results)
            elif hasattr(self.reranking_engine, 'rerank'):
                reranked_results = self.reranking_engine.rerank(query, combined_results)
            else:
                self.logger.warning("重排序引擎没有可用的rerank方法，跳过reranking")
                return combined_results
            
            self.logger.info(f"混合reranking完成，输入: {len(combined_results)}, 输出: {len(reranked_results)}")
            return reranked_results
            
        except Exception as e:
            self.logger.error(f"混合reranking执行失败: {str(e)}")
            return combined_results
    
    def _execute_new_pipeline(self, query: str, reranked_results: List[Any], **kwargs) -> Dict[str, Any]:
        """
        执行新Pipeline（LLM + 溯源）
        
        :param query: 查询文本
        :param reranked_results: 重排序后的结果
        :return: Pipeline执行结果
        """
        try:
            # 创建新Pipeline实例
            if not self.llm_engine or not self.source_filter_engine:
                self.logger.warning("LLM引擎或源过滤引擎不可用，跳过Pipeline执行")
                return {
                    'filtered_results': reranked_results[:5] if reranked_results else [],
                    'llm_answer': '抱歉，Pipeline执行失败，返回原始结果。',
                    'pipeline_metrics': {'total_time': 0, 'input_count': len(reranked_results), 'output_count': min(5, len(reranked_results))}
                }
            
            # 创建Pipeline配置
            pipeline_config = {
                'enable_llm_generation': True,
                'enable_source_filtering': True,
                'max_context_results': 10,
                'max_content_length': 1000
            }
            
            pipeline = UnifiedPipeline(pipeline_config, self.llm_engine, self.source_filter_engine)
            
            # 准备Pipeline输入格式
            pipeline_input = []
            for result in reranked_results:
                if isinstance(result, dict):
                    # 提取必要字段
                    content = result.get('content', result.get('page_content', ''))
                    metadata = result.get('metadata', {})
                    pipeline_input.append({
                        'content': content,
                        'metadata': metadata
                    })
            
            # 执行Pipeline
            pipeline_result = pipeline.process(query, pipeline_input, **kwargs)
            
            self.logger.info(f"新Pipeline执行完成，输出结果: {len(pipeline_result.get('filtered_results', []))}")
            return pipeline_result
            
        except Exception as e:
            self.logger.error(f"新Pipeline执行失败: {str(e)}")
            # 返回默认结果
            return {
                'filtered_results': reranked_results[:5] if reranked_results else [],
                'llm_answer': '抱歉，Pipeline执行失败，返回原始结果。',
                'pipeline_metrics': {'total_time': 0, 'input_count': len(reranked_results), 'output_count': min(5, len(reranked_results))}
            }
    
    def get_status(self) -> Dict[str, Any]:
        """获取引擎状态信息"""
        return {
            'name': self.name,
            'version': self.version,
            'status': self.status.value if hasattr(self, 'status') else 'ready',
            'enabled': self.config.enabled if hasattr(self, 'config') else True,
            'stats': getattr(self, 'stats', {}),
            'engine_mode': 'simplified_hybrid',
            'sub_engines': {
                'image': self.image_engine is not None,
                'text': self.text_engine is not None,
                'table': self.table_engine is not None
            },
            'reranking_engine': self.reranking_engine is not None
        }

    def _setup_components(self):
        """设置引擎组件 - 实现抽象方法"""
        # 验证子引擎连接状态
        self._validate_engine_connections()
        
        self.logger.info("子引擎组件设置完成")
    
    def _validate_config(self):
        """验证配置 - 实现抽象方法"""
        if not self.hybrid_config:
            raise ValueError("混合引擎配置不能为空")
        
        # 验证权重配置
        image_weight = getattr(self.hybrid_config, 'image_weight', 0.33)
        text_weight = getattr(self.hybrid_config, 'text_weight', 0.34)
        table_weight = getattr(self.hybrid_config, 'table_weight', 0.33)
        
        total_weight = image_weight + text_weight + table_weight
        
        if abs(total_weight - 1.0) > 0.01:
            self.logger.warning(f"权重配置总和不为1.0: {total_weight}")
        
        self.logger.info("混合引擎配置验证通过")
