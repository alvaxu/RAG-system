'''
程序说明：
## 1. 测试table_engine的reranking和new pipeline集成
## 2. 验证配置是否正确加载
## 3. 测试reranking服务是否正常工作
## 4. 测试new pipeline是否正常执行
'''

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_table_engine_config():
    """测试table_engine的配置加载"""
    
    print("=" * 60)
    print("🔍 测试TableEngine的配置加载")
    print("=" * 60)
    
    try:
        # 导入配置
        from v2.config.v2_config import TableEngineConfigV2
        
        # 创建配置实例
        config = TableEngineConfigV2()
        
        print("✅ 配置加载成功")
        print(f"引擎名称: {config.name}")
        print(f"最大结果数: {config.max_results}")
        print(f"表格相似度阈值: {config.table_similarity_threshold}")
        print(f"使用新Pipeline: {config.use_new_pipeline}")
        print(f"启用增强重排序: {config.enable_enhanced_reranking}")
        
        # 检查reranking配置
        if config.reranking:
            print("\n📊 Reranking配置:")
            for key, value in config.reranking.items():
                print(f"  {key}: {value}")
        else:
            print("\n⚠️ Reranking配置为空")
        
        # 检查召回策略配置
        if config.recall_strategy:
            print("\n📊 召回策略配置:")
            for layer, layer_config in config.recall_strategy.items():
                print(f"  {layer}: {layer_config}")
        else:
            print("\n⚠️ 召回策略配置为空")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_table_engine_initialization():
    """测试table_engine的初始化"""
    
    print("\n" + "=" * 60)
    print("🔍 测试TableEngine的初始化")
    print("=" * 60)
    
    try:
        # 导入TableEngine
        from v2.core.table_engine import TableEngine
        from v2.config.v2_config import TableEngineConfigV2
        
        # 创建配置
        config = TableEngineConfigV2()
        
        # 创建TableEngine实例（跳过文档加载）
        table_engine = TableEngine(
            config=config,
            vector_store=None,
            document_loader=None,
            skip_initial_load=True
        )
        
        print("✅ TableEngine初始化成功")
        print(f"引擎名称: {table_engine.name}")
        print(f"配置类型: {type(table_engine.config)}")
        print(f"重排序服务: {table_engine.table_reranking_service}")
        
        # 检查配置属性
        print(f"\n📊 配置属性检查:")
        print(f"  enable_enhanced_reranking: {getattr(config, 'enable_enhanced_reranking', 'Not Found')}")
        print(f"  use_new_pipeline: {getattr(config, 'use_new_pipeline', 'Not Found')}")
        print(f"  reranking: {getattr(config, 'reranking', 'Not Found')}")
        
        return True
        
    except Exception as e:
        print(f"❌ TableEngine初始化测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_reranking_service():
    """测试reranking服务"""
    
    print("\n" + "=" * 60)
    print("🔍 测试Reranking服务")
    print("=" * 60)
    
    try:
        # 导入reranking服务
        from v2.core.reranking_services import create_reranking_service
        
        # 创建reranking配置
        reranking_config = {
            "target_count": 10,
            "use_llm_enhancement": True,
            "model_name": "gte-rerank-v2",
            "similarity_threshold": 0.7
        }
        
        # 创建reranking服务
        reranking_service = create_reranking_service('table', reranking_config)
        
        if reranking_service:
            print("✅ Reranking服务创建成功")
            print(f"服务名称: {reranking_service.get_service_name()}")
            print(f"支持类型: {reranking_service.get_supported_types()}")
        else:
            print("❌ Reranking服务创建失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Reranking服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_unified_pipeline():
    """测试unified pipeline"""
    
    print("\n" + "=" * 60)
    print("🔍 测试Unified Pipeline")
    print("=" * 60)
    
    try:
        # 导入unified pipeline
        from v2.core.unified_pipeline import UnifiedPipeline
        
        # 创建pipeline配置
        pipeline_config = {
            'enable_llm_generation': True,
            'enable_source_filtering': True,
            'max_context_results': 10,
            'max_content_length': 1000
        }
        
        # 创建Mock引擎
        from unittest.mock import Mock
        
        llm_engine = Mock()
        llm_engine.generate_answer.return_value = "基于查询和上下文信息生成的答案"
        
        source_filter_engine = Mock()
        source_filter_engine.filter_sources.return_value = [{'content': '测试内容', 'score': 0.8}]
        
        # 创建UnifiedPipeline实例
        pipeline = UnifiedPipeline(
            config=pipeline_config,
            llm_engine=llm_engine,
            source_filter_engine=source_filter_engine
        )
        
        print("✅ UnifiedPipeline创建成功")
        print(f"配置: {pipeline_config}")
        
        # 测试pipeline处理
        test_results = [
            {'content': '测试表格内容1', 'score': 0.9, 'metadata': {'table_type': 'financial'}},
            {'content': '测试表格内容2', 'score': 0.7, 'metadata': {'table_type': 'hr'}}
        ]
        
        pipeline_result = pipeline.process("测试查询", test_results, query_type='table')
        
        if pipeline_result.success:
            print("✅ Pipeline处理成功")
            print(f"LLM答案长度: {len(pipeline_result.llm_answer)}")
            print(f"过滤后源数量: {len(pipeline_result.filtered_sources)}")
        else:
            print(f"❌ Pipeline处理失败: {pipeline_result.error_message}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ UnifiedPipeline测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    
    print("🚀 开始测试TableEngine的Reranking和New Pipeline集成")
    print("=" * 60)
    
    test_results = []
    
    # 测试配置加载
    test_results.append(("配置加载", test_table_engine_config()))
    
    # 测试TableEngine初始化
    test_results.append(("TableEngine初始化", test_table_engine_initialization()))
    
    # 测试Reranking服务
    test_results.append(("Reranking服务", test_reranking_service()))
    
    # 测试Unified Pipeline
    test_results.append(("Unified Pipeline", test_unified_pipeline()))
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！TableEngine的Reranking和New Pipeline集成正常")
    else:
        print("⚠️ 部分测试失败，请检查相关配置和代码")
    
    return passed == total

if __name__ == "__main__":
    main()
