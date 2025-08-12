# **1. 基本介绍**

`V800_v2_main.py` 是V2版本RAG系统的主程序入口，集成了V2引擎系统（图片、文本、表格、混合引擎），提供命令行接口和Web服务。

### **2. 命令行参数说明**

```bash
python V800_v2_main.py [选项]
```

#### **主要参数**

- `--mode`: 运行模式，可选值：`status`、`process`、`qa`、`web`
- `--question`: 问题内容（qa模式必需）
- `--query-type`: 查询类型，可选值：`hybrid`、`image`、`text`、`table`
- `--user-id`: 用户ID，默认：`default_user`
- `--no-memory`: 不使用记忆功能
- `--pdf-dir`: PDF目录路径（process模式）
- `--output-dir`: 输出目录路径（process模式）
- `--host`: Web服务器主机地址，默认：`0.0.0.0`
- `--port`: Web服务器端口，默认：`5000`
- `--debug`: 启用调试模式

### **3. 使用模式详解**

#### **3.1 系统状态查看模式**

```bash
# 查看V2系统状态
python V800_v2_main.py --mode status

# 或者简写（默认模式）
python V800_v2_main.py
```

**输出示例：**

```
🚀 初始化V2 RAG系统...
📊 V2系统状态:
  system_version: V2.0.0
  config_loaded: True
  hybrid_engine_ready: True
  memory_manager_ready: True
  document_pipeline_ready: True
  vector_db: {'path': 'D:\\...\\central\\vector_db', 'metadata_exists': True, 'index_exists': True}
  memory_stats: {'total_users': 1, 'total_memory': 1}
  v2_config: {'image_engine_ready': True, 'text_engine_ready': True, 'table_engine_ready': True}
```

#### **3.2 问答模式**

**图片查询：**

```bash
# 查询图片"图4"
python V800_v2_main.py --mode qa --question "图4是什么？" --query-type image

# 查询图片"财务图表"
python V800_v2_main.py --mode qa --question "财务图表" --query-type image --user-id "user123"
```

**文本查询：**

```bash
# 查询文本内容
python V800_v2_main.py --mode qa --question "中芯国际的业绩如何？" --query-type text

# 查询文本内容，不使用记忆
python V800_v2_main.py --mode qa --question "中芯国际的业绩如何？" --query-type text --no-memory
```

**表格查询：**

```bash
# 查询表格数据
python V800_v2_main.py --mode qa --question "财务数据表格" --query-type table

# 查询表格数据，指定用户ID
python V800_v2_main.py --mode qa --question "财务数据表格" --query-type table --user-id "analyst001"
```

**混合查询：**

```bash
# 混合查询（默认类型）
python V800_v2_main.py --mode qa --question "中芯国际的财务表现如何？"

# 或者明确指定混合查询
python V800_v2_main.py --mode qa --question "中芯国际的财务表现如何？" --query-type hybrid
```

#### **3.3 文档处理模式**

```bash
# 处理文档（使用配置文件中的默认路径）
python V800_v2_main.py --mode process

# 处理指定目录的文档
python V800_v2_main.py --mode process --pdf-dir "D:/documents/pdfs" --output-dir "D:/documents/output"
```

#### **3.4 Web服务器模式**

```bash
# 启动Web服务器（默认端口5000）
python V800_v2_main.py --mode web

# 启动Web服务器，指定主机和端口
python V800_v2_main.py --mode web --host 127.0.0.1 --port 5001

# 启动Web服务器，启用调试模式
python V800_v2_main.py --mode web --host 127.0.0.1 --port 5001 --debug
```

### **4. 实际使用示例**

#### **示例1：快速检查系统状态**

```bash
python V800_v2_main.py
```

#### **示例2：查询图片信息**

```bash
python V800_v2_main.py --mode qa --question "图4：中芯国际归母净利润情况概览" --query-type image
```

#### **示例3：查询公司业绩文本**

```bash
python V800_v2_main.py --mode qa --question "中芯国际2024年业绩表现" --query-type text
```

#### **示例4：查询财务表格数据**

```bash
python V800_v2_main.py --mode qa --question "财务数据表格 营收利润" --query-type table
```

#### **示例5：综合查询公司信息**

```bash
python V800_v2_main.py --mode qa --question "中芯国际公司概况、业绩、财务图表" --query-type hybrid
```

#### **示例6：启动Web服务供团队使用**

```bash
python V800_v2_main.py --mode web --host 0.0.0.0 --port 5000
```

### **5. Web界面使用**

启动Web服务器后，可以通过浏览器访问：

- **V2前端界面**: `http://localhost:5000/v2`
- **健康检查**: `http://localhost:5000/health`
- **API状态**: `http://localhost:5000/api/v2/status`

### **6. 高级用法**

#### **6.1 批量查询脚本**

```bash
# 创建查询脚本
echo "图4是什么？" > queries.txt
echo "中芯国际业绩如何？" >> queries.txt
echo "财务数据表格" >> queries.txt

# 批量执行查询
while IFS= read -r question; do
    echo "查询: $question"
    python V800_v2_main.py --mode qa --question "$question" --query-type hybrid
    echo "---"
done < queries.txt
```

#### **6.2 定时任务**

```bash
# 每天检查系统状态
0 9 * * * cd /path/to/project && python V800_v2_main.py --mode status >> daily_status.log
```

### **7. 常见问题解决**

#### **7.1 端口被占用**

```bash
# 使用不同端口
python V800_v2_main.py --mode web --port 5001
```

#### **7.2 内存不足**

```bash
# 不使用记忆功能
python V800_v2_main.py --mode qa --question "问题" --query-type hybrid --no-memory
```

#### **7.3 调试模式**

```bash
# 启用调试模式查看详细日志
python V800_v2_main.py --mode web --debug
```

### **8. 性能优化建议**

1. **查询类型选择**：根据查询内容选择合适的查询类型，避免不必要的混合查询
2. **结果数量控制**：在Web界面中调整最大结果数，避免返回过多数据
3. **缓存利用**：系统会自动缓存查询结果，重复查询会更快
4. **并发控制**：Web模式下避免同时发起过多查询请求

### **9. 监控和维护**

```bash
# 检查引擎状态
curl http://localhost:5000/api/v2/engines/status

# 刷新引擎缓存
curl -X POST http://localhost:5000/api/v2/engines/refresh

# 查看系统健康状态
curl http://localhost:5000/health
```
