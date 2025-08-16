#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试第五层召回策略的各个子策略
验证同义词、概念、相关词、领域扩展召回是否都在工作
"""

import sys
import os
import logging

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 设置工作目录
os.chdir(project_root)

from v2.config.v2_config import V2ConfigManager
from v2.core.text_engine import TextEngine
from v2.core.document_loader import DocumentLoader
from document_processing.vector_generator import VectorGenerator

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_layer5_strategies():
    """测试第五层的各个召回策略"""
    
    print("🔍 开始测试第五层召回策略...")
    
    try:
        # 1. 初始化配置
        print("1. 初始化配置...")
        config_manager = V2ConfigManager()
        v2_config = config_manager.config
        
        print(f"📋 文本引擎配置: {v2_config.text_engine}")
        
        # 2. 初始化向量数据库
        print("2. 初始化向量数据库...")
        
        # 检查向量数据库路径
        vector_db_path = os.path.join(project_root, "central", "vector_db")
        if not os.path.exists(vector_db_path):
            print(f"❌ 向量数据库路径不存在: {vector_db_path}")
            return
        
        print(f"✅ 向量数据库路径存在: {vector_db_path}")
        
        # 创建配置字典
        config_dict = {
            'text_embedding_model': 'text-embedding-v1',
            'dashscope_api_key': ''  # 使用默认API密钥管理
        }
        
        vector_store = VectorGenerator(config_dict).load_vector_store(vector_db_path)
        print(f"✅ 向量存储加载成功: {type(vector_store)}")
        
        # 3. 初始化文档加载器
        print("3. 初始化文档加载器...")
        document_loader = DocumentLoader(vector_store)
        
        # 4. 初始化文本引擎
        print("4. 初始化文本引擎...")
        text_engine = TextEngine(
            config=v2_config.text_engine,
            vector_store=vector_store,
            document_loader=document_loader
        )
        
        print("✅ 初始化完成")
        
        # 5. 测试查询
        test_queries = [
            "中芯国际芯片制造技术",
            "半导体晶圆代工工艺",
            "集成电路设计方法"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{'='*60}")
            print(f"测试查询 {i}: {query}")
            print(f"{'='*60}")
            
            # 执行查询
            result = text_engine.process_query(query)
            
            if result.success:
                print(f"✅ 查询成功，返回 {len(result.results)} 个结果")
                
                # 分析第五层的结果
                layer5_results = []
                for doc_result in result.results:
                    strategy = doc_result.get('search_strategy', '')
                    if strategy.startswith('expansion_'):
                        layer5_results.append(doc_result)
                
                print(f"🔍 第五层结果数量: {len(layer5_results)}")
                
                # 统计各个策略的结果
                strategy_counts = {}
                for result in layer5_results:
                    strategy = result.get('search_strategy', '')
                    strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
                
                print("📊 第五层各策略结果统计:")
                for strategy, count in strategy_counts.items():
                    print(f"  {strategy}: {count} 个")
                
                # 显示前几个结果的详细信息
                print(f"\n📋 前3个第五层结果详情:")
                for i, result in enumerate(layer5_results[:3], 1):
                    print(f"  结果 {i}:")
                    print(f"    策略: {result.get('search_strategy', 'N/A')}")
                    print(f"    分数: {result.get('expansion_score', 'N/A')}")
                    print(f"    内容长度: {len(result.get('content', ''))}")
                    print(f"    文档ID: {result.get('doc_id', 'N/A')}")
                    print()
                
            else:
                print(f"❌ 查询失败: {result.error_message}")
        
        print("\n🎯 测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    setup_logging()
    test_layer5_strategies()
