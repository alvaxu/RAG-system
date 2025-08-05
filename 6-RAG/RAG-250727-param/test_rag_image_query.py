'''
测试RAG系统如何回答图像相关问题
'''

import os
import sys
import logging
from typing import List, Dict, Any

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from core.enhanced_qa_system import EnhancedQASystem

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_image_query():
    """测试RAG系统对图像问题的回答"""
    try:
        # 加载配置
        config = Settings.load_from_file('config.json')
        from langchain_community.vectorstores import FAISS
        from langchain_community.embeddings import DashScopeEmbeddings
        
        # 初始化向量数据库
        embeddings = DashScopeEmbeddings(
            dashscope_api_key=config.dashscope_api_key,
            model="text-embedding-v1"
        )
        
        vector_store = FAISS.load_local(
            config.vector_db_dir,
            embeddings,
            allow_dangerous_deserialization=True
        )
        
        # 初始化QA系统
        qa_system = EnhancedQASystem(
            vector_store,
            config.dashscope_api_key,
            None,
            config.to_dict()
        )
        
        # 测试问题
        test_questions = [
            "这张图是什么？",
            "图片里显示了什么内容？",
            "这张图表是什么类型的？",
            "图片中的信息是什么？"
        ]
        
        print("🔍 测试RAG系统对图像问题的回答...")
        print("="*60)
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n📝 问题 {i}: {question}")
            print("-" * 40)
            
            try:
                # 获取回答
                result = qa_system.answer_question(question)
                answer = result.get('answer', result)  # 兼容返回字典或字符串
                
                print("🤖 RAG系统回答:")
                print(answer)
                
                # 分析回答的来源
                print("\n📊 回答分析:")
                if "图片" in answer or "图表" in answer or "图像" in answer:
                    print("✅ 回答中包含了图像相关内容")
                else:
                    print("❌ 回答中没有明显的图像内容")
                    
            except Exception as e:
                print(f"❌ 获取回答失败: {e}")
        
        print("\n" + "="*60)
        print("💡 分析结论:")
        print("1. RAG系统可能通过以下方式提供图像信息:")
        print("   - 利用图片的元数据（标题、脚注）")
        print("   - 基于embedding的语义匹配")
        print("   - LLM的推理和上下文理解")
        print("2. 虽然ONE-PEACE不能直接输出文字描述，但RAG系统")
        print("   可以通过其他方式提供丰富的图像信息")
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

def analyze_image_metadata():
    """分析图片的元数据信息"""
    try:
        from langchain_community.vectorstores import FAISS
        from langchain_community.embeddings import DashScopeEmbeddings
        
        # 加载向量数据库
        embeddings = DashScopeEmbeddings(
            dashscope_api_key="sk-bfff6cdc92e84b2f89064cd382fdbe4a",
            model="text-embedding-v1"
        )
        
        vector_store = FAISS.load_local(
            "./central/vector_db",
            embeddings,
            allow_dangerous_deserialization=True
        )
        
        print("\n🔍 分析图片元数据信息...")
        print("="*60)
        
        image_count = 0
        for doc_id, doc in vector_store.docstore._dict.items():
            metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
            
            if metadata.get('chunk_type') == 'image':
                image_count += 1
                print(f"\n📷 图片 {image_count}:")
                print(f"   文档ID: {doc_id}")
                print(f"   文档名称: {metadata.get('document_name', '未知')}")
                print(f"   图片标题: {metadata.get('img_caption', [])}")
                print(f"   图片脚注: {metadata.get('img_footnote', [])}")
                print(f"   增强描述: {metadata.get('enhanced_description', '无')}")
                print(f"   语义描述: {metadata.get('semantic_description', '无')}")
                
                if image_count >= 3:  # 只显示前3张图片
                    break
        
        print(f"\n📊 元数据分析:")
        print(f"总共找到 {image_count} 张图片")
        print("这些元数据信息为RAG系统提供了丰富的图像描述基础")
        
    except Exception as e:
        logger.error(f"分析元数据失败: {e}")

def main():
    """主函数"""
    print("🔍 开始测试RAG系统的图像问答能力...")
    
    # 测试RAG系统的图像问答
    test_image_query()
    
    # 分析图片元数据
    analyze_image_metadata()

if __name__ == "__main__":
    main() 