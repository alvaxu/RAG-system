'''
程序说明：
## 1. 调试文档结构
## 2. 检查返回的文档对象类型和属性
## 3. 分析为什么metadata和page_content属性丢失
'''

import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from V501_unified_main import UnifiedRAGSystem
from config.settings import Settings

def debug_document_structure():
    """调试文档结构"""
    
    print("🔍 调试文档结构")
    print("=" * 60)
    
    try:
        # 加载配置
        settings = Settings.load_from_file('config.json')
        
        # 初始化RAG系统
        rag_system = UnifiedRAGSystem(settings)
        
        if not rag_system.qa_system:
            print("❌ QA系统未初始化，无法测试")
            return False
        
        # 测试问题
        question = "请显示图4"
        print(f"问题: {question}")
        
        # 提问
        result = rag_system.ask_question(question, use_memory=False)
        
        if result['success']:
            sources = result.get('sources', [])
            print(f"✅ 提问成功")
            print(f"📊 来源数量: {len(sources)}")
            
            # 详细检查每个来源
            for i, source in enumerate(sources, 1):
                print(f"\n来源 {i}:")
                
                # 检查对象类型
                print(f"  🏷️ 对象类型: {type(source)}")
                print(f"  🏷️ 对象类名: {source.__class__.__name__}")
                
                # 检查所有属性
                print(f"  📋 所有属性:")
                for attr in dir(source):
                    if not attr.startswith('_'):
                        try:
                            value = getattr(source, attr)
                            if callable(value):
                                print(f"    {attr}: <method>")
                            else:
                                print(f"    {attr}: {repr(value)[:100]}")
                        except Exception as e:
                            print(f"    {attr}: <error: {e}>")
                
                # 检查是否有metadata属性
                if hasattr(source, 'metadata'):
                    print(f"  ✅ 有metadata属性")
                    metadata = source.metadata
                    print(f"  📄 metadata类型: {type(metadata)}")
                    print(f"  📄 metadata内容: {metadata}")
                else:
                    print(f"  ❌ 没有metadata属性")
                
                # 检查是否有page_content属性
                if hasattr(source, 'page_content'):
                    print(f"  ✅ 有page_content属性")
                    content = source.page_content
                    print(f"  📝 page_content类型: {type(content)}")
                    print(f"  📝 page_content内容: {content[:200]}...")
                else:
                    print(f"  ❌ 没有page_content属性")
                
                # 尝试转换为字典
                try:
                    if hasattr(source, '__dict__'):
                        print(f"  📋 __dict__内容: {source.__dict__}")
                    else:
                        print(f"  ❌ 没有__dict__属性")
                except Exception as e:
                    print(f"  ❌ 访问__dict__失败: {e}")
                
                # 尝试转换为字符串
                try:
                    str_repr = str(source)
                    print(f"  📝 字符串表示: {str_repr[:200]}...")
                except Exception as e:
                    print(f"  ❌ 字符串转换失败: {e}")
                
                # 检查是否是字典
                if isinstance(source, dict):
                    print(f"  ✅ 是字典类型")
                    for key, value in source.items():
                        print(f"    {key}: {repr(value)[:100]}")
                else:
                    print(f"  ❌ 不是字典类型")
            
            # 总结
            print(f"\n📋 调试总结:")
            print("-" * 40)
            print(f"文档对象类型: {type(sources[0]) if sources else 'None'}")
            print(f"文档对象类名: {sources[0].__class__.__name__ if sources else 'None'}")
            
            return True
            
        else:
            print(f"❌ 提问失败: {result.get('error', '未知错误')}")
            return False
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_document_structure()
