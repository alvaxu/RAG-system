"""
溯源模块

实现智能溯源功能，支持正向和反向溯源：
- 正向溯源（基于输入文档）
- 反向溯源（基于LLM答案）
- 溯源模式切换
- 溯源信息格式化
"""

from .source_service import AttributionService

__all__ = [
    "AttributionService"
]
