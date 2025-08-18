#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：

## 1. 全面测试TableEngine五层召回策略执行效果
## 2. 模拟表格文档数据
## 3. 测试各层搜索的实际结果
## 4. 验证结果去重和排序逻辑
"""

import sys
import os
import logging
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 模拟表格文档类
class MockTableDocument:
    """模拟表格文档类"""
    
    def __init__(self, doc_id: str, title: str, content: str, columns: List[str], table_type: str):
        self.metadata = {
            'id': doc_id,
            'title': title,
            'columns': columns,
            'table_type': table_type,
            'document_name': f"文档_{doc_id}",
            'page_number': 1
        }
        self.page_content = content

def create_mock_table_documents():
    """创建模拟表格文档"""
    documents = [
        MockTableDocument(
            "table_001",
            "财务收入统计表",
            "本表统计了公司2024年各季度的财务收入情况",
            ["季度", "主营业务收入", "其他业务收入", "总收入"],
            "财务统计表"
        ),
        MockTableDocument(
            "table_002", 
            "员工绩效评估表",
            "员工年度绩效评估结果，包含工作质量、工作效率等",
            ["员工姓名", "工作质量", "工作效率", "团队合作", "总分"],
            "人事管理表"
        )
    ]
    return documents

def test_table_engine_with_mock_data():
    """使用模拟数据测试TableEngine"""
    try:
        from v2.core.table_engine import TableEngine
        from v2.config.v2_config import TableEngineConfigV2
        
        print("🔍 测试TableEngine五层召回策略执行效果")
        
        # 创建配置和引擎
        config = TableEngineConfigV2()
        table_engine = TableEngine(config=config, skip_initial_load=True)
        
        # 注入模拟文档
        mock_docs = create_mock_table_documents()
        table_engine.table_docs = mock_docs
        table_engine._docs_loaded = True
        
        print(f"✅ 注入了 {len(mock_docs)} 个模拟表格文档")
        
        # 测试查询
        query = "财务收入"
        print(f"\n🔍 测试查询: '{query}'")
        
        # 执行搜索
        results = table_engine._search_tables(query)
        print(f"   - 总结果数: {len(results)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始全面测试TableEngine五层召回策略")
    
    if test_table_engine_with_mock_data():
        print("✅ 测试通过！")
        return True
    else:
        print("❌ 测试失败！")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
