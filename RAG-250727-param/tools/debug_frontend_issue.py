#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试前端问题的脚本

## 1. 功能特点
- 模拟前端请求，检查网络和响应问题
- 测试不同的请求头和参数
- 检查响应格式和错误处理
- 模拟前端的错误处理逻辑

## 2. 与其他版本的不同点
- 专门针对前端问题的调试脚本
- 模拟真实的浏览器请求行为
"""

import requests
import json
import time

def test_frontend_request_simulation():
    """模拟前端请求，检查问题"""
    print("🔍 模拟前端请求，检查问题...")
    
    base_url = "http://localhost:5000"
    
    # 模拟前端的请求头
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # 测试数据 - 与前端发送的完全一致
    test_data = {
        "question": "中芯国际的主要业务和核心技术是什么？",
        "query_type": "text",
        "max_results": 10
    }
    
    print(f"📤 发送请求:")
    print(f"   URL: {base_url}/api/v2/qa/ask")
    print(f"   方法: POST")
    print(f"   请求头: {headers}")
    print(f"   请求体: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
    
    try:
        # 发送请求
        start_time = time.time()
        response = requests.post(
            f"{base_url}/api/v2/qa/ask",
            json=test_data,
            headers=headers,
            timeout=30
        )
        request_time = time.time() - start_time
        
        print(f"\n📥 收到响应:")
        print(f"   状态码: {response.status_code}")
        print(f"   响应时间: {request_time:.2f}秒")
        print(f"   响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"✅ 请求成功，响应解析正常")
                print(f"   成功状态: {result.get('success', 'N/A')}")
                print(f"   查询类型: {result.get('query_type', 'N/A')}")
                print(f"   答案长度: {len(result.get('answer', ''))}")
                print(f"   来源数量: {len(result.get('sources', []))}")
                
                # 检查是否有错误信息
                if result.get('error'):
                    print(f"   ⚠️ 响应中包含错误信息: {result.get('error')}")
                
                # 检查响应格式
                print(f"\n🔍 响应格式检查:")
                required_fields = ['success', 'question', 'query_type', 'answer', 'sources']
                for field in required_fields:
                    if field in result:
                        print(f"   ✅ {field}: 存在")
                    else:
                        print(f"   ❌ {field}: 缺失")
                
                # 检查答案内容
                answer = result.get('answer', '')
                if answer:
                    print(f"\n📝 答案内容预览:")
                    print(f"   {answer[:200]}...")
                else:
                    print(f"\n⚠️ 答案内容为空")
                
                # 检查来源信息
                sources = result.get('sources', [])
                if sources:
                    print(f"\n📚 来源信息:")
                    for i, source in enumerate(sources[:3]):
                        print(f"   来源{i+1}:")
                        print(f"     ID: {source.get('id', 'N/A')}")
                        print(f"     文档名: {source.get('document_name', 'N/A')}")
                        print(f"     页码: {source.get('page_number', 'N/A')}")
                        print(f"     类型: {source.get('chunk_type', 'N/A')}")
                        print(f"     分数: {source.get('score', 'N/A')}")
                else:
                    print(f"\n⚠️ 来源信息为空")
                
            except json.JSONDecodeError as e:
                print(f"❌ 响应JSON解析失败: {e}")
                print(f"   响应内容: {response.text[:500]}...")
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"   响应内容: {response.text}")
            
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时")
    except requests.exceptions.ConnectionError:
        print(f"❌ 连接错误")
    except Exception as e:
        print(f"❌ 请求异常: {e}")

def test_error_scenarios():
    """测试错误场景"""
    print("\n🔍 测试错误场景...")
    
    base_url = "http://localhost:5000"
    headers = {'Content-Type': 'application/json'}
    
    # 测试1: 空问题
    print("\n📝 测试1: 空问题")
    try:
        response = requests.post(f"{base_url}/api/v2/qa/ask", json={
            "question": "",
            "query_type": "text"
        }, headers=headers)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 400:
            result = response.json()
            print(f"   错误信息: {result.get('error', 'N/A')}")
    except Exception as e:
        print(f"   异常: {e}")
    
    # 测试2: 缺少必要参数
    print("\n📝 测试2: 缺少必要参数")
    try:
        response = requests.post(f"{base_url}/api/v2/qa/ask", json={
            "query_type": "text"
        }, headers=headers)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 400:
            result = response.json()
            print(f"   错误信息: {result.get('error', 'N/A')}")
    except Exception as e:
        print(f"   异常: {e}")
    
    # 测试3: 无效的查询类型
    print("\n📝 测试3: 无效的查询类型")
    try:
        response = requests.post(f"{base_url}/api/v2/qa/ask", json={
            "question": "测试问题",
            "query_type": "invalid_type"
        }, headers=headers)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 400:
            result = response.json()
            print(f"   错误信息: {result.get('error', 'N/A')}")
    except Exception as e:
        print(f"   异常: {e}")

def test_network_issues():
    """测试网络问题"""
    print("\n🔍 测试网络问题...")
    
    base_url = "http://localhost:5000"
    
    # 测试连接性
    try:
        response = requests.get(f"{base_url}/api/v2/status", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器连接正常")
        else:
            print(f"⚠️ 服务器响应异常: {response.status_code}")
    except requests.exceptions.Timeout:
        print("❌ 服务器连接超时")
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器")
    except Exception as e:
        print(f"❌ 连接测试异常: {e}")
    
    # 测试响应时间
    try:
        start_time = time.time()
        response = requests.get(f"{base_url}/api/v2/status", timeout=10)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            print(f"✅ 响应时间: {response_time:.2f}秒")
            if response_time > 5:
                print("⚠️ 响应时间较长，可能影响用户体验")
        else:
            print(f"⚠️ 响应异常: {response.status_code}")
    except Exception as e:
        print(f"❌ 响应时间测试异常: {e}")

def main():
    """主函数"""
    print("🚀 开始调试前端问题...")
    print("=" * 60)
    
    # 测试前端请求模拟
    test_frontend_request_simulation()
    
    # 测试错误场景
    test_error_scenarios()
    
    # 测试网络问题
    test_network_issues()
    
    print("\n" + "=" * 60)
    print("🏁 前端问题调试完成")
    print("\n📋 问题诊断建议:")
    print("1. 检查前端JavaScript控制台是否有错误信息")
    print("2. 检查网络请求的详细信息（浏览器开发者工具）")
    print("3. 确认前端发送的请求格式与后端期望的一致")
    print("4. 检查是否有CORS或其他跨域问题")

if __name__ == "__main__":
    main()
