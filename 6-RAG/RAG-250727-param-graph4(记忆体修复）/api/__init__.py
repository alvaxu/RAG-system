'''
程序说明：
## 1. API接口模块的统一入口
## 2. 提供Web API接口
## 3. 整合问答系统和记忆管理
## 4. 提供RESTful API服务
'''

from .app import create_app
from .routes import api_bp

__all__ = [
    'create_app',
    'api_bp'
] 