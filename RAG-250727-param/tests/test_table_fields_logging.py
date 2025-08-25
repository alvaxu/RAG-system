#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：验证table_engine的字段传递
检查reranked_results中是否包含完整的表格字段
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v2.core.table_engine import TableEngine
from v2.config.v2_config import V2ConfigManager

def test_table_fields_logging():
    """测试表格字段的日志输出"""
    
    try:
        # 初始化配置
        config_manager = V2ConfigManager()
        config = config_manager.config
        
        # 初始化TableEngine
        table_engine = TableEngine(config)
        
        # 执行一个简单的表格查询
        query = "中芯国际的财务数据"
        print(f"🔍 执行查询: {query}")
        
        # 调用search方法，这会触发我们添加的日志
        result = table_engine.search(query)
        
        print("✅ 查询执行完成，请查看日志输出")
        print("🔍 日志应该显示:")
        print("  1. reranked_results的字段检查")
        print("  2. 表格相关字段的内容")
        print("  3. Pipeline的字段使用情况")
        
        return result
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🔍 开始测试table_engine的字段传递...")
    result = test_table_fields_logging()
    
    if result:
        print("✅ 测试完成，请检查日志输出")
    else:
        print("❌ 测试失败")
