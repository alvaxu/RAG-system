"""
提示词管理器模块

RAG系统的提示词管理核心组件，负责：
1. 提示词模板管理
2. 动态提示词生成
3. 提示词优化和版本控制
4. 多语言和多场景支持
"""

import logging
import json
import time
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class PromptTemplate:
    """提示词模板数据类"""
    name: str
    template: str
    description: str
    category: str
    version: str
    parameters: List[str]
    examples: List[Dict[str, str]]
    created_at: float
    updated_at: float
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

class PromptManager:
    """提示词管理器 - 核心提示词管理组件"""
    
    def __init__(self, config_integration):
        """
        初始化提示词管理器
        
        :param config_integration: 配置集成管理器实例
        """
        self.config = config_integration
        self.templates: Dict[str, PromptTemplate] = {}
        self.template_cache: Dict[str, str] = {}
        self.usage_stats: Dict[str, Dict[str, Any]] = {}
        
        # 加载默认提示词模板
        self._load_default_templates()
        
        logger.info("提示词管理器初始化完成")
    
    def _load_default_templates(self):
        """加载默认提示词模板"""
        default_templates = {
            'rag_qa': PromptTemplate(
                name='rag_qa',
                template="""你是一个专业的AI助手，请基于提供的上下文信息回答问题。

基于以下上下文信息回答问题：

上下文：
{context}

问题：
{query}

请提供准确、详细的答案：""",
                description='RAG问答标准提示词模板',
                category='qa',
                version='1.0.0',
                parameters=['context', 'query'],
                examples=[
                    {
                        'context': '人工智能是计算机科学的一个分支...',
                        'query': '什么是人工智能？',
                        'output': '基于上下文，人工智能是...'
                    }
                ],
                created_at=time.time(),
                updated_at=time.time()
            ),
            
            'rag_analysis': PromptTemplate(
                name='rag_analysis',
                template="""你是一个专业的分析师，请基于提供的上下文信息进行深入分析。

基于以下上下文信息进行分析：

上下文：
{context}

分析要求：
{query}

请提供详细的分析报告：""",
                description='RAG分析提示词模板',
                category='analysis',
                version='1.0.0',
                parameters=['context', 'query'],
                examples=[
                    {
                        'context': '机器学习算法的发展历程...',
                        'query': '分析机器学习的发展趋势',
                        'output': '基于上下文分析，机器学习的发展趋势包括...'
                    }
                ],
                created_at=time.time(),
                updated_at=time.time()
            ),
            
            'rag_summary': PromptTemplate(
                name='rag_summary',
                template="""你是一个专业的总结专家，请基于提供的上下文信息生成摘要。

基于以下上下文信息生成摘要：

上下文：
{context}

摘要要求：
{query}

请提供简洁准确的摘要：""",
                description='RAG摘要提示词模板',
                category='summary',
                version='1.0.0',
                parameters=['context', 'query'],
                examples=[
                    {
                        'context': '深度学习在图像识别领域的应用...',
                        'query': '总结主要应用场景',
                        'output': '基于上下文，深度学习在图像识别领域的主要应用场景包括...'
                    }
                ],
                created_at=time.time(),
                updated_at=time.time()
            )
        }
        
        self.templates.update(default_templates)
        logger.info(f"加载了 {len(default_templates)} 个默认提示词模板")
    
    def get_template(self, template_name: str) -> Optional[PromptTemplate]:
        """
        获取提示词模板
        
        :param template_name: 模板名称
        :return: 提示词模板对象
        """
        return self.templates.get(template_name)
    
    def generate_prompt(self, template_name: str, parameters: Dict[str, Any]) -> str:
        """
        生成提示词
        
        :param template_name: 模板名称
        :param parameters: 参数字典
        :return: 生成的提示词
        """
        try:
            template = self.get_template(template_name)
            if not template:
                raise ValueError(f"提示词模板 '{template_name}' 不存在")
            
            # 检查必需参数
            missing_params = [param for param in template.parameters if param not in parameters]
            if missing_params:
                raise ValueError(f"缺少必需参数: {missing_params}")
            
            # 生成提示词
            prompt = template.template
            for param, value in parameters.items():
                placeholder = f"{{{param}}}"
                if placeholder in prompt:
                    prompt = prompt.replace(placeholder, str(value))
            
            # 更新使用统计
            self._update_usage_stats(template_name, len(prompt))
            
            # 缓存生成的提示词
            cache_key = f"{template_name}_{hash(str(parameters))}"
            self.template_cache[cache_key] = prompt
            
            logger.info(f"生成提示词成功: {template_name}, 长度: {len(prompt)}")
            return prompt
            
        except Exception as e:
            logger.error(f"生成提示词失败: {e}")
            raise
    
    def add_template(self, template: PromptTemplate) -> bool:
        """
        添加新的提示词模板
        
        :param template: 提示词模板对象
        :return: 是否添加成功
        """
        try:
            if template.name in self.templates:
                logger.warning(f"提示词模板 '{template.name}' 已存在，将被覆盖")
            
            template.updated_at = time.time()
            self.templates[template.name] = template
            
            # 清除相关缓存
            self._clear_template_cache(template.name)
            
            logger.info(f"添加提示词模板成功: {template.name}")
            return True
            
        except Exception as e:
            logger.error(f"添加提示词模板失败: {e}")
            return False
    
    def update_template(self, template_name: str, **kwargs) -> bool:
        """
        更新提示词模板
        
        :param template_name: 模板名称
        :param kwargs: 更新参数
        :return: 是否更新成功
        """
        try:
            template = self.get_template(template_name)
            if not template:
                logger.error(f"提示词模板 '{template_name}' 不存在")
                return False
            
            # 更新字段
            for key, value in kwargs.items():
                if hasattr(template, key):
                    setattr(template, key, value)
            
            template.updated_at = time.time()
            
            # 清除相关缓存
            self._clear_template_cache(template_name)
            
            logger.info(f"更新提示词模板成功: {template_name}")
            return True
            
        except Exception as e:
            logger.error(f"更新提示词模板失败: {e}")
            return False
    
    def delete_template(self, template_name: str) -> bool:
        """
        删除提示词模板
        
        :param template_name: 模板名称
        :return: 是否删除成功
        """
        try:
            if template_name not in self.templates:
                logger.warning(f"提示词模板 '{template_name}' 不存在")
                return False
            
            del self.templates[template_name]
            
            # 清除相关缓存
            self._clear_template_cache(template_name)
            
            logger.info(f"删除提示词模板成功: {template_name}")
            return True
            
        except Exception as e:
            logger.error(f"删除提示词模板失败: {e}")
            return False
    
    def list_templates(self, category: Optional[str] = None) -> List[PromptTemplate]:
        """
        列出提示词模板
        
        :param category: 分类过滤（可选）
        :return: 模板列表
        """
        if category:
            return [template for template in self.templates.values() if template.category == category]
        return list(self.templates.values())
    
    def search_templates(self, keyword: str) -> List[PromptTemplate]:
        """
        搜索提示词模板
        
        :param keyword: 搜索关键词
        :return: 匹配的模板列表
        """
        keyword_lower = keyword.lower()
        results = []
        
        for template in self.templates.values():
            if (keyword_lower in template.name.lower() or 
                keyword_lower in template.description.lower() or
                keyword_lower in template.category.lower()):
                results.append(template)
        
        return results
    
    def export_templates(self, export_path: str) -> bool:
        """
        导出提示词模板
        
        :param export_path: 导出路径
        :return: 是否导出成功
        """
        try:
            export_data = {
                'export_time': time.time(),
                'templates': [template.to_dict() for template in self.templates.values()]
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"导出提示词模板成功: {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"导出提示词模板失败: {e}")
            return False
    
    def import_templates(self, import_path: str) -> bool:
        """
        导入提示词模板
        
        :param import_path: 导入路径
        :return: 是否导入成功
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            imported_count = 0
            for template_data in import_data.get('templates', []):
                template = PromptTemplate(**template_data)
                if self.add_template(template):
                    imported_count += 1
            
            logger.info(f"导入提示词模板成功: {imported_count} 个")
            return True
            
        except Exception as e:
            logger.error(f"导入提示词模板失败: {e}")
            return False
    
    def get_usage_stats(self, template_name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取使用统计
        
        :param template_name: 模板名称（可选）
        :return: 使用统计信息
        """
        if template_name:
            return self.usage_stats.get(template_name, {})
        
        return self.usage_stats
    
    def _update_usage_stats(self, template_name: str, prompt_length: int):
        """更新使用统计"""
        if template_name not in self.usage_stats:
            self.usage_stats[template_name] = {
                'usage_count': 0,
                'total_length': 0,
                'last_used': 0,
                'avg_length': 0
            }
        
        stats = self.usage_stats[template_name]
        stats['usage_count'] += 1
        stats['total_length'] += prompt_length
        stats['last_used'] = time.time()
        stats['avg_length'] = stats['total_length'] / stats['usage_count']
    
    def _clear_template_cache(self, template_name: str):
        """清除模板相关缓存"""
        cache_keys = [key for key in self.template_cache.keys() if key.startswith(template_name)]
        for key in cache_keys:
            del self.template_cache[key]
    
    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态信息"""
        return {
            'status': 'ready',
            'service_type': 'Prompt Manager',
            'template_count': len(self.templates),
            'cache_size': len(self.template_cache),
            'categories': list(set(template.category for template in self.templates.values())),
            'total_usage': sum(stats.get('usage_count', 0) for stats in self.usage_stats.values())
        }
