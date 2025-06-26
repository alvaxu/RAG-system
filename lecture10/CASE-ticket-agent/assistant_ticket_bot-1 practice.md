# 门票助手程序解析

## 1. 程序概述
这是一个基于通义千问大语言模型的门票查询助手程序，支持通过命令行界面(TUI)和网页界面(GUI)两种方式与用户交互。程序主要功能是查询和分析门票订单数据。

## 2. 程序架构

### 2.1 核心组件
1. **系统提示（system_prompt）**
   - 定义门票订单表结构
   - 说明SKU类型和查询方式
   - 提供SQL查询示例

2. **SQL查询工具（ExcSQLTool）**
   - 继承自BaseTool基类
   - 执行SQL查询并返回结果
   - 支持数据库连接和错误处理

3. **交互界面**
   - 命令行界面（TUI）
   - 网页界面（GUI）

### 2.2 数据表结构
```sql
CREATE TABLE tkt_orders (
    order_time DATETIME,             -- 订单日期
    account_id INT,                  -- 预定用户ID
    gov_id VARCHAR(18),              -- 商品使用人ID（身份证号）
    gender VARCHAR(10),              -- 使用人性别
    age INT,                         -- 年龄
    province VARCHAR(30),           -- 使用人省份
    SKU VARCHAR(100),                -- 商品SKU名
    product_serial_no VARCHAR(30),  -- 商品ID
    eco_main_order_id VARCHAR(20),  -- 订单ID
    sales_channel VARCHAR(20),      -- 销售渠道
    status VARCHAR(30),             -- 商品状态
    order_value DECIMAL(10,2),       -- 订单金额
    quantity INT                     -- 商品数量
);
```

### 2.3 门票类型
1. 一日门票SKU：
   - Universal Studios Beijing One-Day Dated Ticket-Standard
   - Universal Studios Beijing One-Day Dated Ticket-Child
   - Universal Studios Beijing One-Day Dated Ticket-Senior

2. 二日门票SKU：
   - USB 1.5-Day Dated Ticket Standard
   - USB 1.5-Day Dated Ticket Discounted

## 3. 功能实现

### 3.1 SQL查询工具
```python
@register_tool('exc_sql')
class ExcSQLTool(BaseTool):
```
- 支持SQL语句执行
- 返回查询结果（最多10行）
- 错误处理和异常捕获

### 3.2 助手服务初始化
```python
def init_agent_service():
```
- 配置通义千问模型参数
- 初始化助手实例
- 注册SQL查询工具
- 设置助手名称和描述

### 3.3 交互界面

#### 3.3.1 命令行界面（TUI）
```python
def app_tui():
```
- 支持连续对话
- 支持文件输入
- 实时响应用户查询
- 异常处理和错误提示

#### 3.3.2 网页界面（GUI）
```python
def app_gui():
```
- 基于WebUI提供图形界面
- 预设常用查询建议
- 支持实时对话
- 异常处理和错误提示

## 4. 使用说明

### 4.1 环境要求
- Python 3.x
- 必要的依赖包：
  - dashscope
  - qwen_agent
  - pandas
  - sqlalchemy
  - mysql-connector-python

### 4.2 配置要求
- 通义千问API密钥（DASHSCOPE_API_KEY）
- MySQL数据库连接信息

### 4.3 运行方式
```python
if __name__ == '__main__':
    app_gui()  # 图形界面模式（默认）
    # app_tui()  # 命令行模式
```

## 5. 示例查询
1. 2023年4、5、6月一日门票，二日门票的销量统计（按周）
2. 2023年7月的不同省份入园人数统计
3. 2023年10月1-7日销售渠道订单金额排名

## 6. 注意事项

1. 数据库安全
   - 使用安全的数据库连接方式
   - 避免SQL注入风险
   - 限制查询结果数量

2. 错误处理
   - 处理数据库连接错误
   - 处理SQL执行错误
   - 处理用户输入验证

3. 性能优化
   - 限制查询结果数量
   - 优化SQL查询语句
   - 处理大数据量查询

## 7. 可能的改进方向

1. 功能扩展
   - 添加更多数据分析功能
   - 支持更多查询维度
   - 添加数据可视化功能

2. 性能优化
   - 实现查询缓存
   - 优化数据库连接池
   - 添加查询超时控制

3. 用户体验
   - 优化错误提示
   - 添加更多查询建议
   - 支持更多查询格式 