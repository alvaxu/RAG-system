"""
RAG-System V3 项目安装配置文件

程序说明：
## 1. 定义项目为Python包，支持开发环境安装
## 2. 配置项目结构，确保db_system和rag_system都能正确导入
## 3. 不强制要求所有依赖包，避免安装失败
"""

from setuptools import setup, find_packages

setup(
    name="rag-system-v3",
    version="3.0.0",
    description="RAG-System V3 - 智能检索增强生成系统",
    author="RAG-System Team",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    # 暂时不指定install_requires，避免依赖冲突
    # install_requires=[],
)
