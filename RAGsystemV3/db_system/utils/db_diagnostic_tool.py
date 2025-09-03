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
            
            # 加载配置
            if not self.config_manager.load_config():
                logging.warning("配置加载失败，使用默认值")
                # 如果配置加载失败，尝试使用默认路径
                if not self.config_manager.is_loaded:
                    logging.info("尝试使用默认配置路径重新加载...")
                    default_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config", "v3_config.json")
                    if os.path.exists(default_config_path):
                        self.config_manager = ConfigManager(default_config_path)
                        if not self.config_manager.load_config():
                            logging.error("默认配置路径加载也失败")
            
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
            
            # 8.1 按vector_type分析向量数据
            print("🔢 按向量类型分析向量数据...")
            vector_type_info = self._analyze_vector_data_by_type(self.vector_store_manager.vector_store)

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
                'vector_type_info': vector_type_info,
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
            
            # 获取向量数据库路径 - 修复配置加载问题
            vector_db_path = None
            if self.config_manager.is_loaded:
                vector_db_path = self.config_manager.get_path('vector_db_dir')
            else:
                # 如果配置未加载，尝试重新加载
                logging.info("配置未加载，尝试重新加载...")
                if self.config_manager.load_config():
                    vector_db_path = self.config_manager.get_path('vector_db_dir')
                else:
                    # 使用默认路径
                    vector_db_path = "./central/vector_db"
                    logging.warning("配置加载失败，使用默认路径")
            
            basic_info = {
                'total_docs': total_docs,  # 修复字段名不一致问题
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
            vector_types = defaultdict(int)
            document_names = set()
            all_fields = set()
            
            for doc_id, doc in docstore.items():
                metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
                
                # 统计分块类型
                chunk_type = metadata.get('chunk_type', 'unknown')
                chunk_types[chunk_type] += 1
                
                # 统计向量类型
                vector_type = metadata.get('vector_type', 'unknown')
                vector_types[vector_type] += 1
                
                # 直接获取文档名称
                doc_name = metadata.get('document_name', 'unknown')
                document_names.add(doc_name)
                
                # 收集所有字段
                all_fields.update(metadata.keys())
            
            structure_info = {
                'chunk_type_distribution': dict(chunk_types),
                'vector_type_distribution': dict(vector_types),
                'unique_document_names': list(document_names),
                'total_unique_documents': len(document_names),
                'all_metadata_fields': list(all_fields),
                'total_metadata_fields': len(all_fields)
            }
            
            print(f"\n📊 分块类型分布:")
            for chunk_type, count in sorted(chunk_types.items()):
                print(f"   {chunk_type}: {count}")
            
            print(f"\n🔢 向量类型分布:")
            for vector_type, count in sorted(vector_types.items()):
                print(f"   {vector_type}: {count}")
            
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
                'dual_vector_storage_stats': {
                    'visual_embedding_count': 0,
                    'description_embedding_count': 0,
                    'dual_storage_count': 0
                },
                'samples': []
            }
            
            print(f"\n📷 找到 {len(image_docs)} 个图片文档")
            
            # 分析enhanced_description字段
            enhanced_count = 0
            empty_count = 0
            
            # 分析双重向量存储
            visual_embedding_count = 0
            description_embedding_count = 0
            dual_storage_count = 0
            
            # 按image_id分组统计双重向量存储
            image_id_groups = defaultdict(list)
            for doc_id, doc in image_docs:
                image_id = doc.metadata.get('image_id', 'unknown')
                vector_type = doc.metadata.get('vector_type', 'unknown')
                image_id_groups[image_id].append(vector_type)
            
            for image_id, vector_types in image_id_groups.items():
                if 'visual_embedding' in vector_types:
                    visual_embedding_count += 1
                if 'description_embedding' in vector_types:
                    description_embedding_count += 1
                if 'visual_embedding' in vector_types and 'description_embedding' in vector_types:
                    dual_storage_count += 1
            
            for doc_id, doc in image_docs:
                # 直接从metadata获取enhanced_description
                enhanced_desc = doc.metadata.get('enhanced_description', '')
                if enhanced_desc:
                    enhanced_count += 1
                else:
                    empty_count += 1
            
            image_info['enhanced_description_stats']['with_enhanced'] = enhanced_count
            image_info['enhanced_description_stats']['without_enhanced'] = empty_count
            image_info['dual_vector_storage_stats']['visual_embedding_count'] = visual_embedding_count
            image_info['dual_vector_storage_stats']['description_embedding_count'] = description_embedding_count
            image_info['dual_vector_storage_stats']['dual_storage_count'] = dual_storage_count
            
            print(f"✅ 有enhanced_description的图片: {enhanced_count}")
            print(f"❌ 无enhanced_description的图片: {empty_count}")
            if (enhanced_count + empty_count) > 0:
                print(f"📈 覆盖率: {enhanced_count/(enhanced_count+empty_count)*100:.1f}%")
            
            print(f"\n🔢 双重向量存储统计:")
            print(f"  visual_embedding向量: {visual_embedding_count}")
            print(f"  description_embedding向量: {description_embedding_count}")
            print(f"  双重存储的图片: {dual_storage_count}")
            if len(image_id_groups) > 0:
                print(f"📈 双重存储覆盖率: {dual_storage_count/len(image_id_groups)*100:.1f}%")
            
            # 显示前5个图片文档的详细信息
            for i, (doc_id, doc) in enumerate(image_docs[:5]):
                # 直接从metadata获取信息
                document_name = doc.metadata.get('document_name', 'N/A')
                page_number = doc.metadata.get('page_number', 'N/A')
                image_id = doc.metadata.get('image_id', 'N/A')
                vector_type = doc.metadata.get('vector_type', 'N/A')
                enhanced_description = doc.metadata.get('enhanced_description', '')
                
                sample_info = {
                    'index': i+1,
                    'doc_id': doc_id,
                    'document_name': document_name,
                    'page_number': page_number,
                    'image_id': image_id,
                    'vector_type': vector_type,
                    'enhanced_description': enhanced_description[:100] + '...' if len(enhanced_description) > 100 else enhanced_description
                }
                image_info['samples'].append(sample_info)
                
                print(f"\n📷 图片文档 {i+1}:")
                print(f"  ID: {doc_id}")
                print(f"  文档名: {document_name}")
                print(f"  页码: {page_number}")
                print(f"  图片ID: {image_id}")
                print(f"  向量类型: {vector_type}")
                print(f"  增强描述: {enhanced_description[:100] + '...' if len(enhanced_description) > 100 else enhanced_description}")
            
            if len(image_docs) > 5:
                print(f"\n... 还有 {len(image_docs) - 5} 个图片文档")
            
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
                # 直接从metadata获取信息
                document_name = doc.metadata.get('document_name', 'N/A')
                page_number = doc.metadata.get('page_number', 'N/A')
                table_id = doc.metadata.get('table_id', 'N/A')
                table_type = doc.metadata.get('table_type', 'N/A')
                
                sample_info = {
                    'index': i+1,
                    'doc_id': doc_id,
                    'document_name': document_name,
                    'page_number': page_number,
                    'table_id': table_id,
                    'table_type': table_type
                }
                table_info['samples'].append(sample_info)
                
                print(f"\n📄 表格文档 {i+1}:")
                print(f"  文档ID: {doc_id}")
                print(f"  文档名: {document_name}")
                print(f"  页码: {page_number}")
                print(f"  表格ID: {table_id}")
                print(f"  表格类型: {table_type}")
                
                # 收集元数据字段
                if hasattr(doc, 'metadata') and doc.metadata:
                    table_info['metadata_fields'].update(doc.metadata.keys())
                    
                    # 统计特定字段
                    if table_type and table_type != 'N/A':
                        table_info['table_types'][table_type] += 1
                    if document_name and document_name != 'N/A':
                        table_info['document_names'].add(document_name)
            
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
                # 直接从metadata获取信息
                document_name = doc.metadata.get('document_name', 'N/A')
                page_number = doc.metadata.get('page_number', 'N/A')
                chunk_index = doc.metadata.get('chunk_index', 'N/A')
                
                sample_info = {
                    'index': i+1,
                    'doc_id': doc_id,
                    'document_name': document_name,
                    'page_number': page_number,
                    'chunk_index': chunk_index,
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

    def _analyze_vector_data_by_type(self, vector_store) -> Dict[str, Any]:
        """按vector_type分析向量数据"""
        print("\n🔢 按向量类型分析向量数据")
        print("=" * 60)

        if not vector_store:
            print("❌ 向量存储对象无效")
            return None

        try:
            docstore = vector_store.docstore._dict
            
            # 按vector_type分组统计
            vector_type_stats = defaultdict(list)
            vector_type_counts = defaultdict(int)
            
            for doc_id, doc in docstore.items():
                metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
                vector_type = metadata.get('vector_type', 'unknown')
                vector_type_counts[vector_type] += 1
                
                # 获取对应的向量索引
                try:
                    # 这里需要根据doc_id找到对应的向量索引
                    # 由于FAISS索引和docstore的对应关系，我们需要通过其他方式获取
                    vector_type_stats[vector_type].append(doc_id)
                except:
                    pass
            
            print(f"📊 向量类型统计:")
            for vector_type, count in sorted(vector_type_counts.items()):
                print(f"  {vector_type}: {count}")
            
            # 分析每种向量类型的质量
            vector_type_info = {}
            for vector_type, doc_ids in vector_type_stats.items():
                if vector_type != 'unknown' and len(doc_ids) > 0:
                    print(f"\n🔍 {vector_type} 向量分析:")
                    print(f"  数量: {len(doc_ids)}")
                    
                    # 这里可以添加更详细的向量质量分析
                    vector_type_info[vector_type] = {
                        'count': len(doc_ids),
                        'doc_ids': doc_ids[:5]  # 只保存前5个作为示例
                    }
            
            return vector_type_info

        except Exception as e:
            print(f"❌ 按向量类型分析失败: {e}")
            return None

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
                report['overall_score'] += 15
            elif enhanced_ratio > 0.5:
                print("⚠️  图片增强描述覆盖率一般")
                report['overall_score'] += 10
                report['recommendations'].append("提升图片增强描述覆盖率")
            else:
                print("❌ 图片增强描述覆盖率不足")
                report['issues'].append("图片增强描述覆盖率低")
                report['recommendations'].append("检查图片增强处理流程")
            
            # 检查6: 双重向量存储完整性
            dual_stats = image_info.get('dual_vector_storage_stats', {})
            if dual_stats:
                dual_ratio = dual_stats.get('dual_storage_count', 0) / max(1, len(set(doc.metadata.get('image_id', '') for doc in self.vector_store_manager.vector_store.docstore._dict.values() if doc.metadata.get('chunk_type') == 'image')))
                if dual_ratio > 0.8:
                    print("✅ 双重向量存储覆盖率良好")
                    report['overall_score'] += 15
                elif dual_ratio > 0.5:
                    print("⚠️  双重向量存储覆盖率一般")
                    report['overall_score'] += 10
                    report['recommendations'].append("提升双重向量存储覆盖率")
                else:
                    print("❌ 双重向量存储覆盖率不足")
                    report['issues'].append("双重向量存储覆盖率低")
                    report['recommendations'].append("检查双重向量存储流程")
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
    
    def _show_type_overview(self, chunk_type: str):
        """显示某个类型的基本情况"""
        print(f"\n📊 {chunk_type.upper()} 类型基本情况")
        print("=" * 60)
        
        vector_store = self.vector_store_manager.vector_store
        if not vector_store or not hasattr(vector_store, 'docstore'):
            print("❌ 无法获取向量存储信息")
            return
        
        docstore = vector_store.docstore._dict
        
        # 筛选指定类型的文档
        type_docs = []
        for doc_id, doc in docstore.items():
            metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
            if metadata.get('chunk_type') == chunk_type:
                type_docs.append((doc_id, doc))
        
        if not type_docs:
            print(f"❌ 未找到 {chunk_type} 类型的文档")
            return
        
        print(f"📚 找到 {len(type_docs)} 个 {chunk_type} 文档")
        
        # 统计基本信息
        total_content_length = 0
        metadata_fields = set()
        document_names = set()
        
        for doc_id, doc in type_docs:
            if hasattr(doc, 'page_content'):
                total_content_length += len(doc.page_content)
            
            metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
            metadata_fields.update(metadata.keys())
            
            # 直接获取文档名
            doc_name = metadata.get('document_name', 'N/A')
            if doc_name != 'N/A':
                document_names.add(doc_name)
        
        print(f"\n📊 基本统计:")
        print(f"  总文档数: {len(type_docs)}")
        print(f"  总内容长度: {total_content_length}")
        print(f"  平均内容长度: {total_content_length / len(type_docs):.1f}")
        print(f"  唯一文档名: {len(document_names)}")
        print(f"  元数据字段数: {len(metadata_fields)}")
        
        if document_names:
            print(f"\n📚 文档名列表:")
            for i, name in enumerate(sorted(document_names)[:5], 1):
                print(f"  {i}. {name}")
            if len(document_names) > 5:
                print(f"  ... 还有 {len(document_names) - 5} 个文档")
        
        print(f"\n🔧 元数据字段:")
        for i, field in enumerate(sorted(metadata_fields)[:10], 1):
            print(f"  {i}. {field}")
        if len(metadata_fields) > 10:
            print(f"  ... 还有 {len(metadata_fields) - 10} 个字段")
    
    def _show_type_detailed_metadata(self, chunk_type: str):
        """显示某个类型中所有文档的详细metadata"""
        print(f"\n🔍 {chunk_type.upper()} 类型详细Metadata分析")
        print("=" * 80)
        
        vector_store = self.vector_store_manager.vector_store
        if not vector_store or not hasattr(vector_store, 'docstore'):
            print("❌ 无法获取向量存储信息")
            return
        
        docstore = vector_store.docstore._dict
        
        # 筛选指定类型的文档
        type_docs = []
        for doc_id, doc in docstore.items():
            metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
            if metadata.get('chunk_type') == chunk_type:
                type_docs.append((doc_id, doc))
        
        if not type_docs:
            print(f"❌ 未找到 {chunk_type} 类型的文档")
            return
        
        print(f"📚 找到 {len(type_docs)} 个 {chunk_type} 文档")
        print("🔍 开始分析每个文档的完整metadata...")
        
        # 分析每个文档的metadata
        for i, (doc_id, doc) in enumerate(type_docs, 1):
            print(f"\n📄 {chunk_type.upper()} 文档 {i}:")
            print("-" * 60)
            print(f"文档ID: {doc_id}")
            
            metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
            
            # 显示外层metadata
            print(f"\n🔧 外层Metadata ({len(metadata)} 个字段):")
            for key, value in sorted(metadata.items()):
                if key in ['description_embedding', 'image_embedding', 'text_embedding', 'table_embedding'] and isinstance(value, (list, tuple)):
                    # 限制embedding字段的显示长度，只显示前3个值
                    if len(value) > 3:
                        print(f"  {key}: [{value[0]}, {value[1]}, {value[2]}, ...] (共{len(value)}个元素)")
                    else:
                        print(f"  {key}: {list(value)}")
                else:
                    # 限制显示长度
                    if isinstance(value, str) and len(str(value)) > 100:
                        display_value = str(value)[:100] + "..."
                    else:
                        display_value = str(value)
                    print(f"  {key}: {display_value}")
            
            # 显示内容预览
            if hasattr(doc, 'page_content'):
                # 根据文档类型选择正确的内容字段
                if chunk_type == 'text' and metadata.get('text'):
                    # 文本文档：显示text字段内容
                    content = metadata['text']
                    if len(content) > 200:
                        content_preview = content[:200] + "..."
                    else:
                        content_preview = content
                    print(f"\n📝 文本内容预览:")
                    print(f"  {content_preview}")
                elif chunk_type == 'table' and metadata.get('table_content'):
                    # 表格文档：显示table_content字段内容
                    content = metadata['table_content']
                    if len(content) > 200:
                        content_preview = content[:200] + "..."
                    else:
                        content_preview = content
                    print(f"\n📊 表格内容预览:")
                    print(f"  {content_preview}")
                elif chunk_type == 'image' and metadata.get('enhanced_description'):
                    # 图像文档：显示enhanced_description字段内容
                    content = metadata['enhanced_description']
                    if len(content) > 200:
                        content_preview = content[:200] + "..."
                    else:
                        content_preview = content
                    print(f"\n🖼️ 图像描述预览:")
                    print(f"  {content_preview}")
                else:
                    # 其他情况：显示page_content或尝试其他字段
                    content = doc.page_content if hasattr(doc, 'page_content') else "无内容"
                    if len(content) > 200:
                        content_preview = content[:200] + "..."
                    else:
                        content_preview = content
                    print(f"\n📝 内容预览:")
                    print(f"  {content_preview}")
            
            # 询问是否继续显示下一个文档
            if i < len(type_docs):
                print(f"\n是否继续显示下一个文档? (y/n): ", end="")
                try:
                    user_input = input().strip().lower()
                    if user_input != 'y':
                        print("停止显示详细metadata")
                        break
                except KeyboardInterrupt:
                    print("\n用户中断，停止显示")
                    break
                except:
                    print("继续显示下一个文档...")
    
    def _show_interactive_menu(self):
        """显示交互式菜单"""
        print("\n🎯 数据库诊断工具 - 交互式菜单")
        print("=" * 60)
        print("请选择要执行的操作:")
        print("1. 📊 展示数据库整体情况")
        print("2. 📷 展示图片类型基本情况")
        print("3. 📊 展示表格类型基本情况")
        print("4. 📝 展示文本类型基本情况")
        print("5. 🔍 展示图片类型所有字段和值")
        print("6. 🔍 展示表格类型所有字段和值")
        print("7. 🔍 展示文本类型所有字段和值")
        print("8. 🔢 展示双重向量存储分析")
        print("9. 🔢 按vector_type分析向量数据")
        print("10. 📋 运行完整诊断")
        print("11. 🚪 退出")
        print("-" * 60)
    
    def run_interactive_mode(self):
        """运行交互式模式"""
        print("🔍 V3版本数据库诊断工具启动")
        print("=" * 60)
        
        try:
            # 加载向量数据库
            print("📚 加载向量数据库...")
            if not self.vector_store_manager.load():
                print("❌ 无法加载向量数据库")
                return
            
            print("✅ 向量数据库加载成功")
            
            while True:
                self._show_interactive_menu()
                
                try:
                    choice = input("请输入选择 (1-11): ").strip()
                    
                    if choice == '1':
                        # 展示数据库整体情况
                        print("\n📊 数据库整体情况")
                        print("=" * 60)
                        basic_info = self._get_basic_info()
                        structure_info = self._analyze_document_structure()
                        
                        print(f"📚 总文档数: {basic_info.get('total_docs', 'N/A')}")
                        print(f"📁 向量数据库路径: {basic_info.get('vector_db_path', 'N/A')}")
                        print(f"✅ 向量数据库存在: {basic_info.get('vector_db_exists', 'N/A')}")
                        
                        print(f"\n📊 分块类型分布:")
                        for chunk_type, count in structure_info.get('chunk_types', {}).items():
                            print(f"  {chunk_type}: {count}")
                        
                        print(f"\n📚 文档统计:")
                        print(f"  总文档数: {structure_info.get('total_docs', 'N/A')}")
                        print(f"  唯一文档名: {structure_info.get('unique_document_names', 'N/A')}")
                        
                        doc_names = structure_info.get('document_names', [])
                        if doc_names:
                            print(f"  具体文档名: {doc_names[:3]}")
                            if len(doc_names) > 3:
                                print(f"  ... 还有 {len(doc_names) - 3} 个文档")
                    
                    elif choice == '2':
                        # 展示图片类型基本情况
                        self._show_type_overview('image')
                    
                    elif choice == '3':
                        # 展示表格类型基本情况
                        self._show_type_overview('table')
                    
                    elif choice == '4':
                        # 展示文本类型基本情况
                        self._show_type_overview('text')
                    
                    elif choice == '5':
                        # 展示图片类型所有字段和值
                        self._show_type_detailed_metadata('image')
                    
                    elif choice == '6':
                        # 展示表格类型所有字段和值
                        self._show_type_detailed_metadata('table')
                    
                    elif choice == '7':
                        # 展示文本类型所有字段和值
                        self._show_type_detailed_metadata('text')
                    
                    elif choice == '8':
                        # 展示双重向量存储分析
                        print("\n🔢 双重向量存储分析")
                        print("=" * 60)
                        image_info = self._check_image_docs()
                        
                    elif choice == '9':
                        # 按vector_type分析向量数据
                        print("\n🔢 按向量类型分析向量数据")
                        print("=" * 60)
                        vector_type_info = self._analyze_vector_data_by_type(self.vector_store_manager.vector_store)
                        
                    elif choice == '10':
                        # 运行完整诊断
                        print("\n🚀 开始运行完整诊断...")
                        self.run_diagnostic()
                    
                    elif choice == '11':
                        # 退出
                        print("👋 感谢使用数据库诊断工具！")
                        break
                    
                    else:
                        print("❌ 无效选择，请输入 1-11 之间的数字")
                    
                    if choice != '11':
                        input("\n按回车键继续...")
                        print("\n" + "="*60)
                
                except KeyboardInterrupt:
                    print("\n\n👋 用户中断，退出程序")
                    break
                except Exception as e:
                    print(f"❌ 执行过程中出现错误: {e}")
                    input("按回车键继续...")
        
        except Exception as e:
            print(f"❌ 程序启动失败: {e}")
            import traceback
            traceback.print_exc()

    def _save_results(self, results: Dict[str, Any], output_file: str):
        """保存诊断结果到文件"""
        try:
            # 清理numpy数组和其他不可序列化的对象
            cleaned_results = self._clean_for_json(results)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(cleaned_results, f, ensure_ascii=False, indent=2)
            print(f"💾 诊断结果已保存到: {output_file}")
        except Exception as e:
            logging.error(f"保存结果失败: {e}")
            print(f"❌ 保存结果失败: {e}")
    
    def _clean_for_json(self, obj):
        """清理对象中的numpy数组和其他不可JSON序列化的对象"""
        import numpy as np
        
        if isinstance(obj, dict):
            return {key: self._clean_for_json(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._clean_for_json(item) for item in obj]
        elif isinstance(obj, np.ndarray):
            # 将numpy数组转换为列表
            return obj.tolist()
        elif isinstance(obj, (np.integer, np.floating)):
            # 将numpy数值类型转换为Python原生类型
            return obj.item()
        elif hasattr(obj, '__dict__'):
            # 对于其他对象，尝试转换为字典
            try:
                return self._clean_for_json(obj.__dict__)
            except:
                return str(obj)
        else:
            return obj

def main():
    """主函数"""
    try:
        tool = DatabaseDiagnosticTool()
        tool.run_interactive_mode()
    except Exception as e:
        print(f"❌ 程序启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
