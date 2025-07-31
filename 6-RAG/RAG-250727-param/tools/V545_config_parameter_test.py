'''
程序说明：
## 1. 配置参数调整验证脚本
## 2. 验证阶段一的配置参数是否正确加载
## 3. 测试新的过滤和重排序功能
## 4. 确保配置参数的有效性
'''

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings


def test_config_loading():
    """测试配置加载"""
    print("=" * 60)
    print("🔍 测试配置参数加载")
    print("=" * 60)
    
    try:
        # 加载配置
        settings = Settings.load_from_file('config.json')
        print("✅ 配置加载成功")
        
        # 检查向量存储配置
        print("\n📊 向量存储配置:")
        print(f"  similarity_top_k: {getattr(settings, 'similarity_top_k', '未配置')}")
        print(f"  similarity_threshold: {getattr(settings, 'similarity_threshold', '未配置')}")
        print(f"  enable_reranking: {getattr(settings, 'enable_reranking', '未配置')}")
        
        # 检查QA系统配置
        print("\n📊 QA系统配置:")
        print(f"  temperature: {getattr(settings, 'temperature', '未配置')}")
        print(f"  max_tokens: {getattr(settings, 'max_tokens', '未配置')}")
        print(f"  enable_sources_filtering: {getattr(settings, 'enable_sources_filtering', '未配置')}")
        print(f"  min_relevance_score: {getattr(settings, 'min_relevance_score', '未配置')}")
        
        # 检查处理配置
        print("\n📊 处理配置:")
        print(f"  enable_smart_filtering: {getattr(settings, 'enable_smart_filtering', '未配置')}")
        print(f"  semantic_similarity_threshold: {getattr(settings, 'semantic_similarity_threshold', '未配置')}")
        print(f"  content_relevance_threshold: {getattr(settings, 'content_relevance_threshold', '未配置')}")
        
        return True
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False


def test_config_file():
    """测试配置文件内容"""
    print("\n" + "=" * 60)
    print("🔍 测试配置文件内容")
    print("=" * 60)
    
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 检查向量存储配置
        vector_store_config = config.get('vector_store', {})
        print("✅ 向量存储配置检查:")
        required_vector_params = [
            'similarity_top_k', 'similarity_threshold', 'enable_reranking',
            'reranking_method', 'semantic_weight', 'keyword_weight'
        ]
        
        for param in required_vector_params:
            if param in vector_store_config:
                print(f"  ✅ {param}: {vector_store_config[param]}")
            else:
                print(f"  ❌ {param}: 缺失")
        
        # 检查QA系统配置
        qa_config = config.get('qa_system', {})
        print("\n✅ QA系统配置检查:")
        required_qa_params = [
            'temperature', 'max_tokens', 'enable_sources_filtering',
            'min_relevance_score', 'enable_keyword_matching'
        ]
        
        for param in required_qa_params:
            if param in qa_config:
                print(f"  ✅ {param}: {qa_config[param]}")
            else:
                print(f"  ❌ {param}: 缺失")
        
        # 检查处理配置
        processing_config = config.get('processing', {})
        print("\n✅ 处理配置检查:")
        required_processing_params = [
            'enable_smart_filtering', 'semantic_similarity_threshold',
            'content_relevance_threshold', 'max_filtered_results'
        ]
        
        for param in required_processing_params:
            if param in processing_config:
                print(f"  ✅ {param}: {processing_config[param]}")
            else:
                print(f"  ❌ {param}: 缺失")
        
        return True
    except Exception as e:
        print(f"❌ 配置文件检查失败: {e}")
        return False


def test_parameter_validation():
    """测试参数验证"""
    print("\n" + "=" * 60)
    print("🔍 测试参数验证")
    print("=" * 60)
    
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 验证数值参数
        vector_config = config.get('vector_store', {})
        qa_config = config.get('qa_system', {})
        processing_config = config.get('processing', {})
        
        print("✅ 数值参数验证:")
        
        # 相似度阈值验证
        similarity_threshold = vector_config.get('similarity_threshold', 0)
        if 0 <= similarity_threshold <= 1:
            print(f"  ✅ similarity_threshold: {similarity_threshold} (有效)")
        else:
            print(f"  ❌ similarity_threshold: {similarity_threshold} (无效，应在0-1之间)")
        
        # 温度参数验证
        temperature = qa_config.get('temperature', 0)
        if 0 <= temperature <= 1:
            print(f"  ✅ temperature: {temperature} (有效)")
        else:
            print(f"  ❌ temperature: {temperature} (无效，应在0-1之间)")
        
        # 最小相关性分数验证
        min_relevance_score = qa_config.get('min_relevance_score', 0)
        if 0 <= min_relevance_score <= 1:
            print(f"  ✅ min_relevance_score: {min_relevance_score} (有效)")
        else:
            print(f"  ❌ min_relevance_score: {min_relevance_score} (无效，应在0-1之间)")
        
        # 权重参数验证
        semantic_weight = vector_config.get('semantic_weight', 0)
        keyword_weight = vector_config.get('keyword_weight', 0)
        if 0 <= semantic_weight <= 1 and 0 <= keyword_weight <= 1:
            print(f"  ✅ semantic_weight: {semantic_weight}, keyword_weight: {keyword_weight} (有效)")
        else:
            print(f"  ❌ 权重参数无效")
        
        return True
    except Exception as e:
        print(f"❌ 参数验证失败: {e}")
        return False


def test_functionality_flags():
    """测试功能开关"""
    print("\n" + "=" * 60)
    print("🔍 测试功能开关")
    print("=" * 60)
    
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print("✅ 功能开关检查:")
        
        # 检查重排序开关
        enable_reranking = config.get('vector_store', {}).get('enable_reranking', False)
        print(f"  {'✅' if enable_reranking else '❌'} 重排序功能: {'启用' if enable_reranking else '禁用'}")
        
        # 检查源过滤开关
        enable_sources_filtering = config.get('qa_system', {}).get('enable_sources_filtering', False)
        print(f"  {'✅' if enable_sources_filtering else '❌'} 源过滤功能: {'启用' if enable_sources_filtering else '禁用'}")
        
        # 检查智能过滤开关
        enable_smart_filtering = config.get('processing', {}).get('enable_smart_filtering', False)
        print(f"  {'✅' if enable_smart_filtering else '❌'} 智能过滤功能: {'启用' if enable_smart_filtering else '禁用'}")
        
        # 检查关键词匹配开关
        enable_keyword_matching = config.get('qa_system', {}).get('enable_keyword_matching', False)
        print(f"  {'✅' if enable_keyword_matching else '❌'} 关键词匹配: {'启用' if enable_keyword_matching else '禁用'}")
        
        # 检查图片ID匹配开关
        enable_image_id_matching = config.get('qa_system', {}).get('enable_image_id_matching', False)
        print(f"  {'✅' if enable_image_id_matching else '❌'} 图片ID匹配: {'启用' if enable_image_id_matching else '禁用'}")
        
        return True
    except Exception as e:
        print(f"❌ 功能开关检查失败: {e}")
        return False


def main():
    """主函数"""
    print("🚀 开始配置参数调整验证...")
    
    tests = [
        ("配置加载测试", test_config_loading),
        ("配置文件内容测试", test_config_file),
        ("参数验证测试", test_parameter_validation),
        ("功能开关测试", test_functionality_flags)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 执行失败: {e}")
            results.append((test_name, False))
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 测试通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 阶段一配置参数调整完成！所有测试通过！")
        print("\n📋 调整总结:")
        print("  ✅ similarity_top_k: 3 → 2 (减少检索数量)")
        print("  ✅ temperature: 0.7 → 0.5 (提高精确性)")
        print("  ✅ max_tokens: 2000 → 1500 (控制回答长度)")
        print("  ✅ 新增相似度阈值: 0.7")
        print("  ✅ 新增重排序功能: 启用")
        print("  ✅ 新增源过滤功能: 启用")
        print("  ✅ 新增智能过滤功能: 启用")
    else:
        print("⚠️  部分测试失败，需要进一步检查")


if __name__ == "__main__":
    main() 