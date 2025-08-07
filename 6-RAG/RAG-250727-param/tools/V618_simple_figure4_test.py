'''
程序说明：
## 1. 简单的图4测试脚本
## 2. 直接检查返回的文档内容
## 3. 确认图4检索是否真的修复了
'''

import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from V501_unified_main import UnifiedRAGSystem
from config.settings import Settings

def simple_figure4_test():
    """简单的图4测试"""
    
    print("🔍 简单图4测试")
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
                
                # 检查是否有metadata属性
                if hasattr(source, 'metadata'):
                    print(f"  ✅ 有metadata属性")
                    metadata = source.metadata
                    
                    # 检查文档名称
                    doc_name = metadata.get('document_name', '未知文档')
                    print(f"  📄 文档名称: {doc_name}")
                    
                    # 检查文档类型
                    chunk_type = metadata.get('chunk_type', '未知类型')
                    print(f"  🏷️ 文档类型: {chunk_type}")
                    
                    # 检查图片标题
                    img_caption = metadata.get('img_caption', [])
                    if img_caption:
                        print(f"  🖼️ 图片标题: {img_caption}")
                        
                        # 检查是否包含图4
                        caption_text = ' '.join(img_caption)
                        if '图4' in caption_text:
                            print(f"  ✅ 包含图4!")
                        else:
                            print(f"  ❌ 不包含图4")
                    else:
                        print(f"  ❌ 没有图片标题")
                    
                    # 检查其他元数据
                    page_number = metadata.get('page_number', '未知页码')
                    print(f"  📍 页码: {page_number}")
                    
                    # 检查图片ID
                    image_id = metadata.get('image_id', '无ID')
                    print(f"  🆔 图片ID: {image_id}")
                    
                else:
                    print(f"  ❌ 没有metadata属性")
                
                # 检查page_content
                if hasattr(source, 'page_content'):
                    content = source.page_content
                    print(f"  📝 内容长度: {len(content)}")
                    print(f"  📝 内容预览: {content[:100]}...")
                    
                    # 检查内容中是否包含图4
                    if '图4' in content:
                        print(f"  ✅ 内容中包含图4!")
                    else:
                        print(f"  ❌ 内容中不包含图4")
                else:
                    print(f"  ❌ 没有page_content属性")
            
            # 总结
            print(f"\n📋 测试总结:")
            print("-" * 40)
            
            figure4_count = 0
            for source in sources:
                if hasattr(source, 'metadata'):
                    img_caption = source.metadata.get('img_caption', [])
                    caption_text = ' '.join(img_caption) if img_caption else ''
                    if '图4' in caption_text:
                        figure4_count += 1
            
            print(f"找到图4文档数量: {figure4_count}")
            
            if figure4_count > 0:
                print(f"✅ 图4检索问题已修复!")
                print(f"🎉 系统能够正确找到图4文档")
            else:
                print(f"❌ 图4检索问题仍然存在")
            
            return figure4_count > 0
            
        else:
            print(f"❌ 提问失败: {result.get('error', '未知错误')}")
            return False
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    simple_figure4_test()
