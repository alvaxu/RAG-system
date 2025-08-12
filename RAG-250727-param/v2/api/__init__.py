'''
程序说明：

## 1. V2.0.0 API服务包初始化文件
## 2. 导出API路由和Flask应用
## 3. 与老版本API完全分离
'''

from .v2_routes import v2_api_bp

__all__ = ['v2_api_bp']
