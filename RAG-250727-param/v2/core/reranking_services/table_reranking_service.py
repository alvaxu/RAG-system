#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
程序说明：
## 1. TableRerankingService - 表格重排序服务
## 2. 使用DashScope大模型进行智能重排序
## 3. 支持配置开关控制是否启用大模型
## 4. 专门针对表格内容进行优化

## 主要特点：
- 使用DashScope gte-rerank-v2模型
- 表格特化的重排序策略
- 考虑表格结构、列名、数据类型等特征
- 与TextRerankingService和ImageRerankingService保持一致的接口
'''

import logging
from typing import List, Dict, Any, Optional
from .base_reranking_service import BaseRerankingService
import dashscope
from dashscope.rerank import text_rerank

logger = logging.getLogger(__name__)

class TableRerankingService(BaseRerankingService):
    """表格重排序服务 - 使用DashScope大模型"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化表格重排序服务
        
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
            logger.info(f"TableRerankingService初始化完成，使用模型: {self.model_name}")
        else:
            logger.warning("TableRerankingService初始化失败：未找到API密钥")
    
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
        return "TableRerankingService"
    
    def get_supported_types(self) -> List[str]:
        """获取支持的内容类型"""
        return ['table', 'spreadsheet', 'data_table', 'financial_table', 'hr_table']
    
    def rerank(self, query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        使用大模型对表格候选文档进行重排序
        
        :param query: 查询文本
        :param candidates: 候选文档列表
        :return: 重排序后的文档列表
        """
        try:
            # 验证候选文档
            valid_candidates = self.validate_candidates(candidates)
            if not valid_candidates:
                logger.warning("没有有效的候选文档，返回空列表")
                return []
            
            # 如果未启用大模型增强，返回原始排序
            if not self.use_llm_enhancement:
                logger.info("大模型增强未启用，返回原始排序")
                return self._fallback_rerank(query, valid_candidates)
            
            # 预处理候选文档，为表格重排序优化
            processed_candidates = self._preprocess_table_candidates(valid_candidates)
            
            # 使用DashScope大模型进行重排序
            reranked_results = self._llm_rerank(query, processed_candidates)
            
            # 后处理结果，添加表格特化的元数据
            final_results = self._postprocess_table_results(reranked_results, query)
            
            logger.info(f"表格重排序完成，处理了 {len(valid_candidates)} 个候选文档，返回 {len(final_results)} 个结果")
            return final_results
            
        except Exception as e:
            logger.error(f"表格重排序失败: {e}")
            # 降级到基础重排序
            return self._fallback_rerank(query, candidates)
    
    def _preprocess_table_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        预处理表格候选文档，为重排序优化
        
        :param candidates: 候选文档列表
        :return: 预处理后的候选文档列表
        """
        processed_candidates = []
        
        for candidate in candidates:
            try:
                # 提取表格结构信息
                table_info = self._extract_table_structure(candidate)
                
                # 构建优化的重排序文本
                rerank_text = self._build_rerank_text(candidate, table_info)
                
                processed_candidate = {
                    'original': candidate,
                    'rerank_text': rerank_text,
                    'table_info': table_info
                }
                processed_candidates.append(processed_candidate)
                
            except Exception as e:
                logger.warning(f"预处理候选文档失败: {e}")
                # 使用原始内容作为备选
                processed_candidates.append({
                    'original': candidate,
                    'rerank_text': candidate.get('content', ''),
                    'table_info': {}
                })
        
        return processed_candidates
    
    def _extract_table_structure(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取表格结构信息
        
        :param candidate: 候选文档
        :return: 表格结构信息字典
        """
        table_info = {
            'table_type': 'unknown',
            'columns': [],
            'row_count': 0,
            'column_count': 0,
            'data_completeness': 0.0,
            'business_domain': 'unknown'
        }
        
        try:
            metadata = candidate.get('metadata', {})
            content = candidate.get('content', '')
            
            # 提取表格类型
            table_info['table_type'] = metadata.get('table_type', 'unknown')
            
            # 提取列信息
            columns = metadata.get('columns', [])
            if isinstance(columns, list):
                table_info['columns'] = columns
                table_info['column_count'] = len(columns)
            
            # 提取行数信息
            table_info['row_count'] = metadata.get('table_row_count', 0)
            
            # 分析数据完整性
            if content:
                lines = content.split('\n')
                valid_lines = sum(1 for line in lines if line.strip() and not line.startswith('['))
                table_info['data_completeness'] = valid_lines / len(lines) if lines else 0.0
            
            # 识别业务领域
            table_info['business_domain'] = self._identify_business_domain(content, columns)
            
        except Exception as e:
            logger.debug(f"提取表格结构信息失败: {e}")
        
        return table_info
    
    def _identify_business_domain(self, content: str, columns: List[str]) -> str:
        """
        识别表格的业务领域
        
        :param content: 表格内容
        :param columns: 列名列表
        :return: 业务领域
        """
        try:
            content_lower = content.lower()
            columns_lower = [col.lower() for col in columns]
            
            # 财务领域关键词
            financial_keywords = ['收入', '支出', '利润', '成本', '费用', '资产', '负债', '权益', '现金流', '预算', '实际', '差异', '金额']
            if any(kw in content_lower for kw in financial_keywords) or any(any(kw in col for kw in financial_keywords) for col in columns_lower):
                return 'finance'
            
            # 人事领域关键词
            hr_keywords = ['姓名', '员工', '部门', '职位', '薪资', '工资', '奖金', '入职', '离职', '考勤', '绩效', '工号', '性别', '年龄']
            if any(kw in content_lower for kw in hr_keywords) or any(any(kw in col for kw in hr_keywords) for col in columns_lower):
                return 'hr'
            
            # 库存领域关键词
            inventory_keywords = ['产品', '商品', '库存', '数量', '进货', '出货', '库存量', '库存值', '货号', '型号', '规格', '单价', '总价']
            if any(kw in content_lower for kw in inventory_keywords) or any(any(kw in col for kw in inventory_keywords) for col in columns_lower):
                return 'inventory'
            
            # 统计领域关键词
            statistical_keywords = ['数量', '次数', '频率', '比例', '百分比', '增长', '下降', '趋势', '统计', '汇总', '总数', '平均', '最大', '最小']
            if any(kw in content_lower for kw in statistical_keywords) or any(any(kw in col for kw in statistical_keywords) for col in columns_lower):
                return 'statistical'
            
            return 'general'
            
        except Exception as e:
            logger.debug(f"识别业务领域失败: {e}")
            return 'unknown'
    
    def _build_rerank_text(self, candidate: Dict[str, Any], table_info: Dict[str, Any]) -> str:
        """
        构建用于重排序的文本
        
        :param candidate: 候选文档
        :param table_info: 表格结构信息
        :return: 重排序文本
        """
        try:
            content = candidate.get('content', '')
            metadata = candidate.get('metadata', {})
            
            # 构建表格描述
            table_description = f"表格类型: {table_info['table_type']}, "
            table_description += f"业务领域: {table_info['business_domain']}, "
            table_description += f"列数: {table_info['column_count']}, "
            table_description += f"行数: {table_info['row_count']}, "
            table_description += f"数据完整性: {table_info['data_completeness']:.2f}"
            
            # 添加列名信息
            if table_info['columns']:
                columns_text = ", ".join(table_info['columns'][:5])  # 只显示前5列
                if len(table_info['columns']) > 5:
                    columns_text += f"等{len(table_info['columns'])}列"
                table_description += f", 列名: {columns_text}"
            
            # 添加文档信息
            doc_name = metadata.get('document_name', '未知文档')
            page_number = metadata.get('page_number', '未知页')
            table_description += f", 来源: {doc_name} 第{page_number}页"
            
            # 组合最终文本
            rerank_text = f"{table_description}\n\n表格内容:\n{content}"
            
            return rerank_text
            
        except Exception as e:
            logger.debug(f"构建重排序文本失败: {e}")
            return candidate.get('content', '')
    
    def _llm_rerank(self, query: str, processed_candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        使用DashScope大模型进行重排序
        
        :param query: 查询文本
        :param processed_candidates: 预处理后的候选文档
        :return: 重排序后的结果
        """
        try:
            # 准备重排序数据
            documents = [candidate['rerank_text'] for candidate in processed_candidates]
            
            # 调用DashScope重排序API - 与TextRerankingService和ImageRerankingService保持一致
            response = text_rerank.TextReRank.call(
                model=self.model_name,
                query=query,
                documents=documents,
                top_k=min(self.top_k, len(documents))
            )
            
            if response.status_code == 200:
                # 处理重排序结果
                reranked_results = []
                for result in response.output.results:
                    index = result.index
                    score = result.relevance_score
                    
                    if score >= self.similarity_threshold:
                        original_candidate = processed_candidates[index]['original']
                        table_info = processed_candidates[index]['table_info']
                        
                        reranked_results.append({
                            'doc': original_candidate,
                            'score': score,
                            'table_info': table_info,
                            'rerank_source': 'llm'
                        })
                
                # 按分数排序
                reranked_results.sort(key=lambda x: x['score'], reverse=True)
                logger.info(f"大模型重排序成功，返回 {len(reranked_results)} 个结果")
                return reranked_results
            else:
                logger.warning(f"DashScope重排序API调用失败: {response.message}")
                return self._fallback_rerank(query, [c['original'] for c in processed_candidates])
                
        except Exception as e:
            logger.error(f"大模型重排序失败: {e}")
            return self._fallback_rerank(query, [c['original'] for c in processed_candidates])
    
    def _fallback_rerank(self, query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        降级重排序策略
        
        :param query: 查询文本
        :param candidates: 候选文档列表
        :return: 重排序后的结果
        """
        try:
            # 简单的基于关键词匹配的降级重排序
            scored_candidates = []
            
            for candidate in candidates:
                score = self._calculate_fallback_score(query, candidate)
                if score > 0:
                    scored_candidates.append({
                        'doc': candidate,
                        'score': score,
                        'table_info': {},
                        'rerank_source': 'fallback'
                    })
            
            # 按分数排序并限制数量
            scored_candidates.sort(key=lambda x: x['score'], reverse=True)
            return scored_candidates[:self.top_k]
            
        except Exception as e:
            logger.error(f"降级重排序失败: {e}")
            return candidates[:self.top_k]
    
    def _calculate_fallback_score(self, query: str, candidate: Dict[str, Any]) -> float:
        """
        计算降级重排序分数
        
        :param query: 查询文本
        :param candidate: 候选文档
        :return: 分数
        """
        try:
            score = 0.0
            content = candidate.get('content', '').lower()
            metadata = candidate.get('metadata', {})
            query_lower = query.lower()
            
            # 内容匹配分数
            query_words = query_lower.split()
            matched_words = sum(1 for word in query_words if word in content)
            if matched_words > 0:
                score += min(1.0, matched_words / len(query_words)) * 0.6
            
            # 列名匹配分数
            columns = metadata.get('columns', [])
            if isinstance(columns, list):
                for col in columns:
                    if isinstance(col, str) and query_lower in col.lower():
                        score += 0.3
            
            # 表格类型匹配分数
            table_type = metadata.get('table_type', '').lower()
            if query_lower in table_type:
                score += 0.1
            
            return score
            
        except Exception as e:
            logger.debug(f"计算降级分数失败: {e}")
            return 0.0
    
    def _postprocess_table_results(self, reranked_results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        后处理重排序结果，添加表格特化的元数据
        
        :param reranked_results: 重排序结果
        :param query: 查询文本
        :return: 后处理后的结果
        """
        try:
            for result in reranked_results:
                # 添加表格质量评分
                table_info = result.get('table_info', {})
                quality_score = self._calculate_table_quality_score(table_info)
                result['table_quality_score'] = quality_score
                
                # 添加查询相关性评分
                relevance_score = self._calculate_query_relevance(query, result['doc'])
                result['query_relevance_score'] = relevance_score
                
                # 添加综合评分
                result['final_score'] = (result['score'] * 0.7 + 
                                       quality_score * 0.2 + 
                                       relevance_score * 0.1)
            
            # 按综合评分重新排序
            reranked_results.sort(key=lambda x: x['final_score'], reverse=True)
            
            return reranked_results
            
        except Exception as e:
            logger.error(f"后处理表格结果失败: {e}")
            return reranked_results
    
    def _calculate_table_quality_score(self, table_info: Dict[str, Any]) -> float:
        """
        计算表格质量评分
        
        :param table_info: 表格结构信息
        :return: 质量评分 (0-1)
        """
        try:
            score = 0.0
            
            # 数据完整性 (40%)
            score += table_info.get('data_completeness', 0.0) * 0.4
            
            # 列数合理性 (30%)
            column_count = table_info.get('column_count', 0)
            if 2 <= column_count <= 20:
                score += 0.3
            elif column_count > 20:
                score += 0.15
            else:
                score += 0.1
            
            # 类型识别 (20%)
            if table_info.get('table_type') not in ['unknown', 'general']:
                score += 0.2
            
            # 业务领域识别 (10%)
            if table_info.get('business_domain') not in ['unknown', 'general']:
                score += 0.1
            
            return min(1.0, score)
            
        except Exception as e:
            logger.debug(f"计算表格质量评分失败: {e}")
            return 0.0
    
    def _calculate_query_relevance(self, query: str, candidate: Dict[str, Any]) -> float:
        """
        计算查询相关性评分
        
        :param query: 查询文本
        :param candidate: 候选文档
        :return: 相关性评分 (0-1)
        """
        try:
            score = 0.0
            content = candidate.get('content', '').lower()
            metadata = candidate.get('metadata', {})
            query_lower = query.lower()
            
            # 内容相关性
            query_words = query_lower.split()
            content_words = content.split()
            common_words = set(query_words) & set(content_words)
            if common_words:
                score += len(common_words) / len(query_words) * 0.5
            
            # 列名相关性
            columns = metadata.get('columns', [])
            if isinstance(columns, list):
                for col in columns:
                    if isinstance(col, str) and query_lower in col.lower():
                        score += 0.3
            
            # 表格类型相关性
            table_type = metadata.get('table_type', '').lower()
            if query_lower in table_type:
                score += 0.2
            
            return min(1.0, score)
            
        except Exception as e:
            logger.debug(f"计算查询相关性失败: {e}")
            return 0.0
