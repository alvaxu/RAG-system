# RAG系统V3部署指南

## 📋 系统概述

RAG系统V3是一个基于检索增强生成（Retrieval-Augmented Generation）的智能问答系统，支持文本、图像和表格的多模态检索，具备完整的配置管理、性能优化和前端界面。

## 🏗️ 系统架构

### 核心组件
- **召回引擎**：支持文本、图像、表格的智能检索
- **LLM调用器**：集成大语言模型，支持多种提示词模板
- **重排序服务**：多模型重排序，提升结果质量
- **配置管理**：高级配置管理，支持导入导出、版本控制、热更新
- **前端界面**：基于Vue.js 3的现代化用户界面

### 技术栈
- **后端**：Python 3.8+, FastAPI, FAISS, Jieba
- **前端**：Vue.js 3, Vite, Element Plus, SCSS
- **数据库**：向量数据库（FAISS）
- **AI模型**：通义千问（DashScope）

## 📦 环境要求

### 系统要求
- **操作系统**：Windows 10/11, Linux, macOS
- **Python版本**：3.8 或更高版本
- **Node.js版本**：16.0 或更高版本
- **内存**：至少 4GB RAM
- **存储**：至少 2GB 可用空间

### Python依赖
```bash
# 核心依赖
fastapi>=0.104.0
uvicorn>=0.24.0
faiss-cpu>=1.7.4
jieba>=0.42.1
pydantic>=2.0.0
python-multipart>=0.0.6

# AI模型依赖
dashscope>=1.14.0

# 数据处理依赖
numpy>=1.24.0
pandas>=2.0.0
pillow>=10.0.0

# 配置管理依赖
pyyaml>=6.0
```

### 前端依赖
```json
{
  "dependencies": {
    "vue": "^3.3.0",
    "vue-router": "^4.2.0",
    "element-plus": "^2.4.0",
    "axios": "^1.5.0"
  },
  "devDependencies": {
    "vite": "^4.4.0",
    "@vitejs/plugin-vue": "^4.3.0",
    "sass": "^1.66.0"
  }
}
```

## 🚀 安装部署

### 1. 克隆项目
```bash
git clone <repository-url>
cd RAGsystemV3
```

### 2. 后端部署

#### 2.1 创建虚拟环境
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

#### 2.2 安装Python依赖
```bash
pip install -r requirements.txt
```

#### 2.3 配置环境变量
创建 `.env` 文件：
```bash
# AI模型配置
DASHSCOPE_API_KEY=your_dashscope_api_key_here

# 数据库配置
VECTOR_DB_PATH=./data/vector_db
CONFIG_PATH=./config

# 服务配置
HOST=0.0.0.0
PORT=8000
DEBUG=False
```

#### 2.4 初始化数据库
```bash
python -m rag_system.main --init-db
```

#### 2.5 启动后端服务
```bash
# 开发模式
python -m rag_system.main --mode dev

# 生产模式
python -m rag_system.main --mode prod
```

### 3. 前端部署

#### 3.1 安装Node.js依赖
```bash
cd frontend
npm install
```

#### 3.2 配置API地址
编辑 `frontend/src/services/api.js`：
```javascript
const API_BASE_URL = 'http://localhost:8000/api/v1';
```

#### 3.3 构建前端
```bash
# 开发模式
npm run dev

# 生产构建
npm run build
```

#### 3.4 部署前端
```bash
# 将构建结果部署到Web服务器
cp -r dist/* /var/www/html/
```

## ⚙️ 配置说明

### 系统配置
系统配置文件位于 `config/` 目录：

- `v3_config.json`：主配置文件
- `v3_config_schema.json`：配置模式定义
- `backups/`：配置备份目录

### 主要配置项
```json
{
  "rag_system": {
    "query_processing": {
      "max_results": 10,
      "similarity_threshold": 0.3
    },
    "retrieval": {
      "batch_size": 32,
      "cache_enabled": true,
      "cache_ttl": 3600
    },
    "llm_caller": {
      "model_name": "qwen-turbo",
      "max_tokens": 2000,
      "temperature": 0.7
    },
    "reranking": {
      "enabled": true,
      "models": ["dashscope", "rule_based"],
      "weights": [0.6, 0.4]
    }
  }
}
```

## 🔧 系统管理

### 配置管理
```bash
# 导出配置
python -m rag_system.core.config_advanced --export config_backup.json

# 导入配置
python -m rag_system.core.config_advanced --import config_backup.json

# 备份配置
python -m rag_system.core.config_advanced --backup

# 恢复配置
python -m rag_system.core.config_advanced --restore backup_name
```

### 性能监控
```bash
# 查看系统状态
python -m rag_system.main --status

# 查看性能指标
python -m rag_system.main --metrics

# 清理缓存
python -m rag_system.main --clear-cache
```

### 日志管理
```bash
# 查看日志
tail -f logs/v3_processing.log

# 清理日志
python -m rag_system.main --clean-logs
```

## 🧪 测试验证

### 运行测试套件
```bash
cd rag_system/tests
python run_all_tests.py
```

### 功能测试
```bash
# 测试召回引擎
python test_retrieval_algorithms_simple.py

# 测试LLM调用器
python test_llm_caller_enhanced.py

# 测试重排序服务
python test_reranking_enhanced.py

# 测试视觉搜索
python test_visual_search.py

# 测试表格搜索
python test_table_search.py

# 测试混合搜索
python test_hybrid_search.py

# 测试性能优化
python test_performance_optimization.py

# 测试配置管理
python test_config_advanced.py
```

## 🚨 故障排除

### 常见问题

#### 1. API密钥问题
```
错误：DashScope API调用失败: Invalid API-key provided
解决：检查DASHSCOPE_API_KEY环境变量是否正确设置
```

#### 2. 数据库连接问题
```
错误：向量数据库初始化失败
解决：检查VECTOR_DB_PATH路径是否存在且有写权限
```

#### 3. 前端连接问题
```
错误：前端无法连接后端API
解决：检查API_BASE_URL配置和后端服务是否正常运行
```

#### 4. 内存不足
```
错误：内存不足导致服务崩溃
解决：增加系统内存或调整batch_size配置
```

### 日志分析
```bash
# 查看错误日志
grep "ERROR" logs/v3_processing.log

# 查看警告日志
grep "WARNING" logs/v3_processing.log

# 查看性能日志
grep "performance" logs/v3_processing.log
```

## 📊 性能优化

### 系统优化建议
1. **内存优化**：调整batch_size和cache_size参数
2. **CPU优化**：启用并行处理，调整线程数
3. **存储优化**：定期清理缓存和日志文件
4. **网络优化**：使用CDN加速前端资源

### 监控指标
- **响应时间**：平均查询响应时间 < 2秒
- **吞吐量**：支持并发查询数 > 100
- **准确率**：检索准确率 > 85%
- **可用性**：系统可用性 > 99%

## 🔒 安全考虑

### 数据安全
- 定期备份配置和数据库
- 使用HTTPS加密传输
- 限制API访问权限
- 定期更新依赖包

### 访问控制
- 配置防火墙规则
- 使用API密钥认证
- 限制文件上传类型
- 监控异常访问

## 📈 扩展部署

### 水平扩展
- 使用负载均衡器分发请求
- 部署多个后端实例
- 使用共享存储保存数据
- 配置服务发现机制

### 垂直扩展
- 增加服务器内存和CPU
- 使用SSD存储提升I/O性能
- 优化数据库索引
- 启用GPU加速（如适用）

## 📞 技术支持

### 联系方式
- **项目仓库**：[GitHub Repository URL]
- **问题反馈**：[Issues URL]
- **文档更新**：[Wiki URL]

### 版本信息
- **当前版本**：V3.0.0
- **发布日期**：2025-09-01
- **兼容性**：Python 3.8+, Node.js 16+

---

## 📝 更新日志

### V3.0.0 (2025-09-01)
- ✅ 完成核心架构重构
- ✅ 实现多模态检索（文本、图像、表格）
- ✅ 集成高级配置管理
- ✅ 开发现代化前端界面
- ✅ 完成系统集成测试
- ✅ 完善部署文档

---

**注意**：本部署指南基于RAG系统V3.0.0版本编写，如有疑问请参考项目文档或联系技术支持。
