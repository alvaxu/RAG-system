#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：验证前端修复效果
测试内容：
1. 预设问题显示
2. 查询类型切换
3. 记忆管理功能
"""

import requests
import json
import time

def test_preset_questions():
    """测试预设问题加载"""
    print("🔍 测试预设问题加载...")
    
    try:
        # 测试文本类型预设问题
        response = requests.get('http://localhost:5000/api/v2/qa/preset-questions?type=text')
        if response.ok:
            data = response.json()
            print(f"✅ 文本类型预设问题加载成功: {len(data.get('questions', []))} 个问题")
            for i, q in enumerate(data.get('questions', [])[:3]):
                print(f"   {i+1}. {q}")
        else:
            print(f"❌ 文本类型预设问题加载失败: {response.status_code}")
            
        # 测试图片类型预设问题
        response = requests.get('http://localhost:5000/api/v2/qa/preset-questions?type=image')
        if response.ok:
            data = response.json()
            print(f"✅ 图片类型预设问题加载成功: {len(data.get('questions', []))} 个问题")
        else:
            print(f"❌ 图片类型预设问题加载失败: {response.status_code}")
            
        # 测试表格类型预设问题
        response = requests.get('http://localhost:5000/api/v2/qa/preset-questions?type=table')
        if response.ok:
            data = response.json()
            print(f"✅ 表格类型预设问题加载成功: {len(data.get('questions', []))} 个问题")
        else:
            print(f"❌ 表格类型预设问题加载失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 测试预设问题失败: {e}")

def test_memory_stats():
    """测试记忆统计功能"""
    print("\n🧠 测试记忆统计功能...")
    
    try:
        response = requests.get('http://localhost:5000/api/v2/memory/stats')
        if response.ok:
            data = response.json()
            stats = data.get('stats', {})
            print(f"✅ 记忆统计获取成功:")
            print(f"   会话记忆: {stats.get('session_memory_count', 0)}")
            print(f"   用户记忆: {stats.get('user_memory_count', 0)}")
        else:
            print(f"❌ 记忆统计获取失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 测试记忆统计失败: {e}")

def test_query_types():
    """测试不同查询类型"""
    print("\n🔍 测试不同查询类型...")
    
    test_questions = {
        'text': '中芯国际的主要业务是什么？',
        'image': '中芯国际的产能利用率图表',
        'table': '中芯国际的财务数据表格'
    }
    
    for query_type, question in test_questions.items():
        try:
            print(f"\n📝 测试 {query_type} 查询: {question}")
            
            payload = {
                'question': question,
                'query_type': query_type,
                'session_id': f'test_session_{int(time.time())}'
            }
            
            response = requests.post(
                'http://localhost:5000/api/v2/qa/ask',
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.ok:
                data = response.json()
                if data.get('success'):
                    print(f"✅ {query_type} 查询成功")
                    print(f"   答案长度: {len(data.get('answer', ''))}")
                    print(f"   来源数量: {len(data.get('sources', []))}")
                    
                    # 检查来源类型
                    sources = data.get('sources', [])
                    if sources:
                        source_types = set()
                        for source in sources[:3]:  # 只检查前3个
                            if 'formatted_source' in source:
                                source_text = source['formatted_source']
                                if '文本' in source_text:
                                    source_types.add('text')
                                elif '图片' in source_text:
                                    source_types.add('image')
                                elif '表格' in source_text:
                                    source_types.add('table')
                        
                        print(f"   来源类型: {', '.join(source_types)}")
                        
                        # 验证查询类型是否正确
                        if query_type == 'text' and 'table' in source_types:
                            print(f"   ⚠️  警告: 文本查询返回了表格内容")
                        elif query_type == 'image' and 'text' in source_types:
                            print(f"   ⚠️  警告: 图片查询返回了文本内容")
                        elif query_type == 'table' and 'text' in source_types:
                            print(f"   ⚠️  警告: 表格查询返回了文本内容")
                        else:
                            print(f"   ✅ 来源类型符合预期")
                else:
                    print(f"❌ {query_type} 查询失败: {data.get('error', '未知错误')}")
            else:
                print(f"❌ {query_type} 查询HTTP错误: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 测试 {query_type} 查询失败: {e}")
        
        time.sleep(1)  # 避免请求过快

def main():
    """主测试函数"""
    print("🚀 开始测试前端修复效果...")
    print("=" * 50)
    
    # 测试预设问题
    test_preset_questions()
    
    # 测试记忆统计
    test_memory_stats()
    
    # 测试查询类型
    test_query_types()
    
    print("\n" + "=" * 50)
    print("🎯 测试完成！")
    print("\n📋 测试结果说明:")
    print("1. 预设问题: 应该能正确加载和显示")
    print("2. 记忆管理: 应该能正确获取统计信息")
    print("3. 查询类型: 应该根据query_type正确过滤结果")
    print("4. 来源类型: 应该与查询类型匹配")

if __name__ == "__main__":
    main()
