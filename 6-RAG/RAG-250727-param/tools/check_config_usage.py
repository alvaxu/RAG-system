#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import Settings
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_config_usage():
    """检查各个模块是否正确使用了config.json中的参数"""
    
    print("=" * 60)
    print("配置使用情况检查")
    print("=" * 60)
    
    # 1. 加载配置文件
    try:
        settings = Settings.load_from_file("config.json")
        print("✅ 成功加载config.json")
    except Exception as e:
        print(f"❌ 加载config.json失败: {e}")
        return
    
    # 2. 检查config.json中的关键参数
    print("\n📋 config.json中的关键参数:")
    config_params = {
        "API配置": {
            "dashscope_api_key": settings.dashscope_api_key[:10] + "..." if settings.dashscope_api_key else "未设置",
            "mineru_api_key": settings.mineru_api_key[:10] + "..." if settings.mineru_api_key else "未设置"
        },
        "路径配置": {
            "web_app_dir": settings.web_app_dir,
            "central_images_dir": settings.central_images_dir,
            "vector_db_dir": settings.vector_db_dir,
            "memory_db_dir": settings.memory_db_dir
        },
        "处理配置": {
            "chunk_size": settings.chunk_size,
            "chunk_overlap": settings.chunk_overlap,
            "enable_smart_filtering": settings.enable_smart_filtering,
            "semantic_similarity_threshold": settings.semantic_similarity_threshold,
            "content_relevance_threshold": settings.content_relevance_threshold
        },
        "向量存储配置": {
            "vector_dimension": settings.vector_dimension,
            "similarity_top_k": settings.similarity_top_k,
            "similarity_threshold": settings.similarity_threshold
        },
        "问答系统配置": {
            "model_name": settings.model_name,
            "temperature": settings.temperature,
            "max_tokens": settings.max_tokens
        },
        "记忆配置": {
            "memory_enabled": settings.memory_enabled,
            "memory_max_size": settings.memory_max_size
        }
    }
    
    for category, params in config_params.items():
        print(f"\n{category}:")
        for key, value in params.items():
            print(f"  {key}: {value}")
    
    # 3. 检查路径是否存在
    print("\n📁 路径存在性检查:")
    paths_to_check = [
        ("web_app_dir", settings.web_app_dir),
        ("central_images_dir", settings.central_images_dir),
        ("vector_db_dir", settings.vector_db_dir),
        ("memory_db_dir", settings.memory_db_dir),
        ("add_pdf_dir", settings.add_pdf_dir),
        ("add_md_dir", settings.add_md_dir)
    ]
    
    for name, path in paths_to_check:
        exists = os.path.exists(path)
        status = "✅" if exists else "❌"
        print(f"  {status} {name}: {path} ({'存在' if exists else '不存在'})")
    
    # 4. 检查API模块的配置使用
    print("\n🔧 API模块配置使用检查:")
    try:
        from api.app import create_app
        app = create_app(settings)
        print("  ✅ api/app.py 正确使用了Settings配置")
        
        # 检查app配置中的关键参数
        app_settings = app.config.get('SETTINGS')
        if app_settings:
            print(f"  ✅ web_app_dir: {app_settings.web_app_dir}")
            print(f"  ✅ central_images_dir: {app_settings.central_images_dir}")
            print(f"  ✅ memory_db_dir: {app_settings.memory_db_dir}")
        else:
            print("  ❌ app配置中没有SETTINGS")
            
    except Exception as e:
        print(f"  ❌ api/app.py 配置使用检查失败: {e}")
    
    # 5. 检查Core模块的配置使用
    print("\n🧠 Core模块配置使用检查:")
    try:
        from core.enhanced_qa_system import EnhancedQASystem
        from core.memory_manager import MemoryManager
        
        # 检查MemoryManager
        memory_manager = MemoryManager(settings.memory_db_dir)
        print("  ✅ core/memory_manager.py 正确使用了memory_db_dir配置")
        
        # 检查EnhancedQASystem的配置参数
        config_dict = settings.to_dict()
        qa_config = config_dict.get('qa_system', {})
        processing_config = config_dict.get('processing', {})
        vector_config = config_dict.get('vector_store', {})
        
        print(f"  ✅ qa_system配置: {qa_config.get('model_name', 'N/A')}")
        print(f"  ✅ processing配置: chunk_size={processing_config.get('chunk_size', 'N/A')}")
        print(f"  ✅ vector_store配置: similarity_top_k={vector_config.get('similarity_top_k', 'N/A')}")
        
    except Exception as e:
        print(f"  ❌ Core模块配置使用检查失败: {e}")
    
    # 6. 检查智能过滤引擎的阈值设置
    print("\n🔍 智能过滤引擎阈值检查:")
    try:
        from core.smart_filter_engine import SmartFilterEngine
        
        processing_config = {
            'enable_smart_filtering': settings.enable_smart_filtering,
            'semantic_similarity_threshold': settings.semantic_similarity_threshold,
            'content_relevance_threshold': settings.content_relevance_threshold,
            'max_filtered_results': settings.max_filtered_results
        }
        
        smart_filter = SmartFilterEngine(processing_config)
        print(f"  ✅ 智能过滤引擎初始化成功")
        print(f"  ✅ semantic_similarity_threshold: {smart_filter.semantic_similarity_threshold}")
        print(f"  ✅ content_relevance_threshold: {smart_filter.content_relevance_threshold}")
        print(f"  ✅ max_filtered_results: {smart_filter.max_filtered_results}")
        
    except Exception as e:
        print(f"  ❌ 智能过滤引擎检查失败: {e}")
    
    # 7. 检查Web应用前端
    print("\n🌐 Web应用前端检查:")
    web_app_dir = settings.web_app_dir
    index_html_path = os.path.join(web_app_dir, "index.html")
    
    if os.path.exists(index_html_path):
        print(f"  ✅ index.html存在: {index_html_path}")
        
        # 检查前端是否使用了正确的API端点
        try:
            with open(index_html_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if '/api/qa/ask' in content:
                    print("  ✅ 前端使用了正确的问答API端点")
                if '/api/memory/' in content:
                    print("  ✅ 前端使用了正确的记忆管理API端点")
                if '/api/system/' in content:
                    print("  ✅ 前端使用了正确的系统状态API端点")
        except Exception as e:
            print(f"  ❌ 前端文件读取失败: {e}")
    else:
        print(f"  ❌ index.html不存在: {index_html_path}")
    
    print("\n" + "=" * 60)
    print("配置使用情况检查完成")
    print("=" * 60)

if __name__ == "__main__":
    check_config_usage() 