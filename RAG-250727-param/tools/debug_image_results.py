#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
程序说明：

## 1. 调试图片结果
检查图片查询API返回的数据结构，确认image_results字段

## 2. 验证数据传递
确认前端是否能正确接收到图片数据
"""

import requests
import json
import time
from datetime import datetime

def debug_image_results():
    """调试图片结果"""
    print("🔍 调试图片查询API返回的数据结构")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    # 测试图片查询
    test_data = {
        "question": "图4",
        "query_type": "image",
        "max_results": 4,
        "user_id": "test_user"
    }
    
    try:
        print("1. 发送图片查询请求...")
        start_time = time.time()
        response = requests.post(f"{base_url}/api/v2/qa/ask", json=test_data, timeout=30)
        processing_time = time.time() - start_time
        
        print(f"   ⏱️  响应时间: {processing_time:.2f}秒")
        print(f"   📊 HTTP状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 查询成功")
            
            # 检查答案
            answer = data.get('answer', '')
            print(f"\n2. 答案内容:")
            print(f"   📝 答案长度: {len(answer)}")
            print(f"   📄 答案内容预览: {answer[:200]}...")
            
            # 检查是否包含图片相关关键词
            image_keywords = ['图片', '图表', '图4', 'enhanced_description']
            for keyword in image_keywords:
                if keyword in answer:
                    print(f"   ✅ 答案中包含: {keyword}")
                else:
                    print(f"   ❌ 答案中不包含: {keyword}")
            
            # 检查图片结果
            image_results = data.get('image_results', [])
            print(f"\n3. 图片结果字段:")
            print(f"   🖼️  image_results字段: {'存在' if 'image_results' in data else '不存在'}")
            print(f"   📊  image_results数量: {len(image_results)}")
            
            if image_results:
                print(f"\n4. 图片结果详情:")
                for i, img in enumerate(image_results):
                    print(f"   图片 {i+1}:")
                    print(f"     - 标题: {img.get('caption', 'N/A')}")
                    print(f"     - 文档名: {img.get('document_name', 'N/A')}")
                    print(f"     - 页码: {img.get('page_number', 'N/A')}")
                    print(f"     - 图片路径: {img.get('image_path', 'N/A')}")
                    print(f"     - 增强描述长度: {len(img.get('enhanced_description', ''))}")
            
            # 检查来源详情
            sources = data.get('sources', [])
            print(f"\n5. 来源详情:")
            print(f"   📋 来源数量: {len(sources)}")
            
            # 检查响应结构
            print(f"\n6. 完整响应结构:")
            for key, value in data.items():
                if key == 'answer':
                    print(f"   - {key}: {type(value)} (长度: {len(str(value))})")
                elif key == 'image_results':
                    print(f"   - {key}: {type(value)} (数量: {len(value) if isinstance(value, list) else 'N/A'})")
                else:
                    print(f"   - {key}: {type(value)}")
            
        else:
            print(f"   ❌ 查询失败: {response.text}")
            
    except Exception as e:
        print(f"   💥 测试失败: {e}")

def main():
    """主函数"""
    print("🚀 图片结果调试")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    debug_image_results()
    
    print("\n🎯 调试完成！")
    print("\n📋 检查要点:")
    print("1. ✅ 答案是否只包含文字描述（不包含图片内容）")
    print("2. ✅ image_results字段是否存在且包含图片数据")
    print("3. ✅ 前端是否能正确接收和显示图片")

if __name__ == "__main__":
    main()
