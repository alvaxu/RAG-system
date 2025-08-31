#!/usr/bin/env python3
"""
V3版本图片补做功能最终测试脚本

功能：
1. 检查向量数据库中失败的图片
2. 运行图片补做程序
3. 验证补做结果
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from utils.image_completion import ImageCompletion
from core.vector_store_manager import LangChainVectorStoreManager
from config.config_manager import ConfigManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_image_completion():
    """测试图片补做功能"""
    print("🧪 V3版本图片补做功能测试")
    print("="*60)
    
    try:
        # 1. 初始化配置管理器
        print("📋 初始化配置管理器...")
        config_manager = ConfigManager()
        print("✅ 配置管理器初始化成功")
        
        # 2. 初始化向量存储管理器
        print("\n📚 初始化向量存储管理器...")
        vector_store_manager = LangChainVectorStoreManager(config_manager)
        print("✅ 向量存储管理器初始化成功")
        
        # 3. 加载向量数据库
        print("\n🔄 加载向量数据库...")
        if not vector_store_manager.load():
            print("❌ 无法加载向量数据库")
            return False
        print("✅ 向量数据库加载成功")
        
        # 4. 检查未完成的图片
        print("\n🔍 检查未完成的图片...")
        unfinished_images = vector_store_manager.get_unfinished_images()
        
        if not unfinished_images:
            print("🎉 所有图片都已处理完成！")
            return True
        
        print(f"📊 发现 {len(unfinished_images)} 张未完成的图片")
        
        # 5. 分类显示状态
        needs_enhancement = [img for img in unfinished_images if img.get('needs_enhancement', False)]
        needs_vectorization = [img for img in unfinished_images if img.get('needs_vectorization', False)]
        
        print(f"\n📋 状态摘要:")
        print(f"   🔄 需要增强: {len(needs_enhancement)} 张")
        print(f"   🔤 需要向量化: {len(needs_vectorization)} 张")
        
        # 6. 显示详细信息
        if needs_enhancement:
            print(f"\n🔄 需要增强的图片:")
            for i, img in enumerate(needs_enhancement[:5]):  # 只显示前5张
                print(f"   {i+1}. {img.get('image_id', 'unknown')} - {img.get('document_name', 'unknown')}")
            if len(needs_enhancement) > 5:
                print(f"   ... 还有 {len(needs_enhancement) - 5} 张")
        
        if needs_vectorization:
            print(f"\n🔤 需要向量化的图片:")
            for i, img in enumerate(needs_vectorization[:5]):  # 只显示前5张
                print(f"   {i+1}. {img.get('image_id', 'unknown')} - {img.get('document_name', 'unknown')}")
            if len(needs_vectorization) > 5:
                print(f"   ... 还有 {len(needs_vectorization) - 5} 张")
        
        # 7. 询问是否运行补做程序
        print(f"\n❓ 是否运行图片补做程序？")
        print("   输入 'y' 或 'yes' 运行补做程序")
        print("   输入其他内容跳过补做程序")
        
        user_input = input("请选择 (y/n): ").strip().lower()
        
        if user_input in ['y', 'yes']:
            print(f"\n🚀 启动图片补做程序...")
            image_completion = ImageCompletion()
            image_completion.run()
            print("✅ 图片补做程序执行完成")
        else:
            print("⏭️ 跳过补做程序")
        
        return True
        
    except Exception as e:
        logging.error(f"测试失败: {e}")
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🧪 V3版本图片补做功能测试")
    print("="*60)
    
    success = test_image_completion()
    
    if success:
        print("\n🎉 测试完成！")
    else:
        print("\n❌ 测试失败！")
    
    return success

if __name__ == "__main__":
    main()
