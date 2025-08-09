#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细分析图片的enhanced_description内容，区分基础处理和深度增强
"""

import os
import sys
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def analyze_enhanced_descriptions():
    """详细分析图片的enhanced_description内容"""
    
    try:
        from langchain_community.vectorstores import FAISS
        from langchain_community.embeddings import DashScopeEmbeddings
        from config.settings import Settings
        
        # 加载配置
        settings = Settings.load_from_file('config.json')
        
        # 加载向量数据库
        embeddings = DashScopeEmbeddings(
            dashscope_api_key=settings.dashscope_api_key, 
            model='text-embedding-v1'
        )
        vector_store = FAISS.load_local(
            './central/vector_db', 
            embeddings, 
            allow_dangerous_deserialization=True
        )
        
        print("🔍 详细分析图片的enhanced_description内容...")
        print("=" * 80)
        
        # 获取所有图片文档
        image_docs = []
        for doc_id, doc in vector_store.docstore._dict.items():
            if doc.metadata.get('image_path'):
                image_docs.append((doc_id, doc.metadata))
        
        print(f"📊 找到 {len(image_docs)} 个图片文档")
        print()
        
        # 分析前几个图片的详细内容
        for i, (doc_id, metadata) in enumerate(image_docs[:5]):
            print(f"📷 图片 {i+1}: {metadata.get('image_path', 'Unknown')}")
            print(f"   ID: {doc_id}")
            
            # 检查深度增强字段
            has_layered = 'layered_descriptions' in metadata
            has_structured = 'structured_info' in metadata
            has_timestamp = 'enhancement_timestamp' in metadata
            has_enabled = 'enhancement_enabled' in metadata
            
            print(f"   深度增强字段:")
            print(f"     layered_descriptions: {has_layered}")
            print(f"     structured_info: {has_structured}")
            print(f"     enhancement_timestamp: {has_timestamp}")
            print(f"     enhancement_enabled: {has_enabled}")
            
            # 分析enhanced_description内容
            enhanced_desc = metadata.get('enhanced_description', '')
            if enhanced_desc:
                print(f"   enhanced_description 长度: {len(enhanced_desc)}")
                print(f"   内容预览: {enhanced_desc[:200]}...")
                
                # 检查是否包含深度增强标记
                depth_markers = [
                    '基础视觉描述:', '内容理解描述:', '数据趋势描述:', 
                    '语义特征描述:', '数据点:', '趋势分析:', '关键洞察:'
                ]
                
                found_markers = [marker for marker in depth_markers if marker in enhanced_desc]
                if found_markers:
                    print(f"   包含的深度增强标记: {found_markers}")
                else:
                    print(f"   不包含深度增强标记")
            else:
                print(f"   没有enhanced_description字段")
            
            print("-" * 60)
        
        # 统计分析
        print("\n📊 统计分析:")
        print("=" * 60)
        
        depth_enhanced_count = 0
        basic_processed_count = 0
        no_description_count = 0
        
        for doc_id, metadata in image_docs:
            has_layered = 'layered_descriptions' in metadata
            has_structured = 'structured_info' in metadata
            enhanced_desc = metadata.get('enhanced_description', '')
            
            if has_layered and has_structured:
                depth_enhanced_count += 1
            elif enhanced_desc:
                basic_processed_count += 1
            else:
                no_description_count += 1
        
        print(f"深度增强图片: {depth_enhanced_count}")
        print(f"基础处理图片: {basic_processed_count}")
        print(f"无描述图片: {no_description_count}")
        print(f"总计: {len(image_docs)}")
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_enhanced_descriptions()
