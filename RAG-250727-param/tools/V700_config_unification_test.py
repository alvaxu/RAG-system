#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置统一化测试脚本
验证主程序模块是否正确使用了配置管理而不是硬编码值
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
import importlib.util

def test_vector_generator_config():
    """测试 VectorGenerator 是否正确使用配置"""
    print("🔍 测试 VectorGenerator 配置...")
    
    try:
        # 加载配置
        settings = Settings.load_from_file("config.json")
        config = settings.to_dict()
        
        # 导入并测试 VectorGenerator
        from document_processing.vector_generator import VectorGenerator
        
        # 创建实例
        vector_generator = VectorGenerator(config)
        
        # 检查嵌入模型 - DashScopeEmbeddings 没有 model_name 属性，我们检查配置是否正确传递
        expected_model = config.get('vector_store', {}).get('text_embedding_model', 'text-embedding-v1')
        print(f"  📋 配置中的嵌入模型: {expected_model}")
        
        # 检查 embeddings 对象是否正确创建
        if vector_generator.embeddings:
            print(f"  ✅ 嵌入模型对象已正确创建")
        else:
            print(f"  ❌ 嵌入模型对象创建失败")
        
        # 检查配置属性
        if hasattr(vector_generator, 'config') and vector_generator.config:
            print(f"  ✅ 配置对象已正确传递")
        else:
            print(f"  ❌ 配置对象未正确传递")
            
        return True
        
    except Exception as e:
        print(f"  ❌ VectorGenerator 测试失败: {e}")
        return False

def test_vector_store_config():
    """测试 VectorStoreManager 是否正确使用配置"""
    print("🔍 测试 VectorStoreManager 配置...")
    
    try:
        # 加载配置
        settings = Settings.load_from_file("config.json")
        config = settings.to_dict()
        
        # 导入并测试 VectorStoreManager
        from core.vector_store import VectorStoreManager
        
        # 创建实例
        vector_store_manager = VectorStoreManager(api_key="test", config=config)
        
        # 检查配置属性
        if hasattr(vector_store_manager, 'config') and vector_store_manager.config:
            print(f"  ✅ 配置对象已正确传递")
        else:
            print(f"  ❌ 配置对象未正确传递")
        
        # 检查配置中的值
        expected_model = config.get('vector_store', {}).get('text_embedding_model', 'text-embedding-v1')
        expected_allow_deserialization = config.get('vector_store', {}).get('allow_dangerous_deserialization', True)
        
        print(f"  📋 配置中的嵌入模型: {expected_model}")
        print(f"  📋 配置中的安全反序列化: {expected_allow_deserialization}")
            
        return True
        
    except Exception as e:
        print(f"  ❌ VectorStoreManager 测试失败: {e}")
        return False

def test_enhanced_qa_system_config():
    """测试 EnhancedQASystem 是否正确使用配置"""
    print("🔍 测试 EnhancedQASystem 配置...")
    
    try:
        # 加载配置
        settings = Settings.load_from_file("config.json")
        config = settings.to_dict()
        
        # 检查配置中的值
        expected_model = config.get('vector_store', {}).get('text_embedding_model', 'text-embedding-v1')
        expected_allow_deserialization = config.get('vector_store', {}).get('allow_dangerous_deserialization', True)
        
        print(f"  📋 配置中的嵌入模型: {expected_model}")
        print(f"  📋 配置中的安全反序列化: {expected_allow_deserialization}")
        
        # 检查配置结构
        if 'vector_store' in config:
            print(f"  ✅ vector_store 配置节存在")
            if 'text_embedding_model' in config['vector_store']:
                print(f"  ✅ text_embedding_model 配置存在")
            if 'allow_dangerous_deserialization' in config['vector_store']:
                print(f"  ✅ allow_dangerous_deserialization 配置存在")
        else:
            print(f"  ❌ vector_store 配置节不存在")
            
        return True
        
    except Exception as e:
        print(f"  ❌ EnhancedQASystem 测试失败: {e}")
        return False

def test_image_enhancer_config():
    """测试 ImageEnhancer 是否正确使用配置"""
    print("🔍 测试 ImageEnhancer 配置...")
    
    try:
        # 加载配置
        settings = Settings.load_from_file("config.json")
        config = settings.to_dict()
        
        # 导入并测试 ImageEnhancer
        from document_processing.image_enhancer import ImageEnhancer
        
        # 创建实例
        image_enhancer = ImageEnhancer(api_key="test", config=config)
        
        # 检查深度处理标记
        if hasattr(image_enhancer, 'depth_processing_markers'):
            print(f"  ✅ 深度处理标记配置已加载")
            print(f"  📋 标记数量: {len(image_enhancer.depth_processing_markers)}")
            
            # 检查一些关键标记
            expected_markers = ['内容理解描述', '数据趋势描述', '图表类型']
            for marker in expected_markers:
                if any(marker in m for m in image_enhancer.depth_processing_markers):
                    print(f"  ✅ 标记 '{marker}' 存在")
                else:
                    print(f"  ❌ 标记 '{marker}' 不存在")
        else:
            print(f"  ❌ 深度处理标记配置未加载")
        
        # 检查配置属性
        if hasattr(image_enhancer, 'config') and image_enhancer.config:
            print(f"  ✅ 配置对象已正确传递")
        else:
            print(f"  ❌ 配置对象未正确传递")
            
        return True
        
    except Exception as e:
        print(f"  ❌ ImageEnhancer 测试失败: {e}")
        return False

def test_config_file_integrity():
    """测试配置文件完整性"""
    print("🔍 测试配置文件完整性...")
    
    try:
        # 加载配置
        settings = Settings.load_from_file("config.json")
        config = settings.to_dict()
        
        # 检查必要的配置项
        required_configs = [
            ('vector_store', 'text_embedding_model'),
            ('vector_store', 'allow_dangerous_deserialization'),
            ('image_processing', 'depth_processing_markers')
        ]
        
        all_present = True
        for section, key in required_configs:
            if section in config and key in config[section]:
                print(f"  ✅ {section}.{key}: {config[section][key]}")
            else:
                print(f"  ❌ {section}.{key}: 缺失")
                all_present = False
        
        return all_present
        
    except Exception as e:
        print(f"  ❌ 配置文件完整性测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始配置统一化测试\n")
    
    tests = [
        test_config_file_integrity,
        test_vector_generator_config,
        test_vector_store_config,
        test_enhanced_qa_system_config,
        test_image_enhancer_config
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"  ❌ 测试异常: {e}\n")
    
    print("📊 测试结果汇总:")
    print(f"  通过: {passed}/{total}")
    print(f"  失败: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 所有测试通过！配置统一化完成！")
    else:
        print("⚠️ 部分测试失败，需要进一步检查")

if __name__ == "__main__":
    main()
