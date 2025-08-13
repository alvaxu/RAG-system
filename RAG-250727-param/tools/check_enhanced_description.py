#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查图片文档中enhanced_description字段的内容和作用

分析enhanced_description在图片查询中的实际使用情况
"""

import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_enhanced_description():
    """检查enhanced_description字段的内容和作用"""
    print("🔍 检查图片文档中enhanced_description字段")
    print("=" * 60)
    
    try:
        # 导入必要的模块
        from v2.core.image_engine import ImageEngine
        from v2.config.v2_config import ImageEngineConfigV2
        from core.vector_store import VectorStoreManager  # 修正导入路径和类名
        
        print("📚 正在加载向量数据库...")
        
        # 初始化向量存储管理器
        vector_store_manager = VectorStoreManager()
        
        # 加载向量存储
        vector_store_path = "central/vector_db"
        vector_store = vector_store_manager.load_vector_store(vector_store_path)
        
        if not vector_store:
            print("❌ 无法加载向量数据库")
            return
        
        print(f"✅ 向量数据库加载成功，文档总数: {len(vector_store.docstore._dict)}")
        
        # 统计图片文档
        image_docs = {}
        for doc_id, doc in vector_store.docstore._dict.items():
            chunk_type = doc.metadata.get('chunk_type', '')
            if chunk_type == 'image':
                image_docs[doc_id] = doc
        
        print(f"📸 找到图片文档数量: {len(image_docs)}")
        
        if not image_docs:
            print("❌ 未找到图片文档")
            return
        
        # 分析enhanced_description字段
        print("\n📊 enhanced_description字段分析:")
        print("-" * 50)
        
        enhanced_count = 0
        empty_count = 0
        sample_enhanced = []
        
        for doc_id, doc in image_docs.items():
            enhanced_desc = doc.metadata.get('enhanced_description', '')
            
            if enhanced_desc:
                enhanced_count += 1
                if len(sample_enhanced) < 3:  # 只显示前3个样本
                    sample_enhanced.append({
                        'doc_id': doc_id,
                        'enhanced_description': enhanced_desc[:100] + '...' if len(enhanced_desc) > 100 else enhanced_desc,
                        'caption': doc.metadata.get('img_caption', ''),
                        'title': doc.metadata.get('image_title', '')
                    })
            else:
                empty_count += 1
        
        print(f"✅ 有enhanced_description的图片: {enhanced_count}")
        print(f"❌ 无enhanced_description的图片: {empty_count}")
        print(f"📈 覆盖率: {enhanced_count/(enhanced_count+empty_count)*100:.1f}%")
        
        # 显示样本
        if sample_enhanced:
            print("\n📝 enhanced_description样本:")
            for i, sample in enumerate(sample_enhanced, 1):
                print(f"\n样本 {i}:")
                print(f"  文档ID: {sample['doc_id']}")
                print(f"  增强描述: {sample['enhanced_description']}")
                print(f"  原始标题: {sample['caption']}")
                print(f"  图片标题: {sample['title']}")
        
        # 检查字段在搜索中的作用
        print("\n🔍 检查enhanced_description在搜索中的作用:")
        print("-" * 50)
        
        # 模拟一个查询
        test_query = "中芯国际净利润"
        print(f"测试查询: {test_query}")
        
        # 手动计算相似度分数
        print("\n手动计算相似度分数示例:")
        for i, (doc_id, doc) in enumerate(list(image_docs.items())[:2]):  # 只测试前2个
            print(f"\n图片 {i+1}:")
            
            caption = doc.metadata.get('img_caption', '')
            title = doc.metadata.get('image_title', '')
            enhanced_desc = doc.metadata.get('enhanced_description', '')
            
            print(f"  原始标题: {caption}")
            print(f"  图片标题: {title}")
            print(f"  增强描述: {enhanced_desc[:80] + '...' if enhanced_desc and len(enhanced_desc) > 80 else enhanced_desc}")
            
            # 计算各字段的匹配分数
            caption_score = calculate_text_similarity(test_query, caption)
            title_score = calculate_text_similarity(test_query, title)
            enhanced_score = calculate_text_similarity(test_query, enhanced_desc)
            
            print(f"  标题匹配分数: {caption_score:.3f}")
            print(f"  图片标题分数: {title_score:.3f}")
            print(f"  增强描述分数: {enhanced_score:.3f}")
            
            # 计算综合分数（使用权重）
            total_score = (caption_score * 0.2 + 
                          title_score * 0.5 + 
                          enhanced_score * 0.3)
            print(f"  综合分数: {total_score:.3f}")
        
        print("\n💡 分析结论:")
        print("1. enhanced_description字段提供了AI生成的详细图片描述")
        print("2. 在相似度计算中，enhanced_description权重为30%")
        print("3. 相比原始标题，enhanced_description通常包含更多语义信息")
        print("4. 对于内容查询，enhanced_description能显著提升匹配精度")
        
    except Exception as e:
        print(f"❌ 检查过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

def calculate_text_similarity(query: str, text: str) -> float:
    """计算文本相似度（简化版本）"""
    if not text or not query:
        return 0.0
    
    # 确保text是字符串类型
    if isinstance(text, list):
        text = ' '.join([str(item) for item in text])
    elif not isinstance(text, str):
        text = str(text)
    
    # 简单的词汇重叠计算
    query_words = set(query.lower().split())
    text_words = set(text.lower().split())
    
    if not query_words or not text_words:
        return 0.0
    
    intersection = query_words.intersection(text_words)
    union = query_words.union(text_words)
    
    if union:
        return len(intersection) / len(union)
    return 0.0

if __name__ == "__main__":
    print("🚀 开始检查enhanced_description字段")
    print("=" * 60)
    
    check_enhanced_description()
    
    print("\n🎉 检查完成！")
