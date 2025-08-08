'''
程序说明：
## 1. 分析向量数据库中所有三种类型文档的元数据字段
## 2. 对比不同类型文档的字段差异
## 3. 识别每种类型文档的独特字段和共同字段
'''

import pickle
import os
import sys
from collections import defaultdict

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from config.settings import Settings

def analyze_all_metadata_fields():
    """分析所有类型文档的元数据字段"""
    
    print("🔍 分析向量数据库中所有类型文档的元数据字段")
    print("=" * 80)
    
    try:
        # 加载配置
        config = Settings.load_from_file('config.json')
        embeddings = DashScopeEmbeddings(dashscope_api_key=config.dashscope_api_key, model="text-embedding-v1")
        
        # 加载向量数据库
        vector_db_path = "./central/vector_db"
        vector_store = FAISS.load_local(vector_db_path, embeddings, allow_dangerous_deserialization=True)
        
        print(f"✅ 向量数据库加载成功")
        print(f"📊 总文档数: {len(vector_store.docstore._dict)}")
        
        # 按类型分组文档
        docs_by_type = defaultdict(list)
        
        for doc_id, doc in vector_store.docstore._dict.items():
            metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
            chunk_type = metadata.get('chunk_type', 'unknown')
            docs_by_type[chunk_type].append((doc_id, doc))
        
        # 显示各类型文档数量
        print(f"\n📊 各类型文档数量:")
        for doc_type, docs in docs_by_type.items():
            emoji = {'image': '🖼️', 'text': '📄', 'table': '📊', 'unknown': '❓'}.get(doc_type, '📄')
            print(f"  {emoji} {doc_type}: {len(docs)} 个")
        
        # 分析每种类型的字段
        print(f"\n🔍 各类型文档的元数据字段分析:")
        print("=" * 80)
        
        all_fields_by_type = {}
        
        for doc_type, docs in docs_by_type.items():
            if not docs:
                continue
                
            emoji = {'image': '🖼️', 'text': '📄', 'table': '📊', 'unknown': '❓'}.get(doc_type, '📄')
            print(f"\n{emoji} {doc_type.upper()} 类型文档:")
            print("-" * 60)
            
            # 收集所有字段
            fields = defaultdict(set)
            field_values = defaultdict(list)
            
            for doc_id, doc in docs:
                metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
                
                for field_name, field_value in metadata.items():
                    fields[field_name].add(type(field_value).__name__)
                    field_values[field_name].append(field_value)
            
            all_fields_by_type[doc_type] = dict(fields)
            
            # 显示字段统计
            print(f"  总字段数: {len(fields)}")
            
            # 显示每个字段的详细信息
            for field_name, value_types in sorted(fields.items()):
                value_type_str = ", ".join(sorted(value_types))
                sample_values = field_values[field_name][:3]  # 取前3个样本
                
                print(f"    📝 {field_name}:")
                print(f"      类型: {value_type_str}")
                print(f"      样本值: {sample_values}")
                
                # 如果是特殊字段，显示更多信息
                if field_name in ['page_content', 'enhanced_description', 'content']:
                    non_empty_count = sum(1 for v in field_values[field_name] if v and str(v).strip())
                    print(f"      非空值数量: {non_empty_count}/{len(field_values[field_name])}")
        
        # 对比不同类型的字段差异
        print(f"\n🔍 不同类型文档的字段对比:")
        print("=" * 80)
        
        # 获取所有字段
        all_fields = set()
        for fields in all_fields_by_type.values():
            all_fields.update(fields.keys())
        
        print(f"  所有字段总数: {len(all_fields)}")
        
        # 分析字段分布
        field_distribution = defaultdict(list)
        for field in all_fields:
            for doc_type, fields in all_fields_by_type.items():
                if field in fields:
                    field_distribution[field].append(doc_type)
        
        # 显示字段分布
        print(f"\n📊 字段分布情况:")
        print("-" * 60)
        
        common_fields = []
        unique_fields = defaultdict(list)
        
        for field, types in field_distribution.items():
            if len(types) == len(all_fields_by_type):
                common_fields.append(field)
                print(f"  🌐 {field}: 所有类型都有")
            else:
                unique_fields[tuple(types)].append(field)
                print(f"  🎯 {field}: 仅 {', '.join(types)} 类型有")
        
        # 显示共同字段和独特字段
        print(f"\n📋 字段分类总结:")
        print("-" * 60)
        
        print(f"  🌐 共同字段 ({len(common_fields)}个):")
        for field in sorted(common_fields):
            print(f"    - {field}")
        
        print(f"\n  🎯 独特字段:")
        for types, fields in unique_fields.items():
            type_str = ", ".join(types)
            print(f"    {type_str} 类型独有 ({len(fields)}个):")
            for field in sorted(fields):
                print(f"      - {field}")
        
        # 总结
        print(f"\n📊 分析总结:")
        print("=" * 80)
        
        total_docs = sum(len(docs) for docs in docs_by_type.values())
        print(f"  总文档数: {total_docs}")
        print(f"  文档类型数: {len(docs_by_type)}")
        print(f"  总字段数: {len(all_fields)}")
        print(f"  共同字段数: {len(common_fields)}")
        
        unique_field_count = sum(len(fields) for fields in unique_fields.values())
        print(f"  独特字段数: {unique_field_count}")
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_all_metadata_fields()
