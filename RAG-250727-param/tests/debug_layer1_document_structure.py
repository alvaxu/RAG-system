'''
程序说明：
## 1. 检查第一层召回的Document对象结构
## 2. 验证page_content字段是否完整
## 3. 检查是否需要字段补充
'''

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_layer1_document_structure():
    """测试第一层召回的Document对象结构"""
    print("🔍 开始检查第一层召回的Document对象结构...")
    
    try:
        from v2.config.v2_config import V2ConfigManager
        from v2.core.table_engine import TableEngine
        
        # 获取配置
        config_manager = V2ConfigManager()
        table_config = config_manager.config.table_engine
        
        print(f"📋 表格引擎配置:")
        print(f"  enabled: {table_config.enabled}")
        print(f"  max_recall_results: {getattr(table_config, 'max_recall_results', '属性不存在')}")
        
        # 创建表格引擎
        table_engine = TableEngine(config=table_config)
        
        # 确保文档已加载
        if not table_engine._docs_loaded:
            table_engine._ensure_docs_loaded()
        
        print(f"📋 文档加载状态:")
        print(f"  _docs_loaded: {table_engine._docs_loaded}")
        print(f"  table_docs数量: {len(table_engine.table_docs)}")
        
        # 检查table_docs中的Document对象结构
        print(f"\n🔍 检查table_docs中的Document对象结构:")
        for i, doc in enumerate(table_engine.table_docs[:5]):  # 只检查前5个
            print(f"\n📋 Document {i+1}:")
            print(f"  类型: {type(doc)}")
            print(f"  属性: {[attr for attr in dir(doc) if not attr.startswith('_')]}")
            
            # 检查page_content字段
            if hasattr(doc, 'page_content'):
                page_content = doc.page_content
                print(f"  page_content类型: {type(page_content)}")
                print(f"  page_content长度: {len(page_content) if page_content else 0}")
                print(f"  page_content内容预览: {page_content[:100] if page_content else '空'}")
            else:
                print(f"  ❌ 缺少page_content属性")
            
            # 检查metadata字段
            if hasattr(doc, 'metadata'):
                metadata = doc.metadata
                print(f"  metadata类型: {type(metadata)}")
                if isinstance(metadata, dict):
                    print(f"  metadata键: {list(metadata.keys())}")
                    
                    # 检查metadata中是否有page_content
                    if 'page_content' in metadata:
                        meta_page_content = metadata['page_content']
                        print(f"  metadata.page_content类型: {type(meta_page_content)}")
                        print(f"  metadata.page_content长度: {len(meta_page_content) if meta_page_content else 0}")
                        print(f"  metadata.page_content内容预览: {meta_page_content[:100] if meta_page_content else '空'}")
                    else:
                        print(f"  metadata中不包含page_content字段")
                else:
                    print(f"  metadata不是字典类型: {metadata}")
            else:
                print(f"  ❌ 缺少metadata属性")
        
        # 执行第一层召回
        print(f"\n🔍 执行第一层召回...")
        test_query = "中芯国际的营业收入从2017年到2024年的变化趋势如何？"
        layer1_results = table_engine._table_structure_precise_search(test_query, top_k=5)
        
        print(f"📋 第一层召回结果:")
        print(f"  返回数量: {len(layer1_results)}")
        
        # 检查第一层召回返回的Document对象结构
        for i, result in enumerate(layer1_results):
            print(f"\n🔍 第一层召回结果 {i+1}:")
            print(f"  结果类型: {type(result)}")
            print(f"  结果键: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
            
            if 'doc' in result and result['doc']:
                doc = result['doc']
                print(f"  doc类型: {type(doc)}")
                print(f"  doc属性: {[attr for attr in dir(doc) if not attr.startswith('_')]}")
                
                # 检查page_content字段
                if hasattr(doc, 'page_content'):
                    page_content = doc.page_content
                    print(f"  doc.page_content类型: {type(page_content)}")
                    print(f"  doc.page_content长度: {len(page_content) if page_content else 0}")
                    print(f"  doc.page_content内容预览: {page_content[:100] if page_content else '空'}")
                    
                    # 如果page_content为空，检查metadata中是否有
                    if not page_content and hasattr(doc, 'metadata'):
                        metadata = doc.metadata
                        if isinstance(metadata, dict) and 'page_content' in metadata:
                            meta_page_content = metadata['page_content']
                            print(f"  🔍 metadata.page_content存在，长度: {len(meta_page_content) if meta_page_content else 0}")
                            print(f"  🔍 需要补充page_content字段！")
                else:
                    print(f"  ❌ doc缺少page_content属性")
                
                # 检查metadata字段
                if hasattr(doc, 'metadata'):
                    metadata = doc.metadata
                    print(f"  doc.metadata类型: {type(metadata)}")
                    if isinstance(metadata, dict):
                        print(f"  doc.metadata键: {list(metadata.keys())}")
                        
                        # 检查关键字段
                        key_fields = ['document_name', 'page_number', 'table_type', 'chunk_type']
                        for field in key_fields:
                            if field in metadata:
                                print(f"  doc.metadata.{field}: {metadata[field]}")
                            else:
                                print(f"  doc.metadata.{field}: 不存在")
                    else:
                        print(f"  doc.metadata不是字典类型: {metadata}")
                else:
                    print(f"  ❌ doc缺少metadata属性")
            else:
                print(f"  ❌ 结果中缺少doc字段")
        
        print(f"\n✅ 第一层召回Document对象结构检查完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_layer1_document_structure()
