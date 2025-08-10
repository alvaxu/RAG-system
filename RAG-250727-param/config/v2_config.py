'''
程序说明：
## 1. V2.0.0 配置管理中心
## 2. 统一的引擎配置管理
## 3. 功能开关和参数配置
## 4. 向后兼容现有配置
'''

import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


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


@dataclass
class TableEngineConfigV2(EngineConfigV2):
    """表格引擎V2.0配置"""
    name: str = "table_engine"
    max_results: int = 15
    table_similarity_threshold: float = 0.65
    header_weight: float = 0.4
    content_weight: float = 0.4
    structure_weight: float = 0.2
    enable_structure_search: bool = True
    enable_content_search: bool = True


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


@dataclass
class V2SystemConfig:
    """V2.0系统配置"""
    # 系统基本信息
    system_name: str = "RAG-System-V2.0.0"
    version: str = "2.0.0"
    debug_mode: bool = False
    
    # 引擎配置
    image_engine: ImageEngineConfigV2 = None
    text_engine: TextEngineConfigV2 = None
    table_engine: TableEngineConfigV2 = None
    hybrid_engine: HybridEngineConfigV2 = None
    
    # 功能开关
    enable_image_search: bool = True
    enable_text_search: bool = True
    enable_table_search: bool = True
    enable_hybrid_search: bool = True
    
    # 性能配置
    max_concurrent_queries: int = 5
    query_timeout: float = 60.0
    cache_size: int = 1000
    
    def __post_init__(self):
        """初始化默认引擎配置"""
        if self.image_engine is None:
            self.image_engine = ImageEngineConfigV2()
        if self.text_engine is None:
            self.text_engine = TextEngineConfigV2()
        if self.table_engine is None:
            self.table_engine = TableEngineConfigV2()
        if self.hybrid_engine is None:
            self.hybrid_engine = HybridEngineConfigV2()


class V2ConfigManager:
    """V2.0配置管理器"""
    
    def __init__(self, config_file: str = "config/v2_config.json"):
        """
        初始化V2.0配置管理器
        
        :param config_file: 配置文件路径
        """
        self.config_file = Path(config_file)
        self.config = self._load_config()
    
    def _load_config(self) -> V2SystemConfig:
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                return self._create_config_from_dict(config_data)
            except Exception as e:
                print(f"加载V2.0配置失败: {e}")
        
        # 返回默认配置
        return V2SystemConfig()
    
    def _create_config_from_dict(self, config_data: Dict[str, Any]) -> V2SystemConfig:
        """从字典创建配置对象"""
        # 创建引擎配置
        image_config = ImageEngineConfigV2(**config_data.get('image_engine', {}))
        text_config = TextEngineConfigV2(**config_data.get('text_engine', {}))
        table_config = TableEngineConfigV2(**config_data.get('table_engine', {}))
        hybrid_config = HybridEngineConfigV2(**config_data.get('hybrid_engine', {}))
        
        # 创建系统配置
        system_config = V2SystemConfig(
            system_name=config_data.get('system_name', 'RAG-System-V2.0.0'),
            version=config_data.get('version', '2.0.0'),
            debug_mode=config_data.get('debug_mode', False),
            image_engine=image_config,
            text_engine=text_config,
            table_engine=table_config,
            hybrid_engine=hybrid_config,
            enable_image_search=config_data.get('enable_image_search', True),
            enable_text_search=config_data.get('enable_text_search', True),
            enable_table_search=config_data.get('enable_table_search', True),
            enable_hybrid_search=config_data.get('enable_hybrid_search', True),
            max_concurrent_queries=config_data.get('max_concurrent_queries', 5),
            query_timeout=config_data.get('query_timeout', 60.0),
            cache_size=config_data.get('cache_size', 1000)
        )
        
        return system_config
    
    def save_config(self):
        """保存配置到文件"""
        try:
            # 确保目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 转换配置为字典
            config_dict = {
                'system_name': self.config.system_name,
                'version': self.config.version,
                'debug_mode': self.config.debug_mode,
                'image_engine': asdict(self.config.image_engine),
                'text_engine': asdict(self.config.text_engine),
                'table_engine': asdict(self.config.table_engine),
                'hybrid_engine': asdict(self.config.hybrid_engine),
                'enable_image_search': self.config.enable_image_search,
                'enable_text_search': self.config.enable_text_search,
                'enable_table_search': self.config.enable_table_search,
                'enable_hybrid_search': self.config.enable_hybrid_search,
                'max_concurrent_queries': self.config.max_concurrent_queries,
                'query_timeout': self.config.query_timeout,
                'cache_size': self.config.cache_size
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            print(f"V2.0配置已保存到: {self.config_file}")
            
        except Exception as e:
            print(f"保存V2.0配置失败: {e}")
    
    def get_engine_config(self, engine_type: str) -> Optional[EngineConfigV2]:
        """获取指定引擎的配置"""
        engine_map = {
            'image': self.config.image_engine,
            'text': self.config.text_engine,
            'table': self.config.table_engine,
            'hybrid': self.config.hybrid_engine
        }
        return engine_map.get(engine_type)
    
    def is_engine_enabled(self, engine_type: str) -> bool:
        """检查指定引擎是否启用"""
        if engine_type == 'image':
            return self.config.enable_image_search and self.config.image_engine.enabled
        elif engine_type == 'text':
            return self.config.enable_text_search and self.config.text_engine.enabled
        elif engine_type == 'table':
            return self.config.enable_table_search and self.config.table_engine.enabled
        elif engine_type == 'hybrid':
            return self.config.enable_hybrid_search and self.config.hybrid_engine.enabled
        return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态信息"""
        return {
            'system_name': self.config.system_name,
            'version': self.config.version,
            'debug_mode': self.config.debug_mode,
            'engines': {
                'image': {
                    'enabled': self.is_engine_enabled('image'),
                    'config': asdict(self.config.image_engine)
                },
                'text': {
                    'enabled': self.is_engine_enabled('text'),
                    'config': asdict(self.config.text_engine)
                },
                'table': {
                    'enabled': self.is_engine_enabled('table'),
                    'config': asdict(self.config.table_engine)
                },
                'hybrid': {
                    'enabled': self.is_engine_enabled('hybrid'),
                    'config': asdict(self.config.hybrid_engine)
                }
            },
            'features': {
                'enable_image_search': self.config.enable_image_search,
                'enable_text_search': self.config.enable_text_search,
                'enable_table_search': self.config.enable_table_search,
                'enable_hybrid_search': self.config.enable_hybrid_search
            },
            'performance': {
                'max_concurrent_queries': self.config.max_concurrent_queries,
                'query_timeout': self.config.query_timeout,
                'cache_size': self.config.cache_size
            }
        }


# 创建默认配置实例
def create_default_v2_config() -> V2SystemConfig:
    """创建默认V2.0配置"""
    return V2SystemConfig()


def load_v2_config(config_file: str = "config/v2_config.json") -> V2ConfigManager:
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
