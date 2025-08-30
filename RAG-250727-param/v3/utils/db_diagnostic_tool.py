#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
V3版本数据库诊断工具

功能：
1. 分析向量数据库结构和内容
2. 检查文档类型分布
3. 分析元数据字段
4. 输出诊断报告
5. 支持保存结果到JSON文件
6. 🔢 向量数据深度分析（范数分布、维度验证）
7. 🔗 向量相似度分析（质量评估、异常检测）
8. 📋 数据质量检查报告（100分制评分）
9. 📋 详细文档列表显示（可选交互功能）
'''

import os
import json
import logging
import pickle
import numpy as np
from typing import Dict, List, Any, Optional
from pathlib import Path
from collections import defaultdict

from core.vector_store_manager import LangChainVectorStoreManager
from config.config_manager import ConfigManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DatabaseDiagnosticTool:
    """数据库诊断工具"""
    
    def __init__(self, config_path: str = None):
        """初始化诊断工具"""
        try:
            if config_path:
                self.config_manager = ConfigManager(config_path)
            else:
                self.config_manager = ConfigManager()
            
            self.vector_store_manager = LangChainVectorStoreManager(self.config_manager)
            logging.info("数据库诊断工具初始化完成")
            
        except Exception as e:
            logging.error(f"初始化失败: {e}")
            raise
    
    def run_diagnostic(self) -> Dict[str, Any]:
        """运行完整的数据库诊断"""
        print("🔍 V3版本数据库诊断工具启动")
        print("=" * 60)
        
        try:
            # 1. 加载向量数据库
            print("📚 加载向量数据库...")
            if not self.vector_store_manager.load():
                print("❌ 无法加载向量数据库")
                return {'success': False, 'error': '无法加载向量数据库'}
            
            # 2. 获取数据库基本信息
            print("📊 获取数据库基本信息...")
            basic_info = self._get_basic_info()
            
            # 3. 分析文档结构
            print("🔍 分析文档结构...")
            structure_info = self._analyze_document_structure()
            
            # 4. 分析元数据
            print("📋 分析元数据...")
            metadata_info = self._analyze_metadata()
            
            # 5. 检查图片文档
            print("📷 检查图片文档...")
            image_info = self._check_image_docs()
            
            # 6. 检查表格文档
            print("📊 检查表格文档...")
            table_info = self._check_table_docs()
            
            # 7. 检查文本文档
            print("📝 检查文本文档...")
            text_info = self._check_text_docs()

            # 8. 分析向量数据
            print("🔢 分析向量数据...")
            vector_info = self._analyze_vector_data(self.vector_store_manager.vector_store)

            # 9. 生成数据质量检查报告
            print("📋 生成数据质量检查报告...")
            quality_report = self._generate_quality_report(structure_info, image_info, table_info, vector_info)

            # 10. 生成诊断报告
            print("📋 生成诊断报告...")
            diagnostic_report = {
                'success': True,
                'basic_info': basic_info,
                'structure_info': structure_info,
                'metadata_info': metadata_info,
                'image_info': image_info,
                'table_info': table_info,
                'text_info': text_info,
                'vector_info': vector_info,
                'quality_report': quality_report
            }

            # 11. 显示详细文档列表（可选）
            show_detailed = input("\n是否显示详细的文档列表? (y/n): ").strip().lower()
            if show_detailed == 'y':
                self._show_detailed_document_list(structure_info)

            # 12. 询问是否保存结果
            save_choice = input("\n是否保存诊断结果到文件? (y/n): ").strip().lower()
            if save_choice == 'y':
                output_file = "v3_db_diagnostic_results.json"
                self._save_results(diagnostic_report, output_file)
                print(f"💾 诊断结果已保存到: {output_file}")
            
            print("\n✅ 数据库诊断完成！")
            return diagnostic_report
            
        except Exception as e:
            logging.error(f"数据库诊断失败: {e}")
            print(f"❌ 数据库诊断失败: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def _get_basic_info(self) -> Dict[str, Any]:
        """获取数据库基本信息"""
        try:
            vector_store = self.vector_store_manager.vector_store
            if not vector_store or not hasattr(vector_store, 'docstore'):
                return {'error': '向量存储结构异常'}
            
            docstore = vector_store.docstore._dict
            total_docs = len(docstore)
            
            # 获取向量数据库路径
            vector_db_path = self.config_manager.get_path('vector_db_dir')
            
            basic_info = {
                'total_documents': total_docs,
                'vector_db_path': vector_db_path,
                'vector_db_exists': os.path.exists(vector_db_path) if vector_db_path else False
            }
            
            # 检查向量数据库文件
            if vector_db_path and os.path.exists(vector_db_path):
                files = list(Path(vector_db_path).glob('*'))
                basic_info['vector_db_files'] = [
                    {
                        'name': f.name,
                        'size': f.stat().st_size if f.is_file() else 0,
                        'type': 'file' if f.is_file() else 'directory'
                    }
                    for f in files
                ]
            
            print(f"📚 总文档数: {total_docs}")
            print(f"📁 向量数据库路径: {vector_db_path}")
            print(f"✅ 向量数据库存在: {basic_info['vector_db_exists']}")
            
            return basic_info
            
        except Exception as e:
            logging.error(f"获取基本信息失败: {e}")
            return {'error': str(e)}
    
    def _analyze_document_structure(self) -> Dict[str, Any]:
        """分析文档结构"""
        try:
            vector_store = self.vector_store_manager.vector_store
            if not vector_store or not hasattr(vector_store, 'docstore'):
                return {'error': '向量存储结构异常'}
            
            docstore = vector_store.docstore._dict
            
            # 统计文档类型分布
            chunk_types = defaultdict(int)
            document_names = set()
            all_fields = set()
            
            for doc_id, doc in docstore.items():
                metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
                
                # 统计分块类型
                chunk_type = metadata.get('chunk_type', 'unknown')
                chunk_types[chunk_type] += 1
                
                # 统计文档名称
                doc_name = metadata.get('document_name', 'unknown')
                document_names.add(doc_name)
                
                # 收集所有字段
                all_fields.update(metadata.keys())
            
            structure_info = {
                'chunk_type_distribution': dict(chunk_types),
                'unique_document_names': list(document_names),
                'total_unique_documents': len(document_names),
                'all_metadata_fields': list(all_fields),
                'total_metadata_fields': len(all_fields)
            }
            
            print(f"\n📊 分块类型分布:")
            for chunk_type, count in sorted(chunk_types.items()):
                print(f"   {chunk_type}: {count}")
            
            print(f"\n📚 文档统计:")
            print(f"  总文档数: {len(docstore)}")
            print(f"  唯一文档名: {len(document_names)}")
            print(f"  具体文档名: {list(document_names)}")
            print(f"  元数据字段数: {len(all_fields)}")
            
            return structure_info
            
        except Exception as e:
            logging.error(f"分析文档结构失败: {e}")
            return {'error': str(e)}
    
    def _analyze_metadata(self) -> Dict[str, Any]:
        """分析元数据结构"""
        try:
            vector_store = self.vector_store_manager.vector_store
            if not vector_store or not hasattr(vector_store, 'docstore'):
                return {'error': '向量存储结构异常'}
            
            docstore = vector_store.docstore._dict
            
            # 分析字段类型和示例
            field_types = defaultdict(set)
            field_examples = defaultdict(list)
            chunk_type_fields = defaultdict(set)
            
            for doc_id, doc in docstore.items():
                metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
                chunk_type = metadata.get('chunk_type', 'unknown')
                
                for field, value in metadata.items():
                    field_types[field].add(type(value).__name__)
                    chunk_type_fields[chunk_type].add(field)
                    
                    # 保存前3个示例
                    if len(field_examples[field]) < 3:
                        field_examples[field].append({
                            'chunk_type': chunk_type,
                            'value': str(value)[:100] + '...' if len(str(value)) > 100 else str(value)
                        })
            
            metadata_info = {
                'field_types': {k: list(v) for k, v in field_types.items()},
                'chunk_type_fields': {k: list(v) for k, v in chunk_type_fields.items()},
                'field_examples': {k: v for k, v in field_examples.items()}
            }
            
            print(f"\n🔍 字段类型分析:")
            for field, types in sorted(field_types.items()):
                print(f"  {field}: {', '.join(sorted(types))}")
            
            return metadata_info
            
        except Exception as e:
            logging.error(f"分析元数据失败: {e}")
            return {'error': str(e)}
    
    def _check_image_docs(self) -> Dict[str, Any]:
        """检查图片文档"""
        try:
            vector_store = self.vector_store_manager.vector_store
            if not vector_store or not hasattr(vector_store, 'docstore'):
                return {'error': '向量存储结构异常'}
            
            docstore = vector_store.docstore._dict
            image_docs = []
            
            for doc_id, doc in docstore.items():
                if hasattr(doc, 'metadata') and doc.metadata and doc.metadata.get('chunk_type') == 'image':
                    image_docs.append((doc_id, doc))
            
            image_info = {
                'total_image_docs': len(image_docs),
                'enhanced_description_stats': {
                    'with_enhanced': 0,
                    'without_enhanced': 0
                },
                'samples': []
            }
            
            print(f"\n📷 找到 {len(image_docs)} 个图片文档")
            
            # 分析enhanced_description字段
            enhanced_count = 0
            empty_count = 0
            
            for doc_id, doc in image_docs:
                enhanced_desc = doc.metadata.get('enhanced_description', '')
                if enhanced_desc:
                    enhanced_count += 1
                else:
                    empty_count += 1
            
            image_info['enhanced_description_stats']['with_enhanced'] = enhanced_count
            image_info['enhanced_description_stats']['without_enhanced'] = empty_count
            
            print(f"✅ 有enhanced_description的图片: {enhanced_count}")
            print(f"❌ 无enhanced_description的图片: {empty_count}")
            if (enhanced_count + empty_count) > 0:
                print(f"📈 覆盖率: {enhanced_count/(enhanced_count+empty_count)*100:.1f}%")
            
            # 显示前几个图片文档的详细信息
            for i, (doc_id, doc) in enumerate(image_docs[:3]):
                sample_info = {
                    'index': i+1,
                    'doc_id': doc_id,
                    'document_name': doc.metadata.get('document_name', 'N/A'),
                    'page_number': doc.metadata.get('page_number', 'N/A'),
                    'image_id': doc.metadata.get('image_id', 'N/A'),
                    'enhanced_description': doc.metadata.get('enhanced_description', '')[:100] + '...' if len(doc.metadata.get('enhanced_description', '')) > 100 else doc.metadata.get('enhanced_description', '')
                }
                image_info['samples'].append(sample_info)
                
                print(f"\n📷 图片文档 {i+1}:")
                print(f"  ID: {doc_id}")
                print(f"  文档名: {doc.metadata.get('document_name', 'N/A')}")
                print(f"  页码: {doc.metadata.get('page_number', 'N/A')}")
                print(f"  图片ID: {doc.metadata.get('image_id', 'N/A')}")
                print(f"  增强描述: {doc.metadata.get('enhanced_description', '')[:100] + '...' if len(doc.metadata.get('enhanced_description', '')) > 100 else doc.metadata.get('enhanced_description', '')}")
            
            return image_info
            
        except Exception as e:
            logging.error(f"检查图片文档失败: {e}")
            return {'error': str(e)}
    
    def _check_table_docs(self) -> Dict[str, Any]:
        """检查表格文档"""
        try:
            vector_store = self.vector_store_manager.vector_store
            if not vector_store or not hasattr(vector_store, 'docstore'):
                return {'error': '向量存储结构异常'}
            
            docstore = vector_store.docstore._dict
            table_docs = []
            
            for doc_id, doc in docstore.items():
                if hasattr(doc, 'metadata') and doc.metadata and doc.metadata.get('chunk_type') == 'table':
                    table_docs.append((doc_id, doc))
            
            table_info = {
                'total_table_docs': len(table_docs),
                'metadata_fields': set(),
                'table_types': defaultdict(int),
                'document_names': set(),
                'samples': []
            }
            
            print(f"\n📊 找到 {len(table_docs)} 个表格文档")
            
            # 分析前几个表格文档
            for i, (doc_id, doc) in enumerate(table_docs[:3]):
                sample_info = {
                    'index': i+1,
                    'doc_id': doc_id,
                    'document_name': doc.metadata.get('document_name', 'N/A'),
                    'page_number': doc.metadata.get('page_number', 'N/A'),
                    'table_id': doc.metadata.get('table_id', 'N/A'),
                    'table_type': doc.metadata.get('table_type', 'N/A')
                }
                table_info['samples'].append(sample_info)
                
                print(f"\n📄 表格文档 {i+1}:")
                print(f"  文档ID: {doc_id}")
                print(f"  文档名: {doc.metadata.get('document_name', 'N/A')}")
                print(f"  页码: {doc.metadata.get('page_number', 'N/A')}")
                print(f"  表格ID: {doc.metadata.get('table_id', 'N/A')}")
                print(f"  表格类型: {doc.metadata.get('table_type', 'N/A')}")
                
                # 收集元数据字段
                if hasattr(doc, 'metadata') and doc.metadata:
                    table_info['metadata_fields'].update(doc.metadata.keys())
                    
                    # 统计特定字段
                    if doc.metadata.get('table_type'):
                        table_info['table_types'][doc.metadata['table_type']] += 1
                    if doc.metadata.get('document_name'):
                        table_info['document_names'].add(doc.metadata['document_name'])
            
            # 转换set为list以便JSON序列化
            table_info['metadata_fields'] = list(table_info['metadata_fields'])
            table_info['document_names'] = list(table_info['document_names'])
            table_info['table_types'] = dict(table_info['table_types'])
            
            print(f"\n📊 表格文档统计:")
            print(f"  总文档数: {table_info['total_table_docs']}")
            print(f"  元数据字段数: {len(table_info['metadata_fields'])}")
            
            return table_info
            
        except Exception as e:
            logging.error(f"检查表格文档失败: {e}")
            return {'error': str(e)}
    
    def _check_text_docs(self) -> Dict[str, Any]:
        """检查文本文档"""
        try:
            vector_store = self.vector_store_manager.vector_store
            if not vector_store or not hasattr(vector_store, 'docstore'):
                return {'error': '向量存储结构异常'}
            
            docstore = vector_store.docstore._dict
            text_docs = []
            
            for doc_id, doc in docstore.items():
                if hasattr(doc, 'metadata') and doc.metadata and doc.metadata.get('chunk_type') == 'text':
                    text_docs.append((doc_id, doc))
            
            text_info = {
                'total_text_docs': len(text_docs),
                'document_names': set(),
                'page_numbers': set(),
                'samples': []
            }
            
            print(f"\n📝 找到 {len(text_docs)} 个文本文档")
            
            # 分析前几个文本文档
            for i, (doc_id, doc) in enumerate(text_docs[:3]):
                sample_info = {
                    'index': i+1,
                    'doc_id': doc_id,
                    'document_name': doc.metadata.get('document_name', 'N/A'),
                    'page_number': doc.metadata.get('page_number', 'N/A'),
                    'chunk_index': doc.metadata.get('chunk_index', 'N/A'),
                    'content_preview': doc.page_content[:100] + '...' if hasattr(doc, 'page_content') and len(doc.page_content) > 100 else (doc.page_content if hasattr(doc, 'page_content') else 'N/A')
                }
                text_info['samples'].append(sample_info)
                
                print(f"\n📝 文本文档 {i+1}:")
                print(f"  文档ID: {doc_id}")
                print(f"  文档名: {doc.metadata.get('document_name', 'N/A')}")
                print(f"  页码: {doc.metadata.get('page_number', 'N/A')}")
                print(f"  块索引: {doc.metadata.get('chunk_index', 'N/A')}")
                print(f"  内容预览: {doc.page_content[:100] + '...' if hasattr(doc, 'page_content') and len(doc.page_content) > 100 else (doc.page_content if hasattr(doc, 'page_content') else 'N/A')}")
                
                # 收集统计信息
                if doc.metadata.get('document_name'):
                    text_info['document_names'].add(doc.metadata['document_name'])
                if doc.metadata.get('page_number'):
                    text_info['page_numbers'].add(doc.metadata['page_number'])
            
            # 转换set为list以便JSON序列化
            text_info['document_names'] = list(text_info['document_names'])
            text_info['page_numbers'] = list(text_info['page_numbers'])
            
            print(f"\n📝 文本文档统计:")
            print(f"  总文档数: {text_info['total_text_docs']}")
            print(f"  唯一文档名: {len(text_info['document_names'])}")
            print(f"  页码范围: {min(text_info['page_numbers']) if text_info['page_numbers'] else 'N/A'} - {max(text_info['page_numbers']) if text_info['page_numbers'] else 'N/A'}")
            
            return text_info

        except Exception as e:
            logging.error(f"检查文本文档失败: {e}")
            return {'error': str(e)}

    def _analyze_vector_data(self, vector_store) -> Dict[str, Any]:
        """分析向量数据的分布和样本"""
        print("\n🔢 向量数据分析")
        print("=" * 60)

        if not vector_store:
            print("❌ 向量存储对象无效")
            return None

        try:
            # 获取向量数据
            vectors = vector_store.index.reconstruct_n(0, vector_store.index.ntotal)
            vector_info = {
                'vector_count': vector_store.index.ntotal,
                'vector_dimension': vector_store.index.d,
                'vectors': vectors
            }

            print(f"📊 向量统计:")
            print(f"  向量数量: {vector_info['vector_count']}")
            print(f"  向量维度: {vector_info['vector_dimension']}")

            if vector_info['vector_count'] > 0:
                # 向量范数分析
                norms = np.linalg.norm(vectors, axis=1)
                vector_info['norm_stats'] = {
                    'min': float(norms.min()),
                    'max': float(norms.max()),
                    'mean': float(norms.mean()),
                    'std': float(norms.std())
                }

                print(f"\n📏 向量范数统计:")
                print(f"  最小值: {norms.min():.4f}")
                print(f"  最大值: {norms.max():.4f}")
                print(f"  平均值: {norms.mean():.4f}")
                print(f"  标准差: {norms.std():.4f}")

                # 显示向量样本
                show_samples = input("\n是否显示向量数据样本? (y/n): ").strip().lower()
                if show_samples == 'y':
                    print(f"\n🔍 向量样本:")
                    sample_count = min(5, vector_info['vector_count'])
                    for i in range(sample_count):
                        print(f"  向量 {i+1}: [{vectors[i][0]:.4f}, {vectors[i][1]:.4f}, ..., {vectors[i][-1]:.4f}]")
                        print(f"    范数: {norms[i]:.4f}")

                    # 分析向量相似度
                    if vector_info['vector_count'] > 1:
                        self._analyze_vector_similarity(vectors, vector_info)

            return vector_info

        except Exception as e:
            print(f"❌ 向量数据分析失败: {e}")
            return None

    def _analyze_vector_similarity(self, vectors, vector_info):
        """分析向量相似度 - 评估向量化质量和发现潜在问题"""
        print("\n🔗 向量相似度分析")
        print("-" * 40)
        print("🎯 作用：评估向量化质量，发现重复内容，优化检索参数")

        try:
            # 计算前10个向量之间的相似度
            sample_size = min(10, vector_info['vector_count'])
            sample_vectors = vectors[:sample_size]

            # 归一化向量用于计算余弦相似度
            norms = np.linalg.norm(sample_vectors, axis=1, keepdims=True)
            normalized_vectors = sample_vectors / norms

            # 计算相似度矩阵
            similarity_matrix = np.dot(normalized_vectors, normalized_vectors.T)

            print(f"📈 前{sample_size}个向量的相似度矩阵:")
            print("     ", end="")
            for i in range(sample_size):
                print("8d")
            print()

            for i in range(sample_size):
                print("3d", end="")
                for j in range(sample_size):
                    if i == j:
                        print("1.0000", end="")
                    else:
                        sim = similarity_matrix[i, j]
                        # 用不同标识符表示相似度级别
                        if sim > 0.8:
                            print(".4f", end="")
                        elif sim > 0.6:
                            print(".4f", end="")
                        elif sim > 0.4:
                            print(".4f", end="")
                        else:
                            print(".4f", end="")
                print()

            # 分析相似度分布
            similarities = []
            for i in range(sample_size):
                for j in range(i+1, sample_size):
                    similarities.append(similarity_matrix[i, j])

            if similarities:
                similarities = np.array(similarities)
                print("\n📊 相似度统计:")
                print(f"  平均相似度: {similarities.mean():.4f}")
                print(f"  最大相似度: {similarities.max():.4f}")
                print(f"  最小相似度: {similarities.min():.4f}")
                print(f"  相似度标准差: {similarities.std():.4f}")
                # 质量评估
                print("\n🔍 质量评估:")
                if similarities.mean() > 0.7:
                    print("  ⚠️  相似度过高：可能存在大量重复内容")
                elif similarities.mean() > 0.5:
                    print("  ✅ 相似度适中：内容多样性良好")
                elif similarities.mean() > 0.3:
                    print("  ✅ 相似度正常：内容区分度良好")
                else:
                    print("  ✅ 相似度较低：内容高度多样化")

                # 检查是否有异常高的相似度
                high_sim_pairs = [(i, j) for i in range(sample_size) for j in range(i+1, sample_size) if similarity_matrix[i, j] > 0.9]
                if high_sim_pairs:
                    print(f"  🚨 发现 {len(high_sim_pairs)} 对高度相似的向量 (>0.9)")
                    print("     可能表示重复内容或向量化异常")

        except Exception as e:
            print(f"❌ 相似度分析失败: {e}")

    def _generate_quality_report(self, structure_info, image_info, table_info, vector_info) -> Dict[str, Any]:
        """生成数据质量检查报告"""
        print("\n📋 数据质量检查报告")
        print("=" * 60)

        report = {
            'overall_score': 0,
            'issues': [],
            'recommendations': []
        }

        # 检查1: 文档数量合理性
        if structure_info and structure_info.get('total_docs', 0) > 0:
            print("✅ 文档数量检查通过")
            report['overall_score'] += 20
        else:
            print("❌ 文档数量异常")
            report['issues'].append("数据库中没有文档")
            report['recommendations'].append("检查文档处理流程是否正常")

        # 检查2: 元数据完整性
        if structure_info and len(structure_info.get('all_metadata_fields', [])) > 10:
            print("✅ 元数据字段丰富")
            report['overall_score'] += 25
        else:
            print("❌ 元数据字段不足")
            report['issues'].append("元数据字段数量不足")
            report['recommendations'].append("检查metadata提取逻辑")

        # 检查3: 图片文档质量
        if image_info and image_info['total_image_docs'] > 0:
            enhanced_ratio = image_info['enhanced_description_stats']['with_enhanced'] / max(1, image_info['total_image_docs'])
            if enhanced_ratio > 0.8:
                print("✅ 图片增强描述覆盖率良好")
                report['overall_score'] += 20
            elif enhanced_ratio > 0.5:
                print("⚠️  图片增强描述覆盖率一般")
                report['overall_score'] += 15
                report['recommendations'].append("提升图片增强描述覆盖率")
            else:
                print("❌ 图片增强描述覆盖率不足")
                report['issues'].append("图片增强描述覆盖率低")
                report['recommendations'].append("检查图片增强处理流程")
        else:
            print("⚠️  没有图片文档")
            report['recommendations'].append("检查图片处理流程")

        # 检查4: 表格文档质量
        if table_info and table_info['total_table_docs'] > 0:
            processed_ratio = table_info.get('has_processed_content', 0) / max(1, table_info['total_table_docs'])
            if processed_ratio > 0.8:
                print("✅ 表格语义化处理覆盖率良好")
                report['overall_score'] += 15
            else:
                print("❌ 表格语义化处理覆盖率不足")
                report['issues'].append("表格语义化处理覆盖率低")
                report['recommendations'].append("检查表格语义化处理流程")
        else:
            print("⚠️  没有表格文档")

        # 检查5: 向量数据质量
        if vector_info and vector_info['vector_count'] > 0:
            if 'norm_stats' in vector_info:
                norm_std = vector_info['norm_stats']['std']
                if norm_std < 1.0:
                    print("✅ 向量范数分布均匀")
                    report['overall_score'] += 20
                else:
                    print("⚠️  向量范数分布不均匀")
                    report['overall_score'] += 15
                    report['recommendations'].append("检查向量标准化处理")

            # 检查向量维度一致性
            if vector_info['vector_dimension'] == 1536:  # DashScope默认维度
                print("✅ 向量维度正确")
            else:
                print(f"⚠️  向量维度异常: {vector_info['vector_dimension']}")
                report['issues'].append(f"向量维度异常: {vector_info['vector_dimension']}")
                report['recommendations'].append("检查embedding模型配置")
        else:
            print("❌ 没有向量数据")
            report['issues'].append("没有向量数据")
            report['recommendations'].append("检查向量化流程")

        # 生成总体评价
        print("\n🏆 总体评价:")
        if report['overall_score'] >= 90:
            print("  🎉 优秀 - 数据质量非常良好")
        elif report['overall_score'] >= 70:
            print("  ✅ 良好 - 数据质量基本满足要求")
        elif report['overall_score'] >= 50:
            print("  ⚠️  一般 - 数据质量需要改进")
        else:
            print("  ❌ 较差 - 数据质量存在严重问题")

        print(f"  📊 综合得分: {report['overall_score']}/100")

        if report['issues']:
            print("\n🔧 发现的问题:")
            for issue in report['issues']:
                print(f"  • {issue}")

        if report['recommendations']:
            print("\n💡 改进建议:")
            for rec in report['recommendations']:
                print(f"  • {rec}")

        report['overall_score'] = report['overall_score']
        return report

    def _show_detailed_document_list(self, structure_info):
        """显示详细的文档列表"""
        print("\n📋 详细文档列表")
        print("=" * 80)

        # 从docstore中获取详细信息
        vector_store = self.vector_store_manager.vector_store
        if not vector_store or not hasattr(vector_store, 'docstore'):
            print("❌ 无法获取文档详细信息")
            return

        docstore = vector_store.docstore._dict

        # 按chunk_type分组显示
        from collections import defaultdict
        docs_by_type = defaultdict(list)

        for doc_id, doc in docstore.items():
            metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
            chunk_type = metadata.get('chunk_type', 'unknown')

            doc_info = {
                'doc_id': doc_id,
                'chunk_type': chunk_type,
                'document_name': metadata.get('document_name', 'N/A'),
                'page_number': metadata.get('page_number', 'N/A'),
                'content_length': len(doc.page_content) if hasattr(doc, 'page_content') else 0,
                'metadata_fields_count': len(metadata),
                'metadata_keys': list(metadata.keys())
            }
            docs_by_type[chunk_type].append(doc_info)

        for chunk_type, docs in docs_by_type.items():
            print(f"\n🔹 {chunk_type.upper()} 文档 ({len(docs)} 个):")
            print("-" * 60)

            # 显示前10个文档的详细信息
            for i, doc in enumerate(docs[:10]):
                print("2d")
                print(f"      文档名: {doc['document_name']}")
                print(f"      页码: {doc['page_number']}")
                print(f"      内容长度: {doc['content_length']}")
                print(f"      元数据字段数: {doc['metadata_fields_count']}")
                print(f"      元数据字段: {', '.join(doc['metadata_keys'][:8])}...")
                if len(doc['metadata_keys']) > 8:
                    print(f"                   ... 还有 {len(doc['metadata_keys']) - 8} 个字段")

            if len(docs) > 10:
                print(f"      ... 还有 {len(docs) - 10} 个文档")

            # 显示该类型的统计信息
            total_content_length = sum(doc['content_length'] for doc in docs)
            avg_content_length = total_content_length / len(docs) if docs else 0
            print(f"\n  📊 {chunk_type} 统计:")
            print(f"    总内容长度: {total_content_length}")
            print(f"    平均内容长度: {avg_content_length:.1f}")
            print(f"    平均元数据字段数: {sum(doc['metadata_fields_count'] for doc in docs) / len(docs):.1f}")
    
    def _save_results(self, results: Dict[str, Any], output_file: str):
        """保存诊断结果到文件"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"💾 诊断结果已保存到: {output_file}")
        except Exception as e:
            logging.error(f"保存结果失败: {e}")
            print(f"❌ 保存结果失败: {e}")

def main():
    """主函数"""
    try:
        tool = DatabaseDiagnosticTool()
        tool.run_diagnostic()
    except Exception as e:
        print(f"❌ 程序启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
