# RAG-System V2.0.0 智能问答系统

## 🚀 系统概述

RAG-System V2.0.0 是一个完全重构的智能问答系统，采用模块化架构设计，支持图片、文本、表格等多种内容类型的智能查询。

## 🏗️ 架构特点

### 1. **完全独立的V2.0架构**
- 与老版本完全分离，不影响现有系统
- 独立的配置管理和模块结构
- 可并行运行，便于对比测试

### 2. **模块化设计**
- `core/` - 核心查询引擎
- `api/` - API服务接口
- `web/` - Web用户界面
- `config/` - 配置管理
- `utils/` - 工具函数
- `tests/` - 测试代码
- `docs/` - 文档说明

### 3. **智能查询引擎**
- **ImageEngine**: 图片内容查询
- **TextEngine**: 文本内容查询  
- **TableEngine**: 表格数据查询
- **HybridEngine**: 混合查询融合

## 📁 目录结构

```
v2/
├── __init__.py              # V2.0包初始化
├── README.md                # 本文档
├── core/                    # 核心引擎
│   ├── __init__.py
│   ├── base_engine.py      # 基础引擎抽象类
│   ├── image_engine.py     # 图片查询引擎
│   ├── text_engine.py      # 文本查询引擎
│   ├── table_engine.py     # 表格查询引擎
│   └── hybrid_engine.py    # 混合查询引擎
├── config/                  # 配置管理
│   ├── __init__.py
│   ├── v2_config.py        # 配置类定义
│   └── v2_config.json      # 配置文件
├── api/                     # API服务
├── web/                     # Web界面
├── utils/                   # 工具函数
├── tests/                   # 测试代码
└── docs/                    # 详细文档
```

## 🔧 使用方法

### 1. **导入V2.0模块**
```python
from v2 import ImageEngine, TextEngine, TableEngine, HybridEngine
from v2.config import V2ConfigManager
```

### 2. **配置管理**
```python
config_manager = V2ConfigManager()
config = config_manager.load_config()
```

### 3. **使用查询引擎**
```python
# 图片查询
image_engine = ImageEngine(config.image_engine)
results = image_engine.process_query("查找包含图表的图片")

# 混合查询
hybrid_engine = HybridEngine(config.hybrid_engine)
results = hybrid_engine.process_query("分析文档中的图表和数据")
```

## 🚦 开发状态

- ✅ **已完成**: 核心引擎架构、配置管理
- 🔄 **进行中**: API服务开发、Web界面
- ⏳ **待开发**: 系统集成、性能优化

## 📋 下一步计划

1. **API服务开发** - 创建V2.0的RESTful API
2. **Web界面开发** - 构建现代化的用户界面
3. **系统集成测试** - 验证完整功能流程
4. **性能优化** - 提升查询响应速度

## 🔗 相关文档

- [开发规划文档](../prjdoc/V701_V200_QA系统开发详细规划.md)
- [技术架构说明](../prjdoc/V501_0_项目架构总览.md)
- [API接口文档](./docs/api.md)

## 📞 技术支持

如有问题或建议，请联系开发团队。
