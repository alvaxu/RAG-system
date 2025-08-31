# V3 RAG系统

基于V3向量数据库的智能问答系统

## 项目简介

V3 RAG系统是一个基于V3向量数据库构建的智能问答系统，采用前后端分离架构，提供多模态内容的智能检索和问答服务。

## 系统架构

### 核心模块

- **查询处理器** (`core/query_processor.py`): 系统核心控制器，负责查询流程编排
- **召回引擎** (`core/retrieval.py`): 实现多模态内容的召回检索
- **重排序服务** (`core/reranking.py`): 使用DashScope reranking API进行结果重排序
- **LLM调用器** (`core/llm_caller.py`): 集成DashScope LLM服务
- **溯源服务** (`core/attribution.py`): 实现智能溯源功能
- **展示选择器** (`core/display.py`): 智能展示模式选择

### 技术栈

- **后端框架**: FastAPI
- **向量数据库**: FAISS + LangChain
- **LLM服务**: DashScope Qwen
- **重排序**: DashScope Reranking API
- **前端**: Vue.js 3.x (待开发)

## 快速开始

### 环境要求

- Python 3.8+
- 足够的磁盘空间用于向量数据库

### 安装依赖

```bash
cd rag_system
pip install -r requirements.txt
```

### 环境变量配置

```bash
# DashScope API密钥
export DASHSCOPE_API_KEY="your_api_key_here"

# MinerU API密钥（如果需要）
export MINERU_API_KEY="your_mineru_api_key_here"
```

### 启动服务

```bash
python main.py
```

服务将在 `http://localhost:8000` 启动

### API文档

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 主要功能

### 1. 智能查询处理

- 支持多种查询类型：文本、图片、表格、智能、混合
- 自动查询类型识别
- 智能流程编排

### 2. 多模态召回

- 文本召回（3层策略）
- 图片召回（4层策略）
- 表格召回（4层策略）
- 混合召回策略

### 3. 智能重排序

- 基于DashScope reranking API
- 内容类型特化处理
- 批量优化

### 4. LLM问答

- 集成DashScope Qwen模型
- 智能提示词构建
- 上下文优化

### 5. 智能溯源

- 支持正向和反向溯源
- 基于答案内容的智能匹配
- 可配置溯源模式

### 6. 展示模式选择

- 智能展示模式推荐
- 基于内容和查询类型的动态选择
- 多种布局配置

## 开发指南

### 目录结构

```
rag_system/
├── core/           # 核心业务逻辑
├── api/            # API接口层
├── utils/          # 工具函数
├── main.py         # 主程序入口
├── requirements.txt # 依赖包
└── README.md       # 项目说明
```

### 代码规范

- 遵循PEP 8代码风格
- 使用类型注解
- 完善的文档字符串
- 统一的命名规范

### 测试

```bash
# 运行测试
pytest

# 运行特定测试
pytest tests/test_query_processor.py
```

## 配置说明

系统配置通过环境变量和配置文件管理，主要配置项包括：

- LLM模型参数
- 重排序配置
- 召回策略参数
- 性能调优参数

## 部署说明

### 开发环境

- 使用 `python main.py` 启动
- 支持热重载
- 详细的调试日志

### 生产环境

- 使用 `uvicorn` 启动
- 配置反向代理（Nginx）
- 日志轮转和监控

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交代码
4. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件
- 项目讨论区

## 更新日志

### v3.0.0 (2025-08-31)

- 初始版本发布
- 核心功能模块完成
- API接口基本实现
- 基础架构搭建完成
