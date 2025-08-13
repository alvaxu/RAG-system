#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
文档结构调试程序 - 专门用于分析文本查询返回的文档结构

## 1. 功能特点
- 详细分析文本查询返回的文档结构
- 显示每个文档的完整字段和类型
- 帮助诊断为什么文本查询返回"未知来源"

## 2. 使用方法
- 直接运行：python debug_doc_structure.py
- 会测试多个文本查询问题
- 详细显示每个文档的结构信息
"""

import sys
import os
import json
import time
from typing import Dict, Any, List

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v2.core.hybrid_engine import HybridEngine
from v2.core.base_engine import QueryType

def debug_document_structure(doc: Any, doc_index: int) -> Dict[str, Any]:
    """
    调试单个文档的结构
    
    :param doc: 文档对象
    :param doc_index: 文档索引
    :return: 调试信息字典
    """
    debug_info = {
        'index': doc_index,
        'type': str(type(doc)),
        'attributes': {},
        'dict_keys': [],
        'metadata_fields': {},
        'content_fields': {},
        'analysis': {}
    }
    
    # 分析对象类型和属性
    if hasattr(doc, '__dict__'):
        debug_info['attributes'] = {k: str(type(v)) for k, v in doc.__dict__.items()}
    
    # 如果是字典类型
    if isinstance(doc, dict):
        debug_info['dict_keys'] = list(doc.keys())
        
        # 分析每个字段
        for key, value in doc.items():
            if key == 'doc' and isinstance(value, dict):
                debug_info['content_fields']['doc'] = {
                    'type': str(type(value)),
                    'keys': list(value.keys()) if isinstance(value, dict) else str(value),
                    'sample_values': {k: str(v)[:100] for k, v in list(value.items())[:3]} if isinstance(value, dict) else str(value)
                }
            elif key == 'metadata' and hasattr(value, 'get'):
                debug_info['metadata_fields'] = {k: str(type(v)) for k, v in list(value.items())[:5]}
            else:
                debug_info['content_fields'][key] = {
                    'type': str(type(value)),
                    'value': str(value)[:100] if value is not None else None
                }
    
    # 如果是Document对象
    elif hasattr(doc, 'metadata'):
        debug_info['metadata_fields'] = {k: str(type(v)) for k, v in list(doc.metadata.items())[:5]}
        if hasattr(doc, 'page_content'):
            debug_info['content_fields']['page_content'] = {
                'type': str(type(doc.page_content)),
                'length': len(doc.page_content) if doc.page_content else 0,
                'preview': doc.page_content[:100] if doc.page_content else None
            }
    
    # 分析文档结构类型
    if isinstance(doc, dict):
        if 'doc' in doc and isinstance(doc['doc'], dict):
            debug_info['analysis']['structure_type'] = 'nested_doc'
            debug_info['analysis']['description'] = '包含嵌套doc字段的字典结构'
        elif 'enhanced_description' in doc:
            debug_info['analysis']['structure_type'] = 'image_doc'
            debug_info['analysis']['description'] = '图片文档结构'
        elif 'page_content' in doc:
            debug_info['analysis']['structure_type'] = 'text_table_doc'
            debug_info['analysis']['description'] = '文本或表格文档结构'
        elif 'content' in doc:
            debug_info['analysis']['structure_type'] = 'content_doc'
            debug_info['analysis']['description'] = '包含content字段的文档结构'
        else:
            debug_info['analysis']['structure_type'] = 'unknown_dict'
            debug_info['analysis']['description'] = '未知的字典结构'
    elif hasattr(doc, 'metadata'):
        debug_info['analysis']['structure_type'] = 'langchain_document'
        debug_info['analysis']['description'] = 'LangChain Document对象'
    else:
        debug_info['analysis']['structure_type'] = 'unknown_object'
        debug_info['analysis']['description'] = '未知对象类型'
    
    return debug_info

def test_text_query_document_structure():
    """
    测试文本查询的文档结构
    """
    print("🔍 开始调试文本查询的文档结构...")
    
    try:
        # 初始化引擎（使用默认配置）
        from v2.config.v2_config import HybridEngineConfigV2, V2ConfigManager
        
        config_manager = V2ConfigManager()
        v2_config = config_manager.config  # 获取V2配置对象
        
        # 检查配置是否正确加载
        print(f"📋 配置信息:")
        print(f"   文本引擎配置: {v2_config.text_engine}")
        print(f"   混合引擎配置: {v2_config.hybrid_engine}")
        
        hybrid_engine = HybridEngine(v2_config.hybrid_engine)
        
        # 测试问题
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
                result = hybrid_engine.process_query(
                    question, 
                    query_type=QueryType.TEXT,
                    max_results=5  # 限制结果数量便于分析
                )
                
                if result.success:
                    print(f"✅ 查询成功，找到 {len(result.results)} 个结果")
                    
                    # 分析每个文档的结构
                    for j, doc in enumerate(result.results):
                        print(f"\n📄 文档 {j+1}:")
                        print(f"{'-'*60}")
                        
                        debug_info = debug_document_structure(doc, j+1)
                        
                        # 显示基本信息
                        print(f"   类型: {debug_info['type']}")
                        print(f"   结构类型: {debug_info['analysis']['structure_type']}")
                        print(f"   描述: {debug_info['analysis']['description']}")
                        
                        # 显示字典键（如果是字典）
                        if debug_info['dict_keys']:
                            print(f"   字典键: {debug_info['dict_keys']}")
                        
                        # 显示属性（如果有）
                        if debug_info['attributes']:
                            print(f"   属性: {debug_info['attributes']}")
                        
                        # 显示元数据字段（如果有）
                        if debug_info['metadata_fields']:
                            print(f"   元数据字段: {debug_info['metadata_fields']}")
                        
                        # 显示内容字段（如果有）
                        if debug_info['content_fields']:
                            print(f"   内容字段:")
                            for field, info in debug_info['content_fields'].items():
                                print(f"     {field}: {info}")
                        
                        print()
                        
                        # 如果文档结构复杂，显示更多细节
                        if debug_info['analysis']['structure_type'] == 'nested_doc':
                            print(f"   🔍 嵌套文档详细分析:")
                            nested_doc = doc.get('doc', {})
                            if isinstance(nested_doc, dict):
                                for key, value in nested_doc.items():
                                    print(f"     {key}: {type(value)} = {str(value)[:100]}")
                            print()
                
                else:
                    print(f"❌ 查询失败: {result.error_message}")
                    
            except Exception as e:
                print(f"❌ 处理查询时发生错误: {str(e)}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"❌ 初始化引擎时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """
    主函数
    """
    print("🚀 文档结构调试程序启动...")
    print("🔍 专门用于分析文本查询返回的文档结构")
    print()
    
    test_text_query_document_structure()
    
    print("\n✅ 调试完成！")
    print("💡 请根据上述分析结果，确定文档结构处理的问题所在")

if __name__ == "__main__":
    main()
