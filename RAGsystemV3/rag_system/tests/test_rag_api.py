#!/usr/bin/env python3
"""
RAG系统V3 API测试脚本

测试RAG系统的Web API接口功能
"""

import requests
import json
import time
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# API基础地址
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v3/rag"

def test_health():
    """测试健康检查"""
    print("🔍 测试健康检查...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ 健康检查通过")
            print(f"📊 响应: {response.json()}")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False

def test_query():
    """测试智能查询"""
    print("\n🔍 测试智能查询...")
    
    query_data = {
        "query": "中芯国际2025年一季度业绩如何？",
        "query_type": "smart",
        "max_results": 5,
        "relevance_threshold": 0.5,
        "enable_streaming": False
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/query",
            json=query_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result is None:
                print("❌ 智能查询返回空结果")
                return False
                
            print("✅ 智能查询成功")
            print(f"📊 查询类型: {result.get('query_type', 'N/A')}")
            
            # 安全地访问answer字段
            answer = result.get('answer')
            if answer:
                print(f"📊 答案: {answer[:100]}...")
            else:
                print("📊 答案: 无")
                
            # 安全地访问results字段
            results = result.get('results', [])
            print(f"📊 结果数量: {len(results)}")
            return True
        else:
            print(f"❌ 智能查询失败: {response.status_code}")
            print(f"📊 错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 智能查询异常: {e}")
        return False

def test_search():
    """测试内容搜索"""
    print("\n🔍 测试内容搜索...")
    
    search_data = {
        "query": "中芯国际业绩图表",
        "content_type": "image",
        "max_results": 10,
        "similarity_threshold": 0.3
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/search",
            json=search_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 内容搜索成功")
            print(f"📊 查询: {result.get('query', 'N/A')}")
            print(f"📊 结果数量: {result.get('total_count', 0)}")
            print(f"📊 处理时间: {result.get('processing_time', 0):.2f}秒")
            return True
        else:
            print(f"❌ 内容搜索失败: {response.status_code}")
            print(f"📊 错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 内容搜索异常: {e}")
        return False

def test_config():
    """测试配置信息"""
    print("\n🔍 测试配置信息...")
    
    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/config")
        if response.status_code == 200:
            result = response.json()
            print("✅ 配置信息获取成功")
            print(f"📊 状态: {result.get('status', 'N/A')}")
            return True
        else:
            print(f"❌ 配置信息获取失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 配置信息获取异常: {e}")
        return False

def test_stats():
    """测试系统统计"""
    print("\n🔍 测试系统统计...")
    
    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/stats")
        if response.status_code == 200:
            result = response.json()
            print("✅ 系统统计获取成功")
            print(f"📊 状态: {result.get('status', 'N/A')}")
            return True
        else:
            print(f"❌ 系统统计获取失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 系统统计获取异常: {e}")
        return False

def run_rag_api_tests():
    """运行RAG API测试 - 供测试框架调用"""
    try:
        print("\n" + "="*60)
        print("🧪 运行RAG系统V3 API接口测试")
        print("="*60)
        
        # 等待服务启动
        print("⏳ 等待服务启动...")
        time.sleep(2)
        
        # 运行测试
        tests = [
            ("健康检查", test_health),
            ("配置信息", test_config),
            ("系统统计", test_stats),
            ("内容搜索", test_search),
            ("智能查询", test_query),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name}测试异常: {e}")
                results.append((test_name, False))
        
        # 显示测试结果
        print("\n" + "="*50)
        print("📊 测试结果汇总")
        print("="*50)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\n📈 总体结果: {passed}/{total} 测试通过")
        
        if passed == total:
            print("🎉 所有API测试通过！RAG系统V3 API运行正常")
            return True
        else:
            print("⚠️ 部分API测试失败，请检查系统状态")
            return False
            
    except Exception as e:
        print(f"❌ RAG API测试执行失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🧪 RAG系统V3 API测试")
    print("="*50)
    
    # 等待服务启动
    print("⏳ 等待服务启动...")
    time.sleep(2)
    
    # 运行测试
    tests = [
        ("健康检查", test_health),
        ("配置信息", test_config),
        ("系统统计", test_stats),
        ("内容搜索", test_search),
        ("智能查询", test_query),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            results.append((test_name, False))
    
    # 显示测试结果
    print("\n" + "="*50)
    print("📊 测试结果汇总")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📈 总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！RAG系统V3运行正常")
    else:
        print("⚠️ 部分测试失败，请检查系统状态")

if __name__ == "__main__":
    main()
