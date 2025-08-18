#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
程序说明：
## 1. 直接查看表格文档的实际内容
## 2. 检查表格文档的元数据和页面内容结构
## 3. 分析为什么评分算法给所有文档的分数都这么低
'''

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def inspect_table_content():
    """检查表格文档的实际内容"""
    print("=" * 60)
    print("检查表格文档的实际内容")
    print("=" * 60)
    
    try:
        # 导入必要的模块
        from v2.config.v2_config import load_v2_config
        from v2.core.table_engine import TableEngine
        
        print("🔍 加载配置...")
        config_manager = load_v2_config('v2/config/v2_config.json')
        table_config = config_manager.get_engine_config('table')
        
        print("🔍 初始化表格引擎...")
        table_engine = TableEngine(table_config, skip_initial_load=False)
        
        print(f"📊 表格文档数量: {len(table_engine.table_docs)}")
        
        if not table_engine.table_docs:
            print("❌ 没有表格文档，无法进行分析")
            return
        
        # 分析前5个文档的详细内容
        print("\n🔍 分析前5个表格文档的详细内容...")
        for i, doc in enumerate(table_engine.table_docs[:5]):
            print(f"\n{'='*50}")
            print(f"📄 文档 {i+1}")
            print(f"{'='*50}")
            
            # 检查文档基本属性
            print(f"文档类型: {type(doc)}")
            print(f"是否有metadata: {hasattr(doc, 'metadata')}")
            print(f"是否有page_content: {hasattr(doc, 'page_content')}")
            
            if hasattr(doc, 'metadata'):
                metadata = doc.metadata
                print(f"\n📋 METADATA:")
                print(f"  类型: {type(metadata)}")
                print(f"  内容: {metadata}")
                
                # 检查关键字段
                key_fields = [
                    'chunk_type', 'columns', 'table_row_count', 'table_column_count', 
                    'table_type', 'source', 'document_name', 'page_number'
                ]
                print(f"\n🔑 关键字段检查:")
                for field in key_fields:
                    value = metadata.get(field, 'NOT_FOUND')
                    print(f"  {field}: {value}")
            
            if hasattr(doc, 'page_content'):
                content = doc.page_content
                print(f"\n📝 PAGE_CONTENT:")
                print(f"  长度: {len(content)}")
                print(f"  前500字符: {content[:500]}...")
                
                # 检查内容特征
                print(f"\n🔍 内容特征分析:")
                lines = content.split('\n')
                print(f"  总行数: {len(lines)}")
                
                # 显示前10行
                print(f"  前10行内容:")
                for j, line in enumerate(lines[:10]):
                    print(f"    {j+1:2d}: {line[:100]}")
                
                # 检查是否包含表格特征
                table_indicators = ['|', '\t', '表格', '表', '行', '列', '数据', '统计']
                found_indicators = []
                for indicator in table_indicators:
                    if indicator in content:
                        found_indicators.append(indicator)
                
                print(f"  表格特征: {found_indicators if found_indicators else '无'}")
                
                # 检查是否包含财务相关关键词
                financial_keywords = ['收入', '支出', '利润', '成本', '费用', '营收', '收益', '金额', '总额']
                found_financial = []
                for keyword in financial_keywords:
                    if keyword in content:
                        found_financial.append(keyword)
                
                print(f"  财务关键词: {found_financial if found_financial else '无'}")
                
                # 检查是否包含时间相关关键词
                time_keywords = ['2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024', '年', '月']
                found_time = []
                for keyword in time_keywords:
                    if keyword in content:
                        found_time.append(keyword)
                
                print(f"  时间关键词: {found_time if found_time else '无'}")
                
                # 检查是否包含中芯国际相关关键词
                smic_keywords = ['中芯国际', 'SMIC', '中芯', '芯片', '半导体']
                found_smic = []
                for keyword in smic_keywords:
                    if keyword in content:
                        found_smic.append(keyword)
                
                print(f"  中芯国际关键词: {found_smic if found_smic else '无'}")
            
            # 执行表格结构分析
            print(f"\n🔍 执行表格结构分析...")
            try:
                analysis = table_engine._analyze_table_structure(doc)
                print(f"分析结果:")
                for key, value in analysis.items():
                    print(f"  {key}: {value}")
                
                # 计算质量评分
                quality_score = table_engine._calculate_quality_score(analysis)
                print(f"质量评分: {quality_score}")
                
            except Exception as e:
                print(f"❌ 分析失败: {e}")
                import traceback
                print(f"详细错误: {traceback.format_exc()}")
        
        print("\n🎉 表格文档内容检查完成！")
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        print(f"详细错误信息: {traceback.format_exc()}")

def main():
    """主函数"""
    print("🚀 开始检查表格文档的实际内容")
    
    inspect_table_content()
    
    print("\n" + "=" * 60)
    print("检查完成！")

if __name__ == "__main__":
    main()
