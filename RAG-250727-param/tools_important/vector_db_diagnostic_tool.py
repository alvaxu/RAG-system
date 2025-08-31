#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
程序说明：
## 1. 综合诊断工具，用于分析vector_db的结构、index、元数据及内容
## 2. 整合了多个独立诊断脚本的功能，提供统一的诊断界面
'''

import sys
import os
import json
import pickle
import logging
import numpy as np
from pathlib import Path
from collections import defaultdict

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

def load_vector_store(vector_db_path):
    """加载向量存储"""
    try:
        config = Settings.load_from_file('config.json')
        
        # 使用统一的API密钥管理模块获取API密钥
        config_key = config.dashscope_api_key
        api_key = get_dashscope_api_key(config_key)
        
        if not api_key:
            logger.warning("未找到有效的DashScope API密钥")
            return None
        
        # 初始化DashScope embeddings
        try:
            embedding_model = config.text_embedding_model
        except Exception as e:
            print(f"⚠️ 无法加载配置，使用默认embedding模型: {e}")
            embedding_model = 'text-embedding-v1'
        
        embeddings = DashScopeEmbeddings(dashscope_api_key=api_key, model=embedding_model)
        vector_store = FAISS.load_local(vector_db_path, embeddings, allow_dangerous_deserialization=True)
        logger.info(f"向量存储加载成功，包含 {len(vector_store.docstore._dict)} 个文档")
        return vector_store
    except Exception as e:
        logger.error(f"加载向量存储失败: {e}")
        return None

def check_vector_db_files(vector_db_path):
    """检查vector_db中的文件"""
    print(f"📁 检查目录: {vector_db_path}")
    print(f"目录存在: {os.path.exists(vector_db_path)}")
    
    if not os.path.exists(vector_db_path):
        return None
    
    vector_db_path = Path(vector_db_path)
    files = list(vector_db_path.glob('*'))
    print(f"文件数量: {len(files)}")
    file_info = []
    
    for file_path in files:
        info = {
            'name': file_path.name,
            'size': file_path.stat().st_size
        }
        print(f"\n📄 文件: {file_path.name}")
        print(f"  大小: {file_path.stat().st_size} bytes")
        
        if file_path.suffix == '.pkl':
            try:
                with open(file_path, 'rb') as f:
                    data = pickle.load(f)
                
                info['type'] = str(type(data))
                info['length'] = len(data) if hasattr(data, '__len__') else 'No length'
                print(f"  类型: {type(data)}")
                print(f"  长度: {len(data) if hasattr(data, '__len__') else 'No length'}")
                
                if hasattr(data, '__len__') and len(data) > 0:
                    if isinstance(data, list):
                        info['first_element_type'] = str(type(data[0]))
                        print(f"  第一个元素类型: {type(data[0])}")
                        if isinstance(data[0], dict):
                            info['first_element_keys'] = list(data[0].keys())
                            print(f"  第一个元素键: {list(data[0].keys())}")
                    elif isinstance(data, dict):
                        info['keys'] = list(data.keys())
                        print(f"  键: {list(data.keys())}")
                            
            except Exception as e:
                info['error'] = str(e)
                print(f"  读取失败: {e}")
        
        elif file_path.suffix == '.faiss':
            info['type'] = 'FAISS索引文件'
            print(f"  FAISS索引文件")
        
        file_info.append(info)
    
    return file_info

def check_index_structure(vector_db_path):
    """检查index.pkl的详细结构"""
    index_path = Path(vector_db_path) / 'index.pkl'
    index_info = {
        'path': str(index_path),
        'exists': index_path.exists()
    }
    
    print(f"\n📊 index.pkl 结构分析")
    print(f"文件路径: {index_path}")
    print(f"文件存在: {index_path.exists()}")
    
    if not index_path.exists():
        print(f"❌ 索引文件不存在: {index_path}")
        return index_info
    
    try:
        with open(index_path, 'rb') as f:
            index_data = pickle.load(f)
        
        index_info['type'] = str(type(index_data))
        index_info['length'] = len(index_data)
        print(f"数据类型: {type(index_data)}")
        print(f"数据长度: {len(index_data)}")
        print()
        
        index_info['elements'] = []
        for i, item in enumerate(index_data):
            element_info = {
                'index': i+1,
                'type': str(type(item)),
                'length': len(item) if hasattr(item, '__len__') else 'No length'
            }
            print(f"📋 第{i+1}个元素:")
            print(f"  类型: {type(item)}")
            print(f"  长度: {len(item) if hasattr(item, '__len__') else 'No length'}")
            
            if isinstance(item, list):
                element_info['is_list'] = True
                element_info['list_length'] = len(item)
                print(f"  列表元素数量: {len(item)}")
                if len(item) > 0:
                    element_info['first_element_type'] = str(type(item[0]))
                    print(f"  第一个元素类型: {type(item[0])}")
                    if isinstance(item[0], dict):
                        element_info['first_element_keys'] = list(item[0].keys())
                        print(f"  第一个元素键: {list(item[0].keys())}")
            
            elif isinstance(item, dict):
                element_info['is_dict'] = True
                element_info['keys'] = list(item.keys())
                print(f"  字典键: {list(item.keys())}")
            
            index_info['elements'].append(element_info)
            print()
        
        # 检查是否包含元数据
        print("🔍 查找元数据:")
        index_info['metadata'] = []
        for i, item in enumerate(index_data):
            if isinstance(item, list) and len(item) > 0:
                # 检查第一个元素是否有document_name字段
                if isinstance(item[0], dict) and 'document_name' in item[0]:
                    metadata_info = {
                        'element_index': i+1,
                        'doc_count': len(item)
                    }
                    print(f"  第{i+1}个元素包含元数据，文档数量: {len(item)}")
                    # 统计chunk_type
                    chunk_types = {}
                    for doc in item:
                        if isinstance(doc, dict):
                            chunk_type = doc.get('chunk_type', 'unknown')
                            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
                    metadata_info['chunk_types'] = chunk_types
                    print(f"  Chunk类型分布: {chunk_types}")
                    
                    # 显示一些示例
                    print(f"  示例文档:")
                    metadata_info['sample_docs'] = []
                    for j, doc in enumerate(item[:2]):
                        if isinstance(doc, dict):
                            doc_info = {
                                'index': j+1,
                                'chunk_type': doc.get('chunk_type', 'N/A'),
                                'document_name': doc.get('document_name', 'N/A'),
                                'page_number': doc.get('page_number', 'N/A')
                            }
                            print(f"    [{j+1}] {doc.get('chunk_type', 'N/A')}: {doc.get('document_name', 'N/A')} (p.{doc.get('page_number', 'N/A')})")
                            metadata_info['sample_docs'].append(doc_info)
                    index_info['metadata'].append(metadata_info)
                    break
        
        return index_info
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        index_info['error'] = str(e)
        return index_info

def analyze_metadata_structure(vector_db_path):
    """分析元数据结构"""
    metadata_path = Path(vector_db_path) / 'metadata.pkl'
    metadata_info = {
        'path': str(metadata_path),
        'exists': metadata_path.exists()
    }
    
    print(f"\n📋 元数据结构分析")
    print(f"文件路径: {metadata_path}")
    print(f"文件存在: {metadata_path.exists()}")
    
    if not metadata_path.exists():
        print(f"❌ 元数据文件不存在: {metadata_path}")
        return metadata_info
    
    try:
        with open(metadata_path, 'rb') as f:
            metadata = pickle.load(f)
        
        metadata_info['type'] = str(type(metadata))
        metadata_info['length'] = len(metadata)
        print(f"数据类型: {type(metadata)}")
        print(f"数据长度: {len(metadata)}")
        print()
        
        # 分析字段结构
        field_types = defaultdict(set)
        field_examples = defaultdict(list)
        chunk_type_fields = defaultdict(set)
        
        for i, item in enumerate(metadata):
            if isinstance(item, dict):
                chunk_type = item.get('chunk_type', 'unknown')
                
                for field, value in item.items():
                    field_types[field].add(type(value).__name__)
                    chunk_type_fields[chunk_type].add(field)
                    
                    # 保存前3个示例
                    if len(field_examples[field]) < 3:
                        field_examples[field].append({
                            'chunk_type': chunk_type,
                            'value': str(value)[:100] + '...' if len(str(value)) > 100 else str(value)
                        })
        
        metadata_info['field_types'] = {k: list(v) for k, v in field_types.items()}
        metadata_info['chunk_type_fields'] = {k: list(v) for k, v in chunk_type_fields.items()}
        metadata_info['field_examples'] = {k: v for k, v in field_examples.items()}
        
        print("🔍 字段类型分析:")
        for field, types in sorted(field_types.items()):
            print(f"  {field}: {', '.join(sorted(types))}")
        
        print("\n📋 按chunk_type分组的字段:")
        for chunk_type, fields in sorted(chunk_type_fields.items()):
            print(f"  {chunk_type}: {', '.join(sorted(fields))}")
        
        print("\n📝 字段示例:")
        for field, examples in sorted(field_examples.items()):
            print(f"  {field}:")
            for example in examples:
                print(f"    [{example['chunk_type']}] {example['value']}")
        
        # 分析特定字段
        print("\n🎯 关键字段分析:")
        key_fields = ['document_name', 'page_number', 'chunk_type', 'source', 'title']
        metadata_info['key_fields'] = []
        for field in key_fields:
            if field in field_types:
                values = [item.get(field, 'N/A') for item in metadata if isinstance(item, dict)]
                unique_values = set(values)
                field_info = {
                    'field': field,
                    'unique_count': len(unique_values)
                }
                print(f"  {field}: {len(unique_values)} 个唯一值")
                if len(unique_values) <= 5:
                    field_info['values'] = list(unique_values)
                    print(f"    值: {list(unique_values)}")
                else:
                    field_info['sample_values'] = list(unique_values)[:5]
                    print(f"    前5个值: {list(unique_values)[:5]}")
                metadata_info['key_fields'].append(field_info)
        
        return metadata_info
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        metadata_info['error'] = str(e)
        return metadata_info

def check_faiss_structure(vector_db_path):
    """检查FAISS索引的实际结构"""
    faiss_path = Path(vector_db_path) / 'index.faiss'
    faiss_info = {
        'path': str(faiss_path),
        'exists': faiss_path.exists()
    }
    
    print(f"\n🔍 检查FAISS索引结构:")
    print("=" * 60)
    
    if not faiss_path.exists():
        print(f"❌ FAISS文件不存在: {faiss_path}")
        return faiss_info
    
    try:
        # 检查FAISS文件大小
        faiss_size = faiss_path.stat().st_size
        faiss_info['size'] = faiss_size
        print(f"📏 FAISS文件大小: {faiss_size} bytes")
        
        # 尝试加载FAISS索引
        try:
            import faiss
            index = faiss.read_index(str(faiss_path))
            faiss_info['type'] = str(type(index))
            faiss_info['dimension'] = index.d
            faiss_info['vector_count'] = index.ntotal
            print(f"🔢 FAISS索引信息:")
            print(f"  向量维度: {index.d}")
            print(f"  向量数量: {index.ntotal}")
            print(f"  索引类型: {type(index)}")
            
            # 检查是否有向量数据
            if hasattr(index, 'get_xb'):
                try:
                    vectors = index.get_xb()
                    faiss_info['vectors_type'] = str(type(vectors))
                    print(f"  向量数据类型: {type(vectors)}")
                    if hasattr(vectors, 'shape'):
                        faiss_info['vectors_shape'] = vectors.shape
                        print(f"  向量数据形状: {vectors.shape}")
                    
                    # 检查前几个向量
                    if vectors.shape[0] > 0:
                        faiss_info['first_vector_sample'] = vectors[0][:5].tolist()
                        faiss_info['norm_range'] = {
                            'min': float(np.linalg.norm(vectors, axis=1).min()),
                            'max': float(np.linalg.norm(vectors, axis=1).max())
                        }
                        print(f"  第一个向量: {vectors[0][:5]}... (前5维)")
                        print(f"  向量范数范围: {np.linalg.norm(vectors, axis=1).min():.4f} - {np.linalg.norm(vectors, axis=1).max():.4f}")
                except Exception as e:
                    faiss_info['vectors_error'] = str(e)
                    print(f"  无法获取向量数据: {e}")
            
        except ImportError:
            faiss_info['error'] = "无法导入faiss库"
            print("❌ 无法导入faiss库")
        except Exception as e:
            faiss_info['error'] = str(e)
            print(f"❌ 加载FAISS索引失败: {e}")
        
        return faiss_info
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        faiss_info['error'] = str(e)
        return faiss_info

def analyze_database_structure(vector_store):
    """分析数据库结构"""
    print("\n📊 向量数据库结构分析")
    print("=" * 60)

    if not vector_store or not hasattr(vector_store, 'docstore') or not hasattr(vector_store.docstore, '_dict'):
        print("❌ 向量存储结构异常")
        return None

    docstore = vector_store.docstore._dict
    total_docs = len(docstore)
    print(f"📚 总文档数: {total_docs}")

    if total_docs == 0:
        print("❌ 数据库中没有文档")
        return None

    # 分析文档类型分布
    chunk_types = {}
    document_names = set()
    all_fields = set()
    detailed_docs = []

    # 收集所有字段和统计信息
    for doc_id, doc in docstore.items():
        metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}

        # 统计分块类型
        chunk_type = metadata.get('chunk_type', 'unknown')
        if chunk_type not in chunk_types:
            chunk_types[chunk_type] = 0
        chunk_types[chunk_type] += 1

        # 统计文档名称
        doc_name = metadata.get('document_name', 'unknown')
        document_names.add(doc_name)

        # 收集所有字段
        all_fields.update(metadata.keys())

        # 收集详细文档信息
        doc_info = {
            'doc_id': doc_id,
            'chunk_type': chunk_type,
            'document_name': doc_name,
            'page_number': metadata.get('page_number', 'N/A'),
            'content_length': len(doc.page_content) if hasattr(doc, 'page_content') else 0,
            'metadata_fields_count': len(metadata),
            'metadata_keys': list(metadata.keys())
        }
        detailed_docs.append(doc_info)

    print(f"\n📊 分块类型分布:")
    for chunk_type, count in chunk_types.items():
        print(f"  {chunk_type}: {count}")

    print(f"\n📚 文档统计:")
    print(f"  总文档数: {total_docs}")
    print(f"  唯一文档名: {len(document_names)}")
    print(f"  文档名称: {sorted(list(document_names))[:5]}...")
    if len(document_names) > 5:
        print(f"      ... 还有 {len(document_names) - 5} 个文档")

    print(f"\n📋 字段统计:")
    print(f"  总字段数: {len(all_fields)}")
    print(f"  所有字段: {sorted(list(all_fields))}")

    # 显示详细文档列表（可选）
    show_detailed = input("\n是否显示详细的文档列表? (y/n): ").strip().lower()
    if show_detailed == 'y':
        show_detailed_document_list(detailed_docs)

    return {
        'total_docs': total_docs,
        'chunk_types': chunk_types,
        'document_names': list(document_names),
        'all_fields': list(all_fields),
        'detailed_docs': detailed_docs
    }

def show_detailed_document_list(detailed_docs):
    """显示详细的文档列表"""
    print("
📋 详细文档列表"    print("=" * 80)

    # 按chunk_type分组显示
    from collections import defaultdict
    docs_by_type = defaultdict(list)

    for doc in detailed_docs:
        docs_by_type[doc['chunk_type']].append(doc)

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

def check_image_docs(vector_store):
    """检查图片文档的存储结构和enhanced_description字段"""
    print(f"\n🔍 检查图片文档")
    print("=" * 60)
    
    if not vector_store or not hasattr(vector_store, 'docstore') or not hasattr(vector_store.docstore, '_dict'):
        print("❌ 向量存储结构异常")
        return None
    
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
    
    print(f"📷 找到 {len(image_docs)} 个图片文档")
    
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
    print(f"📈 覆盖率: {enhanced_count/(enhanced_count+empty_count)*100:.1f}%" if (enhanced_count+empty_count) > 0 else "📈 覆盖率: N/A")
    
    # 显示前几个图片文档的详细信息
    for i, (doc_id, doc) in enumerate(image_docs[:3]):
        sample_info = {
            'index': i+1,
            'doc_id': doc_id,
            'document_name': doc.metadata.get('document_name', 'N/A'),
            'page_number': doc.metadata.get('page_number', 'N/A'),
            'image_id': doc.metadata.get('image_id', 'N/A'),
            'image_type': doc.metadata.get('image_type', 'N/A'),
            'img_caption': doc.metadata.get('img_caption', 'N/A'),
            'enhanced_description': doc.metadata.get('enhanced_description', '')[:100] + '...' if len(doc.metadata.get('enhanced_description', '')) > 100 else doc.metadata.get('enhanced_description', ''),
            'page_content_length': len(doc.page_content) if hasattr(doc, 'page_content') else 'N/A'
        }
        image_info['samples'].append(sample_info)
        
        print(f"\n📷 图片文档 {i+1}:")
        print(f"  ID: {doc_id}")
        print(f"  文档名: {doc.metadata.get('document_name', 'N/A')}")
        print(f"  页码: {doc.metadata.get('page_number', 'N/A')}")
        print(f"  图片ID: {doc.metadata.get('image_id', 'N/A')}")
        print(f"  图片类型: {doc.metadata.get('image_type', 'N/A')}")
        print(f"  图片标题: {doc.metadata.get('img_caption', 'N/A')}")
        print(f"  增强描述: {doc.metadata.get('enhanced_description', '')[:100] + '...' if len(doc.metadata.get('enhanced_description', '')) > 100 else doc.metadata.get('enhanced_description', '')}")
        print(f"  page_content长度: {len(doc.page_content) if hasattr(doc, 'page_content') else 'N/A'}")
        
        # 检查是否有向量相关的属性
        vector_attrs = []
        for attr in dir(doc):
            if 'vector' in attr.lower() or 'embedding' in attr.lower():
                vector_attrs.append(attr)
        
        if vector_attrs:
            print(f"  向量相关属性: {vector_attrs}")
        else:
            print("  向量相关属性: 无")
        
        # 检查metadata中的semantic_features
        if hasattr(doc, 'metadata') and 'semantic_features' in doc.metadata:
            semantic = doc.metadata['semantic_features']
            print(f"  semantic_features: {semantic}")
        else:
            print("  semantic_features: 无")
    
    return image_info

def analyze_table_docs(vector_store):
    """分析表格文档的内容和元数据"""
    print(f"\n🔍 分析表格文档")
    print("=" * 60)
    
    if not vector_store or not hasattr(vector_store, 'docstore') or not hasattr(vector_store.docstore, '_dict'):
        print("❌ 向量存储结构异常")
        return None
    
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
        'content_lengths': [],
        'has_columns': 0,
        'has_table_type': 0,
        'has_html_content': 0,
        'has_processed_content': 0,
        'samples': []
    }
    
    print(f"📊 找到 {len(table_docs)} 个表格文档")
    
    # 分析前几个表格文档的详细内容
    for i, (doc_id, doc) in enumerate(table_docs[:3]):
        sample_info = {
            'index': i+1,
            'doc_id': doc_id,
            'document_name': doc.metadata.get('document_name', 'N/A'),
            'page_number': doc.metadata.get('page_number', 'N/A'),
            'table_id': doc.metadata.get('table_id', 'N/A'),
            'table_type': doc.metadata.get('table_type', 'N/A'),
            'content_preview': doc.page_content[:200] + '...' if hasattr(doc, 'page_content') and len(doc.page_content) > 200 else (doc.page_content if hasattr(doc, 'page_content') else 'N/A'),
            'metadata': doc.metadata
        }
        table_info['samples'].append(sample_info)
        
        print(f"\n{'='*50}")
        print(f"📄 表格文档 {i+1}")
        print(f"{'='*50}")
        print(f"文档ID: {doc_id}")
        print(f"文档名: {doc.metadata.get('document_name', 'N/A')}")
        print(f"页码: {doc.metadata.get('page_number', 'N/A')}")
        print(f"表格ID: {doc.metadata.get('table_id', 'N/A')}")
        print(f"表格类型: {doc.metadata.get('table_type', 'N/A')}")
        
        # 分析元数据 - 显示所有字段的值
        print(f"\n📋 元数据分析:")
        print(f"  元数据字段: {list(doc.metadata.keys())}")
        table_info['metadata_fields'].update(doc.metadata.keys())
        
        # 显示每个元数据字段的详细值
        print(f"\n🔍 详细元数据字段值:")
        for field, value in doc.metadata.items():
            if isinstance(value, str) and len(value) > 100:
                print(f"  {field}: {value[:100]}... (长度: {len(value)})")
            elif isinstance(value, list):
                if len(value) > 5:
                    print(f"  {field}: {value[:5]}... (共{len(value)}项)")
                else:
                    print(f"  {field}: {value}")
            else:
                print(f"  {field}: {value}")
        
        # 统计特定字段
        if doc.metadata.get('table_type'):
            table_info['table_types'][doc.metadata['table_type']] += 1
            table_info['has_table_type'] += 1
        if doc.metadata.get('document_name'):
            table_info['document_names'].add(doc.metadata['document_name'])
        headers = doc.metadata.get('table_headers')
        if isinstance(headers, list) and len(headers) > 0:
            table_info['has_columns'] += 1
        
        # 分析内容 - 优先检查元数据中的HTML内容，然后检查doc.page_content属性
        print(f"\n📝 内容分析:")
        
        # 优先检查元数据中的page_content字段（HTML内容）
        if 'page_content' in doc.metadata and doc.metadata['page_content']:
            html_content = doc.metadata['page_content']
            print(f"  HTML内容长度: {len(html_content)}")
            table_info['content_lengths'].append(len(html_content))
            
            # 检查是否包含HTML内容
            if '<table' in str(html_content).lower() or '<tr' in str(html_content).lower() or '<td' in str(html_content).lower():
                print("  HTML内容类型: 包含HTML表格内容")
                table_info['has_html_content'] += 1  # 统计HTML内容数量
                # 显示HTML内容预览
                html_preview = str(html_content)[:200] + "..." if len(str(html_content)) > 200 else str(html_content)
                print(f"  HTML内容预览: {html_preview}")
            else:
                print("  HTML内容类型: 不包含明显的HTML表格内容")
        
        # 检查doc.page_content属性（通常是语义化内容）
        if hasattr(doc, 'page_content') and doc.page_content:
            semantic_content = doc.page_content
            print(f"  语义化内容长度: {len(semantic_content)}")
            
            # 检查语义化内容是否包含HTML标签
            if '<table' in semantic_content.lower() or '<tr' in semantic_content.lower() or '<td' in semantic_content.lower():
                print("  语义化内容类型: 包含HTML表格内容")
            else:
                print("  语义化内容类型: 不包含明显的HTML表格内容")
            
            # 显示语义化内容预览
            semantic_preview = semantic_content[:200] + "..." if len(semantic_content) > 200 else semantic_content
            print(f"  语义化内容预览: {semantic_preview}")
        else:
            print("  ❌ 没有语义化内容")
        
        # 检查语义化内容
        has_semantic_content = 0
        key = 'processed_table_content'
        if key in doc.metadata and doc.metadata[key] is not None and len(str(doc.metadata[key])) > 0:
            has_semantic_content += 1
            print(f"  语义化内容: 存在 ({key})")
            print(f"  语义化内容预览: {doc.metadata[key][:100] + '...' if len(doc.metadata[key]) > 100 else doc.metadata[key]}")
            # 显示完整的processed_table_content内容（用于embedding的文本）
            print(f"  🔍 完整内容（用于embedding）:")
            print(f"    {doc.metadata[key]}")
        else:
            print(f"  语义化内容: 不存在")
            # 调试：记录缺失的文档详情
            table_id = doc.metadata.get('table_id', 'Unknown')
            page_num = doc.metadata.get('page_number', 'Unknown')
            processed_content = doc.metadata.get('processed_table_content')
            print(f"    ⚠️  详细信息: {table_id} (页码: {page_num})")
            print(f"    processed_table_content值: {repr(processed_content)}")
        table_info['has_processed_content'] += has_semantic_content
    
    # 分析剩余文档的元数据
    if len(table_docs) > 3:
        print(f"\n🔍 分析剩余 {len(table_docs) - 3} 个文档的元数据...")
        for i, (doc_id, doc) in enumerate(table_docs[3:]):
            if hasattr(doc, 'metadata') and doc.metadata:
                table_info['metadata_fields'].update(doc.metadata.keys())
                
                # 统计特定字段
                if doc.metadata.get('table_type'):
                    table_info['table_types'][doc.metadata['table_type']] += 1
                    table_info['has_table_type'] += 1
                if doc.metadata.get('document_name'):
                    table_info['document_names'].add(doc.metadata['document_name'])
                headers = doc.metadata.get('table_headers')
                if isinstance(headers, list) and len(headers) > 0:
                    table_info['has_columns'] += 1
                # 检查HTML内容 - 优先检查元数据中的page_content字段，然后检查doc.page_content属性
                has_html_content = False
                if 'page_content' in doc.metadata and doc.metadata['page_content']:
                    # 检查元数据中的page_content字段
                    if any(tag in str(doc.metadata['page_content']).lower() for tag in ['<table', '<tr', '<td']):
                        has_html_content = True
                elif hasattr(doc, 'page_content') and doc.page_content:
                    # 检查doc.page_content属性
                    if any(tag in doc.page_content.lower() for tag in ['<table', '<tr', '<td']):
                        has_html_content = True
                
                if has_html_content:
                    table_info['has_html_content'] += 1
                
                # 检查语义化内容 - 只统计processed_table_content字段
                key = 'processed_table_content'
                processed_content = doc.metadata.get(key)
                if key in doc.metadata and doc.metadata[key] is not None and len(str(doc.metadata[key])) > 0:
                    table_info['has_processed_content'] += 1
                else:
                    # 调试：记录缺失的文档
                    table_id = doc.metadata.get('table_id', 'Unknown')
                    page_num = doc.metadata.get('page_number', 'Unknown')
                    print(f"    ⚠️  缺少processed_table_content: {table_id} (页码: {page_num})")
                    print(f"        processed_table_content值: {repr(processed_content)}")
        
        print(f"  完成剩余文档分析")
    
    # 显示统计信息
    print(f"\n📊 表格文档统计信息")
    print("=" * 60)
    print(f"总文档数: {table_info['total_table_docs']}")
    print(f"有表格类型的文档: {table_info['has_table_type']}")
    print(f"有列信息的文档: {table_info['has_columns']}")
    print(f"包含HTML内容的文档: {table_info['has_html_content']}")
    print(f"包含语义化处理内容的文档: {table_info['has_processed_content']}")
    print(f"\n元数据字段总数: {len(table_info['metadata_fields'])}")
    print(f"元数据字段: {sorted(list(table_info['metadata_fields']))}")
    
    if table_info['table_types']:
        print(f"\n表格类型分布:")
        for table_type, count in sorted(table_info['table_types'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {table_type}: {count}")
    
    if table_info['document_names']:
        print(f"\n文档名称 (共{len(table_info['document_names'])}个):")
        for doc_name in sorted(list(table_info['document_names']))[:5]:
            print(f"  {doc_name}")
        if len(table_info['document_names']) > 5:
            print(f"  ... 还有 {len(table_info['document_names']) - 5} 个")
    
    if table_info['content_lengths']:
        avg_length = sum(table_info['content_lengths']) / len(table_info['content_lengths'])
        print(f"\n内容长度统计:")
        print(f"  平均长度: {avg_length:.1f}")
        print(f"  最短长度: {min(table_info['content_lengths'])}")
        print(f"  最长长度: {max(table_info['content_lengths'])}")
    
    return table_info

def analyze_vector_data(vector_store):
    """分析向量数据的分布和样本"""
    print("
🔢 向量数据分析"    print("=" * 60)

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

                # 显示向量分布直方图
                try:
                    import matplotlib.pyplot as plt
                    plt.figure(figsize=(10, 6))
                    plt.hist(norms, bins=50, alpha=0.7, color='blue', edgecolor='black')
                    plt.title('向量范数分布')
                    plt.xlabel('范数值')
                    plt.ylabel('频次')
                    plt.grid(True, alpha=0.3)
                    plt.savefig('vector_norm_distribution.png', dpi=150, bbox_inches='tight')
                    plt.close()
                    print("
💾 向量范数分布图已保存为: vector_norm_distribution.png"                except ImportError:
                    print("
⚠️  matplotlib未安装，无法生成分布图"                except Exception as e:
                    print(f"
⚠️  生成分布图失败: {e}"            # 分析向量相似度
            if vector_info['vector_count'] > 1:
                analyze_vector_similarity(vectors, vector_info)

        return vector_info

    except Exception as e:
        print(f"❌ 向量数据分析失败: {e}")
        return None

def analyze_vector_similarity(vectors, vector_info):
    """分析向量相似度 - 评估向量化质量和发现潜在问题"""
    print("
🔗 向量相似度分析"    print("-" * 40)
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
                    # 用不同颜色标识相似度级别
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
            print("
📊 相似度统计:"            print(".4f"            print(".4f"            print(".4f"            print(".4f"
            # 质量评估
            print("
🔍 质量评估:"            if similarities.mean() > 0.7:
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

def generate_quality_report(vector_store, structure_info, image_info, table_info, vector_info):
    """生成数据质量检查报告"""
    print("
📋 数据质量检查报告"    print("=" * 60)

    report = {
        'overall_score': 0,
        'issues': [],
        'recommendations': []
    }

    # 检查1: 文档数量合理性
    if structure_info and structure_info['total_docs'] > 0:
        print("✅ 文档数量检查通过")
        report['overall_score'] += 20
    else:
        print("❌ 文档数量异常")
        report['issues'].append("数据库中没有文档")
        report['recommendations'].append("检查文档处理流程是否正常")

    # 检查2: 元数据完整性
    if structure_info and len(structure_info['all_fields']) > 10:
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
        processed_ratio = table_info['has_processed_content'] / max(1, table_info['total_table_docs'])
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
    print("
🏆 总体评价:"    if report['overall_score'] >= 90:
        print("  🎉 优秀 - 数据质量非常良好")
    elif report['overall_score'] >= 70:
        print("  ✅ 良好 - 数据质量基本满足要求")
    elif report['overall_score'] >= 50:
        print("  ⚠️  一般 - 数据质量需要改进")
    else:
        print("  ❌ 较差 - 数据质量存在严重问题")

    print(f"  📊 综合得分: {report['overall_score']}/100")

    if report['issues']:
        print("
🔧 发现的问题:"        for issue in report['issues']:
            print(f"  • {issue}")

    if report['recommendations']:
        print("
💡 改进建议:"        for rec in report['recommendations']:
            print(f"  • {rec}")

    report['overall_score'] = report['overall_score']
    return report

def check_memory_content():
    """检查记忆文件内容"""
    memory_info = {
        'conversation_contexts': {
            'exists': False,
            'users': []
        },
        'user_preferences': {
            'exists': False,
            'users': []
        }
    }
    
    print("\n📁 检查记忆文件内容")
    print("=" * 50)
    
    # 检查conversation_contexts.json
    try:
        memory_db_path = Path('central/memory_db')
        conv_path = memory_db_path / 'conversation_contexts.json'
        if conv_path.exists():
            with open(conv_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            memory_info['conversation_contexts']['exists'] = True
            print("📝 conversation_contexts.json:")
            for user_id, context in data.items():
                history = context.get('conversation_history', [])
                user_info = {
                    'user_id': user_id,
                    'history_count': len(history)
                }
                print(f"  {user_id}: {len(history)} 条记录")
                if user_id == 'test_user':
                    print("    最后3个问题:")
                    user_info['last_questions'] = []
                    for i, item in enumerate(history[-3:]):
                        question = item['question']
                        print(f"      {i+1}. {question}")
                        user_info['last_questions'].append(question)
                    last_question = context.get('last_question', 'N/A')
                    print(f"    最新问题: {last_question}")
                    user_info['last_question'] = last_question
                memory_info['conversation_contexts']['users'].append(user_info)
        else:
            print(f"❌ conversation_contexts.json文件不存在: {conv_path}")
    except Exception as e:
        print(f"❌ 读取conversation_contexts.json失败: {e}")
        memory_info['conversation_contexts']['error'] = str(e)
    
    # 检查user_preferences.json
    try:
        pref_path = memory_db_path / 'user_preferences.json'
        if pref_path.exists():
            with open(pref_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            memory_info['user_preferences']['exists'] = True
            print("\n📊 user_preferences.json:")
            for user_id, prefs in data.items():
                interest_areas = prefs.get('interest_areas', [])
                frequent_queries = prefs.get('frequent_queries', [])
                user_info = {
                    'user_id': user_id,
                    'interest_areas_count': len(interest_areas),
                    'frequent_queries_count': len(frequent_queries)
                }
                print(f"  {user_id}: {len(interest_areas)} 个兴趣领域, {len(frequent_queries)} 个常用查询")
                memory_info['user_preferences']['users'].append(user_info)
        else:
            print(f"❌ user_preferences.json文件不存在: {pref_path}")
    except Exception as e:
        print(f"❌ 读取user_preferences.json失败: {e}")
        memory_info['user_preferences']['error'] = str(e)
    
    return memory_info

def main():
    """主函数"""
    print("🔍 向量数据库综合诊断工具")
    print("=" * 60)
    
    try:
        config = Settings.load_from_file('config.json')
        vector_db_path = config.vector_db_dir
        
        print(f"📁 向量数据库路径: {vector_db_path}")
        
        # 检查路径是否存在，如果不存在尝试其他可能的路径
        if not os.path.exists(vector_db_path):
            possible_paths = [
                "./central/vector_db",
                "./vector_db",
                "./central/vector_db_test",
                "./vector_db_test"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    vector_db_path = path
                    print(f"✅ 找到向量数据库路径: {vector_db_path}")
                    break
            else:
                print(f"❌ 向量数据库路径不存在，尝试过的路径:")
                for path in possible_paths:
                    print(f"   - {path}")
                return
        
        # 检查文件结构
        file_info = check_vector_db_files(vector_db_path)
        if not file_info:
            print("❌ 无法检查文件结构，目录不存在")
            return
        
        # 检查索引结构
        index_info = check_index_structure(vector_db_path)
        
        # 分析元数据结构
        metadata_info = analyze_metadata_structure(vector_db_path)
        
        # 检查FAISS索引结构
        faiss_info = check_faiss_structure(vector_db_path)
        
        # 加载向量存储
        vector_store = load_vector_store(vector_db_path)
        if not vector_store:
            print("❌ 无法加载向量存储")
            return
        
        # 分析数据库结构
        structure_info = analyze_database_structure(vector_store)
        
        # 检查图片文档
        image_info = check_image_docs(vector_store)
        
        # 分析表格文档
        table_info = analyze_table_docs(vector_store)

        # 分析向量数据
        vector_info = analyze_vector_data(vector_store)

        # 生成数据质量检查报告
        quality_report = generate_quality_report(vector_store, structure_info, image_info, table_info, vector_info)

        # 检查记忆文件内容
        memory_info = check_memory_content()
        
        # TODO: 整合其他诊断功能
        print("📊 开始综合诊断...")
        
        # 保存分析结果的选择
        save_choice = input("\n是否保存分析结果到文件? (y/n): ").strip().lower()
        if save_choice == 'y':
            output_file = "vector_db_diagnostic_results.json"
            results = {
                'file_info': file_info,
                'index_info': index_info,
                'metadata_info': metadata_info,
                'faiss_info': faiss_info,
                'structure_info': structure_info,
                'image_info': image_info,
                'table_info': table_info,
                'vector_info': vector_info,
                'quality_report': quality_report,
                'memory_info': memory_info
            }
            
            # 转换结果中的set类型为list类型以确保JSON可序列化
            def convert_sets_to_lists(obj):
                if isinstance(obj, set):
                    return list(obj)
                elif isinstance(obj, dict):
                    return {k: convert_sets_to_lists(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_sets_to_lists(item) for item in obj]
                elif isinstance(obj, tuple):
                    return tuple(convert_sets_to_lists(item) for item in obj)
                else:
                    return obj
            
            serializable_results = convert_sets_to_lists(results)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_results, f, ensure_ascii=False, indent=2)
            print(f"💾 分析结果已保存到: {output_file}")
        
        print("\n✅ 数据库综合诊断完成！")
        
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        print(f"❌ 程序执行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
