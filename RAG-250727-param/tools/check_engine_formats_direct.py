#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
## 1. 直接分析三个引擎的代码，获取真实的输出格式
## 2. 不依赖配置系统，直接查看代码结构
## 3. 为unified_pipeline的智能处理提供准确依据
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def analyze_text_engine_output():
    """分析TextEngine的输出格式"""
    print("🔍 分析TextEngine输出格式...")
    
    try:
        # 直接读取text_engine.py文件
        text_engine_path = project_root / "v2" / "core" / "text_engine.py"
        
        with open(text_engine_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找process_query方法
        lines = content.split('\n')
        
        print("📋 TextEngine.process_query方法分析:")
        for i, line in enumerate(lines):
            if 'def process_query' in line:
                print(f"  第{i+1}行: {line.strip()}")
                # 查找return语句
                for j in range(i+1, min(i+100, len(lines))):
                    if 'return QueryResult' in lines[j]:
                        print(f"  第{j+1}行: {lines[j].strip()}")
                        # 查看QueryResult的构造参数
                        start_line = j
                        for k in range(j+1, min(j+20, len(lines))):
                            if ')' in lines[k]:
                                print(f"    QueryResult构造参数:")
                                for param_line in range(start_line+1, k+1):
                                    if lines[param_line].strip() and not lines[param_line].strip().startswith('#'):
                                        print(f"      {lines[param_line].strip()}")
                                break
                        break
                break
        
        # 查找_vector_similarity_search方法
        print("\n📋 TextEngine._vector_similarity_search方法分析:")
        for i, line in enumerate(lines):
            if 'def _vector_similarity_search' in line:
                print(f"  第{i+1}行: {line.strip()}")
                # 查找返回的processed_doc结构
                for j in range(i+1, min(i+100, len(lines))):
                    if 'processed_doc = {' in lines[j]:
                        print(f"  第{j+1}行: {lines[j].strip()}")
                        # 查看processed_doc的完整结构
                        for k in range(j+1, min(j+20, len(lines))):
                            if '}' in lines[k] and 'processed_doc' in lines[k]:
                                print(f"    processed_doc结构:")
                                for param_line in range(j+1, k+1):
                                    if lines[param_line].strip() and not lines[param_line].strip().startswith('#'):
                                        print(f"      {lines[param_line].strip()}")
                                break
                        break
                break
                
        print("✅ TextEngine分析完成")
        
    except Exception as e:
        print(f"❌ TextEngine分析失败: {e}")

def analyze_image_engine_output():
    """分析ImageEngine的输出格式"""
    print("\n🔍 分析ImageEngine输出格式...")
    
    try:
        # 直接读取image_engine.py文件
        image_engine_path = project_root / "v2" / "core" / "image_engine.py"
        
        with open(image_engine_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找process_query方法
        lines = content.split('\n')
        
        print("📋 ImageEngine.process_query方法分析:")
        for i, line in enumerate(lines):
            if 'def process_query' in line:
                print(f"  第{i+1}行: {line.strip()}")
                # 查找return语句
                for j in range(i+1, min(i+100, len(lines))):
                    if 'return QueryResult' in lines[j]:
                        print(f"  第{j+1}行: {lines[j].strip()}")
                        # 查看QueryResult的构造参数
                        start_line = j
                        for k in range(j+1, min(j+20, len(lines))):
                            if ')' in lines[k]:
                                print(f"    QueryResult构造参数:")
                                for param_line in range(start_line+1, k+1):
                                    if lines[param_line].strip() and not lines[param_line].strip().startswith('#'):
                                        print(f"      {lines[param_line].strip()}")
                                break
                        break
                break
        
        # 查找_enhance_reranked_results方法
        print("\n📋 ImageEngine._enhance_reranked_results方法分析:")
        for i, line in enumerate(lines):
            if 'def _enhance_reranked_results' in line:
                print(f"  第{i+1}行: {line.strip()}")
                # 查找返回的enhanced_result结构
                for j in range(i+1, min(i+100, len(lines))):
                    if 'enhanced_result = {' in lines[j]:
                        print(f"  第{j+1}行: {lines[j].strip()}")
                        # 查看enhanced_result的完整结构
                        for k in range(j+1, min(j+20, len(lines))):
                            if '}' in lines[k] and 'enhanced_result' in lines[k]:
                                print(f"    enhanced_result结构:")
                                for param_line in range(j+1, k+1):
                                    if lines[param_line].strip() and not lines[param_line].strip().startswith('#'):
                                        print(f"      {lines[param_line].strip()}")
                                break
                        break
                break
                
        print("✅ ImageEngine分析完成")
        
    except Exception as e:
        print(f"❌ ImageEngine分析失败: {e}")

def analyze_table_engine_output():
    """分析TableEngine的输出格式"""
    print("\n🔍 分析TableEngine输出格式...")
    
    try:
        # 直接读取table_engine.py文件
        table_engine_path = project_root / "v2" / "core" / "table_engine.py"
        
        with open(table_engine_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找process_query方法
        lines = content.split('\n')
        
        print("📋 TableEngine.process_query方法分析:")
        for i, line in enumerate(lines):
            if 'def process_query' in line:
                print(f"  第{i+1}行: {line.strip()}")
                # 查找return语句
                for j in range(i+1, min(i+100, len(lines))):
                    if 'return QueryResult' in lines[j]:
                        print(f"  第{j+1}行: {lines[j].strip()}")
                        # 查看QueryResult的构造参数
                        start_line = j
                        for k in range(j+1, min(j+20, len(lines))):
                            if ')' in lines[k]:
                                print(f"    QueryResult构造参数:")
                                for param_line in range(start_line+1, k+1):
                                    if lines[param_line].strip() and not lines[param_line].strip().startswith('#'):
                                        print(f"      {lines[param_line].strip()}")
                                break
                        break
                break
        
        # 查找_search_tables方法
        print("\n📋 TableEngine._search_tables方法分析:")
        for i, line in enumerate(lines):
            if 'def _search_tables' in line:
                print(f"  第{i+1}行: {line.strip()}")
                # 查找返回的processed_doc结构
                for j in range(i+1, min(i+100, len(lines))):
                    if 'processed_doc = {' in lines[j]:
                        print(f"  第{j+1}行: {lines[j].strip()}")
                        # 查看processed_doc的完整结构
                        for k in range(j+1, min(j+20, len(lines))):
                            if '}' in lines[k] and 'processed_doc' in lines[k]:
                                print(f"    processed_doc结构:")
                                for param_line in range(j+1, k+1):
                                    if lines[param_line].strip() and not lines[param_line].strip().startswith('#'):
                                        print(f"      {lines[param_line].strip()}")
                                break
                        break
                break
                
        print("✅ TableEngine分析完成")
        
    except Exception as e:
        print(f"❌ TableEngine分析失败: {e}")

def analyze_query_result_structure():
    """分析QueryResult的实际结构"""
    print("\n🔍 分析QueryResult实际结构...")
    
    try:
        # 直接读取base_engine.py文件
        base_engine_path = project_root / "v2" / "core" / "base_engine.py"
        
        with open(base_engine_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找QueryResult类定义
        lines = content.split('\n')
        
        print("📋 QueryResult类定义分析:")
        for i, line in enumerate(lines):
            if 'class QueryResult' in line:
                print(f"  第{i+1}行: {line.strip()}")
                # 查找字段定义
                for j in range(i+1, min(i+50, len(lines))):
                    if ':' in lines[j] and ':' in lines[j+1] and 'typing.' in lines[j+1]:
                        field_name = lines[j].strip().rstrip(':')
                        field_type = lines[j+1].strip()
                        print(f"    {field_name}: {field_type}")
                    elif 'def __init__' in lines[j]:
                        break
                break
                
        print("✅ QueryResult分析完成")
        
    except Exception as e:
        print(f"❌ QueryResult分析失败: {e}")

if __name__ == "__main__":
    print("=" * 80)
    print("🎯 三个引擎输出格式直接代码分析")
    print("=" * 80)
    
    analyze_text_engine_output()
    analyze_image_engine_output()
    analyze_table_engine_output()
    analyze_query_result_structure()
    
    print("\n" + "=" * 80)
    print("📊 分析完成")
    print("=" * 80)
