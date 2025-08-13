#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
程序说明：

## 1. 测试图片服务
测试图片服务路由是否正常工作，图片文件是否能被访问

## 2. 测试图片路径
验证图片路径的构建和访问是否正确

## 3. 调试图片显示问题
帮助诊断图片显示失败的原因
"""

import requests
import os
from pathlib import Path

def test_image_service():
    """测试图片服务"""
    print("🖼️  测试图片服务")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # 测试图片服务路由
    print("1. 测试图片服务路由...")
    try:
        response = requests.get(f"{base_url}/images/test.jpg", timeout=10)
        print(f"   HTTP状态码: {response.status_code}")
        if response.status_code == 404:
            print("   ✅ 图片服务路由正常（返回404是预期的，因为test.jpg不存在）")
        else:
            print(f"   ⚠️  意外状态码: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 图片服务路由测试失败: {e}")
    
    # 检查central/images目录
    print("\n2. 检查图片目录...")
    images_dir = Path("central/images")
    if images_dir.exists():
        print(f"   ✅ 图片目录存在: {images_dir}")
        image_files = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpeg"))
        print(f"   📸 找到 {len(image_files)} 个图片文件")
        
        if image_files:
            # 测试第一个图片文件
            test_image = image_files[0]
            print(f"   🧪 测试图片: {test_image.name}")
            
            try:
                response = requests.get(f"{base_url}/images/{test_image.name}", timeout=10)
                print(f"   HTTP状态码: {response.status_code}")
                if response.status_code == 200:
                    print(f"   ✅ 图片访问成功: {test_image.name}")
                    print(f"   内容类型: {response.headers.get('content-type', 'unknown')}")
                    print(f"   文件大小: {len(response.content)} 字节")
                else:
                    print(f"   ❌ 图片访问失败: {response.status_code}")
            except Exception as e:
                print(f"   ❌ 图片访问测试失败: {e}")
    else:
        print(f"   ❌ 图片目录不存在: {images_dir}")
    
    # 测试API返回的图片路径
    print("\n3. 测试图片查询API...")
    try:
        response = requests.post(f"{base_url}/api/v2/qa/ask", json={
            "question": "图4",
            "query_type": "image",
            "max_results": 3,
            "user_id": "test_user"
        }, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            image_results = data.get('image_results', [])
            print(f"   ✅ 图片查询成功，返回 {len(image_results)} 个图片结果")
            
            if image_results:
                print("   📸 图片路径信息:")
                for i, img in enumerate(image_results):
                    image_path = img.get('image_path', '')
                    print(f"     图片 {i+1}: {image_path}")
                    
                    if image_path:
                        # 测试这个图片路径
                        try:
                            # 提取文件名
                            if '\\' in image_path:
                                filename = image_path.split('\\')[-1]
                            elif '/' in image_path:
                                filename = image_path.split('/')[-1]
                            else:
                                filename = image_path
                            
                            img_response = requests.get(f"{base_url}/images/{filename}", timeout=10)
                            print(f"       访问状态: {img_response.status_code}")
                            if img_response.status_code == 200:
                                print(f"       ✅ 图片可访问: {filename}")
                            else:
                                print(f"       ❌ 图片不可访问: {filename}")
                        except Exception as e:
                            print(f"       ❌ 图片访问测试失败: {e}")
        else:
            print(f"   ❌ 图片查询失败: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ 图片查询测试失败: {e}")

def main():
    """主函数"""
    print("🚀 RAG系统图片服务测试")
    print("=" * 60)
    
    test_image_service()
    
    print("\n🎯 测试完成！")
    print("\n📋 检查要点:")
    print("1. ✅ 图片服务路由是否正常")
    print("2. ✅ 图片文件是否能被访问")
    print("3. ✅ API返回的图片路径是否正确")
    print("4. ✅ 图片文件是否存在于正确目录")

if __name__ == "__main__":
    main()
