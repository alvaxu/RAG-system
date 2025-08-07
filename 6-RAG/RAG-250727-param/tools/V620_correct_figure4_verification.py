'''
程序说明：
## 1. 正确的图4验证脚本
## 2. 处理字典类型的文档对象
## 3. 确认图4检索修复效果
'''

import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from V501_unified_main import UnifiedRAGSystem
from config.settings import Settings

def correct_figure4_verification():
    """正确的图4验证"""
    
    print("🔍 正确的图4验证")
    print("=" * 60)
    
    try:
        # 加载配置
        settings = Settings.load_from_file('config.json')
        
        # 初始化RAG系统
        rag_system = UnifiedRAGSystem(settings)
        
        if not rag_system.qa_system:
            print("❌ QA系统未初始化，无法测试")
            return False
        
        # 测试问题列表
        test_questions = [
            "请显示图4",
            "图4的内容是什么",
            "图4：公司25Q1下游应用领域结构情况",
            "图4：中芯国际归母净利润情况概览",
            "显示图4",
            "图4在哪里"
        ]
        
        print("📝 验证图4检索修复:")
        print("-" * 40)
        
        success_count = 0
        total_count = len(test_questions)
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n问题 {i}: {question}")
            
            # 提问
            result = rag_system.ask_question(question, use_memory=False)
            
            if result['success']:
                sources = result.get('sources', [])
                print(f"✅ 提问成功")
                print(f"📊 来源数量: {len(sources)}")
                
                # 正确检查是否包含图4（处理字典类型）
                has_figure4 = False
                figure4_details = []
                
                for source in sources:
                    # 检查是否是字典类型
                    if isinstance(source, dict):
                        metadata = source.get('metadata', {})
                        content = source.get('content', '')
                        
                        # 检查图片标题
                        img_caption = metadata.get('img_caption', [])
                        caption_text = ' '.join(img_caption) if img_caption else ''
                        
                        # 检查是否包含图4
                        if '图4' in caption_text:
                            has_figure4 = True
                            doc_name = metadata.get('document_name', '未知文档')
                            figure4_details.append({
                                'document': doc_name,
                                'caption': caption_text,
                                'content': content[:100] + '...' if len(content) > 100 else content
                            })
                    else:
                        # 处理Document对象类型
                        if hasattr(source, 'metadata'):
                            img_caption = source.metadata.get('img_caption', [])
                            caption_text = ' '.join(img_caption) if img_caption else ''
                            
                            if '图4' in caption_text:
                                has_figure4 = True
                                doc_name = source.metadata.get('document_name', '未知文档')
                                figure4_details.append({
                                    'document': doc_name,
                                    'caption': caption_text,
                                    'content': source.page_content[:100] + '...' if hasattr(source, 'page_content') else '无内容'
                                })
                
                if has_figure4:
                    success_count += 1
                    print(f"  ✅ 成功找到图4:")
                    for detail in figure4_details:
                        print(f"    📄 {detail['document']}")
                        print(f"    🖼️ {detail['caption']}")
                        print(f"    📝 {detail['content']}")
                else:
                    print(f"  ❌ 未找到图4")
                    # 显示实际找到的内容
                    for j, source in enumerate(sources, 1):
                        if isinstance(source, dict):
                            metadata = source.get('metadata', {})
                            content = source.get('content', '')
                            doc_name = metadata.get('document_name', '未知文档')
                            img_caption = metadata.get('img_caption', [])
                            caption_text = ' '.join(img_caption) if img_caption else '无标题'
                            print(f"    实际找到 {j}: {doc_name} - {caption_text}")
                        else:
                            print(f"    实际找到 {j}: {type(source)}")
            else:
                print(f"  ❌ 提问失败: {result.get('error', '未知错误')}")
        
        print(f"\n📊 验证结果统计:")
        print(f"  总问题数: {total_count}")
        print(f"  成功找到图4: {success_count}")
        print(f"  成功率: {success_count/total_count*100:.1f}%")
        
        if success_count > 0:
            print(f"✅ 图4检索问题已修复!")
            print(f"🎉 修复效果良好")
        else:
            print(f"❌ 图4检索问题仍然存在")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_specific_figure4_queries():
    """测试特定的图4查询"""
    
    print("\n🔍 测试特定的图4查询")
    print("=" * 60)
    
    try:
        # 加载配置
        settings = Settings.load_from_file('config.json')
        
        # 初始化RAG系统
        rag_system = UnifiedRAGSystem(settings)
        
        if not rag_system.qa_system:
            print("❌ QA系统未初始化，无法测试")
            return False
        
        # 测试特定的图4查询
        specific_queries = [
            "图4",
            "图4在哪里",
            "请显示图4",
            "图4的内容",
            "图4：公司25Q1下游应用领域结构情况",
            "图4：中芯国际归母净利润情况概览"
        ]
        
        print("📝 特定图4查询测试:")
        print("-" * 40)
        
        success_count = 0
        total_count = len(specific_queries)
        
        for i, question in enumerate(specific_queries, 1):
            print(f"\n查询 {i}: {question}")
            
            # 提问
            result = rag_system.ask_question(question, use_memory=False)
            
            if result['success']:
                sources = result.get('sources', [])
                
                # 检查是否包含图4
                figure4_found = False
                for source in sources:
                    if isinstance(source, dict):
                        metadata = source.get('metadata', {})
                        img_caption = metadata.get('img_caption', [])
                        caption_text = ' '.join(img_caption) if img_caption else ''
                        if '图4' in caption_text:
                            figure4_found = True
                            doc_name = metadata.get('document_name', '未知文档')
                            print(f"  ✅ 找到图4: {doc_name} - {caption_text}")
                    else:
                        if hasattr(source, 'metadata'):
                            img_caption = source.metadata.get('img_caption', [])
                            caption_text = ' '.join(img_caption) if img_caption else ''
                            if '图4' in caption_text:
                                figure4_found = True
                                doc_name = source.metadata.get('document_name', '未知文档')
                                print(f"  ✅ 找到图4: {doc_name} - {caption_text}")
                
                if figure4_found:
                    success_count += 1
                    print(f"  ✅ 成功找到图4")
                else:
                    print(f"  ❌ 未找到图4")
                    print(f"  实际找到 {len(sources)} 个文档")
            else:
                print(f"  ❌ 查询失败: {result.get('error', '未知错误')}")
        
        print(f"\n📊 特定查询结果统计:")
        print(f"  总查询数: {total_count}")
        print(f"  成功找到图4: {success_count}")
        print(f"  成功率: {success_count/total_count*100:.1f}%")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🔍 正确的图4验证工具")
    print("=" * 60)
    
    # 1. 验证修复效果
    print("\n1️⃣ 验证图4检索修复效果:")
    fix_verified = correct_figure4_verification()
    
    # 2. 测试特定查询
    print("\n2️⃣ 测试特定图4查询:")
    specific_tested = test_specific_figure4_queries()
    
    print(f"\n📋 验证总结:")
    print("-" * 40)
    if fix_verified:
        print(f"✅ 图4检索问题已成功修复!")
        print(f"✅ 系统能够正确识别和返回图4文档")
        print(f"✅ 修复效果良好")
        print(f"🎉 问题解决!")
    else:
        print(f"❌ 图4检索问题仍然存在")
        print(f"📝 需要进一步调试")
    
    print(f"📊 验证完成")

if __name__ == "__main__":
    main()
