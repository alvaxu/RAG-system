'''
程序说明：
## 1. 测试阶段一参数调整的效果
## 2. 验证向量检索参数从5调整为3的影响
## 3. 测试图片搜索的相关性改进
## 4. 对比调整前后的搜索结果差异
'''

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from config.config_manager import ConfigManager
from core.qa_system import QASystem
from core.memory_manager import MemoryManager
from core.vector_store import VectorStoreManager


def test_optimized_parameters():
    """
    测试优化后的参数设置
    """
    print("=== 测试阶段一参数调整效果 ===")
    
    # 获取配置管理器
    config_manager = ConfigManager()
    
    # 打印当前配置
    print("\n当前配置:")
    print(f"相似度Top-K: {config_manager.settings.similarity_top_k}")
    print(f"向量维度: {config_manager.settings.vector_dimension}")
    
    # 获取API密钥
    api_key = config_manager.settings.dashscope_api_key
    if not api_key or api_key == '你的DashScope API密钥':
        print("错误: 未配置有效的DashScope API密钥")
        return
    
    # 获取向量存储路径
    vector_db_path = config_manager.settings.get_vector_db_path()
    print(f"向量存储路径: {vector_db_path}")
    
    # 初始化向量存储管理器
    vector_store_manager = VectorStoreManager(api_key)
    
    # 加载向量存储
    vector_store = vector_store_manager.load_vector_store(vector_db_path)
    if not vector_store:
        print("错误: 无法加载向量存储")
        return
    
    # 验证向量存储
    if not vector_store_manager.validate_vector_store(vector_store):
        print("错误: 向量存储验证失败")
        return
    
    # 获取统计信息
    stats = vector_store_manager.get_vector_store_statistics(vector_store)
    print(f"\n向量存储统计:")
    print(f"总文档数: {stats.get('total_documents', 0)}")
    print(f"文档类型: {stats.get('document_types', {})}")
    
    # 初始化记忆管理器
    memory_manager = MemoryManager(config_manager.settings.get_memory_db_path())
    
    # 初始化问答系统
    qa_system = QASystem(vector_store, api_key, memory_manager)
    
    # 测试查询
    test_queries = [
        "文档中有没有关于个股走势表现的图",
        "公司营业收入情况",
        "毛利率和净利率图表"
    ]
    
    print("\n=== 测试查询结果 ===")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. 查询: {query}")
        print("-" * 50)
        
        # 执行查询
        result = qa_system.answer_question(query, k=3)
        
        # 打印结果
        print(f"回答: {result.get('answer', '无回答')}")
        print(f"来源数量: {len(result.get('sources', []))}")
        
        # 打印来源详情
        sources = result.get('sources', [])
        if sources:
            print("来源详情:")
            for j, source in enumerate(sources, 1):
                metadata = source.get('metadata', {})
                chunk_type = metadata.get('chunk_type', 'unknown')
                image_id = metadata.get('image_id', 'N/A')
                document_name = metadata.get('document_name', '未知文档')
                
                print(f"  {j}. 类型: {chunk_type}")
                if chunk_type == 'image':
                    print(f"     图片ID: {image_id}")
                print(f"     文档: {document_name}")
                print(f"     内容: {source.get('content', '')[:100]}...")
        
        print(f"成本: {result.get('cost', 0.0)}")
    
    print("\n=== 参数调整总结 ===")
    print("✅ 相似度Top-K从5调整为3")
    print("✅ answer_question默认k从5调整为3")
    print("✅ _search_images默认k从10调整为3")
    print("✅ answer_with_memory默认k从10调整为3")
    print("✅ API路由默认k从5调整为3")
    print("✅ 向量存储搜索默认k从5调整为3")
    
    print("\n预期效果:")
    print("- 减少无关图片的显示")
    print("- 提高搜索结果的相关性")
    print("- 减少重复内容")
    print("- 提升用户体验")


def test_image_search_specific():
    """
    专门测试图片搜索功能
    """
    print("\n=== 专门测试图片搜索 ===")
    
    # 获取配置管理器
    config_manager = ConfigManager()
    api_key = config_manager.settings.dashscope_api_key
    
    if not api_key or api_key == '你的DashScope API密钥':
        print("错误: 未配置有效的DashScope API密钥")
        return
    
    # 初始化向量存储管理器
    vector_store_manager = VectorStoreManager(api_key)
    vector_db_path = config_manager.settings.get_vector_db_path()
    vector_store = vector_store_manager.load_vector_store(vector_db_path)
    
    if not vector_store:
        print("错误: 无法加载向量存储")
        return
    
    # 测试图片搜索
    image_query = "个股走势表现"
    print(f"图片搜索查询: {image_query}")
    
    # 使用不同的k值进行对比
    k_values = [3, 5, 10]
    
    for k in k_values:
        print(f"\n--- k={k} 的搜索结果 ---")
        results = vector_store_manager.search_similar(vector_store, image_query, k=k)
        
        print(f"找到 {len(results)} 个结果:")
        for i, result in enumerate(results, 1):
            metadata = result.get('metadata', {})
            chunk_type = metadata.get('chunk_type', 'unknown')
            image_id = metadata.get('image_id', 'N/A')
            content = result.get('content', '')[:100]
            
            print(f"  {i}. 类型: {chunk_type}")
            if chunk_type == 'image':
                print(f"     图片ID: {image_id}")
            print(f"     内容: {content}...")


if __name__ == "__main__":
    try:
        test_optimized_parameters()
        test_image_search_specific()
        print("\n✅ 阶段一参数调整测试完成")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc() 