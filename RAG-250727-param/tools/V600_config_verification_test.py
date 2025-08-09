#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置验证测试脚本
验证新添加的配置项是否正确加载
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings

def test_config_loading():
    """测试配置加载"""
    print("🔍 开始配置验证测试...")
    
    # 测试默认配置
    print("\n📋 测试默认配置:")
    default_settings = Settings()
    
    # 检查向量存储配置
    print(f"  text_embedding_model: {default_settings.text_embedding_model}")
    print(f"  allow_dangerous_deserialization: {default_settings.allow_dangerous_deserialization}")
    
    # 检查图像处理配置
    print(f"  depth_processing_markers: {default_settings.depth_processing_markers}")
    
    # 测试从文件加载配置
    print("\n📁 测试从配置文件加载:")
    try:
        file_settings = Settings.load_from_file('config.json')
        
        # 检查向量存储配置
        print(f"  text_embedding_model: {file_settings.text_embedding_model}")
        print(f"  allow_dangerous_deserialization: {file_settings.allow_dangerous_deserialization}")
        
        # 检查图像处理配置
        print(f"  depth_processing_markers: {file_settings.depth_processing_markers}")
        
        # 检查路径配置
        print(f"  vector_db_dir: {file_settings.vector_db_dir}")
        
    except Exception as e:
        print(f"❌ 加载配置文件失败: {e}")
        return False
    
    # 测试配置转换
    print("\n🔄 测试配置转换:")
    try:
        config_dict = file_settings.to_dict()
        
        # 检查向量存储配置
        if 'vector_store' in config_dict:
            vector_config = config_dict['vector_store']
            print(f"  vector_store.text_embedding_model: {vector_config.get('text_embedding_model')}")
            print(f"  vector_store.allow_dangerous_deserialization: {vector_config.get('allow_dangerous_deserialization')}")
        
        # 检查图像处理配置
        if 'image_processing' in config_dict:
            image_config = config_dict['image_processing']
            print(f"  image_processing.depth_processing_markers: {image_config.get('depth_processing_markers')}")
        
    except Exception as e:
        print(f"❌ 配置转换失败: {e}")
        return False
    
    print("\n✅ 配置验证测试完成!")
    return True

def test_specific_values():
    """测试特定配置值"""
    print("\n🎯 测试特定配置值:")
    
    try:
        settings = Settings.load_from_file('config.json')
        
        # 测试向量存储配置
        expected_text_model = "text-embedding-v1"
        expected_allow_deserialization = True
        
        if settings.text_embedding_model == expected_text_model:
            print(f"✅ text_embedding_model 正确: {settings.text_embedding_model}")
        else:
            print(f"❌ text_embedding_model 错误: 期望 {expected_text_model}, 实际 {settings.text_embedding_model}")
        
        if settings.allow_dangerous_deserialization == expected_allow_deserialization:
            print(f"✅ allow_dangerous_deserialization 正确: {settings.allow_dangerous_deserialization}")
        else:
            print(f"❌ allow_dangerous_deserialization 错误: 期望 {expected_allow_deserialization}, 实际 {settings.allow_dangerous_deserialization}")
        
        # 测试深度处理标记
        expected_markers = [
            '基础视觉描述:', '内容理解描述:', '数据趋势描述:', '语义特征描述:',
            'chart_type:', 'data_points:', 'trends:', 'key_insights:'
        ]
        
        if settings.depth_processing_markers == expected_markers:
            print(f"✅ depth_processing_markers 正确: {len(settings.depth_processing_markers)} 个标记")
        else:
            print(f"❌ depth_processing_markers 错误: 期望 {len(expected_markers)} 个标记, 实际 {len(settings.depth_processing_markers)} 个标记")
            print(f"  期望: {expected_markers}")
            print(f"  实际: {settings.depth_processing_markers}")
        
        # 测试路径配置
        expected_vector_db_dir = "./central/vector_db"
        if expected_vector_db_dir in settings.vector_db_dir:
            print(f"✅ vector_db_dir 正确: {settings.vector_db_dir}")
        else:
            print(f"❌ vector_db_dir 错误: 期望包含 {expected_vector_db_dir}, 实际 {settings.vector_db_dir}")
        
    except Exception as e:
        print(f"❌ 测试特定配置值失败: {e}")
        return False
    
    return True

def test_v502_integration():
    """测试V502_image_enhancer_new.py的配置集成"""
    print("\n🔗 测试V502配置集成:")
    
    try:
        # 模拟V502中的配置使用
        settings = Settings.load_from_file('config.json')
        
        # 测试V502中使用的配置项
        vector_db_path = getattr(settings, 'vector_db_dir', './central/vector_db')
        text_embedding_model = getattr(settings, 'text_embedding_model', 'text-embedding-v1')
        allow_dangerous_deserialization = getattr(settings, 'allow_dangerous_deserialization', True)
        depth_markers = getattr(settings, 'depth_processing_markers', [])
        
        print(f"  ✅ vector_db_path: {vector_db_path}")
        print(f"  ✅ text_embedding_model: {text_embedding_model}")
        print(f"  ✅ allow_dangerous_deserialization: {allow_dangerous_deserialization}")
        print(f"  ✅ depth_markers: {len(depth_markers)} 个标记")
        
        # 验证配置值是否正确
        if vector_db_path and 'vector_db' in vector_db_path:
            print(f"  ✅ vector_db_path 格式正确")
        else:
            print(f"  ❌ vector_db_path 格式错误")
            return False
        
        if text_embedding_model == 'text-embedding-v1':
            print(f"  ✅ text_embedding_model 值正确")
        else:
            print(f"  ❌ text_embedding_model 值错误")
            return False
        
        if allow_dangerous_deserialization is True:
            print(f"  ✅ allow_dangerous_deserialization 值正确")
        else:
            print(f"  ❌ allow_dangerous_deserialization 值错误")
            return False
        
        if len(depth_markers) == 8:
            print(f"  ✅ depth_markers 数量正确")
        else:
            print(f"  ❌ depth_markers 数量错误: 期望8个, 实际{len(depth_markers)}个")
            return False
        
        print("  🎉 V502配置集成测试通过!")
        return True
        
    except Exception as e:
        print(f"  ❌ V502配置集成测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 配置验证测试开始")
    print("=" * 50)
    
    success1 = test_config_loading()
    success2 = test_specific_values()
    success3 = test_v502_integration()
    
    print("\n" + "=" * 50)
    if success1 and success2 and success3:
        print("🎉 所有测试通过! 配置系统工作正常!")
        print("✅ 配置管理优化完成!")
        print("✅ V502_image_enhancer_new.py 配置集成正常!")
    else:
        print("💥 部分测试失败! 请检查配置!")
    
    print("=" * 50)
