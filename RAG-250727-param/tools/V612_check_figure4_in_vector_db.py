'''
程序说明：

## 1. 检查向量数据库中图4的完整信息
## 2. 验证两张图4是否都正确存储在数据库中
## 3. 分析数据库是否有问题
'''

import os
import sys
import pickle
import json
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import FAISS
from config.config_manager import ConfigManager

def check_figure4_in_vector_db():
    """检查向量数据库中图4的完整信息"""
    
    # 加载配置
    config = ConfigManager()
    
    # 向量数据库路径
    vector_db_path = config.settings.vector_db_dir
    
    print("🔍 检查向量数据库中图4的完整信息")
    print("=" * 60)
    
    # 检查向量数据库文件是否存在
    if not os.path.exists(vector_db_path):
        print(f"❌ 向量数据库路径不存在: {vector_db_path}")
        return
    
    index_file = os.path.join(vector_db_path, "index.pkl")
    metadata_file = os.path.join(vector_db_path, "metadata.pkl")
    
    if not os.path.exists(index_file) or not os.path.exists(metadata_file):
        print(f"❌ 向量数据库文件不完整")
        print(f"   index.pkl: {'✅' if os.path.exists(index_file) else '❌'}")
        print(f"   metadata.pkl: {'✅' if os.path.exists(metadata_file) else '❌'}")
        return
    
    print("✅ 向量数据库文件存在")
    
    try:
        # 加载向量数据库
        embeddings = DashScopeEmbeddings(
            dashscope_api_key=config.settings.dashscope_api_key, 
            model="text-embedding-v1"
        )
        vector_store = FAISS.load_local(
            vector_db_path, 
            embeddings, 
            allow_dangerous_deserialization=True
        )
        
        print(f"✅ 向量数据库加载成功")
        print(f"📊 总文档数: {len(vector_store.docstore._dict)}")
        print(f"📊 索引大小: {vector_store.index.ntotal}")
        
        # 查找所有包含"图4"的文档
        print(f"\n🔍 查找包含'图4'的文档...")
        print("-" * 40)
        
        figure4_docs = []
        for doc_id, doc in vector_store.docstore._dict.items():
            content = doc.page_content
            metadata = doc.metadata
            
            # 检查内容中是否包含"图4"
            if "图4" in content:
                figure4_docs.append({
                    'id': doc_id,
                    'content': content,
                    'metadata': metadata,
                    'document_name': metadata.get('document_name', '未知文档'),
                    'chunk_type': metadata.get('chunk_type', 'text'),
                    'img_caption': metadata.get('img_caption', []),
                    'page_number': metadata.get('page_number', 0)
                })
        
        print(f"📋 找到 {len(figure4_docs)} 个包含'图4'的文档")
        
        if figure4_docs:
            print(f"\n📄 图4文档详情:")
            for i, doc in enumerate(figure4_docs, 1):
                print(f"\n文档 {i}:")
                print(f"  📄 文档名称: {doc['document_name']}")
                print(f"  🏷️ 文档类型: {doc['chunk_type']}")
                print(f"  📍 页码: {doc['page_number']}")
                
                # 显示图片标题
                if doc['img_caption']:
                    print(f"  🖼️ 图片标题: {doc['img_caption']}")
                
                # 显示内容片段
                content_preview = doc['content'][:200] + "..." if len(doc['content']) > 200 else doc['content']
                print(f"  📝 内容预览: {content_preview}")
                
                # 显示完整元数据
                print(f"  🔍 完整元数据: {json.dumps(doc['metadata'], ensure_ascii=False, indent=2)}")
        
        # 专门查找两张图4
        print(f"\n🎯 专门查找两张图4:")
        print("-" * 40)
        
        # 图4-1: 中原证券的图4
        print(f"\n1️⃣ 查找中原证券图4: '公司25Q1下游应用领域结构情况'")
        zhongyuan_figure4 = []
        for doc in figure4_docs:
            if "公司25Q1下游应用领域结构情况" in doc['content']:
                zhongyuan_figure4.append(doc)
        
        if zhongyuan_figure4:
            print(f"✅ 找到 {len(zhongyuan_figure4)} 个中原证券图4")
            for doc in zhongyuan_figure4:
                print(f"   📄 文档: {doc['document_name']}")
                print(f"   🏷️ 类型: {doc['chunk_type']}")
        else:
            print(f"❌ 未找到中原证券图4")
        
        # 图4-2: 上海证券的图4
        print(f"\n2️⃣ 查找上海证券图4: '中芯国际归母净利润情况概览'")
        shanghai_figure4 = []
        for doc in figure4_docs:
            if "中芯国际归母净利润情况概览" in doc['content']:
                shanghai_figure4.append(doc)
        
        if shanghai_figure4:
            print(f"✅ 找到 {len(shanghai_figure4)} 个上海证券图4")
            for doc in shanghai_figure4:
                print(f"   📄 文档: {doc['document_name']}")
                print(f"   🏷️ 类型: {doc['chunk_type']}")
        else:
            print(f"❌ 未找到上海证券图4")
        
        # 测试检索功能
        print(f"\n🧪 测试检索功能:")
        print("-" * 40)
        
        test_queries = [
            "图4",
            "公司25Q1下游应用领域结构情况",
            "中芯国际归母净利润情况概览",
            "请显示图4"
        ]
        
        for query in test_queries:
            print(f"\n🔍 查询: '{query}'")
            try:
                results = vector_store.similarity_search(query, k=3)
                print(f"✅ 找到 {len(results)} 个结果")
                
                for j, result in enumerate(results, 1):
                    doc_name = result.metadata.get('document_name', '未知文档')
                    chunk_type = result.metadata.get('chunk_type', 'text')
                    img_caption = result.metadata.get('img_caption', [])
                    
                    print(f"   结果 {j}:")
                    print(f"     文档: {doc_name}")
                    print(f"     类型: {chunk_type}")
                    if img_caption:
                        print(f"     图片标题: {img_caption}")
                    print(f"     内容: {result.page_content[:100]}...")
                    
            except Exception as e:
                print(f"❌ 检索失败: {e}")
        
        # 检查图片类型文档
        print(f"\n🖼️ 检查图片类型文档:")
        print("-" * 40)
        
        image_docs = []
        for doc_id, doc in vector_store.docstore._dict.items():
            if doc.metadata.get('chunk_type') == 'image':
                image_docs.append({
                    'id': doc_id,
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'document_name': doc.metadata.get('document_name', '未知文档'),
                    'img_caption': doc.metadata.get('img_caption', [])
                })
        
        print(f"📊 总共有 {len(image_docs)} 个图片文档")
        
        # 查找图片文档中的图4
        figure4_images = []
        for doc in image_docs:
            if doc['img_caption'] and any("图4" in caption for caption in doc['img_caption']):
                figure4_images.append(doc)
        
        print(f"🖼️ 找到 {len(figure4_images)} 个图4图片文档")
        
        if figure4_images:
            for i, doc in enumerate(figure4_images, 1):
                print(f"\n图片 {i}:")
                print(f"  📄 文档: {doc['document_name']}")
                print(f"  🖼️ 标题: {doc['img_caption']}")
                print(f"  📝 描述: {doc['content'][:200]}...")
        
        # 总结
        print(f"\n📋 检查总结:")
        print("-" * 40)
        print(f"✅ 向量数据库状态: 正常")
        print(f"📊 总文档数: {len(vector_store.docstore._dict)}")
        print(f"🖼️ 图片文档数: {len(image_docs)}")
        print(f"📄 包含'图4'的文档数: {len(figure4_docs)}")
        print(f"🖼️ 图4图片文档数: {len(figure4_images)}")
        
        # 判断是否有问题
        if len(figure4_docs) == 0:
            print(f"❌ 问题: 未找到任何包含'图4'的文档")
        elif len(figure4_images) == 0:
            print(f"⚠️ 问题: 未找到图4的图片文档")
        else:
            print(f"✅ 图4文档存在，数据库正常")
        
    except Exception as e:
        print(f"❌ 加载向量数据库失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_figure4_in_vector_db()
