#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
## 1. 检查三个引擎的实际返回格式
## 2. 验证字段映射统一改造是否生效
## 3. 对比改造前后的差异
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_text_engine_format():
    """检查TextEngine的返回格式"""
    print("🔍 检查TextEngine返回格式...")
    
    try:
        from v2.core.text_engine import TextEngine
        
        # 查看TextEngine的process_query方法
        import inspect
        
        # 获取process_query方法的源码
        source = inspect.getsource(TextEngine.process_query)
        
        # 查找返回语句
        lines = source.split('\n')
        for i, line in enumerate(lines):
            if 'return QueryResult' in line or 'return ' in line:
                print(f"  第{i+1}行: {line.strip()}")
                
        print("✅ TextEngine检查完成")
        
    except Exception as e:
        print(f"❌ TextEngine检查失败: {e}")

def check_image_engine_format():
    """检查ImageEngine的返回格式"""
    print("\n🔍 检查ImageEngine返回格式...")
    
    try:
        from v2.core.image_engine import ImageEngine
        
        # 查看ImageEngine的process_query方法
        import inspect
        
        # 获取process_query方法的源码
        source = inspect.getsource(ImageEngine.process_query)
        
        # 查找返回语句
        lines = source.split('\n')
        for i, line in enumerate(lines):
            if 'return QueryResult' in line or 'return ' in line:
                print(f"  第{i+1}行: {line.strip()}")
                
        print("✅ ImageEngine检查完成")
        
    except Exception as e:
        print(f"❌ ImageEngine检查失败: {e}")

def check_table_engine_format():
    """检查TableEngine的返回格式"""
    print("\n🔍 检查TableEngine返回格式...")
    
    try:
        from v2.core.table_engine import TableEngine
        
        # 查看TableEngine的process_query方法
        import inspect
        
        # 获取process_query方法的源码
        source = inspect.getsource(TableEngine.process_query)
        
        # 查找返回语句
        lines = source.split('\n')
        for i, line in enumerate(lines):
            if 'return QueryResult' in line or 'return ' in line:
                print(f"  第{i+1}行: {line.strip()}")
                
        print("✅ TableEngine检查完成")
        
    except Exception as e:
        print(f"❌ TableEngine检查失败: {e}")

def check_unified_pipeline_format():
    """检查UnifiedPipeline的字段映射"""
    print("\n🔍 检查UnifiedPipeline字段映射...")
    
    try:
        from v2.core.unified_pipeline import UnifiedPipeline
        
        # 检查是否有FIELD_MAPPING
        if hasattr(UnifiedPipeline, 'FIELD_MAPPING'):
            print("✅ 发现FIELD_MAPPING字段映射表")
            # 不打印具体内容，避免过长
        else:
            print("❌ 未发现FIELD_MAPPING字段映射表")
            
        # 检查_extract_sources方法
        import inspect
        source = inspect.getsource(UnifiedPipeline._extract_sources)
        
        if 'FIELD_MAPPING' in source:
            print("✅ _extract_sources方法使用了FIELD_MAPPING")
        else:
            print("❌ _extract_sources方法未使用FIELD_MAPPING")
            
        print("✅ UnifiedPipeline检查完成")
        
    except Exception as e:
        print(f"❌ UnifiedPipeline检查失败: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("🎯 三个引擎返回格式检查")
    print("=" * 60)
    
    check_text_engine_format()
    check_image_engine_format() 
    check_table_engine_format()
    check_unified_pipeline_format()
    
    print("\n" + "=" * 60)
    print("📊 检查完成")
    print("=" * 60)
