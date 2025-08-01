#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
## 1. 检查系统中所有组件的嵌入模型使用情况
## 2. 确保文本嵌入模型和 multimodal 嵌入模型的一致性
## 3. 识别硬编码的模型名称
## 4. 验证配置管理是否正确应用
"""

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from config.settings import Settings

def check_embedding_models():
    """
    检查系统中所有组件的嵌入模型使用情况
    """
    print("🔍 检查嵌入模型一致性...")
    print("=" * 60)
    
    # 1. 检查配置文件
    print("\n📋 1. 配置文件检查:")
    config_file = "config.json"
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        vector_store_config = config.get('vector_store', {})
        text_model = vector_store_config.get('text_embedding_model', '未配置')
        multimodal_model = vector_store_config.get('multimodal_embedding_model', '未配置')
        
        print(f"   config.json 中的配置:")
        print(f"   - text_embedding_model: {text_model}")
        print(f"   - multimodal_embedding_model: {multimodal_model}")
    else:
        print(f"   ❌ {config_file} 不存在")
    
    # 2. 检查 Settings 类
    print("\n⚙️ 2. Settings 类检查:")
    try:
        settings = Settings.load_from_file("config.json")
        settings_dict = settings.to_dict()
        vector_store_config = settings_dict.get('vector_store', {})
        text_model = vector_store_config.get('text_embedding_model', '未配置')
        multimodal_model = vector_store_config.get('multimodal_embedding_model', '未配置')
        
        print(f"   Settings 类中的配置:")
        print(f"   - text_embedding_model: {text_model}")
        print(f"   - multimodal_embedding_model: {multimodal_model}")
    except Exception as e:
        print(f"   ❌ Settings 类检查失败: {e}")
    
    # 3. 检查关键文件中的硬编码模型
    print("\n🔧 3. 关键文件中的模型使用情况:")
    
    files_to_check = [
        "core/enhanced_qa_system.py",
        "core/vector_store.py", 
        "document_processing/enhanced_vector_generator.py",
        "document_processing/enhanced_image_processor.py",
        "document_processing/image_processor.py"
    ]
    
    text_model_usage = {}
    multimodal_model_usage = {}
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查文本嵌入模型
            if 'text-embedding-v4' in content:
                lines = content.split('\n')
                text_lines = []
                for i, line in enumerate(lines, 1):
                    if 'text-embedding-v4' in line:
                        text_lines.append(f"第{i}行: {line.strip()}")
                text_model_usage[file_path] = text_lines
            
            # 检查 multimodal 嵌入模型
            if 'multimodal_embedding_one_peace_v1' in content:
                lines = content.split('\n')
                multimodal_lines = []
                for i, line in enumerate(lines, 1):
                    if 'multimodal_embedding_one_peace_v1' in line:
                        multimodal_lines.append(f"第{i}行: {line.strip()}")
                multimodal_model_usage[file_path] = multimodal_lines
        else:
            print(f"   ⚠️ 文件不存在: {file_path}")
    
    # 显示文本嵌入模型使用情况
    print("\n   📝 文本嵌入模型 (text-embedding-v4) 使用情况:")
    if text_model_usage:
        for file_path, lines in text_model_usage.items():
            print(f"   📄 {file_path}:")
            for line in lines:
                print(f"      {line}")
    else:
        print("   ✅ 未发现硬编码的 text-embedding-v4")
    
    # 显示 multimodal 嵌入模型使用情况
    print("\n   🖼️ Multimodal 嵌入模型 (multimodal_embedding_one_peace_v1) 使用情况:")
    if multimodal_model_usage:
        for file_path, lines in multimodal_model_usage.items():
            print(f"   📄 {file_path}:")
            for line in lines:
                print(f"      {line}")
    else:
        print("   ✅ 未发现硬编码的 multimodal_embedding_one_peace_v1")
    
    # 4. 检查配置管理实现
    print("\n🔧 4. 配置管理实现检查:")
    
    # 检查是否使用了配置参数
    config_usage_files = [
        "core/enhanced_qa_system.py",
        "core/vector_store.py",
        "document_processing/enhanced_vector_generator.py",
        "document_processing/enhanced_image_processor.py",
        "document_processing/image_processor.py"
    ]
    
    for file_path in config_usage_files:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否接受 config 参数
            has_config_param = 'def __init__(self, config' in content or 'def __init__(self, *, config' in content
            # 检查是否从配置中获取模型
            uses_config_model = 'config.get' in content and ('text_embedding_model' in content or 'multimodal_embedding_model' in content)
            
            status = "✅" if has_config_param and uses_config_model else "❌"
            print(f"   {status} {file_path}:")
            print(f"      - 接受 config 参数: {'是' if has_config_param else '否'}")
            print(f"      - 使用配置中的模型: {'是' if uses_config_model else '否'}")
    
    # 5. 总结和建议
    print("\n📊 5. 总结和建议:")
    
    issues_found = []
    
    # 检查配置文件是否包含嵌入模型配置
    if not os.path.exists(config_file) or 'text_embedding_model' not in str(config):
        issues_found.append("config.json 中缺少嵌入模型配置")
    
    # 检查是否有硬编码的模型名称
    if text_model_usage or multimodal_model_usage:
        issues_found.append("发现硬编码的模型名称，需要改为使用配置")
    
    if issues_found:
        print("   ❌ 发现以下问题:")
        for issue in issues_found:
            print(f"      - {issue}")
        
        print("\n   💡 建议修复:")
        print("      1. 在 config.json 中添加嵌入模型配置")
        print("      2. 修改硬编码的模型名称为使用配置")
        print("      3. 确保所有组件都接受 config 参数")
    else:
        print("   ✅ 嵌入模型配置一致，未发现问题")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    check_embedding_models() 