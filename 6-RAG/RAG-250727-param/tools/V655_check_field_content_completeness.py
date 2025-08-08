'''
程序说明：

## 1. 检查向量数据库中字段内容的完整性
## 2. 特别关注图片文档的关键字段是否为空
## 3. 识别可能导致检索失败的字段内容缺失问题
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

def check_field_content_completeness():
    """检查字段内容的完整性"""
    
    print("🔍 检查向量数据库字段内容完整性")
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
        
        # 检查每种类型的字段内容完整性
        print(f"\n🔍 字段内容完整性检查:")
        print("=" * 80)
        
        for doc_type, docs in docs_by_type.items():
            if not docs:
                continue
                
            emoji = {'image': '🖼️', 'text': '📄', 'table': '📊', 'unknown': '❓'}.get(doc_type, '📄')
            print(f"\n{emoji} {doc_type.upper()} 类型文档字段完整性:")
            print("-" * 60)
            
            # 收集字段统计
            field_stats = defaultdict(lambda: {'total': 0, 'empty': 0, 'non_empty': 0, 'empty_docs': []})
            
            for doc_id, doc in docs:
                metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
                
                for field_name, field_value in metadata.items():
                    field_stats[field_name]['total'] += 1
                    
                    # 检查是否为空
                    is_empty = (
                        field_value is None or 
                        (isinstance(field_value, str) and not field_value.strip()) or
                        (isinstance(field_value, list) and len(field_value) == 0) or
                        (isinstance(field_value, dict) and len(field_value) == 0)
                    )
                    
                    if is_empty:
                        field_stats[field_name]['empty'] += 1
                        field_stats[field_name]['empty_docs'].append(doc_id)
                    else:
                        field_stats[field_name]['non_empty'] += 1
            
            # 显示字段完整性统计
            for field_name, stats in sorted(field_stats.items()):
                empty_rate = (stats['empty'] / stats['total']) * 100 if stats['total'] > 0 else 0
                status_emoji = "❌" if empty_rate > 0 else "✅"
                
                print(f"  {status_emoji} {field_name}:")
                print(f"    总数: {stats['total']}, 非空: {stats['non_empty']}, 空值: {stats['empty']} ({empty_rate:.1f}%)")
                
                # 如果空值较多，显示一些空值的文档ID
                if stats['empty'] > 0 and stats['empty'] <= 5:
                    print(f"    空值文档: {stats['empty_docs']}")
                elif stats['empty'] > 5:
                    print(f"    空值文档: {stats['empty_docs'][:3]}... (共{stats['empty']}个)")
        
        # 特别检查图片文档的关键字段
        print(f"\n🔍 图片文档关键字段详细检查:")
        print("=" * 80)
        
        image_docs = docs_by_type.get('image', [])
        if image_docs:
            print(f"🖼️ 检查 {len(image_docs)} 个图片文档")
            
            # 关键字段列表
            critical_fields = [
                'enhanced_description', 'image_id', 'image_path', 
                'image_filename', 'img_caption', 'img_footnote'
            ]
            
            critical_field_issues = []
            
            for doc_id, doc in image_docs:
                metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
                
                doc_issues = []
                for field in critical_fields:
                    if field in metadata:
                        value = metadata[field]
                        is_empty = (
                            value is None or 
                            (isinstance(value, str) and not value.strip()) or
                            (isinstance(value, list) and len(value) == 0)
                        )
                        if is_empty:
                            doc_issues.append(field)
                    else:
                        doc_issues.append(f"{field}(缺失)")
                
                if doc_issues:
                    critical_field_issues.append((doc_id, doc_issues))
            
            if critical_field_issues:
                print(f"❌ 发现 {len(critical_field_issues)} 个图片文档存在关键字段问题:")
                for doc_id, issues in critical_field_issues[:10]:  # 只显示前10个
                    print(f"  📄 {doc_id}: {', '.join(issues)}")
                if len(critical_field_issues) > 10:
                    print(f"  ... 还有 {len(critical_field_issues) - 10} 个文档存在问题")
            else:
                print(f"✅ 所有图片文档的关键字段都完整")
        
        # 检查文档内容
        print(f"\n🔍 文档内容检查:")
        print("=" * 80)
        
        content_issues = []
        for doc_type, docs in docs_by_type.items():
            for doc_id, doc in docs:
                # 检查文档内容是否为空
                if not hasattr(doc, 'page_content') or not doc.page_content or not doc.page_content.strip():
                    content_issues.append((doc_type, doc_id, "page_content为空"))
                
                # 检查元数据是否为空
                if not hasattr(doc, 'metadata') or not doc.metadata:
                    content_issues.append((doc_type, doc_id, "metadata为空"))
        
        if content_issues:
            print(f"❌ 发现 {len(content_issues)} 个文档存在内容问题:")
            for doc_type, doc_id, issue in content_issues[:10]:
                emoji = {'image': '🖼️', 'text': '📄', 'table': '📊'}.get(doc_type, '📄')
                print(f"  {emoji} {doc_id}: {issue}")
            if len(content_issues) > 10:
                print(f"  ... 还有 {len(content_issues) - 10} 个文档存在问题")
        else:
            print(f"✅ 所有文档的内容都完整")
        
        # 总结
        print(f"\n📊 检查总结:")
        print("=" * 80)
        
        total_docs = sum(len(docs) for docs in docs_by_type.values())
        print(f"  总文档数: {total_docs}")
        print(f"  图片文档数: {len(docs_by_type.get('image', []))}")
        print(f"  内容问题数: {len(content_issues)}")
        print(f"  关键字段问题数: {len(critical_field_issues) if 'critical_field_issues' in locals() else 0}")
        
        if content_issues or ('critical_field_issues' in locals() and critical_field_issues):
            print(f"\n⚠️  建议:")
            print(f"  1. 检查文档处理流程，确保所有字段都被正确填充")
            print(f"  2. 重新处理存在问题的文档")
            print(f"  3. 验证图片增强处理是否完成")
        else:
            print(f"\n✅ 数据库字段内容完整性良好")
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_field_content_completeness()
