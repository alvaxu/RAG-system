#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
## 1. 简单的V2引擎连接测试
## 2. 验证引擎是否能正确加载数据库中的文档
## 3. 检查各类型文档的加载数量
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v2.core.image_engine import ImageEngine
from v2.core.text_engine import TextEngine
from v2.core.table_engine import TableEngine
from v2.core.hybrid_engine import HybridEngine
from v2.config.v2_config import ImageEngineConfigV2, TextEngineConfigV2, TableEngineConfigV2, HybridEngineConfigV2
from config.config_manager import ConfigManager
from document_processing.vector_generator import VectorGenerator

def test_v2_engines():
    """测试V2引擎的数据库连接"""
    print("🔍 测试V2引擎数据库连接...")
    
    # 加载配置
    config_manager = ConfigManager()
    vector_db_path = config_manager.get_settings().vector_db_dir
    print(f"📁 向量数据库路径: {vector_db_path}")
    
    try:
        # 加载向量数据库
        print("\n📚 加载向量数据库...")
        vector_generator = VectorGenerator(config_manager.get_settings())
        vector_store = vector_generator.load_vector_store(vector_db_path)
        print(f"✅ 向量数据库加载成功")
        
        # 测试图片引擎
        print("\n📸 测试图片引擎...")
        image_config = ImageEngineConfigV2()
        image_engine = ImageEngine(image_config, vector_store)
        print(f"✅ 图片引擎初始化成功")
        print(f"📊 图片文档数量: {len(image_engine.image_docs)}")
        
        # 测试文本引擎
        print("\n📝 测试文本引擎...")
        text_config = TextEngineConfigV2()
        text_engine = TextEngine(text_config, vector_store)
        print(f"✅ 文本引擎初始化成功")
        print(f"📊 文本文档数量: {len(text_engine.text_docs)}")
        
        # 测试表格引擎
        print("\n📊 测试表格引擎...")
        table_config = TableEngineConfigV2()
        table_engine = TableEngine(table_config, vector_store)
        print(f"✅ 表格引擎初始化成功")
        print(f"📊 表格文档数量: {len(table_engine.table_docs)}")
        
        # 测试混合引擎
        print("\n🔄 测试混合引擎...")
        hybrid_config = HybridEngineConfigV2()
        hybrid_engine = HybridEngine(hybrid_config, image_engine, text_engine, table_engine)
        print(f"✅ 混合引擎初始化成功")
        
        # 总结
        total_docs = len(image_engine.image_docs) + len(text_engine.text_docs) + len(table_engine.table_docs)
        print(f"\n🎯 总结:")
        print(f"   图片文档: {len(image_engine.image_docs)}")
        print(f"   文本文档: {len(text_engine.text_docs)}")
        print(f"   表格文档: {len(table_engine.table_docs)}")
        print(f"   总计: {total_docs}")
        
        if total_docs > 0:
            print("✅ V2引擎数据库连接成功！")
            return True
        else:
            print("❌ V2引擎没有连接到任何文档")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_v2_engines()
    sys.exit(0 if success else 1)
