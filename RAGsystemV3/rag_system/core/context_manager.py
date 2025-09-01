"""
上下文管理器模块

RAG系统的上下文管理核心组件，负责：
1. 上下文优化和重组
2. 长度控制和智能截断
3. 上下文质量评估
4. 多模态上下文支持
"""

import logging
import time
import re
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class ContextChunk:
    """上下文块数据类"""
    content: str
    chunk_id: str
    content_type: str
    relevance_score: float
    source: str
    metadata: Dict[str, Any]
    
    def __str__(self) -> str:
        return f"ContextChunk(id={self.chunk_id}, type={self.content_type}, score={self.relevance_score:.3f})"

class ContextManager:
    """上下文管理器 - 核心上下文管理组件"""
    
    def __init__(self, config_integration):
        """
        初始化上下文管理器
        
        :param config_integration: 配置集成管理器实例
        """
        self.config = config_integration
        
        # 获取配置参数
        self.max_context_length = self.config.get('rag_system.query_processing.max_context_length', 4000)
        self.max_chunks = self.config.get('rag_system.query_processing.max_chunks', 10)
        self.relevance_threshold = self.config.get('rag_system.query_processing.relevance_threshold', 0.7)
        
        # 上下文处理统计
        self.context_stats = {
            'total_processed': 0,
            'total_length': 0,
            'avg_length': 0,
            'truncation_count': 0,
            'optimization_count': 0
        }
        
        logger.info("上下文管理器初始化完成")
    
    def optimize_context(self, context_chunks: List[ContextChunk], 
                        query: str, 
                        max_length: Optional[int] = None) -> str:
        """
        优化上下文，生成最佳的上下文组合
        
        :param context_chunks: 上下文块列表
        :param query: 查询文本
        :param max_length: 最大长度限制（可选）
        :return: 优化后的上下文文本
        """
        try:
            start_time = time.time()
            
            if not context_chunks:
                logger.warning("没有提供上下文块")
                return ""
            
            # 使用配置的最大长度或传入的长度
            target_length = max_length or self.max_context_length
            
            # 1. 按相关性排序
            sorted_chunks = self._sort_by_relevance(context_chunks, query)
            
            # 2. 智能选择上下文块
            selected_chunks = self._select_optimal_chunks(sorted_chunks, target_length)
            
            # 3. 重组和格式化上下文
            optimized_context = self._reorganize_context(selected_chunks, query)
            
            # 4. 长度检查和截断
            final_context = self._ensure_length_limit(optimized_context, target_length)
            
            # 更新统计信息
            self._update_stats(len(final_context), len(context_chunks), len(selected_chunks))
            
            processing_time = time.time() - start_time
            logger.info(f"上下文优化完成，长度: {len(final_context)}/{target_length}, "
                       f"处理时间: {processing_time:.3f}s")
            
            return final_context
            
        except Exception as e:
            logger.error(f"上下文优化失败: {e}")
            # 返回原始上下文的简化版本
            return self._fallback_context(context_chunks)
    
    def _sort_by_relevance(self, context_chunks: List[ContextChunk], 
                          query: str) -> List[ContextChunk]:
        """
        按相关性对上下文块进行排序
        
        :param context_chunks: 上下文块列表
        :param query: 查询文本
        :return: 排序后的上下文块列表
        """
        try:
            # 计算查询相关性分数
            for chunk in context_chunks:
                if chunk.relevance_score <= 0:
                    chunk.relevance_score = self._calculate_query_relevance(query, chunk.content)
            
            # 按相关性分数降序排序
            sorted_chunks = sorted(context_chunks, 
                                 key=lambda x: x.relevance_score, 
                                 reverse=True)
            
            logger.debug(f"上下文块排序完成，最高相关性: {sorted_chunks[0].relevance_score:.3f}")
            return sorted_chunks
            
        except Exception as e:
            logger.error(f"上下文块排序失败: {e}")
            return context_chunks
    
    def _select_optimal_chunks(self, sorted_chunks: List[ContextChunk], 
                              target_length: int) -> List[ContextChunk]:
        """
        智能选择最优的上下文块组合
        
        :param sorted_chunks: 排序后的上下文块列表
        :param target_length: 目标长度
        :return: 选中的上下文块列表
        """
        try:
            selected_chunks = []
            current_length = 0
            chunk_count = 0
            
            for chunk in sorted_chunks:
                # 检查相关性阈值
                if chunk.relevance_score < self.relevance_threshold:
                    continue
                
                # 检查长度限制
                chunk_length = len(chunk.content)
                if current_length + chunk_length > target_length:
                    # 如果添加这个块会超出长度，尝试智能截断
                    if chunk.relevance_score > 0.9:  # 高相关性块优先
                        truncated_content = self._smart_truncate(chunk.content, 
                                                             target_length - current_length)
                        if truncated_content:
                            chunk.content = truncated_content
                            chunk_length = len(truncated_content)
                        else:
                            continue
                    else:
                        continue
                
                # 检查块数量限制
                if chunk_count >= self.max_chunks:
                    break
                
                selected_chunks.append(chunk)
                current_length += chunk_length
                chunk_count += 1
                
                # 如果已经达到目标长度，停止选择
                if current_length >= target_length:
                    break
            
            logger.debug(f"选择了 {len(selected_chunks)} 个上下文块，总长度: {current_length}")
            return selected_chunks
            
        except Exception as e:
            logger.error(f"选择最优上下文块失败: {e}")
            return sorted_chunks[:self.max_chunks]
    
    def _reorganize_context(self, selected_chunks: List[ContextChunk], 
                           query: str) -> str:
        """
        重组和格式化上下文
        
        :param selected_chunks: 选中的上下文块列表
        :param query: 查询文本
        :return: 重组后的上下文文本
        """
        try:
            if not selected_chunks:
                return ""
            
            # 按内容类型分组
            type_groups = defaultdict(list)
            for chunk in selected_chunks:
                type_groups[chunk.content_type].append(chunk)
            
            # 构建格式化的上下文
            context_parts = []
            
            # 添加文本内容
            if 'text' in type_groups:
                text_chunks = type_groups['text']
                text_content = "\n\n".join([chunk.content for chunk in text_chunks])
                context_parts.append(f"文本信息：\n{text_content}")
            
            # 添加表格内容
            if 'table' in type_groups:
                table_chunks = type_groups['table']
                table_content = "\n\n".join([chunk.content for chunk in table_chunks])
                context_parts.append(f"表格数据：\n{table_content}")
            
            # 添加图片内容
            if 'image' in type_groups:
                image_chunks = type_groups['image']
                image_descriptions = []
                for chunk in image_chunks:
                    desc = chunk.metadata.get('description', chunk.content)
                    image_descriptions.append(f"- {desc}")
                context_parts.append(f"图片信息：\n" + "\n".join(image_descriptions))
            
            # 组合所有内容
            final_context = "\n\n".join(context_parts)
            
            # 添加上下文来源信息
            sources = list(set(chunk.source for chunk in selected_chunks))
            if sources:
                final_context += f"\n\n信息来源：{', '.join(sources)}"
            
            return final_context
            
        except Exception as e:
            logger.error(f"重组上下文失败: {e}")
            # 返回简单的组合
            return "\n\n".join([chunk.content for chunk in selected_chunks])
    
    def _ensure_length_limit(self, context: str, max_length: int) -> str:
        """
        确保上下文长度不超过限制
        
        :param context: 上下文文本
        :param max_length: 最大长度
        :return: 长度限制内的上下文
        """
        try:
            if len(context) <= max_length:
                return context
            
            # 智能截断
            truncated_context = self._smart_truncate(context, max_length)
            
            if truncated_context:
                self.context_stats['truncation_count'] += 1
                logger.info(f"上下文已截断，从 {len(context)} 到 {len(truncated_context)} 字符")
                return truncated_context
            else:
                # 如果智能截断失败，使用简单截断
                simple_truncated = context[:max_length-100] + "..."
                self.context_stats['truncation_count'] += 1
                logger.warning("智能截断失败，使用简单截断")
                return simple_truncated
                
        except Exception as e:
            logger.error(f"长度限制检查失败: {e}")
            return context[:max_length] if len(context) > max_length else context
    
    def _smart_truncate(self, text: str, max_length: int) -> Optional[str]:
        """
        智能截断文本，保持语义完整性
        
        :param text: 要截断的文本
        :param max_length: 最大长度
        :return: 截断后的文本，如果失败返回None
        """
        try:
            if len(text) <= max_length:
                return text
            
            # 尝试在句子边界截断
            sentences = re.split(r'[。！？.!?]', text)
            truncated = ""
            
            for sentence in sentences:
                if len(truncated + sentence) <= max_length - 10:  # 留出一些空间
                    truncated += sentence + "。"
                else:
                    break
            
            if truncated and len(truncated) <= max_length:
                return truncated
            
            # 如果句子截断失败，尝试在段落边界截断
            paragraphs = text.split('\n\n')
            truncated = ""
            
            for paragraph in paragraphs:
                if len(truncated + paragraph) <= max_length - 20:
                    truncated += paragraph + "\n\n"
                else:
                    break
            
            if truncated and len(truncated) <= max_length:
                return truncated.strip()
            
            return None
            
        except Exception as e:
            logger.error(f"智能截断失败: {e}")
            return None
    
    def _calculate_query_relevance(self, query: str, content: str) -> float:
        """
        计算查询与内容的相关性分数
        
        :param query: 查询文本
        :param content: 内容文本
        :return: 相关性分数 (0.0-1.0)
        """
        try:
            if not query or not content:
                return 0.0
            
            # 简单的关键词匹配计算
            query_words = set(query.lower().split())
            content_words = set(content.lower().split())
            
            if not query_words or not content_words:
                return 0.0
            
            # 计算Jaccard相似度
            intersection = len(query_words.intersection(content_words))
            union = len(query_words.union(content_words))
            
            if union == 0:
                return 0.0
            
            jaccard_similarity = intersection / union
            
            # 计算词频相似度
            query_freq = {}
            content_freq = {}
            
            for word in query_words:
                query_freq[word] = query.lower().count(word)
            
            for word in content_words:
                content_freq[word] = content.lower().count(word)
            
            # 计算余弦相似度
            common_words = query_words.intersection(content_words)
            if not common_words:
                return jaccard_similarity
            
            numerator = sum(query_freq[word] * content_freq[word] for word in common_words)
            query_norm = sum(query_freq[word] ** 2 for word in query_words) ** 0.5
            content_norm = sum(content_freq[word] ** 2 for word in content_words) ** 0.5
            
            if query_norm == 0 or content_norm == 0:
                return jaccard_similarity
            
            cosine_similarity = numerator / (query_norm * content_norm)
            
            # 综合相似度
            combined_similarity = (jaccard_similarity + cosine_similarity) / 2
            
            return max(0.0, min(1.0, combined_similarity))
            
        except Exception as e:
            logger.error(f"计算查询相关性失败: {e}")
            return 0.0
    
    def _fallback_context(self, context_chunks: List[ContextChunk]) -> str:
        """
        生成备用的简化上下文
        
        :param context_chunks: 上下文块列表
        :return: 简化的上下文文本
        """
        try:
            if not context_chunks:
                return ""
            
            # 选择前几个块，简单组合
            selected_chunks = context_chunks[:min(3, len(context_chunks))]
            simple_context = "\n\n".join([chunk.content for chunk in selected_chunks])
            
            # 限制长度
            if len(simple_context) > self.max_context_length:
                simple_context = simple_context[:self.max_context_length-100] + "..."
            
            return simple_context
            
        except Exception as e:
            logger.error(f"生成备用上下文失败: {e}")
            return ""
    
    def _update_stats(self, final_length: int, total_chunks: int, selected_chunks: int):
        """更新统计信息"""
        try:
            self.context_stats['total_processed'] += 1
            self.context_stats['total_length'] += final_length
            
            # 计算平均长度
            total_processed = self.context_stats['total_processed']
            self.context_stats['avg_length'] = self.context_stats['total_length'] / total_processed
            
            # 记录优化次数
            if selected_chunks < total_chunks:
                self.context_stats['optimization_count'] += 1
                
        except Exception as e:
            logger.error(f"更新统计信息失败: {e}")
    
    def get_context_stats(self) -> Dict[str, Any]:
        """获取上下文处理统计信息"""
        return self.context_stats.copy()
    
    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态信息"""
        return {
            'status': 'ready',
            'service_type': 'Context Manager',
            'max_context_length': self.max_context_length,
            'max_chunks': self.max_chunks,
            'relevance_threshold': self.relevance_threshold,
            'context_stats': self.context_stats
        }
