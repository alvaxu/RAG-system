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
    
    def __init__(self, config, vector_store=None, document_loader=None, skip_initial_load=False):
        """
        初始化表格引擎 - 重构版本，支持更好的配置验证和文档加载
        
        :param config: 表格引擎配置
        :param vector_store: 向量数据库
        :param document_loader: 文档加载器
        :param skip_initial_load: 是否跳过初始文档加载
        """
        super().__init__(config)
        
        logger.info("🔍 开始初始化TableEngine")
        logger.info(f"配置类型: {type(config)}")
        logger.info(f"向量数据库: {vector_store}")
        logger.info(f"文档加载器: {document_loader}")
        logger.info(f"跳过初始加载: {skip_initial_load}")
        
        self.vector_store = vector_store
        self.document_loader = document_loader
        self.table_docs = []  # 表格文档缓存
        self._docs_loaded = False
        
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
        logger.info("开始初始化六层召回策略...")
        self._initialize_recall_strategy()
        logger.info("✅ 六层召回策略初始化完成")
        
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
        """验证六层召回策略配置"""
        try:
            if not hasattr(self.config, 'recall_strategy'):
                logger.warning("⚠️ 未配置召回策略，使用默认配置")
                return
            
            strategy = self.config.recall_strategy
            required_layers = [
                'layer1_structure_search',    # 新增：表格结构搜索
                'layer2_vector_search',       # 原第一层：向量相似度搜索
                'layer3_keyword_search',      # 原第二层：语义关键词搜索
                'layer4_hybrid_search',       # 原第三层：混合搜索策略
                'layer5_fuzzy_search',        # 原第四层：智能模糊匹配
                'layer6_expansion_search'     # 原第五层：智能扩展召回
            ]
            
            for layer in required_layers:
                if layer not in strategy:
                    logger.warning(f"⚠️ 缺少召回策略配置: {layer}")
                else:
                    layer_config = strategy[layer]
                    if not isinstance(layer_config, dict):
                        logger.warning(f"⚠️ 召回策略配置格式错误: {layer}")
                    else:
                        enabled = layer_config.get('enabled', True)
                        top_k = layer_config.get('top_k', 50)
                        logger.info(f"✅ {layer}: {'启用' if enabled else '禁用'}, top_k: {top_k}")
            
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
                        'metadata': getattr(doc, 'metadata', {})
                    }
                    rerank_candidates.append(rerank_candidate)
                else:
                    logger.warning(f"候选文档缺少必要属性，跳过重排序")
            
            if not rerank_candidates:
                logger.warning("没有有效的重排序候选文档，返回原始结果")
                return candidates
            
            # 调用表格重排序服务
            reranked_results = self.table_reranking_service.rerank(query, rerank_candidates)
            
            # 修复：确保返回结果格式一致
            final_results = []
            for i, reranked_result in enumerate(reranked_results):
                if isinstance(reranked_result, dict):
                    # 如果重排序结果包含原始候选信息，直接使用
                    if 'doc' in reranked_result:
                        final_results.append({
                            'doc': reranked_result['doc'],
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
            intent_analysis = {
                'primary_intent': 'search',
                'target_type': 'unknown',
                'target_domain': 'unknown',
                'target_purpose': 'unknown',
                'specific_keywords': [],
                'requires_full_table': False
            }
            
            query_lower = query.lower()
            # 使用优化的分词和关键词提取
            query_keywords = self._extract_keywords(query, top_k=20)
            query_tokens = self._tokenize_text(query_lower)
            
            # 识别主要意图
            detail_keywords = ['详细', '完整', '全部', '具体', '详情', '明细']
            if any(kw in query_lower for kw in detail_keywords):
                intent_analysis['primary_intent'] = 'detail_view'
                intent_analysis['requires_full_table'] = True
            
            summary_keywords = ['总结', '汇总', '总计', '概述', '概览', '总体']
            if any(kw in query_lower for kw in summary_keywords):
                intent_analysis['primary_intent'] = 'summary'
            
            comparison_keywords = ['对比', '比较', '差异', '变化', '增长', '下降']
            if any(kw in query_lower for kw in comparison_keywords):
                intent_analysis['primary_intent'] = 'comparison'
            
            # 识别目标表格类型
            financial_keywords = ['收入', '支出', '利润', '成本', '费用', '毛利', '净利', '资产', '负债', '权益', '现金流', '预算', '实际', '差异', '金额', '总额', '小计', '合计']
            if any(kw in query_keywords for kw in financial_keywords):
                intent_analysis['target_type'] = 'financial'
                intent_analysis['specific_keywords'].extend([keyword for keyword in financial_keywords if keyword in query_keywords])
            
            hr_keywords = ['姓名', '员工', '部门', '职位', '薪资', '工资', '奖金', '入职', '离职', '考勤', '绩效', '工号', '性别', '年龄']
            if any(kw in query_keywords for kw in hr_keywords):
                intent_analysis['target_type'] = 'hr'
                intent_analysis['specific_keywords'].extend([keyword for keyword in hr_keywords if keyword in query_keywords])
            
            statistical_keywords = ['数量', '次数', '频率', '比例', '百分比', '增长', '下降', '趋势', '统计', '汇总', '总数', '平均', '最大', '最小', '标准差']
            if any(kw in query_keywords for kw in statistical_keywords):
                intent_analysis['target_type'] = 'statistical'
                intent_analysis['specific_keywords'].extend([keyword for keyword in statistical_keywords if keyword in query_keywords])
            
            configuration_keywords = ['配置', '设置', '参数', '选项', '值', '默认', '范围', '限制', '条件', '规则']
            if any(kw in query_keywords for kw in configuration_keywords):
                intent_analysis['target_type'] = 'configuration'
                intent_analysis['specific_keywords'].extend([keyword for keyword in configuration_keywords if keyword in query_keywords])
            
            inventory_keywords = ['产品', '商品', '库存', '数量', '进货', '出货', '库存量', '库存值', '货号', '型号', '规格', '单价', '总价']
            if any(kw in query_keywords for kw in inventory_keywords):
                intent_analysis['target_type'] = 'inventory'
                intent_analysis['specific_keywords'].extend([keyword for keyword in inventory_keywords if keyword in query_keywords])
            
            # 识别目标业务领域
            finance_keywords = ['收入', '支出', '利润', '成本', '费用', '资产', '负债', '权益', '现金流', '预算', '实际', '差异', '金额', '账户', '交易', '投资', '贷款', '利率']
            if any(kw in query_keywords for kw in finance_keywords):
                intent_analysis['target_domain'] = 'finance'
                intent_analysis['specific_keywords'].extend([keyword for keyword in finance_keywords if keyword in query_keywords and keyword not in intent_analysis['specific_keywords']])
            
            manufacturing_keywords = ['产品', '生产', '制造', '工厂', '设备', '零件', '组件', '库存', '产量', '质量', '缺陷', '维修', '维护', '工艺', '流程']
            if any(kw in query_keywords for kw in manufacturing_keywords):
                intent_analysis['target_domain'] = 'manufacturing'
                intent_analysis['specific_keywords'].extend([keyword for keyword in manufacturing_keywords if keyword in query_keywords and keyword not in intent_analysis['specific_keywords']])
            
            retail_keywords = ['销售', '销售额', '商品', '客户', '订单', '退货', '折扣', '促销', '库存', '价格', '毛利', '净利', '渠道', '门店', '电商']
            if any(kw in query_keywords for kw in retail_keywords):
                intent_analysis['target_domain'] = 'retail'
                intent_analysis['specific_keywords'].extend([keyword for keyword in retail_keywords if keyword in query_keywords and keyword not in intent_analysis['specific_keywords']])
            
            education_keywords = ['学生', '教师', '课程', '成绩', '考试', '学年', '学期', '班级', '学科', '学费', '奖学金', '出勤', '毕业', '入学']
            if any(kw in query_keywords for kw in education_keywords):
                intent_analysis['target_domain'] = 'education'
                intent_analysis['specific_keywords'].extend([keyword for keyword in education_keywords if keyword in query_keywords and keyword not in intent_analysis['specific_keywords']])
            
            medical_keywords = ['患者', '医生', '医院', '诊所', '诊断', '治疗', '药物', '处方', '手术', '病历', '检查', '费用', '保险', '住院', '门诊']
            if any(kw in query_keywords for kw in medical_keywords):
                intent_analysis['target_domain'] = 'medical'
                intent_analysis['specific_keywords'].extend([keyword for keyword in medical_keywords if keyword in query_keywords and keyword not in intent_analysis['specific_keywords']])
            
            # 识别目标用途
            reporting_keywords = ['报告', '总结', '汇总', '统计', '分析', '结果', '数据', '指标', '绩效', '状态', '进展', '趋势']
            if any(kw in query_keywords for kw in reporting_keywords):
                intent_analysis['target_purpose'] = 'reporting'
            
            planning_keywords = ['计划', '规划', '预算', '目标', '预测', '安排', '时间表', '日程', '未来', '预期', '分配']
            if any(kw in query_keywords for kw in planning_keywords):
                intent_analysis['target_purpose'] = 'planning'
            
            monitoring_keywords = ['监控', '监测', '跟踪', '状态', '进展', '完成', '达成', '指标', 'KPI', '异常', '预警', '报警']
            if any(kw in query_keywords for kw in monitoring_keywords):
                intent_analysis['target_purpose'] = 'monitoring'
            
            comparison_keywords = ['对比', '比较', '差异', '变化', '增长', '下降', '之前', '之后', '去年', '今年', '上月', '本月', '季度']
            if any(kw in query_keywords for kw in comparison_keywords):
                intent_analysis['target_purpose'] = 'comparison'
            
            inventory_keywords = ['库存', '存货', '数量', '进货', '出货', '结余', '盘点', '库存量', '库存值']
            if any(kw in query_keywords for kw in inventory_keywords):
                intent_analysis['target_purpose'] = 'inventory'
            
            scheduling_keywords = ['安排', '日程', '时间表', '排班', '预约', '会议', '活动', '时间', '日期', '地点']
            if any(kw in query_keywords for kw in scheduling_keywords):
                intent_analysis['target_purpose'] = 'scheduling'
            
            logger.debug(f"查询意图分析结果: {intent_analysis}")
            return intent_analysis
            
        except Exception as e:
            logger.error(f"查询意图分析失败: {e}")
            return {
                'primary_intent': 'search',
                'target_type': 'unknown',
                'target_domain': 'unknown',
                'target_purpose': 'unknown',
                'specific_keywords': [],
                'requires_full_table': False
            }
    
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
            logger.info(f"查询意图分析: {intent_analysis['primary_intent']}, 目标类型: {intent_analysis['target_type']}")
            
            # 执行搜索
            search_results = self._search_tables(query)
            
            # 根据意图调整结果
            if intent_analysis['primary_intent'] == 'detail_view' and intent_analysis['requires_full_table']:
                # 如果用户意图是查看详细信息，尝试获取完整表格
                if search_results and len(search_results) > 0:
                    top_result = search_results[0]
                    table_id = top_result['doc'].metadata.get('table_id', 'unknown')
                    full_table_result = self.get_full_table(table_id)
                    if full_table_result['status'] == 'success':
                        search_results[0]['full_content'] = full_table_result['content']
                        search_results[0]['full_metadata'] = full_table_result['metadata']
            
            # 格式化结果
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
                
                formatted_result = {
                    'id': metadata.get('table_id', 'unknown'),
                    'content': getattr(doc, 'page_content', ''),
                    'score': result['score'],
                    'source': result.get('source', 'unknown'),  # 修复：使用get方法提供默认值
                    'layer': result.get('layer', 1),  # 修复：使用get方法提供默认值
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
                    'pipeline': 'table_engine',
                    'intent_analysis': intent_analysis,
                    'search_strategy': 'six_layer_recall',
                    'docs_loaded': self._docs_loaded,
                    'vector_store_available': self.vector_store is not None,
                    'document_loader_available': self.document_loader is not None
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
    
    def _search_tables(self, query: str) -> List[Dict[str, Any]]:
        """
        执行表格搜索 - 重构的五层召回策略
        
        :param query: 查询文本
        :return: 搜索结果列表
        """
        results = []
        
        # 获取配置参数
        threshold = getattr(self.config, 'table_similarity_threshold', 0.65)
        max_results = getattr(self.config, 'max_results', 10)
        max_recall_results = getattr(self.config, 'max_recall_results', 150)
        
        try:
            # 第一层：表格结构搜索（新增）
            if hasattr(self.config, 'recall_strategy') and self.config.recall_strategy.get('layer1_structure_search', {}).get('enabled', True):
                structure_results = self._table_structure_search(query, max_recall_results)
                results.extend(structure_results)
                logger.info(f"第一层表格结构搜索返回 {len(structure_results)} 个结果")
            
            # 第二层：向量相似度搜索（原第一层）
            if hasattr(self.config, 'recall_strategy') and self.config.recall_strategy.get('layer2_vector_search', {}).get('enabled', True):
                vector_results = self._vector_search(query, max_recall_results)
                results.extend(vector_results)
                logger.info(f"第二层向量搜索返回 {len(vector_results)} 个结果")
            
            # 第三层：语义关键词搜索（原第二层）
            if hasattr(self.config, 'recall_strategy') and self.config.recall_strategy.get('layer3_keyword_search', {}).get('enabled', True):
                keyword_results = self._keyword_search(query, max_recall_results)
                results.extend(keyword_results)
                logger.info(f"第三层关键词搜索返回 {len(keyword_results)} 个结果")
            
            # 第四层：混合搜索策略（原第三层）
            if hasattr(self.config, 'recall_strategy') and self.config.recall_strategy.get('layer4_hybrid_search', {}).get('enabled', True):
                hybrid_results = self._hybrid_search(query, max_recall_results)
                results.extend(hybrid_results)
                logger.info(f"第四层混合搜索返回 {len(hybrid_results)} 个结果")
            
            # 第五层：智能模糊匹配（原第四层）
            if hasattr(self.config, 'recall_strategy') and self.config.recall_strategy.get('layer5_fuzzy_search', {}).get('enabled', True):
                fuzzy_results = self._fuzzy_search(query, max_recall_results)
                results.extend(fuzzy_results)
                logger.info(f"第五层模糊搜索返回 {len(fuzzy_results)} 个结果")
            
            # 第六层：查询扩展召回（原第五层）
            if hasattr(self.config, 'recall_strategy') and self.config.recall_strategy.get('layer6_expansion_search', {}).get('enabled', True):
                expansion_results = self._expansion_search(query, max_recall_results)
                results.extend(expansion_results)
                logger.info(f"第六层扩展搜索返回 {len(expansion_results)} 个结果")
            
            # 如果没有结果，降低阈值重试
            if not results and threshold > 0.3:
                logger.info(f"未找到结果，降低阈值从 {threshold} 到 0.3")
                return self._search_tables_with_lower_threshold(query, 0.3)
            
            # 去重和排序
            results = self._deduplicate_and_sort_results(results)
            
            # 应用表格重排序（如果启用）
            if hasattr(self.config, 'enable_enhanced_reranking') and self.config.enable_enhanced_reranking:
                if self.table_reranking_service:
                    logger.info("🔍 启用表格重排序服务")
                    results = self._rerank_table_results(query, results)
                else:
                    logger.info("ℹ️ 表格重排序服务未初始化，跳过重排序")
            else:
                logger.info("ℹ️ 未启用增强重排序，跳过重排序")
            
            # 限制结果数量
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"表格搜索失败: {e}")
            return []
    
    def _table_structure_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """
        第一层：表格结构搜索（新增）
        
        :param query: 查询文本
        :param max_results: 最大结果数
        :return: 搜索结果列表
        """
        if not self.table_docs:
            return []
        
        try:
            # 获取配置参数
            layer_config = self.config.recall_strategy.get('layer1_structure_search', {})
            top_k = layer_config.get('top_k', 50)
            structure_threshold = layer_config.get('structure_threshold', 0.1)
            
            results = []
            query_lower = query.lower()
            
            for doc in self.table_docs:
                # 严格检查文档类型
                if not hasattr(doc, 'metadata') or not hasattr(doc, 'page_content'):
                    logger.debug(f"跳过文档: 缺少必要属性")
                    continue
                
                if not isinstance(doc.metadata, dict):
                    logger.debug(f"跳过文档: metadata不是字典类型")
                    continue
                
                if not isinstance(doc.page_content, str):
                    logger.debug(f"跳过文档: page_content不是字符串类型")
                    continue
                
                score = 0.3  # 基础分数，提高召回率
                
                try:
                    # 分析表格结构
                    structure_analysis = self._analyze_table_structure(doc)
                    
                    # 表格类型匹配
                    if structure_analysis['table_type'] != 'unknown':
                        table_type_lower = structure_analysis['table_type'].lower()
                        if query_lower in table_type_lower:
                            score += 0.4
                        elif any(word in table_type_lower for word in query_lower.split()):
                            score += 0.4
                    
                    # 业务领域匹配
                    if structure_analysis['business_domain'] != 'unknown':
                        domain_lower = structure_analysis['business_domain'].lower()
                        if query_lower in domain_lower:
                            score += 0.5
                        elif any(word in domain_lower for word in query_lower.split()):
                            score += 0.5
                    
                    # 主要用途匹配
                    if structure_analysis['primary_purpose'] != 'unknown':
                        purpose_lower = structure_analysis['primary_purpose'].lower()
                        if query_lower in purpose_lower:
                            score += 0.4
                        elif any(word in purpose_lower for word in query_lower.split()):
                            score += 0.4
                    
                    # 列名精确匹配
                    columns = structure_analysis['columns']
                    if isinstance(columns, list):
                        for col in columns:
                            if isinstance(col, str):
                                col_lower = col.lower()
                                if query_lower in col_lower:
                                    score += 0.8  # 列名匹配权重最高
                                elif any(word in col_lower for word in query_lower.split()):
                                    score += 0.5
                    
                    # 表格质量加分
                    quality_score = structure_analysis['quality_score']
                    score += quality_score * 0.3  # 提高质量分数权重  # 质量分数作为额外加分
                    
                    # 截断惩罚
                    if structure_analysis['is_truncated']:
                        score -= 0.1  # 截断的表格略微降低分数
                        logger.debug(f"表格 {doc.metadata.get('table_id', 'unknown')} 因截断被扣分: -0.1")
                        
                except Exception as e:
                    logger.debug(f"计算表格结构搜索分数失败: {e}")
                    score = 0.3  # 基础分数，提高召回率
                
                if score >= structure_threshold:
                    results.append({
                        'doc': doc,
                        'score': score,
                        'source': 'structure_search',
                        'layer': 1,
                        'structure_analysis': structure_analysis
                    })
            
            # 按分数排序并限制数量
            results.sort(key=lambda x: x['score'], reverse=True)
            logger.info(f"表格结构搜索找到 {len(results)} 个符合阈值的结果")
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"表格结构搜索失败: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return []
    
    def _vector_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """
        第二层：向量相似度搜索
        
        :param query: 查询文本
        :param max_results: 最大结果数
        :return: 搜索结果列表
        """
        if not self.vector_store:
            logger.warning("⚠️ 向量数据库未连接，跳过向量搜索")
            return []
        
        try:
            # 获取配置参数 - 修复：使用正确的配置键名
            layer_config = self.config.recall_strategy.get('layer2_vector_search', {})
            top_k = layer_config.get('top_k', 50)
            similarity_threshold = layer_config.get('similarity_threshold', 0.65)
            
            logger.info(f"🔍 第二层向量搜索配置: top_k={top_k}, similarity_threshold={similarity_threshold}")
            logger.info(f"🔍 向量数据库状态: {self.vector_store is not None}")
            
            # 执行向量搜索
            logger.info(f"🔍 开始执行向量搜索，查询: {query}")
            
            # 修复：检查向量数据库是否支持相似度搜索
            if not hasattr(self.vector_store, 'similarity_search'):
                logger.warning("⚠️ 向量数据库不支持similarity_search方法")
                return []
            
            vector_results = self.vector_store.similarity_search(
                query, 
                k=top_k,
                filter={'chunk_type': 'table'}  # 使用正确的字段名
            )
            
            logger.info(f"🔍 向量搜索原始结果数量: {len(vector_results)}")
            
            results = []
            logger.info(f"🔍 开始处理向量搜索结果，相似度阈值: {similarity_threshold}")
            
            for i, doc in enumerate(vector_results):
                # 修复：处理可能没有score属性的情况
                if hasattr(doc, 'score'):
                    score = doc.score
                elif hasattr(doc, 'metadata') and 'score' in doc.metadata:
                    score = doc.metadata['score']
                else:
                    # 如果没有分数，使用默认分数
                    score = 0.5
                    logger.debug(f"文档 {i+1} 没有分数，使用默认分数: {score}")
                
                logger.info(f"🔍 文档 {i+1}: score={score}, 阈值={similarity_threshold}, 通过={score >= similarity_threshold}")
                
                if score >= similarity_threshold:
                    results.append({
                        'doc': doc,
                        'score': score,
                        'source': 'vector_search',
                        'layer': 2  # 修复：第二层向量搜索
                    })
            
            logger.info(f"🔍 向量搜索找到 {len(results)} 个符合阈值的结果")
            return results
            
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return []
    
    def _keyword_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """
        第三层：关键词搜索
        
        :param query: 查询文本
        :param max_results: 最大结果数
        :return: 搜索结果列表
        """
        if not self.table_docs:
            return []
        
        try:
            # 获取配置参数
            layer_config = self.config.recall_strategy.get('layer3_keyword_search', {})
            top_k = layer_config.get('top_k', 50)
            keyword_threshold = layer_config.get('keyword_threshold', 0.3)
            
            results = []
            # 使用优化的分词和关键词提取
            query_keywords = self._extract_keywords(query, top_k=20)
            query_tokens = self._tokenize_text(query.lower())
            
            for doc in self.table_docs:
                # 严格检查文档类型
                if not hasattr(doc, 'metadata') or not hasattr(doc, 'page_content'):
                    logger.debug(f"跳过文档: 缺少必要属性")
                    continue
                
                if not isinstance(doc.metadata, dict):
                    logger.debug(f"跳过文档: metadata不是字典类型")
                    continue
                
                if not isinstance(doc.page_content, str):
                    logger.debug(f"跳过文档: page_content不是字符串类型")
                    continue
                
                score = 0.3  # 基础分数，提高召回率
                
                try:
                    content = doc.page_content.lower()
                    metadata = doc.metadata
                    
                    # 内容关键词匹配
                    content_keywords = self._extract_keywords(content, top_k=20)
                    content_tokens = self._tokenize_text(content)
                    
                    # 关键词匹配（权重较高）
                    common_keywords = set(query_keywords) & set(content_keywords)
                    if common_keywords:
                        score += len(common_keywords) * 0.4
                    
                    # 分词匹配
                    common_tokens = set(query_tokens) & set(content_tokens)
                    if common_tokens:
                        score += len(common_tokens) * 0.2
                    
                    # 列名关键词匹配
                    columns = metadata.get('columns', [])
                    if isinstance(columns, list):
                        for col in columns:
                            if isinstance(col, str):
                                col_lower = col.lower()
                                col_keywords = self._extract_keywords(col_lower, top_k=10)
                                col_tokens = self._tokenize_text(col_lower)
                                
                                # 列名关键词匹配（权重最高）
                                if any(kw in col_keywords for kw in query_keywords):
                                    score += 0.4
                                # 列名分词匹配
                                elif any(token in col_tokens for token in query_tokens):
                                    score += 0.4
                                    
                except Exception as e:
                    logger.debug(f"计算关键词搜索分数失败: {e}")
                    score = 0.3  # 基础分数，提高召回率
                
                if score >= keyword_threshold:
                    results.append({
                        'doc': doc,
                        'score': score,
                        'source': 'keyword_search',
                        'layer': 3
                    })
            
            # 按分数排序并限制数量
            results.sort(key=lambda x: x['score'], reverse=True)
            logger.info(f"关键词搜索找到 {len(results)} 个符合阈值的结果")
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"关键词搜索失败: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return []
    
    def _hybrid_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """
        第三层：混合搜索策略
        
        :param query: 查询文本
        :param max_results: 最大结果数
        :return: 搜索结果列表
        """
        if not self.table_docs:
            return []
        
        try:
            # 获取配置参数
            layer_config = self.config.recall_strategy.get('layer4_hybrid_search', {})
            top_k = layer_config.get('top_k', 50)
            vector_weight = layer_config.get('vector_weight', 0.7)
            keyword_weight = layer_config.get('keyword_weight', 0.3)
            
            results = []
            query_lower = query.lower()
            
            for doc in self.table_docs:
                # 严格检查文档类型
                if not hasattr(doc, 'metadata') or not hasattr(doc, 'page_content'):
                    logger.debug(f"跳过文档: 缺少必要属性")
                    continue
                
                if not isinstance(doc.metadata, dict):
                    logger.debug(f"跳过文档: metadata不是字典类型")
                    continue
                
                if not isinstance(doc.page_content, str):
                    logger.debug(f"跳过文档: page_content不是字符串类型")
                    continue
                
                # 计算向量相似度分数（模拟）
                vector_score = 0.3  # 基础分数，提高召回率
                try:
                    content = doc.page_content.lower()
                    query_words = query_lower.split()
                    matched_words = sum(1 for word in query_words if word in content)
                    if matched_words > 0:
                        vector_score = min(1.0, matched_words / len(query_words))
                except Exception as e:
                    logger.debug(f"计算向量分数失败: {e}")
                    vector_score = 0.3  # 基础分数，提高召回率
                
                # 计算关键词匹配分数
                keyword_score = 0.3  # 基础分数，提高召回率
                try:
                    title = doc.metadata.get('title', '').lower()
                    if query_lower in title:
                        keyword_score += 0.4
                    
                    columns = doc.metadata.get('columns', [])
                    if isinstance(columns, list):
                        for col in columns:
                            if isinstance(col, str) and query_lower in col.lower():
                                keyword_score += 0.4
                except Exception as e:
                    logger.debug(f"计算关键词分数失败: {e}")
                    keyword_score = 0.3  # 基础分数，提高召回率
                
                # 混合分数计算
                hybrid_score = (vector_score * vector_weight) + (keyword_score * keyword_weight)
                
                if hybrid_score > 0:
                    results.append({
                        'doc': doc,
                        'score': hybrid_score,
                        'source': 'hybrid_search',
                        'layer': 4,
                        'vector_score': vector_score,
                        'keyword_score': keyword_score
                    })
            
            # 按分数排序并限制数量
            results.sort(key=lambda x: x['score'], reverse=True)
            logger.info(f"混合搜索找到 {len(results)} 个结果")
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"混合搜索失败: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return []
    
    def _fuzzy_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """
        第五层：模糊搜索
        
        :param query: 查询文本
        :param max_results: 最大结果数
        :return: 搜索结果列表
        """
        if not self.table_docs:
            return []
        
        try:
            # 获取配置参数
            layer_config = self.config.recall_strategy.get('layer5_fuzzy_search', {})
            top_k = layer_config.get('top_k', 25)
            fuzzy_threshold = layer_config.get('fuzzy_threshold', 0.2)
            
            results = []
            query_keywords = self._extract_keywords(query, top_k=20)
            query_tokens = self._tokenize_text(query.lower())
            
            for doc in self.table_docs:
                # 严格检查文档类型
                if not hasattr(doc, 'metadata') or not hasattr(doc, 'page_content'):
                    logger.debug(f"跳过文档: 缺少必要属性")
                    continue
                
                if not isinstance(doc.metadata, dict):
                    logger.debug(f"跳过文档: metadata不是字典类型")
                    continue
                
                if not isinstance(doc.page_content, str):
                    logger.debug(f"跳过文档: page_content不是字符串类型")
                    continue
                
                score = 0.3  # 基础分数，提高召回率
                
                try:
                    content = doc.page_content.lower()
                    metadata = doc.metadata
                    
                    # 内容模糊匹配
                    content_keywords = self._extract_keywords(content, top_k=20)
                    content_tokens = self._tokenize_text(content)
                    
                    # 关键词模糊匹配
                    for q_kw in query_keywords:
                        for c_kw in content_keywords:
                            if q_kw in c_kw or c_kw in q_kw:
                                score += 0.15
                    
                    # 分词模糊匹配
                    for q_token in query_tokens:
                        for c_token in content_tokens:
                            if q_token in c_token or c_token in q_token:
                                score += 0.08
                    
                    # 列名模糊匹配
                    columns = metadata.get('columns', [])
                    if isinstance(columns, list):
                        for col in columns:
                            if isinstance(col, str):
                                col_lower = col.lower()
                                col_keywords = self._extract_keywords(col_lower, top_k=10)
                                col_tokens = self._tokenize_text(col_lower)
                                
                                # 列名关键词模糊匹配（权重较高）
                                for q_kw in query_keywords:
                                    for c_kw in col_keywords:
                                        if q_kw in c_kw or c_kw in q_kw:
                                            score += 0.25
                                
                                # 列名分词模糊匹配
                                for q_token in query_tokens:
                                    for c_token in col_tokens:
                                        if q_token in c_token or c_token in q_token:
                                            score += 0.15
                                            
                except Exception as e:
                    logger.debug(f"计算模糊搜索分数失败: {e}")
                    score = 0.3  # 基础分数，提高召回率
                
                if score >= fuzzy_threshold:
                    results.append({
                        'doc': doc,
                        'score': score,
                        'source': 'fuzzy_search',
                        'layer': 5
                    })
            
            # 按分数排序并限制数量
            results.sort(key=lambda x: x['score'], reverse=True)
            logger.info(f"模糊搜索找到 {len(results)} 个符合阈值的结果")
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"模糊搜索失败: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return []
    
    def _expansion_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """
        第六层：查询扩展召回
        
        :param query: 查询文本
        :param max_results: 最大结果数
        :return: 搜索结果列表
        """
        if not self.table_docs:
            return []
        
        try:
            # 获取配置参数
            layer_config = self.config.recall_strategy.get('layer6_expansion_search', {})
            top_k = layer_config.get('top_k', 25)
            
            results = []
            query_lower = query.lower()
            
            # 简单的查询扩展策略
            expanded_terms = self._expand_query_terms(query_lower)
            
            for doc in self.table_docs:
                # 严格检查文档类型
                if not hasattr(doc, 'metadata') or not hasattr(doc, 'page_content'):
                    logger.debug(f"跳过文档: 缺少必要属性")
                    continue
                
                if not isinstance(doc.metadata, dict):
                    logger.debug(f"跳过文档: metadata不是字典类型")
                    continue
                
                if not isinstance(doc.page_content, str):
                    logger.debug(f"跳过文档: page_content不是字符串类型")
                    continue
                
                score = 0.3  # 基础分数，提高召回率
                
                try:
                    # 基于扩展术语的匹配
                    title = doc.metadata.get('title', '').lower()
                    content = doc.page_content.lower()
                    columns = doc.metadata.get('columns', [])
                    table_type = doc.metadata.get('table_type', '').lower()
                    
                    for term in expanded_terms:
                        # 标题匹配
                        if term in title:
                            score += 0.4
                        
                        # 列名匹配
                        if isinstance(columns, list):
                            for col in columns:
                                if isinstance(col, str) and term in col.lower():
                                    score += 0.3
                        
                        # 内容匹配
                        if term in content:
                            score += 0.2
                        
                        # 表格类型匹配
                        if term in table_type:
                            score += 0.3
                            
                except Exception as e:
                    logger.debug(f"计算扩展搜索分数失败: {e}")
                    score = 0.3  # 基础分数，提高召回率
                
                if score > 0:
                    results.append({
                        'doc': doc,
                        'score': score,
                        'source': 'expansion_search',
                        'layer': 6,
                        'expanded_terms': expanded_terms
                    })
            
            # 按分数排序并限制数量
            results.sort(key=lambda x: x['score'], reverse=True)
            logger.info(f"扩展搜索找到 {len(results)} 个结果，扩展术语: {expanded_terms}")
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"扩展搜索失败: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return []
    
    def _expand_query_terms(self, query: str) -> List[str]:
        """
        扩展查询术语
        
        :param query: 原始查询
        :return: 扩展后的术语列表
        """
        # 简单的同义词扩展
        synonyms = {
            '财务': ['财务', '会计', '资金', '预算', '成本'],
            '数据': ['数据', '统计', '数字', '指标', '报表'],
            '表格': ['表格', '表', '清单', '目录', '索引'],
            '报告': ['报告', '报表', '总结', '分析', '评估'],
            '收入': ['收入', '营收', '销售额', '营业额', '收益'],
            '支出': ['支出', '费用', '成本', '开销', '花费'],
            '利润': ['利润', '盈利', '收益', '净利', '毛利']
        }
        
        expanded_terms = [query]
        
        # 查找同义词
        for key, values in synonyms.items():
            if key in query:
                expanded_terms.extend(values)
        
        # 去重并返回
        return list(set(expanded_terms))
    
    def _search_tables_with_lower_threshold(self, query: str, threshold: float) -> List[Dict[str, Any]]:
        """
        使用较低阈值重新搜索
        
        :param query: 查询文本
        :param threshold: 相似度阈值
        :return: 搜索结果列表
        """
        # 临时降低阈值
        original_threshold = getattr(self.config, 'table_similarity_threshold', 0.65)
        setattr(self.config, 'table_similarity_threshold', threshold)
        
        try:
            results = self._search_tables(query)
            return results
        finally:
            # 恢复原始阈值
            setattr(self.config, 'table_similarity_threshold', original_threshold)
    
    def _deduplicate_and_sort_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        去重和排序结果 - 支持五层召回策略
        
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
    
    def _validate_recall_strategy(self):
        """验证六层召回策略配置"""
        try:
            if not hasattr(self.config, 'recall_strategy'):
                logger.warning("⚠️ 未配置召回策略，使用默认配置")
                return
            
            strategy = self.config.recall_strategy
            required_layers = [
                'layer1_structure_search',    # 新增：表格结构搜索
                'layer2_vector_search',       # 原第一层：向量相似度搜索
                'layer3_keyword_search',      # 原第二层：语义关键词搜索
                'layer4_hybrid_search',       # 原第三层：混合搜索策略
                'layer5_fuzzy_search',        # 原第四层：智能模糊匹配
                'layer6_expansion_search'     # 原第五层：智能扩展召回
            ]
            
            for layer in required_layers:
                if layer not in strategy:
                    logger.warning(f"⚠️ 缺少召回策略配置: {layer}")
                else:
                    layer_config = strategy[layer]
                    if not isinstance(layer_config, dict):
                        logger.warning(f"⚠️ 召回策略配置格式错误: {layer}")
                    else:
                        enabled = layer_config.get('enabled', True)
                        top_k = layer_config.get('top_k', 50)
                        logger.info(f"✅ {layer}: {'启用' if enabled else '禁用'}, top_k: {top_k}")
            
        except Exception as e:
            logger.error(f"验证召回策略配置失败: {e}")
    
    def _initialize_recall_strategy(self):
        """初始化六层召回策略"""
        try:
            self._validate_recall_strategy()
            
            # 检查必要的配置项
            if not hasattr(self.config, 'use_new_pipeline'):
                logger.warning("未配置use_new_pipeline，默认启用")
            
            if not hasattr(self.config, 'enable_enhanced_reranking'):
                logger.warning("未配置enable_enhanced_reranking，默认启用")
            
            logger.info("六层召回策略初始化完成")
            
        except Exception as e:
            logger.error(f"初始化召回策略失败: {e}")
    
    def clear_cache(self):
        """清理表格引擎缓存"""
        self.table_docs = []
        self._docs_loaded = False
        logger.info("表格引擎缓存已清理")

    def _analyze_table_structure(self, doc):
        """
        分析表格结构，提取深层特征
        
        :param doc: 表格文档
        :return: 表格结构分析结果
        """
        try:
            analysis = {
                'table_type': 'unknown',
                'columns': [],
                'row_count': 0,
                'column_count': 0,
                'data_completeness': 0.0,
                'quality_score': 0.0,
                'business_domain': 'unknown',
                'primary_purpose': 'unknown',
                'is_truncated': False,
                'truncation_type': 'none',
                'truncated_rows': 0,
                'original_row_count': 0
            }
            
            # 从元数据中提取基本信息
            metadata = getattr(doc, 'metadata', {})
            if metadata:
                analysis['columns'] = metadata.get('columns', [])
                analysis['row_count'] = metadata.get('table_row_count', 0)
                analysis['column_count'] = metadata.get('table_column_count', 0)
                analysis['table_type'] = metadata.get('table_type', 'unknown')
                analysis['original_row_count'] = metadata.get('original_row_count', analysis['row_count'])
            
            # 分析表格内容
            content = getattr(doc, 'page_content', '')
            if content:
                # 计算数据完整性
                analysis['data_completeness'] = self._calculate_data_completeness(content)
                
                # 检测截断状态
                truncation_info = self._detect_truncation(content, analysis['row_count'], analysis['original_row_count'])
                analysis['is_truncated'] = truncation_info['is_truncated']
                analysis['truncation_type'] = truncation_info['truncation_type']
                analysis['truncated_rows'] = truncation_info['truncated_rows']
                
                # 识别表格类型
                analysis['table_type'] = self._identify_table_type(content, analysis['columns'])
                
                # 识别业务领域
                analysis['business_domain'] = self._identify_business_domain(content, analysis['columns'])
                
                # 识别主要用途
                analysis['primary_purpose'] = self._identify_primary_purpose(content, analysis['columns'])
            
            # 计算质量评分
            analysis['quality_score'] = self._calculate_quality_score(analysis)
            
            logger.debug(f"表格结构分析完成: {analysis}")
            return analysis
            
        except Exception as e:
            logger.error(f"表格结构分析失败: {e}")
            return {
                'table_type': 'unknown',
                'columns': [],
                'row_count': 0,
                'column_count': 0,
                'data_completeness': 0.0,
                'quality_score': 0.0,
                'business_domain': 'unknown',
                'primary_purpose': 'unknown',
                'is_truncated': False,
                'truncation_type': 'none',
                'truncated_rows': 0,
                'original_row_count': 0
            }
    
    def _detect_truncation(self, content, current_rows, original_rows):
        """
        检测表格是否被截断以及截断类型
        
        :param content: 表格内容
        :param current_rows: 当前行数
        :param original_rows: 原始行数
        :return: 截断信息字典
        """
        try:
            truncation_info = {
                'is_truncated': False,
                'truncation_type': 'none',
                'truncated_rows': 0
            }
            
            # 检查内容中是否包含截断标记
            content_lower = content.lower()
            if '[表格数据行已截断处理]' in content_lower:
                truncation_info['is_truncated'] = True
                truncation_info['truncation_type'] = 'row_truncation'
            elif '[表格内容已截断处理]' in content_lower:
                truncation_info['is_truncated'] = True
                truncation_info['truncation_type'] = 'content_truncation'
            elif '[表格格式已优化]' in content_lower:
                truncation_info['is_truncated'] = True
                truncation_info['truncation_type'] = 'format_optimization'
            
            # 检查行数差异
            if original_rows > current_rows:
                truncation_info['is_truncated'] = True
                truncation_info['truncated_rows'] = original_rows - current_rows
                if truncation_info['truncation_type'] == 'none':
                    truncation_info['truncation_type'] = 'row_truncation'
            
            return truncation_info
            
        except Exception as e:
            logger.error(f"检测截断状态失败: {e}")
            return {
                'is_truncated': False,
                'truncation_type': 'none',
                'truncated_rows': 0
            }
    
    def _calculate_data_completeness(self, content):
        """计算数据完整性"""
        try:
            if not content:
                return 0.0
            
            # 简单的完整性计算：基于非空行和有效数据
            lines = content.split('\n')
            if not lines:
                return 0.0
            
            valid_lines = 0
            total_lines = len(lines)
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('[') and len(line) > 5:  # 排除截断标记和空行
                    valid_lines += 1
            
            return valid_lines / total_lines if total_lines > 0 else 0.0
            
        except Exception as e:
            logger.error(f"计算数据完整性失败: {e}")
            return 0.0
    
    def _identify_table_type(self, content: str, columns: List[str]) -> str:
        """
        识别表格类型
        
        :param content: 表格内容
        :param columns: 表格列名列表
        :return: 表格类型
        """
        try:
            content_lower = content.lower()
            columns_lower = [col.lower() for col in columns]
            
            # 财务表格
            financial_keywords = ['收入', '支出', '利润', '成本', '费用', '毛利', '净利', '资产', '负债', '权益', '现金流', '预算', '实际', '差异', '金额', '总额', '小计', '合计']
            if any(kw in content_lower for kw in financial_keywords) or any(any(kw in col for kw in financial_keywords) for col in columns_lower):
                return 'financial'
            
            # 人事表格
            hr_keywords = ['姓名', '员工', '部门', '职位', '薪资', '工资', '奖金', '入职', '离职', '考勤', '绩效', '工号', '性别', '年龄']
            if any(kw in content_lower for kw in hr_keywords) or any(any(kw in col for kw in hr_keywords) for col in columns_lower):
                return 'hr'
            
            # 统计表格
            statistical_keywords = ['数量', '次数', '频率', '比例', '百分比', '增长', '下降', '趋势', '统计', '汇总', '总数', '平均', '最大', '最小', '标准差']
            if any(kw in content_lower for kw in statistical_keywords) or any(any(kw in col for kw in statistical_keywords) for col in columns_lower):
                return 'statistical'
            
            # 配置表格
            configuration_keywords = ['配置', '设置', '参数', '选项', '值', '默认', '范围', '限制', '条件', '规则']
            if any(kw in content_lower for kw in configuration_keywords) or any(any(kw in col for kw in configuration_keywords) for col in columns_lower):
                return 'configuration'
            
            # 库存表格
            inventory_keywords = ['产品', '商品', '库存', '数量', '进货', '出货', '库存量', '库存值', '货号', '型号', '规格', '单价', '总价']
            if any(kw in content_lower for kw in inventory_keywords) or any(any(kw in col for kw in inventory_keywords) for col in columns_lower):
                return 'inventory'
            
            return 'general'  # 默认类型
            
        except Exception as e:
            logger.error(f"识别表格类型失败: {e}")
            return 'unknown'
    
    def _identify_business_domain(self, content: str, columns: List[str]) -> str:
        """
        识别表格所属业务领域
        
        :param content: 表格内容
        :param columns: 表格列名列表
        :return: 业务领域
        """
        try:
            content_lower = content.lower()
            columns_lower = [col.lower() for col in columns]
            
            # 金融领域
            finance_keywords = ['收入', '支出', '利润', '成本', '费用', '资产', '负债', '权益', '现金流', '预算', '实际', '差异', '金额', '账户', '交易', '投资', '贷款', '利率']
            if any(kw in content_lower for kw in finance_keywords) or any(any(kw in col for kw in finance_keywords) for col in columns_lower):
                return 'finance'
            
            # 制造业
            manufacturing_keywords = ['产品', '生产', '制造', '工厂', '设备', '零件', '组件', '库存', '产量', '质量', '缺陷', '维修', '维护', '工艺', '流程']
            if any(kw in content_lower for kw in manufacturing_keywords) or any(any(kw in col for kw in manufacturing_keywords) for col in columns_lower):
                return 'manufacturing'
            
            # 零售业
            retail_keywords = ['销售', '销售额', '商品', '客户', '订单', '退货', '折扣', '促销', '库存', '价格', '毛利', '净利', '渠道', '门店', '电商']
            if any(kw in content_lower for kw in retail_keywords) or any(any(kw in col for kw in retail_keywords) for col in columns_lower):
                return 'retail'
            
            # 教育领域
            education_keywords = ['学生', '教师', '课程', '成绩', '考试', '学年', '学期', '班级', '学科', '学费', '奖学金', '出勤', '毕业', '入学']
            if any(kw in content_lower for kw in education_keywords) or any(any(kw in col for kw in education_keywords) for col in columns_lower):
                return 'education'
            
            # 医疗领域
            medical_keywords = ['患者', '医生', '医院', '诊所', '诊断', '治疗', '药物', '处方', '手术', '病历', '检查', '费用', '保险', '住院', '门诊']
            if any(kw in content_lower for kw in medical_keywords) or any(any(kw in col for kw in medical_keywords) for col in columns_lower):
                return 'medical'
            
            return 'general'  # 默认领域
            
        except Exception as e:
            logger.error(f"识别业务领域失败: {e}")
            return 'unknown'
    
    def _identify_primary_purpose(self, content: str, columns: List[str]) -> str:
        """
        识别表格主要用途
        
        :param content: 表格内容
        :param columns: 表格列名列表
        :return: 主要用途
        """
        try:
            content_lower = content.lower()
            columns_lower = [col.lower() for col in columns]
            
            # 报告用途
            reporting_keywords = ['报告', '总结', '汇总', '统计', '分析', '结果', '数据', '指标', '绩效', '状态', '进展', '趋势']
            if any(kw in content_lower for kw in reporting_keywords) or any(any(kw in col for kw in reporting_keywords) for col in columns_lower):
                return 'reporting'
            
            # 计划用途
            planning_keywords = ['计划', '规划', '预算', '目标', '预测', '安排', '时间表', '日程', '未来', '预期', '分配']
            if any(kw in content_lower for kw in planning_keywords) or any(any(kw in col for kw in planning_keywords) for col in columns_lower):
                return 'planning'
            
            # 监控用途
            monitoring_keywords = ['监控', '监测', '跟踪', '状态', '进展', '完成', '达成', '指标', 'KPI', '异常', '预警', '报警']
            if any(kw in content_lower for kw in monitoring_keywords) or any(any(kw in col for kw in monitoring_keywords) for col in columns_lower):
                return 'monitoring'
            
            # 对比用途
            comparison_keywords = ['对比', '比较', '差异', '变化', '增长', '下降', '之前', '之后', '去年', '今年', '上月', '本月', '季度']
            if any(kw in content_lower for kw in comparison_keywords) or any(any(kw in col for kw in comparison_keywords) for col in columns_lower):
                return 'comparison'
            
            # 库存用途
            inventory_keywords = ['库存', '存货', '数量', '进货', '出货', '结余', '盘点', '库存量', '库存值']
            if any(kw in content_lower for kw in inventory_keywords) or any(any(kw in col for kw in inventory_keywords) for col in columns_lower):
                return 'inventory'
            
            # 安排用途
            scheduling_keywords = ['安排', '日程', '时间表', '排班', '预约', '会议', '活动', '时间', '日期', '地点']
            if any(kw in content_lower for kw in scheduling_keywords) or any(any(kw in col for kw in scheduling_keywords) for col in columns_lower):
                return 'scheduling'
            
            return 'general'  # 默认用途
            
        except Exception as e:
            logger.error(f"识别主要用途失败: {e}")
            return 'unknown'
    
    def _calculate_quality_score(self, analysis):
        """计算表格质量评分"""
        try:
            score = 0.3  # 基础分数，提高召回率
            
            # 基础分数：数据完整性 (40%)
            score += analysis['data_completeness'] * 0.4
            
            # 结构分数：列数和行数合理性 (30%)
            if analysis['column_count'] > 0 and analysis['row_count'] > 0:
                # 列数合理性：2-20列为佳
                if 2 <= analysis['column_count'] <= 20:
                    score += 0.3
                elif analysis['column_count'] > 20:
                    score += 0.15  # 列数过多，减分
                else:
                    score += 0.1   # 列数过少，减分
            
            # 类型识别分数：能识别出具体类型 (20%)
            if analysis['table_type'] not in ['unknown', 'general']:
                score += 0.2
            
            # 业务领域识别分数：能识别出具体领域 (10%)
            if analysis['business_domain'] not in ['unknown', 'general']:
                score += 0.1
            
            # 截断惩罚：如果表格被截断，质量分数降低 (10%)
            if analysis['is_truncated']:
                score -= 0.1
            
            return min(1.0, score)
            
        except Exception as e:
            logger.error(f"计算质量评分失败: {e}")
            return 0.0

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

    def _extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        """
        提取文本关键词
        
        :param text: 输入文本
        :param top_k: 返回关键词数量
        :return: 关键词列表
        """
        try:
            # 使用jieba.analyse提取关键词
            keywords = jieba.analyse.extract_tags(text, topK=top_k, withWeight=False)
            
            # 过滤停用词
            filtered_keywords = [kw for kw in keywords if kw not in stop_words and len(kw) > 1]
            
            return filtered_keywords[:top_k]
            
        except Exception as e:
            logger.error(f"关键词提取失败: {e}")
            return []
    
    def _tokenize_text(self, text: str) -> List[str]:
        """
        对文本进行分词
        
        :param text: 输入文本
        :return: 分词结果列表
        """
        try:
            # 使用jieba进行分词
            tokens = list(jieba.cut(text))
            
            # 过滤停用词和短词
            filtered_tokens = [token for token in tokens if token not in stop_words and len(token) > 1]
            
            return filtered_tokens
            
        except Exception as e:
            logger.error(f"文本分词失败: {e}")
            return []
