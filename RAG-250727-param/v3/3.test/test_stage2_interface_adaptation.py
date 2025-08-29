"""
第二阶段LangChain改造测试程序 - 接口适配层

测试修改后的vectorization_manager.py是否能正常使用新的LangChain组件：
1. 验证接口兼容性
2. 测试功能完整性
3. 确保向后兼容性
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

def test_interface_adaptation():
    """测试接口适配层"""
    print("🚀 开始第二阶段接口适配层改造测试")
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
        
        # 测试2: 向量化管理器
        print("\n🔧 测试2: 向量化管理器")
        from core.vectorization_manager import VectorizationManager
        
        vectorization_manager = VectorizationManager(config_manager)
        print("✅ 向量化管理器初始化成功")
        
        # 测试3: 获取向量化状态
        print("\n📊 测试3: 获取向量化状态")
        status = vectorization_manager.get_vectorization_status()
        print(f"📊 向量化状态: {status}")
        
        # 测试4: 文本向量化接口
        print("\n📝 测试4: 文本向量化接口")
        test_texts = [
            "人工智能是计算机科学的一个分支",
            "机器学习是人工智能的重要技术",
            "深度学习是机器学习的一个子领域"
        ]
        
        # 准备测试数据
        text_items = []
        for i, text in enumerate(test_texts):
            text_items.append({
                'content': text,
                'metadata': {'source': f'test_{i}', 'timestamp': time.time()}
            })
        
        print(f"📝 开始向量化 {len(text_items)} 个文本...")
        vectorized_texts = vectorization_manager.vectorize_content(text_items, 'text')
        
        if vectorized_texts:
            success_count = len([t for t in vectorized_texts if t.get('vectorization_status') == 'success'])
            print(f"✅ 文本向量化完成: {success_count}/{len(text_items)} 成功")
            
            # 验证结果
            for i, result in enumerate(vectorized_texts):
                if result.get('vectorization_status') == 'success':
                    embedding = result.get('text_embedding', [])
                    print(f"   文本 {i+1}: {len(embedding)} 维向量")
                else:
                    print(f"   文本 {i+1}: 向量化失败 - {result.get('error_message', '未知错误')}")
        else:
            print("❌ 文本向量化失败")
            return False
        
        # 测试5: 表格向量化接口
        print("\n📊 测试5: 表格向量化接口")
        test_tables = [
            "姓名\t年龄\t职业\n张三\t25\t工程师\n李四\t30\t设计师",
            "产品\t价格\t库存\nA产品\t100\t50\nB产品\t200\t30"
        ]
        
        # 准备测试数据
        table_items = []
        for i, table in enumerate(test_tables):
            table_items.append({
                'content': table,
                'metadata': {'source': f'table_{i}', 'timestamp': time.time()}
            })
        
        print(f"📊 开始向量化 {len(table_items)} 个表格...")
        vectorized_tables = vectorization_manager.vectorize_content(table_items, 'table')
        
        if vectorized_tables:
            success_count = len([t for t in vectorized_tables if t.get('vectorization_status') == 'success'])
            print(f"✅ 表格向量化完成: {success_count}/{len(table_items)} 成功")
        else:
            print("❌ 表格向量化失败")
            return False
        
        # 测试6: 完整内容向量化
        print("\n🔗 测试6: 完整内容向量化")
        complete_metadata = {
            'text_chunks': text_items,
            'tables': table_items,
            'images': []  # 暂时不测试图片
        }
        
        print("🔗 开始完整内容向量化...")
        complete_results = vectorization_manager.vectorize_all_content(complete_metadata)
        
        if complete_results:
            print("✅ 完整内容向量化完成")
            
            # 统计结果
            text_count = len(complete_results.get('text_chunks', []))
            table_count = len(complete_results.get('tables', []))
            print(f"📊 处理结果: 文本 {text_count} 个, 表格 {table_count} 个")
        else:
            print("❌ 完整内容向量化失败")
            return False
        
        # 测试7: 验证和统计功能
        print("\n🔍 测试7: 验证和统计功能")
        
        # 验证文本向量化结果
        text_validation = vectorization_manager.validate_vectorization_results(
            complete_results.get('text_chunks', []), 'text'
        )
        print(f"📝 文本向量化验证: {text_validation}")
        
        # 获取文本向量化统计
        text_stats = vectorization_manager.get_vectorization_statistics(
            complete_results.get('text_chunks', []), 'text'
        )
        print(f"📊 文本向量化统计: {text_stats}")
        
        print("\n🎉 第二阶段接口适配层测试完成！")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        logging.error(f"测试错误: {e}", exc_info=True)
        return False

def test_backward_compatibility():
    """测试向后兼容性"""
    print("\n🔄 向后兼容性测试")
    print("=" * 40)
    
    try:
        from config.config_manager import ConfigManager
        from core.vectorization_manager import VectorizationManager
        
        config_manager = ConfigManager()
        vectorization_manager = VectorizationManager(config_manager)
        
        # 测试原有的接口调用方式
        print("📝 测试原有接口调用方式...")
        
        # 测试单个文本向量化
        test_text = "这是一个向后兼容性测试文本"
        text_item = {'content': test_text, 'metadata': {'test': 'backward_compatibility'}}
        
        result = vectorization_manager.vectorize_content([text_item], 'text')
        if result and result[0].get('vectorization_status') == 'success':
            print("✅ 原有接口调用方式正常")
        else:
            print("❌ 原有接口调用方式异常")
            return False
        
        print("✅ 向后兼容性测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 向后兼容性测试失败: {e}")
        logging.error(f"向后兼容性测试错误: {e}", exc_info=True)
        return False

def main():
    """主函数"""
    print("🔧 LangChain改造第二阶段测试程序 - 接口适配层")
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
    
    # 运行接口适配层测试
    if test_interface_adaptation():
        print("\n🎯 接口适配层测试通过，开始向后兼容性测试...")
        
        if test_backward_compatibility():
            print("\n" + "=" * 60)
            print("🎉 第二阶段接口适配层改造测试全部完成！")
            print("✅ 接口适配层功能正常")
            print("✅ 向后兼容性保持")
            print("✅ 系统集成正常")
            print("\n🚀 可以进入第三阶段改造")
        else:
            print("\n❌ 向后兼容性测试失败")
            print("🔧 需要修复兼容性问题后重新测试")
    else:
        print("\n❌ 接口适配层测试失败，请检查错误信息")
        print("🔧 需要修复问题后重新测试")

if __name__ == "__main__":
    main()
