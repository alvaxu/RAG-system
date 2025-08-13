#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：验证LLM答案和来源信息的修复效果
测试内容：
1. LLM答案是否正确生成和显示
2. 来源信息是否正确提取和格式化
3. 元数据是否正确传递
"""

import requests
import json
import time
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_text_query():
    """测试文本查询"""
    print("🔍 测试文本查询...")
    
    url = "http://localhost:5000/api/v2/qa/ask"
    data = {
        "question": "中芯国际从2000年到2020年的发展历程中有哪些重要节点?",
        "query_type": "text",
        "user_id": "test_user",
        "max_results": 10
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 文本查询成功")
            print(f"   问题: {data['question']}")
            print(f"   答案长度: {len(result.get('answer', ''))}")
            print(f"   来源数量: {len(result.get('sources', []))}")
            print(f"   总结果数: {result.get('total_count', 0)}")
            
            # 检查答案
            answer = result.get('answer', '')
            if answer and len(answer) > 50:
                print(f"✅ LLM答案正常生成")
                print(f"   答案预览: {answer[:100]}...")
            else:
                print(f"❌ LLM答案异常: {answer}")
            
            # 检查来源
            sources = result.get('sources', [])
            if sources:
                print(f"✅ 来源信息正常提取")
                for i, source in enumerate(sources[:3]):  # 只显示前3个
                    formatted = source.get('formatted_source', '未知来源')
                    print(f"   来源{i+1}: {formatted}")
            else:
                print(f"❌ 来源信息为空")
            
            # 检查元数据
            metadata = result.get('metadata', {})
            if metadata:
                print(f"✅ 元数据正常传递")
                print(f"   查询意图: {metadata.get('query_intent', 'N/A')}")
                print(f"   使用的引擎: {metadata.get('engines_used', [])}")
                print(f"   优化详情: {metadata.get('optimization_details', {})}")
            else:
                print(f"⚠️  元数据为空")
                
        else:
            print(f"❌ 文本查询失败: HTTP {response.status_code}")
            print(f"   错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 文本查询异常: {e}")

def test_hybrid_query():
    """测试混合查询"""
    print("\n🔗 测试混合查询...")
    
    url = "http://localhost:5000/api/v2/qa/ask"
    data = {
        "question": "中芯国际的整体财务表现和业务发展情况如何?",
        "query_type": "hybrid",
        "user_id": "test_user",
        "max_results": 15
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 混合查询成功")
            print(f"   问题: {data['question']}")
            print(f"   答案长度: {len(result.get('answer', ''))}")
            print(f"   来源数量: {len(result.get('sources', []))}")
            print(f"   总结果数: {result.get('total_count', 0)}")
            
            # 检查答案
            answer = result.get('answer', '')
            if answer and len(answer) > 50:
                print(f"✅ LLM答案正常生成")
                print(f"   答案预览: {answer[:100]}...")
            else:
                print(f"❌ LLM答案异常: {answer}")
            
            # 检查来源
            sources = result.get('sources', [])
            if sources:
                print(f"✅ 来源信息正常提取")
                for i, source in enumerate(sources[:3]):  # 只显示前3个
                    formatted = source.get('formatted_source', '未知来源')
                    source_type = source.get('source_type', 'unknown')
                    print(f"   来源{i+1} ({source_type}): {formatted}")
            else:
                print(f"❌ 来源信息为空")
            
            # 检查元数据
            metadata = result.get('metadata', {})
            if metadata:
                print(f"✅ 元数据正常传递")
                print(f"   查询意图: {metadata.get('query_intent', 'N/A')}")
                print(f"   使用的引擎: {metadata.get('engines_used', [])}")
                print(f"   优化详情: {metadata.get('optimization_details', {})}")
                
                # 检查优化管道详情
                opt_details = metadata.get('optimization_details', {})
                if opt_details:
                    print(f"   重排序结果数: {opt_details.get('reranked_count', 0)}")
                    print(f"   过滤后结果数: {opt_details.get('filtered_count', 0)}")
                    print(f"   过滤后来源数: {opt_details.get('filtered_sources_count', 0)}")
                    print(f"   管道指标: {opt_details.get('pipeline_metrics', {})}")
            else:
                print(f"⚠️  元数据为空")
                
        else:
            print(f"❌ 混合查询失败: HTTP {response.status_code}")
            print(f"   错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 混合查询异常: {e}")

def test_direct_engine_query():
    """测试直接引擎查询"""
    print("\n⚙️  测试直接引擎查询...")
    
    # 测试文本引擎
    print("   测试文本引擎...")
    url = "http://localhost:5000/api/v2/query/text"
    data = {
        "query": "中芯国际的主要业务",
        "max_results": 5,
        "user_id": "test_user"
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 文本引擎查询成功")
            print(f"      结果数量: {len(result.get('results', []))}")
            
            # 检查结果结构
            results = result.get('results', [])
            if results:
                first_result = results[0]
                print(f"      第一个结果结构: {list(first_result.keys())}")
                print(f"      文档名: {first_result.get('document_name', 'N/A')}")
                print(f"      页码: {first_result.get('page_number', 'N/A')}")
                print(f"      类型: {first_result.get('chunk_type', 'N/A')}")
        else:
            print(f"   ❌ 文本引擎查询失败: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ 文本引擎查询异常: {e}")

def check_system_status():
    """检查系统状态"""
    print("\n📊 检查系统状态...")
    
    try:
        # 检查混合引擎状态
        url = "http://localhost:5000/api/v2/engine/hybrid/status"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            status = response.json()
            print(f"✅ 混合引擎状态正常")
            print(f"   引擎名称: {status.get('engine_name', 'N/A')}")
            print(f"   版本: {status.get('version', 'N/A')}")
            print(f"   状态: {status.get('status', 'N/A')}")
            
            config = status.get('config', {})
            print(f"   图片搜索: {'启用' if config.get('enable_image_search') else '禁用'}")
            print(f"   文本搜索: {'启用' if config.get('enable_text_search') else '禁用'}")
            print(f"   表格搜索: {'启用' if config.get('enable_table_search') else '禁用'}")
            print(f"   优化管道: {'启用' if config.get('enable_optimization_pipeline') else '禁用'}")
        else:
            print(f"❌ 混合引擎状态检查失败: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ 系统状态检查异常: {e}")

def main():
    """主函数"""
    print("🚀 开始测试LLM答案和来源信息修复效果...")
    print("=" * 60)
    
    # 检查系统状态
    check_system_status()
    
    # 测试各种查询
    test_text_query()
    test_hybrid_query()
    test_direct_engine_query()
    
    print("\n" + "=" * 60)
    print("🎯 测试完成！")
    print("\n📋 测试总结:")
    print("1. 如果LLM答案正常生成且长度>50，说明LLM功能正常")
    print("2. 如果来源信息显示正确的文档名和页码，说明元数据提取正常")
    print("3. 如果元数据包含优化管道信息，说明优化管道工作正常")
    print("4. 如果仍有'未知来源'，需要进一步检查文档结构")

if __name__ == "__main__":
    main()
