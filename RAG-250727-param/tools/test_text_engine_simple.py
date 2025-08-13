#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
简单文本引擎测试程序 - 直接测试文本引擎功能

## 1. 功能特点
- 直接初始化文本引擎
- 测试文本查询功能
- 分析查询结果和文档结构

## 2. 使用方法
- 直接运行：python test_text_engine_simple.py
- 会测试文本查询功能
- 显示查询结果和文档结构
"""

import sys
import os
import json
import time
from typing import Dict, Any, List

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_text_engine_direct():
    """
    直接测试文本引擎
    """
    print("🔍 开始直接测试文本引擎...")
    
    try:
        # 导入必要的模块
        from v2.config.v2_config import V2ConfigManager
        from v2.core.text_engine import TextEngine
        from document_processing.vector_generator import VectorGenerator
        
        # 初始化配置
        config_manager = V2ConfigManager()
        v2_config = config_manager.config
        
        print(f"📋 文本引擎配置: {v2_config.text_engine}")
        
        # 检查向量数据库路径
        vector_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "central", "vector_db")
        if not os.path.exists(vector_db_path):
            print(f"❌ 向量数据库路径不存在: {vector_db_path}")
            return
        
        print(f"✅ 向量数据库路径存在: {vector_db_path}")
        
        # 加载向量存储
        print("🔄 正在加载向量存储...")
        
        # 创建配置字典
        config_dict = {
            'text_embedding_model': 'text-embedding-v1',
            'dashscope_api_key': ''  # 使用默认API密钥管理
        }
        
        vector_store = VectorGenerator(config_dict).load_vector_store(vector_db_path)
        print(f"✅ 向量存储加载成功: {type(vector_store)}")
        
        # 初始化文本引擎
        print("🔄 正在初始化文本引擎...")
        text_engine = TextEngine(
            config=v2_config.text_engine,
            vector_store=vector_store
        )
        print("✅ 文本引擎初始化成功")
        
        # 测试查询
        test_questions = [
            "中芯国际的主要业务是什么？",
            "中芯国际的产能利用率如何？"
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n{'='*80}")
            print(f"📝 测试问题 {i}: {question}")
            print(f"{'='*80}")
            
            try:
                # 执行文本查询
                print("🔄 正在执行文本查询...")
                result = text_engine.process_query(question, max_results=5)
                
                print(f"✅ 查询成功，找到 {len(result.results)} 个结果")
                
                # 分析每个文档的结构
                for j, doc in enumerate(result.results):
                    print(f"\n📄 文档 {j+1}:")
                    print(f"{'-'*60}")
                    
                    # 显示文档类型
                    print(f"   类型: {type(doc)}")
                    
                    # 如果是字典类型
                    if isinstance(doc, dict):
                        print(f"   字典键: {list(doc.keys())}")
                        
                        # 显示关键字段
                        for key in ['document_name', 'page_number', 'chunk_type', 'page_content']:
                            if key in doc:
                                value = doc[key]
                                if isinstance(value, str) and len(value) > 100:
                                    value = value[:100] + "..."
                                print(f"   {key}: {value}")
                        
                        # 特殊处理嵌套文档结构
                        if 'doc' in doc and isinstance(doc['doc'], dict):
                            print(f"   🔍 嵌套文档内容:")
                            nested_doc = doc['doc']
                            print(f"     嵌套文档类型: {type(nested_doc)}")
                            print(f"     嵌套文档键: {list(nested_doc.keys())}")
                            
                            for key in ['document_name', 'page_number', 'chunk_type', 'page_content', 'content']:
                                if key in nested_doc:
                                    value = nested_doc[key]
                                    if isinstance(value, str) and len(value) > 100:
                                        value = value[:100] + "..."
                                    print(f"     {key}: {value}")
                                else:
                                    print(f"     {key}: 不存在")
                        else:
                            print(f"   ⚠️ 没有嵌套doc字段或doc不是字典")
                    
                    # 如果是Document对象
                    elif hasattr(doc, 'metadata'):
                        print(f"   Document对象，元数据: {doc.metadata}")
                        if hasattr(doc, 'page_content'):
                            content = doc.page_content
                            if len(content) > 100:
                                content = content[:100] + "..."
                            print(f"   内容预览: {content}")
                    
                    print()
                
            except Exception as e:
                print(f"❌ 处理查询时发生错误: {str(e)}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"❌ 初始化时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """
    主函数
    """
    print("🚀 简单文本引擎测试程序启动...")
    print("🔍 直接测试文本引擎功能，绕过混合引擎")
    print()
    
    test_text_engine_direct()
    
    print("\n✅ 测试完成！")

if __name__ == "__main__":
    main()
