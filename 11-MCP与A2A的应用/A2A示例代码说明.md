# A2A示例代码说明

## 一、整体架构与功能概述

本示例包含两个主要程序：
- `WeatherAgent.py`：天气智能体服务，负责对外提供天气查询API。
- `BasketBallAgent.py`：篮球活动决策智能体，通过A2A协议调用天气智能体，自动决策是否安排篮球活动。

两者通过A2A（Agent-to-Agent）协议进行交互，实现了智能体间的能力发现、任务提交、结果获取的标准流程。

---

## 二、WeatherAgent.py 详解

### 1. 主要功能
- 提供指定日期、指定地点（目前仅支持"北京"）的天气数据查询服务。
- 以RESTful API形式对外暴露能力，支持A2A标准的能力发现与任务提交。

### 2. 主要接口
- `/.well-known/agent.json`：
  - 返回智能体的能力描述（Agent Card），包括名称、版本、描述、API端点、输入参数格式、认证方式等。
- `/api/tasks/weather`：
  - POST接口，接收A2A标准的任务请求，返回指定日期的天气数据。

### 3. 关键实现
- 使用FastAPI框架实现Web服务。
- 通过`WeatherTaskRequest`模型接收任务请求，参数包括`task_id`和`params`（其中`params`需包含`date`和`location`）。
- 内部维护一个`weather_db`字典，模拟天气数据。
- 返回结果中包含`artifact`字段，内含天气详情。
- 支持API Key认证（但示例未做实际校验）。

### 4. 示例返回
```json
{
  "task_id": "xxx",
  "status": "completed",
  "artifact": {
    "date": "2025-05-08",
    "weather": {"temperature": "25℃", "condition": "雷阵雨"}
  }
}
```

---

## 三、BasketBallAgent.py 详解

### 1. 主要功能
- 作为决策智能体，自动判断某天是否适合安排篮球活动。
- 通过A2A协议调用WeatherAgent，获取天气信息，结合业务逻辑做出决策。

### 2. 关键实现
- 通过HTTP请求获取WeatherAgent的能力描述（agent.json），动态发现API端点。
- 构造A2A标准任务对象（包含`task_id`和`params`），并POST到WeatherAgent的`/api/tasks/weather`接口。
- 解析返回的天气数据，根据天气情况（如有"雨"或"雪"则取消，否则确认）做出决策。
- 返回决策结果，包括活动状态和原因。

### 3. 主要方法说明
- `_create_task(target_date)`：生成A2A标准任务请求体。
- `check_weather(target_date)`：调用WeatherAgent获取天气数据。
- `schedule_meeting(date)`：综合决策逻辑，判断是否安排篮球活动。

### 4. 示例决策结果
- 天气良好：
```json
{"status": "confirmed", "weather": {"temperature": "22℃", "condition": "多云转晴"}}
```
- 恶劣天气：
```json
{"status": "cancelled", "reason": "恶劣天气"}
```
- 查询失败：
```json
{"status": "error", "detail": "天气查询失败: ..."}
```

---

## 四、两者之间的关系与A2A协议流程

### 1. 能力发现
- `BasketBallAgent`首先通过GET请求`WeatherAgent`的`/.well-known/agent.json`，获取其能力描述和API端点。

### 2. 任务提交
- `BasketBallAgent`根据agent.json中的`task_submit`端点，POST标准任务请求（含task_id和params）到WeatherAgent。

### 3. 结果获取与决策
- `WeatherAgent`返回天气数据，`BasketBallAgent`解析后根据天气情况自动决策。

### 4. 认证机制
- agent.json中声明了API Key认证，`BasketBallAgent`在请求头中携带Authorization字段（示例未做实际校验）。

### 5. 交互流程图
```
BasketBallAgent                WeatherAgent
     |   GET /.well-known/agent.json   |
     |------------------------------->|
     |                                |
     |   POST /api/tasks/weather      |
     |------------------------------->|
     |                                |
     |   返回天气结果                 |
     |<-------------------------------|
     |                                |
     |   业务决策输出                 |
```

---

## 五、使用示例

1. 启动WeatherAgent服务（监听8000端口）。
2. 运行BasketBallAgent.py，调用`schedule_meeting("2025-05-08")`。
3. 控制台输出篮球安排结果：
```
篮球安排结果: {'status': 'cancelled', 'reason': '恶劣天气'}
```

---

## 六、总结与扩展

- 本示例展示了A2A智能体标准的基本用法，包括能力发现、任务提交、结果获取、认证等。
- 可扩展为多智能体协作、异步任务、SSE订阅等更复杂场景。
- 适合用作多智能体系统、智能体编排、自动化决策等场景的参考模板。 