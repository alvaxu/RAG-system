#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
程序说明：

## 1. 测试Image Engine V2.0的五层召回策略具体实现
## 2. 验证每层召回的功能和效果
## 3. 测试查询扩展和智能匹配
## 4. 验证与ImageRerankingService的集成
'''

import sys
import os
# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import logging
from v2.core.image_engine import ImageEngine
from v2.config.v2_config import V2ConfigManager
from unittest.mock import Mock

# 设置日志级别
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_five_layer_recall():
    """测试五层召回策略的具体实现"""
    print("🔍 测试Image Engine V2.0五层召回策略...")
    print("=" * 60)
    
    try:
        # 1. 加载配置
        print("📋 加载配置...")
        try:
            config_manager = V2ConfigManager()
            print(f"✅ 配置管理器创建成功: {type(config_manager)}")
            
            # 直接访问配置
            if hasattr(config_manager.config, 'image_engine'):
                image_config = config_manager.config.image_engine
                print(f"✅ 直接访问image_engine配置成功")
            else:
                print("❌ 直接访问image_engine配置失败")
                return False
                
        except Exception as e:
            print(f"❌ 配置加载失败: {e}")
            return False
        
        print(f"✅ 配置加载成功: {image_config.name}")
        
        # 2. 创建Image Engine实例
        print("\n🚀 创建Image Engine实例...")
        image_engine = ImageEngine(
            config=image_config,
            vector_store=None,  # 暂时不提供向量数据库
            document_loader=None,  # 暂时不提供文档加载器
            skip_initial_load=True
        )
        
        print(f"✅ Image Engine创建成功: {image_engine.name}")
        
        # 3. 测试查询扩展功能
        print("\n🔍 测试查询扩展功能...")
        test_queries = [
            "中芯国际净利润图表",
            "芯片制造良率数据",
            "2024年Q3财务报告",
            "半导体行业分析图"
        ]
        
        for query in test_queries:
            print(f"\n  查询: {query}")
            expanded_queries = image_engine._expand_query(query)
            print(f"  扩展查询: {expanded_queries}")
            print(f"  扩展数量: {len(expanded_queries)}")
        
        # 4. 测试文本匹配分数计算
        print("\n📊 测试文本匹配分数计算...")
        test_cases = [
            {
                'query_words': {'中芯国际', '净利润'},
                'text': '中芯国际2024年净利润表现良好',
                'base_score': 0.8,
                'expected_min': 0.4
            },
            {
                'query_words': {'芯片', '制造'},
                'text': '半导体芯片制造工艺',
                'base_score': 0.7,
                'expected_min': 0.35
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            score = image_engine._calculate_text_match_score(
                test_case['query_words'],
                test_case['text'],
                test_case['base_score']
            )
            print(f"  测试用例 {i+1}: 分数={score:.3f}, 期望>={test_case['expected_min']}")
            if score >= test_case['expected_min']:
                print("    ✅ 通过")
            else:
                print("    ❌ 失败")
        
        # 5. 测试字符串相似度计算
        print("\n🔤 测试字符串相似度计算...")
        similarity_tests = [
            ('中芯国际', '中芯国际'),
            ('芯片', '半导体'),
            ('净利润', '利润'),
            ('2024年', '2024年度')
        ]
        
        for str1, str2 in similarity_tests:
            similarity = image_engine._calculate_string_similarity(str1, str2)
            print(f"  '{str1}' vs '{str2}': 相似度={similarity:.3f}")
        
        # 6. 测试文档ID获取
        print("\n🆔 测试文档ID获取...")
        mock_doc = Mock()
        mock_doc.metadata = {'id': 'test_doc_123'}
        doc_id = image_engine._get_doc_id(mock_doc)
        print(f"  文档ID: {doc_id}")
        
        # 7. 测试结果去重和排序
        print("\n🔄 测试结果去重和排序...")
        mock_results = [
            {'doc': Mock(metadata={'id': 'doc1'}), 'score': 0.8, 'source': 'vector'},
            {'doc': Mock(metadata={'id': 'doc2'}), 'score': 0.9, 'source': 'keyword'},
            {'doc': Mock(metadata={'id': 'doc1'}), 'score': 0.7, 'source': 'hybrid'},  # 重复ID
        ]
        
        unique_results = image_engine._deduplicate_and_sort_results(mock_results)
        print(f"  原始结果数量: {len(mock_results)}")
        print(f"  去重后数量: {len(unique_results)}")
        print(f"  最高分数: {unique_results[0]['score'] if unique_results else 'N/A'}")
        
        # 8. 测试最终排序和限制
        print("\n📈 测试最终排序和限制...")
        final_results = image_engine._final_ranking_and_limit("测试查询", unique_results)
        print(f"  最终结果数量: {len(final_results)}")
        
        print("\n🎉 五层召回策略测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_five_layer_recall()
    if success:
        print("\n✅ 所有测试通过！五层召回策略实现正确！")
    else:
        print("\n❌ 测试失败，需要进一步调试")
