'''
程序说明：
## 1. 混合reranking service - 专门处理混合引擎的reranking需求
## 2. 融合三个引擎的recall结果，进行统一的reranking
## 3. 设计理念与单引擎reranking service完全一致
## 4. 支持多种内容类型的混合reranking
'''

import logging
from typing import List, Dict, Any, Optional
from .base_reranking_service import BaseRerankingService
from .reranking_service_factory import RerankingServiceFactory

logger = logging.getLogger(__name__)


class HybridRerankingService(BaseRerankingService):
    """
    混合reranking service
    
    专门处理混合引擎的reranking需求，融合三个引擎的recall结果
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化混合reranking service
        
        :param config: 配置参数
        """
        # 设置基本属性
        self.name = "HybridRerankingService"
        self.version = "2.0.0"
        
        # 调用父类构造函数
        super().__init__(config or {})
        
        # 创建各引擎的reranking service实例
        self.reranking_factory = RerankingServiceFactory()
        self.image_reranking_service = self.reranking_factory.create_service('image', config)
        self.text_reranking_service = self.reranking_factory.create_service('text', config)
        self.table_reranking_service = self.reranking_factory.create_service('table', config)
        
        logger.info(f"混合reranking service初始化完成: {self.name}")
    
    def rerank_candidates(self, query: str, candidates: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """
        对混合候选结果进行reranking
        
        :param query: 查询文本
        :param candidates: 候选结果列表
        :param kwargs: 其他参数
        :return: 重排序后的结果列表
        """
        try:
            logger.info(f"开始混合reranking，输入候选数量: {len(candidates)}")
            
            if not candidates:
                logger.warning("没有候选结果，跳过reranking")
                return []
            
            # 1. 按内容类型分组候选结果
            grouped_candidates = self._group_candidates_by_type(candidates)
            
            # 2. 分别对各类型结果进行reranking
            reranked_results = {}
            for content_type, type_candidates in grouped_candidates.items():
                if type_candidates:
                    reranked_results[content_type] = self._rerank_by_type(
                        query, content_type, type_candidates, **kwargs
                    )
                else:
                    reranked_results[content_type] = []
            
            # 3. 融合各类型的reranking结果
            final_results = self._merge_reranked_results(reranked_results)
            
            # 4. 应用混合排序策略
            final_results = self._apply_hybrid_ranking_strategy(query, final_results)
            
            logger.info(f"混合reranking完成，输入: {len(candidates)}, 输出: {len(final_results)}")
            return final_results
            
        except Exception as e:
            logger.error(f"混合reranking执行失败: {str(e)}")
            # 返回原始结果
            return candidates
    
    def rerank(self, query: str, candidates: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """
        执行重排序（实现抽象方法）
        
        :param query: 查询文本
        :param candidates: 候选文档列表
        :param kwargs: 其他参数
        :return: 重排序后的文档列表
        """
        return self.rerank_candidates(query, candidates, **kwargs)
    
    def get_service_name(self) -> str:
        """
        获取服务名称（实现抽象方法）
        
        :return: 服务名称字符串
        """
        return self.name
    
    def get_supported_types(self) -> List[str]:
        """
        获取支持的内容类型（实现抽象方法）
        
        :return: 支持的内容类型列表
        """
        return ['image', 'text', 'table', 'hybrid']
    
    def _group_candidates_by_type(self, candidates: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        按内容类型分组候选结果
        
        :param candidates: 候选结果列表
        :return: 按类型分组的结果
        """
        grouped = {'image': [], 'text': [], 'table': [], 'unknown': []}
        
        for candidate in candidates:
            content_type = self._detect_content_type(candidate)
            grouped[content_type].append(candidate)
        
        logger.info(f"候选结果分组完成: 图片={len(grouped['image'])}, 文本={len(grouped['text'])}, 表格={len(grouped['table'])}, 未知={len(grouped['unknown'])}")
        return grouped
    
    def _detect_content_type(self, candidate: Dict[str, Any]) -> str:
        """
        检测候选结果的内容类型
        
        :param candidate: 候选结果
        :return: 内容类型
        """
        # 检查chunk_type字段
        chunk_type = candidate.get('chunk_type', '').lower()
        if 'image' in chunk_type or 'img' in chunk_type:
            return 'image'
        elif 'table' in chunk_type or 'tab' in chunk_type:
            return 'table'
        elif 'text' in chunk_type or 'txt' in chunk_type:
            return 'text'
        
        # 检查其他字段
        if 'image_path' in candidate or 'enhanced_description' in candidate:
            return 'image'
        elif 'table_type' in candidate or 'table_data' in candidate:
            return 'table'
        else:
            return 'text'  # 默认为文本类型
    
    def _rerank_by_type(self, query: str, content_type: str, candidates: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """
        对特定类型的结果进行reranking
        
        :param query: 查询文本
        :param content_type: 内容类型
        :param candidates: 该类型的候选结果
        :param kwargs: 其他参数
        :return: 重排序后的结果
        """
        try:
            if content_type == 'image' and self.image_reranking_service:
                return self.image_reranking_service.rerank_candidates(query, candidates, **kwargs)
            elif content_type == 'table' and self.table_reranking_service:
                return self.table_reranking_service.rerank_candidates(query, candidates, **kwargs)
            elif content_type == 'text' and self.text_reranking_service:
                return self.text_reranking_service.rerank_candidates(query, candidates, **kwargs)
            else:
                # 如果没有对应的reranking service，返回原始结果
                logger.warning(f"内容类型 {content_type} 没有对应的reranking service，返回原始结果")
                return candidates
                
        except Exception as e:
            logger.error(f"内容类型 {content_type} 的reranking执行失败: {str(e)}")
            return candidates
    
    def _merge_reranked_results(self, reranked_results: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        融合各类型的reranking结果
        
        :param reranked_results: 各类型的reranking结果
        :return: 融合后的结果
        """
        merged_results = []
        
        # 按类型顺序合并结果
        type_order = ['image', 'table', 'text']  # 优先级顺序
        
        for content_type in type_order:
            if content_type in reranked_results and reranked_results[content_type]:
                # 为每个结果添加类型标识和排序权重
                for i, result in enumerate(reranked_results[content_type]):
                    if isinstance(result, dict):
                        result['hybrid_rank'] = len(merged_results) + i
                        result['content_type'] = content_type
                        result['type_priority'] = type_order.index(content_type)
                    merged_results.append(result)
        
        logger.info(f"融合完成，总结果数量: {len(merged_results)}")
        return merged_results
    
    def _apply_hybrid_ranking_strategy(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        应用混合排序策略
        
        :param query: 查询文本
        :param results: 融合后的结果
        :return: 最终排序后的结果
        """
        try:
            if not results:
                return results
            
            # 1. 计算混合相关性分数
            for result in results:
                result['hybrid_score'] = self._calculate_hybrid_score(query, result)
            
            # 2. 按混合分数排序
            results.sort(key=lambda x: x.get('hybrid_score', 0), reverse=True)
            
            # 3. 应用多样性策略（确保不同类型的结果都有代表）
            diverse_results = self._apply_diversity_strategy(results)
            
            logger.info(f"混合排序策略应用完成，最终结果数量: {len(diverse_results)}")
            return diverse_results
            
        except Exception as e:
            logger.error(f"混合排序策略应用失败: {str(e)}")
            return results
    
    def _calculate_hybrid_score(self, query: str, result: Dict[str, Any]) -> float:
        """
        计算混合相关性分数
        
        :param query: 查询文本
        :param result: 结果项
        :return: 混合分数
        """
        try:
            # 基础分数
            base_score = result.get('relevance_score', 0.5)
            
            # 类型权重
            type_priority = result.get('type_priority', 0)
            type_weight = 1.0 - (type_priority * 0.1)  # 图片 > 表格 > 文本
            
            # 混合排序权重
            hybrid_rank = result.get('hybrid_rank', 0)
            rank_weight = 1.0 - (hybrid_rank * 0.01)  # 排名越靠前权重越高
            
            # 计算最终分数
            final_score = base_score * type_weight * rank_weight
            
            return round(final_score, 4)
            
        except Exception as e:
            logger.error(f"混合分数计算失败: {str(e)}")
            return 0.5
    
    def _apply_diversity_strategy(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        应用多样性策略，确保不同类型的结果都有代表
        
        :param results: 排序后的结果
        :return: 多样性调整后的结果
        """
        try:
            if len(results) <= 10:  # 结果数量较少时，不需要多样性调整
                return results
            
            # 按类型分组
            type_groups = {'image': [], 'table': [], 'text': []}
            for result in results:
                content_type = result.get('content_type', 'text')
                if content_type in type_groups:
                    type_groups[content_type].append(result)
            
            # 确保每种类型都有代表
            diverse_results = []
            max_per_type = max(3, len(results) // 3)  # 每种类型最多选择的数量
            
            for content_type, type_results in type_groups.items():
                if type_results:
                    # 选择该类型中分数最高的结果
                    selected = type_results[:max_per_type]
                    diverse_results.extend(selected)
            
            # 如果总数不够，从剩余结果中补充
            remaining = [r for r in results if r not in diverse_results]
            if remaining and len(diverse_results) < len(results):
                diverse_results.extend(remaining[:len(results) - len(diverse_results)])
            
            logger.info(f"多样性策略应用完成，调整前: {len(results)}, 调整后: {len(diverse_results)}")
            return diverse_results
            
        except Exception as e:
            logger.error(f"多样性策略应用失败: {str(e)}")
            return results
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            'name': self.name,
            'version': self.version,
            'enabled': True,
            'sub_services': {
                'image': self.image_reranking_service is not None,
                'text': self.text_reranking_service is not None,
                'table': self.table_reranking_service is not None
            }
        }
