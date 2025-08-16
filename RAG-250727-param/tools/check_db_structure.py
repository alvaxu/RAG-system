'''
程序说明：
## 1. 检查向量数据库结构的增强版脚本
## 2. 基于view_image_descriptions.py的数据库连接方法
## 3. 分析数据库中的字段和内容类型
## 4. 抽样提取不同类型文档（图片、文本、表格）的存放情况
## 5. 提供详细的统计信息和样本展示
'''

import sys
import os
import json
import logging
from pathlib import Path

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
            from config.settings import Settings
            config = Settings.load_from_file('../config.json')
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

def analyze_database_structure(vector_store):
    """分析数据库结构"""
    print("📊 向量数据库结构分析")
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
    
    print(f"\n📊 分块类型分布:")
    for chunk_type, count in chunk_types.items():
        print(f"  {chunk_type}: {count}")
    
    print(f"\n📚 文档统计:")
    print(f"  总文档数: {total_docs}")
    print(f"  唯一文档名: {len(document_names)}")
    print(f"  文档名称: {sorted(list(document_names))[:5]}...")
    
    print(f"\n📋 字段统计:")
    print(f"  总字段数: {len(all_fields)}")
    print(f"  所有字段: {sorted(list(all_fields))}")
    
    return {
        'total_docs': total_docs,
        'chunk_types': chunk_types,
        'document_names': list(document_names),
        'all_fields': list(all_fields)
    }

def sample_documents_by_type(vector_store, chunk_type: str, sample_size: int = 3):
    """按类型抽样提取文档"""
    print(f"\n🔍 抽样提取 {chunk_type} 类型文档 (最多 {sample_size} 个):")
    print("-" * 60)
    
    samples = []
    count = 0
    
    for doc_id, doc in vector_store.docstore._dict.items():
        if count >= sample_size:
            break
            
        metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
        if metadata.get('chunk_type') == chunk_type:
            count += 1
            
            sample_info = {
                'doc_id': doc_id,
                'content_preview': str(doc.page_content)[:200] + "..." if len(str(doc.page_content)) > 200 else str(doc.page_content),
                'metadata': metadata
            }
            samples.append(sample_info)
            
            print(f"\n📄 样本 {count}:")
            print(f"  🆔 文档ID: {doc_id}")
            print(f"  📄 文档名称: {metadata.get('document_name', 'N/A')}")
            print(f"  📖 页码: {metadata.get('page_number', 'N/A')}")
            print(f"  📝 分块索引: {metadata.get('chunk_index', 'N/A')}")
            
            # 根据类型显示特定字段
            if chunk_type == 'image':
                print(f"  🖼️ 图片ID: {metadata.get('image_id', 'N/A')}")
                print(f"  🏷️ 图片类型: {metadata.get('image_type', 'N/A')}")
                print(f"  📋 图片标题: {metadata.get('img_caption', 'N/A')}")
                print(f"  🎯 增强描述: {metadata.get('enhanced_description', 'N/A')[:100]}...")
                
            elif chunk_type == 'table':
                print(f"  📊 表格ID: {metadata.get('table_id', 'N/A')}")
                print(f"  🏷️ 表格类型: {metadata.get('table_type', 'N/A')}")
                
            elif chunk_type == 'text':
                print(f"  📝 内容预览: {sample_info['content_preview']}")
            
            print(f"  🔧 所有元数据字段: {list(metadata.keys())}")
    
    if not samples:
        print(f"  ❌ 未找到 {chunk_type} 类型的文档")
    
    return samples

def analyze_field_content(vector_store, field_name: str):
    """分析特定字段的内容分布"""
    print(f"\n🔍 分析字段 '{field_name}' 的内容分布:")
    print("-" * 60)
    
    field_values = {}
    field_types = {}
    
    for doc_id, doc in vector_store.docstore._dict.items():
        metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
        value = metadata.get(field_name)
        
        if value is not None:
            # 统计值分布
            if value not in field_values:
                field_values[value] = 0
            field_values[value] += 1
            
            # 统计类型分布
            value_type = type(value).__name__
            if value_type not in field_types:
                field_types[value_type] = 0
            field_types[value_type] += 1
    
    if not field_values:
        print(f"  ❌ 字段 '{field_name}' 在所有文档中都不存在")
        return
    
    print(f"  📊 值分布 (共 {len(field_values)} 个唯一值):")
    for value, count in sorted(field_values.items(), key=lambda x: x[1], reverse=True)[:10]:
        if isinstance(value, str) and len(value) > 50:
            display_value = value[:50] + "..."
        else:
            display_value = str(value)
        print(f"    '{display_value}': {count} 次")
    
    print(f"\n  🔧 类型分布:")
    for value_type, count in field_types.items():
        print(f"    {value_type}: {count} 次")

def show_detailed_statistics(vector_store, structure_info):
    """显示详细的统计信息"""
    print(f"\n📊 详细统计信息")
    print("=" * 60)
    
    # 按文档名称统计
    doc_stats = {}
    for doc_id, doc in vector_store.docstore._dict.items():
        metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
        doc_name = metadata.get('document_name', 'unknown')
        chunk_type = metadata.get('chunk_type', 'unknown')
        
        if doc_name not in doc_stats:
            doc_stats[doc_name] = {'total': 0, 'types': {}}
        
        doc_stats[doc_name]['total'] += 1
        if chunk_type not in doc_stats[doc_name]['types']:
            doc_stats[doc_name]['types'][chunk_type] = 0
        doc_stats[doc_name]['types'][chunk_type] += 1
    
    print("📄 按文档统计:")
    for doc_name, stats in sorted(doc_stats.items()):
        print(f"  {doc_name}:")
        print(f"    总分块数: {stats['total']}")
        for chunk_type, count in stats['types'].items():
            print(f"    - {chunk_type}: {count}")
    
    # 字段使用率统计
    field_usage = {}
    total_docs = structure_info['total_docs']
    
    for doc_id, doc in vector_store.docstore._dict.items():
        metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
        for field in metadata.keys():
            if field not in field_usage:
                field_usage[field] = 0
            field_usage[field] += 1
    
    print(f"\n📋 字段使用率统计:")
    for field, usage_count in sorted(field_usage.items(), key=lambda x: x[1], reverse=True):
        usage_rate = (usage_count / total_docs) * 100
        print(f"  {field}: {usage_count}/{total_docs} ({usage_rate:.1f}%)")

def save_analysis_results(structure_info, output_file: str = "database_analysis.json"):
    """保存分析结果到文件"""
    try:
        # 准备可序列化的数据
        serializable_info = {
            'total_docs': structure_info['total_docs'],
            'chunk_types': structure_info['chunk_types'],
            'document_names': structure_info['document_names'],
            'all_fields': structure_info['all_fields'],
            'analysis_timestamp': str(Path().cwd()),
            'analysis_summary': f"数据库包含 {structure_info['total_docs']} 个文档，{len(structure_info['chunk_types'])} 种分块类型"
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_info, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 分析结果已保存到: {output_file}")
        
    except Exception as e:
        logger.error(f"保存分析结果失败: {e}")

def main():
    """主函数"""
    print("🔍 向量数据库结构分析工具")
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
        
        # 加载向量存储
        vector_store = load_vector_store(vector_db_path)
        if not vector_store:
            print("❌ 无法加载向量存储")
            return
        
        # 分析数据库结构
        structure_info = analyze_database_structure(vector_store)
        if not structure_info:
            return
        
        # 显示详细统计
        show_detailed_statistics(vector_store, structure_info)
        
        # 抽样提取不同类型的文档
        print(f"\n🔍 抽样分析不同类型文档:")
        for chunk_type in structure_info['chunk_types'].keys():
            sample_documents_by_type(vector_store, chunk_type, sample_size=2)
        
        # 分析重要字段
        important_fields = ['chunk_type', 'document_name', 'page_number', 'chunk_index']
        for field in important_fields:
            if field in structure_info['all_fields']:
                analyze_field_content(vector_store, field)
        
        # 保存分析结果
        save_choice = input("\n是否保存分析结果到文件? (y/n): ").strip().lower()
        if save_choice == 'y':
            output_file = "database_analysis.json"
            save_analysis_results(structure_info, output_file)
        
        print("\n✅ 数据库结构分析完成！")
        
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        print(f"❌ 程序执行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
