#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试表格查询数据流
确认从表格引擎到unified_pipeline的完整数据格式
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def debug_table_data_flow():
    """调试表格查询数据流"""
    
    print("🔍 调试表格查询数据流")
    print("=" * 50)
    
    try:
        # 导入必要的模块
        print("📦 导入模块...")
        from v2.config.v2_config import V2ConfigManager
        
        print("✅ 配置管理器导入成功")
        
        # 获取配置
        print("\n🔧 加载配置...")
        config_manager = V2ConfigManager()
        
        print("✅ 配置管理器创建成功")
        
        # 检查配置对象
        print(f"\n📋 配置对象类型: {type(config_manager.config)}")
        print(f"配置对象属性: {[attr for attr in dir(config_manager.config) if not attr.startswith('_')]}")
        
        # 检查表格引擎配置
        print("\n🔍 检查表格引擎配置...")
        
        # 直接从配置对象获取
        if hasattr(config_manager.config, 'table_engine'):
            table_config = getattr(config_manager.config, 'table_engine')
            print(f"✅ 表格引擎配置获取成功")
            print(f"配置类型: {type(table_config)}")
            print(f"配置属性: {[attr for attr in dir(table_config) if not attr.startswith('_')]}")
            print(f"enabled: {getattr(table_config, 'enabled', 'N/A')}")
            print(f"name: {getattr(table_config, 'name', 'N/A')}")
        else:
            print("❌ 配置对象中没有table_engine属性")
            return
        
        if not table_config.enabled:
            print("❌ 表格引擎未启用")
            return
        
        print(f"✅ 表格引擎配置: {table_config.name}")
        
        # 创建表格引擎实例
        print("\n🚀 创建表格引擎实例...")
        from v2.core.table_engine import TableEngine
        
        # 跳过初始文档加载，专注于测试数据流
        table_engine = TableEngine(table_config, skip_initial_load=True)
        
        # 手动调用_initialize()来设置引擎状态为READY
        try:
            table_engine._initialize()
            print("✅ 表格引擎初始化成功")
        except Exception as e:
            print(f"⚠️ 表格引擎初始化失败: {e}")
        
        print("✅ 表格引擎实例创建成功")
        
        # 检查表格引擎状态
        print(f"\n📊 表格引擎状态:")
        status = table_engine.get_status()
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        print(f"is_ready(): {table_engine.is_ready()}")
        print(f"is_enabled(): {table_engine.is_enabled()}")
        print(f"config.enabled: {table_engine.config.enabled}")
        
        # 测试查询
        test_query = "中芯国际的研发投入和专利申请情况如何？"
        print(f"\n📝 测试查询: {test_query}")
        
        # 执行查询
        print("\n🚀 开始执行表格查询...")
        result = table_engine.process_query(test_query)
        
        if not result.success:
            print(f"❌ 查询失败: {result.error_message}")
            return
        
        print(f"✅ 查询成功，结果数量: {len(result.results)}")
        
        # 检查结果格式
        print("\n📊 检查结果格式:")
        for i, doc in enumerate(result.results):
            print(f"\n--- 结果 {i+1} ---")
            print(f"类型: {type(doc)}")
            print(f"键: {list(doc.keys()) if isinstance(doc, dict) else 'N/A'}")
            
            if isinstance(doc, dict):
                # 检查关键字段
                print(f"id: {doc.get('id', 'N/A')}")
                print(f"chunk_type: {doc.get('chunk_type', 'N/A')}")
                print(f"document_name: {doc.get('document_name', 'N/A')}")
                print(f"page_number: {doc.get('page_number', 'N/A')}")
                
                # 检查metadata
                if 'metadata' in doc:
                    metadata = doc['metadata']
                    print(f"metadata类型: {type(metadata)}")
                    print(f"metadata键: {list(metadata.keys()) if isinstance(metadata, dict) else 'N/A'}")
                    if isinstance(metadata, dict):
                        print(f"metadata.document_name: {metadata.get('document_name', 'N/A')}")
                        print(f"metadata.page_number: {metadata.get('page_number', 'N/A')}")
                
                # 检查是否有doc键
                if 'doc' in doc:
                    print(f"doc键存在: {type(doc['doc'])}")
                    if hasattr(doc['doc'], 'metadata'):
                        print(f"doc.doc.metadata: {doc['doc'].metadata}")
                    else:
                        print("doc.doc没有metadata属性")
        
        # 检查metadata
        if hasattr(result, 'metadata'):
            print(f"\n📋 结果metadata:")
            for key, value in result.metadata.items():
                print(f"  {key}: {value}")
        
        print("\n🎯 调试完成")
        
    except Exception as e:
        print(f"💥 调试异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_table_data_flow()
