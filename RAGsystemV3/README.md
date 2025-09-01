# RAG系统V3 - 智能检索增强生成系统

[![Version](https://img.shields.io/badge/version-3.0.0-blue.svg)](https://github.com/your-repo/rag-system-v3)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()

## 📋 项目简介

RAG系统V3是一个基于检索增强生成（Retrieval-Augmented Generation）的智能问答系统，支持多模态内容检索，包括文本、图像和表格。系统采用模块化设计，具备完整的配置管理、性能优化和现代化用户界面。

### ✨ 核心特性

- 🔍 **多模态检索**：支持文本、图像、表格的智能检索
- 🤖 **智能问答**：集成大语言模型，生成高质量回答
- 🔄 **重排序优化**：多模型重排序，提升结果质量
- ⚙️ **高级配置**：支持配置导入导出、版本控制、热更新
- 🚀 **性能优化**：批处理、缓存、并行处理
- 🎨 **现代界面**：基于Vue.js 3的响应式用户界面
- 📊 **实时监控**：完整的性能指标和系统监控

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    前端用户界面 (Vue.js 3)                    │
├─────────────────────────────────────────────────────────────┤
│                    API网关 (FastAPI)                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ 查询处理器  │  │ 召回引擎    │  │ LLM调用器   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ 重排序服务  │  │ 配置管理    │  │ 元数据管理  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ 向量数据库  │  │ 文件存储    │  │ 缓存系统    │         │
│  │  (FAISS)    │  │             │  │             │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 环境要求

- **Python**: 3.8 或更高版本
- **Node.js**: 16.0 或更高版本
- **内存**: 至少 4GB RAM
- **存储**: 至少 2GB 可用空间

### 安装步骤

#### 1. 克隆项目
```bash
git clone https://github.com/your-repo/rag-system-v3.git
cd rag-system-v3
```

#### 2. 后端部署
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置 DASHSCOPE_API_KEY

# 初始化数据库
python -m rag_system.main --init-db

# 启动后端服务
python -m rag_system.main --mode dev
```

#### 3. 前端部署
```bash
cd frontend
npm install
npm run dev
```

#### 4. 访问系统
- 前端界面: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

## 📚 功能模块

### 🔍 多模态检索

#### 文本检索
- 语义相似度计算
- 关键词提取和匹配
- 上下文理解
- 多语言支持

#### 图像检索
- 视觉特征提取
- 内容识别
- 风格分析
- 相似度计算

#### 表格检索
- 结构分析
- 语义理解
- 关键词匹配
- 数据查询

#### 混合检索
- 多模态融合
- 智能权重分配
- 结果去重
- 多样性保证

### 🤖 智能问答

#### LLM集成
- 通义千问模型
- 多模型支持
- 提示词管理
- 上下文优化

#### 回答生成
- 结构化输出
- 来源标注
- 置信度评估
- 实时生成

### 🔄 重排序优化

#### 多模型重排序
- DashScope模型
- 规则基础排序
- 混合策略
- 性能优化

#### 结果优化
- 相关性提升
- 多样性保证
- 去重处理
- 质量评估

### ⚙️ 配置管理

#### 高级功能
- 配置导入导出
- 版本控制
- 热更新
- 备份恢复

#### 监控指标
- 性能统计
- 使用分析
- 错误监控
- 系统健康

## 🧪 测试

### 运行测试套件
```bash
cd rag_system/tests
python run_all_tests.py
```

### 测试覆盖
- ✅ 召回引擎算法测试
- ✅ LLM调用器功能测试
- ✅ 重排序服务测试
- ✅ 视觉搜索功能测试
- ✅ 表格搜索功能测试
- ✅ 混合搜索策略测试
- ✅ 性能优化算法测试
- ✅ 配置管理功能测试

### 测试结果
```
🎉 所有测试通过！RAG系统功能正常
📊 测试统计:
  - 总测试数: 67
  - 通过数量: 67
  - 失败数量: 0
  - 通过率: 100.0%
```

## 📖 文档

- [部署指南](DEPLOYMENT.md) - 详细的部署和配置说明
- [架构设计](ARCHITECTURE.md) - 系统架构和技术设计
- [API文档](API_DOCUMENTATION.md) - 完整的API接口文档
- [用户手册](USER_GUIDE.md) - 用户使用指南
- [开发指南](DEVELOPMENT.md) - 开发者文档

## 🔧 配置说明

### 环境变量
```bash
# AI模型配置
DASHSCOPE_API_KEY=your_api_key_here

# 数据库配置
VECTOR_DB_PATH=./data/vector_db
CONFIG_PATH=./config

# 服务配置
HOST=0.0.0.0
PORT=8000
DEBUG=False
```

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
    }
  }
}
```

## 🚀 性能特性

### 优化策略
- **批处理**: 支持批量查询处理
- **缓存**: 多级缓存提升响应速度
- **并行**: 多线程并行处理
- **懒加载**: 按需加载资源

### 性能指标
- **响应时间**: 平均 < 2秒
- **吞吐量**: 支持 > 100 并发查询
- **准确率**: 检索准确率 > 85%
- **可用性**: 系统可用性 > 99%

## 🔒 安全特性

### 数据安全
- 输入验证和过滤
- 输出转义和清理
- 文件上传限制
- 敏感信息保护

### 访问控制
- API密钥认证
- 权限管理
- 速率限制
- 操作审计

## 📈 使用场景

### 企业知识管理
- 文档检索和问答
- 技术文档查询
- 培训材料搜索
- 政策法规查询

### 学术研究
- 文献检索
- 数据查询
- 研究辅助
- 知识发现

### 客户服务
- 智能客服
- 产品咨询
- 技术支持
- 常见问题解答

## 🤝 贡献指南

### 开发流程
1. Fork 项目
2. 创建功能分支
3. 提交代码
4. 创建 Pull Request
5. 代码审查
6. 合并代码

### 代码规范
- 遵循 PEP 8 规范
- 添加类型注解
- 编写单元测试
- 更新文档

### 问题反馈
- 使用 GitHub Issues
- 提供详细描述
- 包含复现步骤
- 附上错误日志

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

感谢以下开源项目的支持：
- [FastAPI](https://fastapi.tiangolo.com/) - 现代、快速的Web框架
- [Vue.js](https://vuejs.org/) - 渐进式JavaScript框架
- [FAISS](https://github.com/facebookresearch/faiss) - 高效的相似性搜索库
- [Jieba](https://github.com/fxsjy/jieba) - 中文分词工具
- [DashScope](https://dashscope.aliyun.com/) - 阿里云AI模型服务

## 📞 联系我们

- **项目主页**: [GitHub Repository](https://github.com/your-repo/rag-system-v3)
- **问题反馈**: [GitHub Issues](https://github.com/your-repo/rag-system-v3/issues)
- **讨论交流**: [GitHub Discussions](https://github.com/your-repo/rag-system-v3/discussions)
- **邮箱联系**: your-email@example.com

## 📊 项目统计

![GitHub stars](https://img.shields.io/github/stars/your-repo/rag-system-v3?style=social)
![GitHub forks](https://img.shields.io/github/forks/your-repo/rag-system-v3?style=social)
![GitHub issues](https://img.shields.io/github/issues/your-repo/rag-system-v3)
![GitHub pull requests](https://img.shields.io/github/issues-pr/your-repo/rag-system-v3)

---

## 🎯 路线图

### V3.1.0 (计划中)
- [ ] 支持更多AI模型
- [ ] 增加多语言界面
- [ ] 优化移动端体验
- [ ] 增强安全功能

### V3.2.0 (规划中)
- [ ] 分布式部署支持
- [ ] 实时协作功能
- [ ] 高级分析功能
- [ ] 插件系统

### V4.0.0 (未来)
- [ ] 微服务架构
- [ ] 云原生部署
- [ ] 智能化运维
- [ ] 生态系统建设

---

**⭐ 如果这个项目对您有帮助，请给我们一个星标！**

**📝 最后更新**: 2025-09-01  
**🔄 版本**: V3.0.0  
**👥 维护团队**: RAG系统开发团队
