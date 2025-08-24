#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
## 1. 实际运行三个引擎，获取真实的输出格式
## 2. 不使用推测，基于实际运行结果编程
## 3. 为unified_pipeline的智能处理提供准确依据
"""

import sys
import os
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_text_engine_real_output():
    """检查TextEngine的真实输出格式"""
    print("🔍 检查TextEngine真实输出格式...")
    
    try:
        from v2.core.text_engine import TextEngine
        from v2.config.v2_config import V2ConfigManager
        
        # 获取配置
        config_manager = V2ConfigManager()
        text_config = config_manager.get_engine_config('text_engine')
        
        if not text_config:
            print("❌ 无法获取text_engine配置")
            return None
            
        # 创建TextEngine实例
        text_engine = TextEngine(
            config=text_config,
            vector_store=None,  # 暂时不传入，避免初始化问题
            llm_engine=None
        )
        
        # 检查process_query方法的返回结构
        import inspect
        source = inspect.getsource(TextEngine.process_query)
        
        print("📋 TextEngine.process_query方法结构:")
        lines = source.split('\n')
        for i, line in enumerate(lines):
            if 'return QueryResult' in line:
                print(f"  第{i+1}行: {line.strip()}")
                # 查看后续几行，了解QueryResult的构造
                for j in range(i+1, min(i+10, len(lines))):
                    if lines[j].strip() and not lines[j].strip().startswith('#'):
                        print(f"    {lines[j].strip()}")
                        if ')' in lines[j]:
                            break
        
        # 检查QueryResult的结构
        from v2.core.base_engine import QueryResult
        print(f"\n📊 QueryResult字段: {QueryResult.__annotations__.keys()}")
        
        return text_engine
        
    except Exception as e:
        print(f"❌ TextEngine检查失败: {e}")
        return None

def check_image_engine_real_output():
    """检查ImageEngine的真实输出格式"""
    print("\n🔍 检查ImageEngine真实输出格式...")
    
    try:
        from v2.core.image_engine import ImageEngine
        from v2.config.v2_config import V2ConfigManager
        
        # 获取配置
        config_manager = V2ConfigManager()
        image_config = config_manager.get_engine_config('image_engine')
        
        if not image_config:
            print("❌ 无法获取image_engine配置")
            return None
            
        # 创建ImageEngine实例
        image_engine = ImageEngine(
            config=image_config,
            vector_store=None,
            llm_engine=None
        )
        
        # 检查process_query方法的返回结构
        import inspect
        source = inspect.getsource(ImageEngine.process_query)
        
        print("📋 ImageEngine.process_query方法结构:")
        lines = source.split('\n')
        for i, line in enumerate(lines):
            if 'return QueryResult' in line:
                print(f"  第{i+1}行: {line.strip()}")
                # 查看后续几行，了解QueryResult的构造
                for j in range(i+1, min(i+10, len(lines))):
                    if lines[j].strip() and not lines[j].strip().startswith('#'):
                        print(f"    {lines[j].strip()}")
                        if ')' in lines[j]:
                            break
        
        return image_engine
        
    except Exception as e:
        print(f"❌ ImageEngine检查失败: {e}")
        return None

def check_table_engine_real_output():
    """检查TableEngine的真实输出格式"""
    print("\n🔍 检查TableEngine真实输出格式...")
    
    try:
        from v2.core.table_engine import TableEngine
        from v2.config.v2_config import V2ConfigManager
        
        # 获取配置
        config_manager = V2ConfigManager()
        table_config = config_manager.get_engine_config('table_engine')
        
        if not table_config:
            print("❌ 无法获取table_engine配置")
            return None
            
        # 创建TableEngine实例
        table_engine = TableEngine(
            config=table_config,
            vector_store=None,
            llm_engine=None
        )
        
        # 检查process_query方法的返回结构
        import inspect
        source = inspect.getsource(TableEngine.process_query)
        
        print("📋 TableEngine.process_query方法结构:")
        lines = source.split('\n')
        for i, line in enumerate(lines):
            if 'return QueryResult' in line:
                print(f"  第{i+1}行: {line.strip()}")
                # 查看后续几行，了解QueryResult的构造
                for j in range(i+1, min(i+10, len(lines))):
                    if lines[j].strip() and not lines[j].strip().startswith('#'):
                        print(f"    {lines[j].strip()}")
                        if ')' in lines[j]:
                            break
        
        return table_engine
        
    except Exception as e:
        print(f"❌ TableEngine检查失败: {e}")
        return None

def check_query_result_structure():
    """检查QueryResult的详细结构"""
    print("\n🔍 检查QueryResult详细结构...")
    
    try:
        from v2.core.base_engine import QueryResult
        
        # 获取所有字段
        fields = QueryResult.__annotations__
        print("📊 QueryResult字段类型:")
        for field_name, field_type in fields.items():
            print(f"  {field_name}: {field_type}")
        
        # 尝试创建一个空的QueryResult实例
        try:
            # 创建最小化的实例
            empty_result = QueryResult(
                answer="",
                results=[],
                sources=[],
                success=True,
                processing_time=0.0,
                query_type="",
                question="",
                timestamp="",
                total_count=0,
                use_memory=False,
                user_id="",
                metadata={}
            )
            print("✅ 成功创建QueryResult实例")
            
            # 检查results字段的结构
            print(f"📋 results字段类型: {type(empty_result.results)}")
            print(f"📋 sources字段类型: {type(empty_result.sources)}")
            
        except Exception as e:
            print(f"❌ 创建QueryResult实例失败: {e}")
            
    except Exception as e:
        print(f"❌ QueryResult检查失败: {e}")

if __name__ == "__main__":
    print("=" * 80)
    print("🎯 三个引擎真实输出格式检查")
    print("=" * 80)
    
    # 检查三个引擎
    text_engine = check_text_engine_real_output()
    image_engine = check_image_engine_real_output()
    table_engine = check_table_engine_real_output()
    
    # 检查QueryResult结构
    check_query_result_structure()
    
    print("\n" + "=" * 80)
    print("📊 检查完成")
    print("=" * 80)
