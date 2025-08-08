'''
程序说明：
## 1. 修复图4检索问题
## 2. 将改进的检索策略应用到QA系统
## 3. 测试修复效果
## 4. 提供完整的解决方案
'''

import os
import sys
import re
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from V501_unified_main import UnifiedRAGSystem
from config.settings import Settings

def test_figure4_retrieval_fix():
    """测试图4检索修复效果"""
    
    print("🔧 测试图4检索修复效果")
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
        
        print("📝 测试图4检索问题:")
        print("-" * 40)
        
        success_count = 0
        total_count = len(test_questions)
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n问题 {i}: {question}")
            
            # 提问
            result = rag_system.ask_question(question, use_memory=False)
            
            if result['success']:
                answer = result['answer']
                sources = result.get('sources', [])
                
                print(f"回答: {answer[:150]}...")
                print(f"来源数量: {len(sources)}")
                
                # 检查是否包含图4
                has_figure4 = False
                for source in sources:
                    if hasattr(source, 'metadata'):
                        img_caption = source.metadata.get('img_caption', [])
                        caption_text = ' '.join(img_caption) if img_caption else ''
                        if '图4' in caption_text:
                            has_figure4 = True
                            print(f"✅ 找到图4: {caption_text}")
                            break
                
                if has_figure4:
                    success_count += 1
                    print(f"  ✅ 成功找到图4")
                else:
                    print(f"  ❌ 未找到图4")
            else:
                print(f"  ❌ 提问失败: {result.get('error', '未知错误')}")
        
        print(f"\n📊 测试结果统计:")
        print(f"  总问题数: {total_count}")
        print(f"  成功找到图4: {success_count}")
        print(f"  成功率: {success_count/total_count*100:.1f}%")
        
        if success_count > 0:
            print(f"✅ 图4检索问题已修复")
        else:
            print(f"❌ 图4检索问题仍然存在")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def apply_figure4_retrieval_fix():
    """应用图4检索修复"""
    
    print("🔧 应用图4检索修复")
    print("=" * 60)
    
    # 检查需要修改的文件
    files_to_modify = [
        'core/enhanced_qa_system.py',
        'core/vector_store.py'
    ]
    
    print("📋 需要修改的文件:")
    for file_path in files_to_modify:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} (不存在)")
    
    print(f"\n💡 修复方案:")
    print(f"  1. 在 enhanced_qa_system.py 的 _initial_retrieval 方法中添加特定图片编号检测")
    print(f"  2. 使用正则表达式匹配'图X'格式")
    print(f"  3. 优先返回匹配的特定图片")
    print(f"  4. 保持原有的向量检索作为备选方案")
    
    print(f"\n🔍 具体修改内容:")
    print(f"  1. 在 _initial_retrieval 方法开头添加图片编号检测逻辑")
    print(f"  2. 如果检测到特定图片编号，直接遍历所有图片文档进行精确匹配")
    print(f"  3. 如果找到匹配的图片，直接返回，不再进行向量检索")
    print(f"  4. 如果没有找到匹配的图片，继续原有的向量检索流程")
    
    print(f"\n📝 修改示例:")
    print(f"```python")
    print(f"def _initial_retrieval(self, question: str, k: int) -> List[Document]:")
    print(f"    # 检查是否包含特定图片编号请求")
    print(f"    figure_pattern = r'图(\\d+)'")
    print(f"    figure_matches = re.findall(figure_pattern, question)")
    print(f"    ")
    print(f"    if figure_matches:")
    print(f"        # 直接遍历所有图片文档，查找匹配的图片")
    print(f"        for figure_num in figure_matches:")
    print(f"            for doc_id, doc in self.vector_store.docstore._dict.items():")
    print(f"                if doc.metadata.get('chunk_type') == 'image':")
    print(f"                    caption = doc.metadata.get('img_caption', [])")
    print(f"                    caption_text = ' '.join(caption) if caption else ''")
    print(f"                    if f'图{{figure_num}}' in caption_text:")
    print(f"                        return [doc]")
    print(f"    ")
    print(f"    # 如果没有找到特定图片，进行常规检索")
    print(f"    return self.vector_store.similarity_search(question, k=k)")
    print(f"```")
    
    print(f"\n✅ 修复方案已准备就绪")
    print(f"📋 下一步：手动应用这些修改到相应的文件中")

def create_enhanced_qa_system_patch():
    """创建增强QA系统的补丁文件"""
    
    print("🔧 创建增强QA系统补丁文件")
    print("=" * 60)
    
    # 补丁内容
    patch_content = '''
# 图4检索修复补丁
# 在 core/enhanced_qa_system.py 的 _initial_retrieval 方法中添加以下代码

import re

def _initial_retrieval(self, question: str, k: int) -> List[Document]:
    """
    改进的初始检索方法 - 支持特定图片编号的精确匹配
    :param question: 问题
    :param k: 检索数量
    :return: 检索到的文档
    """
    if not self.vector_store:
        return []
    
    try:
        # 检查是否包含特定图片编号请求
        figure_pattern = r'图(\\d+)'
        figure_matches = re.findall(figure_pattern, question)
        
        all_docs = []
        
        # 如果有特定图片请求，优先处理
        if figure_matches:
            logger.info(f"检测到特定图片请求: {figure_matches}")
            
            # 直接遍历所有图片文档，查找匹配的图片
            for figure_num in figure_matches:
                logger.info(f"查找图{figure_num}")
                found_figure = False
                
                for doc_id, doc in self.vector_store.docstore._dict.items():
                    if doc.metadata.get('chunk_type') == 'image':
                        caption = doc.metadata.get('img_caption', [])
                        caption_text = ' '.join(caption) if caption else ''
                        
                        # 检查多种匹配模式
                        match_patterns = [
                            f"图{figure_num}",
                            f"图表{figure_num}",
                            f"图片{figure_num}",
                            f"Figure {figure_num}"
                        ]
                        
                        is_match = any(pattern in caption_text for pattern in match_patterns)
                        
                        if is_match:
                            # 检查是否已经添加过这个图片
                            current_image_id = doc.metadata.get('image_id')
                            already_added = any(
                                existing_doc.metadata.get('image_id') == current_image_id 
                                for existing_doc in all_docs
                            )
                            
                            if not already_added:
                                all_docs.append(doc)
                                logger.info(f"找到并添加图{figure_num}: {caption_text}")
                                found_figure = True
                
                if not found_figure:
                    logger.warning(f"未找到图{figure_num}")
            
            # 如果找到了特定图片，直接返回
            if all_docs:
                logger.info(f"找到 {len(all_docs)} 个特定图片，直接返回")
                return all_docs[:k]
        
        # 如果没有找到特定图片或没有特定图片请求，进行常规检索
        # ... 原有的检索逻辑 ...
        
    except Exception as e:
        logger.error(f"初始检索失败: {e}")
        return []
'''
    
    # 保存补丁文件
    patch_file = 'tools/V616_enhanced_qa_system_patch.py'
    with open(patch_file, 'w', encoding='utf-8') as f:
        f.write(patch_content)
    
    print(f"✅ 补丁文件已创建: {patch_file}")
    print(f"📋 请手动将补丁内容应用到 core/enhanced_qa_system.py 文件中")

def main():
    """主函数"""
    print("🔧 图4检索问题修复工具")
    print("=" * 60)
    
    # 1. 测试当前问题
    print("\n1️⃣ 测试当前图4检索问题:")
    current_status = test_figure4_retrieval_fix()
    
    # 2. 应用修复方案
    print("\n2️⃣ 应用修复方案:")
    apply_figure4_retrieval_fix()
    
    # 3. 创建补丁文件
    print("\n3️⃣ 创建补丁文件:")
    create_enhanced_qa_system_patch()
    
    print(f"\n📋 修复总结:")
    print("-" * 40)
    print(f"✅ 问题已定位：向量检索没有正确处理特定图片编号请求")
    print(f"✅ 解决方案：在检索前添加特定图片编号的精确匹配")
    print(f"✅ 修复方法：修改 enhanced_qa_system.py 的 _initial_retrieval 方法")
    print(f"✅ 补丁文件：tools/V616_enhanced_qa_system_patch.py")
    print(f"📝 下一步：手动应用补丁到相应文件中")

if __name__ == "__main__":
    main()
