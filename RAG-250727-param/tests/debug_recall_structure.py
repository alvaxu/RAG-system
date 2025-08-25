'''
程序说明：
## 1. 检查recall阶段返回的结果结构
## 2. 验证Document对象是否完整
## 3. 检查是否需要补全信息
'''

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_recall_structure():
    """测试recall阶段返回的结果结构"""
    print("🔍 开始检查recall阶段返回的结果结构...")
    
    try:
        from v2.config.v2_config import V2ConfigManager
        from v2.core.table_engine import TableEngine
        
        # 获取配置
        config_manager = V2ConfigManager()
        table_config = config_manager.config.table_engine
        
        print(f"📋 表格引擎配置:")
        print(f"  enabled: {table_config.enabled}")
        print(f"  max_recall_results: {table_config.max_recall_results}")
        print(f"  max_results: {table_config.max_results}")
        
        # 创建表格引擎
        table_engine = TableEngine(config=table_config)
        
        # 测试查询
        test_query = "中芯国际的营业收入从2017年到2024年的变化趋势如何？"
        print(f"\n🔍 测试查询: {test_query}")
        
        # 执行第一层召回
        print("\n📋 执行第一层召回（表格结构精确匹配）...")
        layer1_results = table_engine._table_structure_precise_search(test_query, top_k=5)
        
        print(f"第一层召回结果数量: {len(layer1_results)}")
        for i, result in enumerate(layer1_results):
            print(f"\n🔍 第一层结果 {i+1}:")
            print(f"  类型: {type(result)}")
            print(f"  键: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
            
            if isinstance(result, dict) and 'doc' in result:
                doc = result['doc']
                print(f"  doc类型: {type(doc)}")
                print(f"  doc属性: {[attr for attr in dir(doc) if not attr.startswith('_')]}")
                
                if hasattr(doc, 'metadata'):
                    metadata = doc.metadata
                    print(f"  metadata类型: {type(metadata)}")
                    print(f"  metadata键: {list(metadata.keys()) if isinstance(metadata, dict) else 'N/A'}")
                    print(f"  document_name: {metadata.get('document_name', '未找到')}")
                    print(f"  page_number: {metadata.get('page_number', '未找到')}")
                    print(f"  chunk_type: {metadata.get('chunk_type', '未找到')}")
                    print(f"  table_id: {metadata.get('table_id', '未找到')}")
                    print(f"  page_content长度: {len(getattr(doc, 'page_content', ''))}")
                else:
                    print(f"  ❌ doc缺少metadata属性")
            else:
                print(f"  ❌ 结果缺少doc键")
        
        # 执行第二层召回
        print("\n📋 执行第二层召回（向量语义搜索）...")
        layer2_results = table_engine._enhanced_vector_search(test_query, top_k=5)
        
        print(f"第二层召回结果数量: {len(layer2_results)}")
        for i, result in enumerate(layer2_results):
            print(f"\n🔍 第二层结果 {i+1}:")
            print(f"  类型: {type(result)}")
            print(f"  键: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
            
            if isinstance(result, dict) and 'doc' in result:
                doc = result['doc']
                print(f"  doc类型: {type(doc)}")
                print(f"  doc属性: {[attr for attr in dir(doc) if not attr.startswith('_')]}")
                
                if hasattr(doc, 'metadata'):
                    metadata = doc.metadata
                    print(f"  metadata类型: {type(metadata)}")
                    print(f"  metadata键: {list(metadata.keys()) if isinstance(metadata, dict) else 'N/A'}")
                    print(f"  document_name: {metadata.get('document_name', '未找到')}")
                    print(f"  page_number: {metadata.get('page_number', '未找到')}")
                    print(f"  chunk_type: {metadata.get('chunk_type', '未找到')}")
                    print(f"  table_id: {metadata.get('table_id', '未找到')}")
                    print(f"  page_content长度: {len(getattr(doc, 'page_content', ''))}")
                else:
                    print(f"  ❌ doc缺少metadata属性")
            else:
                print(f"  ❌ 结果缺少doc键")
        
        print("\n✅ recall阶段结构检查完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_recall_structure()
