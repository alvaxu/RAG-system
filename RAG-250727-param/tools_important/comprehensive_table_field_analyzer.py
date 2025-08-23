#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
程序说明：

## 1. 全面分析向量数据库中表格相关的所有字段
## 2. 检查HTML格式表格内容的存储位置和完整性
## 3. 验证表格处理优化后的字段变化
## 4. 提供详细的字段统计和内容分析报告

## 主要功能：
- 分析所有表格文档的元数据字段
- 检查HTML内容的存储位置（page_content vs metadata中的page_content）
- 验证语义化处理内容的存在性
- 统计字段覆盖率和内容质量
- 生成详细的表格字段分析报告
'''

import sys
import os
import json
import pickle
import logging
import numpy as np
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Any, Optional, Tuple

# 修复路径问题，添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings

# 导入统一的API密钥管理模块
from config.api_key_manager import get_dashscope_api_key

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensiveTableFieldAnalyzer:
    """全面的表格字段分析器"""
    
    def __init__(self, vector_db_path: str):
        """
        初始化分析器
        
        :param vector_db_path: 向量数据库路径
        """
        self.vector_db_path = vector_db_path
        self.vector_store = None
        self.analysis_results = {
            'summary': {},
            'field_analysis': {},
            'content_analysis': {},
            'html_content_analysis': {},
            'semantic_content_analysis': {},
            'metadata_completeness': {},
            'sample_documents': []
        }
    
    def load_vector_store(self) -> bool:
        """加载向量存储"""
        try:
            config = Settings.load_from_file('config.json')
            
            # 使用统一的API密钥管理模块获取API密钥
            config_key = config.dashscope_api_key
            api_key = get_dashscope_api_key(config_key)
            
            if not api_key:
                logger.warning("未找到有效的DashScope API密钥")
                return False
            
            # 初始化DashScope embeddings
            try:
                embedding_model = config.text_embedding_model
            except Exception as e:
                print(f"⚠️ 无法加载配置，使用默认embedding模型: {e}")
                embedding_model = 'text-embedding-v1'
            
            embeddings = DashScopeEmbeddings(dashscope_api_key=api_key, model=embedding_model)
            self.vector_store = FAISS.load_local(self.vector_db_path, embeddings, allow_dangerous_deserialization=True)
            logger.info(f"向量存储加载成功，包含 {len(self.vector_store.docstore._dict)} 个文档")
            return True
        except Exception as e:
            logger.error(f"加载向量存储失败: {e}")
            return False
    
    def analyze_table_documents(self) -> Dict[str, Any]:
        """分析所有表格文档"""
        if not self.vector_store or not hasattr(self.vector_store, 'docstore') or not hasattr(self.vector_store.docstore, '_dict'):
            print("❌ 向量存储结构异常")
            return {}
        
        docstore = self.vector_store.docstore._dict
        table_docs = []
        
        # 收集所有表格文档
        for doc_id, doc in docstore.items():
            try:
                if hasattr(doc, 'metadata') and doc.metadata and doc.metadata.get('chunk_type') == 'table':
                    table_docs.append((doc_id, doc))
            except Exception as e:
                logger.warning(f"处理文档 {doc_id} 时出错: {e}")
                continue
        
        print(f"🔍 找到 {len(table_docs)} 个表格文档")
        
        # 分析每个表格文档
        field_counter = Counter()
        html_content_stats = {
            'in_metadata': 0,
            'in_page_content': 0,
            'both_locations': 0,
            'neither_location': 0,
            'html_tags_detected': 0
        }
        
        semantic_content_stats = {
            'processed_table_content': 0,
            'table_summary': 0,
            'table_title': 0,
            'table_headers': 0,
            'table_row_count': 0,
            'table_column_count': 0
        }
        
        content_lengths = []
        document_names = set()
        table_types = Counter()
        
        # 详细分析前5个文档
        detailed_samples = min(5, len(table_docs))
        
        for i, (doc_id, doc) in enumerate(table_docs):
            # 统计字段
            if hasattr(doc, 'metadata') and doc.metadata:
                field_counter.update(doc.metadata.keys())
                
                # 统计特定字段
                for field in semantic_content_stats.keys():
                    if doc.metadata.get(field):
                        semantic_content_stats[field] += 1
                
                # 统计文档名称和表格类型
                if doc.metadata.get('document_name'):
                    document_names.add(doc.metadata['document_name'])
                if doc.metadata.get('table_type'):
                    table_types[doc.metadata['table_type']] += 1
            
            # HTML内容分析
            html_in_metadata = False
            html_in_page_content = False
            
            # 检查元数据中的HTML内容
            if 'page_content' in doc.metadata and doc.metadata['page_content']:
                content = str(doc.metadata['page_content'])
                if self._contains_html_tags(content):
                    html_in_metadata = True
                    html_content_stats['in_metadata'] += 1
                    html_content_stats['html_tags_detected'] += 1
                    content_lengths.append(len(content))
            
            # 检查doc.page_content属性
            if hasattr(doc, 'page_content') and doc.page_content:
                content = str(doc.page_content)
                if self._contains_html_tags(content):
                    html_in_page_content = True
                    html_content_stats['in_page_content'] += 1
                    html_content_stats['html_tags_detected'] += 1
                    if not html_in_metadata:
                        content_lengths.append(len(content))
            
            # 统计HTML内容位置
            if html_in_metadata and html_in_page_content:
                html_content_stats['both_locations'] += 1
            elif not html_in_metadata and not html_in_page_content:
                html_content_stats['neither_location'] += 1
            
            # 🔑 修复：统计所有HTML内容的长度，不重复计算
            if html_in_metadata:
                content_lengths.append(len(str(doc.metadata['page_content'])))
            if html_in_page_content:
                content_lengths.append(len(str(doc.page_content)))
            
            # 保存详细样本
            if i < detailed_samples:
                sample = self._create_document_sample(doc_id, doc, html_in_metadata, html_in_page_content)
                self.analysis_results['sample_documents'].append(sample)
        
        # 🔑 新增：动态检测所有元数据字段
        all_metadata_fields = set()
        for doc_id, doc in table_docs:
            if hasattr(doc, 'metadata') and doc.metadata:
                all_metadata_fields.update(doc.metadata.keys())
        
        # 保存分析结果
        self.analysis_results['summary'] = {
            'total_table_docs': len(table_docs),
            'unique_document_names': len(document_names),
            'document_names': list(document_names),
            'table_types': dict(table_types),
            'all_metadata_fields': list(all_metadata_fields)  # 🔑 新增：所有元数据字段
        }
        
        self.analysis_results['field_analysis'] = {
            'total_fields': len(field_counter),
            'field_frequency': dict(field_counter),
            'most_common_fields': field_counter.most_common(10)
        }
        
        self.analysis_results['html_content_analysis'] = html_content_stats
        self.analysis_results['semantic_content_analysis'] = semantic_content_stats
        self.analysis_results['content_analysis'] = {
            'total_content_lengths': len(content_lengths),
            'avg_content_length': np.mean(content_lengths) if content_lengths else 0,
            'min_content_length': min(content_lengths) if content_lengths else 0,
            'max_content_length': max(content_lengths) if content_lengths else 0
        }
        
        return self.analysis_results
    
    def _contains_html_tags(self, content: str) -> bool:
        """检查内容是否包含HTML标签"""
        import re
        # 使用正则表达式检测所有HTML标签，更全面准确
        html_pattern = r'<[^>]+>'
        return bool(re.search(html_pattern, content))
    
    def _create_document_sample(self, doc_id: str, doc: Any, html_in_metadata: bool, html_in_page_content: bool) -> Dict[str, Any]:
        """创建文档样本信息"""
        sample = {
            'doc_id': doc_id,
            'metadata_fields': list(doc.metadata.keys()) if hasattr(doc, 'metadata') and doc.metadata else [],
            'html_content_locations': {
                'in_metadata': html_in_metadata,
                'in_page_content': html_in_page_content
            }
        }
        
        # 添加关键元数据字段
        if hasattr(doc, 'metadata') and doc.metadata:
            for key in ['document_name', 'page_number', 'table_id', 'table_type', 'table_title', 'table_summary']:
                if key in doc.metadata:
                    sample[key] = doc.metadata[key]
        
        # 添加内容预览
        if hasattr(doc, 'page_content') and doc.page_content:
            sample['page_content_preview'] = str(doc.page_content)[:200] + '...' if len(str(doc.page_content)) > 200 else str(doc.page_content)
        
        if 'page_content' in doc.metadata and doc.metadata['page_content']:
            sample['metadata_page_content_preview'] = str(doc.metadata['page_content'])[:200] + '...' if len(str(doc.metadata['page_content'])) > 200 else str(doc.metadata['page_content'])
        
        return sample
    
    def generate_report(self) -> str:
        """生成分析报告"""
        report = []
        report.append("=" * 80)
        report.append("📊 表格字段全面分析报告")
        report.append("=" * 80)
        
        # 摘要信息
        summary = self.analysis_results['summary']
        report.append(f"\n📋 摘要信息:")
        report.append(f"  总表格文档数: {summary['total_table_docs']}")
        report.append(f"  唯一文档名数量: {summary['unique_document_names']}")
        report.append(f"  文档名称: {', '.join(summary['document_names'][:5])}")
        if len(summary['document_names']) > 5:
            report.append(f"  ... 还有 {len(summary['document_names']) - 5} 个")
        
        # 🔑 新增：显示所有元数据字段
        if 'all_metadata_fields' in summary and summary['all_metadata_fields']:
            report.append(f"  所有元数据字段 ({len(summary['all_metadata_fields'])}个):")
            fields_list = sorted(summary['all_metadata_fields'])
            for i in range(0, len(fields_list), 5):  # 每行显示5个字段
                row_fields = fields_list[i:i+5]
                report.append(f"    {', '.join(row_fields)}")
        
        # 表格类型分布
        if summary['table_types']:
            report.append(f"\n📊 表格类型分布:")
            for table_type, count in sorted(summary['table_types'].items(), key=lambda x: x[1], reverse=True):
                report.append(f"  {table_type}: {count}")
        
        # 字段分析
        field_analysis = self.analysis_results['field_analysis']
        report.append(f"\n🔍 字段分析:")
        report.append(f"  总字段数: {field_analysis['total_fields']}")
        report.append(f"  最常见字段 (前10):")
        for field, count in field_analysis['most_common_fields']:
            report.append(f"    {field}: {count}")
        
        # HTML内容分析
        html_analysis = self.analysis_results['html_content_analysis']
        report.append(f"\n🌐 HTML内容分析:")
        report.append(f"  元数据中包含HTML: {html_analysis['in_metadata']}")
        report.append(f"  page_content中包含HTML: {html_analysis['in_page_content']}")
        report.append(f"  两处都有HTML: {html_analysis['both_locations']}")
        report.append(f"  都没有HTML: {html_analysis['neither_location']}")
        report.append(f"  检测到HTML标签: {html_analysis['html_tags_detected']}")
        
        # 语义化内容分析
        semantic_analysis = self.analysis_results['semantic_content_analysis']
        report.append(f"\n🧠 语义化内容分析:")
        for field, count in semantic_analysis.items():
            report.append(f"  {field}: {count}")
        
        # 内容长度分析
        content_analysis = self.analysis_results['content_analysis']
        report.append(f"\n📏 内容长度分析:")
        report.append(f"  有内容长度的文档: {content_analysis['total_content_lengths']}")
        if content_analysis['total_content_lengths'] > 0:
            report.append(f"  平均长度: {content_analysis['avg_content_length']:.1f}")
            report.append(f"  最短长度: {content_analysis['min_content_length']}")
            report.append(f"  最长长度: {content_analysis['max_content_length']}")
        
        # 详细样本
        if self.analysis_results['sample_documents']:
            report.append(f"\n📄 详细样本 (前{len(self.analysis_results['sample_documents'])}个):")
            for i, sample in enumerate(self.analysis_results['sample_documents']):
                report.append(f"\n  📋 样本 {i+1}:")
                report.append(f"    文档ID: {sample['doc_id']}")
                if 'document_name' in sample:
                    report.append(f"    文档名: {sample['document_name']}")
                if 'table_id' in sample:
                    report.append(f"    表格ID: {sample['table_id']}")
                if 'table_type' in sample:
                    report.append(f"    表格类型: {sample['table_type']}")
                
                report.append(f"    HTML内容位置:")
                report.append(f"      元数据中: {'✅' if sample['html_content_locations']['in_metadata'] else '❌'}")
                report.append(f"      page_content中: {'✅' if sample['html_content_locations']['in_page_content'] else '❌'}")
                
                report.append(f"    元数据字段数: {len(sample['metadata_fields'])}")
                report.append(f"    元数据字段: {', '.join(sample['metadata_fields'][:10])}")
                if len(sample['metadata_fields']) > 10:
                    report.append(f"      ... 还有 {len(sample['metadata_fields']) - 10} 个")
        
        # 关键发现和建议
        report.append(f"\n💡 关键发现和建议:")
        
        # 检查HTML内容存储情况
        html_in_metadata = html_analysis['in_metadata']
        html_in_page_content = html_analysis['in_page_content']
        
        if html_in_metadata and html_in_page_content:
            report.append("  ✅ HTML内容在两个位置都有存储，确保内容完整性")
        elif html_in_metadata:
            report.append("  ✅ HTML内容存储在元数据中，符合优化方案设计")
        elif html_in_page_content:
            report.append("  ⚠️ HTML内容只存储在page_content中，建议检查元数据存储")
        else:
            report.append("  ❌ 未检测到HTML内容，需要检查表格处理流程")
        
        # 检查语义化内容
        processed_content_count = semantic_analysis['processed_table_content']
        if processed_content_count > 0:
            report.append(f"  ✅ 有 {processed_content_count} 个文档包含语义化处理内容")
        else:
            report.append("  ⚠️ 未检测到语义化处理内容，建议检查表格处理优化")
        
        # 🔑 改进：字段完整性检查，基于实际发现的字段
        if 'all_metadata_fields' in summary:
            actual_fields = set(summary['all_metadata_fields'])
            expected_fields = ['table_id', 'table_type', 'table_title', 'table_summary', 'table_headers', 'table_row_count', 'table_column_count']
            missing_fields = [field for field in expected_fields if field not in actual_fields]
            extra_fields = [field for field in actual_fields if field not in expected_fields and not field.startswith('_')]
            
            if missing_fields:
                report.append(f"  ⚠️ 缺少预期字段: {', '.join(missing_fields)}")
            else:
                report.append("  ✅ 所有预期字段都存在")
            
            if extra_fields:
                report.append(f"  🔍 发现额外字段: {', '.join(extra_fields[:10])}")
                if len(extra_fields) > 10:
                    report.append(f"      ... 还有 {len(extra_fields) - 10} 个额外字段")
        else:
            report.append("  ⚠️ 无法检查字段完整性，缺少字段信息")
        
        report.append("\n" + "=" * 80)
        return "\n".join(report)
    
    def save_analysis_results(self, output_file: str = "table_field_analysis_results.json"):
        """保存分析结果到文件"""
        try:
            # 转换numpy类型为Python原生类型
            def convert_numpy_types(obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, dict):
                    return {key: convert_numpy_types(value) for key, value in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy_types(item) for item in obj]
                else:
                    return obj
            
            converted_results = convert_numpy_types(self.analysis_results)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(converted_results, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 分析结果已保存到: {output_file}")
            return True
        except Exception as e:
            print(f"❌ 保存分析结果失败: {e}")
            return False

def main():
    """主函数"""
    print("🔍 表格字段全面分析器")
    print("=" * 50)
    
    # 检查向量数据库路径
    vector_db_path = "../central/vector_db"
    if not os.path.exists(vector_db_path):
        print(f"❌ 向量数据库路径不存在: {vector_db_path}")
        return
    
    # 创建分析器
    analyzer = ComprehensiveTableFieldAnalyzer(vector_db_path)
    
    # 加载向量存储
    print("📂 正在加载向量存储...")
    if not analyzer.load_vector_store():
        print("❌ 无法加载向量存储")
        return
    
    # 分析表格文档
    print("🔍 正在分析表格文档...")
    results = analyzer.analyze_table_documents()
    
    # 生成报告
    print("📊 正在生成分析报告...")
    report = analyzer.generate_report()
    print(report)
    
    # 保存结果
    print("💾 正在保存分析结果...")
    analyzer.save_analysis_results()
    
    print("\n✅ 分析完成！")

if __name__ == "__main__":
    main()
