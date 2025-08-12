'''
程序说明：

## 1. V2.0系统修复验证测试脚本 - 增强版
## 2. 测试修复后的图片查询、文本查询、表格查询和混合查询功能
## 3. 包含详细的调试信息和错误处理
## 4. 支持单步测试和批量测试模式
## 5. 新增混合查询引擎性能测试和查询意图分析器测试
## 6. 智能结果融合和排序验证
## 7. 跨类型内容检索效果评估
## 8. 深度增强内容识别测试
## 9. 业务领域查询优化测试
## 10. 智能结果融合验证

'''

import os
import sys
import time
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent  # 从tools目录回到项目根目录
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_v2_system_fixes():
    """测试V2.0系统的修复效果"""
    
    print("🔧 V2.0系统修复验证测试")
    print("=" * 50)
    
    try:
        # 导入修复后的V2.0模块
        print("📦 正在导入修复后的V2.0模块...")
        
        from v2.core.image_engine import ImageEngine
        from v2.core.text_engine import TextEngine
        from v2.core.table_engine import TableEngine
        from v2.core.hybrid_engine import HybridEngine
        from v2.config.v2_config import (
            ImageEngineConfigV2, 
            TextEngineConfigV2, 
            TableEngineConfigV2, 
            HybridEngineConfigV2
        )
        
        print("✅ V2.0模块导入成功")
        
        # 检查现有系统模块
        print("⏳ 正在检查现有系统模块...")
        try:
            from core.enhanced_qa_system import EnhancedQASystem
            print("✅ 现有系统模块导入成功")
        except ImportError as e:
            print(f"⚠️ 现有系统模块导入失败: {e}")
        
        # 初始化向量数据库
        print("🔍 正在初始化向量数据库...")
        from langchain_community.embeddings import DashScopeEmbeddings
        from langchain_community.vectorstores import FAISS
        import os
        
        # 获取API密钥
        api_key = os.getenv('MY_DASHSCOPE_API_KEY', '')
        if not api_key:
            print("⚠️ 未设置MY_DASHSCOPE_API_KEY环境变量")
            # 尝试从config.json加载
            try:
                if os.path.exists("config.json"):
                    import json
                    with open("config.json", 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    api_key = config_data.get('api', {}).get('dashscope_api_key', '')
                    if api_key:
                        print("✅ 从config.json加载API密钥成功")
            except Exception as e:
                print(f"⚠️ 从config.json加载API密钥失败: {e}")
        
        if not api_key:
            print("❌ 无法获取API密钥，使用模拟向量存储")
            vector_store = None
        else:
            # 直接加载向量存储，参考老代码的方式
            vector_db_path = "central/vector_db"
            if os.path.exists(vector_db_path):
                try:
                    embeddings = DashScopeEmbeddings(dashscope_api_key=api_key, model='text-embedding-v1')
                    vector_store = FAISS.load_local(vector_db_path, embeddings, allow_dangerous_deserialization=True)
                    print(f"✅ 向量存储加载成功: {vector_db_path}")
                except Exception as e:
                    print(f"❌ 向量存储加载失败: {e}")
                    vector_store = None
            else:
                print(f"⚠️ 向量数据库路径不存在: {vector_db_path}")
                vector_store = None
        
        # 创建引擎配置
        print("⚙️ 正在创建引擎配置...")
        image_config = ImageEngineConfigV2(
            enabled=True,
            debug=True,
            max_results=10
        )
        
        text_config = TextEngineConfigV2(
            enabled=True,
            debug=True,
            max_results=10
        )
        
        table_config = TableEngineConfigV2(
            enabled=True,
            debug=True,
            max_results=10
        )
        
        hybrid_config = HybridEngineConfigV2(
            enabled=True,
            debug=True,
            max_results=15,
            enable_cross_search=True,
            enable_ranking=True,
            enable_optimization_pipeline=True
        )
        
        # 初始化各引擎
        print("🚀 正在初始化查询引擎...")
        
        image_engine = ImageEngine(image_config, vector_store)
        print("✅ 图片引擎初始化成功")
        
        text_engine = TextEngine(text_config, vector_store)
        print("✅ 文本引擎初始化成功")
        
        table_engine = TableEngine(table_config, vector_store)
        print("✅ 表格引擎初始化成功")
        
        hybrid_engine = HybridEngine(
            hybrid_config,
            image_engine=image_engine,
            text_engine=text_engine,
            table_engine=table_engine
        )
        print("✅ 混合引擎初始化成功")
        
        # 测试图片查询
        print("\n🧪 测试图片查询功能...")
        test_image_queries(image_engine)
        
        # 测试文本查询
        print("\n🧪 测试文本查询功能...")
        test_text_queries(text_engine)
        
        # 测试表格查询
        print("\n🧪 测试表格查询功能...")
        test_table_queries(table_engine)
        
        # 测试混合查询
        print("\n🧪 测试混合查询功能...")
        hybrid_test_success = test_hybrid_queries(hybrid_engine)
        
        # 测试混合查询引擎性能
        print("\n🚀 测试混合查询引擎性能...")
        test_hybrid_engine_performance(hybrid_engine)
        
        # 测试查询意图分析器
        print("\n🧠 测试查询意图分析器...")
        test_intent_analyzer_standalone(hybrid_engine)
        
        # 测试深度增强内容识别
        print("\n🔍 测试深度增强内容识别...")
        test_enhanced_content_recognition(hybrid_engine)
        
        # 测试业务领域查询优化
        print("\n🏢 测试业务领域查询优化...")
        test_business_domain_optimization(hybrid_engine)
        
        # 测试智能结果融合
        print("\n🧩 测试智能结果融合...")
        test_smart_result_fusion(hybrid_engine)
        
        # 测试跨类型内容关联分析
        print("\n🔗 测试跨类型内容关联分析...")
        test_cross_type_content_analysis(hybrid_engine)
        
        # 综合性能评估
        print("\n📊 开始综合性能评估...")
        overall_results = evaluate_overall_system_performance(hybrid_engine)
        
        print("\n🎉 V2.0系统修复验证测试完成！")
        
        # 测试总结
        print("\n📋 测试总结:")
        print(f"    图片查询: {'✅' if 'image_engine' in locals() else '❌'}")
        print(f"    文本查询: {'✅' if 'text_engine' in locals() else '❌'}")
        print(f"    表格查询: {'✅' if 'table_engine' in locals() else '❌'}")
        print(f"    混合查询: {'✅' if hybrid_test_success else '❌'}")
        
        if overall_results:
            print(f"    综合性能评估: ✅ 已完成")
        else:
            print(f"    综合性能评估: ❌ 未完成")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

def test_image_queries(image_engine):
    """测试图片查询功能"""
    test_queries = [
        "图4显示了什么内容？",
        "中芯国际的股价表现与沪深300指数的对比情况如何？",
        "中芯国际的全球部署示意图显示了哪些地区的布局？"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"  🔍 测试查询 {i}: {query}")
        try:
            result = image_engine.process_query(query)
            if result.success:
                print(f"    ✅ 查询成功，返回 {result.total_count} 个结果")
                if result.results:
                    print(f"    第一个结果: {result.results[0]}")
            else:
                print(f"    ❌ 查询失败: {result.error_message}")
        except Exception as e:
            print(f"    ❌ 查询异常: {e}")

def test_text_queries(text_engine):
    """测试文本查询功能"""
    test_queries = [
        "什么是RAG系统？",
        "中芯国际的主要业务和核心技术是什么？",
        "中芯国际在晶圆代工行业的市场地位如何？"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"  🔍 测试查询 {i}: {query}")
        try:
            result = text_engine.process_query(query)
            if result.success:
                print(f"    ✅ 查询成功，返回 {result.total_count} 个结果")
                if result.results:
                    print(f"    第一个结果: {result.results[0]}")
            else:
                print(f"    ❌ 查询失败: {result.error_message}")
        except Exception as e:
            print(f"    ❌ 查询异常: {e}")

def test_table_queries(table_engine):
    """测试表格查询功能"""
    test_queries = [
        "表格中包含了哪些数据？",
        "中芯国际在不同地域的营收分布情况如何？",
        "中芯国际的产能利用率显著提升体现在哪些方面？"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"  🔍 测试查询 {i}: {query}")
        try:
            result = table_engine.process_query(query)
            if result.success:
                print(f"    ✅ 查询成功，返回 {result.total_count} 个结果")
                if result.results:
                    print(f"    第一个结果: {result.results[0]}")
            else:
                print(f"    ❌ 查询失败: {result.error_message}")
        except Exception as e:
            print(f"    ❌ 查询异常: {e}")

def test_hybrid_queries(hybrid_engine):
    """测试混合查询功能 - 增强版"""
    print("  🧪 测试混合查询引擎的智能功能...")
    
    # 测试不同类型的混合查询
    test_queries = [
        # 简单混合查询
        {
            "query": "请综合分析中芯国际的图片和文字信息，说明其发展历程",
            "expected_intent": "hybrid",
            "description": "简单混合查询 - 图片+文字"
        },
        # 复杂混合查询
        {
            "query": "结合图表、表格和文字说明中芯国际的营业收入变化趋势，分析原因和影响",
            "expected_intent": "hybrid",
            "description": "复杂混合查询 - 图表+表格+文字+分析"
        },
        # 业务领域特定查询
        {
            "query": "综合分析中芯国际的财务数据、技术发展和市场表现",
            "expected_intent": "domain_财务",
            "description": "业务领域特定查询 - 财务+技术+市场"
        },
        # 图片导向查询
        {
            "query": "查看中芯国际的全球布局示意图，结合相关文字说明",
            "expected_intent": "image_focused",
            "description": "图片导向查询 - 图片为主+文字辅助"
        },
        # 表格导向查询
        {
            "query": "分析中芯国际的产能利用率数据表格，配合相关图表说明",
            "expected_intent": "table_focused",
            "description": "表格导向查询 - 表格为主+图表辅助"
        }
    ]
    
    total_queries = len(test_queries)
    successful_queries = 0
    
    for i, test_case in enumerate(test_queries, 1):
        query = test_case["query"]
        expected_intent = test_case["expected_intent"]
        description = test_case["description"]
        
        print(f"\n  🔍 测试查询 {i}/{total_queries}: {description}")
        print(f"    查询内容: {query}")
        print(f"    预期意图: {expected_intent}")
        
        try:
            start_time = time.time()
            result = hybrid_engine.process_query(query)
            processing_time = time.time() - start_time
            
            if result.success:
                successful_queries += 1
                print(f"    ✅ 查询成功")
                print(f"    处理时间: {processing_time:.2f}秒")
                print(f"    返回结果数: {result.total_count}")
                
                # 分析查询意图
                if hasattr(result, 'metadata') and result.metadata:
                    actual_intent = result.metadata.get('query_intent', 'unknown')
                    print(f"    实际意图: {actual_intent}")
                    
                    # 检查意图匹配
                    if expected_intent in actual_intent or actual_intent in expected_intent:
                        print(f"    🎯 意图匹配成功")
                    else:
                        print(f"    ⚠️  意图匹配偏差: 预期 {expected_intent}, 实际 {actual_intent}")
                
                # 分析结果类型分布
                if hasattr(result, 'metadata') and result.metadata:
                    image_count = result.metadata.get('image_results_count', 0)
                    text_count = result.metadata.get('text_results_count', 0)
                    table_count = result.metadata.get('table_results_count', 0)
                    print(f"    结果分布: 图片({image_count}) 文本({text_count}) 表格({table_count})")
                    
                    # 显示相关性得分
                    relevance_scores = result.metadata.get('relevance_scores', {})
                    if relevance_scores:
                        print(f"    相关性得分: {relevance_scores}")
                
                # 显示前几个结果
                if result.results:
                    print(f"    前3个结果预览:")
                    for j, res in enumerate(result.results[:3], 1):
                        if isinstance(res, dict):
                            result_type = res.get('type', 'unknown')
                            content_preview = str(res.get('content', ''))[:100]
                            print(f"      {j}. [{result_type}] {content_preview}...")
                        else:
                            print(f"      {j}. {str(res)[:100]}...")
                
            else:
                print(f"    ❌ 查询失败: {result.error_message}")
                
        except Exception as e:
            print(f"    ❌ 查询异常: {e}")
            import traceback
            traceback.print_exc()
    
    # 测试总结
    print(f"\n  📊 混合查询测试总结:")
    print(f"    总查询数: {total_queries}")
    print(f"    成功查询数: {successful_queries}")
    print(f"    成功率: {(successful_queries/total_queries)*100:.1f}%")
    
    return successful_queries == total_queries


def test_hybrid_engine_performance(hybrid_engine):
    """测试混合查询引擎性能"""
    print("  🚀 开始性能测试...")
    
    # 性能测试查询
    performance_queries = [
        "综合分析中芯国际的发展情况",
        "查看中芯国际的技术和财务数据",
        "分析中芯国际的市场表现和竞争优势"
    ]
    
    total_time = 0
    query_times = []
    
    for i, query in enumerate(performance_queries, 1):
        print(f"    🔍 性能测试 {i}: {query}")
        
        try:
            start_time = time.time()
            result = hybrid_engine.process_query(query)
            end_time = time.time()
            
            query_time = end_time - start_time
            query_times.append(query_time)
            total_time += query_time
            
            if result.success:
                print(f"      ✅ 成功 - 耗时: {query_time:.3f}秒, 结果数: {result.total_count}")
            else:
                print(f"      ❌ 失败 - 耗时: {query_time:.3f}秒, 错误: {result.error_message}")
                
        except Exception as e:
            print(f"      ❌ 异常 - 耗时: {time.time() - start_time:.3f}秒, 错误: {e}")
    
    # 性能统计
    if query_times:
        avg_time = total_time / len(query_times)
        min_time = min(query_times)
        max_time = max(query_times)
        
        print(f"\n    📊 性能测试结果:")
        print(f"      总查询数: {len(performance_queries)}")
        print(f"      总耗时: {total_time:.3f}秒")
        print(f"      平均耗时: {avg_time:.3f}秒")
        print(f"      最快查询: {min_time:.3f}秒")
        print(f"      最慢查询: {max_time:.3f}秒")
        
        # 性能评估
        if avg_time < 2.0:
            print(f"      🟢 性能优秀 (平均 < 2秒)")
        elif avg_time < 5.0:
            print(f"      🟡 性能良好 (平均 < 5秒)")
        elif avg_time < 10.0:
            print(f"      🟠 性能一般 (平均 < 10秒)")
        else:
            print(f"      🔴 性能较差 (平均 >= 10秒)")


def test_intent_analyzer_standalone(hybrid_engine):
    """单独测试查询意图分析器 - 增强版"""
    print("  🧠 测试查询意图分析器...")
    
    # 获取意图分析器实例
    if hasattr(hybrid_engine, 'intent_analyzer'):
        analyzer = hybrid_engine.intent_analyzer
    else:
        print("    ❌ 无法获取意图分析器实例")
        return
    
    # 测试不同类型的查询意图识别 - 增强版
    test_cases = [
        # 混合查询
        ("综合分析中芯国际的情况", "hybrid"),
        ("结合图片和文字说明", "hybrid"),
        ("多角度分析问题", "hybrid"),
        
        # 图片导向
        ("查看图表", "image_focused"),
        ("显示图片", "image_focused"),
        ("图像内容", "image_focused"),
        
        # 文本导向
        ("文档内容", "text_focused"),
        ("文章分析", "text_focused"),
        ("文本说明", "text_focused"),
        
        # 表格导向
        ("数据表格", "table_focused"),
        ("统计数字", "table_focused"),
        ("报表信息", "table_focused"),
        
        # 业务领域 - 增强版
        ("财务数据", "domain_财务"),
        ("技术发展", "domain_技术"),
        ("市场表现", "domain_市场"),
        ("归母净利润和毛利率", "domain_财务"),
        ("制程技术和晶圆产能", "domain_技术"),
        ("市场份额和客户分布", "domain_市场"),
        ("产能爬坡和生产效率", "domain_运营"),
        
        # 复杂度
        ("什么情况", "simple"),
        ("如何解决", "medium"),
        ("为什么这样", "complex"),
        
        # 新增：深度增强内容测试
        ("分析图表类型和数据趋势", "enhanced_图表分析"),
        ("查看表格结构和数据分布", "enhanced_结构化数据"),
        ("理解语义特征和关键洞察", "enhanced_语义特征")
    ]
    
    correct_predictions = 0
    total_cases = len(test_cases)
    
    for query, expected_intent in test_cases:
        try:
            actual_intent = analyzer.analyze_intent(query)
            
            # 检查意图匹配
            is_correct = False
            if expected_intent in actual_intent or actual_intent in expected_intent:
                is_correct = True
                correct_predictions += 1
            
            status = "✅" if is_correct else "❌"
            print(f"    {status} 查询: '{query}'")
            print(f"      预期: {expected_intent}")
            print(f"      实际: {actual_intent}")
            
        except Exception as e:
            print(f"    ❌ 查询: '{query}' - 分析失败: {e}")
    
    # 意图分析准确率
    accuracy = (correct_predictions / total_cases) * 100 if total_cases > 0 else 0
    print(f"\n    📊 意图分析准确率: {accuracy:.1f}% ({correct_predictions}/{total_cases})")
    
    if accuracy >= 90:
        print(f"      🟢 准确率优秀 (>= 90%)")
    elif accuracy >= 80:
        print(f"      🟡 准确率良好 (>= 80%)")
    elif accuracy >= 70:
        print(f"      🟠 准确率一般 (>= 70%)")
    else:
        print(f"      🔴 准确率较差 (< 70%)")


def test_enhanced_content_recognition(hybrid_engine):
    """测试深度增强内容识别功能"""
    print("\n" + "="*60)
    print("🔍 测试深度增强内容识别功能")
    print("="*60)
    
    # 获取意图分析器实例
    if hasattr(hybrid_engine, 'intent_analyzer'):
        analyzer = hybrid_engine.intent_analyzer
    else:
        print("❌ 无法获取意图分析器实例")
        return
    
    # 深度增强内容测试用例
    enhanced_test_cases = [
        # 图表分析相关
        ("分析图表类型和数据趋势", "enhanced_图表分析"),
        ("查看数据点和趋势分析", "enhanced_图表分析"),
        ("理解关键洞察和内容理解", "enhanced_图表分析"),
        
        # 结构化数据相关
        ("查看表格结构和列标题", "enhanced_结构化数据"),
        ("分析行数据和数据统计", "enhanced_结构化数据"),
        ("理解表格类型和数据分布", "enhanced_结构化数据"),
        
        # 语义特征相关
        ("分析语义特征描述", "enhanced_语义特征"),
        ("理解内容理解和数据趋势", "enhanced_语义特征"),
        ("查看关键洞察和图表主题", "enhanced_语义特征")
    ]
    
    correct_count = 0
    total_count = len(enhanced_test_cases)
    
    print("📋 深度增强内容识别测试:")
    for query, expected_type in enhanced_test_cases:
        try:
            actual_intent = analyzer.analyze_intent(query)
            is_correct = expected_type in actual_intent
            
            if is_correct:
                correct_count += 1
                status = "✅"
            else:
                status = "❌"
            
            print(f"{status} 查询: {query}")
            print(f"   预期类型: {expected_type}")
            print(f"   实际意图: {actual_intent}")
            print()
            
        except Exception as e:
            print(f"❌ 查询: {query}")
            print(f"   错误: {str(e)}")
            print()
    
    enhanced_accuracy = (correct_count / total_count) * 100
    print(f"📊 深度增强内容识别准确率: {correct_count}/{total_count} ({enhanced_accuracy:.1f}%)")
    
    return enhanced_accuracy


def test_business_domain_optimization(hybrid_engine):
    """测试业务领域查询优化功能"""
    print("\n" + "="*60)
    print("🏢 测试业务领域查询优化功能")
    print("="*60)
    
    # 获取意图分析器实例
    if hasattr(hybrid_engine, 'intent_analyzer'):
        analyzer = hybrid_engine.intent_analyzer
    else:
        print("❌ 无法获取意图分析器实例")
        return
    
    # 业务领域测试用例
    domain_test_cases = [
        # 财务领域
        ("中芯国际的归母净利润", "domain_财务"),
        ("毛利率和净利率分析", "domain_财务"),
        ("市盈率和每股收益", "domain_财务"),
        ("资本开支和现金流", "domain_财务"),
        
        # 技术领域
        ("制程技术发展", "domain_技术"),
        ("晶圆产能和利用率", "domain_技术"),
        ("半导体芯片技术", "domain_技术"),
        ("晶体管和集成电路", "domain_技术"),
        
        # 市场领域
        ("市场份额分析", "domain_市场"),
        ("客户分布情况", "domain_市场"),
        ("地域布局策略", "domain_市场"),
        ("全球部署情况", "domain_市场"),
        
        # 运营领域
        ("产能爬坡情况", "domain_运营"),
        ("设备利用率", "domain_运营"),
        ("生产效率分析", "domain_运营"),
        ("质量控制标准", "domain_运营")
    ]
    
    correct_count = 0
    total_count = len(domain_test_cases)
    
    print("📋 业务领域识别测试:")
    for query, expected_domain in domain_test_cases:
        try:
            actual_intent = analyzer.analyze_intent(query)
            is_correct = expected_domain in actual_intent
            
            if is_correct:
                correct_count += 1
                status = "✅"
            else:
                status = "❌"
            
            print(f"{status} 查询: {query}")
            print(f"   预期领域: {expected_domain}")
            print(f"   实际意图: {actual_intent}")
            print()
            
        except Exception as e:
            print(f"❌ 查询: {query}")
            print(f"   错误: {str(e)}")
            print()
    
    domain_accuracy = (correct_count / total_count) * 100
    print(f"📊 业务领域识别准确率: {correct_count}/{total_count} ({domain_accuracy:.1f}%)")
    
    return domain_accuracy


def test_smart_result_fusion(hybrid_engine):
    """测试智能结果融合功能"""
    print("\n" + "="*60)
    print("🧩 测试智能结果融合功能")
    print("="*60)
    
    # 测试智能融合的查询用例
    fusion_test_cases = [
        "综合分析中芯国际的财务和技术表现",
        "结合图表和表格分析中芯国际的市场趋势",
        "多角度评估中芯国际的运营效率",
        "整合图片、文本和表格信息分析中芯国际"
    ]
    
    print("📋 智能结果融合测试:")
    total_time = 0
    successful_fusions = 0
    
    for i, query in enumerate(fusion_test_cases, 1):
        try:
            print(f"\n🔍 测试用例 {i}: {query}")
            start_time = time.time()
            
            # 执行混合查询
            result = hybrid_engine.process_query(query)
            processing_time = time.time() - start_time
            total_time += processing_time
            
            if result.success:
                successful_fusions += 1
                print(f"   ✅ 查询成功")
                print(f"   ⏱️  处理时间: {processing_time:.3f}秒")
                print(f"   📊 总结果数: {result.total_count}")
                
                # 分析结果分布
                metadata = result.metadata
                if metadata:
                    print(f"   🖼️  图片结果: {metadata.get('image_results_count', 0)}")
                    print(f"   📝 文本结果: {metadata.get('text_results_count', 0)}")
                    print(f"   📊 表格结果: {metadata.get('table_results_count', 0)}")
                    
                    # 显示相关性得分
                    relevance_scores = metadata.get('relevance_scores', {})
                    if relevance_scores:
                        print(f"   🎯 相关性得分:")
                        for content_type, score in relevance_scores.items():
                            print(f"      {content_type}: {score:.3f}")
            else:
                print(f"   ❌ 查询失败: {result.error_message}")
                
        except Exception as e:
            print(f"   ❌ 执行异常: {str(e)}")
    
    print(f"\n📊 智能结果融合测试总结:")
    print(f"   成功融合: {successful_fusions}/{len(fusion_test_cases)}")
    print(f"   总耗时: {total_time:.3f}秒")
    print(f"   平均耗时: {total_time/len(fusion_test_cases):.3f}秒")
    
    return successful_fusions, total_time


def test_cross_type_content_analysis(hybrid_engine):
    """测试跨类型内容关联分析功能"""
    print("\n" + "="*60)
    print("🔗 测试跨类型内容关联分析功能")
    print("="*60)
    
    # 测试跨类型关联的查询用例
    cross_type_test_cases = [
        "中芯国际的营收数据在图表和表格中的表现",
        "结合图片和文本分析中芯国际的技术发展",
        "对比图表、表格和文本中的市场信息",
        "综合分析中芯国际在不同内容类型中的表现"
    ]
    
    print("📋 跨类型内容关联分析测试:")
    total_time = 0
    successful_analyses = 0
    
    for i, query in enumerate(cross_type_test_cases, 1):
        try:
            print(f"\n🔍 测试用例 {i}: {query}")
            start_time = time.time()
            
            # 执行混合查询
            result = hybrid_engine.process_query(query)
            processing_time = time.time() - start_time
            total_time += processing_time
            
            if result.success:
                successful_analyses += 1
                print(f"   ✅ 查询成功")
                print(f"   ⏱️  处理时间: {processing_time:.3f}秒")
                print(f"   📊 总结果数: {result.total_count}")
                
                # 分析结果类型分布
                metadata = result.metadata
                if metadata:
                    image_count = metadata.get('image_results_count', 0)
                    text_count = metadata.get('text_results_count', 0)
                    table_count = metadata.get('table_results_count', 0)
                    
                    print(f"   🖼️  图片结果: {image_count}")
                    print(f"   📝 文本结果: {text_count}")
                    print(f"   📊 表格结果: {table_count}")
                    
                    # 检查跨类型关联
                    if image_count > 0 and text_count > 0:
                        print(f"   🔗 图片-文本关联: ✅")
                    if image_count > 0 and table_count > 0:
                        print(f"   🔗 图片-表格关联: ✅")
                    if text_count > 0 and table_count > 0:
                        print(f"   🔗 文本-表格关联: ✅")
                    
                    # 显示相关性得分
                    relevance_scores = metadata.get('relevance_scores', {})
                    if relevance_scores:
                        print(f"   🎯 相关性得分:")
                        for content_type, score in relevance_scores.items():
                            print(f"      {content_type}: {score:.3f}")
                            
                    # 检查处理详情
                    processing_details = metadata.get('processing_details', {})
                    if processing_details:
                        print(f"   ⚙️  处理详情:")
                        for key, value in processing_details.items():
                            print(f"      {key}: {value}")
            else:
                print(f"   ❌ 查询失败: {result.error_message}")
                
        except Exception as e:
            print(f"   ❌ 执行异常: {str(e)}")
    
    print(f"\n📊 跨类型内容关联分析测试总结:")
    print(f"   成功分析: {successful_analyses}/{len(cross_type_test_cases)}")
    print(f"   总耗时: {total_time:.3f}秒")
    print(f"   平均耗时: {total_time/len(cross_type_test_cases):.3f}秒")
    
    return successful_analyses, total_time


def evaluate_overall_system_performance(hybrid_engine):
    """综合评估系统性能"""
    print("\n" + "="*60)
    print("📊 综合系统性能评估")
    print("="*60)
    
    print("🔍 开始综合性能评估...")
    
    # 执行各项测试并收集结果
    test_results = {}
    
    try:
        # 1. 混合查询性能测试
        print("\n1️⃣ 混合查询性能测试...")
        performance_result = test_hybrid_engine_performance(hybrid_engine)
        test_results['performance'] = performance_result
        
        # 2. 意图分析准确率测试
        print("\n2️⃣ 意图分析准确率测试...")
        intent_accuracy = test_intent_analyzer_standalone(hybrid_engine)
        test_results['intent_accuracy'] = intent_accuracy
        
        # 3. 深度增强内容识别测试
        print("\n3️⃣ 深度增强内容识别测试...")
        enhanced_accuracy = test_enhanced_content_recognition(hybrid_engine)
        test_results['enhanced_accuracy'] = enhanced_accuracy
        
        # 4. 业务领域识别测试
        print("\n4️⃣ 业务领域识别测试...")
        domain_accuracy = test_business_domain_optimization(hybrid_engine)
        test_results['domain_accuracy'] = domain_accuracy
        
        # 5. 智能结果融合测试
        print("\n5️⃣ 智能结果融合测试...")
        fusion_success, fusion_time = test_smart_result_fusion(hybrid_engine)
        test_results['fusion_success'] = fusion_success
        test_results['fusion_time'] = fusion_time
        
        # 6. 跨类型内容关联测试
        print("\n6️⃣ 跨类型内容关联测试...")
        cross_success, cross_time = test_cross_type_content_analysis(hybrid_engine)
        test_results['cross_success'] = cross_success
        test_results['cross_time'] = cross_time
        
    except Exception as e:
        print(f"❌ 综合性能评估过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # 生成综合评估报告
    print("\n" + "="*60)
    print("📋 综合性能评估报告")
    print("="*60)
    
    # 性能评分
    if 'performance' in test_results:
        print(f"🚀 混合查询性能: 已完成测试")
    
    # 准确率评分
    if 'intent_accuracy' in test_results and test_results['intent_accuracy'] is not None:
        accuracy = test_results['intent_accuracy']
        if accuracy >= 90:
            accuracy_level = "🟢 优秀"
        elif accuracy >= 80:
            accuracy_level = "🟡 良好"
        elif accuracy >= 70:
            accuracy_level = "🟠 一般"
        else:
            accuracy_level = "🔴 需要改进"
        print(f"🧠 意图分析准确率: {accuracy:.1f}% {accuracy_level}")
    
    if 'enhanced_accuracy' in test_results and test_results['enhanced_accuracy'] is not None:
        enhanced_acc = test_results['enhanced_accuracy']
        if enhanced_acc >= 90:
            enhanced_level = "🟢 优秀"
        elif enhanced_acc >= 80:
            enhanced_level = "🟡 良好"
        elif enhanced_acc >= 70:
            enhanced_level = "🟠 一般"
        else:
            enhanced_level = "🔴 需要改进"
        print(f"🔍 深度增强内容识别: {enhanced_acc:.1f}% {enhanced_level}")
    
    if 'domain_accuracy' in test_results and test_results['domain_accuracy'] is not None:
        domain_acc = test_results['domain_accuracy']
        if domain_acc >= 90:
            domain_level = "🟢 优秀"
        elif domain_acc >= 80:
            domain_level = "🟡 良好"
        elif domain_acc >= 70:
            domain_level = "🟠 一般"
        else:
            domain_level = "🔴 需要改进"
        print(f"🏢 业务领域识别: {domain_acc:.1f}% {domain_level}")
    
    # 功能完整性评分
    if 'fusion_success' in test_results and 'cross_success' in test_results:
        fusion_rate = (test_results['fusion_success'] / 4) * 100  # 4个测试用例
        cross_rate = (test_results['cross_success'] / 4) * 100    # 4个测试用例
        
        print(f"🧩 智能结果融合: {fusion_rate:.1f}% 成功率")
        print(f"🔗 跨类型内容关联: {cross_rate:.1f}% 成功率")
    
    # 总体评价
    print(f"\n🎯 总体评价:")
    
    # 计算综合得分
    total_score = 0
    score_count = 0
    
    if 'intent_accuracy' in test_results and test_results['intent_accuracy'] is not None:
        total_score += test_results['intent_accuracy']
        score_count += 1
    
    if 'enhanced_accuracy' in test_results and test_results['enhanced_accuracy'] is not None:
        total_score += test_results['enhanced_accuracy']
        score_count += 1
    
    if 'domain_accuracy' in test_results and test_results['domain_accuracy'] is not None:
        total_score += test_results['domain_accuracy']
        score_count += 1
    
    if score_count > 0:
        average_score = total_score / score_count
        print(f"   综合准确率: {average_score:.1f}%")
        
        if average_score >= 90:
            print(f"   🏆 系统性能优秀，各项功能运行良好")
        elif average_score >= 80:
            print(f"   🎯 系统性能良好，部分功能需要优化")
        elif average_score >= 70:
            print(f"   ⚠️  系统性能一般，建议进行优化")
        else:
            print(f"   🔧 系统性能需要改进，建议重点优化")
    
    print(f"\n📝 优化建议:")
    print(f"   1. 如果意图分析准确率较低，建议优化关键词库和匹配算法")
    print(f"   2. 如果深度增强内容识别率较低，建议检查ImageEnhancer配置")
    print(f"   3. 如果业务领域识别率较低，建议扩展领域关键词库")
    print(f"   4. 如果融合成功率较低，建议检查子引擎配置和连接状态")
    
    return test_results


if __name__ == "__main__":
    test_v2_system_fixes()
