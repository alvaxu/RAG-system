#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试文本查询API修复的脚本
用于验证文本查询API现在是否正确通过优化管道处理并显示来源信息
"""

import requests
import json
import time

# 定义基础URL
base_url = "http://localhost:5000"

def test_text_query_api():
    """测试文本查询API"""
    print("🔍 测试文本查询API...")
    
    url = f"{base_url}/api/v2/query/text"
    data = {
        "query": "中芯国际的产能利用率如何？",
        "max_results": 10
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            print("✅ 文本查询API测试成功")
            print(f"   状态: {result.get('status', 'N/A')}")
            print(f"   结果数量: {len(result.get('results', []))}")
            
            # 显示前3个结果
            for i, doc in enumerate(result.get('results', [])[:3]):
                print(f"   结果{i+1}:")
                print(f"     ID: {doc.get('id', 'N/A')}")
                print(f"     文档名: {doc.get('document_name', 'N/A')}")
                print(f"     页码: {doc.get('page_number', 'N/A')}")
                print(f"     类型: {doc.get('chunk_type', 'N/A')}")
                print(f"     分数: {doc.get('score', 'N/A')}")
                print(f"     内容预览: {doc.get('content', 'N/A')[:100]}...")
        else:
            print(f"❌ 文本查询API测试失败: {response.status_code}")
            print(f"   响应: {response.text}")
    except Exception as e:
        print(f"❌ 文本查询API测试异常: {e}")

def test_hybrid_query_api():
    """测试混合查询API作为对比"""
    print("\n🔍 测试混合查询API作为对比...")
    
    url = f"{base_url}/api/v2/qa/ask"
    data = {
        "question": "中芯国际的产能利用率如何？",
        "query_type": "hybrid",
        "max_results": 10
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            print("✅ 混合查询API测试成功")
            print(f"   状态: {result.get('status', 'N/A')}")
            print(f"   结果数量: {len(result.get('results', []))}")
            
            # 显示前3个结果
            for i, doc in enumerate(result.get('results', [])[:3]):
                print(f"   结果{i+1}:")
                print(f"     ID: {doc.get('id', 'N/A')}")
                print(f"     文档名: {doc.get('document_name', 'N/A')}")
                print(f"     页码: {doc.get('page_number', 'N/A')}")
                print(f"     类型: {doc.get('chunk_type', 'N/A')}")
                print(f"     分数: {doc.get('score', 'N/A')}")
                print(f"     内容预览: {doc.get('content', 'N/A')[:100]}...")
        else:
            print(f"❌ 混合查询API测试失败: {response.status_code}")
            print(f"   响应: {response.text}")
    except Exception as e:
        print(f"❌ 混合查询测试异常: {e}")

def main():
    """主函数"""
    print("🚀 开始测试文本查询API修复...")
    print("=" * 50)
    
    # 测试文本查询API
    test_text_query_api()
    
    # 测试混合查询API作为对比
    test_hybrid_query_api()
    
    print("\n" + "=" * 50)
    print("🏁 测试完成")

if __name__ == "__main__":
    main()
