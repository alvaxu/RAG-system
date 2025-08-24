#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
## 1. 测试unified_pipeline的智能格式处理逻辑
## 2. 模拟三种引擎的不同输出格式
## 3. 验证字段提取和映射是否正确
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_text_engine_format():
    """测试TextEngine格式处理"""
    print("🔍 测试TextEngine格式处理...")
    
    try:
        from v2.core.unified_pipeline import UnifiedPipeline
        
        # 创建UnifiedPipeline实例（不需要完整配置）
        pipeline = UnifiedPipeline(config={}, llm_engine=None, source_filter_engine=None)
        
        # 模拟TextEngine的输出格式
        text_engine_doc = {
            'content': '中芯国际的主要业务是提供集成电路晶圆代工服务',
            'metadata': {
                'document_name': '中芯国际深度研究报告',
                'page_number': 5,
                'chunk_type': 'text',
                'id': 'text_chunk_001'
            },
            'vector_score': 0.85,
            'search_strategy': 'vector_similarity_filter',
            'doc_id': 'text_chunk_001',
            'doc': type('MockDocument', (), {
                'page_content': '中芯国际的主要业务是提供集成电路晶圆代工服务',
                'metadata': {
                    'document_name': '中芯国际深度研究报告',
                    'page_number': 5,
                    'chunk_type': 'text',
                    'id': 'text_chunk_001'
                }
            })()
        }
        
        # 测试metadata提取
        metadata = pipeline._extract_metadata_from_doc(text_engine_doc)
        if metadata:
            print("✅ TextEngine格式metadata提取成功")
            print(f"   document_name: {metadata.get('document_name')}")
            print(f"   chunk_type: {metadata.get('chunk_type')}")
            print(f"   page_number: {metadata.get('page_number')}")
        else:
            print("❌ TextEngine格式metadata提取失败")
        
        # 测试完整源信息构建
        source_info = pipeline._build_unified_source_info(text_engine_doc, metadata)
        if source_info:
            print("✅ TextEngine格式源信息构建成功")
            print(f"   源信息字段数量: {len(source_info)}")
            print(f"   主要字段: {list(source_info.keys())}")
        else:
            print("❌ TextEngine格式源信息构建失败")
            
    except Exception as e:
        print(f"❌ TextEngine格式测试失败: {e}")

def test_image_engine_format():
    """测试ImageEngine格式处理"""
    print("\n🔍 测试ImageEngine格式处理...")
    
    try:
        from v2.core.unified_pipeline import UnifiedPipeline
        
        # 创建UnifiedPipeline实例
        pipeline = UnifiedPipeline(config={}, llm_engine=None, source_filter_engine=None)
        
        # 模拟ImageEngine的输出格式
        image_engine_doc = {
            'document_name': '中芯国际财务报告',
            'page_number': 8,
            'chunk_type': 'image',
            'image_path': '/path/to/image.jpg',
            'caption': ['图4：中芯国际归母净利润情况概览'],
            'enhanced_description': '该图表展示了中芯国际从2017年至2024年的归母净利润变化趋势',
            'image_id': 'img_004',
            'image_filename': 'profit_overview.jpg',
            'image_type': 'chart',
            'extension': 'jpg'
        }
        
        # 测试metadata提取
        metadata = pipeline._extract_metadata_from_doc(image_engine_doc)
        if metadata:
            print("✅ ImageEngine格式metadata提取成功")
            print(f"   document_name: {metadata.get('document_name')}")
            print(f"   chunk_type: {metadata.get('chunk_type')}")
            print(f"   image_path: {metadata.get('image_path')}")
        else:
            print("❌ ImageEngine格式metadata提取失败")
        
        # 测试完整源信息构建
        source_info = pipeline._build_unified_source_info(image_engine_doc, metadata)
        if source_info:
            print("✅ ImageEngine格式源信息构建成功")
            print(f"   源信息字段数量: {len(source_info)}")
            print(f"   图片字段: {source_info.get('caption', 'N/A')}")
        else:
            print("❌ ImageEngine格式源信息构建失败")
            
    except Exception as e:
        print(f"❌ ImageEngine格式测试失败: {e}")

def test_table_engine_format():
    """测试TableEngine格式处理"""
    print("\n🔍 测试TableEngine格式处理...")
    
    try:
        from v2.core.unified_pipeline import UnifiedPipeline
        
        # 创建UnifiedPipeline实例
        pipeline = UnifiedPipeline(config={}, llm_engine=None, source_filter_engine=None)
        
        # 模拟TableEngine的输出格式
        table_engine_doc = {
            'table_id': 'table_001',
            'score': 0.92,
            'layer': 1,
            'adjusted_score': 0.92,
            'final_rank': 1,
            'final_score': 0.92,
            'document_name': '中芯国际财务报告',
            'page_number': 12,
            'chunk_type': 'table',
            'table_title': '中芯国际营业收入统计表',
            'html_content': '<table>...</table>'
        }
        
        # 测试metadata提取
        metadata = pipeline._extract_metadata_from_doc(table_engine_doc)
        if metadata:
            print("✅ TableEngine格式metadata提取成功")
            print(f"   document_name: {metadata.get('document_name')}")
            print(f"   chunk_type: {metadata.get('chunk_type')}")
            print(f"   table_id: {metadata.get('table_id')}")
        else:
            print("❌ TableEngine格式metadata提取失败")
        
        # 测试完整源信息构建
        source_info = pipeline._build_unified_source_info(table_engine_doc, metadata)
        if source_info:
            print("✅ TableEngine格式源信息构建成功")
            print(f"   源信息字段数量: {len(source_info)}")
            print(f"   表格字段: {source_info.get('table_title', 'N/A')}")
        else:
            print("❌ TableEngine格式源信息构建失败")
            
    except Exception as e:
        print(f"❌ TableEngine格式测试失败: {e}")

def test_standard_document_format():
    """测试标准Document对象格式处理"""
    print("\n🔍 测试标准Document对象格式处理...")
    
    try:
        from v2.core.unified_pipeline import UnifiedPipeline
        
        # 创建UnifiedPipeline实例
        pipeline = UnifiedPipeline(config={}, llm_engine=None, source_filter_engine=None)
        
        # 模拟标准Document对象
        class MockDocument:
            def __init__(self):
                self.page_content = '这是一个标准的Document对象'
                self.metadata = {
                    'document_name': '标准文档',
                    'page_number': 1,
                    'chunk_type': 'text',
                    'id': 'doc_001'
                }
        
        standard_doc = MockDocument()
        
        # 测试metadata提取
        metadata = pipeline._extract_metadata_from_doc(standard_doc)
        if metadata:
            print("✅ 标准Document格式metadata提取成功")
            print(f"   document_name: {metadata.get('document_name')}")
            print(f"   chunk_type: {metadata.get('chunk_type')}")
        else:
            print("❌ 标准Document格式metadata提取失败")
        
        # 测试完整源信息构建
        source_info = pipeline._build_unified_source_info(standard_doc, metadata)
        if source_info:
            print("✅ 标准Document格式源信息构建成功")
            print(f"   源信息字段数量: {len(source_info)}")
        else:
            print("❌ 标准Document格式源信息构建失败")
            
    except Exception as e:
        print(f"❌ 标准Document格式测试失败: {e}")

if __name__ == "__main__":
    print("=" * 80)
    print("🎯 测试unified_pipeline智能格式处理逻辑")
    print("=" * 80)
    
    test_text_engine_format()
    test_image_engine_format()
    test_table_engine_format()
    test_standard_document_format()
    
    print("\n" + "=" * 80)
    print("📊 测试完成")
    print("=" * 80)
