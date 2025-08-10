# V502_image_enhancer_new 程序使用说明

## 程序概述

`V502_image_enhancer_new.py` 是一个图片增强新程序，专门用于查询、确认和深度处理数据库中的图片。

## 主要功能

### 1. 查询功能
- 查询数据库中的图片是否做了深度处理
- 列出哪些图片已处理，哪些未处理
- 统计处理状态和数量

### 2. 用户确认
- 根据用户确认决定是否补做深度处理
- 提供友好的交互界面
- 支持用户选择操作

### 3. 深度处理
- 处理方式与主程序 `image_enhancer.py` 完全一致
- 调用相同的图像增强模块
- 保持处理逻辑的一致性

### 4. 字段和逻辑
- 以现有数据库结构为准
- 遵循 `image_enhancer.py` 的字段规范
- 保持数据格式的一致性

## 程序特点

- **模块复用**: 可以调用 `image_enhancer.py` 中的相应模块
- **智能判断**: 自动识别图片是否已深度处理
- **进度显示**: 实时显示处理进度和状态
- **错误处理**: 完善的异常处理和错误报告
- **用户友好**: 清晰的提示信息和操作指引

## 使用方法

### 1. 运行程序
```bash
python V502_image_enhancer_new.py
```

### 2. 程序流程
1. **启动**: 程序初始化并加载配置
2. **查询**: 自动查询数据库中的图片状态
3. **显示**: 显示已处理和未处理的图片详情
4. **确认**: 用户选择是否进行深度处理
5. **处理**: 如果用户确认，开始深度处理图片
6. **结果**: 显示处理结果和统计信息

### 3. 用户交互
程序会提示用户选择操作：
- 输入 `1`: 进行深度处理
- 输入 `2`: 退出程序

## 技术实现

### 核心类
- `ImageEnhanceNew`: 主程序类，包含所有功能方法

### 主要方法
- `load_vector_store()`: 加载向量数据库
- `query_image_status()`: 查询图片处理状态
- `_is_deep_processed()`: 判断是否已深度处理
- `display_image_status()`: 显示图片状态信息
- `get_user_confirmation()`: 获取用户确认
- `process_unprocessed_images()`: 处理未处理的图片
- `display_processing_results()`: 显示处理结果

### 深度处理判断标准
程序通过以下字段判断图片是否已深度处理：
- `layered_descriptions`: 分层描述字段
- `structured_info`: 结构化信息字段
- `enhancement_timestamp`: 增强时间戳
- `enhanced_description`: 增强描述内容（包含深度标记）

## 配置要求

### 必需配置
- `dashscope_api_key`: DashScope API密钥
- 图片处理相关配置（通过以下属性访问）：
  - `enable_enhancement`: 是否启用图像增强
  - `enhancement_model`: 增强模型名称
  - `enhancement_max_tokens`: 最大token数量
  - `enhancement_temperature`: 温度参数
  - `enhancement_batch_size`: 批处理大小
  - `enable_progress_logging`: 是否启用进度日志

### 路径配置
- 向量数据库路径: `./central/vector_db`
- 配置文件: `config.json`

## 依赖模块

- `langchain_community.vectorstores.FAISS`: 向量数据库
- `langchain_community.embeddings.DashScopeEmbeddings`: 嵌入模型
- `config.settings.Settings`: 配置管理
- `document_processing.image_enhancer.ImageEnhancer`: 图像增强器

## 测试程序

### 运行测试
```bash
python test_image_enhancer_new.py
```

### 测试内容
- 模块导入测试
- 配置加载测试
- 向量数据库访问测试

## 注意事项

1. **API限制**: 处理过程中会添加延迟避免API调用限制
2. **文件检查**: 程序会检查图片文件是否存在
3. **错误处理**: 单个图片处理失败不会影响整体流程
4. **进度显示**: 实时显示处理进度和状态信息

## 故障排除

### 常见问题
1. **导入失败**: 检查依赖包是否正确安装
2. **配置错误**: 确认 `config.json` 文件存在且格式正确
3. **数据库访问失败**: 检查向量数据库路径和文件权限
4. **API调用失败**: 确认 DashScope API 密钥有效

### 调试信息
程序提供详细的日志信息，包括：
- 初始化状态
- 数据库加载信息
- 处理进度和结果
- 错误详情和堆栈跟踪

## 更新日志

- **v1.0**: 初始版本，实现基本功能
- 查询数据库图片状态
- 用户确认机制
- 深度处理功能
- 结果统计和显示

## 联系方式

如有问题或建议，请查看项目文档或联系开发团队。
