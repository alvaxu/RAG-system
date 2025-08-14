'''
程序说明：
## 1. 混合查询引擎，支持跨类型内容检索
## 2. 智能结果融合和排序
## 3. 基于用户查询意图的智能路由
## 4. 支持图片、文本、表格的混合查询
## 5. 集成优化引擎，实现完整的检索→重排序→过滤→生成→验证流程
'''

import logging
import time
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base_engine import BaseEngine, QueryResult, QueryType, EngineStatus, EngineConfig
from .image_engine import ImageEngine
from .text_engine import TextEngine
from .table_engine import TableEngine
from .dashscope_reranking_engine import DashScopeRerankingEngine
from .dashscope_llm_engine import DashScopeLLMEngine
from .smart_filter_engine import SmartFilterEngine
from .source_filter_engine import SourceFilterEngine
from .intelligent_post_processing_engine import IntelligentPostProcessingEngine
try:
    from ..config.v2_config import HybridEngineConfigV2, V2ConfigManager
except ImportError:
    from config.v2_config import HybridEngineConfigV2, V2ConfigManager


@dataclass
class HybridQueryResult:
    """混合查询结果数据类"""
    image_results: List[Any]
    text_results: List[Any]
    table_results: List[Any]
    combined_results: List[Any]
    relevance_scores: Dict[str, float]
    query_intent: str
    processing_details: Dict[str, Any]
    optimization_details: Dict[str, Any]  # 新增：优化流程详情


@dataclass
class OptimizationPipelineResult:
    """优化管道结果数据类"""
    reranked_results: List[Any]
    filtered_results: List[Any]
    llm_answer: str
    filtered_sources: List[Any]
    pipeline_metrics: Dict[str, Any]


class HybridEngine(BaseEngine):
    """
    混合查询引擎
    
    支持跨类型内容检索，智能融合图片、文本、表格查询结果
    集成优化引擎，实现完整的检索→重排序→过滤→生成→验证流程
    """
    
    def __init__(self, config: HybridEngineConfigV2, 
                  image_engine: ImageEngine = None,
                  text_engine: TextEngine = None,
                  table_engine: TableEngine = None,
                  reranking_engine: DashScopeRerankingEngine = None,
                  llm_engine: DashScopeLLMEngine = None,
                  smart_filter_engine: SmartFilterEngine = None,
                  source_filter_engine: SourceFilterEngine = None,
                  config_manager: V2ConfigManager = None,
                  memory_manager = None):
        """
        初始化混合查询引擎
        
        :param config: 混合引擎配置
        :param image_engine: 图片引擎实例
        :param text_engine: 文本引擎实例
        :param table_engine: 表格引擎实例
        :param reranking_engine: 重排序引擎实例
        :param llm_engine: LLM引擎实例
        :param smart_filter_engine: 智能过滤引擎实例
        :param source_filter_engine: 源过滤引擎实例
        :param config_manager: 配置管理器实例
        """
        # 转换为基础配置格式
        base_config = EngineConfig(
            enabled=getattr(config, 'enabled', True),
            name=getattr(config, 'name', 'HybridEngine'),
            version=getattr(config, 'version', '1.0.0'),
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
        
        # 优化引擎实例
        self.reranking_engine = reranking_engine
        self.llm_engine = llm_engine
        self.smart_filter_engine = smart_filter_engine
        self.source_filter_engine = source_filter_engine
        
        # 配置管理器
        self.config_manager = config_manager
        
        # 记忆管理器
        self.memory_manager = memory_manager
        
        # 查询意图分析器
        self.intent_analyzer = QueryIntentAnalyzer()
        
        # 结果融合器
        self.result_fusion = ResultFusion(config)
        
        # 初始化智能后处理引擎
        self.intelligent_post_processing_engine = None
        if hasattr(config, 'optimization_pipeline') and config.optimization_pipeline:
            if hasattr(config.optimization_pipeline, 'enable_intelligent_post_processing') and \
               config.optimization_pipeline.enable_intelligent_post_processing:
                try:
                    from .intelligent_post_processing_engine import IntelligentPostProcessingEngine
                    post_proc_config = config.optimization_pipeline.intelligent_post_processing
                    self.intelligent_post_processing_engine = IntelligentPostProcessingEngine(post_proc_config)
                    self.logger.info("智能后处理引擎初始化成功")
                except Exception as e:
                    self.logger.warning(f"智能后处理引擎初始化失败: {str(e)}")
        
        # 优化管道
        optimization_pipeline_config = getattr(config, 'optimization_pipeline', {})
        self.optimization_pipeline = OptimizationPipeline(
            optimization_pipeline_config,
            reranking_engine,
            llm_engine,
            smart_filter_engine,
            source_filter_engine,
            self.intelligent_post_processing_engine
        )
        
        # 验证子引擎连接状态
        self._validate_engine_connections()
        
        self.logger.info(f"混合查询引擎初始化完成: {self.name}")
    
    def _setup_components(self):
        """设置引擎组件"""
        # 验证子引擎是否可用
        if not self._validate_sub_engines():
            raise RuntimeError("子引擎验证失败，无法初始化混合引擎")
        
        self.logger.info("子引擎验证通过，混合引擎组件设置完成")
    
    def _validate_config(self):
        """验证配置参数"""
        if not self.hybrid_config:
            raise ValueError("混合引擎配置不能为空")
        
        # 验证权重配置
        image_weight = getattr(self.hybrid_config, 'image_weight', 0.33)
        text_weight = getattr(self.hybrid_config, 'text_weight', 0.34)
        table_weight = getattr(self.hybrid_config, 'table_weight', 0.33)
        
        total_weight = image_weight + text_weight + table_weight
        
        if abs(total_weight - 1.0) > 0.01:
            self.logger.warning(f"权重配置总和不为1.0: {total_weight}")
        
        # 验证优化管道配置
        if getattr(self.hybrid_config, 'enable_optimization_pipeline', True):
            if not getattr(self.hybrid_config, 'optimization_pipeline', {}):
                raise ValueError("启用优化管道但配置为空")
    
    def _validate_sub_engines(self) -> bool:
        """验证子引擎是否可用"""
        required_engines = []
        
        # 基础引擎验证
        if getattr(self.hybrid_config, 'enable_image_search', True) and self.image_engine:
            required_engines.append(('image', self.image_engine))
        if getattr(self.hybrid_config, 'enable_text_search', True) and self.text_engine:
            required_engines.append(('text', self.text_engine))
        if getattr(self.hybrid_config, 'enable_table_search', True) and self.table_engine:
            required_engines.append(('table', self.table_engine))
        
        # 优化引擎验证
        if getattr(self.hybrid_config, 'enable_optimization_pipeline', True):
            # 获取优化管道配置
            optimization_pipeline = getattr(self.hybrid_config, 'optimization_pipeline', None)
            if optimization_pipeline:
                if hasattr(optimization_pipeline, 'enable_reranking') and optimization_pipeline.enable_reranking and self.reranking_engine:
                    required_engines.append(('reranking', self.reranking_engine))
                if hasattr(optimization_pipeline, 'enable_llm_generation') and optimization_pipeline.enable_llm_generation and self.llm_engine:
                    required_engines.append(('llm', self.llm_engine))
                if hasattr(optimization_pipeline, 'enable_smart_filtering') and optimization_pipeline.enable_smart_filtering and self.smart_filter_engine:
                    required_engines.append(('smart_filter', self.smart_filter_engine))
                if hasattr(optimization_pipeline, 'enable_source_filtering') and optimization_pipeline.enable_source_filtering and self.source_filter_engine:
                    required_engines.append(('source_filter', self.source_filter_engine))
                if hasattr(optimization_pipeline, 'enable_intelligent_post_processing') and optimization_pipeline.enable_intelligent_post_processing and self.intelligent_post_processing_engine:
                    required_engines.append(('intelligent_post_processing', self.intelligent_post_processing_engine))
        
        # 检查引擎状态
        for engine_name, engine in required_engines:
            if not self._is_engine_ready(engine):
                self.logger.warning(f"引擎 {engine_name} 未就绪")
                return False
        
        self.logger.info(f"验证通过，共 {len(required_engines)} 个引擎")
        return True
    
    def _validate_engine_connections(self):
        """验证引擎连接状态"""
        try:
            # 验证基础引擎
            if self.image_engine:
                self.logger.info(f"图片引擎状态: {self.image_engine.get_status()}")
            if self.text_engine:
                self.logger.info(f"文本引擎状态: {self.text_engine.get_status()}")
            if self.table_engine:
                self.logger.info(f"表格引擎状态: {self.table_engine.get_status()}")
            
            # 验证优化引擎
            if self.reranking_engine:
                self.logger.info(f"重排序引擎状态: {self.reranking_engine.get_engine_status()}")
            if self.llm_engine:
                self.logger.info(f"LLM引擎状态: {self.llm_engine.get_engine_status()}")
            if self.smart_filter_engine:
                self.logger.info(f"智能过滤引擎状态: {self.smart_filter_engine.get_engine_status()}")
            if self.source_filter_engine:
                self.logger.info(f"源过滤引擎状态: {self.source_filter_engine.get_engine_status()}")
            if self.intelligent_post_processing_engine:
                self.logger.info("智能后处理引擎状态: 已初始化")
                
        except Exception as e:
            self.logger.error(f"验证引擎连接状态时发生错误: {str(e)}")
    
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
            
            # 1. 检查是否有明确的查询类型
            query_type = kwargs.get('query_type')
            if query_type:
                self.logger.info(f"检测到明确的查询类型: {query_type}")
                # 根据查询类型选择引擎
                engines_to_use = self._select_engines_by_query_type(query_type)
                # 当有明确查询类型时，设置默认的查询意图
                query_intent = f"基于查询类型 {query_type} 的检索"
            else:
                # 2. 分析查询意图
                query_intent = self.intent_analyzer.analyze_intent(query)
                self.logger.info(f"查询意图分析结果: {query_intent}")
                
                # 3. 选择要使用的引擎
                engines_to_use = self._select_engines_by_intent(query_intent)
            
            self.logger.info(f"选择的引擎: {list(engines_to_use.keys())}")
            
            # 3. 执行查询
            if len(engines_to_use) > 1:
                query_results = self._execute_parallel_queries(query, query_intent, **kwargs)
            else:
                query_results = self._execute_sequential_queries(query, engines_to_use, **kwargs)
            
            # 4. 结果融合
            fused_results = self.result_fusion.fuse_results(
                query_results, query_intent, self.hybrid_config
            )
            
            # 5. 优化管道处理（如果启用）
            if getattr(self.hybrid_config, 'enable_optimization_pipeline', True) and self.optimization_pipeline:
                optimization_result = self.optimization_pipeline.process(
                    query, fused_results.combined_results, **kwargs
                )
                
                # 更新融合结果
                fused_results.combined_results = optimization_result.filtered_results
                fused_results.optimization_details = {
                    'reranked_count': len(optimization_result.reranked_results),
                    'filtered_count': len(optimization_result.filtered_results),
                    'llm_answer': optimization_result.llm_answer,
                    'filtered_sources_count': len(optimization_result.filtered_sources),
                    'pipeline_metrics': optimization_result.pipeline_metrics
                }
                
                self.logger.info(f"优化管道处理完成，最终结果数量: {len(fused_results.combined_results)}")
                self.logger.info(f"LLM答案长度: {len(optimization_result.llm_answer) if optimization_result.llm_answer else 0}")
                self.logger.info(f"优化详情: {fused_results.optimization_details}")
            else:
                self.logger.info("优化管道未启用或引擎不可用，跳过优化处理")
            
            # 6. 构建最终结果
            final_result = self._build_final_result(
                query, query_results, fused_results, query_intent, start_time, query_type
            )
            
            processing_time = time.time() - start_time
            self.logger.info(f"查询处理完成，耗时: {processing_time:.2f}秒")
            
            return final_result
            
        except Exception as e:
            self.logger.error(f"查询处理过程中发生错误: {str(e)}")
            processing_time = time.time() - start_time
            
            # 返回错误结果
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
    
    def _execute_parallel_queries(self, query: str, query_intent: str, **kwargs) -> Dict[str, Any]:
        """
        并行执行多个引擎查询
        
        :param query: 查询文本
        :param query_intent: 查询意图
        :param kwargs: 其他参数
        :return: 查询结果字典
        """
        query_results = {}
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            # 提交查询任务
            future_to_engine = {}
            
            if self.image_engine and getattr(self.hybrid_config, 'enable_image_search', True):
                future = executor.submit(self._execute_single_query, self.image_engine, query, **kwargs)
                future_to_engine[future] = 'image'
            
            if self.text_engine and getattr(self.hybrid_config, 'enable_text_search', True):
                future = executor.submit(self._execute_single_query, self.text_engine, query, **kwargs)
                future_to_engine[future] = 'text'
            
            if self.table_engine and getattr(self.hybrid_config, 'enable_table_search', True):
                future = executor.submit(self._execute_single_query, self.table_engine, query, **kwargs)
                future_to_engine[future] = 'table'
            
            # 收集结果
            for future in as_completed(future_to_engine):
                engine_name = future_to_engine[future]
                try:
                    result = future.result()
                    query_results[engine_name] = result
                    self.logger.info(f"引擎 {engine_name} 查询完成")
                except Exception as e:
                    self.logger.error(f"引擎 {engine_name} 查询失败: {str(e)}")
                    query_results[engine_name] = []
        
        return query_results
    
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
            if hasattr(engine, 'get_status'):
                status = engine.get_status()
                return status.get('status') == EngineStatus.READY
            elif hasattr(engine, 'get_engine_status'):
                status = engine.get_engine_status()
                return status.get('enabled', True)
            else:
                return True
        except Exception:
            return False
    
    def _optimize_engine_selection(self, engines: Dict[str, Any], query_intent: str) -> Dict[str, Any]:
        """
        优化引擎选择策略
        
        :param engines: 可用引擎
        :param query_intent: 查询意图
        :return: 优化后的引擎选择
        """
        optimized_engines = {}
        
        # 根据意图和引擎性能优化选择
        for engine_name, engine in engines.items():
            if self._is_engine_ready(engine):
                # 检查引擎是否适合当前查询
                if self._is_engine_suitable_for_intent(engine_name, query_intent):
                    optimized_engines[engine_name] = engine
        
        return optimized_engines
    
    def _is_engine_suitable_for_intent(self, engine_name: str, query_intent: str) -> bool:
        """判断引擎是否适合当前查询意图"""
        intent_lower = query_intent.lower()
        
        if engine_name == 'image':
            return any(keyword in intent_lower for keyword in ['图片', '图像', '照片', '图表', '可视化'])
        elif engine_name == 'text':
            return any(keyword in intent_lower for keyword in ['文本', '文档', '内容', '描述', '说明'])
        elif engine_name == 'table':
            return any(keyword in intent_lower for keyword in ['表格', '数据', '统计', '数字', '列表'])
        
        return True
    
    def _execute_single_query(self, engine: BaseEngine, query: str, **kwargs) -> Any:
        """执行单个引擎查询"""
        try:
            if hasattr(engine, 'process_query'):
                return engine.process_query(query, **kwargs)
            elif hasattr(engine, 'search'):
                return engine.search(query, **kwargs)
            else:
                self.logger.warning(f"引擎 {engine.__class__.__name__} 不支持查询方法")
                return []
        except Exception as e:
            self.logger.error(f"执行引擎查询失败: {str(e)}")
            return []
    
    def _build_final_result(self, query: str, query_results: Dict[str, Any], 
                           fused_results: HybridQueryResult, query_intent: str, 
                           start_time: float, query_type=None) -> QueryResult:
        """
        构建最终查询结果
        
        :param query: 查询文本
        :param query_results: 原始查询结果
        :param fused_results: 融合后的结果
        :param query_intent: 查询意图
        :param start_time: 开始时间
        :return: 最终查询结果
        """
        processing_time = time.time() - start_time
        
        # 构建结果列表
        results = []
        for result in fused_results.combined_results:
            if isinstance(result, dict):
                results.append(result)
            else:
                # 转换为字典格式
                results.append({
                    'content': str(result),
                    'type': 'unknown',
                    'score': 0.0
                })
        
        # 检查是否有优化管道的答案
        llm_answer = ""
        self.logger.info(f"检查优化管道结果: {fused_results.optimization_details}")
        if hasattr(fused_results, 'optimization_details') and fused_results.optimization_details:
            llm_answer = fused_results.optimization_details.get('llm_answer', "")
            self.logger.info(f"找到LLM答案: {llm_answer[:100] if llm_answer else '无'}")
        else:
            self.logger.warning("未找到优化管道结果或结果为空")
        
        # 检查是否有智能后处理的结果
        post_processing_metrics = {}
        if hasattr(fused_results, 'optimization_details') and fused_results.optimization_details:
            post_processing_metrics = fused_results.optimization_details.get('post_processing_metrics', {})
            if post_processing_metrics:
                self.logger.info(f"智能后处理指标: {post_processing_metrics}")
        
        # 构建元数据
        metadata = {
            'query_intent': query_intent,
            'engines_used': list(query_results.keys()),
            'total_results': len(results),
            'optimization_enabled': getattr(self.hybrid_config, 'enable_optimization_pipeline', True),
            'optimization_details': fused_results.optimization_details if hasattr(fused_results, 'optimization_details') else {},
            'llm_answer': llm_answer,  # 添加LLM答案到元数据
            'post_processing_metrics': post_processing_metrics  # 添加智能后处理指标
        }
        
        # 如果有LLM答案，将其添加到元数据中，但不作为source
        # LLM答案只用于answer显示，sources应该来自知识库
        
        # 确定查询类型
        # 优先使用传入的明确查询类型
        if query_type:
            final_query_type = query_type
            self.logger.info(f"使用明确的查询类型: {query_type}")
        # 如果没有明确类型，根据引擎选择推断
        elif len(query_results) == 1:
            engine_name = list(query_results.keys())[0]
            if engine_name == 'text':
                final_query_type = QueryType.TEXT
            elif engine_name == 'image':
                final_query_type = QueryType.IMAGE
            elif engine_name == 'table':
                final_query_type = QueryType.TABLE
            else:
                final_query_type = QueryType.HYBRID
            self.logger.info(f"根据引擎选择推断查询类型: {final_query_type}")
        else:
            final_query_type = QueryType.HYBRID
            self.logger.info("使用默认混合查询类型")
        
        return QueryResult(
            success=True,
            query=query,
            query_type=final_query_type,
            results=results,
            total_count=len(results),
            processing_time=processing_time,
            engine_name=self.name,
            metadata=metadata
        )
    
    def get_hybrid_status(self) -> Dict[str, Any]:
        """获取混合引擎状态信息"""
        status = {
            'engine_name': self.name,
            'version': self.version,
            'status': self.status.value,
            'enabled': self.enabled,
            'config': {
                'enable_image_search': getattr(self.hybrid_config, 'enable_image_search', True),
                'enable_text_search': getattr(self.hybrid_config, 'enable_text_search', True),
                'enable_table_search': getattr(self.hybrid_config, 'enable_table_search', True),
                'enable_hybrid_search': getattr(self.hybrid_config, 'enable_hybrid_search', True),
                'enable_optimization_pipeline': getattr(self.hybrid_config, 'enable_optimization_pipeline', True)
            },
            'engines': {}
        }
        
        # 基础引擎状态
        if self.image_engine:
            status['engines']['image'] = self.image_engine.get_status()
        if self.text_engine:
            status['engines']['text'] = self.text_engine.get_status()
        if self.table_engine:
            status['engines']['table'] = self.table_engine.get_status()
        
        # 优化引擎状态
        if self.reranking_engine:
            status['engines']['reranking'] = self.reranking_engine.get_engine_status()
        if self.llm_engine:
            status['engines']['llm'] = self.llm_engine.get_engine_status()
        if self.smart_filter_engine:
            status['engines']['smart_filter'] = self.smart_filter_engine.get_engine_status()
        if self.source_filter_engine:
            status['engines']['source_filter'] = self.source_filter_engine.get_engine_status()
        
        return status


class OptimizationPipeline:
    """优化管道 - 实现完整的检索→重排序→过滤→生成→验证流程"""
    
    def __init__(self, config, reranking_engine, llm_engine, smart_filter_engine, source_filter_engine, intelligent_post_processing_engine=None):
        """
        初始化优化管道
        
        :param config: 优化管道配置
        :param reranking_engine: 重排序引擎
        :param llm_engine: LLM引擎
        :param smart_filter_engine: 智能过滤引擎
        :param source_filter_engine: 源过滤引擎
        :param intelligent_post_processing_engine: 智能后处理引擎
        """
        self.config = config
        self.reranking_engine = reranking_engine
        self.llm_engine = llm_engine
        self.smart_filter_engine = smart_filter_engine
        self.source_filter_engine = source_filter_engine
        self.intelligent_post_processing_engine = intelligent_post_processing_engine
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("优化管道初始化完成")
    
    def process(self, query: str, results: List[Any], **kwargs) -> OptimizationPipelineResult:
        """
        执行完整的优化流程
        
        :param query: 查询文本
        :param results: 检索结果
        :param kwargs: 其他参数
        :return: 优化管道结果
        """
        start_time = time.time()
        pipeline_metrics = {}
        
        try:
            self.logger.info(f"开始优化管道处理，输入结果数量: {len(results)}")
            
            # 1. 重排序（如果启用）
            reranked_results = results
            if self.config.enable_reranking and self.reranking_engine:
                rerank_start = time.time()
                reranked_results = self._rerank_results(query, results)
                rerank_time = time.time() - rerank_start
                pipeline_metrics['rerank_time'] = rerank_time
                pipeline_metrics['rerank_count'] = len(reranked_results)
                self.logger.info(f"重排序完成，耗时: {rerank_time:.2f}秒")
            
            # 2. 智能过滤（如果启用）
            filtered_results = reranked_results
            if self.config.enable_smart_filtering and self.smart_filter_engine:
                filter_start = time.time()
                filtered_results = self._smart_filter_results(query, reranked_results)
                filter_time = time.time() - filter_start
                pipeline_metrics['filter_time'] = filter_time
                pipeline_metrics['filter_count'] = len(filtered_results)
                self.logger.info(f"智能过滤完成，耗时: {filter_time:.2f}秒")
            
            # 3. LLM生成答案（如果启用）
            llm_answer = ""
            if self.config.enable_llm_generation and self.llm_engine:
                llm_start = time.time()
                llm_answer = self._generate_llm_answer(query, filtered_results)
                llm_time = time.time() - llm_start
                pipeline_metrics['llm_time'] = llm_time
                pipeline_metrics['llm_answer_length'] = len(llm_answer)
                self.logger.info(f"LLM答案生成完成，耗时: {llm_time:.2f}秒")
            
            # 4. 智能后处理（如果启用）
            final_results = filtered_results
            if self.config.enable_intelligent_post_processing and self.intelligent_post_processing_engine and llm_answer:
                post_proc_start = time.time()
                # 准备所有类型的结果
                all_results = self._prepare_all_results_for_post_processing(filtered_results)
                # 执行智能后处理
                post_proc_result = self.intelligent_post_processing_engine.process(llm_answer, all_results)
                # 合并后处理结果
                final_results = self._merge_post_processing_results(filtered_results, post_proc_result)
                post_proc_time = time.time() - post_proc_start
                pipeline_metrics['post_processing_time'] = post_proc_time
                pipeline_metrics['post_processing_metrics'] = post_proc_result.filtering_metrics
                self.logger.info(f"智能后处理完成，耗时: {post_proc_time:.2f}秒")
            
            # 5. 源过滤（如果启用）
            filtered_sources = final_results
            if self.config.enable_source_filtering and self.source_filter_engine and llm_answer:
                source_filter_start = time.time()
                filtered_sources = self._filter_sources(llm_answer, final_results, query)
                source_filter_time = time.time() - source_filter_start
                pipeline_metrics['source_filter_time'] = source_filter_time
                pipeline_metrics['source_filter_count'] = len(filtered_sources)
                self.logger.info(f"源过滤完成，耗时: {source_filter_time:.2f}秒")
            
            # 计算总耗时
            total_time = time.time() - start_time
            pipeline_metrics['total_time'] = total_time
            pipeline_metrics['input_count'] = len(results)
            pipeline_metrics['output_count'] = len(filtered_sources)
            
            self.logger.info(f"优化管道处理完成，总耗时: {total_time:.2f}秒")
            
            return OptimizationPipelineResult(
                reranked_results=reranked_results,
                filtered_results=filtered_sources,
                llm_answer=llm_answer,
                filtered_sources=filtered_sources,
                pipeline_metrics=pipeline_metrics
            )
            
        except Exception as e:
            self.logger.error(f"优化管道处理过程中发生错误: {str(e)}")
            # 返回原始结果
            return OptimizationPipelineResult(
                reranked_results=results,
                filtered_results=results,
                llm_answer="",
                filtered_sources=results,
                pipeline_metrics={'error': str(e)}
            )
    
    def _rerank_results(self, query: str, results: List[Any]) -> List[Any]:
        """重排序结果"""
        try:
            if not results:
                return results
            
            # 准备文档数据
            documents = []
            for result in results:
                if isinstance(result, dict):
                    content = result.get('content', '')
                    if content:
                        documents.append({
                            'content': content,
                            'metadata': result.get('metadata', {}),
                            'original_result': result
                        })
                else:
                    documents.append({
                        'content': str(result),
                        'metadata': {},
                        'original_result': result
                    })
            
            # 执行重排序
            reranked_docs = self.reranking_engine.rerank_documents(query, documents)
            
            # 恢复原始结果格式
            reranked_results = []
            for doc in reranked_docs:
                original_result = doc.get('original_result', doc)
                if isinstance(original_result, dict):
                    original_result['rerank_score'] = doc.get('rerank_score', 0.0)
                    original_result['rerank_rank'] = doc.get('rerank_rank', 0)
                reranked_results.append(original_result)
            
            return reranked_results
            
        except Exception as e:
            self.logger.error(f"重排序失败: {str(e)}")
            return results
    
    def _smart_filter_results(self, query: str, results: List[Any]) -> List[Any]:
        """智能过滤结果"""
        try:
            if not results:
                return results
            
            # 准备文档数据
            documents = []
            for result in results:
                if isinstance(result, dict):
                    content = result.get('content', '')
                    if content:
                        documents.append({
                            'content': content,
                            'metadata': result.get('metadata', {}),
                            'original_result': result
                        })
                else:
                    documents.append({
                        'content': str(result),
                        'metadata': {},
                        'original_result': result
                    })
            
            # 执行智能过滤
            filtered_docs = self.smart_filter_engine.filter_documents(query, documents)
            
            # 恢复原始结果格式
            filtered_results = []
            for doc in filtered_docs:
                original_result = doc.get('original_result', doc)
                if isinstance(original_result, dict):
                    original_result['filter_score'] = doc.get('comprehensive_score', 0.0)
                filtered_results.append(original_result)
            
            return filtered_results
            
        except Exception as e:
            self.logger.error(f"智能过滤失败: {str(e)}")
            return results
    
    def _generate_llm_answer(self, query: str, results: List[Any]) -> str:
        """生成LLM答案"""
        try:
            if not results:
                return "抱歉，我没有找到相关的上下文信息来回答您的问题。"
            
            # 构建上下文
            context_parts = []
            for result in results[:5]:  # 限制上下文长度
                if isinstance(result, dict):
                    content = result.get('content', '')
                    if content:
                        context_parts.append(content[:500])  # 限制每个部分长度
                else:
                    context_parts.append(str(result)[:500])
            
            context = "\n\n".join(context_parts)
            
            # 生成答案
            answer = self.llm_engine.generate_answer(query, context)
            
            return answer
            
        except Exception as e:
            self.logger.error(f"LLM答案生成失败: {str(e)}")
            return "抱歉，生成答案时发生错误。"
    
    def _filter_sources(self, llm_answer: str, results: List[Any], query: str) -> List[Any]:
        """过滤源"""
        try:
            if not results:
                return results
            
            # 准备源数据
            sources = []
            for result in results:
                if isinstance(result, dict):
                    content = result.get('content', '')
                    metadata = result.get('metadata', {})
                    if content:
                        sources.append({
                            'content': content,
                            'metadata': metadata,
                            'original_result': result
                        })
                else:
                    sources.append({
                        'content': str(result),
                        'metadata': {},
                        'original_result': result
                    })
            
            # 执行源过滤
            filtered_sources = self.source_filter_engine.filter_sources(llm_answer, sources, query)
            
            # 恢复原始结果格式
            filtered_results = []
            for source in filtered_sources:
                original_result = source.get('original_result', source)
                if isinstance(original_result, dict):
                    original_result['source_relevance_score'] = source.get('relevance_score', 0.0)
                filtered_results.append(original_result)
            
            return filtered_results
            
        except Exception as e:
            self.logger.error(f"源过滤失败: {str(e)}")
            return results
    
    def _prepare_all_results_for_post_processing(self, filtered_results: List[Any]) -> Dict[str, List[Any]]:
        """
        为智能后处理准备所有类型的结果
        
        :param filtered_results: 过滤后的结果
        :return: 按类型分组的结果字典
        """
        try:
            all_results = {
                'image': [],
                'text': [],
                'table': []
            }
            
            for result in filtered_results:
                if isinstance(result, dict):
                    result_type = result.get('result_type', '')
                    if result_type == 'image':
                        all_results['image'].append(result)
                    elif result_type == 'text':
                        all_results['text'].append(result)
                    elif result_type == 'table':
                        all_results['table'].append(result)
                    else:
                        # 如果没有明确类型，尝试推断
                        if 'image_path' in result or 'caption' in result:
                            all_results['image'].append(result)
                        elif 'content' in result and len(str(result.get('content', ''))) > 100:
                            all_results['text'].append(result)
                        elif 'headers' in result or 'table_data' in result:
                            all_results['table'].append(result)
            
            self.logger.debug(f"为智能后处理准备结果：图片 {len(all_results['image'])} 个，文本 {len(all_results['text'])} 个，表格 {len(all_results['table'])} 个")
            return all_results
            
        except Exception as e:
            self.logger.error(f"准备智能后处理结果失败: {str(e)}")
            return {'image': [], 'text': [], 'table': []}
    
    def _merge_post_processing_results(self, original_results: List[Any], post_proc_result) -> List[Any]:
        """
        合并智能后处理结果
        
        :param original_results: 原始结果
        :param post_proc_result: 智能后处理结果
        :return: 合并后的结果
        """
        try:
            # 直接返回智能后处理引擎过滤后的结果，而不是试图通过ID匹配
            # 这样可以避免ID不匹配导致的合并失败问题
            
            merged_results = []
            
            # 添加过滤后的图片结果
            if hasattr(post_proc_result, 'filtered_images') and post_proc_result.filtered_images:
                merged_results.extend(post_proc_result.filtered_images)
            
            # 添加过滤后的文本结果
            if hasattr(post_proc_result, 'filtered_texts') and post_proc_result.filtered_texts:
                merged_results.extend(post_proc_result.filtered_texts)
            
            # 添加过滤后的表格结果
            if hasattr(post_proc_result, 'filtered_tables') and post_proc_result.filtered_tables:
                merged_results.extend(post_proc_result.filtered_tables)
            
            self.logger.info(f"合并智能后处理结果：从 {len(original_results)} 个合并到 {len(merged_results)} 个")
            return merged_results
            
        except Exception as e:
            self.logger.error(f"合并智能后处理结果失败: {str(e)}")
            return original_results


class QueryIntentAnalyzer:
    """查询意图分析器"""
    
    def __init__(self):
        """初始化查询意图分析器"""
        self.logger = logging.getLogger(__name__)
        
        # 意图关键词映射
        self.intent_keywords = {
            'image': ['图片', '图像', '照片', '图表', '可视化', '图', '画', 'icon', 'image', 'picture', 'chart', 'figure'],
            'text': ['文本', '文档', '内容', '描述', '说明', '文字', '文章', 'text', 'document', 'content'],
            'table': ['表格', '数据', '统计', '数字', '列表', '表', '数据表', 'table', 'data', 'statistics'],
            'hybrid': ['混合', '综合', '全部', '所有', 'hybrid', 'mixed', 'all', 'comprehensive']
        }
        
        # 业务领域关键词
        self.domain_keywords = {
            'technical': ['技术', '技术文档', 'API', '代码', '编程', '开发', 'technical', 'api', 'code', 'development'],
            'business': ['业务', '商业', '市场', '财务', '管理', 'business', 'market', 'finance', 'management'],
            'academic': ['学术', '研究', '论文', '学术论文', 'academic', 'research', 'paper', 'thesis']
        }
        
        # 复杂度关键词
        self.complexity_keywords = {
            'simple': ['简单', '基础', '基本', '简单查询', 'simple', 'basic', 'elementary'],
            'complex': ['复杂', '高级', '深度', '复杂查询', 'complex', 'advanced', 'deep'],
            'enhanced': ['增强', '优化', '改进', 'enhanced', 'optimized', 'improved']
        }
    
    def analyze_intent(self, query: str) -> str:
        """
        分析查询意图
        
        :param query: 查询文本
        :return: 意图分析结果
        """
        try:
            query_lower = query.lower()
            
            # 计算各意图的分数
            intent_scores = self._calculate_intent_scores(query_lower)
            
            # 检测混合意图
            has_hybrid_intent = self._detect_hybrid_intent(query_lower)
            
            # 检测业务领域
            detected_domain = self._detect_business_domain(query_lower)
            
            # 检测复杂度
            complexity = self._detect_complexity(query_lower)
            
            # 检测增强内容类型
            enhanced_content_type = self._detect_enhanced_content_type(query_lower)
            
            # 做出最终意图决策
            final_intent = self._make_intent_decision(
                intent_scores, has_hybrid_intent, detected_domain, complexity, enhanced_content_type, query_lower
            )
            
            self.logger.info(f"查询意图分析完成: {final_intent}")
            return final_intent
            
        except Exception as e:
            self.logger.error(f"查询意图分析失败: {str(e)}")
            return "hybrid"  # 默认返回混合意图
    
    def _calculate_intent_scores(self, query_lower: str) -> Dict[str, float]:
        """计算各意图的分数"""
        intent_scores = {}
        
        for intent, keywords in self.intent_keywords.items():
            score = 0.0
            for keyword in keywords:
                if keyword.lower() in query_lower:
                    score += 1.0
            
            # 归一化分数
            intent_scores[intent] = min(score / len(keywords), 1.0)
        
        return intent_scores
    
    def _detect_hybrid_intent(self, query: str) -> bool:
        """检测是否有混合查询意图"""
        hybrid_indicators = ['混合', '综合', '全部', '所有', 'hybrid', 'mixed', 'all', 'comprehensive']
        return any(indicator in query for indicator in hybrid_indicators)
    
    def _detect_business_domain(self, query_lower: str) -> str:
        """检测业务领域"""
        for domain, keywords in self.domain_keywords.items():
            for keyword in keywords:
                if keyword.lower() in query_lower:
                    return domain
        return "general"
    
    def _detect_complexity(self, query_lower: str) -> str:
        """检测查询复杂度"""
        for complexity, keywords in self.complexity_keywords.items():
            for keyword in keywords:
                if keyword.lower() in query_lower:
                    return complexity
        return "medium"
    
    def _detect_enhanced_content_type(self, query_lower: str) -> str:
        """检测增强内容类型"""
        enhanced_indicators = ['增强', '优化', '改进', 'enhanced', 'optimized', 'improved', '高级', 'advanced']
        if any(indicator in query_lower for indicator in enhanced_indicators):
            return "enhanced"
        return "standard"
    
    def _make_intent_decision(self, intent_scores: Dict[str, float], has_hybrid_intent: bool,
                             detected_domain: str, complexity: str, enhanced_content_type: str,
                             query_lower: str) -> str:
        """做出最终意图决策"""
        
        # 如果有明确的混合意图，直接返回
        if has_hybrid_intent:
            return "hybrid"
        
        # 找出最高分数的意图
        max_score = 0.0
        best_intent = "hybrid"
        
        for intent, score in intent_scores.items():
            if score > max_score:
                max_score = score
                best_intent = intent
        
        # 如果最高分数太低，使用混合意图
        if max_score < 0.3:
            return "hybrid"
        
        # 根据业务领域调整意图
        if detected_domain == "technical" and best_intent == "text":
            return "technical_text"
        elif detected_domain == "business" and best_intent == "table":
            return "business_table"
        elif detected_domain == "academic" and best_intent == "text":
            return "academic_text"
        
        # 根据复杂度调整意图
        if complexity == "complex" and best_intent in ["text", "table"]:
            return f"complex_{best_intent}"
        elif complexity == "enhanced" and best_intent == "image":
            return "enhanced_image"
        
        return best_intent


class ResultFusion:
    """结果融合器"""
    
    def __init__(self, config: HybridEngineConfigV2):
        """
        初始化结果融合器
        
        :param config: 混合引擎配置
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def fuse_results(self, query_results: Dict[str, Any], query_intent: str, 
                    config: HybridEngineConfigV2) -> HybridQueryResult:
        """
        融合查询结果
        
        :param query_results: 查询结果字典
        :param query_intent: 查询意图
        :param config: 混合引擎配置
        :return: 融合后的结果
        """
        try:
            # 提取各引擎的结果
            image_results = query_results.get('image', [])
            text_results = query_results.get('text', [])
            table_results = query_results.get('table', [])
            
            # 如果结果是QueryResult对象，提取其中的results属性
            if hasattr(image_results, 'results'):
                image_results = image_results.results
            if hasattr(text_results, 'results'):
                text_results = text_results.results
            if hasattr(table_results, 'results'):
                table_results = table_results.results
            
            # 计算相关性分数
            relevance_scores = self._calculate_relevance_scores(
                image_results, text_results, table_results, query_intent, config
            )
            
            # 合并结果
            combined = self._combine_results(
                image_results, text_results, table_results, relevance_scores, config
            )
            
            # 智能排序
            sorted_results = self._smart_sort_results(combined, relevance_scores)
            
            # 去重和优化
            final_results = self._deduplicate_and_optimize(sorted_results)
            
            # 构建融合结果
            fused_result = HybridQueryResult(
                image_results=image_results,
                text_results=text_results,
                table_results=table_results,
                combined_results=final_results,
                relevance_scores=relevance_scores,
                query_intent=query_intent,
                processing_details={
                    'fusion_method': 'smart_weighted',
                    'total_input_results': len(image_results) + len(text_results) + len(table_results),
                    'total_output_results': len(final_results)
                },
                optimization_details={}  # 添加缺失的参数
            )
            
            self.logger.info(f"结果融合完成，输入: {fused_result.processing_details['total_input_results']}, 输出: {fused_result.processing_details['total_output_results']}")
            
            return fused_result
            
        except Exception as e:
            self.logger.error(f"结果融合失败: {str(e)}")
            # 返回空结果
            return HybridQueryResult(
                image_results=[],
                text_results=[],
                table_results=[],
                combined_results=[],
                relevance_scores={},
                query_intent=query_intent,
                processing_details={'error': str(e)},
                optimization_details={}  # 添加缺失的参数
            )
    
    def _calculate_relevance_scores(self, image_results: List[Any], text_results: List[Any], 
                                   table_results: List[Any], query_intent: str, 
                                   config: HybridEngineConfigV2) -> Dict[str, float]:
        """计算相关性分数"""
        scores = {}
        
        # 基础分数
        scores['image'] = len(image_results) * getattr(config, 'image_weight', 0.33)
        scores['text'] = len(text_results) * getattr(config, 'text_weight', 0.34)
        scores['table'] = len(table_results) * getattr(config, 'table_weight', 0.33)
        
        # 根据查询意图调整分数
        intent_multipliers = self._get_intent_multipliers(query_intent)
        
        for result_type in scores:
            if result_type in intent_multipliers:
                scores[result_type] *= intent_multipliers[result_type]
        
        # 归一化分数
        total_score = sum(scores.values())
        if total_score > 0:
            for result_type in scores:
                scores[result_type] /= total_score
        
        return scores
    
    def _get_intent_multipliers(self, query_intent: str) -> Dict[str, float]:
        """获取意图乘数"""
        multipliers = {'image': 1.0, 'text': 1.0, 'table': 1.0}
        
        if 'image' in query_intent.lower():
            multipliers['image'] = 1.5
        elif 'text' in query_intent.lower():
            multipliers['text'] = 1.5
        elif 'table' in query_intent.lower():
            multipliers['table'] = 1.5
        elif 'hybrid' in query_intent.lower():
            # 混合查询保持平衡
            pass
        
        return multipliers
    
    def _calculate_result_count_adjustment(self, image_count: int, text_count: int, table_count: int) -> Dict[str, float]:
        """计算结果数量调整因子"""
        total_count = image_count + text_count + table_count
        
        if total_count == 0:
            return {'image': 1.0, 'text': 1.0, 'table': 1.0}
        
        # 根据数量比例调整权重
        adjustments = {
            'image': image_count / total_count,
            'text': text_count / total_count,
            'table': table_count / total_count
        }
        
        return adjustments
    
    def _combine_results(self, image_results: List[Any], text_results: List[Any], 
                        table_results: List[Any], relevance_scores: Dict[str, float], 
                        config: HybridEngineConfigV2) -> List[Any]:
        """合并结果"""
        combined = []
        
        # 准备各类型结果
        prepared_results = []
        
        if image_results:
            prepared_results.extend(self._prepare_results(image_results, 'image', relevance_scores.get('image', 0.0)))
        if text_results:
            prepared_results.extend(self._prepare_results(text_results, 'text', relevance_scores.get('text', 0.0)))
        if table_results:
            prepared_results.extend(self._prepare_results(table_results, 'table', relevance_scores.get('table', 0.0)))
        
        # 按相关性分数排序
        prepared_results.sort(key=lambda x: x.get('fusion_score', 0.0), reverse=True)
        
        # 限制结果数量
        max_results = getattr(config, 'max_results', 10)  # 默认值为10
        combined = prepared_results[:max_results]
        
        return combined
    
    def _prepare_results(self, results: List[Any], result_type: str, base_score: float) -> List[Dict[str, Any]]:
        """准备结果数据"""
        prepared = []
        
        for i, result in enumerate(results):
            if isinstance(result, dict):
                prepared_result = result.copy()
                
                # 关键修复：如果结果包含doc对象，提取其中的元数据
                if 'doc' in prepared_result and hasattr(prepared_result['doc'], 'metadata'):
                    doc = prepared_result['doc']
                    # 提取文档内容
                    if hasattr(doc, 'page_content'):
                        prepared_result['content'] = doc.page_content
                    # 提取元数据
                    if hasattr(doc, 'metadata') and doc.metadata:
                        prepared_result.update(doc.metadata)
                        # 确保关键字段存在
                        if 'document_name' not in prepared_result:
                            prepared_result['document_name'] = doc.metadata.get('document_name', '未知文档')
                        if 'page_number' not in prepared_result:
                            prepared_result['page_number'] = doc.metadata.get('page_number', 'N/A')
                        if 'chunk_type' not in prepared_result:
                            prepared_result['chunk_type'] = doc.metadata.get('chunk_type', result_type)
                        if 'source' not in prepared_result:
                            prepared_result['source'] = doc.metadata.get('source', 'unknown')
                
                # 确保所有结果都有content字段
                if 'content' not in prepared_result or not prepared_result['content']:
                    prepared_result['content'] = self._generate_content_for_result(prepared_result, result_type)
            else:
                prepared_result = {
                    'content': str(result),
                    'type': result_type,
                    'original_result': result
                }
            
            # 添加融合相关信息
            prepared_result['result_type'] = result_type
            prepared_result['base_score'] = base_score
            prepared_result['position_score'] = 1.0 / (i + 1)  # 位置分数
            prepared_result['fusion_score'] = base_score * prepared_result['position_score']
            
            prepared.append(prepared_result)
        
        return prepared
    
    def _generate_content_for_result(self, result: Dict[str, Any], result_type: str) -> str:
        """
        为结果生成合适的content字段
        
        :param result: 结果字典
        :param result_type: 结果类型
        :return: 生成的content字符串
        """
        if result_type == 'image':
            # 图片结果：优先使用增强描述，其次是标题
            enhanced_desc = result.get('enhanced_description', '')
            caption = result.get('caption', '')
            title = result.get('title', '')
            
            if enhanced_desc:
                return str(enhanced_desc)
            elif caption:
                return str(caption)
            elif title and title != '无标题':
                return str(title)
            else:
                return f"图片内容 - {result.get('doc_id', 'unknown')}"
                
        elif result_type == 'table':
            # 表格结果：使用表格内容或结构信息
            content = result.get('content', '')
            structure_info = result.get('structure_info', '')
            
            if content:
                return str(content)
            elif structure_info:
                return str(structure_info)
            else:
                return f"表格内容 - {result.get('document_name', 'unknown')}"
                
        elif result_type == 'text':
            # 文本结果：使用文档内容
            content = result.get('content', '')
            if content:
                return str(content)
            else:
                return f"文本内容 - {result.get('document_name', 'unknown')}"
        
        # 默认情况
        return str(result.get('content', f"{result_type}内容"))
    
    def _assess_content_quality(self, result: Any, result_type: str) -> float:
        """评估内容质量"""
        quality_score = 0.5  # 基础分数
        
        if isinstance(result, dict):
            content = result.get('content', '')
            
            # 长度分数
            if len(content) > 100:
                quality_score += 0.2
            
            # 结构分数
            if '\n' in content:
                quality_score += 0.1
            
            # 元数据分数
            metadata = result.get('metadata', {})
            if metadata:
                quality_score += 0.1
            
            # 类型特定分数
            if result_type == 'image':
                if result.get('enhanced_description'):
                    quality_score += 0.1
            elif result_type == 'table':
                if result.get('structure_info'):
                    quality_score += 0.1
            elif result_type == 'text':
                if result.get('semantic_info'):
                    quality_score += 0.1
        
        return min(quality_score, 1.0)
    
    def _smart_sort_results(self, results: List[Dict[str, Any]], relevance_scores: Dict[str, float]) -> List[Dict[str, Any]]:
        """智能排序结果"""
        def sort_key(result):
            # 综合排序因子
            fusion_score = result.get('fusion_score', 0.0)
            quality_score = self._assess_content_quality(result, result.get('result_type', 'unknown'))
            type_diversity_bonus = self._calculate_type_diversity_bonus(result, results)
            
            # 综合分数
            total_score = fusion_score * 0.6 + quality_score * 0.3 + type_diversity_bonus * 0.1
            
            return total_score
        
        # 按综合分数排序
        sorted_results = sorted(results, key=sort_key, reverse=True)
        
        return sorted_results
    
    def _calculate_enhanced_content_bonus(self, result: Dict[str, Any]) -> float:
        """计算增强内容奖励分数"""
        bonus = 0.0
        
        # 检查是否有增强信息
        if result.get('enhanced_description'):
            bonus += 0.1
        
        if result.get('semantic_info'):
            bonus += 0.1
        
        if result.get('structure_info'):
            bonus += 0.1
        
        # 检查元数据完整性
        metadata = result.get('metadata', {})
        if metadata.get('source_name') and metadata.get('source_name') != '未知文档':
            bonus += 0.05
        
        if metadata.get('page_number'):
            bonus += 0.05
        
        if metadata.get('timestamp'):
            bonus += 0.05
        
        return min(bonus, 0.3)
    
    def _analyze_cross_type_relationships(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """分析跨类型关系"""
        enhanced_results = []
        
        for result in results:
            enhanced_result = result.copy()
            
            # 计算跨类型相关性分数
            cross_type_score = self._calculate_cross_type_score(result, results)
            enhanced_result['cross_type_score'] = cross_type_score
            
            enhanced_results.append(enhanced_result)
        
        return enhanced_results
    
    def _calculate_cross_type_score(self, current_result: Dict[str, Any], all_results: List[Dict[str, Any]]) -> float:
        """计算跨类型相关性分数"""
        cross_type_score = 0.0
        
        current_type = current_result.get('result_type', 'unknown')
        current_content = current_result.get('content', '')
        
        for other_result in all_results:
            if other_result == current_result:
                continue
            
            other_type = other_result.get('result_type', 'unknown')
            other_content = other_result.get('content', '')
            
            # 如果类型不同，检查内容相关性
            if other_type != current_type:
                if self._check_content_relationship(current_content, other_content):
                    cross_type_score += 0.1
                
                if self._check_metadata_relationship(current_result, other_result):
                    cross_type_score += 0.05
        
        return min(cross_type_score, 1.0)
    
    def _check_content_relationship(self, content1: Any, content2: Any) -> bool:
        """检查内容关系"""
        if not content1 or not content2:
            return False
        
        # 简单的关键词匹配检查
        content1_str = str(content1).lower()
        content2_str = str(content2).lower()
        
        # 提取可能的实体和关键词
        words1 = set(content1_str.split())
        words2 = set(content2_str.split())
        
        # 计算重叠度
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if union:
            overlap_ratio = len(intersection) / len(union)
            return overlap_ratio > 0.1  # 10%重叠认为相关
        
        return False
    
    def _check_metadata_relationship(self, result1: Dict[str, Any], result2: Dict[str, Any]) -> bool:
        """检查元数据关系"""
        metadata1 = result1.get('metadata', {})
        metadata2 = result2.get('metadata', {})
        
        # 检查来源关系
        source1 = metadata1.get('source_name', '')
        source2 = metadata2.get('source_name', '')
        
        if source1 and source2 and source1 == source2:
            return True
        
        # 检查页码关系
        page1 = metadata1.get('page_number')
        page2 = metadata2.get('page_number')
        
        if page1 and page2 and abs(page1 - page2) <= 2:
            return True
        
        return False
    
    def _calculate_type_diversity_bonus(self, current_result: Dict[str, Any], all_results: List[Dict[str, Any]]) -> float:
        """计算类型多样性奖励分数"""
        current_type = current_result.get('result_type', 'unknown')
        
        # 统计各类型数量
        type_counts = {}
        for result in all_results:
            result_type = result.get('result_type', 'unknown')
            type_counts[result_type] = type_counts.get(result_type, 0) + 1
        
        # 如果当前类型数量较少，给予奖励
        current_type_count = type_counts.get(current_type, 0)
        total_results = len(all_results)
        
        if total_results > 0:
            type_ratio = current_type_count / total_results
            # 类型比例越低，奖励越高
            diversity_bonus = (1.0 - type_ratio) * 0.2
            return diversity_bonus
        
        return 0.0
    
    def _deduplicate_and_optimize(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重和优化结果"""
        seen_contents = set()
        unique_results = []
        
        for result in results:
            content_key = self._generate_content_key(result)
            
            if content_key not in seen_contents:
                seen_contents.add(content_key)
                unique_results.append(result)
            else:
                # 如果内容重复，选择分数更高的
                existing_result = next(r for r in unique_results if self._generate_content_key(r) == content_key)
                if result.get('fusion_score', 0.0) > existing_result.get('fusion_score', 0.0):
                    # 替换为分数更高的结果
                    unique_results.remove(existing_result)
                    unique_results.append(result)
        
        return unique_results
    
    def _generate_content_key(self, result: Dict[str, Any]) -> str:
        """生成内容键值用于去重"""
        content = result.get('content', '')
        result_type = result.get('result_type', 'unknown')
        
        # 简单的去重键值
        if content:
            # 取内容的前100个字符作为键值
            content_key = content[:100].lower().strip()
            return f"{result_type}:{content_key}"
        else:
            return f"{result_type}:{id(result)}"
