'''
程序说明：

## 1. 测试图片标题精确匹配功能
## 2. 验证修改后的图片检索逻辑是否正确工作
'''

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from core.enhanced_qa_system import load_enhanced_qa_system
from config.settings import Settings

def test_exact_image_matching():
    """测试图片标题精确匹配功能"""
    
    print("🔍 测试图片标题精确匹配功能")
    print("=" * 60)
    
    try:
        # 加载配置和QA系统
        config = Settings.load_from_file('config.json')
        qa_system = load_enhanced_qa_system('./central/vector_db', config.dashscope_api_key, config=config.__dict__)
        
        # 测试用例
        test_cases = [
            "请显示图4：公司25Q1下游应用领域结构情况",
            "请显示图4：中芯国际归母净利润情况概览",
            "请显示图4",  # 不指定完整标题
            "请显示图1：中芯国际全球部署示意图"
        ]
        
        for i, test_query in enumerate(test_cases, 1):
            print(f"\n{i}. 测试查询: {test_query}")
            print("-" * 50)
            
            # 执行查询
            result = qa_system.answer_question(test_query)
            
            # 分析结果
            image_sources = [doc for doc in result['sources'] if doc['metadata'].get('chunk_type') == 'image']
            
            print(f"   检索到的图片数量: {len(image_sources)}")
            
            if image_sources:
                for j, img_doc in enumerate(image_sources, 1):
                    caption = img_doc['metadata'].get('img_caption', [])
                    caption_text = ' '.join(caption) if caption else '无标题'
                    doc_name = img_doc['metadata'].get('document_name', '未知文档')
                    print(f"   {j}. 图片标题: {caption_text}")
                    print(f"      文档来源: {doc_name}")
            else:
                print("   未找到匹配的图片")
            
            print()
        
        print("✅ 测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_exact_image_matching()
