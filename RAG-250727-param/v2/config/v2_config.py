'''
程序说明：
## 1. V2.0.0 配置管理中心
## 2. 统一的引擎配置管理
## 3. 功能开关和参数配置
## 4. 向后兼容现有配置
## 5. 新增优化引擎配置支持
'''

import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class EngineConfigV2:
    """V2.0引擎基础配置"""
    enabled: bool = True
    name: str = "base_engine"
    version: str = "2.0.0"
    debug: bool = False
    max_results: int = 10
    timeout: float = 30.0
    cache_enabled: bool = True
    cache_ttl: int = 300


@dataclass
class RerankingEngineConfigV2(EngineConfigV2):
    """重排序引擎V2.0配置"""
    name: str = "dashscope_reranking"
    model_name: str = "bge-reranker-v2-m3"
    top_k: int = 10
    similarity_threshold: float = 0.7
    weight_semantic: float = 0.8
    weight_keyword: float = 0.2
    enable_reranking: bool = True
    max_batch_size: int = 10


@dataclass
class LLMEngineConfigV2(EngineConfigV2):
    """LLM引擎V2.0配置"""
    name: str = "dashscope_llm"
    model_name: str = "qwen-turbo"
    temperature: float = 0.7
    max_tokens: int = 2000
    top_p: float = 0.8
    enable_stream: bool = False
    system_prompt: str = "你是一个专业的AI助手，能够基于提供的上下文信息生成准确、相关、完整的答案。"
    enable_llm: bool = True


@dataclass
class SmartFilterEngineConfigV2(EngineConfigV2):
    """智能过滤引擎V2.0配置"""
    name: str = "smart_filter"
    enable_filtering: bool = True
    similarity_threshold: float = 0.6
    keyword_weight: float = 0.3
    semantic_weight: float = 0.5
    content_quality_weight: float = 0.2
    min_content_length: int = 10
    max_content_length: int = 10000
    enable_keyword_extraction: bool = True
    enable_content_quality_check: bool = True
    enable_adaptive_threshold: bool = True


@dataclass
class SourceFilterEngineConfigV2(EngineConfigV2):
    """源过滤引擎V2.0配置"""
    name: str = "source_filter"
    enable_filtering: bool = True
    relevance_threshold: float = 0.6
    content_overlap_threshold: float = 0.3
    keyword_match_weight: float = 0.4
    semantic_similarity_weight: float = 0.4
    content_quality_weight: float = 0.2
    enable_dynamic_threshold: bool = True
    min_sources_to_keep: int = 1
    max_sources_to_keep: int = 10
    enable_source_ranking: bool = True


@dataclass
class ImageEngineConfigV2(EngineConfigV2):
    """图片引擎V2.0配置"""
    name: str = "image_engine"
    max_results: int = 20
    image_similarity_threshold: float = 0.6
    keyword_weight: float = 0.4
    caption_weight: float = 0.3
    description_weight: float = 0.3
    enable_fuzzy_match: bool = True
    enable_semantic_search: bool = True


@dataclass
class TextEngineConfigV2(EngineConfigV2):
    """文本引擎V2.0配置"""
    name: str = "text_engine"
    max_results: int = 10
    text_similarity_threshold: float = 0.7
    keyword_weight: float = 0.3
    semantic_weight: float = 0.4
    vector_weight: float = 0.3
    enable_semantic_search: bool = True
    enable_vector_search: bool = True
    
    # 新增：五层召回策略配置
    min_required_results: int = 20
    
    # 召回策略配置
    recall_strategy: Dict[str, Any] = None
    
    # 重排序配置
    reranking: Dict[str, Any] = None
    
    # 评分配置
    scoring: Dict[str, Any] = None
    
    def __post_init__(self):
        """初始化字典字段"""
        if self.recall_strategy is None:
            self.recall_strategy = {
                "layer1_vector_search": {
                    "enabled": True,
                    "top_k": 50,
                    "similarity_threshold": 0.3,
                    "description": "第一层：向量相似度搜索（主要策略）"
                },
                "layer2_semantic_keyword": {
                    "enabled": True,
                    "top_k": 40,
                    "match_threshold": 0.25,
                    "description": "第二层：语义关键词搜索（补充策略）"
                },
                "layer3_hybrid_search": {
                    "enabled": True,
                    "top_k": 35,
                    "vector_weight": 0.4,
                    "keyword_weight": 0.3,
                    "semantic_weight": 0.3,
                    "description": "第三层：混合搜索策略（融合策略）"
                },
                "layer4_smart_fuzzy": {
                    "enabled": True,
                    "top_k": 30,
                    "fuzzy_threshold": 0.2,
                    "description": "第四层：智能模糊匹配（容错策略）"
                },
                "layer5_expansion": {
                    "enabled": True,
                    "top_k": 25,
                    "activation_threshold": 20,
                    "description": "第五层：智能扩展召回（兜底策略）"
                }
            }
        
        if self.reranking is None:
            self.reranking = {
                "enable_type_specific_optimization": True,
                "type_specific_reranking": {
                    "text_analysis": {
                        "content_length_weight": 0.15,
                        "structure_weight": 0.10,
                        "vocabulary_weight": 0.10,
                        "professional_terms_weight": 0.05
                    },
                    "semantic_consistency": {
                        "word_overlap_weight": 0.6,
                        "word_order_weight": 0.4
                    },
                    "context_relevance": {
                        "word_frequency_weight": 0.4,
                        "context_coherence_weight": 0.3,
                        "domain_relevance_weight": 0.3
                    }
                }
            }
        
        if self.scoring is None:
            self.scoring = {
                "comprehensive_ranking": {
                    "base_score_weight": 0.4,
                    "content_relevance_weight": 0.3,
                    "document_quality_weight": 0.2,
                    "search_strategy_weight": 0.1
                },
                "strategy_weights": {
                    "vector_similarity": 1.0,
                    "hybrid_search": 0.9,
                    "semantic_similarity": 0.8,
                    "semantic_keyword": 0.7,
                    "smart_fuzzy": 0.6,
                    "expansion_synonym_expansion": 0.5,
                    "expansion_concept_expansion": 0.5,
                    "expansion_related_word": 0.5,
                    "expansion_domain_expansion": 0.4
                }
            }


@dataclass
class TableEngineConfigV2(EngineConfigV2):
    """表格引擎V2.0配置"""
    name: str = "table_engine"
    max_results: int = 15
    table_similarity_threshold: float = 0.65
    header_weight: float = 0.4
    content_weight: float = 0.4
    structure_weight: float = 0.2
    keyword_weight: float = 0.3  # 添加缺失的属性
    enable_structure_search: bool = True
    enable_content_search: bool = True


@dataclass
class IntelligentPostProcessingConfig:
    """智能后处理配置"""
    enable_image_filtering: bool = True
    enable_text_filtering: bool = True
    enable_table_filtering: bool = True
    max_images_to_keep: int = 2
    max_texts_to_keep: int = 2
    max_tables_to_keep: int = 1
    keyword_match_threshold: float = 0.6


@dataclass
class OptimizationPipelineConfig:
    """优化管道配置"""
    enable_reranking: bool = True
    enable_llm_generation: bool = True
    enable_smart_filtering: bool = True
    enable_source_filtering: bool = True
    enable_intelligent_post_processing: bool = True
    pipeline_order: list = None
    intelligent_post_processing: IntelligentPostProcessingConfig = None
    
    def __post_init__(self):
        if self.pipeline_order is None:
            self.pipeline_order = ["reranking", "smart_filtering", "llm_generation", "intelligent_post_processing", "source_filtering"]
        if self.intelligent_post_processing is None:
            self.intelligent_post_processing = IntelligentPostProcessingConfig()


@dataclass
class HybridEngineConfigV2(EngineConfigV2):
    """混合查询引擎V2.0配置"""
    name: str = "hybrid_engine"
    max_results: int = 25
    image_weight: float = 0.3
    text_weight: float = 0.4
    table_weight: float = 0.3
    enable_cross_search: bool = True
    enable_ranking: bool = True
    enable_optimization_pipeline: bool = True
    optimization_pipeline: OptimizationPipelineConfig = None
    enable_hybrid_search: bool = True # 添加缺失的属性
    enable_table_search: bool = True # 添加缺失的属性
    enable_image_search: bool = True  # 添加缺失的属性
    enable_text_search: bool = True   # 添加缺失的属性
    
    def __post_init__(self):
        if self.optimization_pipeline is None:
            self.optimization_pipeline = OptimizationPipelineConfig()


@dataclass
class V2SystemConfig:
    """V2.0系统配置"""
    # 系统基本信息
    system_name: str = "RAG-System-V2.0.0"
    version: str = "2.0.0"
    debug_mode: bool = False
    
    # 基础引擎配置
    image_engine: ImageEngineConfigV2 = None
    text_engine: TextEngineConfigV2 = None
    table_engine: TableEngineConfigV2 = None
    hybrid_engine: HybridEngineConfigV2 = None
    
    # 优化引擎配置
    reranking_engine: RerankingEngineConfigV2 = None
    llm_engine: LLMEngineConfigV2 = None
    smart_filter_engine: SmartFilterEngineConfigV2 = None
    source_filter_engine: SourceFilterEngineConfigV2 = None
    
    # 功能开关
    enable_image_search: bool = True
    enable_text_search: bool = True
    enable_table_search: bool = True
    enable_hybrid_search: bool = True
    
    # 性能配置
    query_timeout: float = 60.0
    cache_size: int = 1000
    
    def __post_init__(self):
        """初始化默认引擎配置"""
        # 基础引擎
        if self.image_engine is None:
            self.image_engine = ImageEngineConfigV2()
        if self.text_engine is None:
            self.text_engine = TextEngineConfigV2()
        if self.table_engine is None:
            self.table_engine = TableEngineConfigV2()
        if self.hybrid_engine is None:
            self.hybrid_engine = HybridEngineConfigV2()
        
        # 优化引擎
        if self.reranking_engine is None:
            self.reranking_engine = RerankingEngineConfigV2()
        if self.llm_engine is None:
            self.llm_engine = LLMEngineConfigV2()
        if self.smart_filter_engine is None:
            self.smart_filter_engine = SmartFilterEngineConfigV2()
        if self.source_filter_engine is None:
            self.source_filter_engine = SourceFilterEngineConfigV2()


class V2ConfigManager:
    """V2.0配置管理器"""
    
    def __init__(self, config_file: str = None):
        """
        初始化配置管理器
        
        :param config_file: 配置文件路径
        """
        if config_file is None:
            # 自动检测配置文件路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_file = os.path.join(current_dir, "v2_config.json")
        
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> V2SystemConfig:
        """
        加载配置文件
        
        :return: 系统配置对象
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                return self._create_config_from_dict(config_data)
            else:
                logger.warning(f"配置文件不存在: {self.config_file}，使用默认配置")
                return V2SystemConfig()
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}，使用默认配置")
            return V2SystemConfig()
    
    def _create_config_from_dict(self, config_data: Dict[str, Any]) -> V2SystemConfig:
        """
        从字典创建配置对象
        
        :param config_data: 配置字典
        :return: 系统配置对象
        """
        try:
            # 创建基础配置
            config = V2SystemConfig()
            
            # 更新系统基本信息
            for key in ['system_name', 'version', 'debug_mode', 'query_timeout', 'cache_size']:
                if key in config_data:
                    setattr(config, key, config_data[key])
            
            # 更新功能开关
            for key in ['enable_image_search', 'enable_text_search', 'enable_table_search', 'enable_hybrid_search']:
                if key in config_data:
                    setattr(config, key, config_data[key])
            
            # 更新引擎配置
            engine_configs = {
                'image_engine': ImageEngineConfigV2,
                'text_engine': TextEngineConfigV2,
                'table_engine': TableEngineConfigV2,
                'reranking_engine': RerankingEngineConfigV2,
                'llm_engine': LLMEngineConfigV2,
                'smart_filter_engine': SmartFilterEngineConfigV2,
                'source_filter_engine': SourceFilterEngineConfigV2
            }
            
            for engine_name, engine_class in engine_configs.items():
                if engine_name in config_data:
                    engine_data = config_data[engine_name]
                    # 确保配置数据是字典类型
                    if isinstance(engine_data, dict):
                        engine_config = engine_class(**engine_data)
                    else:
                        # 如果不是字典，尝试转换为字典或使用默认值
                        logger.warning(f"引擎 {engine_name} 配置数据类型异常: {type(engine_data)}，使用默认配置")
                        engine_config = engine_class()
                    setattr(config, engine_name, engine_config)
            
            # 特殊处理hybrid_engine，确保optimization_pipeline被正确转换
            if 'hybrid_engine' in config_data:
                hybrid_data = config_data['hybrid_engine'].copy()
                
                # 如果存在optimization_pipeline配置，转换为OptimizationPipelineConfig对象
                if 'optimization_pipeline' in hybrid_data:
                    pipeline_data = hybrid_data['optimization_pipeline']
                    if isinstance(pipeline_data, dict):
                        # 处理intelligent_post_processing配置
                        if 'intelligent_post_processing' in pipeline_data:
                            post_proc_data = pipeline_data['intelligent_post_processing']
                            if isinstance(post_proc_data, dict):
                                pipeline_data['intelligent_post_processing'] = IntelligentPostProcessingConfig(**post_proc_data)
                        
                        hybrid_data['optimization_pipeline'] = OptimizationPipelineConfig(**pipeline_data)
                
                hybrid_config = HybridEngineConfigV2(**hybrid_data)
                setattr(config, 'hybrid_engine', hybrid_config)
            
            return config
            
        except Exception as e:
            logger.error(f"创建配置对象失败: {str(e)}")
            return V2SystemConfig()
    
    def save_config(self):
        """保存配置到文件"""
        try:
            config_dict = asdict(self.config)
            
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"配置已保存到: {self.config_file}")
            
        except Exception as e:
            logger.error(f"保存配置失败: {str(e)}")
    
    def get_engine_config(self, engine_type: str) -> Optional[EngineConfigV2]:
        """
        获取指定引擎的配置
        
        :param engine_type: 引擎类型
        :return: 引擎配置对象
        """
        engine_attr = f"{engine_type}_engine"
        if hasattr(self.config, engine_attr):
            return getattr(self.config, engine_attr)
        return None
    
    def get_engine_config_for_initialization(self, engine_type: str) -> Optional[EngineConfigV2]:
        """
        获取指定引擎的配置，用于引擎初始化
        
        :param engine_type: 引擎类型
        :return: 引擎配置对象
        """
        engine_config = self.get_engine_config(engine_type)
        if engine_config:
            # 确保返回的是dataclass对象，而不是字典
            if isinstance(engine_config, dict):
                # 如果是字典，转换为对应的dataclass对象
                engine_configs = {
                    'smart_filter': SmartFilterEngineConfigV2,
                    'source_filter': SourceFilterEngineConfigV2,
                    'reranking': RerankingEngineConfigV2,
                    'llm': LLMEngineConfigV2
                }
                if engine_type in engine_configs:
                    return engine_configs[engine_type](**engine_config)
                else:
                    logger.warning(f"未知的引擎类型: {engine_type}")
                    return None
            else:
                return engine_config
        return None
    
    def is_engine_enabled(self, engine_type: str) -> bool:
        """
        检查指定引擎是否启用
        
        :param engine_type: 引擎类型
        :return: 是否启用
        """
        engine_config = self.get_engine_config(engine_type)
        if engine_config:
            return engine_config.enabled
        return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        获取系统状态信息
        
        :return: 状态信息字典
        """
        status = {
            "system_name": self.config.system_name,
            "version": self.config.version,
            "debug_mode": self.config.debug_mode,
            "engines": {}
        }
        
        # 收集所有引擎状态
        engine_types = [
            'image', 'text', 'table', 'hybrid',
            'reranking', 'llm', 'smart_filter', 'source_filter'
        ]
        
        for engine_type in engine_types:
            engine_config = self.get_engine_config(engine_type)
            if engine_config:
                status["engines"][engine_type] = {
                    "enabled": engine_config.enabled,
                    "name": engine_config.name,
                    "version": engine_config.version
                }
        
        return status
    
    def update_engine_config(self, engine_type: str, **kwargs) -> bool:
        """
        更新指定引擎的配置
        
        :param engine_type: 引擎类型
        :param kwargs: 要更新的配置参数
        :return: 是否更新成功
        """
        try:
            engine_config = self.get_engine_config(engine_type)
            if not engine_config:
                logger.warning(f"引擎配置不存在: {engine_type}")
                return False
            
            for key, value in kwargs.items():
                if hasattr(engine_config, key):
                    setattr(engine_config, key, value)
                    logger.info(f"引擎 {engine_type} 配置参数 {key} 更新为: {value}")
                else:
                    logger.warning(f"未知的配置参数: {key}")
            
            return True
            
        except Exception as e:
            logger.error(f"更新引擎配置失败: {str(e)}")
            return False


def create_default_v2_config() -> V2SystemConfig:
    """创建默认V2.0配置"""
    return V2SystemConfig()


def load_v2_config(config_file: str = "v2/config/v2_config.json") -> V2ConfigManager:
    """加载V2.0配置管理器"""
    return V2ConfigManager(config_file)


if __name__ == "__main__":
    # 测试配置管理
    config_manager = V2ConfigManager()
    print("V2.0配置加载成功!")
    print(f"系统名称: {config_manager.config.system_name}")
    print(f"版本: {config_manager.config.version}")
    print(f"图片引擎启用: {config_manager.is_engine_enabled('image')}")
    print(f"文本引擎启用: {config_manager.is_engine_enabled('text')}")
    print(f"表格引擎启用: {config_manager.is_engine_enabled('table')}")
    print(f"混合引擎启用: {config_manager.is_engine_enabled('hybrid')}")
    
    # 保存默认配置
    config_manager.save_config()
