# RAG系统V3使用手册

## 📋 系统概述

RAG系统V3是一个智能检索增强生成系统，支持多模态内容查询（文本、图片、表格），提供智能问答、内容检索、答案生成等功能。

## 🚀 快速开始

### 1. 环境要求
- Python 3.8+
- Node.js 16+ (可选，用于前端)
- 已安装的依赖包

### 2. 系统状态检查
```bash
# 检查RAG系统是否已安装
pip list | findstr rag

# 应该看到：rag-system-v3 3.0.0
```

## 🔧 启动服务

### 方式零：一键启动（推荐）
```bash
# 使用启动脚本一键启动后端和前端
python start_rag_system.py
```

### 方式一：启动后端API服务

#### 方法1：从项目根目录启动（推荐）
```bash
# 在项目根目录 (RAGsystemV3/) 执行
python -m uvicorn rag_system.api.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 方法2：从rag_system目录启动
```bash
# 进入RAG系统目录
cd rag_system

# 启动FastAPI服务
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

**注意**：
- 方法1（推荐）：从项目根目录启动，使用完整模块路径
- 方法2：从 `rag_system` 目录启动，使用相对模块路径

**服务地址：**
- API服务：http://localhost:8000
- API文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

### 方式二：启动前端界面
```bash
# 进入前端目录
cd frontend

# 安装依赖（首次运行）
npm install

# 启动开发服务器
npm run dev
```

**注意**：必须在 `frontend` 目录下运行，否则会出现找不到 `package.json` 的错误

**前端地址：**
- 前端界面：http://localhost:3000

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

## 🧪 测试系统

### 运行完整测试套件
```bash
cd rag_system/tests
python run_all_tests.py
```

### 运行特定功能测试
```bash
# 测试查询处理
python test_new_architecture.py

# 测试召回算法
python test_retrieval_algorithms_simple.py

# 测试视觉搜索
python test_visual_search.py

# 测试表格搜索
python test_table_search.py

# 测试性能优化
python test_performance_optimization.py
```

## ⚙️ 配置管理

### 查看系统配置
```bash
curl -X GET "http://localhost:8000/api/v3/rag/config"
```

### 查看向量数据库状态
```bash
curl -X GET "http://localhost:8000/api/v3/rag/vector-db/status"
```

### 查看系统统计
```bash
curl -X GET "http://localhost:8000/api/v3/rag/stats"
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

#### 1. 服务启动失败
```bash
# 检查端口是否被占用
netstat -ano | findstr :8000

# 检查Python环境
python --version
pip list | findstr rag
```

#### 1.1 后端启动失败 - ModuleNotFoundError: No module named 'api'
**问题**：在项目根目录运行 `python -m uvicorn api.main:app`
**解决方案**：
```bash
# 正确做法：先进入rag_system目录
cd rag_system
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 1.2 前端启动失败 - Could not read package.json
**问题**：在项目根目录运行 `npm run dev`
**解决方案**：
```bash
# 正确做法：先进入frontend目录
cd frontend
npm run dev
```

#### 2. 导入错误
```bash
# 重新安装RAG系统
pip install -e .

# 检查Python路径
python -c "import rag_system; print('导入成功')"
```

#### 3. 配置问题
```bash
# 检查配置文件
ls db_system/config/v3_config.json

# 验证配置
curl -X GET "http://localhost:8000/api/v3/rag/config"
```

### 日志查看
```bash
# 查看RAG系统日志
tail -f rag_system/logs/rag_system.log

# 查看V3系统日志
tail -f db_system/logs/v3_processing.log
```

## 📚 更多信息

### 文档资源
- **架构文档**：`ARCHITECTURE.md`
- **API文档**：`API_DOCUMENTATION.md`
- **部署文档**：`DEPLOYMENT.md`
- **项目说明**：`README.md`

### 设计文档
- 查询处理模块设计：`share/1.prepare/33.V3_RAG查询处理模块详细设计文档.md`
- LLM调用模块设计：`share/1.prepare/35.V3_RAG_LLM调用模块详细设计文档.md`
- 配置管理设计：`share/1.prepare/36.RAG系统配置管理详细设计文档.md`
- 图片召回策略：`share/1.prepare/41.RAG系统图片召回策略详细设计文档.md`

## 🆘 技术支持

### 获取帮助
1. 查看API文档：http://localhost:8000/docs
2. 运行测试验证功能
3. 查看日志文件排查问题
4. 参考设计文档了解详细实现

### 系统状态监控
- 健康检查：`/api/v3/rag/health`
- 系统统计：`/api/v3/rag/stats`
- 配置信息：`/api/v3/rag/config`

---

**版本**：RAG系统V3.0.0  
**最后更新**：2025年9月1日  
**维护团队**：RAG系统开发团队
