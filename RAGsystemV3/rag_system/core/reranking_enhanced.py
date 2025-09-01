"""
增强重排序服务模块

RAG系统的智能重排序核心组件，负责：
1. 多模型重排序支持
2. 混合排序策略
3. 性能优化和缓存
4. 重排序质量评估
"""

import logging
import time
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class RerankCandidate:
    """重排序候选项数据类"""
    chunk_id: str
    content: str
    content_type: str
    original_score: float
    metadata: Dict[str, Any]

@dataclass
class RerankResult:
    """重排序结果数据类"""
    chunk_id: str
    rerank_score: float
    original_score: float
    final_score: float
    ranking_position: int
    confidence: float

class MultiModelReranker:
    """多模型重排序器"""
    
    def __init__(self, config_integration):
        """初始化多模型重排序器"""
        self.config = config_integration
        self.reranking_config = self.config.get('rag_system.models.reranking', {})
        
        # 重排序模型配置
        self.models = {
            'dashscope': {
                'enabled': self.reranking_config.get('dashscope.enabled', True),
                'model_name': self.reranking_config.get('dashscope.model_name', 'gte-rerank-v2'),
                'api_key': self.config.get_env_var('DASHSCOPE_API_KEY'),
                'weight': self.reranking_config.get('dashscope.weight', 0.6)
            },
            'rule_based': {
                'enabled': self.reranking_config.get('rule_based.enabled', True),
                'weight': self.reranking_config.get('rule_based.weight', 0.4)
            }
        }
        
        # 性能配置
        self.batch_size = self.reranking_config.get('batch_size', 32)
        self.max_candidates = self.reranking_config.get('max_candidates', 100)
        self.cache_enabled = self.reranking_config.get('cache.enabled', True)
        
        # 缓存和统计
        self.rerank_cache = {}
        self.performance_stats = {
            'total_reranks': 0,
            'total_time': 0.0,
            'avg_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # 初始化模型
        self._initialize_models()
        
        logger.info("增强重排序服务初始化完成")
    
    def _initialize_models(self):
        """初始化重排序模型"""
        try:
            # 初始化DashScope模型
            if self.models['dashscope']['enabled']:
                if self.models['dashscope']['api_key']:
                    import dashscope
                    dashscope.api_key = self.models['dashscope']['api_key']
                    logger.info(f"DashScope重排序模型初始化成功: {self.models['dashscope']['model_name']}")
                else:
                    logger.warning("DashScope API密钥未配置，禁用DashScope重排序")
                    self.models['dashscope']['enabled'] = False
            
            # 检查是否有可用的模型
            available_models = [name for name, config in self.models.items() if config['enabled']]
            if not available_models:
                logger.warning("没有可用的重排序模型，将使用规则基础排序")
                self.models['rule_based']['enabled'] = True
                self.models['rule_based']['weight'] = 1.0
            
            logger.info(f"可用的重排序模型: {available_models}")
            
        except Exception as e:
            logger.error(f"初始化重排序模型失败: {e}")
            self.models['rule_based']['enabled'] = True
            self.models['rule_based']['weight'] = 1.0
    
    def rerank(self, query_text: str, candidates: List[RerankCandidate]) -> List[RerankResult]:
        """对候选结果进行智能重排序"""
        start_time = time.time()
        
        try:
            if not candidates:
                return []
            
            # 限制候选数量
            if len(candidates) > self.max_candidates:
                candidates = candidates[:self.max_candidates]
            
            logger.info(f"开始重排序，候选结果数量: {len(candidates)}")
            
            # 检查缓存
            cache_key = self._generate_cache_key(query_text, candidates)
            if self.cache_enabled and cache_key in self.rerank_cache:
                self.performance_stats['cache_hits'] += 1
                return self.rerank_cache[cache_key]
            
            self.performance_stats['cache_misses'] += 1
            
            # 执行多模型重排序
            rerank_results = self._execute_multi_model_rerank(query_text, candidates)
            
            # 应用排序策略
            final_results = self._apply_sorting_strategies(rerank_results)
            
            # 缓存结果
            if self.cache_enabled:
                self._cache_result(cache_key, final_results)
            
            # 更新统计信息
            processing_time = time.time() - start_time
            self._update_performance_stats(processing_time)
            
            logger.info(f"重排序完成，耗时: {processing_time:.3f}s")
            return final_results
            
        except Exception as e:
            logger.error(f"重排序失败: {e}")
            return self._create_fallback_results(candidates)
    
    def _execute_multi_model_rerank(self, query_text: str, candidates: List[RerankCandidate]) -> List[RerankResult]:
        """执行多模型重排序"""
        try:
            all_scores = defaultdict(dict)
            
            # DashScope重排序
            if self.models['dashscope']['enabled']:
                dashscope_scores = self._dashscope_rerank(query_text, candidates)
                for score in dashscope_scores:
                    all_scores[score['chunk_id']]['dashscope'] = score['rerank_score']
            
            # 规则基础排序
            if self.models['rule_based']['enabled']:
                rule_scores = self._rule_based_rerank(query_text, candidates)
                for score in rule_scores:
                    all_scores[score['chunk_id']]['rule_based'] = score['rerank_score']
            
            # 合并多模型分数
            merged_results = self._merge_model_scores(candidates, all_scores)
            
            return merged_results
            
        except Exception as e:
            logger.error(f"多模型重排序失败: {e}")
            return self._create_fallback_results(candidates)
    
    def _dashscope_rerank(self, query_text: str, candidates: List[RerankCandidate]) -> List[Dict]:
        """DashScope重排序"""
        try:
            from dashscope.rerank import text_rerank
            
            # 准备文档列表
            documents = [candidate.content for candidate in candidates]
            
            # 调用DashScope API
            response = text_rerank.TextReRank.call(
                model=self.models['dashscope']['model_name'],
                query=query_text,
                documents=documents,
                top_k=min(self.batch_size, len(documents))
            )
            
            if response.status_code == 200:
                results = []
                for result in response.output.results:
                    doc_index = result.index
                    if 0 <= doc_index < len(candidates):
                        results.append({
                            'chunk_id': candidates[doc_index].chunk_id,
                            'rerank_score': result.relevance_score
                        })
                return results
            else:
                logger.error(f"DashScope API调用失败: {response.message}")
                return []
                
        except Exception as e:
            logger.error(f"DashScope重排序失败: {e}")
            return []
    
    def _rule_based_rerank(self, query_text: str, candidates: List[RerankCandidate]) -> List[Dict]:
        """规则基础重排序"""
        try:
            results = []
            for candidate in candidates:
                score = self._calculate_rule_based_score(query_text, candidate)
                results.append({
                    'chunk_id': candidate.chunk_id,
                    'rerank_score': score
                })
            return results
            
        except Exception as e:
            logger.error(f"规则基础重排序失败: {e}")
            return []
    
    def _calculate_rule_based_score(self, query: str, candidate: RerankCandidate) -> float:
        """计算规则基础分数"""
        try:
            score = 0.0
            
            # 原始分数权重
            score += candidate.original_score * 0.4
            
            # 内容长度权重
            content_length = len(candidate.content)
            if 50 <= content_length <= 500:
                score += 0.2
            elif content_length > 500:
                score += 0.1
            
            # 内容类型权重
            if candidate.content_type == 'text':
                score += 0.1
            elif candidate.content_type == 'table':
                score += 0.15
            
            return min(1.0, score)
            
        except Exception as e:
            logger.error(f"规则基础分数计算失败: {e}")
            return candidate.original_score
    
    def _merge_model_scores(self, candidates: List[RerankCandidate], all_scores: Dict) -> List[RerankResult]:
        """合并多模型分数"""
        try:
            results = []
            
            for candidate in candidates:
                chunk_id = candidate.chunk_id
                scores = all_scores.get(chunk_id, {})
                
                # 计算加权平均分数
                weighted_score = 0.0
                total_weight = 0.0
                
                for model_name, score in scores.items():
                    weight = self.models[model_name]['weight']
                    weighted_score += score * weight
                    total_weight += weight
                
                # 如果没有模型分数，使用原始分数
                if total_weight == 0:
                    weighted_score = candidate.original_score
                    total_weight = 1.0
                else:
                    weighted_score /= total_weight
                
                # 创建重排序结果
                result = RerankResult(
                    chunk_id=chunk_id,
                    rerank_score=weighted_score,
                    original_score=candidate.original_score,
                    final_score=weighted_score,
                    ranking_position=0,
                    confidence=0.7
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"合并模型分数失败: {e}")
            return self._create_fallback_results(candidates)
    
    def _apply_sorting_strategies(self, results: List[RerankResult]) -> List[RerankResult]:
        """应用排序策略"""
        try:
            if not results:
                return results
            
            # 混合排序策略
            for result in results:
                result.final_score = result.rerank_score * 0.7 + result.original_score * 0.3
            
            # 按最终分数排序
            results.sort(key=lambda x: x.final_score, reverse=True)
            
            # 设置排名位置
            for i, result in enumerate(results):
                result.ranking_position = i + 1
            
            return results
            
        except Exception as e:
            logger.error(f"应用排序策略失败: {e}")
            return results
    
    def _generate_cache_key(self, query_text: str, candidates: List[RerankCandidate]) -> str:
        """生成缓存键"""
        try:
            content_hash = hashlib.md5()
            content_hash.update(query_text.encode('utf-8'))
            
            for candidate in candidates[:10]:
                content_hash.update(candidate.chunk_id.encode('utf-8'))
                content_hash.update(str(candidate.original_score).encode('utf-8'))
            
            return content_hash.hexdigest()
            
        except Exception as e:
            logger.error(f"生成缓存键失败: {e}")
            return ""
    
    def _cache_result(self, cache_key: str, results: List[RerankResult]):
        """缓存重排序结果"""
        try:
            if not cache_key:
                return
            
            if len(self.rerank_cache) >= 100:  # 限制缓存大小
                oldest_key = next(iter(self.rerank_cache))
                del self.rerank_cache[oldest_key]
            
            self.rerank_cache[cache_key] = results
            
        except Exception as e:
            logger.error(f"缓存结果失败: {e}")
    
    def _create_fallback_results(self, candidates: List[RerankCandidate]) -> List[RerankResult]:
        """创建回退结果"""
        try:
            results = []
            for i, candidate in enumerate(candidates):
                result = RerankResult(
                    chunk_id=candidate.chunk_id,
                    rerank_score=candidate.original_score,
                    original_score=candidate.original_score,
                    final_score=candidate.original_score,
                    ranking_position=i + 1,
                    confidence=0.5
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"创建回退结果失败: {e}")
            return []
    
    def _update_performance_stats(self, processing_time: float):
        """更新性能统计"""
        try:
            self.performance_stats['total_reranks'] += 1
            self.performance_stats['total_time'] += processing_time
            self.performance_stats['avg_time'] = (
                self.performance_stats['total_time'] / self.performance_stats['total_reranks']
            )
            
        except Exception as e:
            logger.error(f"更新性能统计失败: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        return self.performance_stats.copy()
    
    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态信息"""
        return {
            'status': 'ready',
            'service_type': 'Enhanced Reranking Service',
            'available_models': [name for name, config in self.models.items() if config['enabled']],
            'cache_enabled': self.cache_enabled,
            'cache_size': len(self.rerank_cache),
            'performance_stats': self.performance_stats
        }
