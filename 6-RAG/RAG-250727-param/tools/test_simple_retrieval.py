"""
程序说明：
## 1. 简单测试向量检索功能
## 2. 验证数据库是否可以正常检索
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from document_processing.vector_generator import VectorGenerator
from config.settings import Settings

def test_simple_retrieval():
    """测试简单检索功能"""
    try:
        # 加载配置
        settings = Settings.load_from_file('config.json')
        print(f"配置加载成功")
        
        # 初始化向量生成器
        vg = VectorGenerator(settings)
        print(f"向量生成器初始化成功")
        
        # 加载向量存储
        vector_store = vg.load_vector_store(settings.vector_db_dir)
        print(f"向量存储加载成功")
        print(f"索引总数: {vector_store.index.ntotal}")
        print(f"文档存储ID数量: {len(vector_store.docstore._dict)}")
        
        # 测试简单检索
        question = "中芯国际"
        print(f"\n测试问题: {question}")
        
        try:
            docs = vector_store.similarity_search(question, k=5)
            print(f"检索成功，获得 {len(docs)} 个文档")
            
            for i, doc in enumerate(docs[:3]):
                print(f"文档 {i+1}:")
                print(f"  内容长度: {len(doc.page_content)} 字符")
                print(f"  内容预览: {doc.page_content[:100]}...")
                print(f"  来源: {doc.metadata.get('source', '未知')}")
                print()
                
        except Exception as e:
            print(f"检索失败: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_retrieval() 