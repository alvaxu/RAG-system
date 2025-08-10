"""
检查图片文档的状态，看看为什么显示所有图片都已经被处理
"""

import os
import sys
import json

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from config.settings import Settings

def check_image_status():
    """检查图片文档的状态"""
    
    # 1. 加载向量数据库
    try:
        config = Settings.load_from_file('config.json')
        api_key = config.dashscope_api_key
        embeddings = DashScopeEmbeddings(dashscope_api_key=api_key, model="text-embedding-v1")
        vector_store = FAISS.load_local("./central/vector_db", embeddings, allow_dangerous_deserialization=True)
        print(f"✅ 向量数据库加载成功，包含 {len(vector_store.docstore._dict)} 个文档")
    except Exception as e:
        print(f"❌ 加载向量数据库失败: {e}")
        return
    
    # 2. 识别图片文档
    image_docs = []
    for doc_id, doc in vector_store.docstore._dict.items():
        metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
        
        # 检查是否为图片类型
        if metadata.get('chunk_type') == 'image':
            doc_info = {
                'doc_id': doc_id,
                'content': doc.page_content,
                'metadata': metadata,
                'image_path': metadata.get('image_path', ''),
                'document_name': metadata.get('document_name', '未知文档'),
                'page_number': metadata.get('page_number', 1),
                'enhanced_description': metadata.get('enhanced_description', ''),
                'v502_enhancement_timestamp': metadata.get('v502_enhancement_timestamp', None),
                'v502_enhanced': metadata.get('v502_enhanced', False)
            }
            image_docs.append(doc_info)
    
    print(f"\n🔍 识别到 {len(image_docs)} 个图片文档")
    
    # 3. 检查每个图片的状态
    processed_count = 0
    unprocessed_count = 0
    
    for i, doc_info in enumerate(image_docs[:5], 1):  # 只显示前5个
        print(f"\n📷 图片 {i}: {doc_info['image_path']}")
        print(f"   文档名称: {doc_info['document_name']}")
        print(f"   页面: {doc_info['page_number']}")
        
        enhanced_description = doc_info['enhanced_description']
        v502_timestamp = doc_info['v502_enhancement_timestamp']
        v502_enhanced = doc_info['v502_enhanced']
        
        print(f"   增强描述长度: {len(enhanced_description)}")
        print(f"   V502时间戳: {v502_timestamp}")
        print(f"   V502标记: {v502_enhanced}")
        
        # 检查V502特有标记
        v502_markers = [
            'V502_enhanced',
            '基础视觉描述:',
            '内容理解描述:', 
            '数据趋势描述:',
            '语义特征描述:',
            '图表类型:',
            '数据点:',
            '趋势分析:',
            '关键洞察:'
        ]
        
        found_markers = [marker for marker in v502_markers if marker in enhanced_description]
        
        if found_markers:
            print(f"   ✅ 已处理 - 找到标记: {found_markers}")
            processed_count += 1
        elif v502_timestamp or v502_enhanced:
            print(f"   ✅ 已处理 - 有时间戳或标记")
            processed_count += 1
        else:
            print(f"   ❌ 未处理")
            unprocessed_count += 1
        
        # 显示增强描述的前100个字符
        if enhanced_description:
            preview = enhanced_description[:100] + "..." if len(enhanced_description) > 100 else enhanced_description
            print(f"   描述预览: {preview}")
        else:
            print(f"   描述预览: 无")
    
    print(f"\n📊 统计结果:")
    print(f"   已处理图片: {processed_count}")
    print(f"   未处理图片: {unprocessed_count}")
    print(f"   总图片数: {len(image_docs)}")
    
    # 4. 检查是否有未处理的图片
    if unprocessed_count > 0:
        print(f"\n🔍 未处理的图片:")
        for doc_info in image_docs:
            enhanced_description = doc_info['enhanced_description']
            v502_timestamp = doc_info['v502_enhancement_timestamp']
            v502_enhanced = doc_info['v502_enhanced']
            
            v502_markers = [
                'V502_enhanced',
                '基础视觉描述:',
                '内容理解描述:', 
                '数据趋势描述:',
                '语义特征描述:',
                '图表类型:',
                '数据点:',
                '趋势分析:',
                '关键洞察:'
            ]
            
            found_markers = [marker for marker in v502_markers if marker in enhanced_description]
            
            if not found_markers and not v502_timestamp and not v502_enhanced:
                print(f"   - {doc_info['image_path']}")

if __name__ == "__main__":
    check_image_status()
