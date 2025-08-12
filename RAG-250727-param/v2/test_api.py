"""
API测试脚本 - 验证新的优化功能接口

## 1. 功能特点
- 测试系统状态接口
- 测试优化引擎状态接口
- 测试优化查询接口

## 2. 测试内容
- 系统状态检查
- 优化引擎状态检查
- 优化查询功能测试
"""

import requests
import json
import time

# 测试配置
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api/v2"

def test_system_status():
    """测试系统状态接口"""
    print("🔧 测试系统状态接口...")
    
    try:
        response = requests.get(f"{API_BASE}/status")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                status = data.get('status', {})
                print(f"✅ 系统状态获取成功")
                print(f"  - 系统名称: {status.get('system_name')}")
                print(f"  - 版本: {status.get('version')}")
                print(f"  - 混合引擎就绪: {status.get('hybrid_engine_ready')}")
                print(f"  - 优化管道启用: {status.get('optimization_pipeline_enabled')}")
                return True
            else:
                print(f"❌ 系统状态获取失败: {data.get('error')}")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")
        return False

def test_optimization_status():
    """测试优化引擎状态接口"""
    print("\n🚀 测试优化引擎状态接口...")
    
    try:
        response = requests.get(f"{API_BASE}/engines/optimization")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                optimization_status = data.get('optimization_status', {})
                print(f"✅ 优化引擎状态获取成功")
                
                # 检查各引擎状态
                engines = ['reranking_engine', 'llm_engine', 'smart_filter_engine', 'source_filter_engine']
                for engine in engines:
                    engine_status = optimization_status.get(engine, {})
                    enabled = engine_status.get('enabled', False)
                    status = engine_status.get('status', 'unknown')
                    print(f"  - {engine}: {'✅' if enabled else '❌'} ({status})")
                
                # 检查管道配置
                pipeline_config = optimization_status.get('pipeline_config', {})
                if pipeline_config:
                    print(f"  - 优化管道配置:")
                    print(f"    * 重排序: {pipeline_config.get('enable_reranking')}")
                    print(f"    * LLM生成: {pipeline_config.get('enable_llm_generation')}")
                    print(f"    * 智能过滤: {pipeline_config.get('enable_smart_filtering')}")
                    print(f"    * 源过滤: {pipeline_config.get('enable_source_filtering')}")
                
                return True
            else:
                print(f"❌ 优化引擎状态获取失败: {data.get('error')}")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")
        return False

def test_optimized_query():
    """测试优化查询接口"""
    print("\n🔍 测试优化查询接口...")
    
    try:
        # 测试查询
        test_query = "请介绍一下中芯国际的技术发展情况"
        
        request_data = {
            "query": test_query,
            "max_results": 10,
            "user_id": "test_user",
            "enable_reranking": True,
            "enable_llm_generation": True,
            "enable_smart_filtering": True,
            "enable_source_filtering": True
        }
        
        print(f"发送查询: {test_query}")
        
        response = requests.post(
            f"{API_BASE}/query/optimized",
            json=request_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ 优化查询成功")
                print(f"  - 查询: {data.get('query')}")
                print(f"  - 结果数量: {data.get('total_count')}")
                print(f"  - 处理时间: {data.get('processing_time', 0):.2f}秒")
                print(f"  - 查询类型: {data.get('query_type')}")
                print(f"  - 优化启用: {data.get('optimization_enabled')}")
                
                # 显示优化详情
                optimization_details = data.get('optimization_details', {})
                if optimization_details:
                    print(f"  - 优化详情:")
                    print(f"    * 重排序数量: {optimization_details.get('reranked_count', 0)}")
                    print(f"    * 过滤后数量: {optimization_details.get('filtered_count', 0)}")
                    print(f"    * 源过滤数量: {optimization_details.get('filtered_sources_count', 0)}")
                
                # 显示结果
                results = data.get('results', [])
                if results:
                    print(f"  - 查询结果:")
                    for i, result in enumerate(results[:3]):  # 只显示前3个结果
                        content = result.get('content', str(result))
                        print(f"    {i+1}. {content[:100]}{'...' if len(content) > 100 else ''}")
                
                return True
            else:
                print(f"❌ 优化查询失败: {data.get('error')}")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")
        return False

def test_benchmark():
    """测试基准测试接口"""
    print("\n⚡ 测试基准测试接口...")
    
    try:
        request_data = {
            "query": "测试查询",
            "test_type": "optimized",
            "iterations": 2
        }
        
        response = requests.post(
            f"{API_BASE}/query/benchmark",
            json=request_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                benchmark = data.get('benchmark', {})
                print(f"✅ 基准测试成功")
                print(f"  - 测试类型: {benchmark.get('test_type')}")
                print(f"  - 迭代次数: {benchmark.get('iterations')}")
                print(f"  - 平均时间: {benchmark.get('average_time', 0):.2f}秒")
                print(f"  - 最小时间: {benchmark.get('min_time', 0):.2f}秒")
                print(f"  - 最大时间: {benchmark.get('max_time', 0):.2f}秒")
                print(f"  - 总时间: {benchmark.get('total_time', 0):.2f}秒")
                
                return True
            else:
                print(f"❌ 基准测试失败: {data.get('error')}")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始API功能测试...")
    print("=" * 50)
    
    # 检查服务器是否运行
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ 服务器未正常运行，请先启动服务器")
            return
    except:
        print("❌ 无法连接到服务器，请先启动服务器")
        return
    
    print("✅ 服务器连接正常，开始测试...\n")
    
    # 执行测试
    tests = [
        ("系统状态", test_system_status),
        ("优化引擎状态", test_optimization_status),
        ("优化查询", test_optimized_query),
        ("基准测试", test_benchmark)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {str(e)}")
            results.append((test_name, False))
    
    # 显示测试结果
    print("\n" + "=" * 50)
    print("📋 测试结果总结:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  - {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 测试完成: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！API功能正常")
    else:
        print("⚠️ 部分测试失败，请检查相关功能")

if __name__ == "__main__":
    main()
