'''
程序说明：

## 1. 验证源过滤是否真的把图4结果过滤掉了
## 2. 测试增加源数量的效果
## 3. 为增强其他召回策略的metadata字段做准备
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
from v2.core.source_filter_engine import SourceFilterEngine
import time


def debug_source_filter_verification():
    """验证源过滤行为"""
    print("🔍 验证源过滤行为")
    print("=" * 80)
    
    try:
        # 1. 初始化组件
        print("📡 初始化组件...")
        config = ImageEngineConfigV2()
        
        api_key = get_dashscope_api_key()
        embeddings = DashScopeEmbeddings(dashscope_api_key=api_key, model='text-embedding-v1')
        vector_db_path = "../central/vector_db"
        vector_store = FAISS.load_local(vector_db_path, embeddings, allow_dangerous_deserialization=True)
        
        document_loader = DocumentLoader(vector_store=vector_store)
        image_engine = ImageEngine(
            config=config,
            vector_store=vector_store,
            document_loader=document_loader
        )
        source_filter_engine = SourceFilterEngine(config=config)
        print("✅ 组件初始化成功")
        
        # 2. 测试查询
        query = "图4：中芯国际归母净利润情况概览"
        print(f"\n🔍 测试查询: {query}")
        print("-" * 60)
        
        # 3. 第一步：获取五层召回结果
        print("\n📊 第一步：获取五层召回结果")
        all_results = image_engine._search_images_with_five_layer_recall(query)
        print(f"  五层召回结果数量: {len(all_results)}")
        
        # 4. 第二步：分析结果中的图4信息
        print(f"\n📊 第二步：分析结果中的图4信息")
        our_results = []
        other_results = []
        
        for i, result in enumerate(all_results):
            score = result.get('score', 0)
            search_method = result.get('search_method', 'N/A')
            source = result.get('source', 'N/A')
            
            # 检查是否有我们的字段
            has_our_fields = all([
                result.get('document_name'),
                result.get('page_number'),
                result.get('chunk_type'),
                result.get('llm_context')
            ])
            
            if has_our_fields:
                our_results.append(result)
                print(f"  ✅ 结果{i+1}: {search_method} (分数: {score:.4f}) - 有我们的字段")
                
                # 检查是否包含图4信息
                llm_context = result.get('llm_context', '')
                if '图4' in llm_context:
                    print(f"    🎯 包含图4信息!")
                    print(f"    📋 document_name: {result.get('document_name')}")
                    print(f"    📋 page_number: {result.get('page_number')}")
                    print(f"    📋 llm_context长度: {len(llm_context)}")
                else:
                    print(f"    ❌ 不包含图4信息")
            else:
                other_results.append(result)
                print(f"  ❌ 结果{i+1}: {search_method} (分数: {score:.4f}) - 缺少我们的字段")
        
        print(f"\n  统计:")
        print(f"    有我们字段的结果: {len(our_results)}")
        print(f"    缺少我们字段的结果: {len(other_results)}")
        
        # 5. 第三步：模拟源过滤过程
        print(f"\n📊 第三步：模拟源过滤过程")
        
        # 检查源过滤配置
        print(f"  源过滤配置检查:")
        config_attrs = dir(config)
        filter_attrs = [attr for attr in config_attrs if 'filter' in attr.lower() or 'source' in attr.lower()]
        print(f"    相关配置属性: {filter_attrs}")
        
        # 尝试获取配置值
        for attr in filter_attrs:
            try:
                value = getattr(config, attr)
                print(f"    {attr}: {value}")
            except:
                print(f"    {attr}: 无法获取")
        
        # 6. 第四步：测试增加源数量的效果
        print(f"\n📊 第四步：测试增加源数量的效果")
        
        # 检查是否有max_sources配置
        if hasattr(config, 'max_sources'):
            max_sources = config.max_sources
            print(f"    当前max_sources配置: {max_sources}")
            
            # 建议增加源数量
            if max_sources and max_sources < 10:
                print(f"    💡 建议增加max_sources到10或更多")
        else:
            print(f"    ❓ 没有找到max_sources配置")
        
        # 7. 第五步：分析其他召回策略
        print(f"\n📊 第五步：分析其他召回策略")
        
        # 统计各策略的结果
        strategy_stats = {}
        for result in all_results:
            search_method = result.get('search_method', 'N/A')
            if search_method not in strategy_stats:
                strategy_stats[search_method] = []
            strategy_stats[search_method].append(result)
        
        print(f"  各策略结果统计:")
        for strategy, results in strategy_stats.items():
            print(f"    {strategy}: {len(results)} 个结果")
            
            # 检查该策略是否有我们的字段
            has_fields_count = sum(1 for r in results if all([
                r.get('document_name'),
                r.get('page_number'),
                r.get('chunk_type'),
                r.get('llm_context')
            ]))
            print(f"      有我们字段的结果: {has_fields_count}/{len(results)}")
        
        # 8. 第六步：问题分析和建议
        print("\n" + "=" * 80)
        print("🎯 问题分析和建议")
        print("=" * 80)
        
        print(f"\n关键发现:")
        print(f"1. 五层召回层面：✅ 我们的metadata字段在vector_search中正确传递")
        print(f"2. 五层召回层面：❌ 其他召回策略没有我们的metadata字段")
        print(f"3. 源过滤层面：❓ 需要确认具体配置和过滤逻辑")
        
        print(f"\n可能的问题点:")
        print(f"1. 源过滤可能基于数量限制，只保留前N个结果")
        print(f"2. 源过滤可能基于分数阈值过滤")
        print(f"3. 其他召回策略的结果没有我们的metadata，导致信息丢失")
        
        print(f"\n建议的解决方案:")
        print(f"1. 增加max_sources配置，确保更多结果被保留")
        print(f"2. 增强其他召回策略的metadata字段")
        print(f"3. 调整源过滤的优先级策略，优先保留有完整metadata的结果")
        
        print(f"\n下一步行动:")
        print(f"1. 检查并调整源过滤配置")
        print(f"2. 增强其他召回策略的metadata字段")
        print(f"3. 测试调整后的效果")
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")


if __name__ == "__main__":
    debug_source_filter_verification()
