# RAG系统测试目录

## 📁 目录结构

```
tests/
├── __init__.py                 # 测试模块初始化文件
├── README.md                   # 本说明文档
├── run_backend_tests.py       # 后端功能测试运行器
├── test_config_validation.py  # 配置验证测试
└── test_new_architecture.py   # 新架构测试
```

## 🚀 运行测试

### 运行所有测试
```bash
cd rag_system
python tests/run_backend_tests.py
```

### 运行特定测试
```bash
# 配置验证测试
python tests/test_config_validation.py

# 新架构测试
python tests/test_new_architecture.py
```

## 🧪 测试内容

### 1. 配置验证测试 (`test_config_validation.py`)
- ✅ 有效配置验证
- ❌ 无效配置验证（缺少字段、类型错误、值超出范围）
- 🔍 配置问题检测
- 🎯 RAG配置验证

### 2. 新架构测试 (`test_new_architecture.py`)
- 🔧 配置集成测试
- 🌐 统一服务接口测试
- 🧠 智能处理器测试
- 🔀 混合处理器测试
- 🚦 查询路由器测试
- 📝 查询处理器测试
- 🔍 查询类型检测测试
- 🎯 端到端查询处理测试

## 📊 测试结果

所有测试通过后，您将看到：
```
🎉 所有测试通过！系统运行正常。
```

## 🔧 添加新测试

1. 在 `tests/` 目录下创建新的测试文件
2. 在 `run_backend_tests.py` 中添加新测试的调用
3. 确保测试文件遵循命名规范：`test_*.py`

## 📝 测试规范

- 测试函数名以 `test_` 开头
- 每个测试函数都有清晰的文档字符串
- 测试失败时提供有意义的错误信息
- 测试完成后返回布尔值表示成功/失败
