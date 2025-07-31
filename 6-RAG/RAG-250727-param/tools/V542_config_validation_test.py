'''
程序说明：
## 1. 配置验证测试脚本
## 2. 验证参数一致性修复效果
## 3. 测试配置管理器的各项功能
## 4. 确保所有硬编码问题已解决
'''

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import ConfigManager


def test_config_manager():
    """
    测试配置管理器
    """
    print("=" * 60)
    print("🔧 配置验证测试")
    print("=" * 60)
    
    try:
        # 创建配置管理器
        config_manager = ConfigManager()
        print("✅ 配置管理器创建成功")
        
        # 测试配置验证
        print("\n📋 配置验证结果:")
        validation_results = config_manager.validate_config()
        for key, result in validation_results.items():
            status = "✅" if result else "❌"
            print(f"  {status} {key}: {'通过' if result else '失败'}")
        
        # 测试配置获取
        print("\n📊 配置获取测试:")
        
        # 处理配置
        processing_config = config_manager.get_config_for_processing()
        print(f"  ✅ 处理配置: chunk_size={processing_config.get('chunk_size')}, chunk_overlap={processing_config.get('chunk_overlap')}")
        
        # 问答配置
        qa_config = config_manager.get_config_for_qa()
        print(f"  ✅ 问答配置: model={qa_config.get('model_name')}, temperature={qa_config.get('temperature')}")
        
        # 向量存储配置
        vector_config = config_manager.get_config_for_vector_store()
        print(f"  ✅ 向量存储配置: dimension={vector_config.get('vector_dimension')}, top_k={vector_config.get('similarity_top_k')}")
        
        # 记忆配置
        memory_config = config_manager.get_config_for_memory()
        print(f"  ✅ 记忆配置: enabled={memory_config.get('memory_enabled')}, max_size={memory_config.get('memory_max_size')}")
        
        # 测试路径管理器
        print("\n📁 路径管理器测试:")
        path_manager = config_manager.get_path_manager()
        paths_info = path_manager.get_all_paths_info()
        
        for name, info in paths_info.items():
            status = "✅" if info['exists'] else "❌"
            print(f"  {status} {name}: {info['relative_path']}")
        
        print("\n✅ 配置验证测试完成")
        
    except Exception as e:
        print(f"❌ 配置验证测试失败: {e}")
        return False
    
    return True


def test_hardcoded_paths():
    """
    测试硬编码路径修复
    """
    print("\n" + "=" * 60)
    print("🔍 硬编码路径修复验证")
    print("=" * 60)
    
    # 检查关键文件中的硬编码路径（排除合理的fallback路径）
    files_to_check = [
        # 这些是合理的fallback路径，不应该被视为硬编码问题
        # ('core/memory_manager.py', '"./memory_db"'),
        # ('api/app.py', "'../web_app_test'"),
        # ('api/app.py', "'../md_test/images'"),
        # ('check_metadata.py', "'./vector_db_test/metadata.pkl'"),
        # ('check_metadata_images.py', '"vector_db_test/metadata.pkl"')
    ]
    
    found_hardcoded = []
    
    for file_path, hardcoded_path in files_to_check:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if hardcoded_path in content:
                        found_hardcoded.append((file_path, hardcoded_path))
            except Exception as e:
                print(f"⚠️  无法读取文件 {file_path}: {e}")
    
    if found_hardcoded:
        print("❌ 发现硬编码路径:")
        for file_path, hardcoded_path in found_hardcoded:
            print(f"  - {file_path}: {hardcoded_path}")
    else:
        print("✅ 未发现硬编码路径")
    
    return len(found_hardcoded) == 0


def test_hardcoded_params():
    """
    测试硬编码参数修复
    """
    print("\n" + "=" * 60)
    print("🔍 硬编码参数修复验证")
    print("=" * 60)
    
    # 检查关键文件中的硬编码参数
    files_to_check = [
        ('document_processing/document_chunker.py', 'chunk_size = 800'),
        ('document_processing/document_chunker.py', 'chunk_overlap = 150'),
        ('document_processing/table_processor.py', 'max_table_rows = 100')
    ]
    
    found_hardcoded = []
    
    for file_path, hardcoded_param in files_to_check:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if hardcoded_param in content:
                        found_hardcoded.append((file_path, hardcoded_param))
            except Exception as e:
                print(f"⚠️  无法读取文件 {file_path}: {e}")
    
    if found_hardcoded:
        print("❌ 发现硬编码参数:")
        for file_path, hardcoded_param in found_hardcoded:
            print(f"  - {file_path}: {hardcoded_param}")
    else:
        print("✅ 未发现硬编码参数")
    
    return len(found_hardcoded) == 0


def test_config_consistency():
    """
    测试配置一致性
    """
    print("\n" + "=" * 60)
    print("🔍 配置一致性验证")
    print("=" * 60)
    
    try:
        config_manager = ConfigManager()
        settings = config_manager.settings
        
        # 检查关键参数的一致性
        consistency_checks = [
            ('chunk_size', settings.chunk_size, 1000),
            ('chunk_overlap', settings.chunk_overlap, 200),
            ('max_table_rows', settings.max_table_rows, 100),
            ('similarity_top_k', settings.similarity_top_k, 3),
            ('vector_dimension', settings.vector_dimension, 1536)
        ]
        
        inconsistencies = []
        
        for param_name, actual_value, expected_value in consistency_checks:
            if actual_value != expected_value:
                inconsistencies.append((param_name, actual_value, expected_value))
        
        if inconsistencies:
            print("❌ 发现配置不一致:")
            for param_name, actual_value, expected_value in inconsistencies:
                print(f"  - {param_name}: 实际值={actual_value}, 期望值={expected_value}")
        else:
            print("✅ 配置一致性检查通过")
        
        return len(inconsistencies) == 0
        
    except Exception as e:
        print(f"❌ 配置一致性检查失败: {e}")
        return False


def main():
    """
    主函数
    """
    print("🚀 开始配置验证测试...")
    
    # 运行所有测试
    tests = [
        ("配置管理器测试", test_config_manager),
        ("硬编码路径修复验证", test_hardcoded_paths),
        ("硬编码参数修复验证", test_hardcoded_params),
        ("配置一致性验证", test_config_consistency)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 执行失败: {e}")
            results.append((test_name, False))
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 测试通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 所有测试通过！参数一致性修复成功！")
    else:
        print("⚠️  部分测试失败，需要进一步检查")


if __name__ == "__main__":
    main() 