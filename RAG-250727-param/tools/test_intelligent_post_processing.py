'''
程序说明：
## 1. 智能后处理引擎测试脚本
## 2. 测试关键词提取、结果过滤等核心功能
## 3. 模拟真实的LLM答案和搜索结果数据
## 4. 验证过滤逻辑和相关性计算
'''

import sys
import os
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v2.core.intelligent_post_processing_engine import IntelligentPostProcessingEngine, FilteringResult
from v2.config.v2_config import IntelligentPostProcessingConfig


def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def create_test_config():
    """创建测试配置"""
    return IntelligentPostProcessingConfig(
        enable_image_filtering=True,
        enable_text_filtering=True,
        enable_table_filtering=True,
        max_images_to_keep=2,
        max_texts_to_keep=2,
        max_tables_to_keep=1,
        keyword_match_threshold=0.6
    )


def create_test_data():
    """创建测试数据"""
    # 模拟LLM答案
    llm_answer = """
    根据查询结果，我找到了以下相关信息：
    
    图4：中芯国际归母净利润情况概览 - 这是一张柱状图，展示了中芯国际从2020年到2023年的归母净利润变化趋势。
    从图表可以看出，中芯国际的净利润在2021年达到峰值，随后在2022年有所下降，2023年又有所回升。
    
    此外，还有相关的财务数据表格显示，中芯国际在半导体行业具有重要地位，其营收和利润表现良好。
    """
    
    # 模拟搜索结果
    all_results = {
        'image': [
            {
                'id': 'img_001',
                'title': '图4：中芯国际归母净利润情况概览',
                'caption': '中芯国际归母净利润柱状图',
                'enhanced_description': '展示2020-2023年净利润变化趋势的柱状图',
                'document_name': '中芯国际财务报告2023.pdf',
                'page_number': 15
            },
            {
                'id': 'img_002',
                'title': '图4：中芯国际营收情况',
                'caption': '中芯国际营收折线图',
                'enhanced_description': '展示2020-2023年营收变化趋势的折线图',
                'document_name': '中芯国际财务报告2023.pdf',
                'page_number': 16
            },
            {
                'id': 'img_003',
                'title': '图5：中芯国际市场份额',
                'caption': '中芯国际市场份额饼图',
                'enhanced_description': '展示中芯国际在半导体市场的份额分布',
                'document_name': '行业分析报告.pdf',
                'page_number': 8
            },
            {
                'id': 'img_004',
                'title': '图4：中芯国际研发投入',
                'caption': '中芯国际研发投入柱状图',
                'enhanced_description': '展示2020-2023年研发投入变化趋势',
                'document_name': '中芯国际年报2023.pdf',
                'page_number': 22
            }
        ],
        'text': [
            {
                'id': 'text_001',
                'title': '中芯国际公司简介',
                'content': '中芯国际集成电路制造有限公司是中国大陆规模最大、技术最先进的集成电路制造企业之一。',
                'document_name': '公司介绍.pdf',
                'page_number': 1
            },
            {
                'id': 'text_002',
                'title': '半导体行业发展趋势',
                'content': '近年来，半导体行业在全球范围内快速发展，中芯国际作为行业重要参与者，表现突出。',
                'document_name': '行业分析.pdf',
                'page_number': 5
            },
            {
                'id': 'text_003',
                'title': '财务分析方法',
                'content': '分析公司财务表现时，需要综合考虑营收、利润、研发投入等多个维度。',
                'document_name': '财务分析指南.pdf',
                'page_number': 12
            }
        ],
        'table': [
            {
                'id': 'table_001',
                'title': '中芯国际财务数据汇总',
                'content': '包含营收、净利润、研发投入等关键财务指标',
                'headers': ['年份', '营收(亿元)', '净利润(亿元)', '研发投入(亿元)'],
                'document_name': '财务数据表.pdf',
                'page_number': 10
            },
            {
                'id': 'table_002',
                'title': '行业对比数据',
                'content': '中芯国际与同行业其他公司的对比数据',
                'headers': ['公司名称', '市场份额', '营收规模', '技术实力'],
                'document_name': '行业对比.pdf',
                'page_number': 15
            }
        ]
    }
    
    return llm_answer, all_results


def test_keyword_extraction(engine):
    """测试关键词提取功能"""
    print("\n=== 测试关键词提取功能 ===")
    
    llm_answer = "图4：中芯国际归母净利润情况概览，这是一张柱状图，展示了中芯国际从2020年到2023年的归母净利润变化趋势。"
    
    keywords = engine._extract_keywords_from_llm(llm_answer)
    print(f"提取的关键词: {keywords}")
    
    expected_keywords = ['中芯国际归母净利润情况概览', '中芯国际', '柱状图', '2020年到2023年', '净利润']
    
    for keyword in expected_keywords:
        if keyword in keywords:
            print(f"✅ 关键词 '{keyword}' 提取成功")
        else:
            print(f"❌ 关键词 '{keyword}' 提取失败")
    
    return keywords


def test_image_filtering(engine):
    """测试图片过滤功能"""
    print("\n=== 测试图片过滤功能 ===")
    
    # 创建测试图片数据
    test_images = [
        {
            'id': 'img_001',
            'title': '图4：中芯国际归母净利润情况概览',
            'caption': '中芯国际归母净利润柱状图',
            'enhanced_description': '展示2020-2023年净利润变化趋势的柱状图'
        },
        {
            'id': 'img_002',
            'title': '图4：中芯国际营收情况',
            'caption': '中芯国际营收折线图',
            'enhanced_description': '展示2020-2023年营收变化趋势的折线图'
        },
        {
            'id': 'img_003',
            'title': '图5：中芯国际市场份额',
            'caption': '中芯国际市场份额饼图',
            'enhanced_description': '展示中芯国际在半导体市场的份额分布'
        }
    ]
    
    keywords = ['中芯国际', '净利润', '柱状图']
    
    filtered_images = engine._filter_images(test_images, keywords)
    print(f"原始图片数量: {len(test_images)}")
    print(f"过滤后图片数量: {len(filtered_images)}")
    
    for img in filtered_images:
        print(f"✅ 保留图片: {img['title']}")
    
    return filtered_images


def test_text_filtering(engine):
    """测试文本过滤功能"""
    print("\n=== 测试文本过滤功能 ===")
    
    # 创建测试文本数据
    test_texts = [
        {
            'id': 'text_001',
            'title': '中芯国际公司简介',
            'content': '中芯国际集成电路制造有限公司是中国大陆规模最大、技术最先进的集成电路制造企业之一。'
        },
        {
            'id': 'text_002',
            'title': '半导体行业发展趋势',
            'content': '近年来，半导体行业在全球范围内快速发展，中芯国际作为行业重要参与者，表现突出。'
        },
        {
            'id': 'text_003',
            'title': '财务分析方法',
            'content': '分析公司财务表现时，需要综合考虑营收、利润、研发投入等多个维度。'
        }
    ]
    
    keywords = ['中芯国际', '半导体', '财务']
    
    filtered_texts = engine._filter_texts(test_texts, keywords)
    print(f"原始文本数量: {len(test_texts)}")
    print(f"过滤后文本数量: {len(filtered_texts)}")
    
    for text in filtered_texts:
        print(f"✅ 保留文本: {text['title']}")
    
    return filtered_texts


def test_table_filtering(engine):
    """测试表格过滤功能"""
    print("\n=== 测试表格过滤功能 ===")
    
    # 创建测试表格数据
    test_tables = [
        {
            'id': 'table_001',
            'title': '中芯国际财务数据汇总',
            'content': '包含营收、净利润、研发投入等关键财务指标',
            'headers': ['年份', '营收(亿元)', '净利润(亿元)', '研发投入(亿元)']
        },
        {
            'id': 'table_002',
            'title': '行业对比数据',
            'content': '中芯国际与同行业其他公司的对比数据',
            'headers': ['公司名称', '市场份额', '营收规模', '技术实力']
        }
    ]
    
    keywords = ['中芯国际', '财务', '净利润']
    
    filtered_tables = engine._filter_tables(test_tables, keywords)
    print(f"原始表格数量: {len(test_tables)}")
    print(f"过滤后表格数量: {len(filtered_tables)}")
    
    for table in filtered_tables:
        print(f"✅ 保留图片: {table['title']}")
    
    return filtered_tables


def test_full_pipeline(engine):
    """测试完整的处理流程"""
    print("\n=== 测试完整处理流程 ===")
    
    llm_answer, all_results = create_test_data()
    
    print(f"LLM答案长度: {len(llm_answer)}")
    print(f"输入图片数量: {len(all_results['image'])}")
    print(f"输入文本数量: {len(all_results['text'])}")
    print(f"输入表格数量: {len(all_results['table'])}")
    
    # 执行智能后处理
    result = engine.process(llm_answer, all_results)
    
    print(f"\n处理结果:")
    print(f"过滤后图片数量: {len(result.filtered_images)}")
    print(f"过滤后文本数量: {len(result.filtered_texts)}")
    print(f"过滤后表格数量: {len(result.filtered_tables)}")
    
    print(f"\n过滤指标:")
    for key, value in result.filtering_metrics.items():
        print(f"  {key}: {value}")
    
    # 显示保留的图片标题
    print(f"\n保留的图片:")
    for img in result.filtered_images:
        print(f"  - {img['title']}")
    
    return result


def main():
    """主测试函数"""
    print("🚀 开始测试智能后处理引擎")
    
    # 设置日志
    setup_logging()
    
    # 创建测试配置
    config = create_test_config()
    print(f"✅ 测试配置创建成功: {config}")
    
    # 创建引擎实例
    engine = IntelligentPostProcessingEngine(config)
    print("✅ 智能后处理引擎创建成功")
    
    try:
        # 测试关键词提取
        test_keyword_extraction(engine)
        
        # 测试图片过滤
        test_image_filtering(engine)
        
        # 测试文本过滤
        test_text_filtering(engine)
        
        # 测试表格过滤
        test_table_filtering(engine)
        
        # 测试完整流程
        test_full_pipeline(engine)
        
        print("\n🎉 所有测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
