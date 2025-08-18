#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
程序说明：
## 1. 诊断TableEngine中表格结构分析的实际输出
## 2. 分析为什么评分算法给所有文档的分数都这么低
## 3. 检查表格文档的元数据和内容结构
'''

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def debug_table_analysis():
    """诊断表格结构分析问题"""
    print("=" * 60)
    print("诊断TableEngine中表格结构分析问题")
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
        
        # 分析前几个文档
        print("\n🔍 分析前3个表格文档的结构...")
        for i, doc in enumerate(table_engine.table_docs[:3]):
            print(f"\n--- 文档 {i+1} ---")
            
            # 检查文档基本属性
            print(f"文档类型: {type(doc)}")
            print(f"是否有metadata: {hasattr(doc, 'metadata')}")
            print(f"是否有page_content: {hasattr(doc, 'page_content')}")
            
            if hasattr(doc, 'metadata'):
                metadata = doc.metadata
                print(f"metadata类型: {type(metadata)}")
                print(f"metadata内容: {metadata}")
                
                # 检查关键字段
                key_fields = ['columns', 'table_row_count', 'table_column_count', 'table_type']
                for field in key_fields:
                    value = metadata.get(field, 'NOT_FOUND')
                    print(f"  {field}: {value}")
            
            if hasattr(doc, 'page_content'):
                content = doc.page_content
                print(f"page_content长度: {len(content)}")
                print(f"page_content前200字符: {content[:200]}...")
            
            # 执行表格结构分析
            print("\n🔍 执行表格结构分析...")
            try:
                analysis = table_engine._analyze_table_structure(doc)
                print(f"分析结果:")
                for key, value in analysis.items():
                    print(f"  {key}: {value}")
                
                # 计算质量评分
                quality_score = table_engine._calculate_quality_score(analysis)
                print(f"质量评分: {quality_score}")
                
                # 模拟结构搜索评分
                print("\n🔍 模拟结构搜索评分...")
                query = "中芯国际的营业收入从2017年到2024年的变化趋势如何？"
                query_lower = query.lower()
                
                score = 0.3  # 基础分数
                print(f"基础分数: {score}")
                
                # 表格类型匹配
                if analysis['table_type'] != 'unknown':
                    table_type_lower = analysis['table_type'].lower()
                    if query_lower in table_type_lower:
                        score += 0.4
                        print(f"表格类型匹配加分: +0.4 (类型: {analysis['table_type']})")
                    elif any(word in table_type_lower for word in query_lower.split()):
                        score += 0.4
                        print(f"表格类型部分匹配加分: +0.4 (类型: {analysis['table_type']})")
                    else:
                        print(f"表格类型不匹配: {analysis['table_type']}")
                else:
                    print("表格类型为unknown，无法匹配")
                
                # 业务领域匹配
                if analysis['business_domain'] != 'unknown':
                    domain_lower = analysis['business_domain'].lower()
                    if query_lower in domain_lower:
                        score += 0.5
                        print(f"业务领域匹配加分: +0.5 (领域: {analysis['business_domain']})")
                    elif any(word in domain_lower for word in query_lower.split()):
                        score += 0.5
                        print(f"业务领域部分匹配加分: +0.5 (领域: {analysis['business_domain']})")
                    else:
                        print(f"业务领域不匹配: {analysis['business_domain']}")
                else:
                    print("业务领域为unknown，无法匹配")
                
                # 列名匹配
                columns = analysis['columns']
                if isinstance(columns, list) and columns:
                    print(f"检查列名匹配: {columns}")
                    for col in columns:
                        if isinstance(col, str):
                            col_lower = col.lower()
                            if query_lower in col_lower:
                                score += 0.8
                                print(f"列名精确匹配加分: +0.8 (列名: {col})")
                            elif any(word in col_lower for word in query_lower.split()):
                                score += 0.5
                                print(f"列名部分匹配加分: +0.5 (列名: {col})")
                else:
                    print("没有列名信息")
                
                # 质量分数
                quality_score = analysis['quality_score']
                score += quality_score * 0.3
                print(f"质量分数加分: +{quality_score * 0.3:.2f} (质量分数: {quality_score})")
                
                print(f"\n🎯 最终评分: {score:.2f}")
                
                # 检查是否通过阈值
                threshold = 0.2  # 配置文件中的值
                print(f"阈值: {threshold}")
                if score >= threshold:
                    print("✅ 通过阈值")
                else:
                    print("❌ 未通过阈值")
                
            except Exception as e:
                print(f"❌ 分析失败: {e}")
                import traceback
                print(f"详细错误: {traceback.format_exc()}")
        
        print("\n🎉 诊断完成！")
        
    except Exception as e:
        print(f"❌ 诊断失败: {e}")
        import traceback
        print(f"详细错误信息: {traceback.format_exc()}")

def main():
    """主函数"""
    print("🚀 开始诊断TableEngine表格结构分析问题")
    
    debug_table_analysis()
    
    print("\n" + "=" * 60)
    print("诊断完成！")

if __name__ == "__main__":
    main()
