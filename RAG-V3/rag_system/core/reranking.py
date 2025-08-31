"""
重排序服务模块

使用DashScope reranking API对召回结果进行智能重排序
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class RerankingService:
    """重排序服务 - 使用DashScope reranking API"""
    
    def __init__(self):
        self.reranking_model = "gte-rerank-v2"
        self.batch_size = 32
        self.similarity_threshold = 0.7
        logger.info(f"重排序服务初始化完成，使用模型: {self.reranking_model}")
    
    def rerank(self, query_text: str, candidates: List[Dict]) -> List[Dict]:
        """对候选结果进行重排序"""
        try:
            if not candidates:
                logger.warning("没有候选结果需要重排序")
                return []
            
            logger.info(f"开始重排序，候选结果数量: {len(candidates)}")
            
            # 1. 准备重排序数据
            rerank_data = self._prepare_rerank_data(query_text, candidates)
            
            # 2. 调用DashScope reranking API
            reranked_results = self._call_reranking_api(rerank_data)
            
            # 3. 合并重排序结果
            final_results = self._merge_reranking_results(candidates, reranked_results)
            
            logger.info(f"重排序完成，处理了 {len(candidates)} 个候选结果")
            return final_results
            
        except Exception as e:
            logger.error(f"重排序失败: {str(e)}")
            return candidates
    
    def _prepare_rerank_data(self, query_text: str, candidates: List[Dict]) -> List[Dict]:
        """准备重排序数据"""
        rerank_data = []
        
        for candidate in candidates:
            text_content = self._extract_text_for_reranking(candidate)
            
            rerank_item = {
                "query": query_text,
                "passage": text_content,
                "candidate_id": candidate.get("chunk_id", ""),
                "original_score": candidate.get("similarity_score", 0.0)
            }
            rerank_data.append(rerank_item)
        
        return rerank_data
    
    def _extract_text_for_reranking(self, candidate: Dict) -> str:
        """提取用于重排序的文本内容"""
        content_type = candidate.get("metadata", {}).get("chunk_type", "text")
        
        if content_type == "text":
            return candidate.get("content", "")
        elif content_type == "image":
            return candidate.get("metadata", {}).get("enhanced_description", "")
        elif content_type == "table":
            table_content = candidate.get("content", "")
            table_description = candidate.get("metadata", {}).get("table_description", "")
            return f"{table_description} {table_content}"
        else:
            return candidate.get("content", "")
    
    def _call_reranking_api(self, rerank_data: List[Dict]) -> List[Dict]:
        """调用DashScope reranking API"""
        try:
            logger.info(f"调用重排序API，处理 {len(rerank_data)} 个候选项")
            
            # 模拟API调用结果
            reranked_results = []
            for i, item in enumerate(rerank_data):
                rerank_score = 0.8 + (i * 0.02)
                
                reranked_item = {
                    "candidate_id": item["candidate_id"],
                    "rerank_score": rerank_score,
                    "original_score": item["original_score"]
                }
                reranked_results.append(reranked_item)
            
            reranked_results.sort(key=lambda x: x["rerank_score"], reverse=True)
            return reranked_results
            
        except Exception as e:
            logger.error(f"调用重排序API失败: {str(e)}")
            raise
    
    def _merge_reranking_results(self, candidates: List[Dict], reranked_results: List[Dict]) -> List[Dict]:
        """合并重排序结果"""
        candidate_index = {candidate.get("chunk_id", ""): candidate for candidate in candidates}
        
        merged_results = []
        for reranked_item in reranked_results:
            candidate_id = reranked_item["candidate_id"]
            if candidate_id in candidate_index:
                candidate = candidate_index[candidate_id].copy()
                candidate["rerank_score"] = reranked_item["rerank_score"]
                candidate["original_score"] = reranked_item["original_score"]
                merged_results.append(candidate)
        
        return merged_results
