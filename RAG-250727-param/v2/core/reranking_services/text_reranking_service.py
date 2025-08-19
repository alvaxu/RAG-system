'''
程序说明：
## 1. TextRerankingService - 文本重排序服务
## 2. 使用DashScope大模型进行智能重排序
## 3. 支持配置开关控制是否启用大模型
## 4. 与原有DashScopeRerankingEngine保持兼容

## 主要变化：
- 从规则化策略改为使用DashScope大模型
- 添加use_llm_enhancement配置开关
- 保持原有的接口和错误处理机制
'''

import logging
from typing import List, Dict, Any, Optional
from .base_reranking_service import BaseRerankingService
import dashscope
from dashscope.rerank import text_rerank

logger = logging.getLogger(__name__)

class TextRerankingService(BaseRerankingService):
    """文本重排序服务 - 使用DashScope大模型"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化文本重排序服务
        
        :param config: 配置字典
        """
        super().__init__(config)
        
        # 大模型配置 - 完全依赖配置文件，不设置硬编码默认值
        self.use_llm_enhancement = config.get('use_llm_enhancement')
        if self.use_llm_enhancement is None:
            raise ValueError("配置中缺少 'use_llm_enhancement' 参数")
            
        self.model_name = config.get('model_name')
        if not self.model_name:
            raise ValueError("配置中缺少 'model_name' 参数")
            
        self.top_k = config.get('target_count')
        if self.top_k is None:
            raise ValueError("配置中缺少 'target_count' 参数")
            
        self.similarity_threshold = config.get('similarity_threshold')
        if self.similarity_threshold is None:
            raise ValueError("配置中缺少 'similarity_threshold' 参数")
        
        # API密钥管理
        self.api_key = self._get_api_key()
        if self.api_key:
            dashscope.api_key = self.api_key
            logger.info(f"TextRerankingService初始化完成，使用模型: {self.model_name}")
        else:
            logger.warning("TextRerankingService初始化失败：未找到API密钥")
    
    def _get_api_key(self) -> Optional[str]:
        """获取DashScope API密钥"""
        try:
            # 尝试从配置中获取
            if hasattr(self.config, 'api_key') and self.config.api_key:
                return self.config.api_key
            
            # 尝试从环境变量获取
            import os
            api_key = os.getenv('DASHSCOPE_API_KEY')
            if api_key:
                return api_key
            
            # 尝试从API密钥管理器获取（与主程序保持一致）
            try:
                from config.api_key_manager import APIKeyManager
                api_key_manager = APIKeyManager()
                api_key = api_key_manager.get_dashscope_api_key()
                if api_key:
                    return api_key
            except ImportError:
                pass
            
            return None
            
        except Exception as e:
            logger.error(f"获取API密钥失败: {e}")
            return None
    
    def get_service_name(self) -> str:
        """获取服务名称"""
        return "TextRerankingService"
    
    def get_supported_types(self) -> List[str]:
        """获取支持的内容类型"""
        return ['text', 'markdown', 'document']
    
    def rerank(self, query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        使用大模型对文本候选文档进行重排序
        
        :param query: 查询文本
        :param candidates: 候选文档列表
        :return: 重排序后的文档列表
        """
        if not self.use_llm_enhancement:
            logger.info("大模型增强未启用，使用规则化策略")
            return self._rule_based_rerank(query, candidates)
        
        if not self.api_key:
            logger.warning("API密钥未配置，回退到规则化策略")
            return self._rule_based_rerank(query, candidates)
        
        try:
            # 验证候选文档
            valid_candidates = self.validate_candidates(candidates)
            if not valid_candidates:
                logger.warning("没有有效的候选文档")
                return []
            
            # 预处理候选文档
            processed_candidates = self.preprocess_candidates(valid_candidates)
            
            # 使用大模型进行重排序
            logger.info(f"开始大模型重排序，候选文档数量: {len(processed_candidates)}")
            reranked_results = self._llm_rerank(query, processed_candidates)
            
            # 记录统计信息
            self.log_reranking_stats(query, len(candidates), len(reranked_results))
            
            logger.info(f"大模型重排序完成，返回 {len(reranked_results)} 个结果")
            return reranked_results
            
        except Exception as e:
            logger.error(f"大模型重排序失败: {e}，回退到规则化策略")
            return self._rule_based_rerank(query, candidates)
    
    def _llm_rerank(self, query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        使用DashScope大模型进行重排序 - 完全按照老的reranking引擎实现
        
        :param query: 查询文本
        :param candidates: 候选文档列表
        :return: 重排序后的文档列表
        """
        try:
            # 准备文档文本 - 与老的reranking引擎完全一致
            documents_text = [doc.get('content', '') for doc in candidates]
            
            logger.info(f"开始调用DashScope API，模型: {self.model_name}, top_k: {self.top_k}")
            logger.info(f"查询: {query}")
            logger.info(f"文档数量: {len(documents_text)}")
            
            # 调用DashScope reranking API - 与老的reranking引擎完全一致
            response = text_rerank.TextReRank.call(
                model=self.model_name,
                query=query,
                documents=documents_text,
                top_k=min(self.top_k, len(candidates))
            )
            
            # 详细的调试信息
            logger.info(f"API响应类型: {type(response)}")
            logger.info(f"API响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                # 处理响应结果 - 与老的reranking引擎完全一致
                reranked_docs = self._process_rerank_response(response, candidates)
                logger.info(f"大模型重排序完成，处理了 {len(reranked_docs)} 个文档")
                return reranked_docs
            else:
                logger.error(f"Reranking API调用失败: {response.message}")
                return candidates
                
        except Exception as e:
            logger.error(f"大模型重排序过程中发生错误: {str(e)}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            return candidates
    
    def _process_rerank_response(self, response: Any, original_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        处理重排序API响应
        
        :param response: API响应对象
        :param original_docs: 原始文档列表
        :return: 处理后的文档列表
        """
        reranked_docs = []
        
        try:
            # 解析响应结果
            results = response.output.results
            
            for result in results:
                doc_index = result.index
                if 0 <= doc_index < len(original_docs):
                    # 复制原始文档并添加排序信息
                    doc = original_docs[doc_index].copy()
                    doc['rerank_score'] = result.relevance_score
                    doc['rerank_rank'] = len(reranked_docs) + 1
                    doc['reranking_method'] = 'llm'
                    reranked_docs.append(doc)
            
            # 按分数降序排列
            reranked_docs.sort(key=lambda x: x.get('rerank_score', 0), reverse=True)
            
            # 限制返回结果数量，只返回配置中指定的target_count数量
            target_count = self.get_config_value('target_count', 10)
            if len(reranked_docs) > target_count:
                reranked_docs = reranked_docs[:target_count]
                logger.info(f"限制结果数量到 {target_count} 个（从 {len(original_docs)} 个中筛选）")
            
        except Exception as e:
            logger.error(f"处理reranking响应时发生错误: {str(e)}")
            return original_docs[:self.get_config_value('target_count', 10)]
            
        return reranked_docs
    
    def _rule_based_rerank(self, query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        规则化重排序（备用方案）
        
        :param query: 查询文本
        :param candidates: 候选文档列表
        :return: 重排序后的文档列表
        """
        logger.info("使用规则化重排序策略")
        
        try:
            # 为每个候选文档计算综合评分
            scored_candidates = []
            for doc in candidates:
                score = self._calculate_rule_based_score(doc)
                doc_copy = doc.copy()
                doc_copy['rule_score'] = score
                doc_copy['reranking_method'] = 'rule'
                scored_candidates.append(doc_copy)
            
            # 按评分降序排列
            scored_candidates.sort(key=lambda x: x.get('rule_score', 0), reverse=True)
            
            # 限制结果数量
            max_results = self.get_config_value('target_count', 10)
            final_results = scored_candidates[:max_results]
            
            # 添加排名信息
            for i, result in enumerate(final_results):
                result['rerank_rank'] = i + 1
            
            logger.info(f"规则化重排序完成，返回 {len(final_results)} 个结果")
            return final_results
            
        except Exception as e:
            logger.error(f"规则化重排序失败: {e}")
            return candidates[:self.get_config_value('target_count', 10)]
    
    def _calculate_rule_based_score(self, doc: Dict[str, Any]) -> float:
        """
        计算规则化评分
        
        :param doc: 文档字典
        :return: 评分分数
        """
        score = 0.0
        
        try:
            # 内容长度评分
            content = doc.get('content', '')
            if content:
                length_score = min(len(content) / 1000.0, 1.0)  # 标准化长度
                score += length_score * self.get_config_value('weights', {}).get('content_length', 0.3)
            
            # 结构完整性评分
            if 'metadata' in doc and doc['metadata']:
                score += 0.2 * self.get_config_value('weights', {}).get('structure', 0.2)
            
            # 词汇丰富度评分（简单实现）
            if content:
                unique_words = len(set(content.split()))
                vocab_score = min(unique_words / 100.0, 1.0)
                score += vocab_score * self.get_config_value('weights', {}).get('vocabulary', 0.25)
            
            # 专业术语评分（简单实现）
            if content and any(term in content.lower() for term in ['技术', '系统', '算法', '模型', '数据']):
                score += 0.25 * self.get_config_value('weights', {}).get('professional_terms', 0.25)
            
        except Exception as e:
            logger.error(f"计算规则化评分时发生错误: {e}")
            score = 0.0
        
        return score
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)
