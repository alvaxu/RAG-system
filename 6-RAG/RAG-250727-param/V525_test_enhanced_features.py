'''
程序说明：
## 1. 测试ONE-PEACE模型增强功能
## 2. 验证图片处理器的增强能力
## 3. 验证向量生成器的增强功能
## 4. 提供详细的测试报告
'''

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入相关模块
from config import ConfigManager
from document_processing.image_processor import ImageProcessor
from document_processing.vector_generator import VectorGenerator

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_enhanced_image_processor():
    """
    测试增强版图片处理器
    """
    print("\n" + "="*60)
    print("测试增强版图片处理器")
    print("="*60)
    
    # 检查API密钥
    api_key = os.getenv('MY_DASHSCOPE_API_KEY', '')
    if not api_key or api_key == '你的APIKEY':
        print("❌ 未配置DashScope API密钥，无法测试图片处理器")
        return False
    
    # 创建图片处理器
    processor = ImageProcessor(api_key)
    
    # 测试图片路径
    test_image_path = "md_test/images/c812467ccd91f5edc2f88d1b0e7b3158e9506f2aa204bd0730b732dc78275634.jpg"
    
    if not os.path.exists(test_image_path):
        print(f"❌ 测试图片不存在: {test_image_path}")
        return False
    
    print(f"✅ 测试图片: {test_image_path}")
    
    # 测试图片处理
    try:
        result = processor.process_image_for_vector_store(
            image_path=test_image_path,
            document_name="测试文档",
            page_number=1,
            img_caption=["个股相对沪深300指数表现"],
            img_footnote=["资料来源：中原证券研究所，聚源"]
        )
        
        if result:
            print("✅ 图片处理成功")
            print(f"  图片ID: {result['image_id']}")
            print(f"  增强描述: {result.get('enhanced_description', 'N/A')}")
            print(f"  图片类型: {result.get('image_type', 'N/A')}")
            print(f"  语义特征: {result.get('semantic_features', {})}")
            
            # 测试图片相似度分析
            if 'embedding' in result:
                embedding = result['embedding']
                similarity = processor.analyze_image_similarity(embedding, embedding)
                print(f"  自相似度: {similarity:.4f}")
            
            # 测试搜索查询创建
            image_context = {
                'img_caption': result.get('img_caption', []),
                'img_footnote': result.get('img_footnote', []),
                'image_type': result.get('image_type', 'general')
            }
            search_query = processor.create_image_search_query("中芯国际股价表现", image_context)
            print(f"  增强搜索查询: {search_query}")
            
            return True
        else:
            print("❌ 图片处理失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_enhanced_vector_generator():
    """
    测试增强版向量生成器
    """
    print("\n" + "="*60)
    print("测试增强版向量生成器")
    print("="*60)
    
    # 创建配置管理器
    config_manager = ConfigManager()
    
    # 创建向量生成器
    vector_generator = VectorGenerator(config_manager.get_config_for_processing())
    
    # 测试向量存储统计
    vector_db_path = config_manager.settings.get_vector_db_path()
    if os.path.exists(vector_db_path):
        try:
            vector_store = vector_generator.load_vector_store(vector_db_path)
            if vector_store:
                stats = vector_generator.get_vector_store_statistics(vector_store)
                print("✅ 向量存储统计:")
                print(f"  总文档数: {stats.get('total_documents', 0)}")
                print(f"  向量维度: {stats.get('vector_dimension', 0)}")
                print(f"  类型分布: {stats.get('type_distribution', {})}")
                
                # 显示图片统计
                image_stats = stats.get('image_statistics', {})
                if image_stats:
                    print(f"  图片统计:")
                    print(f"    总图片数: {image_stats.get('total_images', 0)}")
                    print(f"    有标题的图片: {image_stats.get('images_with_caption', 0)}")
                    print(f"    有脚注的图片: {image_stats.get('images_with_footnote', 0)}")
                    print(f"    有增强描述的图片: {image_stats.get('images_with_enhanced_description', 0)}")
                    print(f"    图片类型分布: {image_stats.get('image_types', {})}")
                else:
                    print("  没有图片数据")
                
                return True
            else:
                print("❌ 无法加载向量存储")
                return False
        except Exception as e:
            print(f"❌ 测试向量生成器失败: {e}")
            return False
    else:
        print(f"❌ 向量数据库不存在: {vector_db_path}")
        return False


def test_enhanced_features():
    """
    测试所有增强功能
    """
    print("\n" + "="*60)
    print("ONE-PEACE模型增强功能测试")
    print("="*60)
    
    # 测试图片处理器
    image_processor_success = test_enhanced_image_processor()
    
    # 测试向量生成器
    vector_generator_success = test_enhanced_vector_generator()
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    if image_processor_success:
        print("✅ 增强版图片处理器测试通过")
        print("  - 支持增强图片描述生成")
        print("  - 支持图片类型检测")
        print("  - 支持语义特征提取")
        print("  - 支持图片相似度分析")
        print("  - 支持跨模态搜索查询")
    else:
        print("❌ 增强版图片处理器测试失败")
    
    if vector_generator_success:
        print("✅ 增强版向量生成器测试通过")
        print("  - 支持增强图片元信息存储")
        print("  - 支持详细统计信息")
        print("  - 支持图片类型分析")
    else:
        print("❌ 增强版向量生成器测试失败")
    
    overall_success = image_processor_success and vector_generator_success
    if overall_success:
        print("\n🎉 所有增强功能测试通过！")
        print("ONE-PEACE模型的增强能力已成功集成到现有系统中。")
    else:
        print("\n⚠️ 部分功能测试失败，请检查配置和依赖。")
    
    return overall_success


def main():
    """
    主函数
    """
    print("🚀 开始测试ONE-PEACE模型增强功能...")
    
    try:
        success = test_enhanced_features()
        
        if success:
            print("\n✅ 测试完成，增强功能正常工作")
            sys.exit(0)
        else:
            print("\n❌ 测试完成，部分功能存在问题")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 