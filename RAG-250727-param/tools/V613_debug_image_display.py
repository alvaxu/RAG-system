'''
程序说明：

## 1. 调试图片显示问题
## 2. 分析图片检索和显示流程
## 3. 检查图4显示的具体问题
## 4. 提供解决方案建议
'''

import os
import sys
import json
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import FAISS
from config.config_manager import ConfigManager

def debug_image_display():
    """调试图片显示问题"""
    
    # 加载配置
    config = ConfigManager()
    
    # 向量数据库路径
    vector_db_path = config.settings.vector_db_dir
    
    print("🔍 调试图片显示问题")
    print("=" * 60)
    
    try:
        # 加载向量数据库
        embeddings = DashScopeEmbeddings(
            dashscope_api_key=config.settings.dashscope_api_key, 
            model="text-embedding-v1"
        )
        vector_store = FAISS.load_local(
            vector_db_path, 
            embeddings, 
            allow_dangerous_deserialization=True
        )
        
        print(f"✅ 向量数据库加载成功")
        print(f"📊 总文档数: {len(vector_store.docstore._dict)}")
        
        # 1. 分析图片检索流程
        print(f"\n🔍 1. 分析图片检索流程")
        print("-" * 40)
        
        # 模拟"请显示图4"的查询
        test_question = "请显示图4"
        print(f"测试问题: '{test_question}'")
        
        # 检查图片请求关键词识别
        image_request_keywords = ['图', '图表', '图片', 'figure', '显示图', '看看图']
        has_image_request = any(keyword in test_question for keyword in image_request_keywords)
        print(f"图片请求识别: {has_image_request}")
        
        # 检查特定图片编号识别
        import re
        figure_pattern = r'图(\d+)'
        figure_matches = re.findall(figure_pattern, test_question)
        print(f"图片编号识别: {figure_matches}")
        
        # 2. 测试图片检索
        print(f"\n🔍 2. 测试图片检索")
        print("-" * 40)
        
        # 直接检索包含"图4"的文档
        print("直接检索包含'图4'的文档:")
        figure4_docs = []
        for doc_id, doc in vector_store.docstore._dict.items():
            if "图4" in doc.page_content:
                figure4_docs.append(doc)
        
        print(f"找到 {len(figure4_docs)} 个包含'图4'的文档")
        
        # 检索图片类型文档
        print("\n检索图片类型文档:")
        image_docs = []
        for doc_id, doc in vector_store.docstore._dict.items():
            if doc.metadata.get('chunk_type') == 'image':
                image_docs.append(doc)
        
        print(f"找到 {len(image_docs)} 个图片文档")
        
        # 查找图4图片文档
        figure4_images = []
        for doc in image_docs:
            caption = doc.metadata.get('img_caption', [])
            if caption and any("图4" in c for c in caption):
                figure4_images.append(doc)
        
        print(f"找到 {len(figure4_images)} 个图4图片文档")
        
        # 3. 测试相似度检索
        print(f"\n🔍 3. 测试相似度检索")
        print("-" * 40)
        
        test_queries = [
            "图4",
            "请显示图4",
            "公司25Q1下游应用领域结构情况",
            "中芯国际归母净利润情况概览"
        ]
        
        for query in test_queries:
            print(f"\n查询: '{query}'")
            try:
                results = vector_store.similarity_search(query, k=5)
                print(f"找到 {len(results)} 个结果")
                
                # 分析结果
                image_results = []
                text_results = []
                
                for i, result in enumerate(results):
                    chunk_type = result.metadata.get('chunk_type', 'text')
                    caption = result.metadata.get('img_caption', [])
                    
                    if chunk_type == 'image':
                        image_results.append({
                            'index': i + 1,
                            'caption': caption,
                            'content_preview': result.page_content[:100]
                        })
                    else:
                        text_results.append({
                            'index': i + 1,
                            'content_preview': result.page_content[:100]
                        })
                
                print(f"  图片结果: {len(image_results)} 个")
                for img in image_results:
                    print(f"    {img['index']}. 标题: {img['caption']}")
                
                print(f"  文本结果: {len(text_results)} 个")
                for txt in text_results[:2]:  # 只显示前2个
                    print(f"    {txt['index']}. 内容: {txt['content_preview']}...")
                    
            except Exception as e:
                print(f"❌ 检索失败: {e}")
        
        # 4. 分析图4图片的具体信息
        print(f"\n🔍 4. 分析图4图片的具体信息")
        print("-" * 40)
        
        if figure4_images:
            for i, doc in enumerate(figure4_images, 1):
                print(f"\n图4图片 {i}:")
                metadata = doc.metadata
                print(f"  图片ID: {metadata.get('image_id', 'N/A')}")
                print(f"  图片路径: {metadata.get('image_path', 'N/A')}")
                print(f"  图片标题: {metadata.get('img_caption', [])}")
                print(f"  图片脚注: {metadata.get('img_footnote', [])}")
                print(f"  文档名称: {metadata.get('document_name', 'N/A')}")
                print(f"  页码: {metadata.get('page_number', 'N/A')}")
                print(f"  内容长度: {len(doc.page_content)}")
                print(f"  内容预览: {doc.page_content[:200]}...")
        else:
            print("❌ 未找到图4图片文档")
        
        # 5. 测试图片过滤逻辑
        print(f"\n🔍 5. 测试图片过滤逻辑")
        print("-" * 40)
        
        # 模拟前端的图片过滤逻辑
        def test_image_filtering(question, image_sources):
            """测试图片过滤逻辑"""
            print(f"测试问题: '{question}'")
            print(f"可用图片源: {len(image_sources)} 个")
            
            # 解析用户图片请求
            user_requests = parse_user_image_requests(question)
            print(f"解析到的用户请求: {user_requests}")
            
            # 查找匹配的图片
            matched_images = find_requested_images(user_requests, image_sources)
            print(f"匹配的图片: {len(matched_images)} 个")
            
            return matched_images
        
        # 转换图片文档为前端格式
        image_sources = []
        for doc in image_docs:
            source = {
                'content': doc.page_content,
                'metadata': doc.metadata
            }
            image_sources.append(source)
        
        # 测试不同的问题
        test_questions = [
            "请显示图4",
            "图4",
            "显示图4",
            "看看图4"
        ]
        
        for question in test_questions:
            matched = test_image_filtering(question, image_sources)
            print(f"问题 '{question}' 匹配到 {len(matched)} 个图片\n")
        
        # 6. 分析问题根源
        print(f"\n🔍 6. 分析问题根源")
        print("-" * 40)
        
        print("可能的问题:")
        print("1. 相似度检索问题:")
        print("   - 查询'图4'时，相似度检索可能返回其他内容")
        print("   - 图片文档的向量表示可能与其他内容相似")
        
        print("\n2. 图片匹配逻辑问题:")
        print("   - 图片标题匹配可能不够精确")
        print("   - 正则表达式匹配可能有问题")
        
        print("\n3. 检索策略问题:")
        print("   - 没有优先检索图片类型的文档")
        print("   - 检索数量限制可能过滤掉了图4")
        
        print("\n4. 前端显示逻辑问题:")
        print("   - 图片URL构建可能有问题")
        print("   - 图片过滤逻辑可能过于严格")
        
        # 7. 提供解决方案
        print(f"\n🔍 7. 提供解决方案")
        print("-" * 40)
        
        print("建议的解决方案:")
        print("1. 改进检索策略:")
        print("   - 当检测到图片请求时，优先检索图片类型文档")
        print("   - 增加图片文档的检索权重")
        
        print("\n2. 优化图片匹配:")
        print("   - 改进图片标题的匹配逻辑")
        print("   - 增加模糊匹配和语义匹配")
        
        print("\n3. 调整检索参数:")
        print("   - 增加检索数量k")
        print("   - 降低相似度阈值")
        
        print("\n4. 前端优化:")
        print("   - 改进图片URL构建逻辑")
        print("   - 优化图片过滤和显示逻辑")
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()


def parse_user_image_requests(user_question):
    """解析用户图片请求（模拟前端逻辑）"""
    requests = []
    question = user_question.lower()
    
    # 提取图表编号
    import re
    chart_number_patterns = [
        r'图(\d+)',
        r'图表(\d+)',
        r'图片(\d+)'
    ]
    
    for pattern in chart_number_patterns:
        matches = re.findall(pattern, question)
        for match in matches:
            requests.append({
                'type': 'chart_number',
                'value': match,
                'pattern': f'图{match}'
            })
    
    return requests


def find_requested_images(user_requests, image_sources):
    """查找匹配的图片（模拟前端逻辑）"""
    matched_images = []
    
    for request in user_requests:
        if request['type'] == 'chart_number':
            figure_num = request['value']
            
            for source in image_sources:
                caption = source['metadata'].get('img_caption', [])
                caption_text = ' '.join(caption)
                
                # 检查是否包含图4
                match_patterns = [
                    f"图{figure_num}",
                    f"图表{figure_num}",
                    f"图片{figure_num}"
                ]
                
                if any(pattern in caption_text for pattern in match_patterns):
                    matched_images.append(source)
    
    return matched_images


if __name__ == "__main__":
    debug_image_display()
