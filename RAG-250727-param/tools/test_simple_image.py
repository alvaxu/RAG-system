#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
程序说明：

## 1. 简单图片服务测试
测试图片服务是否能正确访问图片文件

## 2. 路径验证
验证图片服务使用的路径是否正确
"""

import requests
import os
from pathlib import Path

def test_simple_image():
    """简单图片服务测试"""
    print("🖼️  简单图片服务测试")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # 检查图片目录
    print("1. 检查图片目录...")
    images_dir = Path("central/images")
    if images_dir.exists():
        print(f"   ✅ 图片目录存在: {images_dir.absolute()}")
        
        # 找到第一个图片文件
        image_files = list(images_dir.glob("*.jpg"))
        if image_files:
            test_image = image_files[0]
            print(f"   🧪 测试图片: {test_image.name}")
            print(f"   完整路径: {test_image.absolute()}")
            
            # 测试图片服务
            print(f"\n2. 测试图片服务...")
            try:
                response = requests.get(f"{base_url}/images/{test_image.name}", timeout=10)
                print(f"   HTTP状态码: {response.status_code}")
                print(f"   响应头: {dict(response.headers)}")
                
                if response.status_code == 200:
                    print(f"   ✅ 图片访问成功!")
                    print(f"   内容类型: {response.headers.get('content-type', 'unknown')}")
                    print(f"   文件大小: {len(response.content)} 字节")
                    
                    # 保存测试图片到临时目录
                    test_output = f"test_output_{test_image.name}"
                    with open(test_output, 'wb') as f:
                        f.write(response.content)
                    print(f"   💾 测试图片已保存到: {test_output}")
                    
                else:
                    print(f"   ❌ 图片访问失败: {response.status_code}")
                    print(f"   响应内容: {response.text[:200]}")
                    
            except Exception as e:
                print(f"   ❌ 图片访问测试失败: {e}")
        else:
            print("   ❌ 没有找到jpg图片文件")
    else:
        print(f"   ❌ 图片目录不存在: {images_dir.absolute()}")

def main():
    """主函数"""
    print("🚀 简单图片服务测试")
    print("=" * 60)
    
    test_simple_image()
    
    print("\n🎯 测试完成！")

if __name__ == "__main__":
    main()
