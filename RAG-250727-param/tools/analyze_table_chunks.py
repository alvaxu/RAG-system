#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
程序说明：
## 1. 专门分析向量数据库中的table chunk文档
## 2. 基于现有分析工具，专门提取表格文档的元数据和内容
## 3. 分析表格文档的结构和内容特征
## 4. 帮助理解为什么评分算法给所有文档的分数都这么低
'''

import sys
import os
import pickle
import json
from pathlib import Path
from collections import defaultdict

def analyze_table_chunks():
    """分析向量数据库中的表格文档chunks"""
    print("=" * 60)
    print("分析向量数据库中的表格文档chunks")
    print("=" * 60)
    
    # 检查向量数据库文件
    vector_db_dir = Path("central/vector_db")
    index_file = vector_db_dir / "index.pkl"
    metadata_file = vector_db_dir / "metadata.pkl"
    
    if not index_file.exists():
        print(f"❌ 索引文件不存在: {index_file}")
        return
    
    try:
        # 方法1：从index.pkl读取
        print("🔍 方法1：从index.pkl读取表格文档...")
        table_docs_from_index = extract_table_docs_from_index(index_file)
        
        # 方法2：从metadata.pkl读取（如果存在）
        table_docs_from_metadata = []
        if metadata_file.exists():
            print("\n🔍 方法2：从metadata.pkl读取表格文档...")
            table_docs_from_metadata = extract_table_docs_from_metadata(metadata_file)
        
        # 合并结果
        all_table_docs = table_docs_from_index + table_docs_from_metadata
        
        if not all_table_docs:
            print("❌ 未找到任何表格文档")
            return
        
        print(f"\n📊 找到 {len(all_table_docs)} 个表格文档")
        
        # 分析表格文档的详细内容
        analyze_table_documents(all_table_docs)
        
        # 保存分析结果
        save_analysis_results(all_table_docs)
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        print(f"详细错误信息: {traceback.format_exc()}")

def extract_table_docs_from_index(index_file):
    """从index.pkl中提取表格文档"""
    table_docs = []
    
    try:
        with open(index_file, 'rb') as f:
            index_data = pickle.load(f)
        
        print(f"  索引文件类型: {type(index_data)}")
        print(f"  索引文件长度: {len(index_data)}")
        
        # 检查第1个元素（InMemoryDocstore）
        if len(index_data) >= 1:
            docstore = index_data[0]
            print(f"  第1个元素类型: {type(docstore)}")
            
            if hasattr(docstore, '_dict'):
                docstore_dict = docstore._dict
                print(f"  docstore._dict长度: {len(docstore_dict)}")
                
                # 筛选表格文档
                for doc_id, doc in docstore_dict.items():
                    if hasattr(doc, 'metadata') and doc.metadata:
                        chunk_type = doc.metadata.get('chunk_type', '')
                        if chunk_type == 'table':
                            table_docs.append({
                                'source': 'index_pkl_docstore',
                                'doc_id': doc_id,
                                'doc': doc,
                                'metadata': doc.metadata,
                                'page_content': getattr(doc, 'page_content', '')
                            })
        
        # 检查第2个元素（文档字典）
        if len(index_data) >= 2 and isinstance(index_data[1], dict):
            metadata_dict = index_data[1]
            print(f"  第2个元素类型: {type(metadata_dict)}")
            print(f"  第2个元素长度: {len(metadata_dict)}")
            
            # 筛选表格文档
            for doc_id, doc in metadata_dict.items():
                if isinstance(doc, dict) and doc.get('chunk_type') == 'table':
                    table_docs.append({
                        'source': 'index_pkl_metadata',
                        'doc_id': doc_id,
                        'doc': doc,
                        'metadata': doc,
                        'page_content': doc.get('page_content', '')
                    })
        
        print(f"  从index.pkl找到 {len(table_docs)} 个表格文档")
        
    except Exception as e:
        print(f"  从index.pkl读取失败: {e}")
    
    return table_docs

def extract_table_docs_from_metadata(metadata_file):
    """从metadata.pkl中提取表格文档"""
    table_docs = []
    
    try:
        with open(metadata_file, 'rb') as f:
            metadata = pickle.load(f)
        
        print(f"  metadata.pkl类型: {type(metadata)}")
        print(f"  metadata.pkl长度: {len(metadata)}")
        
        # 筛选表格文档
        for i, item in enumerate(metadata):
            if isinstance(item, dict) and item.get('chunk_type') == 'table':
                table_docs.append({
                    'source': 'metadata_pkl',
                    'doc_id': i,
                    'doc': item,
                    'metadata': item,
                    'page_content': item.get('page_content', '')
                })
        
        print(f"  从metadata.pkl找到 {len(table_docs)} 个表格文档")
        
    except Exception as e:
        print(f"  从metadata.pkl读取失败: {e}")
    
    return table_docs

def analyze_table_documents(table_docs):
    """分析表格文档的详细内容"""
    print(f"\n🔍 分析 {len(table_docs)} 个表格文档的详细内容...")
    
    # 统计信息
    stats = {
        'total_docs': len(table_docs),
        'metadata_fields': set(),
        'table_types': defaultdict(int),
        'document_names': set(),
        'content_lengths': [],
        'has_columns': 0,
        'has_table_type': 0,
        'has_financial_keywords': 0,
        'has_time_keywords': 0,
        'has_smic_keywords': 0
    }
    
    # 分析前10个文档的详细内容
    for i, doc_info in enumerate(table_docs[:10]):
        print(f"\n{'='*50}")
        print(f"📄 表格文档 {i+1}")
        print(f"{'='*50}")
        
        doc = doc_info['doc']
        metadata = doc_info['metadata']
        content = doc_info['page_content']
        source = doc_info['source']
        
        print(f"来源: {source}")
        print(f"文档ID: {doc_info['doc_id']}")
        
        # 分析元数据
        print(f"\n📋 元数据分析:")
        print(f"  元数据字段: {list(metadata.keys())}")
        stats['metadata_fields'].update(metadata.keys())
        
        # 检查关键字段
        key_fields = [
            'chunk_type', 'document_name', 'page_number', 'chunk_index',
            'table_id', 'table_type', 'columns', 'table_row_count', 'table_column_count',
            'source', 'title'
        ]
        
        for field in key_fields:
            value = metadata.get(field, 'NOT_FOUND')
            print(f"  {field}: {value}")
            
            # 统计特定字段
            if field == 'table_type' and value != 'NOT_FOUND':
                stats['table_types'][value] += 1
                stats['has_table_type'] += 1
            elif field == 'document_name' and value != 'NOT_FOUND':
                stats['document_names'].add(value)
            elif field == 'columns' and value != 'NOT_FOUND':
                stats['has_columns'] += 1
        
        # 分析内容
        if content:
            print(f"\n📝 内容分析:")
            print(f"  内容长度: {len(content)}")
            stats['content_lengths'].append(len(content))
            
            # 显示前300字符
            content_preview = content[:300] + "..." if len(content) > 300 else content
            print(f"  内容预览: {content_preview}")
            
            # 分析内容特征
            analyze_content_features(content, stats)
            
            # 检查是否包含特定关键词
            check_keywords_in_content(content, stats)
        else:
            print(f"\n❌ 没有页面内容")
    
    # 显示统计信息
    display_statistics(stats)
    
    # 分析剩余文档的元数据
    if len(table_docs) > 10:
        print(f"\n🔍 分析剩余 {len(table_docs) - 10} 个文档的元数据...")
        for i, doc_info in enumerate(table_docs[10:]):
            metadata = doc_info['metadata']
            stats['metadata_fields'].update(metadata.keys())
            
            # 统计特定字段
            if metadata.get('table_type'):
                stats['table_types'][metadata['table_type']] += 1
                stats['has_table_type'] += 1
            if metadata.get('document_name'):
                stats['document_names'].add(metadata['document_name'])
            if metadata.get('columns'):
                stats['has_columns'] += 1
        
        print(f"  完成剩余文档分析")

def analyze_content_features(content, stats):
    """分析内容特征"""
    lines = content.split('\n')
    print(f"  总行数: {len(lines)}")
    
    # 显示前5行
    print(f"  前5行内容:")
    for j, line in enumerate(lines[:5]):
        print(f"    {j+1:2d}: {line[:100]}")
    
    # 检查表格特征
    table_indicators = ['|', '\t', '表格', '表', '行', '列', '数据', '统计']
    found_indicators = []
    for indicator in table_indicators:
        if indicator in content:
            found_indicators.append(indicator)
    
    print(f"  表格特征: {found_indicators if found_indicators else '无'}")

def check_keywords_in_content(content, stats):
    """检查内容中的关键词"""
    # 财务关键词
    financial_keywords = ['收入', '支出', '利润', '成本', '费用', '营收', '收益', '金额', '总额']
    found_financial = [kw for kw in financial_keywords if kw in content]
    if found_financial:
        stats['has_financial_keywords'] += 1
        print(f"  财务关键词: {found_financial}")
    
    # 时间关键词
    time_keywords = ['2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024', '年', '月']
    found_time = [kw for kw in time_keywords if kw in content]
    if found_time:
        stats['has_time_keywords'] += 1
        print(f"  时间关键词: {found_time}")
    
    # 中芯国际关键词
    smic_keywords = ['中芯国际', 'SMIC', '中芯', '芯片', '半导体']
    found_smic = [kw for kw in smic_keywords if kw in content]
    if found_smic:
        stats['has_smic_keywords'] += 1
        print(f"  中芯国际关键词: {found_smic}")

def display_statistics(stats):
    """显示统计信息"""
    print(f"\n📊 表格文档统计信息")
    print("=" * 60)
    
    print(f"总文档数: {stats['total_docs']}")
    print(f"有表格类型的文档: {stats['has_table_type']}")
    print(f"有列信息的文档: {stats['has_columns']}")
    print(f"有财务关键词的文档: {stats['has_financial_keywords']}")
    print(f"有时间关键词的文档: {stats['has_time_keywords']}")
    print(f"有中芯国际关键词的文档: {stats['has_smic_keywords']}")
    
    print(f"\n元数据字段总数: {len(stats['metadata_fields'])}")
    print(f"元数据字段: {sorted(list(stats['metadata_fields']))}")
    
    if stats['table_types']:
        print(f"\n表格类型分布:")
        for table_type, count in sorted(stats['table_types'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {table_type}: {count}")
    
    if stats['document_names']:
        print(f"\n文档名称 (共{len(stats['document_names'])}个):")
        for doc_name in sorted(list(stats['document_names']))[:10]:
            print(f"  {doc_name}")
        if len(stats['document_names']) > 10:
            print(f"  ... 还有 {len(stats['document_names']) - 10} 个")
    
    if stats['content_lengths']:
        avg_length = sum(stats['content_lengths']) / len(stats['content_lengths'])
        print(f"\n内容长度统计:")
        print(f"  平均长度: {avg_length:.1f}")
        print(f"  最短长度: {min(stats['content_lengths'])}")
        print(f"  最长长度: {max(stats['content_lengths'])}")

def save_analysis_results(table_docs):
    """保存分析结果"""
    try:
        # 准备可序列化的数据
        results = {
            'total_table_docs': len(table_docs),
            'analysis_timestamp': str(Path().cwd()),
            'sample_docs': []
        }
        
        # 保存前5个文档的详细信息
        for i, doc_info in enumerate(table_docs[:5]):
            sample_doc = {
                'index': i,
                'source': doc_info['source'],
                'doc_id': str(doc_info['doc_id']),
                'metadata': doc_info['metadata'],
                'content_preview': doc_info['page_content'][:500] if doc_info['page_content'] else ''
            }
            results['sample_docs'].append(sample_doc)
        
        # 保存到文件
        output_file = "table_chunks_analysis.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 分析结果已保存到: {output_file}")
        
    except Exception as e:
        print(f"❌ 保存分析结果失败: {e}")

def main():
    """主函数"""
    print("🚀 开始分析向量数据库中的表格文档chunks")
    
    analyze_table_chunks()
    
    print("\n" + "=" * 60)
    print("分析完成！")

if __name__ == "__main__":
    main()
