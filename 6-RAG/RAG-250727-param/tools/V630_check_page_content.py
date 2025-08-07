'''
程序说明：
## 1. 检查向量数据库中图片文档的page_content字段
## 2. 分析page_content与enhanced_description的关系
## 3. 验证图片文档的完整结构
'''

import pickle
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from config.settings import Settings

def check_page_content():
    """检查向量数据库中图片文档的page_content字段"""
    
    print("🔍 检查向量数据库中图片文档的page_content字段")
    print("=" * 60)
    
    try:
        # 加载配置
        config = Settings.load_from_file('config.json')
        embeddings = DashScopeEmbeddings(dashscope_api_key=config.dashscope_api_key, model="text-embedding-v1")
        
        # 加载向量数据库
        vector_db_path = "./central/vector_db"
        vector_store = FAISS.load_local(vector_db_path, embeddings, allow_dangerous_deserialization=True)
        
        print(f"✅ 向量数据库加载成功")
        print(f"📊 总文档数: {len(vector_store.docstore._dict)}")
        
        # 统计图片文档
        image_docs = []
        for doc_id, doc in vector_store.docstore._dict.items():
            metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
            if metadata.get('chunk_type') == 'image':
                image_docs.append((doc_id, doc))
        
        print(f"🖼️  图片文档数: {len(image_docs)}")
        
        if not image_docs:
            print("❌ 没有找到图片文档")
            return
        
        # 检查前5个图片文档的page_content
        print(f"\n🔍 前5个图片文档的page_content分析:")
        print("=" * 60)
        
        for i, (doc_id, doc) in enumerate(image_docs[:5]):
            metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
            
            print(f"\n📷 图片文档 {i+1}:")
            print(f"  文档ID: {doc_id}")
            print(f"  图片ID: {metadata.get('image_id', 'No ID')}")
            print(f"  文档名称: {metadata.get('document_name', 'Unknown')}")
            
            # 检查page_content
            page_content = doc.page_content
            print(f"  page_content长度: {len(str(page_content))}")
            print(f"  page_content内容: {repr(page_content)}")
            
            # 检查enhanced_description
            enhanced_desc = metadata.get('enhanced_description', '')
            print(f"  enhanced_description: {repr(enhanced_desc)}")
            
            # 比较两个字段
            if page_content == enhanced_desc:
                print(f"  ✅ page_content与enhanced_description内容相同")
            else:
                print(f"  ⚠️  page_content与enhanced_description内容不同")
                print(f"     差异: page_content长度={len(str(page_content))}, enhanced_description长度={len(str(enhanced_desc))}")
            
            # 检查图片标题
            img_caption = metadata.get('img_caption', [])
            if img_caption:
                caption_text = ' '.join(img_caption)
                print(f"  图片标题: {caption_text}")
        
        # 统计page_content的情况
        print(f"\n📊 page_content统计:")
        print("=" * 60)
        
        empty_content_count = 0
        non_empty_content_count = 0
        same_as_enhanced_count = 0
        different_from_enhanced_count = 0
        
        for doc_id, doc in image_docs:
            metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
            page_content = doc.page_content
            enhanced_desc = metadata.get('enhanced_description', '')
            
            if not page_content or len(str(page_content).strip()) == 0:
                empty_content_count += 1
            else:
                non_empty_content_count += 1
            
            if page_content == enhanced_desc:
                same_as_enhanced_count += 1
            else:
                different_from_enhanced_count += 1
        
        print(f"  空page_content的文档: {empty_content_count}")
        print(f"  有page_content的文档: {non_empty_content_count}")
        print(f"  page_content与enhanced_description相同的文档: {same_as_enhanced_count}")
        print(f"  page_content与enhanced_description不同的文档: {different_from_enhanced_count}")
        
        # 检查metadata.pkl文件
        print(f"\n🔍 检查metadata.pkl文件:")
        print("=" * 60)
        
        metadata_file = Path("central/vector_db/metadata.pkl")
        if metadata_file.exists():
            with open(metadata_file, 'rb') as f:
                metadata_list = pickle.load(f)
            
            print(f"  metadata.pkl中的记录数: {len(metadata_list)}")
            
            # 检查metadata.pkl中是否有page_content字段
            image_metadata = [item for item in metadata_list if item.get('chunk_type') == 'image']
            print(f"  metadata.pkl中的图片记录数: {len(image_metadata)}")
            
            if image_metadata:
                first_image_metadata = image_metadata[0]
                print(f"  第一个图片记录的字段:")
                for key, value in first_image_metadata.items():
                    if key in ['page_content', 'content', 'enhanced_description']:
                        print(f"    {key}: {repr(value)}")
                    elif isinstance(value, list) and len(value) > 0:
                        print(f"    {key}: {value[:3]}... (共{len(value)}项)")
                    else:
                        print(f"    {key}: {value}")
        else:
            print("  ❌ metadata.pkl文件不存在")
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_page_content()
