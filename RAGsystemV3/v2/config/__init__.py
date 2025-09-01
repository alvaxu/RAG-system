'''
程序说明：

## 1. V2.0.0 配置管理包初始化文件
## 2. 导出配置管理器和配置类
## 3. 与老版本配置系统完全分离
'''

from .v2_config import (
    V2ConfigManager,
    V2SystemConfig,
    EngineConfigV2,
    ImageEngineConfigV2,
    TextEngineConfigV2,
    TableEngineConfigV2,
    HybridEngineConfigV2
)

__all__ = [
    'V2ConfigManager',
    'V2SystemConfig',
    'EngineConfigV2',
    'ImageEngineConfigV2',
    'TextEngineConfigV2',
    'TableEngineConfigV2',
    'HybridEngineConfigV2'
]
