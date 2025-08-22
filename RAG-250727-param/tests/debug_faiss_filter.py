#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
调试FAISS filter功能，检查table文档的metadata结构

## 1. 修复VectorStore导入问题
## 2. 检查FAISS索引中table文档的metadata
## 3. 验证filter语法是否正确
"""

import sys
import os
import json
import pickle
import numpy as np

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_faiss_metadata():
    """检查FAISS索引的metadata结构"""
    try:
        # 尝试直接加载metadata文件
        metadata_path = "central/vector_db/metadata.pkl"
        if os.path.exists(metadata_path):
            print(f"✅ 找到metadata文件: {metadata_path}")
            
            with open(metadata_path, 'rb') as f:
                metadata = pickle.load(f)
            
            print(f"✅ 成功加载metadata，包含 {len(metadata)} 个文档")
            
            # 分析chunk_type分布
            chunk_types = {}
            table_docs = []
            
            for i, meta in enumerate(metadata):
                chunk_type = meta.get('chunk_type', 'unknown')
                chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
                
                if chunk_type == 'table':
                    table_docs.append({
                        'index': i,
                        'metadata': meta,
                        'content_preview': meta.get('content', '')[:100] if meta.get('content') else 'N/A'
                    })
            
            print(f"\n📊 chunk_type分布:")
            for chunk_type, count in chunk_types.items():
                print(f"  {chunk_type}: {count}")
            
            print(f"\n📋 table文档详情 (共{len(table_docs)}个):")
            for doc in table_docs[:5]:  # 只显示前5个
                print(f"  索引{i}: {doc['content_preview']}")
                print(f"    metadata: {doc['metadata']}")
                print()
            
            if len(table_docs) > 5:
                print(f"  ... 还有{len(table_docs)-5}个table文档")
            
            return True, table_docs
            
        else:
            print(f"❌ 未找到metadata文件: {metadata_path}")
            return False, []
            
    except Exception as e:
        print(f"❌ 检查metadata失败: {e}")
        return False, []

def test_filter_syntax():
    """测试filter语法"""
    try:
        # 尝试导入VectorStore
        from v2.core.vector_store import VectorStore
        
        print("✅ 成功导入VectorStore")
        
        # 尝试加载向量数据库
        vector_store = VectorStore()
        print("✅ 成功加载向量数据库")
        
        # 测试filter语法
        test_query = "测试查询"
        test_filter = {'chunk_type': 'table'}
        
        print(f"🔍 测试filter语法: {test_filter}")
        
        # 尝试使用filter搜索
        results = vector_store.similarity_search(
            test_query,
            k=5,
            filter=test_filter
        )
        
        print(f"✅ filter搜索成功，返回 {len(results)} 个结果")
        return True
        
    except ImportError as e:
        print(f"❌ 导入VectorStore失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试filter失败: {e}")
        return False

def main():
    """主函数"""
    print("🔍 开始调试FAISS filter功能...")
    print("=" * 50)
    
    # 1. 检查metadata结构
    print("1️⃣ 检查FAISS metadata结构...")
    success, table_docs = check_faiss_metadata()
    
    if not success:
        print("❌ 无法检查metadata，退出")
        return
    
    # 2. 测试filter语法
    print("\n2️⃣ 测试filter语法...")
    filter_success = test_filter_syntax()
    
    # 3. 分析结果
    print("\n3️⃣ 分析结果...")
    if table_docs:
        print(f"✅ 确认存在 {len(table_docs)} 个table文档")
        if filter_success:
            print("✅ filter语法测试成功")
            print("🔍 可能的问题：")
            print("  1. 向量数据库中的chunk_type值可能与预期不符")
            print("  2. metadata结构可能有问题")
            print("  3. 需要检查具体的filter值")
        else:
            print("❌ filter语法测试失败")
    else:
        print("❌ 未找到table文档，这可能是问题的根源")
        print("🔍 建议检查：")
        print("  1. 文档处理时是否正确设置了chunk_type")
        print("  2. 向量化时是否正确保存了metadata")

if __name__ == "__main__":
    main()
