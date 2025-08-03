#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import Settings
from document_processing.vector_generator import VectorGenerator
from core.enhanced_qa_system import EnhancedQASystem
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_retrieval_logic():
    """测试RAG系统的检索逻辑"""
    
    print("=" * 60)
    print("RAG系统检索逻辑测试")
    print("=" * 60)
    
    try:
        # 1. 加载配置
        settings = Settings.load_from_file("config.json")
        
        # 2. 初始化向量生成器
        vector_generator = VectorGenerator(settings)
        
        # 3. 加载向量存储
        vector_store = vector_generator.load_vector_store(settings.vector_db_dir)
        
        if vector_store is None:
            logger.error("无法加载向量存储")
            return
        
        # 4. 初始化QA系统
        qa_system = EnhancedQASystem(
            vector_store=vector_store,
            api_key=settings.dashscope_api_key,
            config=settings.to_dict()
        )
        
        # 5. 测试检索逻辑
        test_questions = [
            "中芯国际深度研究报告讲了些什么",
            "哪三大行业特征助力中芯晶圆制造高速发展",
            "中芯国际的产能利用率如何"
        ]
        
        print(f"\n🔍 测试检索逻辑:")
        for question in test_questions:
            print(f"\n问题: {question}")
            
            # 执行初始检索
            initial_docs = qa_system._initial_retrieval(question, k=10)
            print(f"  初始检索结果: {len(initial_docs)} 个文档")
            
            # 检查文档来源
            sources = []
            for doc in initial_docs:
                source = doc.metadata.get('source', '未知来源')
                sources.append(source)
            
            print(f"  文档来源分布:")
            source_counts = {}
            for source in sources:
                source_counts[source] = source_counts.get(source, 0) + 1
            
            for source, count in source_counts.items():
                print(f"    - {source}: {count} 个文档")
            
            # 执行智能过滤
            filtered_docs = qa_system._apply_smart_filtering(question, initial_docs)
            print(f"  智能过滤后: {len(filtered_docs)} 个文档")
            
            # 检查过滤后的文档来源
            filtered_sources = []
            for doc in filtered_docs:
                source = doc.metadata.get('source', '未知来源')
                filtered_sources.append(source)
            
            print(f"  过滤后文档来源分布:")
            filtered_source_counts = {}
            for source in filtered_sources:
                filtered_source_counts[source] = filtered_source_counts.get(source, 0) + 1
            
            for source, count in filtered_source_counts.items():
                print(f"    - {source}: {count} 个文档")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    test_retrieval_logic() 