# V2 RAG系统API文档

## API概述

V2 RAG系统提供RESTful API接口，支持智能问答、系统状态查询、配置管理等功能。所有API都遵循统一的响应格式和错误处理机制。

## 基础信息

- **基础URL**: `http://localhost:5000`
- **API版本**: v2
- **数据格式**: JSON
- **认证方式**: 无需认证（开发环境）

## 通用响应格式

### 成功响应
```json
{
    "success": true,
    "data": {...},
    "message": "操作成功",
    "timestamp": "2024-01-01T00:00:00Z"
}
```

### 错误响应
```json
{
    "success": false,
    "error": "错误描述",
    "code": "ERROR_CODE",
    "timestamp": "2024-01-01T00:00:00Z"
}
```

## API端点详细说明

### 1. 系统状态查询

#### 获取系统整体状态
- **端点**: `GET /api/v2/status`
- **描述**: 获取系统整体运行状态和优化管道状态
- **参数**: 无
- **响应示例**:
```json
{
    "success": true,
    "data": {
        "system_status": "running",
        "optimization_pipeline_enabled": true,
        "engines": {
            "reranking_engine": "ready",
            "llm_engine": "ready",
            "smart_filter_engine": "ready",
            "source_filter_engine": "ready"
        },
        "timestamp": "2024-01-01T00:00:00Z"
    }
}
```

### 2. 查询处理

#### 优化查询处理
- **端点**: `POST /api/v2/query/optimized`
- **描述**: 使用完整优化管道处理用户查询
- **请求参数**:
```json
{
    "question": "用户问题",
    "enable_reranking": true,
    "enable_smart_filter": true,
    "enable_llm_generation": true,
    "enable_source_filter": true,
    "max_results": 10
}
```
- **响应示例**:
```json
{
    "success": true,
    "data": {
        "answer": "生成的答案",
        "sources": [...],
        "optimization_details": {
            "reranking_time": 0.5,
            "filtering_time": 0.3,
            "llm_generation_time": 2.1,
            "source_filtering_time": 0.2,
            "total_time": 3.1
        },
        "confidence": 0.85
    }
}
```

#### 标准查询处理
- **端点**: `POST /api/v2/qa/ask`
- **描述**: 使用标准流程处理查询（不经过优化管道）
- **请求参数**:
```json
{
    "question": "用户问题",
    "max_results": 10
}
```

### 3. 引擎管理

#### 获取引擎状态
- **端点**: `GET /api/v2/engines/status`
- **描述**: 获取所有引擎的详细状态信息
- **响应示例**:
```json
{
    "success": true,
    "data": {
        "hybrid_engine": {
            "status": "ready",
            "enabled": true,
            "sub_engines": {
                "text_engine": "ready",
                "image_engine": "ready",
                "table_engine": "ready"
            },
            "optimization_pipeline": {
                "enabled": true,
                "stages": ["reranking", "smart_filter", "llm_generation", "source_filter"]
            }
        },
        "optimization_engines": {
            "reranking_engine": {
                "status": "ready",
                "model": "BGE-reranker-v2-m3",
                "enabled": true
            },
            "llm_engine": {
                "status": "ready",
                "model": "Qwen-Turbo",
                "enabled": true
            }
        }
    }
}
```

#### 获取优化引擎状态
- **端点**: `GET /api/v2/engines/optimization`
- **描述**: 获取优化引擎的详细状态
- **响应示例**:
```json
{
    "success": true,
    "data": {
        "reranking_engine": {
            "status": "ready",
            "config": {
                "model": "BGE-reranker-v2-m3",
                "top_k": 10,
                "threshold": 0.5
            }
        },
        "llm_engine": {
            "status": "ready",
            "config": {
                "model": "Qwen-Turbo",
                "max_tokens": 2048,
                "temperature": 0.7
            }
        }
    }
}
```

#### 更新优化引擎配置
- **端点**: `POST /api/v2/engines/optimization/config`
- **描述**: 动态更新优化引擎的配置参数
- **请求参数**:
```json
{
    "engine_type": "reranking_engine",
    "config": {
        "top_k": 15,
        "threshold": 0.6
    }
}
```

### 4. 性能测试

#### 查询性能基准测试
- **端点**: `POST /api/v2/query/benchmark`
- **描述**: 测试不同查询类型的性能表现
- **请求参数**:
```json
{
    "test_queries": [
        "测试问题1",
        "测试问题2"
    ],
    "query_types": ["optimized", "standard", "hybrid"],
    "iterations": 3
}
```
- **响应示例**:
```json
{
    "success": true,
    "data": {
        "benchmark_results": {
            "optimized": {
                "avg_response_time": 3.2,
                "avg_accuracy": 0.88,
                "total_queries": 6
            },
            "standard": {
                "avg_response_time": 1.8,
                "avg_accuracy": 0.75,
                "total_queries": 6
            }
        }
    }
}
```

### 5. 记忆管理

#### 获取对话记忆
- **端点**: `GET /api/v2/memory/history`
- **描述**: 获取用户的对话历史记录
- **参数**: 
  - `user_id`: 用户ID（可选）
  - `limit`: 返回记录数量限制（可选）
- **响应示例**:
```json
{
    "success": true,
    "data": {
        "conversations": [
            {
                "id": "conv_001",
                "question": "问题1",
                "answer": "答案1",
                "timestamp": "2024-01-01T00:00:00Z",
                "relevance_score": 0.85
            }
        ]
    }
}
```

#### 清除对话记忆
- **端点**: `DELETE /api/v2/memory/clear`
- **描述**: 清除指定用户的对话记忆
- **参数**: `user_id`（可选，不提供则清除所有记忆）

## 错误代码说明

| 错误代码 | 描述 | 解决方案 |
|---------|------|----------|
| `ENGINE_NOT_READY` | 引擎未就绪 | 检查引擎配置和API密钥 |
| `INVALID_PARAMETER` | 参数无效 | 检查请求参数格式 |
| `API_KEY_ERROR` | API密钥错误 | 检查配置文件中的API密钥 |
| `ENGINE_ERROR` | 引擎执行错误 | 查看系统日志获取详细信息 |
| `TIMEOUT_ERROR` | 请求超时 | 检查网络连接和系统负载 |

## 使用示例

### Python客户端示例

```python
import requests
import json

# 基础配置
BASE_URL = "http://localhost:5000"
API_VERSION = "v2"

# 发送优化查询
def send_optimized_query(question):
    url = f"{BASE_URL}/api/{API_VERSION}/query/optimized"
    payload = {
        "question": question,
        "enable_reranking": True,
        "enable_smart_filter": True,
        "enable_llm_generation": True,
        "enable_source_filter": True,
        "max_results": 10
    }
    
    response = requests.post(url, json=payload)
    return response.json()

# 获取系统状态
def get_system_status():
    url = f"{BASE_URL}/api/{API_VERSION}/status"
    response = requests.get(url)
    return response.json()

# 使用示例
if __name__ == "__main__":
    # 检查系统状态
    status = get_system_status()
    print("系统状态:", status)
    
    # 发送查询
    result = send_optimized_query("什么是RAG系统？")
    print("查询结果:", result)
```

### JavaScript客户端示例

```javascript
// 基础配置
const BASE_URL = "http://localhost:5000";
const API_VERSION = "v2";

// 发送优化查询
async function sendOptimizedQuery(question) {
    const url = `${BASE_URL}/api/${API_VERSION}/query/optimized`;
    const payload = {
        question: question,
        enable_reranking: true,
        enable_smart_filter: true,
        enable_llm_generation: true,
        enable_source_filter: true,
        max_results: 10
    };
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        return await response.json();
    } catch (error) {
        console.error('查询失败:', error);
        throw error;
    }
}

// 获取系统状态
async function getSystemStatus() {
    const url = `${BASE_URL}/api/${API_VERSION}/status`;
    try {
        const response = await fetch(url);
        return await response.json();
    } catch (error) {
        console.error('获取状态失败:', error);
        throw error;
    }
}
```

## 性能优化建议

1. **批量查询**: 对于多个相关问题，考虑使用批量查询接口
2. **缓存策略**: 客户端可以实现结果缓存，避免重复查询
3. **异步处理**: 对于长时间运行的查询，考虑使用异步处理模式
4. **连接池**: 在高并发场景下，使用HTTP连接池提高性能

## 限制和注意事项

1. **请求频率**: 建议控制请求频率，避免对系统造成过大压力
2. **超时设置**: 根据查询复杂度合理设置客户端超时时间
3. **错误重试**: 实现适当的错误重试机制，但避免无限重试
4. **日志记录**: 记录API调用日志，便于问题排查和性能分析
