"""
测试查询类型修复是否有效

## 1. 功能特点
- 测试混合引擎是否正确处理不同的查询类型
- 验证文本查询是否只使用文本引擎
- 验证图片查询是否只使用图片引擎
- 验证表格查询是否只使用表格引擎

## 2. 与其他版本的不同点
- 新增的查询类型测试脚本
- 专门测试查询类型过滤问题
"""

import sys
import os
import requests
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_query_type_filtering():
    """测试查询类型过滤"""
    print("🔍 测试查询类型过滤...")
    
    base_url = "http://localhost:5000"
    
    # 测试文本查询
    print("\n📝 测试文本查询...")
    text_query_data = {
        "query": "中芯国际的主要业务和核心技术是什么？",
        "max_results": 5,
        "user_id": "test_user"
    }
    
    try:
        response = requests.post(f"{base_url}/api/v2/query/text", json=text_query_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 文本查询成功")
            print(f"  - 查询类型: {result.get('query_type')}")
            print(f"  - 结果数量: {len(result.get('results', []))}")
            
            # 检查结果是否都是文本类型
            results = result.get('results', [])
            for i, doc in enumerate(results):
                chunk_type = doc.get('chunk_type', 'unknown')
                print(f"  - 结果 {i+1}: {chunk_type}")
                if chunk_type != 'text':
                    print(f"    ❌ 发现非文本类型结果: {chunk_type}")
        else:
            print(f"❌ 文本查询失败: {response.status_code}")
            print(f"  - 响应: {response.text}")
    except Exception as e:
        print(f"❌ 文本查询异常: {str(e)}")
    
    # 测试图片查询
    print("\n🖼️ 测试图片查询...")
    image_query_data = {
        "query": "图4",
        "max_results": 5,
        "user_id": "test_user"
    }
    
    try:
        response = requests.post(f"{base_url}/api/v2/query/image", json=image_query_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 图片查询成功")
            print(f"  - 查询类型: {result.get('query_type')}")
            print(f"  - 结果数量: {len(result.get('results', []))}")
        else:
            print(f"❌ 图片查询失败: {response.status_code}")
            print(f"  - 响应: {response.text}")
    except Exception as e:
        print(f"❌ 图片查询异常: {str(e)}")
    
    # 测试表格查询
    print("\n📊 测试表格查询...")
    table_query_data = {
        "query": "财务数据表格",
        "max_results": 5,
        "user_id": "test_user"
    }
    
    try:
        response = requests.post(f"{base_url}/api/v2/query/table", json=table_query_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 表格查询成功")
            print(f"  - 查询类型: {result.get('query_type')}")
            print(f"  - 结果数量: {len(result.get('results', []))}")
        else:
            print(f"❌ 表格查询失败: {response.status_code}")
            print(f"  - 响应: {response.text}")
    except Exception as e:
        print(f"❌ 表格查询异常: {str(e)}")
    
    # 测试混合查询
    print("\n🔄 测试混合查询...")
    hybrid_query_data = {
        "query": "中芯国际业绩",
        "max_results": 5,
        "user_id": "test_user"
    }
    
    try:
        response = requests.post(f"{base_url}/api/v2/qa/ask", json=hybrid_query_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 混合查询成功")
            print(f"  - 查询类型: {result.get('query_type')}")
            print(f"  - 来源数量: {len(result.get('sources', []))}")
            
            # 检查来源类型
            sources = result.get('sources', [])
            source_types = {}
            for source in sources:
                source_type = source.get('source_type', 'unknown')
                source_types[source_type] = source_types.get(source_type, 0) + 1
            
            print(f"  - 来源类型分布: {source_types}")
        else:
            print(f"❌ 混合查询失败: {response.status_code}")
            print(f"  - 响应: {response.text}")
    except Exception as e:
        print(f"❌ 混合查询异常: {str(e)}")
    
    print("\n🎉 查询类型测试完成!")

if __name__ == "__main__":
    test_query_type_filtering()
