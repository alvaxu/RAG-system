"""
记忆压缩引擎

基于RAG系统V3的LLM调用机制，实现智能记忆压缩功能
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

from .models import MemoryChunk, CompressionRecord, CompressionRequest
from .exceptions import CompressionError
from .memory_config_manager import MemoryConfigManager

logger = logging.getLogger(__name__)


class MemoryCompressionEngine:
    """
    记忆压缩引擎
    
    基于现有LLM调用机制，实现多种记忆压缩策略
    """
    
    def __init__(self, config_manager: MemoryConfigManager, llm_caller=None):
        """
        初始化记忆压缩引擎
        
        Args:
            config_manager: 记忆配置管理器实例
            llm_caller: LLM调用器实例（可选）
        """
        self.config_manager = config_manager
        self.llm_caller = llm_caller
        self.compression_config = config_manager.get_compression_config()
        
        # 压缩统计
        self.compression_stats = {
            'total_compressions': 0,
            'total_original_count': 0,
            'total_compressed_count': 0,
            'avg_compression_ratio': 0.0,
            'last_compression_time': None
        }
        
        logger.info("记忆压缩引擎初始化完成")
    
    def compress_memories(self, memories: List[MemoryChunk], 
                         request: CompressionRequest) -> Tuple[List[MemoryChunk], CompressionRecord]:
        """
        压缩记忆列表
        
        Args:
            memories: 待压缩的记忆列表
            request: 压缩请求
            
        Returns:
            Tuple[List[MemoryChunk], CompressionRecord]: 压缩后的记忆列表和压缩记录
            
        Raises:
            CompressionError: 压缩失败
        """
        try:
            start_time = time.time()
            
            if not memories:
                logger.warning("没有记忆需要压缩")
                return [], self._create_compression_record(memories, [], request)
            
            # 检查是否需要压缩
            if not self._should_compress(memories, request):
                logger.info("记忆数量未达到压缩阈值，跳过压缩")
                return memories, self._create_compression_record(memories, memories, request)
            
            # 根据策略执行压缩
            if request.strategy == "semantic":
                compressed_memories = self._semantic_compression(memories, request)
            elif request.strategy == "temporal":
                compressed_memories = self._temporal_compression(memories, request)
            elif request.strategy == "importance":
                compressed_memories = self._importance_compression(memories, request)
            else:
                raise CompressionError(f"不支持的压缩策略: {request.strategy}")
            
            # 创建压缩记录
            compression_record = self._create_compression_record(memories, compressed_memories, request)
            
            # 更新统计信息
            self._update_stats(memories, compressed_memories)
            
            processing_time = time.time() - start_time
            logger.info(f"记忆压缩完成，原始: {len(memories)}, 压缩后: {len(compressed_memories)}, "
                       f"压缩比例: {compression_record.compression_ratio:.2f}, 耗时: {processing_time:.2f}s")
            
            return compressed_memories, compression_record
            
        except Exception as e:
            logger.error(f"记忆压缩失败: {e}")
            raise CompressionError(f"记忆压缩失败: {e}") from e
    
    def _should_compress(self, memories: List[MemoryChunk], request: CompressionRequest) -> bool:
        """
        检查是否需要压缩
        
        Args:
            memories: 记忆列表
            request: 压缩请求
            
        Returns:
            bool: 是否需要压缩
        """
        if request.force:
            return True
        
        threshold = request.threshold or self.compression_config.get('threshold', 20)
        return len(memories) > threshold
    
    def _semantic_compression(self, memories: List[MemoryChunk], 
                             request: CompressionRequest) -> List[MemoryChunk]:
        """
        语义压缩：基于内容相似度合并相关记忆
        
        Args:
            memories: 记忆列表
            request: 压缩请求
            
        Returns:
            List[MemoryChunk]: 压缩后的记忆列表
        """
        try:
            if not self.llm_caller:
                logger.warning("LLM调用器不可用，使用基础语义压缩")
                return self._basic_semantic_compression(memories, request)
            
            # 使用LLM进行智能语义压缩
            return self._llm_semantic_compression(memories, request)
            
        except Exception as e:
            logger.warning(f"语义压缩失败，使用基础压缩: {e}")
            return self._basic_semantic_compression(memories, request)
    
    def _llm_semantic_compression(self, memories: List[MemoryChunk], 
                                 request: CompressionRequest) -> List[MemoryChunk]:
        """
        基于LLM的语义压缩
        
        Args:
            memories: 记忆列表
            request: 压缩请求
            
        Returns:
            List[MemoryChunk]: 压缩后的记忆列表
        """
        try:
            # 构建压缩提示词
            prompt = self._build_compression_prompt(memories, request)
            
            # 调用LLM进行压缩
            response = self.llm_caller.generate_answer(
                query_text="请压缩以下对话记忆，保留重要信息：",
                context_chunks=[],  # 这里需要适配现有的ContextChunk格式
                prompt_template="memory_compression"
            )
            
            # 解析LLM响应，提取压缩后的记忆
            compressed_memories = self._parse_compression_response(response.answer, memories)
            
            return compressed_memories
            
        except Exception as e:
            logger.error(f"LLM语义压缩失败: {e}")
            raise CompressionError("LLM语义压缩失败") from e
    
    def _build_compression_prompt(self, memories: List[MemoryChunk], 
                                 request: CompressionRequest) -> str:
        """
        构建压缩提示词
        
        Args:
            memories: 记忆列表
            request: 压缩请求
            
        Returns:
            str: 压缩提示词
        """
        # 格式化记忆内容
        memory_texts = []
        for i, memory in enumerate(memories):
            memory_texts.append(f"{i+1}. {memory.content}")
        
        memories_text = "\n".join(memory_texts)
        
        prompt = f"""请对以下对话记忆进行智能压缩，保留重要信息并合并相关内容：

原始记忆：
{memories_text}

压缩要求：
- 保留重要的对话内容和关键信息
- 合并相似或重复的内容
- 保持时间顺序和逻辑关系
- 压缩比例控制在{request.max_ratio:.1%}以内

请返回压缩后的记忆列表，每行一个记忆项。"""
        
        return prompt
    
    def _parse_compression_response(self, response: str, original_memories: List[MemoryChunk]) -> List[MemoryChunk]:
        """
        解析LLM压缩响应
        
        Args:
            response: LLM响应文本
            original_memories: 原始记忆列表
            
        Returns:
            List[MemoryChunk]: 解析后的记忆列表
        """
        try:
            compressed_memories = []
            lines = response.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # 创建压缩后的记忆块
                compressed_memory = MemoryChunk(
                    session_id=original_memories[0].session_id if original_memories else "",
                    content=line,
                    content_type="text",
                    relevance_score=0.8,  # 压缩后的记忆默认较高相关性
                    importance_score=0.8,
                    metadata={
                        'compressed': True,
                        'original_count': len(original_memories),
                        'compression_time': datetime.now().isoformat()
                    }
                )
                compressed_memories.append(compressed_memory)
            
            return compressed_memories
            
        except Exception as e:
            logger.error(f"解析压缩响应失败: {e}")
            # 返回原始记忆作为回退
            return original_memories
    
    def _basic_semantic_compression(self, memories: List[MemoryChunk], 
                                   request: CompressionRequest) -> List[MemoryChunk]:
        """
        基础语义压缩：基于关键词和长度进行简单压缩
        
        Args:
            memories: 记忆列表
            request: 压缩请求
            
        Returns:
            List[MemoryChunk]: 压缩后的记忆列表
        """
        # 按重要性排序
        sorted_memories = sorted(memories, key=lambda x: x.importance_score, reverse=True)
        
        # 计算目标数量
        target_count = max(1, int(len(memories) * request.max_ratio))
        
        # 选择最重要的记忆
        compressed_memories = sorted_memories[:target_count]
        
        # 合并相似内容
        merged_memories = self._merge_similar_memories(compressed_memories)
        
        return merged_memories
    
    def _merge_similar_memories(self, memories: List[MemoryChunk]) -> List[MemoryChunk]:
        """
        合并相似的记忆
        
        Args:
            memories: 记忆列表
            
        Returns:
            List[MemoryChunk]: 合并后的记忆列表
        """
        if len(memories) <= 1:
            return memories
        
        merged = []
        used_indices = set()
        
        for i, memory in enumerate(memories):
            if i in used_indices:
                continue
            
            # 查找相似记忆
            similar_memories = [memory]
            for j, other_memory in enumerate(memories[i+1:], i+1):
                if j in used_indices:
                    continue
                
                # 简单的相似度检查（基于关键词重叠）
                if self._calculate_similarity(memory.content, other_memory.content) > 0.6:
                    similar_memories.append(other_memory)
                    used_indices.add(j)
            
            # 合并相似记忆
            if len(similar_memories) > 1:
                merged_content = self._merge_memory_contents(similar_memories)
                merged_memory = MemoryChunk(
                    session_id=memory.session_id,
                    content=merged_content,
                    content_type=memory.content_type,
                    relevance_score=max(m.content for m in similar_memories),
                    importance_score=max(m.importance_score for m in similar_memories),
                    metadata={
                        'merged': True,
                        'original_count': len(similar_memories),
                        'merged_from': [m.chunk_id for m in similar_memories]
                    }
                )
                merged.append(merged_memory)
            else:
                merged.append(memory)
            
            used_indices.add(i)
        
        return merged
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的相似度
        
        Args:
            text1: 文本1
            text2: 文本2
            
        Returns:
            float: 相似度分数 (0-1)
        """
        # 简单的关键词重叠相似度
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _merge_memory_contents(self, memories: List[MemoryChunk]) -> str:
        """
        合并记忆内容
        
        Args:
            memories: 记忆列表
            
        Returns:
            str: 合并后的内容
        """
        # 按时间排序
        sorted_memories = sorted(memories, key=lambda x: x.created_at)
        
        # 合并内容，去重
        contents = []
        seen_content = set()
        
        for memory in sorted_memories:
            if memory.content not in seen_content:
                contents.append(memory.content)
                seen_content.add(memory.content)
        
        return " | ".join(contents)
    
    def _temporal_compression(self, memories: List[MemoryChunk], 
                             request: CompressionRequest) -> List[MemoryChunk]:
        """
        时间压缩：基于时间间隔保留重要记忆
        
        Args:
            memories: 记忆列表
            request: 压缩请求
            
        Returns:
            List[MemoryChunk]: 压缩后的记忆列表
        """
        # 按时间排序
        sorted_memories = sorted(memories, key=lambda x: x.created_at)
        
        # 计算时间间隔
        time_intervals = []
        for i in range(1, len(sorted_memories)):
            interval = (sorted_memories[i].created_at - sorted_memories[i-1].created_at).total_seconds()
            time_intervals.append(interval)
        
        # 选择时间间隔较大的记忆（表示重要事件）
        compressed_memories = [sorted_memories[0]]  # 保留第一个
        
        for i, interval in enumerate(time_intervals):
            if interval > 300:  # 5分钟以上的间隔认为是重要事件
                compressed_memories.append(sorted_memories[i+1])
        
        # 如果压缩后仍然太多，按重要性进一步筛选
        target_count = max(1, int(len(memories) * request.max_ratio))
        if len(compressed_memories) > target_count:
            compressed_memories = sorted(compressed_memories, key=lambda x: x.importance_score, reverse=True)[:target_count]
        
        return compressed_memories
    
    def _importance_compression(self, memories: List[MemoryChunk], 
                               request: CompressionRequest) -> List[MemoryChunk]:
        """
        重要性压缩：基于重要性分数保留重要记忆
        
        Args:
            memories: 记忆列表
            request: 压缩请求
            
        Returns:
            List[MemoryChunk]: 压缩后的记忆列表
        """
        # 按重要性排序
        sorted_memories = sorted(memories, key=lambda x: x.importance_score, reverse=True)
        
        # 计算目标数量
        target_count = max(1, int(len(memories) * request.max_ratio))
        
        # 选择最重要的记忆
        compressed_memories = sorted_memories[:target_count]
        
        return compressed_memories
    
    def _create_compression_record(self, original_memories: List[MemoryChunk], 
                                  compressed_memories: List[MemoryChunk], 
                                  request: CompressionRequest) -> CompressionRecord:
        """
        创建压缩记录
        
        Args:
            original_memories: 原始记忆列表
            compressed_memories: 压缩后记忆列表
            request: 压缩请求
            
        Returns:
            CompressionRecord: 压缩记录
        """
        original_count = len(original_memories)
        compressed_count = len(compressed_memories)
        compression_ratio = compressed_count / original_count if original_count > 0 else 1.0
        
        return CompressionRecord(
            session_id=request.session_id,
            original_count=original_count,
            compressed_count=compressed_count,
            compression_ratio=compression_ratio,
            strategy=request.strategy,
            metadata={
                'request_id': str(time.time()),
                'compression_time': datetime.now().isoformat(),
                'max_ratio': request.max_ratio,
                'force': request.force
            }
        )
    
    def _update_stats(self, original_memories: List[MemoryChunk], 
                     compressed_memories: List[MemoryChunk]) -> None:
        """
        更新压缩统计信息
        
        Args:
            original_memories: 原始记忆列表
            compressed_memories: 压缩后记忆列表
        """
        self.compression_stats['total_compressions'] += 1
        self.compression_stats['total_original_count'] += len(original_memories)
        self.compression_stats['total_compressed_count'] += len(compressed_memories)
        
        # 计算平均压缩比例
        if self.compression_stats['total_original_count'] > 0:
            self.compression_stats['avg_compression_ratio'] = (
                self.compression_stats['total_compressed_count'] / 
                self.compression_stats['total_original_count']
            )
        
        self.compression_stats['last_compression_time'] = datetime.now()
    
    def get_compression_stats(self) -> Dict[str, Any]:
        """
        获取压缩统计信息
        
        Returns:
            Dict[str, Any]: 压缩统计信息
        """
        return self.compression_stats.copy()
