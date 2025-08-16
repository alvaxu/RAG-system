'''
程序说明：
## 1. 测试重复重排序问题修复
## 2. 验证TextEngine使用新Pipeline后，HybridEngine不再重复调用老Pipeline
## 3. 检查整个流程的日志输出
'''

import requests
import json
import time

def test_text_query_no_duplicate_reranking():
    """测试文本查询，检查是否还有重复重排序"""
    
    print("🔍 测试文本查询，检查重复重排序问题修复...")
    
    # 测试查询
    query = "中芯国际的主要业务和核心技术是什么？"
    
    # 发送查询请求
    url = "http://127.0.0.1:5000/api/v2/query/text"
    payload = {
        "query": query,
        "query_type": "text",
        "max_results": 10
    }
    
    try:
        print(f"📤 发送查询: {query}")
        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 查询成功")
            
            # 检查结果
            if result.get('success'):
                print(f"📊 查询结果:")
                print(f"  - 总结果数: {result.get('total_count', 0)}")
                print(f"  - 处理时间: {result.get('processing_time', 0):.2f}秒")
                
                # 检查元数据
                metadata = result.get('metadata', {})
                print(f"  - Pipeline类型: {metadata.get('pipeline', 'unknown')}")
                
                if 'llm_answer' in metadata:
                    llm_answer = metadata['llm_answer']
                    print(f"  - LLM答案长度: {len(llm_answer)}")
                    print(f"  - LLM答案预览: {llm_answer[:100]}...")
                
                if 'pipeline_metrics' in metadata:
                    pipeline_metrics = metadata['pipeline_metrics']
                    print(f"  - Pipeline指标: {pipeline_metrics}")
                
                # 检查是否有重复重排序的迹象
                if 'optimization_details' in metadata:
                    opt_details = metadata['optimization_details']
                    print(f"  - 优化详情: {opt_details}")
                    
                    # 检查是否使用了新Pipeline
                    if opt_details.get('pipeline') == 'unified_pipeline':
                        print("✅ 成功使用新的统一Pipeline")
                    else:
                        print("⚠️ 仍在使用老的优化管道")
                
            else:
                print(f"❌ 查询失败: {result.get('error_message', '未知错误')}")
                
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求异常: {e}")
    except Exception as e:
        print(f"❌ 其他异常: {e}")

def check_server_status():
    """检查服务器状态"""
    try:
        response = requests.get("http://127.0.0.1:5000/v2", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器运行正常")
            return True
        else:
            print(f"⚠️ 服务器状态异常: {response.status_code}")
            return False
    except:
        print("❌ 无法连接到服务器")
        return False

if __name__ == "__main__":
    print("🚀 开始测试重复重排序问题修复...")
    
    # 检查服务器状态
    if not check_server_status():
        print("请先启动V2 Web服务器")
        exit(1)
    
    # 等待一下让服务完全启动
    print("⏳ 等待服务完全启动...")
    time.sleep(3)
    
    # 测试查询
    test_text_query_no_duplicate_reranking()
    
    print("\n🎯 测试完成！")
    print("请检查控制台输出，确认是否还有重复重排序的问题")
