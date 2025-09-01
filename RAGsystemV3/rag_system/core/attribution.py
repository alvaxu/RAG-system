"""
RAG溯源模块

RAG系统的溯源模块，负责答案来源追踪、相关性评分和格式化溯源信息
为RAG系统提供完整的答案可信度支持
"""

import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SourceAttribution:
    """来源溯源信息"""
    chunk_id: str                      # 内容块ID
    document_name: str                 # 文档名称
    page_number: int                   # 页码
    content_type: str                  # 内容类型
    content_preview: str               # 内容预览
    relevance_score: float             # 相关性分数
    confidence_level: str              # 置信度级别
    source_type: str                   # 来源类型
    created_timestamp: int             # 创建时间戳


@dataclass
class AttributionResult:
    """溯源结果"""
    answer_id: str                     # 答案ID
    sources: List[SourceAttribution]   # 来源列表
    overall_confidence: float          # 整体置信度
    attribution_summary: str           # 溯源摘要
    processing_time: float             # 处理时间


class AttributionService:
    """溯源服务 - RAG系统的答案来源追踪模块"""
    
    def __init__(self, metadata_reader):
        """
        初始化溯源服务
        
        :param metadata_reader: RAG元数据读取器实例
        """
        self.metadata_reader = metadata_reader
        logger.info("溯源服务初始化完成")
    
    def get_source_attribution(self, answer_id: str, sources_used: List[str], 
                              attribution_mode: str = 'detailed') -> AttributionResult:
        """
        获取答案来源溯源信息
        
        :param answer_id: 答案ID
        :param sources_used: 使用的来源列表（chunk_id列表）
        :param attribution_mode: 溯源模式（detailed/summary/minimal）
        :return: 溯源结果
        """
        start_time = time.time()
        
        try:
            logger.info(f"开始获取答案溯源信息，答案ID: {answer_id}，来源数量: {len(sources_used)}")
            
            # 1. 收集来源信息
            source_attributions = self._collect_source_info(sources_used)
            
            # 2. 计算相关性分数
            self._calculate_relevance_scores(source_attributions)
            
            # 3. 评估置信度
            confidence_levels = self._assess_confidence_levels(source_attributions)
            
            # 4. 生成溯源摘要
            attribution_summary = self._generate_attribution_summary(
                source_attributions, attribution_mode
            )
            
            # 5. 计算整体置信度
            overall_confidence = self._calculate_overall_confidence(source_attributions)
            
            # 6. 构建溯源结果
            result = AttributionResult(
                answer_id=answer_id,
                sources=source_attributions,
                overall_confidence=overall_confidence,
                attribution_summary=attribution_summary,
                processing_time=time.time() - start_time
            )
            
            logger.info(f"溯源信息获取完成，整体置信度: {overall_confidence:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"获取溯源信息失败: {e}")
            # 返回默认溯源结果
            return self._create_default_attribution_result(answer_id, sources_used)
    
    def _collect_source_info(self, sources_used: List[str]) -> List[SourceAttribution]:
        """
        收集来源信息
        
        :param sources_used: 使用的来源列表
        :return: 来源溯源信息列表
        """
        source_attributions = []
        
        for chunk_id in sources_used:
            try:
                # 读取V3系统元数据
                metadata = self.metadata_reader.read_metadata(chunk_id)
                
                if metadata:
                    # 创建来源溯源信息
                    attribution = SourceAttribution(
                        chunk_id=chunk_id,
                        document_name=metadata.get('document_name', 'Unknown'),
                        page_number=metadata.get('page_number', 0),
                        content_type=metadata.get('chunk_type', 'unknown'),
                        content_preview=self._generate_content_preview(metadata),
                        relevance_score=0.0,  # 稍后计算
                        confidence_level='medium',  # 稍后评估
                        source_type=metadata.get('source_type', 'unknown'),
                        created_timestamp=metadata.get('created_timestamp', 0)
                    )
                    source_attributions.append(attribution)
                else:
                    logger.warning(f"未找到来源元数据: {chunk_id}")
                    
            except Exception as e:
                logger.error(f"收集来源信息失败: {chunk_id}, 错误: {e}")
                continue
        
        return source_attributions
    
    def _generate_content_preview(self, metadata: Dict[str, Any]) -> str:
        """
        生成内容预览
        
        :param metadata: 元数据
        :return: 内容预览
        """
        try:
            content = metadata.get('content', '')
            if not content:
                return "无内容预览"
            
            # 截取前200字符作为预览
            preview = content[:200]
            if len(content) > 200:
                preview += "..."
            
            return preview
            
        except Exception as e:
            logger.error(f"生成内容预览失败: {e}")
            return "内容预览生成失败"
    
    def _calculate_relevance_scores(self, source_attributions: List[SourceAttribution]):
        """
        计算相关性分数
        
        :param source_attributions: 来源溯源信息列表
        """
        try:
            for attribution in source_attributions:
                # 基于内容类型和来源类型计算基础分数
                base_score = self._calculate_base_relevance_score(attribution)
                
                # 基于时间的新鲜度分数
                freshness_score = self._calculate_freshness_score(attribution)
                
                # 综合相关性分数
                attribution.relevance_score = (base_score * 0.7) + (freshness_score * 0.3)
                
        except Exception as e:
            logger.error(f"计算相关性分数失败: {e}")
    
    def _calculate_base_relevance_score(self, attribution: SourceAttribution) -> float:
        """
        计算基础相关性分数
        
        :param attribution: 来源溯源信息
        :return: 基础相关性分数
        """
        try:
            base_score = 0.5  # 基础分数
            
            # 基于内容类型的分数调整
            content_type_scores = {
                'text': 1.0,
                'image': 0.8,
                'table': 0.9
            }
            content_type = attribution.content_type.lower()
            if content_type in content_type_scores:
                base_score *= content_type_scores[content_type]
            
            # 基于来源类型的分数调整
            source_type_scores = {
                'pdf': 1.0,
                'image': 0.8,
                'table': 0.9,
                'unknown': 0.7
            }
            source_type = attribution.source_type.lower()
            if source_type in source_type_scores:
                base_score *= source_type_scores[source_type]
            
            return min(base_score, 1.0)
            
        except Exception as e:
            logger.error(f"计算基础相关性分数失败: {e}")
            return 0.5
    
    def _calculate_freshness_score(self, attribution: SourceAttribution) -> float:
        """
        计算新鲜度分数
        
        :param attribution: 来源溯源信息
        :return: 新鲜度分数
        """
        try:
            if attribution.created_timestamp == 0:
                return 0.5  # 默认分数
            
            # 计算时间差（天）
            current_time = int(time.time())
            time_diff_days = (current_time - attribution.created_timestamp) / (24 * 3600)
            
            # 新鲜度衰减函数（30天内保持高分，之后逐渐降低）
            if time_diff_days <= 30:
                freshness_score = 1.0
            elif time_diff_days <= 90:
                freshness_score = 0.8
            elif time_diff_days <= 180:
                freshness_score = 0.6
            else:
                freshness_score = 0.4
            
            return freshness_score
            
        except Exception as e:
            logger.error(f"计算新鲜度分数失败: {e}")
            return 0.5
    
    def _assess_confidence_levels(self, source_attributions: List[SourceAttribution]):
        """
        评估置信度级别
        
        :param source_attributions: 来源溯源信息列表
        """
        try:
            for attribution in source_attributions:
                # 基于相关性分数评估置信度
                relevance_score = attribution.relevance_score
                
                if relevance_score >= 0.8:
                    confidence_level = 'high'
                elif relevance_score >= 0.6:
                    confidence_level = 'medium'
                else:
                    confidence_level = 'low'
                
                attribution.confidence_level = confidence_level
                
        except Exception as e:
            logger.error(f"评估置信度级别失败: {e}")
    
    def _generate_attribution_summary(self, source_attributions: List[SourceAttribution], 
                                    attribution_mode: str) -> str:
        """
        生成溯源摘要
        
        :param source_attributions: 来源溯源信息列表
        :param attribution_mode: 溯源模式
        :return: 溯源摘要
        """
        try:
            if not source_attributions:
                return "无来源信息"
            
            if attribution_mode == 'minimal':
                return self._generate_minimal_summary(source_attributions)
            elif attribution_mode == 'summary':
                return self._generate_summary_summary(source_attributions)
            else:  # detailed
                return self._generate_detailed_summary(source_attributions)
                
        except Exception as e:
            logger.error(f"生成溯源摘要失败: {e}")
            return "溯源摘要生成失败"
    
    def _generate_minimal_summary(self, source_attributions: List[SourceAttribution]) -> str:
        """生成最小溯源摘要"""
        try:
            total_sources = len(source_attributions)
            high_confidence = sum(1 for s in source_attributions if s.confidence_level == 'high')
            
            summary = f"基于 {total_sources} 个来源生成，其中 {high_confidence} 个高置信度来源。"
            return summary
            
        except Exception as e:
            logger.error(f"生成最小溯源摘要失败: {e}")
            return "溯源摘要生成失败"
    
    def _generate_summary_summary(self, source_attributions: List[SourceAttribution]) -> str:
        """生成摘要溯源摘要"""
        try:
            total_sources = len(source_attributions)
            high_confidence = sum(1 for s in source_attributions if s.confidence_level == 'high')
            medium_confidence = sum(1 for s in source_attributions if s.confidence_level == 'medium')
            
            # 按文档分组统计
            document_stats = {}
            for attribution in source_attributions:
                doc_name = attribution.document_name
                if doc_name not in document_stats:
                    document_stats[doc_name] = 0
                document_stats[doc_name] += 1
            
            summary_parts = [
                f"基于 {total_sources} 个来源生成，",
                f"其中 {high_confidence} 个高置信度来源，{medium_confidence} 个中等置信度来源。",
                f"主要来源文档：{', '.join(list(document_stats.keys())[:3])}"
            ]
            
            return ''.join(summary_parts)
            
        except Exception as e:
            logger.error(f"生成摘要溯源摘要失败: {e}")
            return "溯源摘要生成失败"
    
    def _generate_detailed_summary(self, source_attributions: List[SourceAttribution]) -> str:
        """生成详细溯源摘要"""
        try:
            total_sources = len(source_attributions)
            high_confidence = sum(1 for s in source_attributions if s.confidence_level == 'high')
            medium_confidence = sum(1 for s in source_attributions if s.confidence_level == 'medium')
            low_confidence = sum(1 for s in source_attributions if s.confidence_level == 'low')
            
            # 按文档分组统计
            document_stats = {}
            for attribution in source_attributions:
                doc_name = attribution.document_name
                if doc_name not in document_stats:
                    document_stats[doc_name] = {'count': 0, 'avg_score': 0.0}
                document_stats[doc_name]['count'] += 1
                document_stats[doc_name]['avg_score'] += attribution.relevance_score
            
            # 计算平均分数
            for doc_name in document_stats:
                count = document_stats[doc_name]['count']
                if count > 0:
                    document_stats[doc_name]['avg_score'] /= count
            
            # 按平均分数排序
            sorted_docs = sorted(document_stats.items(), 
                               key=lambda x: x[1]['avg_score'], reverse=True)
            
            summary_parts = [
                f"基于 {total_sources} 个来源生成，",
                f"置信度分布：{high_confidence} 个高置信度，{medium_confidence} 个中等置信度，{low_confidence} 个低置信度。\n\n",
                "主要来源文档：\n"
            ]
            
            # 添加前5个主要文档
            for i, (doc_name, stats) in enumerate(sorted_docs[:5]):
                summary_parts.append(
                    f"{i+1}. {doc_name} ({stats['count']} 个片段，平均相关性: {stats['avg_score']:.2f})\n"
                )
            
            return ''.join(summary_parts)
            
        except Exception as e:
            logger.error(f"生成详细溯源摘要失败: {e}")
            return "溯源摘要生成失败"
    
    def _calculate_overall_confidence(self, source_attributions: List[SourceAttribution]) -> float:
        """
        计算整体置信度
        
        :param source_attributions: 来源溯源信息列表
        :return: 整体置信度分数
        """
        try:
            if not source_attributions:
                return 0.0
            
            # 基于相关性分数和置信度级别计算整体置信度
            total_score = 0.0
            total_weight = 0.0
            
            for attribution in source_attributions:
                # 置信度级别权重
                confidence_weights = {
                    'high': 1.0,
                    'medium': 0.7,
                    'low': 0.4
                }
                
                weight = confidence_weights.get(attribution.confidence_level, 0.5)
                score = attribution.relevance_score * weight
                
                total_score += score
                total_weight += weight
            
            if total_weight > 0:
                overall_confidence = total_score / total_weight
                return min(overall_confidence, 1.0)
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"计算整体置信度失败: {e}")
            return 0.0
    
    def _create_default_attribution_result(self, answer_id: str, sources_used: List[str]) -> AttributionResult:
        """
        创建默认溯源结果（当溯源失败时）
        
        :param answer_id: 答案ID
        :param sources_used: 使用的来源列表
        :return: 默认溯源结果
        """
        try:
            # 创建默认来源溯源信息
            default_sources = []
            for chunk_id in sources_used:
                default_source = SourceAttribution(
                    chunk_id=chunk_id,
                    document_name='Unknown',
                    page_number=0,
                    content_type='unknown',
                    content_preview='内容预览不可用',
                    relevance_score=0.5,
                    confidence_level='medium',
                    source_type='unknown',
                    created_timestamp=0
                )
                default_sources.append(default_source)
            
            return AttributionResult(
                answer_id=answer_id,
                sources=default_sources,
                overall_confidence=0.5,
                attribution_summary=f"基于 {len(sources_used)} 个来源生成，溯源信息获取失败。",
                processing_time=0.0
            )
            
        except Exception as e:
            logger.error(f"创建默认溯源结果失败: {e}")
            # 返回最基本的溯源结果
            return AttributionResult(
                answer_id=answer_id,
                sources=[],
                overall_confidence=0.0,
                attribution_summary="溯源信息不可用",
                processing_time=0.0
            )
    
    def format_attribution_for_display(self, attribution_result: AttributionResult, 
                                     format_type: str = 'html') -> str:
        """
        格式化溯源信息用于显示
        
        :param attribution_result: 溯源结果
        :param format_type: 格式类型（html/markdown/text）
        :return: 格式化后的溯源信息
        """
        try:
            if format_type == 'html':
                return self._format_html(attribution_result)
            elif format_type == 'markdown':
                return self._format_markdown(attribution_result)
            else:  # text
                return self._format_text(attribution_result)
                
        except Exception as e:
            logger.error(f"格式化溯源信息失败: {e}")
            return "溯源信息格式化失败"
    
    def _format_html(self, attribution_result: AttributionResult) -> str:
        """格式化为HTML"""
        try:
            html_parts = [
                '<div class="attribution-info">',
                f'<h3>答案溯源信息</h3>',
                f'<p><strong>整体置信度:</strong> {attribution_result.overall_confidence:.2f}</p>',
                f'<p><strong>来源数量:</strong> {len(attribution_result.sources)}</p>',
                '<hr>',
                '<h4>溯源摘要</h4>',
                f'<p>{attribution_result.attribution_summary}</p>',
                '<hr>',
                '<h4>详细来源</h4>',
                '<div class="sources-list">'
            ]
            
            for i, source in enumerate(attribution_result.sources):
                html_parts.extend([
                    f'<div class="source-item">',
                    f'<h5>来源 {i+1}</h5>',
                    f'<p><strong>文档:</strong> {source.document_name}</p>',
                    f'<p><strong>页码:</strong> {source.page_number}</p>',
                    f'<p><strong>类型:</strong> {source.content_type}</p>',
                    f'<p><strong>相关性:</strong> {source.relevance_score:.2f}</p>',
                    f'<p><strong>置信度:</strong> {source.confidence_level}</p>',
                    f'<p><strong>预览:</strong> {source.content_preview}</p>',
                    '</div>'
                ])
            
            html_parts.extend([
                '</div>',
                '</div>'
            ])
            
            return ''.join(html_parts)
            
        except Exception as e:
            logger.error(f"格式化为HTML失败: {e}")
            return f"<p>溯源信息格式化失败: {e}</p>"
    
    def _format_markdown(self, attribution_result: AttributionResult) -> str:
        """格式化为Markdown"""
        try:
            md_parts = [
                '# 答案溯源信息\n\n',
                f'**整体置信度:** {attribution_result.overall_confidence:.2f}\n\n',
                f'**来源数量:** {len(attribution_result.sources)}\n\n',
                '---\n\n',
                '## 溯源摘要\n\n',
                f'{attribution_result.attribution_summary}\n\n',
                '---\n\n',
                '## 详细来源\n\n'
            ]
            
            for i, source in enumerate(attribution_result.sources):
                md_parts.extend([
                    f'### 来源 {i+1}\n\n',
                    f'- **文档:** {source.document_name}\n',
                    f'- **页码:** {source.page_number}\n',
                    f'- **类型:** {source.content_type}\n',
                    f'- **相关性:** {source.relevance_score:.2f}\n',
                    f'- **置信度:** {source.confidence_level}\n',
                    f'- **预览:** {source.content_preview}\n\n'
                ])
            
            return ''.join(md_parts)
            
        except Exception as e:
            logger.error(f"格式化为Markdown失败: {e}")
            return f"溯源信息格式化失败: {e}"
    
    def _format_text(self, attribution_result: AttributionResult) -> str:
        """格式化为纯文本"""
        try:
            text_parts = [
                '答案溯源信息\n',
                '=' * 20 + '\n',
                f'整体置信度: {attribution_result.overall_confidence:.2f}\n',
                f'来源数量: {len(attribution_result.sources)}\n',
                '-' * 20 + '\n',
                '溯源摘要:\n',
                f'{attribution_result.attribution_summary}\n',
                '-' * 20 + '\n',
                '详细来源:\n\n'
            ]
            
            for i, source in enumerate(attribution_result.sources):
                text_parts.extend([
                    f'来源 {i+1}:\n',
                    f'  文档: {source.document_name}\n',
                    f'  页码: {source.page_number}\n',
                    f'  类型: {source.content_type}\n',
                    f'  相关性: {source.relevance_score:.2f}\n',
                    f'  置信度: {source.confidence_level}\n',
                    f'  预览: {source.content_preview}\n\n'
                ])
            
            return ''.join(text_parts)
            
        except Exception as e:
            logger.error(f"格式化为纯文本失败: {e}")
            return f"溯源信息格式化失败: {e}"
    
    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态信息"""
        return {
            'status': 'ready',
            'service_type': 'RAG Attribution Service',
            'features': [
                'source_attribution',
                'relevance_scoring',
                'confidence_assessment',
                'attribution_summary',
                'multi_format_display'
            ],
            'supported_formats': ['html', 'markdown', 'text'],
            'attribution_modes': ['detailed', 'summary', 'minimal']
        }
