"""
程序说明：
## 1. 检查重排序引擎的配置
## 2. 验证min_similarity_threshold的值
## 3. 测试重排序功能
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.enhanced_qa_system import load_enhanced_qa_system
from config.settings import Settings

def debug_reranking_config():
    """检查重排序引擎配置"""
    print("🔧 检查重排序引擎配置...")
    print("=" * 50)
    
    # 加载配置
    settings = Settings.load_from_file("config.json")
    api_key = settings.dashscope_api_key
    
    if not api_key or api_key == '你的APIKEY':
        print("❌ 错误: 未配置DashScope API密钥")
        return
    
    # 加载QA系统
    vector_db_path = "./central/vector_db"
    qa_system = load_enhanced_qa_system(vector_db_path, api_key)
    
    if not qa_system:
        print("❌ 错误: QA系统加载失败")
        return
    
    print("✅ QA系统加载成功")
    
    # 检查配置
    print("\n📋 检查配置...")
    vector_config = qa_system.config.get('vector_store', {})
    print(f"向量存储配置: {vector_config}")
    
    # 检查重排序引擎
    if qa_system.reranking_engine:
        print(f"\n📋 重排序引擎配置:")
        print(f"   启用重排序: {qa_system.reranking_engine.enable_reranking}")
        print(f"   重排序方法: {qa_system.reranking_engine.reranking_method}")
        print(f"   语义权重: {qa_system.reranking_engine.semantic_weight}")
        print(f"   关键词权重: {qa_system.reranking_engine.keyword_weight}")
        print(f"   最小相似度阈值: {qa_system.reranking_engine.min_similarity_threshold}")
    else:
        print("❌ 重排序引擎未初始化")
    
    # 测试重排序
    print("\n📋 测试重排序...")
    test_docs = [
        {
            'content': '中芯国际是世界领先的集成电路晶圆代工企业之一，主要业务是晶圆代工服务。',
            'metadata': {'document_name': '测试文档1'},
            'score': 0.8
        },
        {
            'content': '中芯国际提供8英寸和12英寸晶圆代工与技术服务，总部位于上海。',
            'metadata': {'document_name': '测试文档2'},
            'score': 0.7
        }
    ]
    
    test_question = "中芯国际的主要业务是什么？"
    
    try:
        reranked_docs = qa_system.reranking_engine.rerank_results(test_question, test_docs)
        print(f"✅ 重排序完成，结果数量: {len(reranked_docs)}")
        
        for i, doc in enumerate(reranked_docs, 1):
            print(f"   文档 {i}: 分数={doc.get('rerank_score', 0):.3f}, 内容={doc['content'][:50]}...")
            
    except Exception as e:
        print(f"❌ 重排序测试失败: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 配置检查完成")

if __name__ == "__main__":
    debug_reranking_config() 