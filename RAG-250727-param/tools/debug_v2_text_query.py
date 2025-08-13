#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试V2文本查询问题的脚本

## 1. 功能特点
- 测试V2混合引擎的文本查询功能
- 检查各个组件的初始化状态
- 诊断查询类型处理逻辑
- 对比不同API接口的响应

## 2. 与其他版本的不同点
- 专门针对V2系统的调试脚本
- 深入检查混合引擎的内部状态
"""

import sys
import os
import requests
import json
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_v2_system_status():
    """测试V2系统状态"""
    print("🔍 测试V2系统状态...")
    
    base_url = "http://localhost:5000"
    
    try:
        response = requests.get(f"{base_url}/api/v2/status")
        if response.status_code == 200:
            result = response.json()
            print("✅ V2系统状态正常")
            print(f"   系统名称: {result.get('status', {}).get('system_name', 'N/A')}")
            print(f"   版本: {result.get('status', {}).get('version', 'N/A')}")
            print(f"   混合引擎就绪: {result.get('status', {}).get('hybrid_engine_ready', 'N/A')}")
            print(f"   文本引擎就绪: {result.get('status', {}).get('text_engine_ready', 'N/A')}")
            print(f"   图片引擎就绪: {result.get('status', {}).get('image_engine_ready', 'N/A')}")
            print(f"   表格引擎就绪: {result.get('status', {}).get('table_engine_ready', 'N/A')}")
            print(f"   优化管道启用: {result.get('status', {}).get('optimization_pipeline_enabled', 'N/A')}")
        else:
            print(f"❌ V2系统状态检查失败: {response.status_code}")
            print(f"   响应: {response.text}")
    except Exception as e:
        print(f"❌ V2系统状态检查异常: {e}")

def test_direct_text_query():
    """测试直接文本查询接口"""
    print("\n🔍 测试直接文本查询接口...")
    
    base_url = "http://localhost:5000"
    
    try:
        response = requests.post(f"{base_url}/api/v2/query/text", json={
            "query": "中芯国际的主要业务和核心技术是什么？",
            "max_results": 10
        })
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 直接文本查询成功")
            print(f"   结果数量: {len(result.get('results', []))}")
            print(f"   查询类型: {result.get('query_type', 'N/A')}")
            
            # 显示前3个结果
            for i, doc in enumerate(result.get('results', [])[:3]):
                print(f"   结果{i+1}:")
                print(f"     ID: {doc.get('id', 'N/A')}")
                print(f"     文档名: {doc.get('document_name', 'N/A')}")
                print(f"     类型: {doc.get('chunk_type', 'N/A')}")
                print(f"     分数: {doc.get('score', 'N/A')}")
        else:
            print(f"❌ 直接文本查询失败: {response.status_code}")
            print(f"   响应: {response.text}")
    except Exception as e:
        print(f"❌ 直接文本查询异常: {e}")

def test_qa_ask_with_text_type():
    """测试qa/ask接口的文本查询类型"""
    print("\n🔍 测试qa/ask接口的文本查询类型...")
    
    base_url = "http://localhost:5000"
    
    try:
        response = requests.post(f"{base_url}/api/v2/qa/ask", json={
            "question": "中芯国际的主要业务和核心技术是什么？",
            "query_type": "text",
            "max_results": 10
        })
        
        if response.status_code == 200:
            result = response.json()
            print("✅ qa/ask文本查询成功")
            print(f"   成功状态: {result.get('success', 'N/A')}")
            print(f"   查询类型: {result.get('query_type', 'N/A')}")
            print(f"   答案长度: {len(result.get('answer', ''))}")
            print(f"   来源数量: {len(result.get('sources', []))}")
            
            if result.get('error'):
                print(f"   ❌ 错误信息: {result.get('error')}")
            
            # 显示来源信息
            sources = result.get('sources', [])
            if sources:
                print(f"   前3个来源:")
                for i, source in enumerate(sources[:3]):
                    print(f"     来源{i+1}: {source.get('document_name', 'N/A')} - {source.get('chunk_type', 'N/A')}")
        else:
            print(f"❌ qa/ask文本查询失败: {response.status_code}")
            print(f"   响应: {response.text}")
    except Exception as e:
        print(f"❌ qa/ask文本查询异常: {e}")

def test_qa_ask_with_hybrid_type():
    """测试qa/ask接口的混合查询类型"""
    print("\n🔍 测试qa/ask接口的混合查询类型...")
    
    base_url = "http://localhost:5000"
    
    try:
        response = requests.post(f"{base_url}/api/v2/qa/ask", json={
            "question": "中芯国际的主要业务和核心技术是什么？",
            "query_type": "hybrid",
            "max_results": 10
        })
        
        if response.status_code == 200:
            result = response.json()
            print("✅ qa/ask混合查询成功")
            print(f"   成功状态: {result.get('success', 'N/A')}")
            print(f"   查询类型: {result.get('query_type', 'N/A')}")
            print(f"   答案长度: {len(result.get('answer', ''))}")
            print(f"   来源数量: {len(result.get('sources', []))}")
            
            if result.get('error'):
                print(f"   ❌ 错误信息: {result.get('error')}")
            
            # 显示来源信息
            sources = result.get('sources', [])
            if sources:
                print(f"   前3个来源:")
                for i, source in enumerate(sources[:3]):
                    print(f"     来源{i+1}: {source.get('document_name', 'N/A')} - {source.get('chunk_type', 'N/A')}")
        else:
            print(f"❌ qa/ask混合查询失败: {response.status_code}")
            print(f"   响应: {response.text}")
    except Exception as e:
        print(f"❌ qa/ask混合查询异常: {e}")

def test_error_handling():
    """测试错误处理"""
    print("\n🔍 测试错误处理...")
    
    base_url = "http://localhost:5000"
    
    # 测试无效的查询类型
    try:
        response = requests.post(f"{base_url}/api/v2/qa/ask", json={
            "question": "测试问题",
            "query_type": "invalid_type",
            "max_results": 10
        })
        
        if response.status_code == 400:
            result = response.json()
            print("✅ 错误处理正常 - 无效查询类型被正确拒绝")
            print(f"   错误信息: {result.get('error', 'N/A')}")
        else:
            print(f"⚠️ 错误处理异常 - 无效查询类型返回状态码: {response.status_code}")
            print(f"   响应: {response.text}")
    except Exception as e:
        print(f"❌ 错误处理测试异常: {e}")

def main():
    """主函数"""
    print("🚀 开始调试V2文本查询问题...")
    print("=" * 60)
    
    # 测试V2系统状态
    test_v2_system_status()
    
    # 测试直接文本查询接口
    test_direct_text_query()
    
    # 测试qa/ask接口的文本查询类型
    test_qa_ask_with_text_type()
    
    # 测试qa/ask接口的混合查询类型
    test_qa_ask_with_hybrid_type()
    
    # 测试错误处理
    test_error_handling()
    
    print("\n" + "=" * 60)
    print("🏁 调试完成")
    print("\n📋 问题诊断建议:")
    print("1. 检查V2系统状态，确保所有引擎都正确初始化")
    print("2. 对比直接文本查询和qa/ask文本查询的结果差异")
    print("3. 检查混合引擎的查询类型处理逻辑")
    print("4. 查看服务器日志，获取详细的错误信息")

if __name__ == "__main__":
    main()
