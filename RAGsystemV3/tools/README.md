# RAG系统运维工具

本目录包含RAG系统的运维工具，用于部署、监控和管理系统。

## 目录结构

```
tools/
├── deploy/                    # 部署工具
│   └── deploy_memory_module.py    # 记忆模块部署脚本
├── monitor/                   # 监控工具
│   └── monitor_memory_module.py  # 记忆模块监控脚本
└── README.md                  # 本说明文件
```

## 工具说明

### 部署工具 (deploy/)

#### deploy_memory_module.py
- **用途**：自动化部署RAG系统记忆模块到生产环境
- **功能**：
  - 检查部署前置条件
  - 备份当前系统
  - 验证记忆模块完整性
  - 运行测试验证
  - 更新项目依赖
  - 部署记忆模块
  - 重启相关服务
  - 验证部署结果
  - 支持回滚操作

- **使用方法**：
  ```bash
  python tools/deploy/deploy_memory_module.py
  ```

### 监控工具 (monitor/)

#### monitor_memory_module.py
- **用途**：监控记忆模块的运行状态和性能指标
- **功能**：
  - API健康状态检查
  - 记忆模块API状态检查
  - 数据库健康状态检查
  - 系统资源使用情况监控
  - 告警条件检查
  - 生成监控报告

- **使用方法**：
  ```bash
  # 单次检查（默认，推荐日常使用）
  python tools/monitor/monitor_memory_module.py
  
  # 单次检查（显式指定）
  python tools/monitor/monitor_memory_module.py check
  
  # 生成JSON报告
  python tools/monitor/monitor_memory_module.py report
  
  # 持续监控（生产环境）
  python tools/monitor/monitor_memory_module.py monitor
  ```

## 注意事项

1. **权限要求**：这些工具需要适当的系统权限来执行部署和监控操作
2. **依赖环境**：确保RAG系统环境已正确配置
3. **配置文件**：监控工具会自动创建配置文件，可根据需要调整
4. **日志记录**：所有操作都会记录到相应的日志文件中

## 维护说明

- 定期检查工具的功能是否正常
- 根据系统变化更新工具配置
- 保持工具与系统版本的同步
