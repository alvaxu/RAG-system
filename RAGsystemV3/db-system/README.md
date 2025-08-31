# V3版本向量数据库构建系统

## 项目简介

V3版本是一个全新的向量数据库构建系统，基于模块化架构设计，支持文本、图像、表格等多种内容类型的智能处理和向量化。系统采用配置驱动的方式，支持Windows环境变量管理，具备完善的失败处理和重试机制。

## 目录结构

```
v3/
├── main.py                          # 主程序入口
├── README.md                        # 本文件
├── config/                          # 配置管理模块
│   ├── __init__.py
│   ├── config_manager.py            # 配置管理器主类
│   ├── config_validator.py          # 配置验证器
│   ├── config_loader.py             # 配置加载器
│   ├── environment_manager.py       # 环境变量管理器（Windows兼容）
│   ├── path_manager.py              # 路径管理器
│   ├── failure_handler.py           # 失败处理管理器
│   ├── v3_config.json              # V3配置文件
│   └── v3_config_schema.json       # 配置模式文件
├── core/                            # 核心模块
│   ├── __init__.py
│   ├── v3_main_processor.py         # 主控制器
│   ├── content_processor.py          # 内容处理器
│   ├── vectorization_manager.py      # 向量化管理
│   └── metadata_manager.py           # 元数据管理
├── processors/                      # 内容处理器模块
│   ├── __init__.py
│   ├── text_processor.py             # 文本处理器
│   ├── image_processor.py            # 图像处理器
│   └── table_processor.py            # 表格处理器
├── vectorization/                   # 向量化模块
│   ├── __init__.py
│   ├── text_vectorizer.py            # 文本向量化
│   ├── image_vectorizer.py           # 图像向量化（双重embedding）
│   └── table_vectorizer.py           # 表格向量化
├── metadata/                        # 元数据管理模块
│   ├── __init__.py
│   ├── metadata_schema.py            # 元数据模式
│   ├── metadata_manager.py           # 元数据管理器
│   └── metadata_validator.py         # 元数据验证器
└── utils/                           # 工具模块
    ├── __init__.py
    ├── document_type_detector.py     # 文档类型检测
    ├── vector_db_validator.py        # 向量数据库验证
    └── mineru_batch_processor.py     # minerU批量处理
```

## 模块说明
