'''
程序说明：
## 1. 分析当前图片文档设计的严密性
## 2. 识别潜在的设计问题和改进点
## 3. 提供设计优化建议
'''

import pickle
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Set

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from config.settings import Settings

def analyze_design_rigor():
    """分析当前设计的严密性"""
    
    print("🔍 分析当前图片文档设计的严密性")
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
        
        # 统计不同类型的文档
        image_docs = []
        text_docs = []
        table_docs = []
        
        for doc_id, doc in vector_store.docstore._dict.items():
            metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
            chunk_type = metadata.get('chunk_type', 'unknown')
            
            if chunk_type == 'image':
                image_docs.append((doc_id, doc))
            elif chunk_type == 'text':
                text_docs.append((doc_id, doc))
            elif chunk_type == 'table':
                table_docs.append((doc_id, doc))
        
        print(f"🖼️  图片文档数: {len(image_docs)}")
        print(f"📄 文本文档数: {len(text_docs)}")
        print(f"📊 表格文档数: {len(table_docs)}")
        
        # 分析设计问题
        print(f"\n🔍 设计严密性分析:")
        print("=" * 80)
        
        # 1. 数据一致性问题
        print(f"\n1️⃣ 数据一致性问题:")
        consistency_issues = analyze_data_consistency(image_docs)
        for issue in consistency_issues:
            print(f"   ⚠️  {issue}")
        
        # 2. 字段冗余问题
        print(f"\n2️⃣ 字段冗余问题:")
        redundancy_issues = analyze_field_redundancy(image_docs)
        for issue in redundancy_issues:
            print(f"   ⚠️  {issue}")
        
        # 3. 逻辑一致性问题
        print(f"\n3️⃣ 逻辑一致性问题:")
        logic_issues = analyze_logic_consistency(image_docs)
        for issue in logic_issues:
            print(f"   ⚠️  {issue}")
        
        # 4. 性能问题
        print(f"\n4️⃣ 性能问题:")
        performance_issues = analyze_performance_issues(image_docs)
        for issue in performance_issues:
            print(f"   ⚠️  {issue}")
        
        # 5. 维护性问题
        print(f"\n5️⃣ 维护性问题:")
        maintenance_issues = analyze_maintenance_issues(image_docs)
        for issue in maintenance_issues:
            print(f"   ⚠️  {issue}")
        
        # 6. 设计优点
        print(f"\n✅ 设计优点:")
        design_strengths = analyze_design_strengths(image_docs)
        for strength in design_strengths:
            print(f"   ✅ {strength}")
        
        # 7. 改进建议
        print(f"\n💡 改进建议:")
        improvement_suggestions = generate_improvement_suggestions(
            consistency_issues, redundancy_issues, logic_issues, 
            performance_issues, maintenance_issues
        )
        for suggestion in improvement_suggestions:
            print(f"   💡 {suggestion}")
        
        # 8. 总体评价
        print(f"\n📊 总体评价:")
        overall_score = calculate_design_score(
            consistency_issues, redundancy_issues, logic_issues,
            performance_issues, maintenance_issues, design_strengths
        )
        print(f"   设计严密性评分: {overall_score}/10")
        
        if overall_score >= 8:
            print(f"   🎉 设计非常严密，只有少量改进空间")
        elif overall_score >= 6:
            print(f"   👍 设计基本严密，建议进行优化")
        elif overall_score >= 4:
            print(f"   ⚠️ 设计存在明显问题，需要重构")
        else:
            print(f"   ❌ 设计存在严重问题，建议重新设计")
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()

def analyze_data_consistency(image_docs: List[tuple]) -> List[str]:
    """分析数据一致性问题"""
    issues = []
    
    if not image_docs:
        return ["没有图片文档可供分析"]
    
    # 检查page_content与enhanced_description的一致性
    inconsistent_count = 0
    for doc_id, doc in image_docs:
        metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
        page_content = doc.page_content
        enhanced_desc = metadata.get('enhanced_description', '')
        
        if page_content != enhanced_desc:
            inconsistent_count += 1
    
    if inconsistent_count > 0:
        issues.append(f"有 {inconsistent_count} 个图片文档的page_content与enhanced_description不一致")
    
    # 检查必需字段的完整性
    missing_fields = {}
    for doc_id, doc in image_docs:
        metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
        
        required_fields = ['image_id', 'image_path', 'document_name', 'chunk_type']
        for field in required_fields:
            if field not in metadata or not metadata[field]:
                missing_fields[field] = missing_fields.get(field, 0) + 1
    
    for field, count in missing_fields.items():
        issues.append(f"有 {count} 个文档缺少必需字段: {field}")
    
    return issues

def analyze_field_redundancy(image_docs: List[tuple]) -> List[str]:
    """分析字段冗余问题"""
    issues = []
    
    if not image_docs:
        return ["没有图片文档可供分析"]
    
    # 检查content字段的冗余
    redundant_content_count = 0
    for doc_id, doc in image_docs:
        metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
        page_content = doc.page_content
        enhanced_desc = metadata.get('enhanced_description', '')
        
        if page_content == enhanced_desc:
            redundant_content_count += 1
    
    if redundant_content_count == len(image_docs):
        issues.append("所有图片文档的page_content与enhanced_description完全相同，存在数据冗余")
    
    # 检查metadata中的冗余字段
    sample_metadata = image_docs[0][1].metadata if image_docs else {}
    redundant_metadata_fields = []
    
    # 检查可能的冗余字段
    potential_redundant = [
        ('page_number', 'page_idx'),
        ('image_filename', 'image_id'),
        ('content', 'enhanced_description')
    ]
    
    for field1, field2 in potential_redundant:
        if field1 in sample_metadata and field2 in sample_metadata:
            redundant_metadata_fields.append(f"{field1} 和 {field2}")
    
    if redundant_metadata_fields:
        issues.append(f"发现潜在的冗余字段对: {', '.join(redundant_metadata_fields)}")
    
    return issues

def analyze_logic_consistency(image_docs: List[tuple]) -> List[str]:
    """分析逻辑一致性问题"""
    issues = []
    
    if not image_docs:
        return ["没有图片文档可供分析"]
    
    # 检查图片文档的处理逻辑
    inconsistent_logic_count = 0
    for doc_id, doc in image_docs:
        metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
        
        # 检查chunk_type与文档内容的逻辑一致性
        if metadata.get('chunk_type') == 'image':
            page_content = doc.page_content
            # 如果page_content包含图片描述，但chunk_type是image，这是合理的
            # 但如果page_content是空或不是图片相关描述，可能有问题
            if not page_content or len(page_content.strip()) == 0:
                inconsistent_logic_count += 1
    
    if inconsistent_logic_count > 0:
        issues.append(f"有 {inconsistent_logic_count} 个图片文档的page_content为空，逻辑不一致")
    
    # 检查图片路径的有效性
    invalid_path_count = 0
    for doc_id, doc in image_docs:
        metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
        image_path = metadata.get('image_path', '')
        
        if image_path and not os.path.exists(image_path):
            invalid_path_count += 1
    
    if invalid_path_count > 0:
        issues.append(f"有 {invalid_path_count} 个图片文档的图片路径无效")
    
    return issues

def analyze_performance_issues(image_docs: List[tuple]) -> List[str]:
    """分析性能问题"""
    issues = []
    
    if not image_docs:
        return ["没有图片文档可供分析"]
    
    # 检查文档大小
    large_docs = 0
    total_size = 0
    
    for doc_id, doc in image_docs:
        metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
        page_content = doc.page_content
        
        doc_size = len(str(page_content)) + len(str(metadata))
        total_size += doc_size
        
        if doc_size > 10000:  # 10KB
            large_docs += 1
    
    if large_docs > 0:
        issues.append(f"有 {large_docs} 个图片文档过大（>10KB），可能影响检索性能")
    
    avg_size = total_size / len(image_docs) if image_docs else 0
    if avg_size > 5000:  # 5KB
        issues.append(f"图片文档平均大小较大（{avg_size:.0f}字节），可能影响系统性能")
    
    # 检查embedding维度一致性
    embedding_dims = set()
    for doc_id, doc in image_docs:
        metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
        semantic_features = metadata.get('semantic_features', {})
        embedding_dim = semantic_features.get('embedding_dimension', 0)
        if embedding_dim > 0:
            embedding_dims.add(embedding_dim)
    
    if len(embedding_dims) > 1:
        issues.append(f"发现多种embedding维度: {embedding_dims}，可能影响检索一致性")
    
    return issues

def analyze_maintenance_issues(image_docs: List[tuple]) -> List[str]:
    """分析维护性问题"""
    issues = []
    
    if not image_docs:
        return ["没有图片文档可供分析"]
    
    # 检查字段命名的一致性
    field_names = set()
    for doc_id, doc in image_docs:
        metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
        field_names.update(metadata.keys())
    
    # 检查是否有不一致的字段命名
    inconsistent_naming = []
    for field in field_names:
        if '_' in field and field.replace('_', '') in field_names:
            inconsistent_naming.append(field)
    
    if inconsistent_naming:
        issues.append(f"发现不一致的字段命名: {inconsistent_naming}")
    
    # 检查文档结构的复杂性
    complex_metadata_count = 0
    for doc_id, doc in image_docs:
        metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
        
        # 检查嵌套结构的复杂性
        nested_levels = 0
        for value in metadata.values():
            if isinstance(value, dict):
                nested_levels += 1
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                nested_levels += 1
        
        if nested_levels > 2:
            complex_metadata_count += 1
    
    if complex_metadata_count > 0:
        issues.append(f"有 {complex_metadata_count} 个文档的元数据结构过于复杂，增加维护难度")
    
    return issues

def analyze_design_strengths(image_docs: List[tuple]) -> List[str]:
    """分析设计优点"""
    strengths = []
    
    if not image_docs:
        return ["没有图片文档可供分析"]
    
    # 检查字段的完整性
    sample_metadata = image_docs[0][1].metadata if image_docs else {}
    important_fields = ['image_id', 'image_path', 'document_name', 'chunk_type', 
                       'img_caption', 'enhanced_description', 'semantic_features']
    
    present_fields = [field for field in important_fields if field in sample_metadata]
    if len(present_fields) >= 6:
        strengths.append(f"图片文档包含完整的元数据字段: {len(present_fields)}/{len(important_fields)}")
    
    # 检查语义特征的丰富性
    semantic_features_count = 0
    for doc_id, doc in image_docs:
        metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
        semantic_features = metadata.get('semantic_features', {})
        if semantic_features and len(semantic_features) >= 3:
            semantic_features_count += 1
    
    if semantic_features_count > 0:
        strengths.append(f"有 {semantic_features_count} 个文档包含丰富的语义特征")
    
    # 检查文档类型的清晰性
    clear_type_count = 0
    for doc_id, doc in image_docs:
        metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
        if metadata.get('chunk_type') == 'image':
            clear_type_count += 1
    
    if clear_type_count == len(image_docs):
        strengths.append("所有图片文档都有清晰的类型标识")
    
    # 检查增强描述的质量
    enhanced_desc_count = 0
    for doc_id, doc in image_docs:
        metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
        enhanced_desc = metadata.get('enhanced_description', '')
        if enhanced_desc and len(enhanced_desc) > 20:
            enhanced_desc_count += 1
    
    if enhanced_desc_count > 0:
        strengths.append(f"有 {enhanced_desc_count} 个文档包含高质量的增强描述")
    
    return strengths

def generate_improvement_suggestions(consistency_issues: List[str], redundancy_issues: List[str], 
                                   logic_issues: List[str], performance_issues: List[str], 
                                   maintenance_issues: List[str]) -> List[str]:
    """生成改进建议"""
    suggestions = []
    
    # 基于一致性问题提出建议
    if any("page_content与enhanced_description不一致" in issue for issue in consistency_issues):
        suggestions.append("统一page_content和enhanced_description的生成逻辑，确保数据一致性")
    
    if any("缺少必需字段" in issue for issue in consistency_issues):
        suggestions.append("建立数据验证机制，确保所有必需字段的完整性")
    
    # 基于冗余问题提出建议
    if any("数据冗余" in issue for issue in redundancy_issues):
        suggestions.append("考虑移除冗余字段，或建立字段间的自动同步机制")
    
    # 基于逻辑问题提出建议
    if any("逻辑不一致" in issue for issue in logic_issues):
        suggestions.append("建立文档类型与内容的逻辑验证规则")
    
    if any("图片路径无效" in issue for issue in logic_issues):
        suggestions.append("添加图片文件存在性检查，建立路径验证机制")
    
    # 基于性能问题提出建议
    if any("文档过大" in issue for issue in performance_issues):
        suggestions.append("优化文档大小，考虑压缩或分块存储大型元数据")
    
    if any("embedding维度" in issue for issue in performance_issues):
        suggestions.append("统一embedding模型和维度，确保检索一致性")
    
    # 基于维护性问题提出建议
    if any("字段命名" in issue for issue in maintenance_issues):
        suggestions.append("建立统一的字段命名规范，避免命名不一致")
    
    if any("结构复杂" in issue for issue in maintenance_issues):
        suggestions.append("简化元数据结构，减少嵌套层级，提高可维护性")
    
    # 通用建议
    suggestions.append("建立数据质量监控机制，定期检查数据一致性")
    suggestions.append("完善文档处理流程的异常处理和日志记录")
    suggestions.append("考虑建立数据版本控制机制，支持数据回滚")
    
    return suggestions

def calculate_design_score(consistency_issues: List[str], redundancy_issues: List[str], 
                          logic_issues: List[str], performance_issues: List[str], 
                          maintenance_issues: List[str], strengths: List[str]) -> float:
    """计算设计评分"""
    base_score = 10.0
    
    # 根据问题数量扣分
    issue_weights = {
        'consistency': 2.0,  # 一致性问题权重最高
        'logic': 1.5,        # 逻辑问题次之
        'redundancy': 1.0,   # 冗余问题
        'performance': 1.0,  # 性能问题
        'maintenance': 0.8   # 维护性问题
    }
    
    deductions = (
        len(consistency_issues) * issue_weights['consistency'] +
        len(logic_issues) * issue_weights['logic'] +
        len(redundancy_issues) * issue_weights['redundancy'] +
        len(performance_issues) * issue_weights['performance'] +
        len(maintenance_issues) * issue_weights['maintenance']
    )
    
    # 根据优点加分
    bonus = len(strengths) * 0.3
    
    final_score = max(0.0, min(10.0, base_score - deductions + bonus))
    return round(final_score, 1)

if __name__ == "__main__":
    analyze_design_rigor()
