#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试image_text filter功能

测试目标：
1. 验证image_text filter是否真的不工作
2. 对比image_text vs text filter的差异
3. 分析为什么image_text filter返回0个结果
"""

import os
import sys
import logging
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_image_text_filter():
    """测试image_text filter功能"""
    print("="*80)
    print("测试image_text filter功能")
    print("="*80)
    
    try:
        # 1. 导入必要的模块
        print("导入必要模块...")
        from langchain_community.vectorstores import FAISS
        from langchain_community.embeddings import DashScopeEmbeddings
        from config.api_key_manager import get_dashscope_api_key
        from config.settings import Settings
        
        print("模块导入成功")
        
        # 2. 获取配置
        print("获取配置...")
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(project_root, 'config.json')
        
        try:
            old_cwd = os.getcwd()
            os.chdir(project_root)
            config = Settings.load_from_file('config.json')
            os.chdir(old_cwd)
        except Exception as e:
            print(f"配置文件加载失败: {e}")
            return False
        
        # 3. 获取API密钥
        api_key = get_dashscope_api_key(config.dashscope_api_key)
        if not api_key:
            print("未找到有效的DashScope API密钥")
            return False
        
        print("配置获取成功")
        
        # 4. 初始化embeddings
        text_embeddings = DashScopeEmbeddings(
            dashscope_api_key=api_key,
            model='text-embedding-v1'
        )
        print("text embeddings初始化成功")
        
        # 5. 加载向量数据库
        vector_db_path = config.vector_db_dir
        vector_store = FAISS.load_local(
            vector_db_path, 
            text_embeddings,
            allow_dangerous_deserialization=True
        )
        print("向量数据库加载成功")
        
        # 6. 分析数据库结构
        docstore_dict = vector_store.docstore._dict
        print(f"数据库包含 {len(docstore_dict)} 个文档")
        
        # 统计不同类型的chunks
        chunk_type_stats = {}
        for doc_id, doc in docstore_dict.items():
            metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
            chunk_type = metadata.get('chunk_type', 'unknown')
            chunk_type_stats[chunk_type] = chunk_type_stats.get(chunk_type, 0) + 1
        
        print("数据库chunk类型统计:")
        for chunk_type, count in chunk_type_stats.items():
            print(f"   - {chunk_type}: {count} 个")
        
        # 7. 关键测试：对比image_text vs text filter
        print("\n" + "="*80)
        print("关键测试：对比image_text vs text filter")
        print("="*80)
        
        test_query = "中芯国际财务图表"
        print(f"测试查询: {test_query}")
        
        # 测试1：无filter搜索
        print("\n测试1：无filter搜索")
        no_filter_results = vector_store.similarity_search(test_query, k=100)
        print(f"   无filter搜索结果数量: {len(no_filter_results)}")
        
        # 统计结果中的chunk_type分布
        no_filter_stats = {}
        for doc in no_filter_results:
            metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
            chunk_type = metadata.get('chunk_type', 'unknown')
            no_filter_stats[chunk_type] = no_filter_stats.get(chunk_type, 0) + 1
        
        print("   无filter结果分布:")
        for chunk_type, count in no_filter_stats.items():
            print(f"     - {chunk_type}: {count} 个")
        
        # 测试2：image_text filter搜索
        print("\n测试2：image_text filter搜索")
        try:
            image_text_filter_results = vector_store.similarity_search(
                test_query, 
                k=100,
                filter={'chunk_type': 'image_text'}
            )
            print(f"   image_text filter搜索结果数量: {len(image_text_filter_results)}")
            
            # 统计结果中的chunk_type分布
            image_text_filter_stats = {}
            for doc in image_text_filter_results:
                metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
                chunk_type = metadata.get('chunk_type', 'unknown')
                image_text_filter_stats[chunk_type] = image_text_filter_stats.get(chunk_type, 0) + 1
            
            print("   image_text filter结果分布:")
            for chunk_type, count in image_text_filter_stats.items():
                print(f"     - {chunk_type}: {count} 个")
                
        except Exception as e:
            print(f"   image_text filter搜索失败: {e}")
            return False
        
        # 测试3：text filter搜索（对比）
        print("\n测试3：text filter搜索（对比）")
        try:
            text_filter_results = vector_store.similarity_search(
                test_query, 
                k=100,
                filter={'chunk_type': 'text'}
            )
            print(f"   text filter搜索结果数量: {len(text_filter_results)}")
            
            # 统计结果中的chunk_type分布
            text_filter_stats = {}
            for doc in text_filter_results:
                metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
                chunk_type = metadata.get('chunk_type', 'unknown')
                text_filter_stats[chunk_type] = text_filter_stats.get(chunk_type, 0) + 1
            
            print("   text filter结果分布:")
            for chunk_type, count in text_filter_stats.items():
                print(f"     - {chunk_type}: {count} 个")
                
        except Exception as e:
            print(f"   text filter搜索失败: {e}")
            return False
        
        # 8. 分析为什么image_text filter返回0个结果
        print("\n" + "="*80)
        print("分析为什么image_text filter返回0个结果")
        print("="*80)
        
        # 检查无filter结果中image_text的数量
        image_text_in_no_filter = no_filter_stats.get('image_text', 0)
        print(f"无filter结果中image_text数量: {image_text_in_no_filter}")
        
        # 检查image_text filter结果数量
        image_text_filter_count = len(image_text_filter_results)
        print(f"image_text filter结果数量: {image_text_filter_count}")
        
        # 分析原因
        if image_text_in_no_filter == 0:
            print("原因分析：无filter搜索就没有找到image_text类型，说明向量相似度搜索本身就没有找到image_text文档")
            print("这不是filter的问题，而是向量搜索的问题")
        elif image_text_filter_count == 0:
            print("原因分析：无filter搜索找到了image_text类型，但filter后返回0个")
            print("这可能是filter的问题，或者是向量搜索与filter的兼容性问题")
        else:
            print("image_text filter工作正常")
        
        # 9. 结论
        print("\n" + "="*80)
        print("测试结论")
        print("="*80)
        
        if image_text_filter_count == 0:
            if image_text_in_no_filter == 0:
                print("结论：image_text filter返回0个结果，不是因为filter不工作")
                print("而是因为向量相似度搜索本身就没有找到image_text类型的文档")
                print("建议：需要检查向量搜索的配置或image_text文档的向量化质量")
            else:
                print("结论：image_text filter可能存在问题")
                print("建议：需要进一步调试filter功能")
        else:
            print("结论：image_text filter工作正常")
        
        print("\n" + "="*80)
        print("测试完成")
        print("="*80)
        
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_image_text_filter()
    if success:
        print("\n测试通过")
    else:
        print("\n测试失败")
