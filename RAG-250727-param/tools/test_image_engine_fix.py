'''
程序说明：
## 1. 测试修改后的image_engine功能
## 2. 验证内容相关性计算是否正常工作
## 3. 验证阈值调整是否解决召回问题
## 4. 对比修改前后的效果
'''

import os
import sys
import json
from typing import Dict, Any, List

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from config.api_key_manager import get_dashscope_api_key
from v2.config.v2_config import ImageEngineConfigV2
from v2.core.image_engine import ImageEngine
from v2.core.document_loader import DocumentLoader


def test_image_engine_fix():
    """测试修改后的image_engine功能"""
    print("🔧 测试修改后的image_engine功能")
    print("=" * 80)
    
    try:
        # 1. 获取API密钥
        print("🔑 获取API密钥...")
        api_key = get_dashscope_api_key()
        if not api_key:
            print("❌ 未找到有效的DashScope API密钥")
            return
        
        print("✅ API密钥获取成功")
        
        # 2. 初始化embeddings
        print("\n🚀 初始化embeddings...")
        embeddings = DashScopeEmbeddings(dashscope_api_key=api_key, model='text-embedding-v1')
        print("✅ embeddings初始化成功")
        
        # 3. 加载向量数据库
        print("\n📚 加载向量数据库...")
        vector_db_path = "../central/vector_db"
        print(f"📁 向量数据库路径: {os.path.abspath(vector_db_path)}")
        
        vector_store = FAISS.load_local(vector_db_path, embeddings, allow_dangerous_deserialization=True)
        print("✅ 向量数据库加载成功")
        
        # 4. 创建ImageEngine配置
        print("\n⚙️ 创建ImageEngine配置...")
        image_config = ImageEngineConfigV2(
            enabled=True,
            max_results=20,
            image_similarity_threshold=0.1,  # 使用新的阈值
            enable_vector_search=True,
            enable_keyword_search=True,
            max_recall_results=150,
            use_new_pipeline=False,
            enable_enhanced_reranking=False
        )
        
        print(f"✅ ImageEngine配置创建成功")
        print(f"  - 新阈值: {image_config.image_similarity_threshold}")
        
        # 5. 初始化ImageEngine
        print("\n🖼️ 初始化ImageEngine...")
        document_loader = DocumentLoader(vector_store=vector_store)
        image_engine = ImageEngine(
            config=image_config,
            vector_store=vector_store,
            document_loader=document_loader,
            skip_initial_load=True  # 跳过文档加载以节省时间
        )
        print("✅ ImageEngine初始化成功")
        
        # 6. 测试查询
        print("\n🔍 测试查询...")
        test_queries = [
            "图4：中芯国际归母净利润情况概览",  # 完美匹配测试
            "产能利用率",  # 部分匹配测试
            "中芯国际净利润",  # 语义匹配测试
        ]
        
        for query in test_queries:
            print(f"\n📝 测试查询: '{query}'")
            print("-" * 60)
            
            try:
                # 调用向量搜索方法 - 增加搜索数量进行调试
                vector_results = image_engine._vector_search(query, max_results=30)
                
                print(f"🔍 向量搜索结果: {len(vector_results)} 个")
                
                if vector_results:
                    print("📊 结果详情:")
                    for i, result in enumerate(vector_results[:3]):  # 只显示前3个
                        score = result.get('score', 0)
                        source = result.get('source', 'unknown')
                        method = result.get('search_method', 'unknown')
                        
                        print(f"  {i+1}. 分数: {score:.4f}")
                        print(f"     来源: {source}")
                        print(f"     方法: {method}")
                        
                        # 显示文档内容片段
                        doc = result.get('doc')
                        if doc and hasattr(doc, 'page_content'):
                            content = doc.page_content[:150] + "..." if len(doc.page_content) > 150 else doc.page_content
                            print(f"     内容: {content}")
                        print()
                    
                    # 分析分数分布
                    scores = [r.get('score', 0) for r in vector_results]
                    min_score = min(scores) if scores else 0
                    max_score = max(scores) if scores else 0
                    avg_score = sum(scores) / len(scores) if scores else 0
                    
                    print(f"📈 分数统计:")
                    print(f"  - 最小分数: {min_score:.4f}")
                    print(f"  - 最大分数: {max_score:.4f}")
                    print(f"  - 平均分数: {avg_score:.4f}")
                    print(f"  - 超过阈值0.1的结果: {len([s for s in scores if s >= 0.1])}/{len(scores)}")
                else:
                    print("⚠️ 没有找到任何结果")
                    
            except Exception as e:
                print(f"❌ 查询失败: {e}")
                import traceback
                print(f"详细错误: {traceback.format_exc()}")
        
        # 7. 测试内容相关性计算函数
        print(f"\n🧮 测试内容相关性计算函数...")
        test_cases = [
            ("图4：中芯国际归母净利润情况概览", "图片标题: 图4：中芯国际归母净利润情况概览 | 图片脚注: 资料来源：iFinD，上海证券研究所"),
            ("产能利用率", "图片标题: 图9：公司季度产能利用率 | 基础视觉描述: 这张图片是一张折线图"),
            ("无关查询", "完全无关的内容")
        ]
        
        for query, content in test_cases:
            score = image_engine._calculate_content_relevance(query, content)
            print(f"  查询: '{query}' -> 分数: {score:.4f}")
        
        # 8. 总结
        print("\n" + "=" * 80)
        print("🎯 测试总结")
        print("=" * 80)
        
        print("\n📋 修改内容:")
        print("1. ✅ 添加了_calculate_content_relevance函数")
        print("2. ✅ 修改了所有向量搜索中的分数计算逻辑")
        print("3. ✅ 调整了阈值从0.05到0.1")
        
        print("\n💡 预期效果:")
        print("1. 解决150个候选结果全部被过滤掉的问题")
        print("2. 提高image_text文档的召回率")
        print("3. 获得合理的相似度分数分布")
        
        print("\n🔧 建议下一步:")
        print("1. 使用V800_v2_main.py运行完整测试")
        print("2. 测试实际的用户查询场景")
        print("3. 根据效果调整阈值和权重")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")


if __name__ == "__main__":
    test_image_engine_fix()
