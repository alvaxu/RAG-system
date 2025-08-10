# RAG-System V2.0.0 架构设计文档

## 🎯 **设计理念**

### **核心原则**

1. **模块化设计**：不同类型内容有独立的处理引擎
2. **集中配置化**：统一的配置管理中心
3. **插件化架构**：支持动态加载不同功能模块
4. **类型分离**：图片、文本、表格分别处理
5. **向后兼容**：不影响现有向量数据库和文本查询

## 🏗️ **系统架构**

### **整体架构图**

```
┌─────────────────────────────────────────────────────────────┐
│                    V2.0.0 核心系统                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  图片引擎   │  │  文本引擎   │  │  表格引擎   │        │
│  │ImageEngine  │  │TextEngine   │  │TableEngine  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  混合引擎   │  │  配置中心   │  │  路由分发   │        │
│  │HybridEngine │  │ConfigCenter │  │Router       │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  向量存储   │  │  记忆管理   │  │  用户界面   │        │
│  │VectorStore  │  │MemoryMgr    │  │WebUI        │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 **核心组件设计**

### **1. 图片处理引擎 (ImageEngine)**

```python
class ImageEngine:
    """
    专门处理图片相关查询的引擎
    """
    def __init__(self, config: ImageConfig):
        self.config = config
        self.image_retriever = ImageRetriever()
        self.image_processor = ImageProcessor()
        self.image_filter = ImageFilter()
  
    def search_images(self, query: str, filters: Dict = None) -> List[ImageResult]:
        """专门检索图片"""
        pass
  
    def process_image_query(self, query: str) -> ImageQueryResult:
        """处理图片查询"""
        pass
```

### **2. 文本处理引擎 (TextEngine)**

```python
class TextEngine:
    """
    专门处理文本相关查询的引擎
    """
    def __init__(self, config: TextConfig):
        self.config = config
        self.text_retriever = TextRetriever()
        self.text_processor = TextProcessor()
  
    def search_text(self, query: str, filters: Dict = None) -> List[TextResult]:
        """专门检索文本"""
        pass
```

### **3. 表格处理引擎 (TableEngine)**

```python
class TableEngine:
    """
    专门处理表格相关查询的引擎
    """
    def __init__(self, config: TableConfig):
        self.config = config
        self.table_retriever = TableRetriever()
        self.table_processor = TableProcessor()
  
    def search_tables(self, query: str, filters: Dict = None) -> List[TableResult]:
        """专门检索表格"""
        pass
```

### **4. 混合查询引擎 (HybridEngine)**

```python
class HybridEngine:
    """
    协调不同类型引擎的混合查询引擎
    """
    def __init__(self, config: HybridConfig):
        self.image_engine = ImageEngine(config.image_config)
        self.text_engine = TextEngine(config.text_config)
        self.table_engine = TableEngine(config.table_config)
  
    def process_query(self, query: str, query_type: str = 'auto') -> QueryResult:
        """智能处理查询，自动选择最合适的引擎"""
        pass
```

## ⚙️ **配置系统设计**

### **V2.0配置结构**

```json
{
  "version": "2.0.0",
  "system": {
    "mode": "production",
    "debug": false,
    "log_level": "INFO"
  },
  "engines": {
    "image": {
      "enabled": true,
      "retrieval_method": "hybrid",
      "similarity_threshold": 0.7,
      "max_results": 10
    },
    "text": {
      "enabled": true,
      "retrieval_method": "vector",
      "similarity_threshold": 0.6,
      "max_results": 15
    },
    "table": {
      "enabled": true,
      "retrieval_method": "structured",
      "similarity_threshold": 0.8,
      "max_results": 8
    }
  },
  "api": {
    "version": "v2",
    "endpoints": {
      "image": "/api/v2/image",
      "text": "/api/v2/text",
      "table": "/api/v2/table",
      "hybrid": "/api/v2/hybrid"
    }
  }
}
```

## 🚀 **实施计划**

### **第一阶段：核心引擎 (Week 1)**

1. 创建基础引擎框架
2. 实现图片引擎核心功能
3. 实现文本引擎核心功能
4. 实现表格引擎核心功能

### **第二阶段：混合引擎 (Week 2)**

1. 实现混合查询引擎
2. 添加智能路由功能
3. 实现结果合并和排序

### **第三阶段：API和界面 (Week 3)**

1. 创建V2.0 API接口
2. 重新设计Web界面
3. 实现查询类型选择器

### **第四阶段：测试和优化 (Week 4)**

1. 全面功能测试
2. 性能优化
3. 文档完善

## 🔄 **迁移策略**

### **向后兼容性**

1. **保持现有API**：V1.0的API继续工作
2. **渐进式迁移**：可以逐步切换到V2.0
3. **配置兼容**：V1.0配置可以转换为V2.0

### **数据兼容性**

1. **向量数据库**：完全兼容，无需重建
2. **文档结构**：保持现有格式
3. **索引系统**：可以继续使用

## 📊 **性能预期**

### **查询性能提升**

- 图片查询：**3-5倍** 速度提升
- 文本查询：**2-3倍** 速度提升
- 表格查询：**4-6倍** 速度提升

### **准确性提升**

- 图片检索准确率：**85% → 95%**
- 文本检索准确率：**80% → 90%**
- 表格检索准确率：**75% → 90%**

## 🎯 **成功指标**

1. **功能完整性**：所有V1.0功能在V2.0中正常工作
2. **性能提升**：查询速度显著提升
3. **用户体验**：界面更加直观，操作更简单
4. **可维护性**：代码结构更清晰，易于扩展
5. **稳定性**：系统运行更稳定，错误率降低


## 📊 **V2.0.0 系统完成状态检查**

### ✅ **已完成的功能**

1. **阶段1：V2.0配置中心** - `config/v2_config.py` ✅

   - 完整的配置类定义
   - V2ConfigManager 配置管理器
   - 支持JSON配置文件
2. **阶段2：V2.0 API路由** - `api/v2_routes.py` ✅

   - 专门的图片查询接口 `/api/v2/query/image`
   - 专门的文本查询接口 `/api/v2/query/text`
   - 专门的表格查询接口 `/api/v2/query/table`
   - 混合查询接口 `/api/v2/query/hybrid`
   - 智能查询接口 `/api/v2/query/smart`
   - 引擎状态和刷新接口
3. **阶段3：V2.0 Web界面** - `web_app/v2_index.html` ✅

   - 现代化的UI设计
   - 查询类型选择标签页
   - 专门的图片查询区域（方案2的实现）
   - 响应式设计
   - 完整的JavaScript功能

### �� **核心特性实现**

- **方案1+2组合**：专门的图片检索方法 + 用户界面明确标识 ✅
- **图表文查询分离**：三种独立的查询类型 ✅
- **智能路由**：自动判断查询类型 ✅
- **混合查询**：并行处理多种内容类型 ✅
- **向后兼容**：不影响现有系统 ✅

### �� **下一步工作建议**

现在V2.0.0的基础架构已经完成，建议进行以下步骤：

1. **集成测试**：将新的API路由集成到主Flask应用
2. **引擎初始化**：确保所有引擎能正确加载和配置
3. **端到端测试**：测试完整的查询流程
4. **性能优化**：根据实际使用情况调整参数

您希望我继续哪个部分的工作？比如：

- 集成V2.0 API到主应用？
- 创建测试脚本来验证系统？
- 还是有其他特定的需求？
