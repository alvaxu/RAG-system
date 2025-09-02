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

### 0. 快速启动（推荐）

#### 使用启动脚本
```bash
# 方法1：Python脚本（跨平台）
python start_rag_system.py

# 方法2：Windows批处理脚本（Windows专用）
start_rag.bat
```

**Python脚本功能（推荐）：**
- 自动检查环境依赖
- 启动后端API服务
- 启动前端开发服务器（开发模式，无需部署）
- 运行系统测试
- 跨平台支持（Windows/Linux/macOS）

**Windows批处理脚本功能：**
- 交互式菜单选择
- 环境依赖检查
- 自动安装前端依赖
- 分离控制台窗口
- Windows专用优化

**开发环境优势：**
- 🚀 **一键启动**：无需复杂的部署步骤
- 🔄 **热重载**：代码修改后自动刷新
- 🐛 **调试友好**：详细的错误信息和调试工具
- 📱 **即时预览**：http://localhost:3000 立即访问

#### 环境准备
**必需软件：**
- Python 3.8+ （已安装并配置到PATH）
- Node.js 16+ （已安装并配置到PATH）
- Git （用于克隆代码）

**验证安装：**
```bash
python --version  # 应显示 Python 3.8+
node --version    # 应显示 Node.js 16+
npm --version     # 应显示 npm 版本
git --version     # 应显示 Git 版本
```

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
创建 `.env` 文件（可选）：
```bash
# AI模型配置（必需）
DASHSCOPE_API_KEY=your_dashscope_api_key_here

# 服务配置（可选，有默认值）
HOST=0.0.0.0
PORT=8000
DEBUG=False
```

**注意：**
- 数据库路径和配置路径由系统自动管理，无需手动配置
- 配置文件位于 `db_system/config/` 目录

#### 2.4 数据库初始化
**无需手动初始化**，数据库会在首次启动时自动初始化。

#### 2.5 启动后端服务
```bash
# 方法1：使用启动脚本（推荐）
python start_rag_system.py

# 方法2：使用Windows批处理脚本（Windows专用）
start_rag.bat

# 方法3：直接启动FastAPI
python -m uvicorn rag_system.api.main:app --host 0.0.0.0 --port 8000 --reload

# 方法4：从rag_system目录启动
cd rag_system
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 前端部署

#### 3.1 安装Node.js依赖
```bash
cd frontend
npm install
```

**注意：**
- 确保 Node.js 已安装并配置到系统 PATH
- 如果 `npm` 命令不可用，请检查 Node.js 安装
- 在 Windows 上，可能需要使用 `npm.cmd` 而不是 `npm`

#### 3.2 配置API地址
编辑 `frontend/src/services/api.js`：
```javascript
const API_BASE_URL = 'http://localhost:8000/api/v3/rag';
```

#### 3.3 开发环境启动（推荐）
**开发环境无需部署，直接启动开发服务器：**
```bash
# 启动前端开发服务器
npm run dev
```

**开发环境特点：**
- ✅ 自动热重载，代码修改后自动刷新
- ✅ 详细的错误信息和调试信息
- ✅ 无需构建，直接运行源代码
- ✅ 访问地址：http://localhost:3000

#### 3.4 生产环境部署（可选）
**仅在生产环境需要构建和部署：**
```bash
# 1. 构建生产版本
npm run build

# 2. 部署到Web服务器（Linux示例）
cp -r dist/* /var/www/html/

# 3. 配置Web服务器（如Nginx）
# 让Web服务器提供静态文件服务
```

**生产环境特点：**
- ✅ 代码经过压缩和优化，性能更好
- ✅ 文件体积更小，加载更快
- ✅ 不暴露源代码，更安全
- ❌ 需要重新构建才能看到代码修改

## 🖥️ Windows批处理脚本使用指南

### start_rag.bat 详细说明

`start_rag.bat` 是专为 Windows 用户设计的交互式启动脚本，提供友好的菜单界面。

#### 启动方式
```bash
# 双击运行或在命令行中执行
start_rag.bat
```

#### 菜单选项说明

**1. 启动后端API服务**
- 仅启动后端服务
- 服务地址：http://localhost:8000
- API文档：http://localhost:8000/docs

**2. 启动前端界面**
- 仅启动前端开发服务器
- 自动检查并安装依赖
- 访问地址：http://localhost:3000

**3. 启动完整系统（推荐）**
- 同时启动后端和前端
- 在独立窗口中运行
- 自动检查环境依赖
- 自动安装前端依赖

**4. 运行API接口测试**
- 执行 `test_rag_api.py` 测试脚本
- 验证API接口功能

**5. 运行后端功能测试**
- 执行 `run_backend_tests.py` 测试套件
- 验证后端核心功能模块

**6. 退出**
- 退出启动脚本

#### 脚本特性

**环境检查：**
- ✅ 自动检查 Python 安装和版本
- ✅ 自动检查 Node.js 安装和版本
- ✅ 自动检查 npm 可用性
- ❌ 环境检查失败时提供详细指导

**依赖管理：**
- ✅ 自动检测前端依赖缺失
- ✅ 自动执行 `npm install`
- ✅ 依赖安装失败时提供错误信息

**用户体验：**
- ✅ 清晰的菜单界面
- ✅ 详细的进度提示
- ✅ 友好的错误信息
- ✅ 分离的控制台窗口

#### 使用示例

```bash
# 启动完整系统
start_rag.bat
# 选择 3

# 仅启动前端
start_rag.bat
# 选择 2

# 运行后端功能测试
start_rag.bat
# 选择 5

# 运行API接口测试
start_rag.bat
# 选择 4
```

#### 故障排除

**常见问题：**

1. **"Python未安装或未配置到PATH"**
   - 解决：安装 Python 3.8+ 并添加到系统 PATH

2. **"Node.js未安装或未配置到PATH"**
   - 解决：安装 Node.js 16+ 并添加到系统 PATH

3. **"前端依赖安装失败"**
   - 解决：检查网络连接，确保 npm 可正常访问

4. **"前端目录不存在package.json文件"**
   - 解决：确保在正确的项目根目录中运行脚本

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
**通过API端点管理配置：**
```bash
# 获取系统配置
curl http://localhost:8000/api/v3/rag/config

# 获取系统状态
curl http://localhost:8000/api/v3/rag/status

# 获取系统统计
curl http://localhost:8000/api/v3/rag/stats
```

**直接操作配置文件：**
```bash
# 配置文件位置
db_system/config/v3_config.json

# 备份配置
cp db_system/config/v3_config.json config_backup.json

# 恢复配置
cp config_backup.json db_system/config/v3_config.json
```

### 性能监控
**通过API端点监控：**
```bash
# 健康检查
curl http://localhost:8000/api/v3/rag/health

# 系统状态
curl http://localhost:8000/api/v3/rag/status

# 系统统计
curl http://localhost:8000/api/v3/rag/stats

# 向量数据库状态
curl http://localhost:8000/api/v3/rag/vector-db/status
```

### 日志管理
**日志文件位置：**
```bash
# 主日志文件
rag_system.log

# 查看日志
tail -f rag_system.log

# 清理日志
rm rag_system.log
```

## 🧪 测试验证

### 运行测试套件
```bash
# 方法1：使用启动脚本运行测试
python start_rag_system.py --test-only

# 方法2：直接运行测试
cd rag_system/tests
python run_backend_tests.py
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
解决：检查 central/vector_db/ 目录是否存在且有写权限
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
grep "ERROR" rag_system.log

# 查看警告日志
grep "WARNING" rag_system.log

# 查看性能日志
grep "performance" rag_system.log
```

## 📊 性能优化

### 系统优化建议
1. **内存优化**：调整batch_size和cache_size参数
2. **CPU优化**：启用并行处理，调整线程数
3. **存储优化**：定期清理缓存和日志文件
4. **网络优化**：使用CDN加速前端资源

### API性能优化
1. **服务状态缓存**：30秒缓存机制，减少重复服务状态检查
2. **轻量级健康检查**：快速响应，支持文档页面预加载
3. **优化响应时间**：所有API端点响应时间 < 0.3秒
4. **智能错误处理**：避免单个服务失败影响整体性能

### 监控指标
- **响应时间**：平均查询响应时间 < 2秒，API端点响应时间 < 0.3秒
- **吞吐量**：支持并发查询数 > 100
- **准确率**：检索准确率 > 85%
- **可用性**：系统可用性 > 99%
- **文档加载**：API文档页面加载时间 < 0.5秒

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
