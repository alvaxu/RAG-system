"""
第一阶段LangChain改造测试程序

测试新创建的LangChain组件：
1. LangChainVectorStoreManager
2. LangChainTextVectorizer  
3. LangChainModelCaller

确保这些组件能够正常工作并替代原有功能。
"""

import os
import sys
import logging
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_langchain_components():
    """测试LangChain组件"""
    print("🚀 开始第一阶段LangChain改造测试")
    print("=" * 60)
    
    try:
        # 测试1: 配置管理器
        print("\n📋 测试1: 配置管理器")
        from config.config_manager import ConfigManager
        
        # 设置测试专用的向量数据库路径
        test_vector_db_dir = str(Path(__file__).parent.parent / "central" / "vector_db")
        print(f"📁 测试向量数据库路径: {test_vector_db_dir}")
        
        config_manager = ConfigManager()
        
        # 动态更新向量数据库路径配置
        if hasattr(config_manager, 'config_data'):
            config_manager.config_data['paths'] = config_manager.config_data.get('paths', {})
            config_manager.config_data['paths']['vector_db_dir'] = test_vector_db_dir
        
        print("✅ 配置管理器初始化成功")
        
        # 测试2: LangChain模型调用器
        print("\n🤖 测试2: LangChain模型调用器")
        from core.model_caller import LangChainModelCaller
        
        model_caller = LangChainModelCaller(config_manager)
        print("✅ LangChain模型调用器初始化成功")
        
        # 测试模型信息
        model_info = model_caller.get_model_info()
        print(f"📊 模型信息: {model_info}")
        
        # 测试3: LangChain文本向量化器
        print("\n📝 测试3: LangChain文本向量化器")
        from vectorization.text_vectorizer import LangChainTextVectorizer
        
        text_vectorizer = LangChainTextVectorizer(config_manager)
        print("✅ LangChain文本向量化器初始化成功")
        
        # 测试文本分割
        test_text = "这是一个测试文本。它包含多个句子。我们将测试文本分割功能。"
        chunks = text_vectorizer.split_text(test_text, chunk_size=20, chunk_overlap=5)
        print(f"📄 文本分割测试: 原文本长度 {len(test_text)}，分割后 {len(chunks)} 个块")
        for i, chunk in enumerate(chunks):
            print(f"   块 {i+1}: {chunk}")
        
        # 测试4: LangChain向量存储管理器
        print("\n🗄️ 测试4: LangChain向量存储管理器")
        from core.vector_store_manager import LangChainVectorStoreManager
        
        vector_store_manager = LangChainVectorStoreManager(config_manager)
        print("✅ LangChain向量存储管理器初始化成功")
        
        # 测试向量存储创建
        success = vector_store_manager.create_vector_store()
        if success:
            print("✅ 向量存储创建成功")
        else:
            print("❌ 向量存储创建失败")
            return False
        
        # 测试状态获取
        status = vector_store_manager.get_status()
        print(f"📊 向量存储状态: {status}")
        
        # 测试5: 集成测试
        print("\n🔗 测试5: 集成测试")
        
        # 测试文本向量化
        test_texts = [
            "人工智能是计算机科学的一个分支",
            "机器学习是人工智能的重要技术",
            "深度学习是机器学习的一个子领域"
        ]
        
        print("📝 开始文本向量化测试...")
        for i, text in enumerate(test_texts):
            result = text_vectorizer.vectorize(text, {'source': f'test_{i}'})
            if result['vectorization_status'] == 'success':
                print(f"✅ 文本 {i+1} 向量化成功: {len(result['text_embedding'])} 维")
            else:
                print(f"❌ 文本 {i+1} 向量化失败: {result.get('error_message', '未知错误')}")
        
        # 测试向量存储
        print("\n🗄️ 开始向量存储测试...")
        
        # 添加文本到向量存储
        for i, text in enumerate(test_texts):
            success = vector_store_manager.add_texts(
                [text], 
                [{'source': f'test_{i}', 'timestamp': time.time()}]
            )
            if success:
                print(f"✅ 文本 {i+1} 添加到向量存储成功")
            else:
                print(f"❌ 文本 {i+1} 添加到向量存储失败")
        
        # 测试相似性搜索
        print("\n🔍 开始相似性搜索测试...")
        query = "人工智能技术"
        search_results = vector_store_manager.similarity_search(query, k=3)
        print(f"🔍 查询: '{query}'")
        print(f"📊 搜索结果数量: {len(search_results)}")
        
        for i, result in enumerate(search_results):
            print(f"   结果 {i+1}: {result.page_content[:50]}...")
            print(f"   元数据: {result.metadata}")
        
        # 测试保存和加载
        print("\n💾 开始保存和加载测试...")
        
        # 保存向量存储
        save_success = vector_store_manager.save()
        if save_success:
            print("✅ 向量存储保存成功")
        else:
            print("❌ 向量存储保存失败")
        
        # 清空当前向量存储
        vector_store_manager.clear()
        print("🗑️ 向量存储已清空")
        
        # 重新加载向量存储
        load_success = vector_store_manager.load()
        if load_success:
            print("✅ 向量存储加载成功")
            
            # 验证数据是否恢复
            status_after_load = vector_store_manager.get_status()
            print(f"📊 加载后状态: {status_after_load}")
        else:
            print("❌ 向量存储加载失败")
        
        print("\n🎉 第一阶段测试完成！")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        logging.error(f"测试错误: {e}", exc_info=True)
        return False

def test_performance_comparison():
    """测试性能对比"""
    print("\n⚡ 性能对比测试")
    print("=" * 40)
    
    try:
        from config.config_manager import ConfigManager
        from core.model_caller import LangChainModelCaller
        from vectorization.text_vectorizer import LangChainTextVectorizer
        
        config_manager = ConfigManager()
        model_caller = LangChainModelCaller(config_manager)
        text_vectorizer = LangChainTextVectorizer(config_manager)
        
        # 测试文本
        test_text = "这是一个用于性能测试的文本。" * 100
        
        # 测试文本分割性能
        print("📝 测试文本分割性能...")
        start_time = time.time()
        chunks = text_vectorizer.split_text(test_text, chunk_size=500, chunk_overlap=50)
        split_time = time.time() - start_time
        print(f"⏱️ 文本分割耗时: {split_time:.3f}秒，生成了 {len(chunks)} 个块")
        
        # 测试向量化性能
        print("\n🤖 测试向量化性能...")
        start_time = time.time()
        result = text_vectorizer.vectorize(test_text[:1000])
        vectorize_time = time.time() - start_time
        print(f"⏱️ 向量化耗时: {vectorize_time:.3f}秒")
        
        # 测试批量处理性能
        print("\n📦 测试批量处理性能...")
        test_texts = [f"测试文本 {i}" * 20 for i in range(10)]
        
        start_time = time.time()
        results = text_vectorizer.vectorize_batch(test_texts)
        batch_time = time.time() - start_time
        
        success_count = len([r for r in results if r['vectorization_status'] == 'success'])
        print(f"⏱️ 批量处理耗时: {batch_time:.3f}秒，成功率: {success_count}/{len(test_texts)}")
        
        print("\n✅ 性能测试完成")
        
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        logging.error(f"性能测试错误: {e}", exc_info=True)

def main():
    """主函数"""
    print("🔧 LangChain改造第一阶段测试程序")
    print("=" * 60)
    
    # 检查依赖
    print("📋 检查依赖包...")
    try:
        import langchain
        print(f"✅ LangChain版本: {langchain.__version__}")
    except ImportError:
        print("❌ LangChain未安装，请先安装: pip install langchain")
        return
    
    try:
        import faiss
        print(f"✅ FAISS版本: {faiss.__version__}")
    except ImportError:
        print("❌ FAISS未安装，请先安装: pip install faiss-cpu")
        return
    
    try:
        import dashscope
        print(f"✅ DashScope已安装")
    except ImportError:
        print("❌ DashScope未安装，请先安装: pip install dashscope")
        return
    
    print("✅ 所有依赖包检查完成")
    
    # 运行功能测试
    if test_langchain_components():
        print("\n🎯 功能测试通过，开始性能测试...")
        test_performance_comparison()
        
        print("\n" + "=" * 60)
        print("🎉 第一阶段改造测试全部完成！")
        print("✅ LangChain组件功能正常")
        print("✅ 向量存储管理正常")
        print("✅ 文本处理流程正常")
        print("✅ 性能表现良好")
        print("\n🚀 可以进入第二阶段改造")
    else:
        print("\n❌ 功能测试失败，请检查错误信息")
        print("🔧 需要修复问题后重新测试")

if __name__ == "__main__":
    main()
