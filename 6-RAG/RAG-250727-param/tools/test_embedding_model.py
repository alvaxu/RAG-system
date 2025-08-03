"""
程序说明：
## 1. 测试嵌入模型是否正常工作
## 2. 验证向量维度是否匹配
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
import dashscope
from langchain_community.embeddings import DashScopeEmbeddings

def test_embedding_model():
    """测试嵌入模型"""
    try:
        # 加载配置
        settings = Settings.load_from_file('config.json')
        print(f"配置加载成功")
        print(f"API密钥长度: {len(settings.dashscope_api_key)}")
        
        # 设置API密钥
        dashscope.api_key = settings.dashscope_api_key
        
        # 初始化嵌入模型
        print(f"初始化嵌入模型...")
        embeddings = DashScopeEmbeddings(
            model="text-embedding-v1",
            dashscope_api_key=settings.dashscope_api_key
        )
        
        # 测试嵌入
        print(f"测试文本嵌入...")
        test_text = "中芯国际"
        embedding = embeddings.embed_query(test_text)
        
        print(f"嵌入成功")
        print(f"嵌入维度: {len(embedding)}")
        print(f"配置的向量维度: {settings.vector_dimension}")
        print(f"维度匹配: {len(embedding) == settings.vector_dimension}")
        
        # 测试批量嵌入
        print(f"\n测试批量嵌入...")
        test_texts = ["中芯国际", "晶圆制造", "深度研究"]
        embeddings_batch = embeddings.embed_documents(test_texts)
        
        print(f"批量嵌入成功")
        print(f"批量嵌入数量: {len(embeddings_batch)}")
        print(f"每个嵌入维度: {len(embeddings_batch[0])}")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_embedding_model() 