#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试智能查询功能的脚本
"""

import requests
import json
import time

def test_web_api_smart_query():
    """
    测试Web API智能查询功能
    """
    print("🚀 开始测试Web API智能查询功能...")
    
    url = "http://127.0.0.1:5000/api/v2/qa/ask"
    headers = {"Content-Type": "application/json"}
    
    test_cases = [
        {
            "question": "请帮我分析一下这个图片中的表格数据", 
            "query_type": "smart",
            "expected_type": "image"  # 期望检测为图片类型
        },
        {
            "question": "中芯国际的财务数据", 
            "query_type": "smart",
            "expected_type": "table"  # 期望检测为表格类型
        },
        {
            "question": "关于中芯国际的最新新闻", 
            "query_type": "smart",
            "expected_type": "text"   # 期望检测为文本类型
        },
        {
            "question": "请综合分析中芯国际的情况", 
            "query_type": "smart",
            "expected_type": "hybrid" # 期望检测为混合类型
        },
    ]
    
    for i, case in enumerate(test_cases):
        print(f"\n--- 测试用例 {i+1}: {case['question']} (类型: {case['query_type']}) ---")
        print(f"期望检测类型: {case['expected_type']}")
        
        payload = {
            "question": case["question"],
            "session_id": "test_session_web_smart",
            "query_type": case["query_type"],
            "max_results": 10
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            
            result = response.json()
            
            print("📊 查询结果:")
            print(f"状态: {result.get('success', 'N/A')}")
            print(f"答案: {result.get('answer', 'N/A')[:100]}...")  # 截断答案
            print(f"处理时间: {result.get('processing_time', 'N/A'):.2f}秒")
            print(f"查询类型 (后端识别): {result.get('query_type', 'N/A')}")
            
            metadata = result.get('metadata', {})
            print(f"引擎使用情况: {metadata.get('engines_used', 'N/A')}")
            print(f"优化管道启用: {metadata.get('optimization_enabled', 'N/A')}")
            
            if result.get('success'):
                print("✅ Web API智能查询测试成功！")
            else:
                print("❌ Web API智能查询测试失败！")
                print(f"错误信息: {result.get('error', 'N/A')}")
                
        except requests.exceptions.ConnectionError as e:
            print(f"❌ 连接错误: 请确保Flask服务器正在运行 (http://127.0.0.1:5000)。错误: {e}")
            break
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP错误: {e.response.status_code} - {e.response.text}")
            print("❌ Web API智能查询测试失败！")
        except Exception as e:
            print(f"❌ 发生未知错误: {e}")
            print("❌ Web API智能查询测试失败！")
        
        time.sleep(1)  # 间隔1秒
        
    print("\n🎉 Web API智能查询功能测试完成。")

def test_command_line_smart_query():
    """
    测试命令行智能查询功能
    """
    print("\n🚀 开始测试命令行智能查询功能...")
    
    try:
        # 导入必要的模块
        import sys
        import os
        
        # 添加项目根目录到Python路径
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from V800_v2_main import V2RAGSystem
        
        # 初始化系统
        print("📋 初始化V2 RAG系统...")
        system = V2RAGSystem()
        print("✅ 系统初始化成功")
        
        # 测试智能查询
        test_cases = [
            {
                "question": "请帮我分析一下这个图片中的表格数据",
                "expected_type": "image"
            },
            {
                "question": "中芯国际的财务数据",
                "expected_type": "table"
            },
            {
                "question": "关于中芯国际的最新新闻",
                "expected_type": "text"
            }
        ]
        
        for i, case in enumerate(test_cases):
            print(f"\n--- 测试用例 {i+1}: {case['question']} ---")
            print(f"期望检测类型: {case['expected_type']}")
            
            # 执行智能查询
            result = system.ask_question(case['question'], query_type='smart')
            
            print("📊 查询结果:")
            print(f"状态: {result.get('success', 'N/A')}")
            print(f"答案: {result.get('answer', 'N/A')[:100]}...")  # 截断答案
            print(f"来源: {result.get('sources', 'N/A')}")
            
            # 验证结果
            if result.get('success'):
                print("✅ 命令行智能查询测试成功！")
            else:
                print("❌ 命令行智能查询测试失败！")
                print(f"错误信息: {result.get('error', 'N/A')}")
                
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        
    print("\n🎉 命令行智能查询功能测试完成。")

if __name__ == "__main__":
    print("🧠 智能查询功能测试")
    print("=" * 50)
    
    # 测试Web API
    test_web_api_smart_query()
    
    # 测试命令行
    test_command_line_smart_query()
    
    print("\n🎉 所有测试完成！")
