# RAG系统V3使用手册

## 📋 系统概述

RAG系统V3是一个智能检索增强生成系统，由两个核心模块组成：

1. **RAG查询系统**：提供智能问答、多模态检索、记忆管理等核心功能
2. **向量数据库构建系统**：负责从原始文档提取数据、生成向量数据库

系统支持多模态内容查询（文本、图片、表格），提供智能问答、内容检索、答案生成、记忆管理等功能。

## 🚀 快速开始

> **前提**：系统已安装并启动，如未启动请参考 `快速启动指南.md`

### 系统访问地址
- **前端界面**：http://localhost:3000
- **API服务**：http://localhost:8000
- **API文档**：http://localhost:8000/docs

## 📖 主要功能

### RAG查询系统功能

#### 1. 智能查询
- **接口**：`POST /api/v3/rag/query`
- **功能**：智能识别查询类型，生成准确答案
- **支持类型**：文本、图片、表格、混合查询

#### 2. 内容搜索
- **接口**：`POST /api/v3/rag/search`
- **功能**：多模态内容检索
- **支持内容**：文本、图片、表格

#### 3. 文档重排序
- **接口**：`POST /api/v3/rag/rerank`
- **功能**：智能重排序检索结果

#### 4. 答案溯源
- **接口**：`POST /api/v3/rag/attribution`
- **功能**：获取答案来源信息

#### 5. 记忆管理
- **接口**：`GET /api/v3/rag/memory/stats`
- **功能**：管理多轮对话记忆
- **支持功能**：记忆统计、会话管理、记忆清理

### 向量数据库构建系统功能

#### 1. 文档处理
- **命令**：`python main.py --input-type pdf`
- **功能**：从PDF文档开始，完整处理流程
- **支持格式**：PDF文档

#### 2. 内容向量化
- **命令**：`python main.py --input-type mineru_output`
- **功能**：从minerU输出开始，进行向量化
- **支持内容**：文本、图片、表格

#### 3. 数据库诊断
- **命令**：`python main.py --diagnose-db`
- **功能**：检查数据库完整性和内容分析
- **支持模式**：完整诊断、交互式诊断

#### 4. 补做处理
- **命令**：`python main.py --check-completion`
- **功能**：检查并补做图片增强和向量化
- **适用场景**：处理中断后的恢复

## 🔍 使用示例

### RAG查询系统API示例

#### 1. 智能查询示例
```bash
curl -X POST "http://localhost:8000/api/v3/rag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "中芯国际2025年一季度业绩如何？",
    "query_type": "smart",
    "max_results": 10,
    "relevance_threshold": 0.5
  }'
```

#### 2. 内容搜索示例
```bash
curl -X POST "http://localhost:8000/api/v3/rag/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "中芯国际业绩图表",
    "content_type": "image",
    "max_results": 20
  }'
```

#### 3. 记忆管理示例
```bash
# 获取记忆统计
curl -X GET "http://localhost:8000/api/v3/rag/memory/stats"

# 获取会话列表
curl -X GET "http://localhost:8000/api/v3/rag/memory/sessions"

# 清理过期记忆
curl -X POST "http://localhost:8000/api/v3/rag/memory/cleanup"
```

#### 4. 健康检查
```bash
curl -X GET "http://localhost:8000/api/v3/rag/health"
```

### 向量数据库构建系统命令示例

#### 1. 从PDF开始处理
```bash
cd db_system
python main.py --input-type pdf --input-path ./document/orig_pdf
```

#### 2. 从minerU输出开始处理
```bash
cd db_system
python main.py --input-type mineru_output --input-path ./document/md
```

#### 3. 数据库诊断
```bash
cd db_system
python main.py --diagnose-db
```

#### 4. 补做处理
```bash
cd db_system
python main.py --check-completion
```

## ⚙️ 系统管理

### RAG查询系统管理

#### 查看系统状态
```bash
# 健康检查
curl -X GET "http://localhost:8000/api/v3/rag/health"

# 系统配置
curl -X GET "http://localhost:8000/api/v3/rag/config"

# 系统统计
curl -X GET "http://localhost:8000/api/v3/rag/stats"

# 向量数据库状态
curl -X GET "http://localhost:8000/api/v3/rag/vector-db/status"

# 记忆模块状态
curl -X GET "http://localhost:8000/api/v3/rag/memory/status"
```

### 向量数据库构建系统管理

#### 查看处理状态
```bash
cd db_system

# 查看详细日志
python main.py --log-level DEBUG

# 检查数据库完整性
python main.py --diagnose-db

# 查看配置信息
python main.py --config-path ./config/v3_config.json --log-level DEBUG
```

#### 数据库维护
```bash
# 备份向量数据库
cp -r central/vector_db/ vector_db_backup_$(date +%Y%m%d)

# 恢复向量数据库
cp -r vector_db_backup_20250909/ central/vector_db/

# 查看数据库结构
ls -la central/vector_db/langchain_faiss_index/
```

## 🎯 使用场景

### 1. 完整文档处理流程
- **步骤1**：将PDF文档放入`db_system/document/orig_pdf/`目录
- **步骤2**：运行向量数据库构建系统处理文档
- **步骤3**：启动RAG查询系统进行智能问答
- **步骤4**：通过前端界面或API进行查询

### 2. 多模态检索
- 文本内容检索
- 图片内容检索
- 表格数据检索
- 混合内容检索

### 3. 智能分析
- 内容相似度分析
- 智能重排序
- 答案质量评估

### 4. 记忆管理
- 多轮对话上下文管理
- 历史查询记录
- 智能查询重写

## 🔧 故障排除

### 常见问题

#### 1. API无响应
```bash
# 检查服务是否启动
curl http://localhost:8000/api/v3/rag/health

# 检查端口占用
netstat -ano | findstr :8000
```

#### 2. 查询返回错误
- 检查查询参数格式是否正确
- 确认向量数据库已初始化
- 查看API文档了解正确的参数格式

#### 3. 前端无法连接后端
- 确认后端服务已启动
- 检查API地址配置是否正确
- 确认防火墙设置允许本地访问

### 日志查看
```bash
# 查看RAG查询系统日志
tail -f logs/rag_system.log

# 查看向量数据库构建系统日志
tail -f db_system/logs/v3_processing.log

# 查看记忆模块日志
grep "memory" logs/rag_system.log

# 查看向量化日志
grep "vectorization" db_system/logs/v3_processing.log
```

## 📚 相关文档

### 快速入门
- **快速启动指南**：`快速启动指南.md` - 5分钟快速体验
- **部署指南**：`DEPLOYMENT.md` - 完整安装部署说明

### 技术文档
- **架构文档**：`ARCHITECTURE.md` - 系统架构设计
- **API文档**：`API_DOCUMENTATION.md` - 详细API说明
- **项目说明**：`README.md` - 项目概述

### 在线资源
- **API文档**：http://localhost:8000/docs
- **系统状态**：http://localhost:8000/api/v3/rag/health

---

**版本**：RAG系统V3.0.0  
**最后更新**：2025年9月1日  
**维护团队**：RAG系统开发团队
