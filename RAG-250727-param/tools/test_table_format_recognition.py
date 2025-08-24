#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试TableEngine格式识别
验证unified_pipeline能正确识别TableEngine的输出格式
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v2.core.unified_pipeline import UnifiedPipeline

def test_table_format_recognition():
    """测试TableEngine格式识别"""
    
    # 创建unified_pipeline实例
    config = {
        'enabled': True,
        'llm_engine': None,
        'source_filter_engine': None
    }
    
    pipeline = UnifiedPipeline(config)
    
    # 模拟TableEngine的输出格式（来自日志）
    table_doc = {
        'id': 'unknown', 
        'content': '', 
        'score': 0.3100101519575618, 
        'source': 'unknown', 
        'layer': 1, 
        'page_content': '', 
        'document_name': '未知文档', 
        'page_number': '未知页', 
        'chunk_type': 'table', 
        'table_type': 'unknown', 
        'doc_id': 'unknown', 
        'metadata': {
            'document_name': '未知文档', 
            'page_number': '未知页', 
            'table_type': 'unknown', 
            'business_domain': 'unknown', 
            'quality_score': 0.0, 
            'is_truncated': False, 
            'truncation_type': 'none', 
            'truncated_rows': 0, 
            'current_rows': 0, 
            'original_rows': 0
        }
    }
    
    print("🔍 测试TableEngine格式识别")
    print(f"📊 输入文档: {table_doc['chunk_type']} - {table_doc['document_name']}")
    
    # 测试metadata提取
    metadata = pipeline._extract_metadata_from_doc(table_doc)
    
    if metadata:
        print(f"✅ metadata提取成功")
        print(f"📋 包含字段: {list(metadata.keys())}")
        print(f"📄 document_name: {metadata.get('document_name')}")
        print(f"📄 page_number: {metadata.get('page_number')}")
        print(f"📄 chunk_type: {metadata.get('chunk_type')}")
    else:
        print("❌ metadata提取失败")
        return False
    
    # 测试源信息构建
    source_info = pipeline._build_unified_source_info(table_doc, metadata)
    
    if source_info:
        print(f"✅ 源信息构建成功")
        print(f"📋 源信息字段: {list(source_info.keys())}")
        print(f"📄 title: {source_info.get('title')}")
        print(f"📄 source_type: {source_info.get('source_type')}")
        print(f"📄 score: {source_info.get('score')}")
    else:
        print("❌ 源信息构建失败")
        return False
    
    print("\n🎉 所有测试通过！TableEngine格式识别正常")
    return True

if __name__ == "__main__":
    try:
        success = test_table_format_recognition()
        if success:
            print("\n✅ 测试成功：unified_pipeline能正确识别TableEngine格式")
        else:
            print("\n❌ 测试失败：TableEngine格式识别有问题")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
