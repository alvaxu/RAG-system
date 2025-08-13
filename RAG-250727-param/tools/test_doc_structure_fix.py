#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：验证文档结构修复是否有效
测试内容：
1. 测试 dict_keys(['doc_id', 'doc', 'score', 'match_type']) 结构的处理
2. 验证 chunk_type 字段的正确提取
3. 确认来源信息的正确显示
"""

import requests
import json
import time
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_doc_structure_fix():
    """测试文档结构修复"""
    print("🧪 测试文档结构修复...")
    print("="*80)
    
    # 测试文本查询
    print("📝 测试文本查询...")
    test_text_query()
    
    print("\n" + "="*80)
    
    # 测试混合查询
    print("🔄 测试混合查询...")
    test_hybrid_query()

def test_text_query():
    """测试文本查询"""
    url = "http://localhost:5000/api/v2/qa/ask"
    
    # 测试问题
    test_questions = [
        "中芯国际的主要业务是什么？",
        "中芯国际的产能利用率如何？",
        "中芯国际的工艺技术发展情况"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n🔍 测试问题 {i}: {question}")
        
        payload = {
            "question": question,
            "query_type": "text",
            "user_id": "test_user"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                
                # 检查答案
                answer = result.get('answer', '')
                print(f"   ✅ 答案长度: {len(answer)} 字符")
                if answer:
                    print(f"   📄 答案预览: {answer[:100]}...")
                else:
                    print("   ❌ 答案为空")
                
                # 检查来源
                sources = result.get('sources', [])
                print(f"   📚 来源数量: {len(sources)}")
                
                # 分析来源类型
                source_types = {}
                for source in sources:
                    source_type = source.get('source_type', 'unknown')
                    source_types[source_type] = source_types.get(source_type, 0) + 1
                
                print(f"   🏷️  来源类型分布: {source_types}")
                
                # 检查是否有未知来源
                unknown_sources = [s for s in sources if s.get('source_type') == 'unknown']
                if unknown_sources:
                    print(f"   ⚠️  发现 {len(unknown_sources)} 个未知来源")
                    for i, s in enumerate(unknown_sources[:3]):  # 只显示前3个
                        print(f"      {i+1}. {s.get('formatted_source', 'N/A')}")
                else:
                    print("   ✅ 所有来源都有正确的类型")
                
                # 检查格式化来源
                formatted_sources = [s.get('formatted_source', '') for s in sources]
                print(f"   📋 格式化来源示例:")
                for i, formatted in enumerate(formatted_sources[:3]):  # 只显示前3个
                    print(f"      {i+1}. {formatted}")
                
            else:
                print(f"   ❌ 请求失败: {response.status_code}")
                print(f"   📄 响应内容: {response.text}")
                
        except Exception as e:
            print(f"   ❌ 请求异常: {e}")
        
        time.sleep(1)  # 避免请求过快

def test_hybrid_query():
    """测试混合查询"""
    url = "http://localhost:5000/api/v2/qa/ask"
    
    test_questions = [
        "中芯国际的财务表现如何？",
        "中芯国际的技术发展路线图"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n🔍 测试混合查询 {i}: {question}")
        
        payload = {
            "question": question,
            "query_type": "hybrid",
            "user_id": "test_user"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                
                # 检查答案
                answer = result.get('answer', '')
                print(f"   ✅ 答案长度: {len(answer)} 字符")
                if answer:
                    print(f"   📄 答案预览: {answer[:100]}...")
                else:
                    print("   ❌ 答案为空")
                
                # 检查来源
                sources = result.get('sources', [])
                print(f"   📚 来源数量: {len(sources)}")
                
                # 分析来源类型
                source_types = {}
                for source in sources:
                    source_type = source.get('source_type', 'unknown')
                    source_types[source_type] = source_types.get(source_type, 0) + 1
                
                print(f"   🏷️  来源类型分布: {source_types}")
                
                # 检查是否有未知来源
                unknown_sources = [s for s in sources if s.get('source_type') == 'unknown']
                if unknown_sources:
                    print(f"   ⚠️  发现 {len(unknown_sources)} 个未知来源")
                    for i, s in enumerate(unknown_sources[:3]):  # 只显示前3个
                        print(f"      {i+1}. {s.get('formatted_source', 'N/A')}")
                else:
                    print("   ✅ 所有来源都有正确的类型")
                
            else:
                print(f"   ❌ 请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ 请求异常: {e}")
        
        time.sleep(1)

def check_system_status():
    """检查系统状态"""
    print("🔍 检查系统状态...")
    
    try:
        response = requests.get("http://localhost:5000/api/v2/status", timeout=10)
        if response.status_code == 200:
            status = response.json()
            print(f"   ✅ 系统状态: {status.get('status', 'unknown')}")
            print(f"   📊 数据库状态: {status.get('database_status', 'unknown')}")
        else:
            print(f"   ❌ 状态检查失败: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 状态检查异常: {e}")

def main():
    """主函数"""
    print("🚀 开始测试文档结构修复...")
    
    # 检查系统状态
    check_system_status()
    
    print("\n" + "="*80)
    
    # 运行测试
    test_doc_structure_fix()
    
    print("\n" + "="*80)
    print("✅ 测试完成！")

if __name__ == "__main__":
    main()
