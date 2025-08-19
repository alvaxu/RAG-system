'''
程序说明：

## 1. 专门调试源过滤逻辑
## 2. 分析五层召回的完整结果排序
## 3. 追踪为什么图4结果被过滤掉
## 4. 检查最终传递给LLM的上下文来源
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


def debug_source_filter_deep():
    """深度调试源过滤逻辑"""
    print("🔍 深度调试源过滤逻辑")
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
        
        # 3. 第一步：获取完整的五层召回结果并分析
        print("\n📊 第一步：获取完整的五层召回结果并分析")
        try:
            all_results = image_engine._search_images_with_five_layer_recall(query)
            print(f"  五层召回结果数量: {len(all_results)}")
            
            if all_results:
                print(f"\n  完整结果分析:")
                
                # 按分数排序
                sorted_results = sorted(all_results, key=lambda x: x.get('score', 0), reverse=True)
                
                # 统计各策略的结果
                strategy_stats = {}
                metadata_stats = {
                    'has_our_fields': 0,
                    'missing_our_fields': 0
                }
                
                for i, result in enumerate(sorted_results):
                    score = result.get('score', 0)
                    search_method = result.get('search_method', 'N/A')
                    source = result.get('source', 'N/A')
                    
                    print(f"    结果{i+1} (分数: {score:.4f}):")
                    print(f"      搜索方法: {search_method}")
                    print(f"      来源: {source}")
                    
                    # 统计策略
                    if search_method not in strategy_stats:
                        strategy_stats[search_method] = 0
                    strategy_stats[search_method] += 1
                    
                    # 检查我们的字段
                    has_our_fields = all([
                        result.get('document_name'),
                        result.get('page_number'),
                        result.get('chunk_type'),
                        result.get('llm_context')
                    ])
                    
                    if has_our_fields:
                        metadata_stats['has_our_fields'] += 1
                        print(f"      ✅ 有我们的字段:")
                        print(f"        document_name: {result.get('document_name')}")
                        print(f"        page_number: {result.get('page_number')}")
                        print(f"        chunk_type: {result.get('chunk_type')}")
                        print(f"        llm_context长度: {len(result.get('llm_context', ''))}")
                        
                        # 检查是否包含图4信息
                        llm_context = result.get('llm_context', '')
                        if '图4' in llm_context:
                            print(f"        🎯 包含图4信息!")
                        else:
                            print(f"        ❌ 不包含图4信息")
                    else:
                        metadata_stats['missing_our_fields'] += 1
                        print(f"      ❌ 缺少我们的字段")
                        
                        # 检查doc内容
                        if 'doc' in result:
                            doc = result['doc']
                            print(f"      📄 doc内容: {doc.page_content[:100]}...")
                            if hasattr(doc, 'metadata') and doc.metadata:
                                print(f"      📄 doc元数据: {doc.metadata}")
                    
                    print()
                
                # 统计总结
                print(f"  📊 统计总结:")
                print(f"    策略分布: {strategy_stats}")
                print(f"    字段完整性: {metadata_stats}")
                
        except Exception as e:
            print(f"  五层召回分析失败: {e}")
            import traceback
            print(f"  详细错误: {traceback.format_exc()}")
        
        # 4. 第二步：模拟源过滤过程
        print(f"\n📊 第二步：模拟源过滤过程")
        try:
            if all_results:
                print(f"  输入结果数量: {len(all_results)}")
                
                # 检查源过滤配置
                print(f"  源过滤配置:")
                print(f"    enable_filtering: {config.enable_filtering}")
                print(f"    min_relevance_score: {getattr(config, 'min_relevance_score', 'N/A')}")
                print(f"    max_sources: {getattr(config, 'max_sources', 'N/A')}")
                
                # 模拟源过滤（不调用LLM，只检查逻辑）
                print(f"\n  模拟源过滤逻辑:")
                
                # 检查每个结果的分数
                scores = [r.get('score', 0) for r in all_results]
                print(f"    分数范围: {min(scores):.4f} - {max(scores):.4f}")
                print(f"    平均分数: {sum(scores)/len(scores):.4f}")
                
                # 检查是否有低分结果
                low_score_results = [r for r in all_results if r.get('score', 0) < 0.5]
                if low_score_results:
                    print(f"    低分结果数量: {len(low_score_results)}")
                    for r in low_score_results[:3]:
                        print(f"      分数: {r.get('score', 0):.4f}, 方法: {r.get('search_method', 'N/A')}")
                
                # 检查我们的图4结果
                our_results = [r for r in all_results if all([
                    r.get('document_name'),
                    r.get('page_number'),
                    r.get('chunk_type'),
                    r.get('llm_context')
                ])]
                
                print(f"\n    我们的结果分析:")
                print(f"      数量: {len(our_results)}")
                for r in our_results:
                    print(f"      分数: {r.get('score', 0):.4f}, 方法: {r.get('search_method', 'N/A')}")
                    if '图4' in r.get('llm_context', ''):
                        print(f"        🎯 包含图4信息!")
                    else:
                        print(f"        ❌ 不包含图4信息")
                
        except Exception as e:
            print(f"  模拟源过滤失败: {e}")
            import traceback
            print(f"  详细错误: {traceback.format_exc()}")
        
        # 5. 第三步：检查源过滤引擎的具体实现
        print(f"\n📊 第三步：检查源过滤引擎的具体实现")
        try:
            # 查看filter_sources方法的完整实现
            import inspect
            source = inspect.getsource(source_filter_engine.filter_sources)
            print(f"  filter_sources方法完整实现:")
            lines = source.split('\n')
            
            # 显示关键部分
            key_sections = []
            for i, line in enumerate(lines):
                if any(keyword in line.lower() for keyword in ['score', 'filter', 'threshold', 'min', 'max']):
                    key_sections.append((i+1, line))
            
            for line_num, line in key_sections:
                print(f"    {line_num:2d}: {line}")
            
            # 显示方法结尾
            print(f"  ...")
            for i in range(max(0, len(lines)-10), len(lines)):
                print(f"    {i+1:2d}: {lines[i]}")
                
        except Exception as e:
            print(f"  源过滤引擎检查失败: {e}")
            import traceback
            print(f"  详细错误: {traceback.format_exc()}")
        
        # 6. 第四步：问题分析
        print("\n" + "=" * 80)
        print("🎯 深度问题分析")
        print("=" * 80)
        
        print(f"\n关键发现:")
        print(f"1. 五层召回层面：✅ 我们的metadata字段在vector_search中正确传递")
        print(f"2. 五层召回层面：❌ 其他召回策略没有我们的metadata字段")
        print(f"3. 源过滤层面：❓ 需要确认过滤规则和阈值")
        
        print(f"\n可能的问题点:")
        print(f"1. 源过滤可能基于分数过滤，我们的结果分数不够高")
        print(f"2. 源过滤可能基于数量限制，只保留前N个结果")
        print(f"3. 最终LLM上下文可能来自其他召回策略的结果")
        print(f"4. 我们的图4信息虽然被召回，但在后续处理中被丢弃")
        
        print(f"\n建议的调试方向:")
        print(f"1. 检查源过滤的具体阈值和规则")
        print(f"2. 确认最终传递给LLM的上下文来源")
        print(f"3. 检查是否需要增强其他召回策略的metadata")
        print(f"4. 考虑调整源过滤的优先级策略")
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")


if __name__ == "__main__":
    debug_source_filter_deep()
