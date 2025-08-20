#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试FAISS filter功能的真相验证

测试目标：
1. 深入验证FAISS是否真的支持filter功能
2. 检查filter是否真的在工作，还是只是返回了所有结果
3. 对比有filter和无filter的搜索结果差异
4. 验证filter是否真的在过滤，还是只是装饰性的
"""

import os
import sys
import time
import logging
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_faiss_filter_truth():
    """深入验证FAISS filter功能的真相"""
    print("="*80)
    print("测试FAISS filter功能的真相验证")
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
        
        print(f"   项目根目录: {project_root}")
        print(f"   配置文件路径: {config_path}")
        
        if not os.path.exists(config_path):
            print(f"  配置文件不存在: {config_path}")
            return False
        
        try:
            # 临时切换到项目根目录，确保路径解析正确
            old_cwd = os.getcwd()
            os.chdir(project_root)
            
            config = Settings.load_from_file('config.json')
            print(f"   配置文件加载成功: {config_path}")
            
            # 恢复原来的工作目录
            os.chdir(old_cwd)
            
        except Exception as e:
            print(f"   配置文件加载失败: {e}")
            os.chdir(old_cwd)
            return False
        
        # 3. 获取API密钥
        api_key = get_dashscope_api_key(config.dashscope_api_key)
        if not api_key:
            print("未找到有效的DashScope API密钥")
            return False
        
        print("配置获取成功")
        
        # 4. 初始化embeddings
        print("初始化embeddings...")
        text_embeddings = DashScopeEmbeddings(
            dashscope_api_key=api_key,
            model='text-embedding-v1'
        )
        print("text embeddings初始化成功")
        
        # 5. 加载向量数据库
        print("加载向量数据库...")
        vector_db_path = config.vector_db_dir
        
        if not os.path.exists(vector_db_path):
            print(f"向量数据库路径不存在: {vector_db_path}")
            return False
        
        print(f"向量数据库路径存在: {vector_db_path}")
        
        try:
            vector_store = FAISS.load_local(
                vector_db_path, 
                text_embeddings,
                allow_dangerous_deserialization=True
            )
            print("向量数据库加载成功")
        except Exception as e:
            print(f"向量数据库加载失败: {e}")
            return False
        
        # 6. 分析数据库结构
        print("分析数据库结构...")
        if not hasattr(vector_store, 'docstore') or not hasattr(vector_store.docstore, '_dict'):
            print("向量数据库结构不符合预期")
            return False
        
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
        
        # 7. 关键测试：验证filter是否真的在工作
        print("\n" + "="*80)
        print("关键测试：验证filter是否真的在工作")
        print("="*80)
        
        test_query = "中芯国际财务图表"
        print(f"测试查询: {test_query}")
        
        # 测试1：无filter搜索
        print("\n测试1：无filter搜索")
        try:
            no_filter_results = vector_store.similarity_search(test_query, k=50)
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
                
        except Exception as e:
            print(f"     无filter搜索失败: {e}")
            return False
        
        # 测试2：使用image filter搜索
        print("\n�� 测试2：使用image filter搜索")
        try:
            image_filter_results = vector_store.similarity_search(
                test_query, 
                k=50,
                filter={'chunk_type': 'image'}
            )
            print(f"   image filter搜索结果数量: {len(image_filter_results)}")
            
            # 统计结果中的chunk_type分布
            image_filter_stats = {}
            for doc in image_filter_results:
                metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
                chunk_type = metadata.get('chunk_type', 'unknown')
                image_filter_stats[chunk_type] = image_filter_stats.get(chunk_type, 0) + 1
            
            print("   image filter结果分布:")
            for chunk_type, count in image_filter_stats.items():
                print(f"     - {chunk_type}: {count} 个")
                
            # 关键验证：检查是否真的只返回了image类型
            non_image_count = sum(count for chunk_type, count in image_filter_stats.items() if chunk_type != 'image')
            if non_image_count == 0:
                print("    image filter真的在工作！只返回了image类型")
            else:
                print(f"     image filter没有工作！返回了 {non_image_count} 个非image类型")
                
        except Exception as e:
            print(f"     image filter搜索失败: {e}")
            return False
        
        # 测试3：使用text filter搜索
        print("\n📋 测试3：使用text filter搜索")
        try:
            text_filter_results = vector_store.similarity_search(
                test_query, 
                k=50,
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
                
            # 关键验证：检查是否真的只返回了text类型
            non_text_count = sum(count for chunk_type, count in text_filter_stats.items() if chunk_type != 'text')
            if non_text_count == 0:
                print("    text filter真的在工作！只返回了text类型")
            else:
                print(f"     text filter没有工作！返回了 {non_text_count} 个非text类型")
                
        except Exception as e:
            print(f"     text filter搜索失败: {e}")
            return False
        
        # 测试4：对比分析
        print("\n�� 测试4：对比分析")
        print("   对比无filter vs image filter vs text filter:")
        print(f"   无filter: {len(no_filter_results)} 个结果")
        print(f"   image filter: {len(image_filter_results)} 个结果")
        print(f"   text filter: {len(text_filter_results)} 个结果")
        
        # 计算filter效果
        if len(no_filter_results) > 0:
            image_filter_ratio = len(image_filter_results) / len(no_filter_results)
            text_filter_ratio = len(text_filter_results) / len(no_filter_results)
            
            print(f"   image filter过滤效果: {image_filter_ratio:.2%}")
            print(f"   text filter过滤效果: {text_filter_ratio:.2%}")
            
            # 判断filter是否真的在工作
            if image_filter_ratio < 0.5 and text_filter_ratio < 0.5:
                print("    filter真的在工作！结果数量明显减少")
            elif image_filter_ratio > 0.8 and text_filter_ratio > 0.8:
                print("     filter没有工作！结果数量几乎没有减少")
            else:
                print("     filter效果不明确，需要进一步验证")
        
        # 测试5：检查FAISS索引类型
        print("\n�� 测试5：检查FAISS索引类型")
        try:
            if hasattr(vector_store, 'index'):
                faiss_index = vector_store.index
                print(f"   FAISS索引类型: {type(faiss_index).__name__}")
                print(f"   索引维度: {faiss_index.d}")
                print(f"   索引大小: {faiss_index.ntotal}")
                
                # 检查是否有filter相关属性
                filter_attrs = [attr for attr in dir(faiss_index) if 'filter' in attr.lower()]
                if filter_attrs:
                    print(f"   Filter相关属性: {filter_attrs}")
                else:
                    print("     没有发现filter相关属性")
            else:
                print("     无法获取FAISS索引信息")
                
        except Exception as e:
            print(f"     检查FAISS索引失败: {e}")
        
        # 8. 结论
        print("\n" + "="*80)
        print("  测试结论")
        print("="*80)
        
        # 基于测试结果给出结论
        if (len(image_filter_results) < len(no_filter_results) * 0.5 and 
            len(text_filter_results) < len(no_filter_results) * 0.5):
            print(" FAISS filter功能真的在工作！")
            print("   建议：可以安全使用filter功能进行chunk_type过滤")
        else:
            print(" FAISS filter功能可能没有工作！")
            print("   建议：需要检查FAISS配置或考虑其他过滤方案")
        
        print("\n" + "="*80)
        print("🎉 测试完成：FAISS filter功能真相验证完成！")
        print("="*80)
        
        return True
        
    except Exception as e:
        print(f"  测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_faiss_filter_truth()
    if success:
        print("\n 测试通过：FAISS filter功能验证完成")
    else:
        print("\n  测试失败：需要检查配置或数据库结构")