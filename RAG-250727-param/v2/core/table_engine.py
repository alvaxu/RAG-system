#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：

## 1. 表格引擎核心实现
## 2. 支持表格查询的专用引擎
## 3. 集成向量搜索和关键词搜索
## 4. 支持表格结构识别和查询优化
"""

import logging
import time
from typing import List, Dict, Any, Optional
from ..core.base_engine import BaseEngine
from ..core.base_engine import EngineConfig
from ..core.base_engine import QueryResult, QueryType
try:
    from .reranking_services import TableRerankingService
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    try:
        from v2.core.reranking_services import TableRerankingService
    except ImportError:
        TableRerankingService = None
import jieba
import jieba.analyse
import re

# 初始化jieba分词器
jieba.initialize()

# 添加自定义词典
custom_words = [
    '财务报表', '收入情况', '员工薪资', '部门分布', '产品库存', '数量统计',
    '详细明细', '汇总统计', '对比分析', '增长趋势', '成本控制', '利润分析',
    '库存管理', '销售业绩', '财务指标', '业务数据', '运营报表', '绩效评估'
]

for word in custom_words:
    jieba.add_word(word)

# 定义停用词
stop_words = {
    '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'
}

logger = logging.getLogger(__name__)


class TableEngine(BaseEngine):
    """
    表格引擎
    
    专门处理表格查询，支持多种搜索策略
    """
    
    def __init__(self, config, vector_store=None, document_loader=None, skip_initial_load=False, 
                 llm_engine=None, source_filter_engine=None):
        """
        初始化表格引擎 - 重构版本，支持更好的配置验证和文档加载
        
        :param config: 表格引擎配置
        :param vector_store: 向量数据库
        :param document_loader: 文档加载器
        :param skip_initial_load: 是否跳过初始文档加载
        :param llm_engine: LLM引擎（用于新Pipeline）
        :param source_filter_engine: 源过滤引擎（用于新Pipeline）
        """
        super().__init__(config)
        
        logger.info("🔍 开始初始化TableEngine")
        logger.info(f"配置类型: {type(config)}")
        logger.info(f"向量数据库: {vector_store}")
        logger.info(f"文档加载器: {document_loader}")
        logger.info(f"跳过初始加载: {skip_initial_load}")
        logger.info(f"LLM引擎: {llm_engine}")
        logger.info(f"源过滤引擎: {source_filter_engine}")
        
        self.vector_store = vector_store
        self.document_loader = document_loader
        self.table_docs = []  # 表格文档缓存
        self._docs_loaded = False
        
        # 新Pipeline相关引擎
        self.llm_engine = llm_engine
        self.source_filter_engine = source_filter_engine
        
        # 初始化表格重排序服务
        self.table_reranking_service = None
        
        logger.info("✅ 基础属性设置完成")
        
        # 验证配置
        logger.info("开始验证配置...")
        self._validate_config()
        logger.info("✅ 配置验证完成")
        
        # 初始化表格重排序服务
        logger.info("开始初始化表格重排序服务...")
        self._initialize_table_reranking_service()
        logger.info("✅ 表格重排序服务初始化完成")
        
        # 初始化五层召回策略
        logger.info("开始初始化五层召回策略...")
        self._initialize_recall_strategy()
        logger.info("✅ 五层召回策略初始化完成")
        
        # 根据参数决定是否加载文档
        if not skip_initial_load:
            logger.info("开始初始文档加载...")
            self._load_documents()
        else:
            logger.info("跳过初始文档加载")
        
        logger.info(f"✅ TableEngine初始化完成，表格文档数量: {len(self.table_docs)}")
    
    def _load_documents(self):
        """加载表格文档 - 重构版本，支持重试和降级策略"""
        if self._docs_loaded:
            return
            
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                logger.info(f"🔄 第{retry_count + 1}次尝试加载表格文档")
                
                # 优先使用统一文档加载器
                if self.document_loader:
                    logger.info("使用统一文档加载器加载表格文档")
                    self.table_docs = self.document_loader.get_documents_by_type('table')
                    if self.table_docs:
                        logger.info(f"✅ 从统一加载器成功加载 {len(self.table_docs)} 个表格文档")
                        self._docs_loaded = True
                        return
                    else:
                        logger.warning("统一加载器未返回表格文档，尝试备选方案")
                
                # 备选方案：从向量数据库加载
                if self.vector_store:
                    logger.info("从向量数据库加载表格文档")
                    self.table_docs = self._load_from_vector_store()
                    if self.table_docs:
                        logger.info(f"✅ 从向量数据库成功加载 {len(self.table_docs)} 个表格文档")
                        self._docs_loaded = True
                        return
                    else:
                        logger.warning("向量数据库未返回表格文档")
                
                # 如果两种方式都失败，抛出异常
                raise ValueError("无法通过任何方式加载表格文档")
                    
            except Exception as e:
                retry_count += 1
                logger.warning(f"⚠️ 表格文档加载失败，第{retry_count}次尝试: {e}")
                logger.warning(f"错误类型: {type(e)}")
                
                if retry_count >= max_retries:
                    # 最终失败，记录错误并清空缓存
                    logger.error(f"❌ 表格文档加载最终失败，已重试{max_retries}次: {e}")
                    import traceback
                    logger.error(f"详细错误信息: {traceback.format_exc()}")
                    self.table_docs = []
                    self._docs_loaded = False
                    return
                else:
                    # 等待后重试
                    import time
                    time.sleep(1)
                    logger.info(f"⏳ 等待1秒后进行第{retry_count + 1}次重试...")
    
    def _load_from_vector_store(self):
        """从向量数据库加载表格文档"""
        try:
            if hasattr(self.vector_store, 'get_table_documents'):
                # 使用专门的表格文档获取方法
                return self.vector_store.get_table_documents()
            elif hasattr(self.vector_store, 'docstore') and hasattr(self.vector_store.docstore, '_dict'):
                # 从docstore中筛选表格文档
                table_docs = []
                docstore_dict = self.vector_store.docstore._dict
                
                logger.info(f"开始从docstore筛选表格文档，总文档数: {len(docstore_dict)}")
                
                for doc_id, doc in docstore_dict.items():
                    # 严格检查文档类型
                    if not hasattr(doc, 'metadata'):
                        logger.debug(f"跳过文档 {doc_id}: 没有metadata属性")
                        continue
                    
                    chunk_type = doc.metadata.get('chunk_type', '')
                    
                    # 判断是否为表格文档
                    if chunk_type == 'table':
                        # 验证文档结构
                        if hasattr(doc, 'page_content') and hasattr(doc, 'metadata'):
                            table_docs.append(doc)
                            if len(table_docs) <= 3:  # 只显示前3个的详细信息
                                logger.debug(f"✅ 加载表格文档: {doc_id}, chunk_type: {chunk_type}")
                                logger.debug(f"  内容长度: {len(doc.page_content)}")
                                logger.debug(f"  元数据: {doc.metadata}")
                        else:
                            logger.warning(f"跳过文档 {doc_id}: 缺少必要属性 (page_content: {hasattr(doc, 'page_content')}, metadata: {hasattr(doc, 'metadata')})")
                    else:
                        logger.debug(f"跳过文档 {doc_id}: chunk_type={chunk_type} (不是表格)")
                
                logger.info(f"从docstore筛选出 {len(table_docs)} 个表格文档")
                
                # 如果没有找到表格文档，尝试其他类型
                if not table_docs:
                    logger.warning("未找到chunk_type='table'的文档，尝试查找包含表格内容的文档...")
                    for doc_id, doc in docstore_dict.items():
                        if hasattr(doc, 'metadata') and hasattr(doc, 'page_content'):
                            content = doc.page_content.lower()
                            # 检查内容是否包含表格特征
                            if any(keyword in content for keyword in ['表格', '表', '行', '列', '数据', '统计']):
                                table_docs.append(doc)
                                logger.debug(f"✅ 通过内容识别表格文档: {doc_id}")
                
                logger.info(f"最终加载 {len(table_docs)} 个表格文档")
                return table_docs
            else:
                logger.warning("向量数据库不支持表格文档获取")
                return []
                
        except Exception as e:
            logger.error(f"从向量数据库加载表格文档失败: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return []
    
    def _ensure_docs_loaded(self):
        """确保文档已加载（延迟加载）"""
        if not self._docs_loaded:
            if self.document_loader:
                logger.info("延迟加载：使用统一文档加载器")
                self._load_from_document_loader()
            else:
                logger.info("延迟加载：使用向量数据库")
                self.table_docs = self._load_from_vector_store()
                self._docs_loaded = True
            
            # 验证加载的文档
            self._validate_loaded_documents()
    
    def _validate_loaded_documents(self):
        """验证已加载的文档"""
        try:
            logger.info(f"开始验证已加载的文档，总数: {len(self.table_docs)}")
            
            if not self.table_docs:
                logger.warning("⚠️ 没有加载到任何表格文档")
                return
            
            valid_docs = []
            invalid_docs = []
            
            for i, doc in enumerate(self.table_docs):
                # 检查文档结构
                if not hasattr(doc, 'metadata'):
                    logger.warning(f"文档 {i}: 缺少metadata属性")
                    invalid_docs.append(i)
                    continue
                
                if not hasattr(doc, 'page_content'):
                    logger.warning(f"文档 {i}: 缺少page_content属性")
                    invalid_docs.append(i)
                    continue
                
                # 检查元数据完整性
                metadata = doc.metadata
                if not isinstance(metadata, dict):
                    logger.warning(f"文档 {i}: metadata不是字典类型，实际类型: {type(metadata)}")
                    invalid_docs.append(i)
                    continue
                
                # 检查内容
                content = doc.page_content
                if not isinstance(content, str):
                    logger.warning(f"文档 {i}: page_content不是字符串类型，实际类型: {type(content)}")
                    invalid_docs.append(i)
                    continue
                
                if len(content.strip()) == 0:
                    logger.warning(f"文档 {i}: page_content为空")
                    invalid_docs.append(i)
                    continue
                
                valid_docs.append(doc)
                logger.debug(f"✅ 文档 {i} 验证通过")
            
            # 更新文档列表
            if invalid_docs:
                logger.warning(f"发现 {len(invalid_docs)} 个无效文档，正在移除...")
                self.table_docs = valid_docs
                logger.info(f"移除无效文档后，剩余 {len(self.table_docs)} 个有效文档")
            else:
                logger.info("所有文档验证通过")
            
            logger.info(f"文档验证完成，有效文档: {len(valid_docs)}, 无效文档: {len(invalid_docs)}")
                
        except Exception as e:
            logger.error(f"文档验证失败: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
    
    def _load_from_document_loader(self):
        """从统一文档加载器获取表格文档"""
        if self.document_loader:
            try:
                self.table_docs = self.document_loader.get_documents_by_type('table')
                self._docs_loaded = True
                logger.info(f"从统一加载器获取表格文档: {len(self.table_docs)} 个")
            except Exception as e:
                logger.error(f"从统一加载器获取表格文档失败: {e}")
                # 降级到向量数据库加载方式
                self.table_docs = self._load_from_vector_store()
                self._docs_loaded = True
        else:
            logger.warning("文档加载器未提供，使用向量数据库加载方式")
            self.table_docs = self._load_from_vector_store()
            self._docs_loaded = True
    
    def _validate_config(self):
        """验证表格引擎配置 - 增强版本，支持Table专用配置验证"""
        # 配置类型检查
        from ..config.v2_config import TableEngineConfigV2
        
        if not isinstance(self.config, TableEngineConfigV2):
            raise ValueError("配置必须是TableEngineConfigV2类型")
        
        # 获取相似度阈值，支持两种配置类型
        threshold = getattr(self.config, 'table_similarity_threshold', 0.7)
        if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 1:
            raise ValueError("表格相似度阈值必须在0-1之间")
        
        # 验证Table专用配置参数
        self._validate_table_specific_config()
        
        # 验证五层召回策略配置
        self._validate_recall_strategy_config()
        
        # 验证重排序配置
        self._validate_reranking_config()
        
        logger.info("✅ 表格引擎配置验证完成")
    
    def _validate_table_specific_config(self):
        """验证Table专用配置参数"""
        try:
            # 验证表格处理相关配置
            table_configs = [
                ('max_table_rows', int, '表格最大行数'),
                ('header_weight', float, '表头权重'),
                ('content_weight', float, '内容权重'),
                ('structure_weight', float, '结构权重'),
                ('enable_structure_search', bool, '启用结构搜索'),
                ('enable_content_search', bool, '启用内容搜索')
            ]
            
            for config_name, expected_type, description in table_configs:
                if hasattr(self.config, config_name):
                    value = getattr(self.config, config_name)
                    if not isinstance(value, expected_type):
                        logger.warning(f"⚠️ {description}配置类型错误: 期望{expected_type.__name__}, 实际{type(value).__name__}")
                    else:
                        logger.debug(f"✅ {description}配置验证通过: {value}")
                else:
                    logger.debug(f"ℹ️ {description}配置未设置，使用默认值")
            
            # 验证权重配置的合理性
            if hasattr(self.config, 'header_weight') and hasattr(self.config, 'content_weight') and hasattr(self.config, 'structure_weight'):
                total_weight = self.config.header_weight + self.config.content_weight + self.config.structure_weight
                if abs(total_weight - 1.0) > 0.01:
                    logger.warning(f"⚠️ 权重配置总和不为1.0: {total_weight}")
            
        except Exception as e:
            logger.error(f"验证Table专用配置失败: {e}")
    
    def _validate_recall_strategy_config(self):
        """验证五层召回策略配置"""
        try:
            if not hasattr(self.config, 'recall_strategy'):
                logger.warning("⚠️ 未配置召回策略，使用默认配置")
                return
            
            strategy = self.config.recall_strategy
            required_layers = [
                'layer1_structure_search',    # 第一层：表格结构搜索
                'layer2_vector_search',       # 第二层：向量语义搜索
                'layer3_keyword_search',      # 第三层：关键词匹配
                'layer4_hybrid_search',       # 第四层：混合智能搜索
                'layer5_expansion_search'     # 第五层：容错扩展搜索
            ]
            
            for layer in required_layers:
                if layer not in strategy:
                    logger.warning(f"⚠️ 缺少召回策略配置: {layer}")
                else:
                    layer_config = strategy[layer]
                    # 修复：支持对象和字典两种格式
                    if hasattr(layer_config, 'enabled'):
                        # 对象格式（通过_convert_recall_strategy_to_objects转换后）
                        enabled = layer_config.enabled
                        top_k = getattr(layer_config, 'top_k', 50)
                        logger.info(f"✅ {layer}: {'启用' if enabled else '禁用'}, top_k: {top_k}")
                    elif isinstance(layer_config, dict):
                        # 字典格式（原始配置）
                        enabled = layer_config.get('enabled', True)
                        top_k = layer_config.get('top_k', 50)
                        logger.info(f"✅ {layer}: {'启用' if enabled else '禁用'}, top_k: {top_k}")
                    else:
                        logger.warning(f"⚠️ 召回策略配置格式错误: {layer}，类型: {type(layer_config)}")
            
        except Exception as e:
            logger.error(f"验证召回策略配置失败: {e}")
    
    def _validate_reranking_config(self):
        """验证重排序配置"""
        try:
            if not hasattr(self.config, 'reranking'):
                logger.warning("⚠️ 未配置重排序，使用默认配置")
                return
            
            reranking = self.config.reranking
            reranking_configs = [
                ('target_count', int, '目标结果数量'),
                ('use_llm_enhancement', bool, '使用LLM增强'),
                ('model_name', str, '模型名称'),
                ('similarity_threshold', float, '相似度阈值')
            ]
            
            for config_name, expected_type, description in reranking_configs:
                if config_name in reranking:
                    value = reranking[config_name]
                    if not isinstance(value, expected_type):
                        logger.warning(f"⚠️ 重排序{description}配置类型错误: 期望{expected_type.__name__}, 实际{type(value).__name__}")
                    else:
                        logger.debug(f"✅ 重排序{description}配置验证通过: {value}")
                else:
                    logger.debug(f"ℹ️ 重排序{description}配置未设置，使用默认值")
            
        except Exception as e:
            logger.error(f"验证重排序配置失败: {e}")
    
    def _initialize_table_reranking_service(self):
        """初始化表格重排序服务"""
        try:
            if not hasattr(self.config, 'reranking'):
                logger.warning("⚠️ 未配置重排序，跳过表格重排序服务初始化")
                return
            
            reranking_config = self.config.reranking
            
            # 检查是否启用LLM增强
            if not reranking_config.get('use_llm_enhancement', False):
                logger.info("ℹ️ LLM增强未启用，跳过表格重排序服务初始化")
                return
            
            # 创建表格重排序服务实例
            self.table_reranking_service = TableRerankingService(reranking_config)
            logger.info(f"✅ 表格重排序服务初始化成功，使用模型: {reranking_config.get('model_name', 'unknown')}")
            
        except Exception as e:
            logger.error(f"❌ 初始化表格重排序服务失败: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            self.table_reranking_service = None
    
    def _rerank_table_results(self, query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        使用表格重排序服务对结果进行重排序
        
        :param query: 查询文本
        :param candidates: 候选结果列表
        :return: 重排序后的结果列表
        """
        try:
            if not self.table_reranking_service:
                logger.info("ℹ️ 表格重排序服务未初始化，跳过重排序")
                return candidates
            
            if not candidates:
                logger.info("ℹ️ 候选结果为空，跳过重排序")
                return candidates
            
            logger.info(f"🔍 开始表格重排序，输入 {len(candidates)} 个候选结果")
            start_time = time.time()
            
            # 准备重排序数据格式
            rerank_candidates = []
            for candidate in candidates:
                # 从doc对象中提取内容
                doc = candidate.get('doc')
                if doc and hasattr(doc, 'page_content') and hasattr(doc, 'metadata'):
                    rerank_candidate = {
                        'content': getattr(doc, 'page_content', ''),
                        'metadata': getattr(doc, 'metadata', {}),
                        'original_candidate': candidate  # 保存原始候选文档的引用
                    }
                    rerank_candidates.append(rerank_candidate)
                else:
                    logger.warning(f"候选文档缺少必要属性，跳过重排序")
            
            if not rerank_candidates:
                logger.warning("没有有效的重排序候选文档，返回原始结果")
                return candidates
            
            # 调用表格重排序服务
            reranked_results = self.table_reranking_service.rerank(query, rerank_candidates)
            
            # 调试：查看重排序结果的格式
            logger.info(f"重排序服务返回 {len(reranked_results)} 个结果")
            for i, result in enumerate(reranked_results):
                if isinstance(result, dict):
                    logger.info(f"重排序结果 {i}: 键={list(result.keys())}")
                    if 'doc' in result:
                        doc_data = result['doc']
                        if isinstance(doc_data, dict):
                            logger.info(f"重排序结果 {i}: doc字段包含键={list(doc_data.keys())}")
                            if 'original_candidate' in doc_data:
                                logger.info(f"重排序结果 {i}: 找到original_candidate引用")
                        else:
                            logger.info(f"重排序结果 {i}: doc字段类型={type(doc_data)}")
                else:
                    logger.info(f"重排序结果 {i}: 类型={type(result)}")
            
            # 修复：确保返回结果格式一致
            final_results = []
            for i, reranked_result in enumerate(reranked_results):
                if isinstance(reranked_result, dict):
                    # 如果重排序结果包含doc字段
                    if 'doc' in reranked_result:
                        # 检查doc字段是否包含original_candidate引用
                        doc_data = reranked_result['doc']
                        if isinstance(doc_data, dict) and 'original_candidate' in doc_data:
                            # 使用原始候选文档引用
                            original_candidate = doc_data['original_candidate']
                            logger.info(f"重排序结果 {i}: 使用原始候选文档引用，类型={type(original_candidate)}")
                        else:
                            # 直接使用doc字段
                            original_candidate = doc_data
                            logger.info(f"重排序结果 {i}: 直接使用doc字段，类型={type(original_candidate)}")
                        
                        # 验证原始候选文档的内容
                        if 'doc' in original_candidate and original_candidate['doc']:
                            doc = original_candidate['doc']
                            content = getattr(doc, 'page_content', '')
                            logger.info(f"重排序结果 {i}: 原始候选文档中doc.page_content长度: {len(content)}")
                        
                        final_results.append({
                            'doc': original_candidate,
                            'score': reranked_result.get('score', 0.5),
                            'source': reranked_result.get('source', 'rerank'),
                            'layer': reranked_result.get('layer', 1)
                        })
                    else:
                        # 否则，构造标准格式
                        original_candidate = candidates[i] if i < len(candidates) else candidates[0]
                        final_results.append({
                            'doc': original_candidate['doc'],
                            'score': reranked_result.get('score', original_candidate.get('score', 0.5)),
                            'source': reranked_result.get('source', 'rerank'),
                            'layer': reranked_result.get('layer', original_candidate.get('layer', 1))
                        })
                else:
                    # 非字典类型，使用原始候选结果
                    logger.warning(f"跳过无效的重排序结果类型: {type(reranked_result)}")
                    if i < len(candidates):
                        final_results.append({
                            'doc': candidates[i]['doc'],
                            'score': candidates[i].get('score', 0.5),
                            'source': candidates[i].get('source', 'unknown'),
                            'layer': candidates[i].get('layer', 1)
                        })
            
            rerank_time = time.time() - start_time
            logger.info(f"✅ 表格重排序完成，处理 {len(candidates)} 个结果，返回 {len(final_results)} 个结果，耗时: {rerank_time:.2f}秒")
            
            return final_results
            
        except Exception as e:
            logger.error(f"❌ 表格重排序失败: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            # 返回原始结果
            return candidates
    
    def _setup_components(self):
        """设置引擎组件 - 实现抽象方法，使用新的文档加载机制"""
        # 检查文档是否已加载，如果没有则加载
        if not self._docs_loaded:
            try:
                logger.info("表格引擎在_setup_components中开始加载文档")
                self._ensure_docs_loaded()
                logger.info(f"✅ 表格引擎在_setup_components中成功加载 {len(self.table_docs)} 个文档")
            except Exception as e:
                logger.error(f"❌ 表格引擎在_setup_components中加载文档失败: {e}")
                import traceback
                logger.error(f"详细错误信息: {traceback.format_exc()}")
                raise
    
    def _analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """
        分析查询意图
        
        :param query: 查询文本
        :return: 查询意图分析结果
        """
        try:
            intent = {
                'query_type': 'unknown',
                'business_domain': 'unknown',
                'data_requirement': 'unknown',
                'time_range': 'unknown',
                'comparison_type': 'unknown'
            }
            
            query_lower = query.lower()
            
            # 分析查询类型
            if any(word in query_lower for word in ['趋势', '变化', '增长', '下降', '波动']):
                intent['query_type'] = 'trend_analysis'
            elif any(word in query_lower for word in ['比较', '对比', '差异', '高低']):
                intent['query_type'] = 'comparison'
            elif any(word in query_lower for word in ['排名', '排序', '前几', '后几']):
                intent['query_type'] = 'ranking'
            elif any(word in query_lower for word in ['统计', '汇总', '总计', '平均']):
                intent['query_type'] = 'statistics'
            
            # 分析业务领域
            if any(word in query_lower for word in ['财务', '收入', '利润', '成本', '资产']):
                intent['business_domain'] = 'finance'
            elif any(word in query_lower for word in ['销售', '市场', '客户', '产品']):
                intent['business_domain'] = 'sales'
            elif any(word in query_lower for word in ['技术', '研发', '创新', '专利']):
                intent['business_domain'] = 'technology'
            
            # 分析数据要求
            if any(word in query_lower for word in ['详细', '具体', '完整']):
                intent['data_requirement'] = 'detailed'
            elif any(word in query_lower for word in ['概览', '总结', '简要']):
                intent['data_requirement'] = 'overview'
            
            # 分析时间范围
            if any(word in query_lower for word in ['年', '季度', '月', '日']):
                intent['time_range'] = 'time_series'
            
            return intent
            
        except Exception as e:
            logger.error(f"查询意图分析失败: {e}")
            return {'query_type': 'unknown', 'business_domain': 'unknown', 'data_requirement': 'unknown', 'time_range': 'unknown', 'comparison_type': 'unknown'}
    
    def _analyze_structure_requirements(self, query: str) -> Dict[str, Any]:
        """分析查询对表格结构的要求"""
        try:
            requirements = {
                'min_rows': 1,
                'max_rows': 1000,
                'min_columns': 1,
                'max_columns': 20,
                'preferred_structure': 'unknown'
            }
            
            query_lower = query.lower()
            
            # 分析行数要求
            if any(word in query_lower for word in ['详细', '完整', '所有']):
                requirements['min_rows'] = 10
                requirements['max_rows'] = 1000
            elif any(word in query_lower for word in ['概览', '总结', '主要']):
                requirements['min_rows'] = 1
                requirements['max_rows'] = 20
            
            # 分析列数要求
            if any(word in query_lower for word in ['多维度', '全面', '综合']):
                requirements['min_columns'] = 3
                requirements['max_columns'] = 20
            elif any(word in query_lower for word in ['简单', '基础']):
                requirements['min_columns'] = 1
                requirements['max_columns'] = 5
            
            return requirements
            
        except Exception as e:
            logger.error(f"结构要求分析失败: {e}")
            return {'min_rows': 1, 'max_rows': 1000, 'min_columns': 1, 'max_columns': 20, 'preferred_structure': 'unknown'}
    
    def process_query(self, query: str, **kwargs) -> QueryResult:
        """
        处理表格查询请求 - 修复版本，与text_engine.py保持一致
        
        :param query: 查询文本
        :param kwargs: 额外参数（包括query_type等）
        :return: QueryResult对象
        """
        if not self.is_enabled():
            return QueryResult(
                success=False,
                query=query,
                query_type=QueryType.TABLE,
                results=[],
                total_count=0,
                processing_time=0.0,
                engine_name=self.name,
                metadata={},
                error_message="表格引擎未启用"
            )
        
        start_time = time.time()
        
        try:
            # 确保文档已加载
            self._ensure_docs_loaded()
            
            # 添加文档状态诊断
            logger.info(f"🔍 表格查询诊断信息:")
            logger.info(f"  - 查询文本: {query}")
            logger.info(f"  - 文档加载状态: {self._docs_loaded}")
            logger.info(f"  - 表格文档数量: {len(self.table_docs)}")
            logger.info(f"  - 向量数据库状态: {self.vector_store is not None}")
            logger.info(f"  - 文档加载器状态: {self.document_loader is not None}")
            
            # 如果文档数量为0，尝试重新加载
            if len(self.table_docs) == 0:
                logger.warning("⚠️ 表格文档数量为0，尝试重新加载...")
                self._docs_loaded = False
                self._ensure_docs_loaded()
                logger.info(f"重新加载后表格文档数量: {len(self.table_docs)}")
            
            # 分析查询意图
            intent_analysis = self._analyze_query_intent(query)
            logger.info(f"查询意图分析: {intent_analysis['query_type']}, 业务领域: {intent_analysis['business_domain']}")
            
            # 执行搜索
            search_results = self._search_tables(query)
            
            # 根据意图调整结果
            if intent_analysis['query_type'] == 'detail_view' and intent_analysis['data_requirement'] == 'detailed':
                # 如果用户意图是查看详细信息，尝试获取完整表格
                if search_results and len(search_results) > 0:
                    top_result = search_results[0]
                    table_id = top_result['doc'].metadata.get('table_id', 'unknown')
                    full_table_result = self.get_full_table(table_id)
                    if full_table_result['status'] == 'success':
                        search_results[0]['full_content'] = full_table_result['content']
                        search_results[0]['full_metadata'] = full_table_result['metadata']
            
            # 检查是否使用新Pipeline
            use_new_pipeline = getattr(self.config, 'use_new_pipeline', True)
            if use_new_pipeline:
                logger.info("使用新的统一Pipeline处理重排序结果")
                # 使用新Pipeline处理结果
                formatted_results = self._process_with_new_pipeline(query, search_results)
            else:
                logger.info("使用传统方式格式化结果")
                # 传统格式化方式
                formatted_results = []
            for result in search_results:
                # 修复：处理重排序后可能没有'doc'键的情况
                if 'doc' not in result:
                    logger.warning(f"跳过无效结果，缺少'doc'键: {result}")
                    # 尝试修复结果格式
                    if isinstance(result, dict) and 'content' in result and 'metadata' in result:
                        # 构造一个模拟的doc对象
                        class MockDoc:
                            def __init__(self, content, metadata):
                                self.page_content = content
                                self.metadata = metadata
                        
                        mock_doc = MockDoc(result['content'], result['metadata'])
                        result['doc'] = mock_doc
                        result['score'] = result.get('score', 0.5)
                        result['source'] = result.get('source', 'unknown')
                        result['layer'] = result.get('layer', 1)
                        logger.info(f"已修复结果格式: {result}")
                    else:
                        continue
                
                doc = result['doc']
                metadata = getattr(doc, 'metadata', {})
                structure_analysis = result.get('structure_analysis', {})
                
                # 方案A：保留现有字段，同时补充顶层键，确保Web端兼容性
                formatted_result = {
                    'id': metadata.get('table_id', 'unknown'),
                    'content': getattr(doc, 'page_content', ''),
                    'score': result['score'],
                    'source': result.get('source', 'unknown'),  # 修复：使用get方法提供默认值
                    'layer': result.get('layer', 1),  # 修复：使用get方法提供默认值
                    
                    # 新增：顶层字段映射，确保Web端能正确获取table_content
                    'page_content': getattr(doc, 'page_content', ''),  # 原content的别名
                    'document_name': metadata.get('document_name', '未知文档'),
                    'page_number': metadata.get('page_number', '未知页'),
                    'chunk_type': 'table',  # 固定为table类型
                    'table_type': structure_analysis.get('table_type', 'unknown'),
                    'doc_id': metadata.get('table_id') or metadata.get('doc_id') or metadata.get('id', 'unknown'),
                    
                    'metadata': {
                        'document_name': metadata.get('document_name', '未知文档'),
                        'page_number': metadata.get('page_number', '未知页'),
                        'table_type': structure_analysis.get('table_type', 'unknown'),
                        'business_domain': structure_analysis.get('business_domain', 'unknown'),
                        'quality_score': structure_analysis.get('quality_score', 0.0),
                        'is_truncated': structure_analysis.get('is_truncated', False),
                        'truncation_type': structure_analysis.get('truncation_type', 'none'),
                        'truncated_rows': structure_analysis.get('truncated_rows', 0),
                        'current_rows': structure_analysis.get('row_count', 0),
                        'original_rows': structure_analysis.get('original_row_count', 0)
                    }
                }
                
                # 如果有完整表格内容，添加到结果中
                if 'full_content' in result:
                    formatted_result['full_content'] = result['full_content']
                    formatted_result['full_metadata'] = result['full_metadata']
                
                formatted_results.append(formatted_result)
            
            processing_time = time.time() - start_time
            
            # 返回QueryResult对象，与text_engine.py保持一致
            return QueryResult(
                success=True,
                query=query,
                query_type=QueryType.TABLE,
                results=formatted_results,
                total_count=len(formatted_results),
                processing_time=processing_time,
                engine_name=self.name,
                metadata={
                    'total_tables': len(self.table_docs),
                    'pipeline': 'unified_pipeline',  # 标记使用新Pipeline
                    'intent_analysis': intent_analysis,
                    'search_strategy': 'five_layer_recall',
                    'docs_loaded': self._docs_loaded,
                    'vector_store_available': self.vector_store is not None,
                    'document_loader_available': self.document_loader is not None,
                    'llm_answer': getattr(self, '_last_pipeline_result', {}).get('llm_answer', '基于新Pipeline生成的答案'),  # 使用Pipeline生成的答案
                    'recall_count': len(search_results),  # 召回数量
                    'final_count': len(formatted_results),  # 最终结果数量
                    'pipeline_metrics': getattr(self, '_last_pipeline_result', {}).get('pipeline_metrics', {})  # Pipeline指标
                }
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"处理表格查询失败: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            
            return QueryResult(
                success=False,
                query=query,
                query_type=QueryType.TABLE,
                results=[],
                total_count=0,
                processing_time=processing_time,
                engine_name=self.name,
                metadata={},
                error_message=str(e)
            )
    
    def _process_with_new_pipeline(self, query: str, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        使用新的统一Pipeline处理搜索结果
        
        :param query: 查询文本
        :param search_results: 搜索结果
        :return: 处理后的结果
        """
        try:
            logger.info("开始使用新Pipeline处理表格搜索结果")
            
            # 1. 首先进行重排序
            reranked_results = self._rerank_table_results(query, search_results)
            logger.info(f"重排序完成，结果数量: {len(reranked_results)}")
            
            # 调试：验证重排序结果的内容
            for i, result in enumerate(reranked_results):
                if 'doc' in result and result['doc']:
                    doc = result['doc']
                    if 'doc' in doc and doc['doc']:
                        content = getattr(doc['doc'], 'page_content', '')
                        logger.info(f"重排序结果 {i}: 在_process_with_new_pipeline中doc.page_content长度: {len(content)}")
                    else:
                        logger.warning(f"重排序结果 {i}: doc字段结构异常: {list(doc.keys()) if isinstance(doc, dict) else type(doc)}")
                else:
                    logger.warning(f"重排序结果 {i}: 缺少doc字段")
            
            # 2. 使用统一Pipeline处理
            from v2.core.unified_pipeline import UnifiedPipeline
            
            # 获取Pipeline配置
            pipeline_config = {
                'enable_llm_generation': True,
                'enable_source_filtering': True,
                'max_context_results': 10,
                'max_content_length': 1000
            }
            
            # 创建统一Pipeline实例
            # 使用注入的引擎
            if not self.llm_engine:
                logger.warning("LLM引擎未注入，使用Mock引擎")
                # 创建Mock LLM引擎
                class MockLLMEngine:
                    def generate_answer(self, query, context):
                        return f"基于查询'{query}'生成的Mock答案，上下文长度: {len(context)}"
                
                llm_engine = MockLLMEngine()
            else:
                llm_engine = self.llm_engine
            
            if not self.source_filter_engine:
                logger.warning("源过滤引擎未注入，使用Mock引擎")
                # 创建Mock源过滤引擎
                class MockSourceFilterEngine:
                    def filter_sources(self, llm_answer, sources, query):
                        return sources[:5]  # 简单返回前5个源
                
                source_filter_engine = MockSourceFilterEngine()
            else:
                source_filter_engine = self.source_filter_engine
            
            unified_pipeline = UnifiedPipeline(
                config=pipeline_config,
                llm_engine=llm_engine,
                source_filter_engine=source_filter_engine
            )
            
            # 转换结果格式为Pipeline期望的格式
            # 增加输入数量限制，让LLM能看到更多上下文
            max_pipeline_inputs = min(8, len(reranked_results))  # 最多8个输入
            pipeline_input = []
            logger.info(f"开始转换 {len(reranked_results)} 个重排序结果为Pipeline输入格式，限制为 {max_pipeline_inputs} 个")
            
            for i, result in enumerate(reranked_results[:max_pipeline_inputs]):
                logger.info(f"处理结果 {i}: 类型={type(result)}, 键={list(result.keys()) if isinstance(result, dict) else 'N/A'}")
                
                # 处理不同的结果格式
                if 'doc' in result and result['doc']:
                    doc = result['doc']
                    # 检查doc是否是包含doc字段的字典（重排序结果格式）
                    if isinstance(doc, dict) and 'doc' in doc and doc['doc']:
                        # 重排序结果格式：{'doc': {'doc': doc_object, ...}, ...}
                        actual_doc = doc['doc']
                        content = getattr(actual_doc, 'page_content', '')
                        metadata = getattr(actual_doc, 'metadata', {})
                        logger.info(f"结果 {i}: 从重排序结果doc.doc对象提取内容，长度: {len(content)}, 内容预览: {content[:100] if content else '空'}")
                    else:
                        # 直接包含doc对象的情况
                        content = getattr(doc, 'page_content', '')
                        metadata = getattr(doc, 'metadata', {})
                        logger.info(f"结果 {i}: 从doc对象提取内容，长度: {len(content)}, 内容预览: {content[:100] if content else '空'}")
                elif 'content' in result:
                    # 直接包含content的情况
                    content = result['content']
                    metadata = result.get('metadata', {})
                    logger.info(f"结果 {i}: 直接使用content，长度: {len(content)}, 内容预览: {content[:100] if content else '空'}")
                else:
                    logger.warning(f"结果 {i} 格式异常，跳过: {result}")
                    continue
                
                # 构造Pipeline输入
                pipeline_item = {
                    'content': content,
                    'metadata': metadata,
                    'score': result.get('score', 0.5),
                    'source': result.get('source', 'unknown'),
                    'layer': result.get('layer', 1)
                }
                pipeline_input.append(pipeline_item)
                logger.debug(f"结果 {i} 转换完成: score={pipeline_item['score']}, layer={pipeline_item['layer']}")
            
            logger.info(f"Pipeline输入转换完成，共 {len(pipeline_input)} 个有效输入")
            
            # 执行Pipeline处理
            pipeline_result = unified_pipeline.process(query, pipeline_input)
            
            if pipeline_result.success:
                logger.info("新Pipeline处理成功")
                logger.info(f"Pipeline返回结果: llm_answer长度={len(pipeline_result.llm_answer) if pipeline_result.llm_answer else 0}, filtered_sources数量={len(pipeline_result.filtered_sources)}")
                
                # 将Pipeline结果转换为TableEngine期望的格式
                formatted_results = []
                for i, source in enumerate(pipeline_result.filtered_sources):
                    logger.debug(f"处理Pipeline源 {i}: {type(source)}")
                    
                    # 构造标准格式
                    formatted_result = {
                        'id': source.get('metadata', {}).get('table_id', f'table_{i}'),
                        'content': source.get('content', ''),
                        'score': source.get('score', 0.5),
                        'source': source.get('source', 'pipeline'),
                        'layer': source.get('layer', 1),
                        
                        # 顶层字段映射
                        'page_content': source.get('content', ''),
                        'document_name': source.get('metadata', {}).get('document_name', '未知文档'),
                        'page_number': source.get('metadata', {}).get('page_number', '未知页'),
                        'chunk_type': 'table',
                        'table_type': source.get('metadata', {}).get('table_type', 'unknown'),
                        'doc_id': source.get('metadata', {}).get('table_id', f'table_{i}'),
                        
                        'metadata': source.get('metadata', {})
                    }
                    formatted_results.append(formatted_result)
                    logger.debug(f"Pipeline源 {i} 转换完成: id={formatted_result['id']}, content长度={len(formatted_result['content'])}")
                
                # 保存Pipeline结果到实例变量，供后续使用
                self._last_pipeline_result = {
                    'llm_answer': pipeline_result.llm_answer,
                    'filtered_sources': pipeline_result.filtered_sources,
                    'pipeline_metrics': pipeline_result.pipeline_metrics
                }
                
                logger.info(f"新Pipeline处理完成，返回 {len(formatted_results)} 个结果")
                return formatted_results
            else:
                logger.warning(f"新Pipeline处理失败: {pipeline_result.error_message}")
                # 回退到传统方式
                return self._format_results_traditional(search_results)
                
        except Exception as e:
            logger.error(f"新Pipeline处理失败: {e}")
            # 回退到传统方式
            return self._format_results_traditional(search_results)
    
    def _format_results_traditional(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        传统方式格式化结果（作为新Pipeline的回退方案）
        
        :param search_results: 搜索结果
        :return: 格式化后的结果
        """
        logger.info("使用传统方式格式化结果")
        formatted_results = []
        
        for result in search_results:
            # 修复：处理重排序后可能没有'doc'键的情况
            if 'doc' not in result:
                logger.warning(f"跳过无效结果，缺少'doc'键: {result}")
                # 尝试修复结果格式
                if isinstance(result, dict) and 'content' in result and 'metadata' in result:
                    # 构造一个模拟的doc对象
                    class MockDoc:
                        def __init__(self, content, metadata):
                            self.page_content = content
                            self.metadata = metadata
                    
                    mock_doc = MockDoc(result['content'], result['metadata'])
                    result['doc'] = mock_doc
                    result['score'] = result.get('score', 0.5)
                    result['source'] = result.get('source', 'unknown')
                    result['layer'] = result.get('layer', 1)
                    logger.info(f"已修复结果格式: {result}")
                else:
                    continue
            
            doc = result['doc']
            metadata = getattr(doc, 'metadata', {})
            structure_analysis = result.get('structure_analysis', {})
            
            # 方案A：保留现有字段，同时补充顶层键，确保Web端兼容性
            formatted_result = {
                'id': metadata.get('table_id', 'unknown'),
                'content': getattr(doc, 'page_content', ''),
                'score': result['score'],
                'source': result.get('source', 'unknown'),
                'layer': result.get('layer', 1),
                
                # 新增：顶层字段映射，确保Web端能正确获取table_content
                'page_content': getattr(doc, 'page_content', ''),
                'document_name': metadata.get('document_name', '未知文档'),
                'page_number': metadata.get('page_number', '未知页'),
                'chunk_type': 'table',
                'table_type': structure_analysis.get('table_type', 'unknown'),
                'doc_id': metadata.get('table_id') or metadata.get('doc_id') or metadata.get('id', 'unknown'),
                
                'metadata': {
                    'document_name': metadata.get('document_name', '未知文档'),
                    'page_number': metadata.get('page_number', '未知页'),
                    'table_type': structure_analysis.get('table_type', 'unknown'),
                    'business_domain': structure_analysis.get('business_domain', 'unknown'),
                    'quality_score': structure_analysis.get('quality_score', 0.0),
                    'is_truncated': structure_analysis.get('is_truncated', False),
                    'truncation_type': structure_analysis.get('truncation_type', 'none'),
                    'truncated_rows': structure_analysis.get('truncated_rows', 0),
                    'current_rows': structure_analysis.get('row_count', 0),
                    'original_rows': structure_analysis.get('original_row_count', 0)
                }
            }
            
            # 如果有完整表格内容，添加到结果中
            if 'full_content' in result:
                formatted_result['full_content'] = result['full_content']
                formatted_result['full_metadata'] = result['full_metadata']
            
            formatted_results.append(formatted_result)
        
        return formatted_results
    
    def _search_tables(self, query: str) -> List[Dict[str, Any]]:
        """
        执行表格搜索 - 新的五层召回策略（与Text/Image Engine保持一致）
        
        :param query: 查询文本
        :return: 搜索结果列表
        """
        # 🔍 诊断信息：检查系统状态
        logger.info("=" * 50)
        logger.info("🔍 开始诊断五层召回策略")
        logger.info(f"查询文本: {query}")
        logger.info(f"向量数据库状态: {self.vector_store}")
        logger.info(f"表格文档缓存数量: {len(self.table_docs)}")
        logger.info(f"文档加载状态: {self._docs_loaded}")
        
        # 检查向量数据库详细信息
        if self.vector_store:
            logger.info(f"向量数据库属性: {dir(self.vector_store)}")
            if hasattr(self.vector_store, 'docstore'):
                logger.info(f"docstore类型: {type(self.vector_store.docstore)}")
                if hasattr(self.vector_store.docstore, '_dict'):
                    logger.info(f"docstore._dict长度: {len(self.vector_store.docstore._dict)}")
                    # 显示前几个文档的元数据
                    doc_count = 0
                    for doc_id, doc in list(self.vector_store.docstore._dict.items())[:3]:
                        logger.info(f"文档 {doc_count}: ID={doc_id}, 类型={type(doc)}")
                        if hasattr(doc, 'metadata'):
                            logger.info(f"  元数据: {doc.metadata}")
                        if hasattr(doc, 'page_content'):
                            logger.info(f"  内容长度: {len(doc.page_content)}")
                        doc_count += 1
                else:
                    logger.warning("❌ docstore没有_dict属性")
            else:
                logger.warning("❌ 向量数据库没有docstore属性")
        else:
            logger.error("❌ 向量数据库为空！")
        
        logger.info("=" * 50)
        
        all_results = []
        min_required = getattr(self.config, 'min_required_results', 20)
        max_recall_results = getattr(self.config, 'max_recall_results', 150)
        
        logger.info(f"开始执行五层召回策略，查询: {query}")
        
        # 第一层：表格结构精确匹配（高精度，低召回）
        logger.info("执行第一层：表格结构精确匹配")
        layer1_results = self._table_structure_precise_search(query, top_k=30)
        all_results.extend(layer1_results)
        logger.info(f"✅ 第一层结构搜索成功，召回 {len(layer1_results)} 个结果")
        
        # 第二层：向量语义搜索（中等精度，中等召回）
        logger.info("执行第二层：向量语义搜索")
        layer2_results = self._enhanced_vector_search(query, top_k=40)
        all_results.extend(layer2_results)
        logger.info(f"✅ 第二层向量搜索成功，召回 {len(layer2_results)} 个结果")
        
        # 第三层：表格内容关键词匹配（中等精度，高召回）
        logger.info("执行第三层：表格内容关键词匹配")
        layer3_results = self._enhanced_content_keyword_search(query, top_k=35)
        all_results.extend(layer3_results)
        logger.info(f"✅ 第三层关键词搜索成功，召回 {len(layer3_results)} 个结果")
        
        # 第四层：混合智能搜索（中等精度，高召回）
        logger.info("执行第四层：混合智能搜索")
        layer4_results = self._enhanced_hybrid_search(query, top_k=30)
        all_results.extend(layer4_results)
        logger.info(f"✅ 第四层混合搜索成功，召回 {len(layer4_results)} 个结果")
        
        # 检查前四层结果数量，决定是否激活第五层
        total_results = len(all_results)
        logger.info(f"前四层总结果数量: {total_results}")
        
        if total_results >= min_required:
            logger.info(f"前四层召回数量充足({total_results} >= {min_required})，跳过第五层")
        else:
            # 第五层：容错扩展搜索（兜底策略）
            logger.warning(f"前四层召回数量不足({total_results} < {min_required})，激活第五层")
            layer5_results = self._fault_tolerant_expansion_search(query, top_k=25)
            all_results.extend(layer5_results)
            logger.info(f"第五层返回 {len(layer5_results)} 个结果")
        
        # 结果融合与去重
        logger.info("开始结果融合与去重")
        final_results = self._merge_and_deduplicate_results(all_results)
        
        # 最终排序
        final_results = self._final_ranking(query, final_results)
        
        # 限制最终结果数量
        max_results = getattr(self.config, 'max_results', 10)
        final_results = final_results[:max_results]
        
        logger.info(f"五层召回策略完成，最终结果数量: {len(final_results)}")
        return final_results
    
    def _table_structure_precise_search(self, query: str, top_k: int = 30) -> List[Dict[str, Any]]:
        """
        第一层：表格结构精确匹配（高精度，低召回）
        
        基于表格的结构特征进行精确匹配：
        1. 表格标题匹配
        2. 列名精确匹配
        3. 表格类型匹配
        4. 表格内容结构分析
        
        :param query: 查询文本
        :param top_k: 最大结果数
        :return: 搜索结果列表
        """
        results = []
        
        try:
            logger.info(f"第一层结构搜索 - 查询: {query}, 目标数量: {top_k}")
            
            # 1. 表格标题精确匹配
            title_matches = self._search_by_table_title(query, top_k // 3)
            results.extend(title_matches)
            logger.info(f"标题匹配结果: {len(title_matches)} 个")
            
            # 2. 列名精确匹配
            column_matches = self._search_by_column_names(query, top_k // 3)
            results.extend(column_matches)
            logger.info(f"列名匹配结果: {len(column_matches)} 个")
            
            # 3. 表格类型匹配
            type_matches = self._search_by_table_type(query, top_k // 3)
            results.extend(type_matches)
            logger.info(f"类型匹配结果: {len(type_matches)} 个")
            
            # 4. 表格内容结构分析
            structure_matches = self._search_by_table_structure(query, top_k // 3)
            results.extend(structure_matches)
            logger.info(f"结构匹配结果: {len(structure_matches)} 个")
            
            # 去重和排序
            unique_results = self._deduplicate_by_doc_id(results)
            sorted_results = sorted(unique_results, key=lambda x: x.get('structure_score', 0), reverse=True)
            
            # 限制结果数量
            final_results = sorted_results[:top_k]
            
            logger.info(f"✅ 第一层结构搜索完成，返回 {len(final_results)} 个结果")
            return final_results
            
        except Exception as e:
            logger.error(f"第一层结构搜索失败: {e}")
            return []
    
    def _search_by_table_title(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """基于表格标题搜索"""
        results = []
        
        try:
            # 提取查询中的关键概念
            query_keywords = self._extract_keywords(query)
            
            for table_doc in self.table_docs:
                if not hasattr(table_doc, 'metadata'):
                    continue
                
                metadata = table_doc.metadata
                table_title = metadata.get('table_title', '')
                
                if not table_title:
                    continue
                
                # 计算标题匹配分数
                title_score = self._calculate_title_similarity(query_keywords, table_title)
                
                if title_score > 0.6:  # 标题匹配阈值
                    results.append({
                        'doc': table_doc,
                        'score': title_score,
                        'source': 'structure_search',
                        'layer': 1,
                        'search_method': 'title_match',
                        'structure_score': title_score,
                        'match_details': f"标题匹配: {table_title}"
                    })
            
            # 按分数排序并限制数量
            sorted_results = sorted(results, key=lambda x: x.get('score', 0), reverse=True)
            return sorted_results[:max_results]
            
        except Exception as e:
            logger.error(f"标题搜索失败: {e}")
            return []
    
    def _search_by_column_names(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """基于列名搜索"""
        results = []
        
        try:
            # 提取查询中的关键概念
            query_keywords = self._extract_keywords(query)
            
            for table_doc in self.table_docs:
                if not hasattr(table_doc, 'metadata'):
                    continue
                
                metadata = table_doc.metadata
                table_headers = metadata.get('table_headers', [])
                
                if not table_headers:
                    continue
                
                # 计算列名匹配分数
                column_score = self._calculate_column_similarity(query_keywords, table_headers)
                
                if column_score > 0.5:  # 列名匹配阈值
                    results.append({
                        'doc': table_doc,
                        'score': column_score,
                        'source': 'structure_search',
                        'layer': 1,
                        'search_method': 'column_match',
                        'structure_score': column_score,
                        'match_details': f"列名匹配: {', '.join(table_headers[:3])}"
                    })
            
            # 按分数排序并限制数量
            sorted_results = sorted(results, key=lambda x: x.get('score', 0), reverse=True)
            return sorted_results[:max_results]
            
        except Exception as e:
            logger.error(f"列名搜索失败: {e}")
            return []
    
    def _search_by_table_type(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """基于表格类型搜索"""
        results = []
        
        try:
            # 分析查询意图，判断表格类型
            query_intent = self._analyze_query_intent(query)
            
            for table_doc in self.table_docs:
                if not hasattr(table_doc, 'metadata'):
                    continue
                
                metadata = table_doc.metadata
                table_type = metadata.get('table_type', '')
                
                if not table_type:
                    continue
                
                # 计算类型匹配分数
                type_score = self._calculate_type_similarity(query_intent, table_type)
                
                if type_score > 0.4:  # 类型匹配阈值
                    results.append({
                        'doc': table_doc,
                        'score': type_score,
                        'source': 'structure_search',
                        'layer': 1,
                        'search_method': 'type_match',
                        'structure_score': type_score,
                        'match_details': f"类型匹配: {table_type}"
                    })
            
            # 按分数排序并限制数量
            sorted_results = sorted(results, key=lambda x: x.get('score', 0), reverse=True)
            return sorted_results[:max_results]
            
        except Exception as e:
            logger.error(f"类型搜索失败: {e}")
            return []
    
    def _search_by_table_structure(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """基于表格结构搜索"""
        results = []
        
        try:
            # 分析查询对表格结构的要求
            structure_requirements = self._analyze_structure_requirements(query)
            
            for table_doc in self.table_docs:
                if not hasattr(table_doc, 'metadata'):
                    continue
                
                metadata = table_doc.metadata
                row_count = metadata.get('table_row_count', 0)
                column_count = metadata.get('table_column_count', 0)
                
                # 计算结构匹配分数
                structure_score = self._calculate_structure_similarity(structure_requirements, row_count, column_count)
                
                if structure_score > 0.3:  # 结构匹配阈值
                    results.append({
                        'doc': table_doc,
                        'score': structure_score,
                        'source': 'structure_search',
                        'layer': 1,
                        'search_method': 'structure_match',
                        'structure_score': structure_score,
                        'match_details': f"结构匹配: {row_count}行×{column_count}列"
                    })
            
            # 按分数排序并限制数量
            sorted_results = sorted(results, key=lambda x: x.get('score', 0), reverse=True)
            return sorted_results[:max_results]
            
        except Exception as e:
            logger.error(f"结构搜索失败: {e}")
            return []
    
    def _calculate_search_k(self, target_k: int, layer_config) -> int:
        """
        智能计算搜索范围，用于post-filter策略
        
        :param target_k: 目标结果数量
        :param layer_config: 层级配置对象
        :return: 搜索范围
        """
        try:
            if hasattr(layer_config, 'top_k'):
                base_top_k = layer_config.top_k
            else:
                base_top_k = 40
            if hasattr(layer_config, 'similarity_threshold'):
                similarity_threshold = layer_config.similarity_threshold
            else:
                similarity_threshold = 0.65
            
            # 根据阈值动态调整搜索范围
            if similarity_threshold < 0.3:
                # 低阈值，需要搜索更多候选结果
                search_k = max(target_k * 4, base_top_k * 2)
            elif similarity_threshold < 0.6:
                # 中等阈值
                search_k = max(target_k * 3, base_top_k * 1.5)
            else:
                # 高阈值，可以搜索较少候选结果
                search_k = max(target_k * 2, base_top_k)
            
            # 设置上限避免过度搜索
            search_k = min(search_k, 150)
            
            logger.info(f"智能计算search_k: 目标{target_k}, 基础top_k{base_top_k}, 阈值{similarity_threshold}, 最终search_k{search_k}")
            return search_k
            
        except Exception as e:
            logger.error(f"计算search_k失败: {e}")
            # 返回安全的默认值
            return max(target_k * 3, 80)

    def _enhanced_vector_search(self, query: str, top_k: int = 40) -> List[Dict[str, Any]]:
        """
        第二层：增强的向量语义搜索（中等精度，中等召回），支持post-filter策略
        
        利用多种向量化策略进行表格召回：
        1. 策略1：尝试使用FAISS filter直接搜索
        2. 策略2：使用post-filter策略（先搜索更多结果，然后过滤）
        3. 策略3：备选方案（如果前两种都失败）
        
        :param query: 查询文本
        :param top_k: 最大结果数
        :return: 搜索结果列表
        """
        results = []
        
        if not self.vector_store or not getattr(self.config, 'enable_vector_search', True):
            logger.info("向量搜索未启用或向量数据库不可用")
            return results
        
        try:
            # 获取第二层配置
            layer2_config = getattr(self.config, 'recall_strategy', {}).get('layer2_vector_search', {})
            if hasattr(layer2_config, 'similarity_threshold'):
                threshold = layer2_config.similarity_threshold
            else:
                threshold = 0.65
            if hasattr(layer2_config, 'top_k'):
                base_top_k = layer2_config.top_k
            else:
                base_top_k = 40
            
            # 智能计算搜索范围
            search_k = self._calculate_search_k(top_k, layer2_config)
            
            logger.info(f"第二层向量搜索 - 查询: {query}, 阈值: {threshold}, 目标数量: {top_k}, 搜索范围: {search_k}")
            
            # 策略1：尝试使用FAISS filter直接搜索table类型文档
            logger.info("策略1：尝试使用FAISS filter直接搜索table类型文档")
            try:
                content_results = self.vector_store.similarity_search(
                    query, 
                    k=top_k,
                    filter={'chunk_type': 'table'}  # 尝试使用filter
                )
                
                logger.info(f"✅ 策略1 filter搜索成功，返回 {len(content_results)} 个结果")
                
                # 处理filter搜索结果
                for doc in content_results:
                    if not hasattr(doc, 'metadata'):
                        continue
                    
                    # 获取相似度分数
                    score = getattr(doc, 'score', 0.5)
                    
                    # 应用阈值过滤
                    if score >= threshold:
                        results.append({
                            'doc': doc,
                            'score': score,
                            'source': 'vector_search',
                            'layer': 2,
                            'search_method': 'content_semantic_similarity_filter',
                            'vector_score': score,
                            'match_details': 'processed_table_content语义匹配(filter)'
                        })
                
                logger.info(f"策略1通过阈值检查的结果数量: {len(results)}")
                
                # 如果filter搜索返回足够的结果，直接返回
                if len(results) >= top_k * 0.8:  # 80%的目标数量
                    return results[:top_k]
                    
            except Exception as e:
                logger.warning(f"策略1 filter搜索失败: {e}")
                logger.info("降级到post-filter策略")
            
            # 策略2：使用post-filter策略（先搜索更多结果，然后过滤）
            logger.info("策略2：使用post-filter策略（先搜索更多结果，然后过滤）")
            
            # 搜索更多候选结果用于后过滤
            all_candidates = self.vector_store.similarity_search(
                query, 
                k=search_k
            )
            
            logger.info(f"策略2搜索返回 {len(all_candidates)} 个候选结果")
            
            # 后过滤：筛选出table类型的文档
            table_candidates = []
            for doc in all_candidates:
                if (hasattr(doc, 'metadata') and doc.metadata and 
                    doc.metadata.get('chunk_type') == 'table'):
                    table_candidates.append(doc)
            
            logger.info(f"后过滤后找到 {len(table_candidates)} 个table文档")
            
            # 处理table搜索结果，应用阈值过滤
            for doc in table_candidates:
                # 获取相似度分数
                score = getattr(doc, 'score', 0.5)
                
                # 应用阈值过滤
                if score >= threshold:
                    results.append({
                        'doc': doc,
                        'score': score,
                        'source': 'vector_search',
                        'layer': 2,
                        'search_method': 'content_semantic_similarity_post_filter',
                        'vector_score': score,
                        'match_details': 'processed_table_content语义匹配(post-filter)'
                    })
            
            logger.info(f"策略2通过阈值检查的结果数量: {len(results)}")
            
            # 按分数排序并限制数量
            results.sort(key=lambda x: x['score'], reverse=True)
            final_results = results[:top_k]
            
            logger.info(f"✅ 策略2 post-filter成功，返回 {len(final_results)} 个结果")
            return final_results
            
        except Exception as e:
            logger.error(f"第二层向量搜索失败: {e}")
            return []
    
    def _enhanced_content_keyword_search(self, query: str, top_k: int = 35) -> List[Dict[str, Any]]:
        """
        第三层：表格内容关键词匹配（中等精度，高召回）
        
        基于表格内容的关键词匹配策略：
        1. 表格标题关键词匹配
        2. 列名关键词匹配
        3. 表格内容关键词匹配
        4. 表格摘要关键词匹配
        
        :param query: 查询文本
        :param top_k: 最大结果数
        :return: 搜索结果列表
        """
        results = []
        
        try:
            logger.info(f"第三层关键词搜索 - 查询: {query}, 目标数量: {top_k}")
            
            # 提取查询关键词
            query_keywords = self._extract_keywords(query)
            logger.info(f"提取的查询关键词: {query_keywords}")
            
            for table_doc in self.table_docs:
                if not hasattr(table_doc, 'metadata'):
                    continue
                
                metadata = table_doc.metadata
                
                # 计算关键词匹配分数
                keyword_score = self._calculate_keyword_match_score(query_keywords, metadata)
                
                if keyword_score > 0.3:  # 关键词匹配阈值
                    results.append({
                        'doc': table_doc,
                        'score': keyword_score,
                        'source': 'keyword_search',
                        'layer': 3,
                        'search_method': 'keyword_match',
                        'keyword_score': keyword_score,
                        'match_details': f"关键词匹配分数: {keyword_score:.2f}"
                    })
            
            # 按分数排序并限制数量
            sorted_results = sorted(results, key=lambda x: x.get('score', 0), reverse=True)
            final_results = sorted_results[:top_k]
            
            logger.info(f"✅ 第三层关键词搜索完成，返回 {len(final_results)} 个结果")
            return final_results
            
        except Exception as e:
            logger.error(f"第三层关键词搜索失败: {e}")
            return []
    
    def _enhanced_hybrid_search(self, query: str, top_k: int = 30) -> List[Dict[str, Any]]:
        """
        第四层：混合智能搜索（中等精度，高召回）
        
        结合多种搜索策略的混合方法：
        1. 结构特征 + 内容特征的组合评分
        2. 表格质量评估
        3. 查询意图分析
        4. 动态权重调整
        
        :param query: 查询文本
        :param top_k: 最大结果数
        :return: 搜索结果列表
        """
        results = []
        
        try:
            logger.info(f"第四层混合搜索 - 查询: {query}, 目标数量: {top_k}")
            
            # 分析查询意图
            query_intent = self._analyze_query_intent(query)
            logger.info(f"查询意图分析: {query_intent}")
            
            for table_doc in self.table_docs:
                if not hasattr(table_doc, 'metadata'):
                    continue
                
                metadata = table_doc.metadata
                
                # 计算混合评分
                hybrid_score = self._calculate_hybrid_score(query, query_intent, metadata)
                
                if hybrid_score > 0.2:  # 混合搜索阈值
                    results.append({
                        'doc': table_doc,
                        'score': hybrid_score,
                        'source': 'hybrid_search',
                        'layer': 4,
                        'search_method': 'hybrid_intelligent',
                        'hybrid_score': hybrid_score,
                        'match_details': f"混合评分: {hybrid_score:.2f}"
                    })
            
            # 按分数排序并限制数量
            sorted_results = sorted(results, key=lambda x: x.get('score', 0), reverse=True)
            final_results = sorted_results[:top_k]
            
            logger.info(f"✅ 第四层混合搜索完成，返回 {len(final_results)} 个结果")
            return final_results
            
        except Exception as e:
            logger.error(f"第四层混合搜索失败: {e}")
            return []
    
    def _fault_tolerant_expansion_search(self, query: str, top_k: int = 25) -> List[Dict[str, Any]]:
        """
        第五层：容错扩展搜索（兜底策略）
        
        当其他层召回不足时的兜底策略：
        1. 模糊匹配
        2. 部分关键词匹配
        3. 表格类型泛化
        4. 降级阈值匹配
        
        :param query: 查询文本
        :param top_k: 最大结果数
        :return: 搜索结果列表
        """
        results = []
        
        try:
            logger.info(f"第五层容错扩展搜索 - 查询: {query}, 目标数量: {top_k}")
            
            # 提取查询关键词（更宽松的提取）
            query_keywords = self._extract_keywords_relaxed(query)
            logger.info(f"宽松提取的查询关键词: {query_keywords}")
            
            for table_doc in self.table_docs:
                if not hasattr(table_doc, 'metadata'):
                    continue
                
                metadata = table_doc.metadata
                
                # 计算容错评分（更宽松的阈值）
                fault_tolerant_score = self._calculate_fault_tolerant_score(query_keywords, metadata)
                
                if fault_tolerant_score > 0.1:  # 容错搜索阈值（很低）
                    results.append({
                        'doc': table_doc,
                        'score': fault_tolerant_score,
                        'source': 'fault_tolerant_search',
                        'layer': 5,
                        'search_method': 'fault_tolerant_expansion',
                        'fault_tolerant_score': fault_tolerant_score,
                        'match_details': f"容错评分: {fault_tolerant_score:.2f}"
                    })
            
            # 按分数排序并限制数量
            sorted_results = sorted(results, key=lambda x: x.get('score', 0), reverse=True)
            final_results = sorted_results[:top_k]
            
            logger.info(f"✅ 第五层容错扩展搜索完成，返回 {len(final_results)} 个结果")
            return final_results
            
        except Exception as e:
            logger.error(f"第五层容错扩展搜索失败: {e}")
            return []
    
    def _merge_and_deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        结果融合与去重
        
        :param results: 原始结果列表
        :return: 去重排序后的结果列表
        """
        if not results:
            return []
        
        try:
            # 去重（基于文档ID）
            seen_docs = set()
            unique_results = []
            
            for result in results:
                doc_id = result['doc'].metadata.get('id', id(result['doc']))
                if doc_id not in seen_docs:
                    seen_docs.add(doc_id)
                    unique_results.append(result)
                else:
                    # 如果文档已存在，选择分数更高的结果
                    existing_result = next(r for r in unique_results if r['doc'].metadata.get('id', id(r['doc'])) == doc_id)
                    if result['score'] > existing_result['score']:
                        # 替换为分数更高的结果
                        unique_results.remove(existing_result)
                        unique_results.append(result)
            
            # 层间权重调整
            for result in unique_results:
                layer = result.get('layer', 1)
                # 根据层级调整分数，层级越低分数越高
                layer_weight = 1.0 / layer
                result['adjusted_score'] = result['score'] * layer_weight
            
            # 按调整后的分数排序
            unique_results.sort(key=lambda x: x.get('adjusted_score', x['score']), reverse=True)
            
            logger.info(f"去重后剩余 {len(unique_results)} 个唯一结果")
            return unique_results
            
        except Exception as e:
            logger.error(f"去重和排序失败: {e}")
            # 降级处理：简单排序
            return sorted(results, key=lambda x: x['score'], reverse=True)
    
    def _final_ranking(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        最终排序
        
        :param query: 查询文本
        :param results: 原始结果列表
        :return: 最终排序后的结果列表
        """
        try:
            if not results:
                return []
            
            # 简单的排序：按分数排序即可
            sorted_results = sorted(results, key=lambda x: x.get('score', 0), reverse=True)
            
            # 添加排名信息
            for i, result in enumerate(sorted_results):
                result['final_rank'] = i + 1
                result['final_score'] = result.get('score', 0.0)
            
            logger.info(f"最终排序完成，结果数量: {len(sorted_results)}")
            return sorted_results
            
        except Exception as e:
            logger.error(f"最终排序失败: {e}")
            return results
    

    
    def _initialize_recall_strategy(self):
        """初始化五层召回策略"""
        try:
            # 检查必要的配置项
            if not hasattr(self.config, 'use_new_pipeline'):
                logger.warning("未配置use_new_pipeline，默认启用")
            
            if not hasattr(self.config, 'enable_enhanced_reranking'):
                logger.warning("未配置enable_enhanced_reranking，默认启用")
            
            logger.info("五层召回策略初始化完成")
            
        except Exception as e:
            logger.error(f"初始化召回策略失败: {e}")
    
    def clear_cache(self):
        """清理表格引擎缓存"""
        self.table_docs = []
        self._docs_loaded = False
        logger.info("表格引擎缓存已清理")

    def _analyze_table_structure(self, doc):
        """
        简化版表格结构分析
        
        :param doc: 表格文档
        :return: 表格结构分析结果
        """
        try:
            analysis = {
                'table_type': 'unknown',
                'columns': [],
                'row_count': 0,
                'column_count': 0,
                'quality_score': 0.0
            }
            
            # 从元数据中提取基本信息
            metadata = getattr(doc, 'metadata', {})
            if metadata:
                analysis['columns'] = metadata.get('table_headers', [])
                analysis['row_count'] = metadata.get('table_row_count', 0)
                analysis['column_count'] = metadata.get('table_column_count', 0)
                analysis['table_type'] = metadata.get('table_type', 'unknown')
            
            # 计算简单的质量评分
            if analysis['row_count'] > 0 and analysis['column_count'] > 0:
                analysis['quality_score'] = min(1.0, (analysis['row_count'] + analysis['column_count']) / 20.0)
            
            return analysis
            
        except Exception as e:
            logger.error(f"表格结构分析失败: {e}")
            return {
                'table_type': 'unknown',
                'columns': [],
                'row_count': 0,
                'column_count': 0,
                'quality_score': 0.0
            }
    


    def get_full_table(self, table_id: str) -> Dict[str, Any]:
        """
        获取完整表格内容（未截断版本）
        
        :param table_id: 表格ID
        :return: 完整表格内容字典
        """
        try:
            # 首先尝试从文档加载器获取完整表格
            if self.document_loader:
                full_doc = self.document_loader.get_full_document_by_id(table_id, chunk_type='table')
                if full_doc:
                    logger.info(f"从文档加载器获取完整表格 {table_id} 成功")
                    return {
                        'status': 'success',
                        'table_id': table_id,
                        'content': getattr(full_doc, 'page_content', ''),
                        'metadata': getattr(full_doc, 'metadata', {}),
                        'message': '完整表格内容从文档加载器获取成功'
                    }
            
            # 如果没有文档加载器或获取失败，尝试从向量存储获取
            if self.vector_store:
                full_doc = self.vector_store.get_full_document_by_id(table_id)
                if full_doc:
                    logger.info(f"从向量存储获取完整表格 {table_id} 成功")
                    return {
                        'status': 'success',
                        'table_id': table_id,
                        'content': getattr(full_doc, 'page_content', ''),
                        'metadata': getattr(full_doc, 'metadata', {}),
                        'message': '完整表格内容从向量存储获取成功'
                    }
            
            # 如果都没有找到，返回错误信息
            logger.warning(f"无法获取完整表格 {table_id}")
            return {
                'status': 'error',
                'table_id': table_id,
                'content': '',
                'metadata': {},
                'message': f'无法获取完整表格 {table_id}，可能是因为没有完整数据或没有配置文档加载器/向量存储'
            }
            
        except Exception as e:
            logger.error(f"获取完整表格 {table_id} 失败: {e}")
            return {
                'status': 'error',
                'table_id': table_id,
                'content': '',
                'metadata': {},
                'message': f'获取完整表格失败: {str(e)}'
            }

    def _extract_keywords(self, text: str) -> List[str]:
        """提取文本关键词"""
        try:
            if not text:
                return []
            
            # 简单的关键词提取（可以后续优化为更复杂的NLP方法）
            text_lower = text.lower()
            
            # 移除标点符号
            text_clean = re.sub(r'[^\w\s]', ' ', text_lower)
            
            # 分词
            words = text_clean.split()
            
            # 过滤停用词和短词
            stop_words = {'的', '是', '在', '有', '和', '与', '或', '但', '而', '如果', '那么', '因为', '所以', '什么', '怎么', '如何', '哪些', '什么', '多少', '几', '个', '年', '月', '日', '时', '分', '秒'}
            keywords = [word for word in words if len(word) > 1 and word not in stop_words]
            
            # 去重并限制数量
            unique_keywords = list(set(keywords))[:20]
            
            return unique_keywords
            
        except Exception as e:
            logger.error(f"关键词提取失败: {e}")
            return []
    
    def _extract_keywords_relaxed(self, text: str) -> List[str]:
        """宽松的关键词提取（用于容错搜索）"""
        try:
            if not text:
                return []
            
            # 更宽松的关键词提取
            text_lower = text.lower()
            
            # 移除标点符号
            text_clean = re.sub(r'[^\w\s]', ' ', text_lower)
            
            # 分词
            words = text_clean.split()
            
            # 只过滤非常短的词
            keywords = [word for word in words if len(word) > 0]
            
            # 去重
            unique_keywords = list(set(keywords))
            
            return unique_keywords
            
        except Exception as e:
            logger.error(f"宽松关键词提取失败: {e}")
            return []
    
    def _calculate_title_similarity(self, query_keywords: List[str], table_title: str) -> float:
        """计算标题相似度分数"""
        try:
            if not table_title or not query_keywords:
                return 0.0
            
            title_lower = table_title.lower()
            title_words = set(title_lower.split())
            
            # 计算关键词匹配度
            matched_keywords = sum(1 for kw in query_keywords if kw.lower() in title_words)
            
            if matched_keywords == 0:
                return 0.0
            
            # 计算相似度分数
            similarity = min(1.0, matched_keywords / len(query_keywords))
            
            return similarity
            
        except Exception as e:
            logger.error(f"标题相似度计算失败: {e}")
            return 0.0
    
    def _calculate_column_similarity(self, query_keywords: List[str], table_headers: List[str]) -> float:
        """计算列名相似度分数"""
        try:
            if not table_headers or not query_keywords:
                return 0.0
            
            # 计算每个列名的匹配分数
            column_scores = []
            
            for header in table_headers:
                if not isinstance(header, str):
                    continue
                
                header_lower = header.lower()
                header_words = set(header_lower.split())
                
                # 计算关键词匹配度
                matched_keywords = sum(1 for kw in query_keywords if kw.lower() in header_words)
                
                if matched_keywords > 0:
                    similarity = min(1.0, matched_keywords / len(query_keywords))
                    column_scores.append(similarity)
            
            if not column_scores:
                return 0.0
            
            # 返回最高分数
            return max(column_scores)
            
        except Exception as e:
            logger.error(f"列名相似度计算失败: {e}")
            return 0.0
    
    def _calculate_type_similarity(self, query_intent: Dict[str, Any], table_type: str) -> float:
        """计算类型相似度分数"""
        try:
            if not table_type or not query_intent:
                return 0.0
            
            table_type_lower = table_type.lower()
            query_type = query_intent.get('query_type', 'unknown')
            business_domain = query_intent.get('business_domain', 'unknown')
            
            score = 0.0
            
            # 查询类型匹配
            if query_type != 'unknown':
                if query_type in table_type_lower:
                    score += 0.5
                elif any(word in table_type_lower for word in query_type.split('_')):
                    score += 0.3
            
            # 业务领域匹配
            if business_domain != 'unknown':
                if business_domain in table_type_lower:
                    score += 0.3
                elif any(word in table_type_lower for word in business_domain.split('_')):
                    score += 0.2
            
            return min(1.0, score)
            
        except Exception as e:
            logger.error(f"类型相似度计算失败: {e}")
            return 0.0
    
    def _calculate_structure_similarity(self, requirements: Dict[str, Any], row_count: int, column_count: int) -> float:
        """计算结构相似度分数"""
        try:
            if not requirements:
                return 0.0
            
            score = 0.0
            
            # 行数匹配
            min_rows = requirements.get('min_rows', 1)
            max_rows = requirements.get('max_rows', 1000)
            
            if min_rows <= row_count <= max_rows:
                score += 0.5
            elif row_count > 0:
                # 部分匹配
                if row_count >= min_rows * 0.5:
                    score += 0.3
                elif row_count <= max_rows * 1.5:
                    score += 0.2
            
            # 列数匹配
            min_columns = requirements.get('min_columns', 1)
            max_columns = requirements.get('max_columns', 20)
            
            if min_columns <= column_count <= max_columns:
                score += 0.5
            elif column_count > 0:
                # 部分匹配
                if column_count >= min_columns * 0.5:
                    score += 0.3
                elif column_count <= max_columns * 1.5:
                    score += 0.2
            
            return min(1.0, score)
            
        except Exception as e:
            logger.error(f"结构相似度计算失败: {e}")
            return 0.0
    
    def _calculate_keyword_match_score(self, query_keywords: List[str], metadata: Dict[str, Any]) -> float:
        """计算关键词匹配分数"""
        try:
            if not query_keywords or not metadata:
                return 0.0
            
            score = 0.0
            
            # 表格标题关键词匹配
            table_title = metadata.get('table_title', '')
            if table_title:
                title_score = self._calculate_title_similarity(query_keywords, table_title)
                score += title_score * 0.4  # 标题权重40%
            
            # 列名关键词匹配
            table_headers = metadata.get('table_headers', [])
            if table_headers:
                column_score = self._calculate_column_similarity(query_keywords, table_headers)
                score += column_score * 0.4  # 列名权重40%
            
            # 表格摘要关键词匹配
            table_summary = metadata.get('table_summary', '')
            if table_summary:
                summary_score = self._calculate_title_similarity(query_keywords, table_summary)
                score += summary_score * 0.2  # 摘要权重20%
            
            return min(1.0, score)
            
        except Exception as e:
            logger.error(f"关键词匹配分数计算失败: {e}")
            return 0.0
    
    def _calculate_hybrid_score(self, query: str, query_intent: Dict[str, Any], metadata: Dict[str, Any]) -> float:
        """计算混合评分"""
        try:
            if not metadata:
                return 0.0
            
            score = 0.0
            
            # 结构特征评分
            structure_score = 0.0
            
            # 表格类型匹配
            table_type = metadata.get('table_type', '')
            if table_type:
                type_score = self._calculate_type_similarity(query_intent, table_type)
                structure_score += type_score * 0.3
            
            # 表格结构匹配
            row_count = metadata.get('table_row_count', 0)
            column_count = metadata.get('table_column_count', 0)
            if row_count > 0 and column_count > 0:
                structure_requirements = self._analyze_structure_requirements(query)
                struct_score = self._calculate_structure_similarity(structure_requirements, row_count, column_count)
                structure_score += struct_score * 0.3
            
            # 表格质量评分
            quality_score = 0.0
            if row_count > 5 and column_count > 2:
                quality_score = 0.4  # 基础质量分数
            
            # 最终混合分数
            score = (structure_score * 0.6) + (quality_score * 0.4)
            
            return min(1.0, score)
            
        except Exception as e:
            logger.error(f"混合评分计算失败: {e}")
            return 0.0
    
    def _calculate_fault_tolerant_score(self, query_keywords: List[str], metadata: Dict[str, Any]) -> float:
        """计算容错评分（更宽松的阈值）"""
        try:
            if not query_keywords or not metadata:
                return 0.0
            
            score = 0.0
            
            # 非常宽松的标题匹配
            table_title = metadata.get('table_title', '')
            if table_title:
                title_lower = table_title.lower()
                for kw in query_keywords:
                    if kw.lower() in title_lower:
                        score += 0.2
                        break
            
            # 非常宽松的列名匹配
            table_headers = metadata.get('table_headers', [])
            if table_headers:
                for header in table_headers:
                    if not isinstance(header, str):
                        continue
                    header_lower = header.lower()
                    for kw in query_keywords:
                        if kw.lower() in header_lower:
                            score += 0.2
                            break
                    if score > 0.2:
                        break
            
            # 表格存在性加分
            if metadata.get('table_id'):
                score += 0.1
            
            return min(1.0, score)
            
        except Exception as e:
            logger.error(f"容错评分计算失败: {e}")
            return 0.0
    
    def _calculate_text_similarity_simple(self, query: str, content: str) -> float:
        """简单的文本相似度计算"""
        try:
            if not query or not content:
                return 0.0
            
            query_lower = query.lower()
            content_lower = content.lower()
            
            # 计算词匹配度
            query_words = set(query_lower.split())
            content_words = set(content_lower.split())
            
            if not query_words:
                return 0.0
            
            # 计算Jaccard相似度
            intersection = len(query_words & content_words)
            union = len(query_words | content_words)
            
            if union == 0:
                return 0.0
            
            similarity = intersection / union
            return similarity
            
        except Exception as e:
            logger.error(f"文本相似度计算失败: {e}")
            return 0.0
    
    def _deduplicate_by_doc_id(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """根据文档ID去重"""
        try:
            seen_doc_ids = set()
            unique_results = []
            
            for result in results:
                doc = result.get('doc')
                if not doc:
                    continue
                
                # 获取文档ID
                doc_id = None
                if hasattr(doc, 'metadata') and isinstance(doc.metadata, dict):
                    doc_id = doc.metadata.get('id') or doc.metadata.get('doc_id') or doc.metadata.get('table_id')
                elif hasattr(doc, 'id'):
                    doc_id = doc.id
                
                if doc_id and doc_id not in seen_doc_ids:
                    seen_doc_ids.add(doc_id)
                    unique_results.append(result)
                elif not doc_id:
                    # 如果没有ID，直接添加
                    unique_results.append(result)
            
            logger.info(f"去重前: {len(results)} 个结果，去重后: {len(unique_results)} 个结果")
            return unique_results
            
        except Exception as e:
            logger.error(f"结果去重失败: {e}")
            return results
    
    def _merge_and_deduplicate_results(self, all_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """合并和去重所有结果"""
        try:
            if not all_results:
                return []
            
            # 去重
            unique_results = self._deduplicate_by_doc_id(all_results)
            
            # 简单的层间权重调整
            for result in unique_results:
                layer = result.get('layer', 1)
                # 根据层级调整分数，层级越低分数越高
                layer_weight = 1.0 / layer
                result['adjusted_score'] = result['score'] * layer_weight
            
            # 按调整后的分数排序
            unique_results.sort(key=lambda x: x.get('adjusted_score', x['score']), reverse=True)
            
            logger.info(f"结果合并完成，最终结果数量: {len(unique_results)}")
            return unique_results
            
        except Exception as e:
            logger.error(f"结果合并失败: {e}")
            return all_results
    

    
    def _get_doc_id(self, doc) -> str:
        """获取文档ID"""
        try:
            if hasattr(doc, 'metadata') and isinstance(doc.metadata, dict):
                return (doc.metadata.get('id') or 
                        doc.metadata.get('doc_id') or 
                        doc.metadata.get('table_id') or 
                        str(id(doc)))
            elif hasattr(doc, 'id'):
                return str(doc.id)
            else:
                return str(id(doc))
        except Exception as e:
            logger.error(f"获取文档ID失败: {e}")
            return str(id(doc))
    
    def _final_ranking(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """最终排序"""
        try:
            if not results:
                return []
            
            # 按分数排序
            sorted_results = sorted(results, key=lambda x: x.get('score', 0), reverse=True)
            
            # 添加排名信息
            for i, result in enumerate(sorted_results):
                result['final_rank'] = i + 1
                result['final_score'] = result.get('score', 0.0)
            
            logger.info(f"最终排序完成，结果数量: {len(sorted_results)}")
            return sorted_results
            
        except Exception as e:
            logger.error(f"最终排序失败: {e}")
            return results
