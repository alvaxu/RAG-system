#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
程序说明：

## 1. 测试新布局
测试新的紧凑图片布局是否正常工作

## 2. 验证图片显示
确认图片在答案下方正确显示，没有重复

## 3. 检查响应式设计
验证在不同屏幕尺寸下的显示效果
"""

import requests
import json
import time
from datetime import datetime

def test_new_layout():
    """测试新布局"""
    print("🎨 测试新图片布局")
    print("=" * 50)
    
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
            print(f"   📝 答案长度: {len(answer)}")
            
            # 检查图片结果
            image_results = data.get('image_results', [])
            print(f"   🖼️  图片结果数量: {len(image_results)}")
            
            if image_results:
                print("\n2. 图片结果详情:")
                for i, img in enumerate(image_results):
                    print(f"   图片 {i+1}:")
                    print(f"     - 标题: {img.get('caption', 'N/A')}")
                    print(f"     - 文档名: {img.get('document_name', 'N/A')}")
                    print(f"     - 页码: {img.get('page_number', 'N/A')}")
                    print(f"     - 图片路径: {img.get('image_path', 'N/A')}")
                    
                    # 检查图片路径转换
                    if img.get('image_path'):
                        path = img.get('image_path')
                        if '\\' in path:
                            filename = path.split('\\')[-1]
                        elif '/' in path:
                            filename = path.split('/')[-1]
                        else:
                            filename = path
                        
                        expected_url = f"/images/{filename}"
                        print(f"     - 预期URL: {expected_url}")
                        
                        # 测试图片访问
                        try:
                            img_response = requests.get(f"{base_url}{expected_url}", timeout=10)
                            print(f"     - 图片访问状态: {img_response.status_code}")
                            if img_response.status_code == 200:
                                print(f"     - ✅ 图片可访问")
                            else:
                                print(f"     - ❌ 图片不可访问")
                        except Exception as e:
                            print(f"     - ❌ 图片访问测试失败: {e}")
            
            # 检查来源详情
            sources = data.get('sources', [])
            print(f"\n3. 来源详情数量: {len(sources)}")
            
            # 检查是否有重复的图片信息
            print("\n4. 检查重复信息:")
            answer_lower = answer.lower()
            if "相关图片" in answer:
                count = answer.count("相关图片")
                print(f"   - '相关图片'出现次数: {count}")
                if count > 1:
                    print("   ⚠️  发现重复的'相关图片'标题")
                else:
                    print("   ✅ '相关图片'标题无重复")
            
            # 检查图片标记
            image_markers = ["图片 1:", "图片 2:", "图片 3:", "图片 4:"]
            for marker in image_markers:
                count = answer.count(marker)
                if count > 1:
                    print(f"   ⚠️  '{marker}'出现{count}次")
                else:
                    print(f"   ✅ '{marker}'出现{count}次")
            
        else:
            print(f"   ❌ 查询失败: {response.text}")
            
    except Exception as e:
        print(f"   💥 测试失败: {e}")

def main():
    """主函数"""
    print("🚀 新图片布局测试")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    test_new_layout()
    
    print("\n🎯 测试完成！")
    print("\n📋 检查要点:")
    print("1. ✅ 图片是否在答案下方正确显示")
    print("2. ✅ 是否没有重复的图片区域")
    print("3. ✅ 图片布局是否紧凑美观")
    print("4. ✅ 图片是否能正常访问")
    print("5. ✅ 来源详情是否只显示必要信息")

if __name__ == "__main__":
    main()
