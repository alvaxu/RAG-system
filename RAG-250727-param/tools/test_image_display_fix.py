#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
程序说明：

## 1. 测试图片显示修复
测试混合查询API是否正确返回image_results字段，以及图片显示功能

## 2. 测试来源详情修复
测试来源详情是否正确显示文档名称，而不是"未知文档"

## 3. 调试信息输出
输出详细的API响应信息，帮助诊断问题
"""

import requests
import json
import time
from datetime import datetime

def test_image_query():
    """测试图片查询功能"""
    print("🖼️  测试图片查询功能")
    print("=" * 50)
    
    # 测试图片查询
    url = "http://localhost:5000/api/v2/qa/ask"
    
    test_cases = [
        {
            "name": "图片查询 - 图4",
            "data": {
                "question": "图4",
                "query_type": "image",
                "max_results": 5,
                "user_id": "test_user"
            }
        },
        {
            "name": "混合查询 - 包含图片",
            "data": {
                "question": "中芯国际的财务数据图表",
                "query_type": "hybrid",
                "max_results": 5,
                "user_id": "test_user"
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📋 测试用例: {test_case['name']}")
        print("-" * 30)
        
        try:
            start_time = time.time()
            response = requests.post(url, json=test_case['data'], timeout=30)
            processing_time = time.time() - start_time
            
            print(f"⏱️  响应时间: {processing_time:.2f}秒")
            print(f"📊 HTTP状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 查询成功")
                print(f"📝 答案长度: {len(data.get('answer', ''))}")
                print(f"🔍 来源数量: {len(data.get('sources', []))}")
                
                # 检查图片结果
                image_results = data.get('image_results', [])
                print(f"🖼️  图片结果数量: {len(image_results)}")
                
                if image_results:
                    print("📸 图片结果详情:")
                    for i, img in enumerate(image_results):
                        print(f"  图片 {i+1}:")
                        print(f"    - 路径: {img.get('image_path', 'N/A')}")
                        print(f"    - 标题: {img.get('caption', 'N/A')}")
                        print(f"    - 描述: {img.get('enhanced_description', 'N/A')[:100]}...")
                        print(f"    - 文档名: {img.get('document_name', 'N/A')}")
                        print(f"    - 页码: {img.get('page_number', 'N/A')}")
                        print(f"    - 分数: {img.get('score', 'N/A')}")
                else:
                    print("⚠️  没有图片结果")
                
                # 检查来源详情
                sources = data.get('sources', [])
                if sources:
                    print("\n📚 来源详情:")
                    for i, source in enumerate(sources):
                        print(f"  来源 {i+1}:")
                        print(f"    - 类型: {source.get('source_type', 'N/A')}")
                        print(f"    - 标题: {source.get('title', 'N/A')}")
                        print(f"    - 文档名: {source.get('document_name', 'N/A')}")
                        print(f"    - 页码: {source.get('page_number', 'N/A')}")
                        print(f"    - 格式化来源: {source.get('formatted_source', 'N/A')}")
                        print(f"    - 分数: {source.get('score', 'N/A')}")
                        
                        # 检查是否有图片路径
                        if source.get('image_path'):
                            print(f"    - 图片路径: {source.get('image_path')}")
                        
                        # 检查是否有增强描述
                        if source.get('enhanced_description'):
                            print(f"    - 增强描述: {source.get('enhanced_description')[:100]}...")
                
                # 检查元数据
                metadata = data.get('metadata', {})
                if metadata:
                    print(f"\n🔧 元数据:")
                    print(f"  - 查询意图: {metadata.get('query_intent', 'N/A')}")
                    print(f"  - 使用的引擎: {metadata.get('engines_used', 'N/A')}")
                    print(f"  - 总结果数: {metadata.get('total_results', 'N/A')}")
                    print(f"  - 优化启用: {metadata.get('optimization_enabled', 'N/A')}")
                    
                    # 检查优化详情
                    optimization_details = metadata.get('optimization_details', {})
                    if optimization_details:
                        print(f"  - 优化详情: {json.dumps(optimization_details, ensure_ascii=False, indent=2)}")
                
            else:
                print(f"❌ 查询失败: {response.text}")
                
        except requests.exceptions.Timeout:
            print("⏰ 请求超时")
        except requests.exceptions.ConnectionError:
            print("🔌 连接错误，请检查服务器是否运行")
        except Exception as e:
            print(f"💥 其他错误: {str(e)}")
        
        print("\n" + "=" * 50)

def test_text_query():
    """测试文本查询功能"""
    print("\n📝 测试文本查询功能")
    print("=" * 50)
    
    url = "http://localhost:5000/api/v2/qa/ask"
    
    test_data = {
        "question": "中芯国际的业绩如何",
        "query_type": "text",
        "max_results": 5,
        "user_id": "test_user"
    }
    
    try:
        start_time = time.time()
        response = requests.post(url, json=test_data, timeout=30)
        processing_time = time.time() - start_time
        
        print(f"⏱️  响应时间: {processing_time:.2f}秒")
        print(f"📊 HTTP状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 查询成功")
            print(f"📝 答案长度: {len(data.get('answer', ''))}")
            print(f"🔍 来源数量: {len(data.get('sources', []))}")
            
            # 检查来源详情
            sources = data.get('sources', [])
            if sources:
                print("\n📚 来源详情:")
                for i, source in enumerate(sources):
                    print(f"  来源 {i+1}:")
                    print(f"    - 类型: {source.get('source_type', 'N/A')}")
                    print(f"    - 标题: {source.get('title', 'N/A')}")
                    print(f"    - 文档名: {source.get('document_name', 'N/A')}")
                    print(f"    - 页码: {source.get('page_number', 'N/A')}")
                    print(f"    - 格式化来源: {source.get('formatted_source', 'N/A')}")
                    print(f"    - 分数: {source.get('score', 'N/A')}")
                    
                    # 检查内容预览
                    if source.get('content_preview'):
                        print(f"    - 内容预览: {source.get('content_preview')[:100]}...")
        else:
            print(f"❌ 查询失败: {response.text}")
            
    except Exception as e:
        print(f"💥 错误: {str(e)}")

def main():
    """主函数"""
    print("🚀 RAG系统图片显示和来源详情修复测试")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 测试图片查询
    test_image_query()
    
    # 测试文本查询
    test_text_query()
    
    print("\n🎯 测试完成！")
    print("\n📋 检查要点:")
    print("1. ✅ 图片查询是否返回image_results字段")
    print("2. ✅ 图片结果是否包含正确的图片路径和描述")
    print("3. ✅ 来源详情是否显示正确的文档名称（不是'未知文档'）")
    print("4. ✅ 图片是否能在前端正确显示")
    print("5. ✅ 来源详情的格式是否正确")

if __name__ == "__main__":
    main()

