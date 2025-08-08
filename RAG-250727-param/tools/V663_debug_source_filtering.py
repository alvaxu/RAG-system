"""
程序说明：

## 1. 调试源过滤问题
检查为什么图片源被过滤掉

## 2. 验证源过滤逻辑
确保图片源能正确通过过滤
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.enhanced_qa_system import load_enhanced_qa_system
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_source_filtering():
    """
    测试源过滤功能
    """
    print("=== 测试源过滤功能 ===")
    
    # 加载QA系统
    qa_system = load_enhanced_qa_system("central/vector_db")
    if not qa_system:
        print("❌ 加载QA系统失败")
        return
    
    print("✅ QA系统加载成功")
    
    # 测试问题
    question = "请显示图4：公司25Q1下游应用领域结构情况"
    
    try:
        # 调用QA系统
        result = qa_system.answer_question(question)
        
        # 分析结果
        answer = result.get('answer', '')
        sources = result.get('sources', [])
        
        print(f"\nLLM回答: {answer[:200]}...")
        print(f"源数量: {len(sources)}")
        
        # 检查每个源
        for i, source in enumerate(sources):
            print(f"\n--- 源 {i+1} ---")
            print(f"类型: {source.get('type', 'unknown')}")
            print(f"标题: {source.get('title', 'N/A')}")
            print(f"内容预览: {source.get('content', '')[:100]}...")
            
            # 检查元数据
            metadata = source.get('metadata', {})
            print(f"元数据: {metadata}")
            
            # 检查相关性分数
            relevance_score = source.get('relevance_score', 'N/A')
            print(f"相关性分数: {relevance_score}")
        
        # 如果没有源，检查源过滤引擎的配置
        if not sources:
            print("\n⚠️  没有找到源，检查源过滤引擎配置...")
            
            # 获取源过滤引擎统计信息
            stats = qa_system.get_optimization_stats()
            source_filter_stats = stats.get('source_filter_engine', {})
            
            print(f"源过滤引擎配置: {source_filter_stats}")
            
            # 检查源过滤引擎是否过于严格
            min_relevance_score = source_filter_stats.get('min_relevance_score', 0.6)
            print(f"最小相关性分数阈值: {min_relevance_score}")
            
            if min_relevance_score > 0.5:
                print("⚠️  建议降低最小相关性分数阈值")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def test_direct_source_filtering():
    """
    直接测试源过滤引擎
    """
    print("\n=== 直接测试源过滤引擎 ===")
    
    # 加载QA系统
    qa_system = load_enhanced_qa_system("central/vector_db")
    if not qa_system:
        print("❌ 加载QA系统失败")
        return
    
    # 模拟LLM回答和源
    llm_answer = "根据图4显示，公司25Q1下游应用领域结构情况如下：消费电子占比41%，智能手机占比24%，电脑与平板占比17%，工业与汽车占比10%，互联与可穿戴设备占比8%。"
    
    # 模拟图片源
    mock_source = {
        'content': '图片标题: 图4：公司25Q1下游应用领域结构情况\n图片描述: 这是一张饼图，展示了不同类别在总和中的占比情况...',
        'metadata': {
            'chunk_type': 'image',
            'img_caption': ['图4：公司25Q1下游应用领域结构情况'],
            'image_id': 'test_image_001'
        },
        'score': 0.8
    }
    
    sources = [mock_source]
    
    try:
        # 直接调用源过滤
        filtered_sources = qa_system._apply_source_filtering(llm_answer, sources)
        
        print(f"原始源数量: {len(sources)}")
        print(f"过滤后源数量: {len(filtered_sources)}")
        
        if filtered_sources:
            for i, source in enumerate(filtered_sources):
                print(f"\n过滤后源 {i+1}:")
                print(f"相关性分数: {source.get('relevance_score', 'N/A')}")
                print(f"内容: {source.get('content', '')[:100]}...")
        else:
            print("❌ 所有源都被过滤掉了")
            
    except Exception as e:
        print(f"❌ 直接测试失败: {e}")

if __name__ == "__main__":
    print("开始调试源过滤问题...")
    
    # 测试源过滤功能
    test_source_filtering()
    
    # 直接测试源过滤引擎
    test_direct_source_filtering()
    
    print("\n=== 调试完成 ===")
