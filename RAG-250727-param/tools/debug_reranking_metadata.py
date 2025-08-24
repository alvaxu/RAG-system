#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
程序说明：
## 1. 调试TableRerankingService的metadata保留问题
## 2. 检查重排序过程中metadata是否丢失
## 3. 验证字段统一改造对metadata的影响
'''

import sys
import os
import logging
from pathlib import Path

# 修复路径问题，添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def test_table_reranking_service():
    """测试TableRerankingService的metadata保留"""
    try:
        from v2.core.table_engine import TableEngine
        from v2.config.v2_config import V2ConfigManager
        
        print("🔍 测试TableRerankingService的metadata保留")
        print("=" * 60)
        
        # 加载配置
        config_manager = V2ConfigManager()
        table_config = config_manager.get_engine_config('table_engine')
        
        if not table_config:
            print("❌ 无法获取table_engine配置")
            return
        
        print(f"✅ 获取到table_engine配置")
        print(f"配置内容: {table_config}")
        
        # 创建TableEngine实例（跳过初始加载）
        table_engine = TableEngine(
            config=table_config,
            skip_initial_load=True
        )
        
        # 手动初始化
        table_engine._initialize()
        
        print(f"✅ TableEngine初始化完成")
        print(f"引擎状态: {table_engine.is_ready()}")
        
        # 检查重排序服务
        if not table_engine.table_reranking_service:
            print("❌ 重排序服务未初始化")
            return
        
        print(f"✅ 重排序服务已初始化")
        print(f"服务名称: {table_engine.table_reranking_service.get_service_name()}")
        
        # 创建测试候选文档
        test_candidates = []
        
        # 模拟从向量数据库返回的文档
        class MockDocument:
            def __init__(self, metadata, page_content):
                self.metadata = metadata
                self.page_content = page_content
        
        # 创建测试文档
        test_doc = MockDocument(
            metadata={
                'document_name': '测试文档',
                'page_number': 1,
                'chunk_type': 'table',
                'table_id': 'test_table_001',
                'table_type': '数据表格',
                'table_title': '测试表格',
                'table_summary': '这是一个测试表格',
                'table_headers': ['列1', '列2'],
                'table_row_count': 2,
                'table_column_count': 2,
                'processed_table_content': '列1 | 列2\n数据1 | 数据2',
                'page_content': '<table><tr><td>列1</td><td>列2</td></tr><tr><td>数据1</td><td>数据2</td></tr></table>'
            },
            page_content='<table><tr><td>列1</td><td>列2</td></tr><tr><td>数据1</td><td>数据2</td></tr></table>'
        )
        
        # 构造候选文档格式
        test_candidate = {
            'doc': test_doc,
            'content': test_doc.page_content,
            'metadata': test_doc.metadata,
            'score': 0.85,
            'source': 'vector_search',
            'layer': 2
        }
        
        test_candidates.append(test_candidate)
        
        print(f"\n📋 测试候选文档:")
        print(f"文档类型: {type(test_candidate['doc'])}")
        print(f"metadata: {test_candidate['metadata']}")
        print(f"document_name: {test_candidate['metadata'].get('document_name', '未找到')}")
        print(f"page_number: {test_candidate['metadata'].get('page_number', '未找到')}")
        
        # 测试重排序服务
        print(f"\n🔍 测试重排序服务...")
        
        try:
            # 调用重排序服务
            reranked_results = table_engine.table_reranking_service.rerank(
                query="测试查询",
                candidates=test_candidates
            )
            
            print(f"✅ 重排序完成，返回 {len(reranked_results)} 个结果")
            
            # 检查重排序结果的metadata
            for i, result in enumerate(reranked_results):
                print(f"\n📊 重排序结果 {i+1}:")
                print(f"结果类型: {type(result)}")
                print(f"结果键: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
                
                if 'doc' in result:
                    doc = result['doc']
                    print(f"doc类型: {type(doc)}")
                    
                    if hasattr(doc, 'metadata'):
                        print(f"doc.metadata: {doc.metadata}")
                        print(f"document_name: {doc.metadata.get('document_name', '未找到')}")
                        print(f"page_number: {doc.metadata.get('page_number', '未找到')}")
                    else:
                        print("❌ doc没有metadata属性")
                        
                    if hasattr(doc, 'page_content'):
                        print(f"page_content长度: {len(doc.page_content)}")
                    else:
                        print("❌ doc没有page_content属性")
                else:
                    print("❌ 结果中没有doc字段")
                
                # 检查其他字段
                for key in ['score', 'table_info', 'rerank_source']:
                    if key in result:
                        print(f"{key}: {result[key]}")
                    else:
                        print(f"❌ 缺少{key}字段")
            
        except Exception as e:
            print(f"❌ 重排序测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试完整的查询流程
        print(f"\n🔍 测试完整的查询流程...")
        
        try:
            # 模拟一个简单的查询
            query = "测试查询"
            results = table_engine._enhanced_vector_search(query, top_k=5)
            
            print(f"✅ 向量搜索完成，返回 {len(results)} 个结果")
            
            # 检查搜索结果的metadata
            for i, result in enumerate(results):
                print(f"\n📊 搜索结果 {i+1}:")
                print(f"结果类型: {type(result)}")
                print(f"结果键: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
                
                if 'doc' in result:
                    doc = result['doc']
                    print(f"doc类型: {type(doc)}")
                    
                    if hasattr(doc, 'metadata'):
                        print(f"doc.metadata: {doc.metadata}")
                        print(f"document_name: {doc.metadata.get('document_name', '未找到')}")
                        print(f"page_number: {doc.metadata.get('page_number', '未找到')}")
                    else:
                        print("❌ doc没有metadata属性")
                        
                    if hasattr(doc, 'page_content'):
                        print(f"page_content长度: {len(doc.page_content)}")
                    else:
                        print("❌ doc没有page_content属性")
                else:
                    print("❌ 结果中没有doc字段")
                
                # 检查其他字段
                for key in ['score', 'source', 'layer']:
                    if key in result:
                        print(f"{key}: {result[key]}")
                    else:
                        print(f"❌ 缺少{key}字段")
            
        except Exception as e:
            print(f"❌ 向量搜索测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\n✅ 测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_table_reranking_service()
