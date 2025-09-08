# RAG系统V3 API文档

## 📋 概述

RAG系统V3提供RESTful API接口，支持多模态内容检索、智能问答、配置管理等功能。本文档详细描述了所有可用的API端点、请求参数、响应格式和使用示例。

## 🔗 基础信息

- **Base URL**: `http://localhost:8000/api/v3/rag`
- **Content-Type**: `application/json`
- **认证方式**: API Key (可选)
- **响应格式**: JSON

## 📚 API端点

### 1. 系统状态

#### 获取系统状态
```http
GET /status
```

#### 健康检查
```http
GET /health
```

**响应示例**:
```json
{
  "status": "ready",
  "version": "3.0.0",
  "uptime": 3600,
  "services": {
    "retrieval_engine": "ready",
    "llm_caller": "ready",
    "reranking_service": "ready",
    "config_manager": "ready"
  },
  "metrics": {
    "total_queries": 1250,
    "average_response_time": 1.2,
    "cache_hit_rate": 0.85
  }
}
```

### 2. 查询处理

#### 智能问答
```http
POST /query
```

#### 批量查询
```http
POST /batch-query
```

#### 流式查询
```http
POST /stream-query
```

**请求参数**:
```json
{
  "query": "什么是人工智能？",
  "max_results": 10,
  "similarity_threshold": 0.3,
  "include_sources": true,
  "response_format": "detailed"
}
```

**响应示例**:
```json
{
  "success": true,
  "query": "什么是人工智能？",
  "answer": "人工智能（AI）是计算机科学的一个分支...",
  "sources": [
    {
      "type": "text",
      "content": "人工智能是计算机科学的一个分支...",
      "similarity": 0.95,
      "metadata": {
        "source": "AI基础教程.pdf",
        "page": 1
      }
    }
  ],
  "processing_time": 1.2,
  "token_usage": {
    "prompt_tokens": 150,
    "completion_tokens": 200,
    "total_tokens": 350
  }
}
```

#### 批量查询
```http
POST /query/batch
```

**请求参数**:
```json
{
  "queries": [
    "什么是机器学习？",
    "深度学习有哪些应用？",
    "自然语言处理技术"
  ],
  "max_results": 5,
  "parallel": true
}
```

**响应示例**:
```json
{
  "success": true,
  "results": [
    {
      "query": "什么是机器学习？",
      "answer": "机器学习是人工智能的一个子领域...",
      "processing_time": 1.1
    },
    {
      "query": "深度学习有哪些应用？",
      "answer": "深度学习在图像识别、语音识别等领域...",
      "processing_time": 1.3
    }
  ],
  "total_processing_time": 2.4
}
```

### 3. 多模态检索

#### 内容搜索
```http
POST /search
```

#### 文本检索
```http
POST /retrieve/text
```

**请求参数**:
```json
{
  "query": "机器学习算法",
  "max_results": 10,
  "similarity_threshold": 0.3,
  "filters": {
    "source_type": "pdf",
    "date_range": {
      "start": "2023-01-01",
      "end": "2024-12-31"
    }
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "query": "机器学习算法",
  "results": [
    {
      "content": "机器学习算法包括监督学习、无监督学习...",
      "similarity": 0.92,
      "metadata": {
        "source": "ML教程.pdf",
        "page": 15,
        "section": "算法概述"
      }
    }
  ],
  "total_results": 1,
  "processing_time": 0.8
}
```

#### 图像检索
```http
POST /retrieve/image
```

**请求参数**:
```json
{
  "query": "美丽的风景",
  "max_results": 5,
  "similarity_threshold": 0.2,
  "visual_features": {
    "colors": ["green", "blue"],
    "objects": ["mountain", "lake"],
    "style": "natural"
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "query": "美丽的风景",
  "results": [
    {
      "image_path": "/images/landscape_001.jpg",
      "similarity": 0.85,
      "visual_features": {
        "dominant_colors": ["green", "blue"],
        "detected_objects": ["mountain", "lake", "sky"],
        "style_attributes": ["natural", "serene"]
      },
      "metadata": {
        "source": "风景摄影集",
        "photographer": "张三",
        "location": "九寨沟"
      }
    }
  ],
  "total_results": 1,
  "processing_time": 1.5
}
```

#### 表格检索
```http
POST /retrieve/table
```

**请求参数**:
```json
{
  "query": "财务数据表格",
  "max_results": 5,
  "table_structure": {
    "min_columns": 3,
    "max_columns": 10,
    "required_headers": ["收入", "支出", "利润"]
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "query": "财务数据表格",
  "results": [
    {
      "table_data": {
        "headers": ["月份", "收入", "支出", "利润"],
        "rows": [
          ["1月", "100000", "80000", "20000"],
          ["2月", "120000", "90000", "30000"]
        ]
      },
      "similarity": 0.88,
      "structure_info": {
        "row_count": 2,
        "column_count": 4,
        "data_types": ["string", "number", "number", "number"]
      },
      "metadata": {
        "source": "财务报告.xlsx",
        "sheet": "月度数据"
      }
    }
  ],
  "total_results": 1,
  "processing_time": 0.9
}
```

#### 混合检索
```http
POST /retrieve/hybrid
```

**请求参数**:
```json
{
  "query": "AI医疗应用",
  "max_results": 15,
  "content_types": ["text", "image", "table"],
  "weights": {
    "text": 0.5,
    "image": 0.3,
    "table": 0.2
  },
  "diversity_strategy": "balanced"
}
```

**响应示例**:
```json
{
  "success": true,
  "query": "AI医疗应用",
  "results": [
    {
      "type": "text",
      "content": "AI在医疗诊断中的应用包括影像分析...",
      "similarity": 0.95,
      "metadata": {
        "source": "AI医疗白皮书.pdf"
      }
    },
    {
      "type": "image",
      "image_path": "/images/medical_ai_001.jpg",
      "similarity": 0.87,
      "metadata": {
        "source": "医疗AI案例集"
      }
    }
  ],
  "content_type_distribution": {
    "text": 8,
    "image": 4,
    "table": 3
  },
  "total_results": 15,
  "processing_time": 2.1
}
```

### 4. 重排序服务

#### 文档重排序
```http
POST /rerank
```

#### 答案溯源
```http
POST /attribution
```

**请求参数**:
```json
{
  "query": "机器学习算法",
  "candidates": [
    {
      "id": "doc_001",
      "content": "监督学习算法包括线性回归...",
      "score": 0.8
    },
    {
      "id": "doc_002", 
      "content": "无监督学习算法包括聚类...",
      "score": 0.7
    }
  ],
  "rerank_models": ["dashscope", "rule_based"],
  "max_results": 10
}
```

**响应示例**:
```json
{
  "success": true,
  "query": "机器学习算法",
  "reranked_results": [
    {
      "id": "doc_001",
      "content": "监督学习算法包括线性回归...",
      "original_score": 0.8,
      "rerank_score": 0.92,
      "confidence": 0.85
    },
    {
      "id": "doc_002",
      "content": "无监督学习算法包括聚类...",
      "original_score": 0.7,
      "rerank_score": 0.78,
      "confidence": 0.82
    }
  ],
  "processing_time": 0.5,
  "model_used": "dashscope"
}
```

### 5. 配置管理

#### 获取配置
```http
GET /config
```

#### 向量数据库状态
```http
GET /vector-db/status
```

#### 系统统计
```http
GET /stats
```

**响应示例**:
```json
{
  "success": true,
  "config": {
    "rag_system": {
      "query_processing": {
        "max_results": 10,
        "similarity_threshold": 0.3
      },
      "retrieval": {
        "batch_size": 32,
        "cache_enabled": true
      },
      "llm_caller": {
        "model_name": "qwen-turbo",
        "max_tokens": 2000
      }
    }
  },
  "version": "3.0.0",
  "last_modified": "2025-09-01T10:00:00Z"
}
```

#### 更新配置
```http
PUT /config
```

**请求参数**:
```json
{
  "config": {
    "rag_system": {
      "query_processing": {
        "max_results": 15,
        "similarity_threshold": 0.25
      }
    }
  },
  "description": "调整查询参数以提升召回率"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "配置更新成功",
  "version": "3.0.1",
  "backup_created": "backup_20250901_100000.json"
}
```

#### 导出配置
```http
GET /config/export
```

**查询参数**:
- `format`: 导出格式 (json/yaml/python)
- `include_backup`: 是否包含备份 (true/false)

**响应示例**:
```json
{
  "success": true,
  "export_path": "/exports/config_20250901.json",
  "format": "json",
  "size": 2048,
  "download_url": "/downloads/config_20250901.json"
}
```

#### 导入配置
```http
POST /config/import
```

**请求参数**:
```json
{
  "config_data": {
    "rag_system": {
      "query_processing": {
        "max_results": 20
      }
    }
  },
  "format": "json",
  "validate": true,
  "backup_current": true
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "配置导入成功",
  "validation_passed": true,
  "backup_created": "backup_pre_import_20250901.json",
  "changes_applied": [
    "query_processing.max_results: 10 -> 20"
  ]
}
```

#### 配置备份
```http
POST /config/backup
```

**请求参数**:
```json
{
  "backup_name": "monthly_backup",
  "description": "月度配置备份",
  "include_versions": true
}
```

**响应示例**:
```json
{
  "success": true,
  "backup_path": "/backups/monthly_backup_20250901.json",
  "backup_id": "backup_20250901_100000",
  "size": 4096
}
```

#### 恢复配置
```http
POST /config/restore
```

**请求参数**:
```json
{
  "backup_id": "backup_20250901_100000",
  "confirm": true
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "配置恢复成功",
  "restored_from": "backup_20250901_100000",
  "current_backup": "backup_pre_restore_20250901.json"
}
```

### 6. 性能监控

#### 获取性能指标
```http
GET /metrics
```

#### 获取缓存状态
```http
GET /cache/status
```

#### 清理缓存
```http
POST /cache/clear
```

**查询参数**:
- `time_range`: 时间范围 (hour/day/week/month)
- `include_details`: 是否包含详细信息 (true/false)

**响应示例**:
```json
{
  "success": true,
  "time_range": "day",
  "metrics": {
    "total_queries": 1250,
    "average_response_time": 1.2,
    "cache_hit_rate": 0.85,
    "error_rate": 0.02,
    "throughput": 52.1,
    "active_connections": 15
  },
  "detailed_metrics": {
    "retrieval_engine": {
      "text_queries": 800,
      "image_queries": 300,
      "table_queries": 150,
      "average_similarity": 0.78
    },
    "llm_caller": {
      "total_calls": 1250,
      "average_tokens": 350,
      "success_rate": 0.98
    },
    "reranking_service": {
      "total_reranks": 1000,
      "average_improvement": 0.15
    }
  }
}
```

#### 获取缓存状态
```http
GET /cache/status
```

**响应示例**:
```json
{
  "success": true,
  "cache_status": {
    "enabled": true,
    "total_entries": 1500,
    "hit_rate": 0.85,
    "miss_rate": 0.15,
    "memory_usage": "256MB",
    "ttl": 3600
  },
  "cache_stats": {
    "query_cache": {
      "entries": 800,
      "hit_rate": 0.90
    },
    "model_cache": {
      "entries": 500,
      "hit_rate": 0.75
    },
    "config_cache": {
      "entries": 200,
      "hit_rate": 0.95
    }
  }
}
```

#### 清理缓存
```http
POST /cache/clear
```

**请求参数**:
```json
{
  "cache_types": ["query", "model", "config"],
  "confirm": true
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "缓存清理完成",
  "cleared_entries": 1500,
  "freed_memory": "256MB"
}
```

### 7. 系统管理

#### 健康检查
```http
GET /health
```

**响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2025-09-01T10:00:00Z",
  "services": {
    "database": "healthy",
    "ai_models": "healthy",
    "cache": "healthy",
    "storage": "healthy"
  },
  "version": "3.0.0"
}
```



## 🔒 错误处理

### 错误响应格式
```json
{
  "success": false,
  "error": {
    "code": "INVALID_QUERY",
    "message": "查询参数无效",
    "details": "查询字符串不能为空",
    "timestamp": "2025-09-01T10:00:00Z"
  }
}
```

### 常见错误代码

| 错误代码 | HTTP状态码 | 描述 |
|---------|-----------|------|
| `INVALID_QUERY` | 400 | 查询参数无效 |
| `QUERY_TOO_LONG` | 400 | 查询字符串过长 |
| `RATE_LIMIT_EXCEEDED` | 429 | 请求频率超限 |
| `MODEL_UNAVAILABLE` | 503 | AI模型不可用 |
| `DATABASE_ERROR` | 500 | 数据库错误 |
| `CONFIG_ERROR` | 500 | 配置错误 |
| `AUTHENTICATION_FAILED` | 401 | 认证失败 |
| `PERMISSION_DENIED` | 403 | 权限不足 |

## 📊 使用示例

### Python客户端示例
```python
import requests
import json

class RAGClient:
    def __init__(self, base_url="http://localhost:8000/api/v3/rag"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def query(self, query_text, max_results=10):
        """发送查询请求"""
        url = f"{self.base_url}/query"
        data = {
            "query": query_text,
            "max_results": max_results,
            "include_sources": True
        }
        response = self.session.post(url, json=data)
        return response.json()
    
    def retrieve_text(self, query_text, max_results=10):
        """文本检索"""
        url = f"{self.base_url}/retrieve/text"
        data = {
            "query": query_text,
            "max_results": max_results
        }
        response = self.session.post(url, json=data)
        return response.json()
    
    def get_status(self):
        """获取系统状态"""
        url = f"{self.base_url}/status"
        response = self.session.get(url)
        return response.json()

# 使用示例
client = RAGClient()
result = client.query("什么是人工智能？")
print(json.dumps(result, indent=2, ensure_ascii=False))
```

### JavaScript客户端示例
```javascript
class RAGClient {
    constructor(baseUrl = 'http://localhost:8000/api/v3/rag') {
        this.baseUrl = baseUrl;
    }
    
    async query(queryText, maxResults = 10) {
        const response = await fetch(`${this.baseUrl}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: queryText,
                max_results: maxResults,
                include_sources: true
            })
        });
        return await response.json();
    }
    
    async retrieveText(queryText, maxResults = 10) {
        const response = await fetch(`${this.baseUrl}/retrieve/text`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: queryText,
                max_results: maxResults
            })
        });
        return await response.json();
    }
    
    async getStatus() {
        const response = await fetch(`${this.baseUrl}/status`);
        return await response.json();
    }
}

// 使用示例
const client = new RAGClient();
client.query('什么是人工智能？')
    .then(result => console.log(result))
    .catch(error => console.error(error));
```

## 🔧 开发工具

### API测试工具
推荐使用以下工具进行API测试：
- **Postman**: 图形化API测试工具
- **curl**: 命令行HTTP客户端
- **HTTPie**: 用户友好的命令行HTTP客户端

### 示例curl命令
```bash
# 获取系统状态
curl -X GET "http://localhost:8000/api/v3/rag/status"

# 发送查询
curl -X POST "http://localhost:8000/api/v3/rag/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "什么是人工智能？", "max_results": 10}'

# 内容搜索
curl -X POST "http://localhost:8000/api/v3/rag/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "机器学习算法", "max_results": 5}'

# 健康检查
curl -X GET "http://localhost:8000/api/v3/rag/health"
```

## 📝 更新日志

### V3.0.0 (2025-09-01)
- ✅ 核心架构重构完成
- ✅ 多模态检索功能实现
- ✅ 配置管理系统集成
- ✅ 前端界面开发完成
- ✅ 系统集成测试通过
- ✅ 性能优化完成

---

**API版本**: V3.0.0  
**文档版本**: 1.0.0  
**最后更新**: 2025-09-01
