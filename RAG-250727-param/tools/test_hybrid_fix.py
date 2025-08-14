"""
程序说明：
混合查询修正验证测试脚本

## 1. 测试混合查询是否真正使用了所有引擎
## 2. 验证修正后的参数传递是否有效
## 3. 对比修正前后的行为差异
"""

import requests
import json
import time

def test_hybrid_query_fix():
    """测试混合查询修正是否有效"""
    
    # 测试配置
    base_url = "http://localhost:5000"
    test_questions = [
        "中芯国际的整体情况如何？",  # 应该触发混合查询
        "请分析中芯国际的财务数据",  # 应该触发表格查询
        "中芯国际的图片资料有哪些？"  # 应该触发图片查询
    ]
    
    print("🧪 开始测试混合查询修正...")
    print("=" * 50)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n📝 测试 {i}: {question}")
        
        try:
            # 发送混合查询请求
            response = requests.post(
                f"{base_url}/api/v2/qa/ask",
                json={
                    "question": question,
                    "query_type": "hybrid",
                    "session_id": "test_session",
                    "max_results": 10
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 请求成功")
                print(f"📊 查询类型: {data.get('query_type', 'N/A')}")
                print(f"⏱️  处理时间: {data.get('processing_time', 'N/A')}秒")
                print(f"📈 结果数量: {data.get('total_count', 'N/A')}")
                
                # 检查是否有元数据信息
                if 'metadata' in data:
                    metadata = data['metadata']
                    print(f"🔧 使用的引擎: {metadata.get('engines_used', 'N/A')}")
                    print(f"🎯 查询意图: {metadata.get('query_intent', 'N/A')}")
                    print(f"⚡ 优化管道启用: {metadata.get('optimization_enabled', 'N/A')}")
                
                # 检查是否有图片结果
                if 'image_results' in data:
                    print(f"🖼️  图片结果数量: {len(data['image_results'])}")
                
                print(f"💬 答案预览: {data.get('answer', '')[:100]}...")
                
            else:
                print(f"❌ 请求失败: HTTP {response.status_code}")
                print(f"错误信息: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 网络请求错误: {e}")
        except Exception as e:
            print(f"❌ 其他错误: {e}")
        
        print("-" * 30)
        time.sleep(1)  # 避免请求过快
    
    print("\n🎉 测试完成！")
    print("\n📋 预期结果:")
    print("1. 混合查询应该使用所有可用的引擎")
    print("2. 元数据中应该显示 'engines_used' 包含多个引擎")
    print("3. 查询意图应该显示 '基于查询类型 hybrid 的检索'")
    print("4. 优化管道应该正常工作")

if __name__ == "__main__":
    test_hybrid_query_fix()
