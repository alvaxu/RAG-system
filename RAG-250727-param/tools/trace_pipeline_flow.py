#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跟踪优化管道流程，分析每个步骤的数据变化
"""

import requests
import json

def trace_pipeline_flow():
    """跟踪优化管道流程"""
    
    url = "http://127.0.0.1:5000/api/v2/qa/ask"
    
    # 测试数据
    data = {
        "question": "中芯国际的主要业务和核心技术是什么？",
        "user_id": "test_user"
    }
    
    try:
        print("🔍 发送测试查询...")
        response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 查询成功!")
            
            # 检查LLM答案
            if 'answer' in result and result['answer']:
                print(f"🤖 LLM答案长度: {len(result['answer'])} 字符")
                print(f"📝 答案内容: {result['answer']}")
            else:
                print("❌ 没有找到LLM答案")
            
            # 检查来源信息
            if 'sources' in result and result['sources']:
                print(f"\n📚 最终来源信息分析:")
                print(f"  总来源数量: {len(result['sources'])}")
                
                # 分析前几个来源的内容长度
                for i, source in enumerate(result['sources'][:5]):
                    content_preview = source.get('content_preview', '')
                    print(f"  来源 {i+1}: {source.get('document_name', 'N/A')} - 第{source.get('page_number', 'N/A')}页")
                    print(f"    内容预览长度: {len(content_preview)} 字符")
                    print(f"    内容预览: {content_preview[:100]}...")
                    print()
            else:
                print("❌ 没有找到来源信息")
                
            # 检查元数据 - 这是关键！
            if 'metadata' in result:
                print(f"\n🔧 优化管道流程分析:")
                metadata = result['metadata']
                print(f"  查询意图: {metadata.get('query_intent', 'N/A')}")
                print(f"  使用的引擎: {metadata.get('engines_used', [])}")
                print(f"  总结果数: {metadata.get('total_results', 0)}")
                print(f"  优化管道启用: {metadata.get('optimization_enabled', False)}")
                
                # 检查优化详情 - 这是关键信息！
                if 'optimization_details' in metadata:
                    opt_details = metadata['optimization_details']
                    print(f"\n📊 优化管道各步骤统计:")
                    print(f"  重排序数量: {opt_details.get('reranked_count', 0)}")
                    print(f"  过滤后数量: {opt_details.get('filtered_count', 0)}")
                    print(f"  过滤后来源数量: {opt_details.get('filtered_sources_count', 0)}")
                    
                    # 检查管道指标
                    if 'pipeline_metrics' in opt_details:
                        metrics = opt_details['pipeline_metrics']
                        print(f"\n⏱️ 各步骤耗时:")
                        print(f"  重排序耗时: {metrics.get('rerank_time', 0):.3f}秒")
                        print(f"  过滤耗时: {metrics.get('filter_time', 0):.3f}秒")
                        print(f"  LLM生成耗时: {metrics.get('llm_time', 0):.3f}秒")
                        print(f"  总耗时: {metrics.get('total_time', 0):.3f}秒")
                        print(f"  输入数量: {metrics.get('input_count', 0)}")
                        print(f"  输出数量: {metrics.get('output_count', 0)}")
                
                # 检查LLM答案是否在元数据中
                if 'llm_answer' in metadata:
                    llm_answer = metadata['llm_answer']
                    if llm_answer:
                        print(f"\n🤖 元数据中的LLM答案:")
                        print(f"  长度: {len(llm_answer)} 字符")
                        print(f"  内容: {llm_answer}")
                    else:
                        print(f"\n❌ 元数据中没有LLM答案")
                else:
                    print(f"\n❌ 元数据中没有llm_answer字段")
                
                # 检查结果列表
                if 'results' in result:
                    results = result['results']
                    print(f"\n📋 结果列表分析:")
                    print(f"  结果总数: {len(results)}")
                    
                    # 检查第一个结果是否是LLM答案
                    if results:
                        first_result = results[0]
                        print(f"  第一个结果类型: {first_result.get('type', 'unknown')}")
                        print(f"  第一个结果内容长度: {len(first_result.get('content', ''))}")
                        print(f"  第一个结果是否主要: {first_result.get('is_primary', False)}")
                        
                        # 检查是否有LLM答案类型的结果
                        llm_results = [r for r in results if r.get('type') == 'llm_answer']
                        if llm_results:
                            print(f"  LLM答案类型结果数量: {len(llm_results)}")
                            for i, llm_result in enumerate(llm_results):
                                print(f"    LLM答案 {i+1}: {len(llm_result.get('content', ''))} 字符")
                        else:
                            print(f"  没有找到LLM答案类型的结果")
                
        else:
            print(f"❌ 查询失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求异常: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析错误: {e}")
    except Exception as e:
        print(f"❌ 其他错误: {e}")

if __name__ == "__main__":
    print("🧪 跟踪优化管道流程")
    print("=" * 60)
    trace_pipeline_flow()
