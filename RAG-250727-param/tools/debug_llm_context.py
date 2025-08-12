#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试LLM上下文构建过程，分析智能过滤引擎的影响
"""

import requests
import json

def debug_llm_context():
    """调试LLM上下文构建过程"""
    
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
                print(f"\n📚 来源信息分析:")
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
                
            # 检查元数据
            if 'metadata' in result:
                print(f"\n🔧 元数据分析:")
                metadata = result['metadata']
                print(f"  查询意图: {metadata.get('query_intent', 'N/A')}")
                print(f"  使用的引擎: {metadata.get('engines_used', [])}")
                print(f"  总结果数: {metadata.get('total_results', 0)}")
                print(f"  优化管道启用: {metadata.get('optimization_enabled', False)}")
                
                # 检查优化详情
                if 'optimization_details' in metadata:
                    opt_details = metadata['optimization_details']
                    print(f"  重排序数量: {opt_details.get('reranked_count', 0)}")
                    print(f"  过滤后数量: {opt_details.get('filtered_count', 0)}")
                    print(f"  过滤后来源数量: {opt_details.get('filtered_sources_count', 0)}")
                    
                    # 检查管道指标
                    if 'pipeline_metrics' in opt_details:
                        metrics = opt_details['pipeline_metrics']
                        print(f"  重排序耗时: {metrics.get('rerank_time', 0):.3f}秒")
                        print(f"  过滤耗时: {metrics.get('filter_time', 0):.3f}秒")
                        print(f"  LLM生成耗时: {metrics.get('llm_time', 0):.3f}秒")
                        print(f"  总耗时: {metrics.get('total_time', 0):.3f}秒")
                
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
    print("🧪 调试LLM上下文构建过程")
    print("=" * 60)
    debug_llm_context()
