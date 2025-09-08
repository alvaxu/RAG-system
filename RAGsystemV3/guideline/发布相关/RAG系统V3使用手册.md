# RAG系统V3使用手册

## 📋 系统概述

RAG系统V3是一个智能检索增强生成系统，支持多模态内容查询（文本、图片、表格），提供智能问答、内容检索、答案生成等功能。

## 🚀 快速开始

> **前提**：系统已安装并启动，如未启动请参考 `快速启动指南.md`

### 系统访问地址
- **前端界面**：http://localhost:3000
- **API服务**：http://localhost:8000
- **API文档**：http://localhost:8000/docs

## 📖 主要功能

### 1. 智能查询
- **接口**：`POST /api/v3/rag/query`
- **功能**：智能识别查询类型，生成准确答案
- **支持类型**：文本、图片、表格、混合查询

### 2. 内容搜索
- **接口**：`POST /api/v3/rag/search`
- **功能**：多模态内容检索
- **支持内容**：文本、图片、表格

### 3. 文档重排序
- **接口**：`POST /api/v3/rag/rerank`
- **功能**：智能重排序检索结果

### 4. 答案溯源
- **接口**：`POST /api/v3/rag/attribution`
- **功能**：获取答案来源信息

## 🔍 API使用示例

### 1. 智能查询示例
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

### 2. 内容搜索示例
```bash
curl -X POST "http://localhost:8000/api/v3/rag/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "中芯国际业绩图表",
    "content_type": "image",
    "max_results": 20
  }'
```

### 3. 健康检查
```bash
curl -X GET "http://localhost:8000/api/v3/rag/health"
```

## ⚙️ 系统管理

### 查看系统状态
```bash
# 健康检查
curl -X GET "http://localhost:8000/api/v3/rag/health"

# 系统配置
curl -X GET "http://localhost:8000/api/v3/rag/config"

# 系统统计
curl -X GET "http://localhost:8000/api/v3/rag/stats"

# 向量数据库状态
curl -X GET "http://localhost:8000/api/v3/rag/vector-db/status"
```

## 🎯 使用场景

### 1. 文档问答
- 上传文档到V3数据库系统
- 使用RAG系统进行智能问答
- 获取带溯源的准确答案

### 2. 多模态检索
- 文本内容检索
- 图片内容检索
- 表格数据检索
- 混合内容检索

### 3. 智能分析
- 内容相似度分析
- 智能重排序
- 答案质量评估

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
# 查看系统日志
tail -f rag_system.log
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
