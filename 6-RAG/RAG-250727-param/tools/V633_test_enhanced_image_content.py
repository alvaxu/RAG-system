'''
程序说明：
## 1. 测试更丰富的图片内容对RAG系统的影响
## 2. 对比不同内容质量下的检索效果
## 3. 分析内容丰富度与问答质量的关系
'''

import pickle
import os
import sys
from collections import defaultdict
import json

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from config.settings import Settings

def test_enhanced_image_content():
    """测试更丰富的图片内容对RAG系统的影响"""
    
    print("🔍 测试更丰富的图片内容对RAG系统的影响")
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
        
        # 分析图片文档的内容质量
        print(f"\n🔍 分析图片文档的内容质量:")
        print("=" * 80)
        
        image_docs = []
        for doc_id, doc in vector_store.docstore._dict.items():
            metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
            if metadata.get('chunk_type') == 'image':
                image_docs.append((doc_id, doc))
        
        print(f"🖼️  图片文档数: {len(image_docs)}")
        
        # 分析内容质量
        content_quality_analysis = analyze_content_quality(image_docs)
        
        # 显示内容质量分析结果
        print(f"\n📊 内容质量分析:")
        print("-" * 60)
        
        for quality_level, docs in content_quality_analysis.items():
            print(f"  {quality_level}: {len(docs)} 个文档")
            if docs:
                sample_doc = docs[0]
                metadata = sample_doc[1].metadata
                page_content = sample_doc[1].page_content
                print(f"    示例内容长度: {len(page_content)} 字符")
                print(f"    示例内容: {page_content[:100]}...")
        
        # 测试不同内容质量下的检索效果
        print(f"\n🔍 测试不同内容质量下的检索效果:")
        print("=" * 80)
        
        test_queries = [
            "中芯国际的营业收入情况",
            "图1显示了什么内容",
            "公司的毛利率和净利率",
            "个股相对沪深300指数的表现",
            "产能利用率的变化趋势"
        ]
        
        for query in test_queries:
            print(f"\n📝 测试查询: {query}")
            print("-" * 40)
            
            # 执行检索
            try:
                results = vector_store.similarity_search(query, k=5)
                
                # 分析检索结果
                image_results = [doc for doc in results if doc.metadata.get('chunk_type') == 'image']
                text_results = [doc for doc in results if doc.metadata.get('chunk_type') == 'text']
                table_results = [doc for doc in results if doc.metadata.get('chunk_type') == 'table']
                
                print(f"  检索到图片文档: {len(image_results)} 个")
                print(f"  检索到文本文档: {len(text_results)} 个")
                print(f"  检索到表格文档: {len(table_results)} 个")
                
                # 分析图片文档的检索质量
                if image_results:
                    print(f"  🖼️  图片文档检索质量分析:")
                    for i, doc in enumerate(image_results[:3]):  # 只分析前3个
                        metadata = doc.metadata
                        page_content = doc.page_content
                        img_caption = metadata.get('img_caption', [''])
                        caption_text = ' '.join(img_caption) if img_caption else '无标题'
                        
                        print(f"    {i+1}. {caption_text}")
                        print(f"       内容长度: {len(page_content)} 字符")
                        print(f"       内容质量: {assess_content_quality(page_content)}")
                        print(f"       相关性: {assess_relevance(query, page_content)}")
                
            except Exception as e:
                print(f"  检索失败: {e}")
        
        # 生成改进建议
        print(f"\n💡 改进建议:")
        print("=" * 80)
        
        suggestions = generate_improvement_suggestions(content_quality_analysis)
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. {suggestion}")
        
        # 总结
        print(f"\n📊 总结:")
        print("=" * 80)
        
        total_images = len(image_docs)
        high_quality = len(content_quality_analysis.get('高质量', []))
        medium_quality = len(content_quality_analysis.get('中等质量', []))
        low_quality = len(content_quality_analysis.get('低质量', []))
        
        print(f"  总图片数: {total_images}")
        print(f"  高质量内容: {high_quality} ({high_quality/total_images*100:.1f}%)")
        print(f"  中等质量内容: {medium_quality} ({medium_quality/total_images*100:.1f}%)")
        print(f"  低质量内容: {low_quality} ({low_quality/total_images*100:.1f}%)")
        
        if high_quality / total_images >= 0.7:
            print(f"  ✅ 图片内容质量良好，RAG系统性能应该不错")
        elif high_quality / total_images >= 0.4:
            print(f"  ⚠️  图片内容质量一般，建议优化")
        else:
            print(f"  ❌ 图片内容质量较差，强烈建议优化")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def analyze_content_quality(image_docs):
    """分析图片文档的内容质量"""
    
    quality_groups = {
        '高质量': [],
        '中等质量': [],
        '低质量': []
    }
    
    for doc_id, doc in image_docs:
        metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
        page_content = doc.page_content
        
        # 评估内容质量
        quality_score = assess_content_quality(page_content)
        
        if quality_score >= 0.8:
            quality_groups['高质量'].append((doc_id, doc))
        elif quality_score >= 0.5:
            quality_groups['中等质量'].append((doc_id, doc))
        else:
            quality_groups['低质量'].append((doc_id, doc))
    
    return quality_groups

def assess_content_quality(content):
    """评估内容质量"""
    if not content or len(content.strip()) == 0:
        return 0.0
    
    score = 0.0
    
    # 1. 内容长度评分 (0-0.3分)
    length_score = min(len(content) / 200, 1.0) * 0.3
    score += length_score
    
    # 2. 信息丰富度评分 (0-0.4分)
    info_keywords = ['图片标题', '图片脚注', '图表类型', '数据', '趋势', '分析']
    info_count = sum(1 for keyword in info_keywords if keyword in content)
    info_score = min(info_count / 3, 1.0) * 0.4
    score += info_score
    
    # 3. 结构化程度评分 (0-0.3分)
    structure_indicators = ['|', ':', ';']
    structure_count = sum(1 for indicator in structure_indicators if indicator in content)
    structure_score = min(structure_count / 2, 1.0) * 0.3
    score += structure_score
    
    return min(score, 1.0)

def assess_relevance(query, content):
    """评估内容与查询的相关性"""
    if not content or not query:
        return 0.0
    
    # 简单的关键词匹配评分
    query_words = set(query.lower().split())
    content_words = set(content.lower().split())
    
    if not query_words:
        return 0.0
    
    # 计算词汇重叠度
    overlap = len(query_words.intersection(content_words))
    relevance = overlap / len(query_words)
    
    return min(relevance, 1.0)

def generate_improvement_suggestions(content_quality_analysis):
    """生成改进建议"""
    suggestions = []
    
    low_quality_count = len(content_quality_analysis.get('低质量', []))
    medium_quality_count = len(content_quality_analysis.get('中等质量', []))
    
    if low_quality_count > 0:
        suggestions.append(f"有 {low_quality_count} 个图片文档内容质量较低，建议增强图片描述生成")
    
    if medium_quality_count > 0:
        suggestions.append(f"有 {medium_quality_count} 个图片文档内容质量一般，可以考虑添加更多语义信息")
    
    suggestions.append("考虑使用更先进的图像理解模型（如ONE-PEACE）来生成更丰富的图片描述")
    suggestions.append("在图片描述中添加更多上下文信息，如数据趋势、关键指标等")
    suggestions.append("建立图片内容质量评估机制，定期检查和优化")
    suggestions.append("考虑为不同类型的图片（图表、照片、表格）使用不同的描述策略")
    
    return suggestions

if __name__ == "__main__":
    test_enhanced_image_content()
