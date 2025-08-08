# RAG-250727-param - 智能问答系统

## 项目简介

这是一个基于RAG（Retrieval-Augmented Generation）技术的智能问答系统，支持多模态文档处理和智能问答功能。

## 主要功能

### 1. 文档处理
- 支持PDF、Markdown等多种文档格式
- 智能文档分块和向量化
- 图片内容提取和处理
- 表格数据识别和处理

### 2. 智能问答
- 基于向量检索的智能问答
- 多模态内容检索（文本、图片、表格）
- 上下文记忆和会话管理
- 智能重排序和过滤

### 3. 系统特性
- 参数化配置管理
- 模块化架构设计
- 支持增量文档处理
- 高性能向量检索

## 项目结构

```
RAG-250727-param/
├── api/                    # API接口模块
├── central/               # 核心数据存储
├── config/                # 配置管理
├── core/                  # 核心功能模块
├── document/              # 文档存储
├── document_processing/   # 文档处理模块
├── tools/                 # 工具脚本
└── web_app_test/         # Web应用测试
```

## 安装和配置

### 1. 环境要求
- Python 3.8+
- 相关依赖包（见requirements.txt）

### 2. 安装步骤
```bash
# 克隆项目
git clone <repository-url>
cd RAG-250727-param

# 安装依赖
pip install -r requirements.txt

# 配置环境
cp config.json.example config.json
# 编辑config.json配置文件
```

### 3. 配置说明
- 在`config.json`中配置API密钥和模型参数
- 支持多种嵌入模型和LLM模型配置
- 可自定义向量数据库和检索参数

## 使用方法

### 1. 文档处理
```python
from document_processing.pipeline import DocumentProcessor

# 初始化文档处理器
processor = DocumentProcessor()

# 处理文档
processor.process_documents("path/to/documents")
```

### 2. 智能问答
```python
from core.enhanced_qa_system import EnhancedQASystem

# 初始化问答系统
qa_system = EnhancedQASystem()

# 提问
response = qa_system.ask("您的问题")
print(response)
```

### 3. API接口
```bash
# 启动API服务
python api/app.py

# 访问Web界面
http://localhost:5000
```

## 版本管理

### 当前版本：V1.0.0
- 基础RAG功能实现
- 多模态文档支持
- 参数化配置系统
- 智能问答引擎

### 版本历史
- V1.0.0: 初始版本，包含核心RAG功能
- 后续版本将在此记录

## 开发指南

### 代码规范
- 使用中文注释
- 遵循PEP 8代码规范
- 函数必须包含文档字符串

### 文件命名规范
- 新文件以版本号开头（如：V100_）
- 使用下划线连接多个英文单词
- 文件名应体现功能特点

### 提交规范
- 使用中文提交信息
- 提交前进行代码检查
- 重要功能需要测试验证

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 贡献指南

欢迎提交Issue和Pull Request来改进项目。

## 联系方式

如有问题，请通过以下方式联系：
- 提交Issue
- 发送邮件

---

**注意**：本项目仍在积极开发中，功能可能会有变化。
