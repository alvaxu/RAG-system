#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试智能查询功能的脚本 - 优化版本
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
            "question": "请帮我分析一下这个图片中的表格数据，特别是表格ID为table_656716的内容", 
            "query_type": "smart",
            "expected_type": "image",  # 明确要求分析图片中的表格
            "description": "图片分析查询"
        },
        {
            "question": "中芯国际2024年的财务数据表格，包括营收、净利润等关键指标", 
            "query_type": "smart",
            "expected_type": "table",  # 明确要求财务数据表格
            "description": "表格数据查询"
        },
        {
            "question": "中芯国际在2024年的最新发展动态和行业新闻", 
            "query_type": "smart",
            "expected_type": "text",   # 明确要求文本新闻信息
            "description": "文本新闻查询"
        },
        {
            "question": "请综合分析中芯国际的技术实力、财务状况、市场表现和未来发展前景", 
            "query_type": "smart",
            "expected_type": "hybrid", # 需要综合分析，确实应该是混合
            "description": "综合分析查询"
        },
        {
            "question": "中芯国际的股价走势图，最近一年的表现如何？", 
            "query_type": "smart",
            "expected_type": "image",  # 明确要求股价走势图
            "description": "图表分析查询"
        },
        {
            "question": "中芯国际的产能利用率数据，包括各季度的具体数值", 
            "query_type": "smart",
            "expected_type": "table",  # 明确要求具体数据表格
            "description": "数据表格查询"
        },
        {
            "question": "中芯国际在半导体行业的技术优势和核心竞争力分析", 
            "query_type": "smart",
            "expected_type": "text",   # 明确要求文本分析
            "description": "技术分析查询"
        },
        {
            "question": "中芯国际的全球布局、技术发展、财务状况和市场前景的全面评估", 
            "query_type": "smart",
            "expected_type": "hybrid", # 全面评估，需要多引擎
            "description": "全面评估查询"
        }
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for i, case in enumerate(test_cases):
        print(f"\n--- 测试用例 {i+1}: {case['description']} ---")
        print(f"查询: {case['question']}")
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
            engines_used = metadata.get('engines_used', [])
            print(f"引擎使用情况: {engines_used}")
            print(f"优化管道启用: {metadata.get('optimization_enabled', 'N/A')}")
            
            # 判断测试是否成功
            if result.get('success'):
                # 检查引擎选择是否符合期望
                if case['expected_type'] == 'hybrid':
                    # 混合查询应该使用多个引擎
                    if len(engines_used) > 1:
                        print("✅ 混合查询测试成功！使用了多个引擎")
                        success_count += 1
                    else:
                        print("❌ 混合查询测试失败！应该使用多个引擎")
                else:
                    # 单一类型查询应该主要使用对应引擎
                    if case['expected_type'] in engines_used:
                        print("✅ 单一类型查询测试成功！使用了期望的引擎")
                        success_count += 1
                    else:
                        print(f"❌ 单一类型查询测试失败！期望使用 {case['expected_type']} 引擎，实际使用 {engines_used}")
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
        
    print(f"\n🎉 Web API智能查询功能测试完成。成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")

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
        
        # 测试智能查询 - 使用更明确的测试用例
        test_cases = [
            {
                "question": "请帮我分析一下这个图片中的表格数据，特别是表格ID为table_656716的内容",
                "expected_type": "image",
                "description": "图片分析查询"
            },
            {
                "question": "中芯国际2024年的财务数据表格，包括营收、净利润等关键指标",
                "expected_type": "table",
                "description": "表格数据查询"
            },
            {
                "question": "中芯国际在2024年的最新发展动态和行业新闻",
                "expected_type": "text",
                "description": "文本新闻查询"
            },
            {
                "question": "中芯国际的股价走势图，最近一年的表现如何？",
                "expected_type": "image",
                "description": "图表分析查询"
            },
            {
                "question": "中芯国际的产能利用率数据，包括各季度的具体数值",
                "expected_type": "table",
                "description": "数据表格查询"
            }
        ]
        
        success_count = 0
        total_count = len(test_cases)
        
        for i, case in enumerate(test_cases):
            print(f"\n--- 测试用例 {i+1}: {case['description']} ---")
            print(f"查询: {case['question']}")
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
                success_count += 1
            else:
                print("❌ 命令行智能查询测试失败！")
                print(f"错误信息: {result.get('error', 'N/A')}")
                
        print(f"\n🎉 命令行智能查询功能测试完成。成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
                
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        
    print("\n🎉 命令行智能查询功能测试完成。")

if __name__ == "__main__":
    print("🧠 智能查询功能测试 - 优化版本")
    print("=" * 60)
    print("📝 测试说明:")
    print("- 优化了测试用例，使查询更加明确")
    print("- 调整了期望类型，使其更符合实际查询意图")
    print("- 增加了成功率统计")
    print("=" * 60)
    
    # 测试Web API
    test_web_api_smart_query()
    
    # 测试命令行
    test_command_line_smart_query()
    
    print("\n🎉 所有测试完成！")
