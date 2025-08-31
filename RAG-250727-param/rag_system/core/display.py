"""
展示模式选择器模块

实现智能展示模式选择，根据查询类型和内容特征推荐最佳展示方式
"""

import logging
from typing import List, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class DisplayMode(Enum):
    """展示模式枚举"""
    TEXT_FOCUSED = "text_focused"
    IMAGE_FOCUSED = "image_focused"
    TABLE_FOCUSED = "table_focused"
    HYBRID_LAYOUT = "hybrid_layout"
    AUTO = "auto"


class DisplaySelector:
    """展示模式选择器 - 实现智能展示模式选择"""
    
    def __init__(self):
        self.default_mode = DisplayMode.AUTO
        logger.info("展示模式选择器初始化完成")
    
    def recommend_mode(self, query_text: str, query_type: str, retrieval_results: List[Dict]) -> Dict[str, Any]:
        """推荐展示模式"""
        try:
            logger.info(f"开始推荐展示模式，查询类型: {query_type}")
            
            # 1. 基于查询类型的模式选择
            type_based_mode = self._select_by_query_type(query_type)
            
            # 2. 基于内容特征的智能检测
            content_based_mode = self._detect_by_content(query_text, retrieval_results)
            
            # 3. 综合推荐
            recommended_mode = self._combine_recommendations(type_based_mode, content_based_mode)
            
            # 4. 生成展示配置
            display_config = self._generate_display_config(recommended_mode)
            
            logger.info(f"展示模式推荐完成: {recommended_mode.value}")
            return display_config
            
        except Exception as e:
            logger.error(f"展示模式推荐失败: {str(e)}")
            return self._get_default_config()
    
    def _select_by_query_type(self, query_type: str) -> DisplayMode:
        """基于查询类型选择展示模式"""
        if query_type == "text":
            return DisplayMode.TEXT_FOCUSED
        elif query_type == "image":
            return DisplayMode.IMAGE_FOCUSED
        elif query_type == "table":
            return DisplayMode.TABLE_FOCUSED
        elif query_type == "hybrid":
            return DisplayMode.HYBRID_LAYOUT
        else:
            return DisplayMode.AUTO
    
    def _detect_by_content(self, query_text: str, retrieval_results: List[Dict]) -> DisplayMode:
        """基于内容特征智能检测展示模式"""
        if not retrieval_results:
            return DisplayMode.AUTO
        
        # 统计不同类型的内容
        content_stats = self._analyze_content_distribution(retrieval_results)
        
        # 基于内容分布推荐模式
        if content_stats["image"] > 0.5:
            return DisplayMode.IMAGE_FOCUSED
        elif content_stats["table"] > 0.4:
            return DisplayMode.TABLE_FOCUSED
        elif content_stats["text"] > 0.6:
            return DisplayMode.TEXT_FOCUSED
        else:
            return DisplayMode.HYBRID_LAYOUT
    
    def _analyze_content_distribution(self, retrieval_results: List[Dict]) -> Dict[str, float]:
        """分析内容分布"""
        total_count = len(retrieval_results)
        if total_count == 0:
            return {"text": 0.0, "image": 0.0, "table": 0.0}
        
        content_counts = {"text": 0, "image": 0, "table": 0}
        
        for result in retrieval_results:
            chunk_type = result.get("metadata", {}).get("chunk_type", "text")
            if chunk_type in content_counts:
                content_counts[chunk_type] += 1
        
        # 计算比例
        distribution = {}
        for content_type, count in content_counts.items():
            distribution[content_type] = count / total_count
        
        return distribution
    
    def _combine_recommendations(self, type_mode: DisplayMode, content_mode: DisplayMode) -> DisplayMode:
        """综合推荐展示模式"""
        # 如果查询类型明确指定，优先使用类型模式
        if type_mode != DisplayMode.AUTO and type_mode != DisplayMode.HYBRID_LAYOUT:
            return type_mode
        
        # 如果内容检测明确，使用内容模式
        if content_mode != DisplayMode.AUTO:
            return content_mode
        
        # 默认使用混合布局
        return DisplayMode.HYBRID_LAYOUT
    
    def _generate_display_config(self, display_mode: DisplayMode) -> Dict[str, Any]:
        """生成展示配置"""
        config = {
            "selected_mode": display_mode.value,
            "reason": self._get_mode_reason(display_mode),
            "layout_config": self._get_layout_config(display_mode)
        }
        
        return config
    
    def _get_mode_reason(self, display_mode: DisplayMode) -> str:
        """获取模式选择原因"""
        reasons = {
            DisplayMode.TEXT_FOCUSED: "基于查询类型，推荐文本优先展示",
            DisplayMode.IMAGE_FOCUSED: "检测到图片相关内容较多，推荐图片优先展示",
            DisplayMode.TABLE_FOCUSED: "检测到表格数据较多，推荐表格优先展示",
            DisplayMode.HYBRID_LAYOUT: "内容类型多样，推荐混合布局展示",
            DisplayMode.AUTO: "智能检测推荐的最佳展示模式"
        }
        return reasons.get(display_mode, "默认展示模式")
    
    def _get_layout_config(self, display_mode: DisplayMode) -> Dict[str, Any]:
        """获取布局配置"""
        layouts = {
            DisplayMode.TEXT_FOCUSED: {
                "main_area": "text",
                "text_ratio": 0.7,
                "image_ratio": 0.2,
                "table_ratio": 0.1
            },
            DisplayMode.IMAGE_FOCUSED: {
                "main_area": "image",
                "text_ratio": 0.3,
                "image_ratio": 0.6,
                "table_ratio": 0.1
            },
            DisplayMode.TABLE_FOCUSED: {
                "main_area": "table",
                "text_ratio": 0.2,
                "image_ratio": 0.1,
                "table_ratio": 0.7
            },
            DisplayMode.HYBRID_LAYOUT: {
                "main_area": "hybrid",
                "text_ratio": 0.4,
                "image_ratio": 0.3,
                "table_ratio": 0.3
            }
        }
        return layouts.get(display_mode, layouts[DisplayMode.HYBRID_LAYOUT])
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "selected_mode": DisplayMode.AUTO.value,
            "reason": "使用默认展示模式",
            "layout_config": self._get_layout_config(DisplayMode.HYBRID_LAYOUT)
        }
