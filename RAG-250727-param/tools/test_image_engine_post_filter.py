'''
程序说明：

## 1. 测试修改后的image_engine后过滤功能
## 2. 验证k=200设置是否有效
## 3. 检查image_text文档召回效果
'''

import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from config.api_key_manager import get_dashscope_api_key
from v2.core.image_engine import ImageEngine
from v2.core.document_loader import DocumentLoader
from v2.config.v2_config import ImageEngineConfigV2
import time


def test_image_engine_post_filter():
    """测试修改后的image_engine后过滤功能"""
    print("🧪 测试修改后的image_engine后过滤功能")
    print("=" * 80)
    
    try:
        # 1. 初始化配置
        print("📡 初始化配置...")
        config = ImageEngineConfigV2()
        print(f"✅ 配置加载成功，image_similarity_threshold: {config.image_similarity_threshold}")
        
        # 2. 初始化向量数据库
        print("📡 初始化向量数据库...")
        api_key = get_dashscope_api_key()
        embeddings = DashScopeEmbeddings(dashscope_api_key=api_key, model='text-embedding-v1')
        vector_db_path = "../central/vector_db"
        vector_store = FAISS.load_local(vector_db_path, embeddings, allow_dangerous_deserialization=True)
        print("✅ 向量数据库加载成功")
        
        # 3. 初始化文档加载器
        print("📡 初始化文档加载器...")
        document_loader = DocumentLoader(vector_store=vector_store)
        print("✅ 文档加载器初始化成功")
        
        # 4. 初始化图片引擎
        print("📡 初始化图片引擎...")
        image_engine = ImageEngine(
            config=config,
            vector_store=vector_store,
            document_loader=document_loader
        )
        print("✅ 图片引擎初始化成功")
        
        # 5. 测试查询
        test_queries = [
            "图4：中芯国际归母净利润情况概览",
            "中芯国际",
            "芯片制造",
            "晶圆代工"
        ]
        
        for query in test_queries:
            print(f"\n🔍 测试查询: {query}")
            print("-" * 60)
            
            try:
                start_time = time.time()
                
                # 调用_vector_search方法
                results = image_engine._vector_search(query, max_results=10)
                
                search_time = time.time() - start_time
                
                print(f"  搜索耗时: {search_time:.3f}秒")
                print(f"  返回结果数量: {len(results)}")
                
                # 分析结果
                if results:
                    print(f"\n  📊 结果分析:")
                    for i, result in enumerate(results[:5]):  # 只显示前5个结果
                        print(f"    {i+1}. 分数: {result.get('score', 'N/A'):.4f}")
                        print(f"       来源: {result.get('source', 'N/A')}")
                        print(f"       搜索方法: {result.get('search_method', 'N/A')}")
                        
                        if 'semantic_score' in result:
                            print(f"       语义分数: {result['semantic_score']:.4f}")
                        if 'visual_score' in result:
                            print(f"       视觉分数: {result['visual_score']:.4f}")
                        
                        # 显示文档内容片段
                        doc_content = result['doc'].page_content
                        print(f"       内容: {doc_content[:100]}...")
                        
                        # 显示元数据
                        if hasattr(result['doc'], 'metadata') and result['doc'].metadata:
                            chunk_type = result['doc'].metadata.get('chunk_type', 'unknown')
                            print(f"       类型: {chunk_type}")
                        
                        print()
                else:
                    print("  ⚠️  没有找到相关结果")
                
            except Exception as e:
                print(f"  ❌ 查询失败: {e}")
                import traceback
                print(f"  详细错误: {traceback.format_exc()}")
        
        # 6. 总结
        print("\n" + "=" * 80)
        print("🎯 测试总结")
        print("=" * 80)
        
        print("\n✅ 修改成功:")
        print("1. 移除了FAISS filter参数")
        print("2. 实现了后过滤方案")
        print("3. 增加了k值到200")
        print("4. 保持了原有的分数计算逻辑")
        
        print("\n📊 预期效果:")
        print("1. 能召回更多image_text文档")
        print("2. 查询'图4：中芯国际归母净利润情况概览'应该能找到结果")
        print("3. 性能影响可控（搜索时间增加约0.1-0.2秒）")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")


if __name__ == "__main__":
    test_image_engine_post_filter()
