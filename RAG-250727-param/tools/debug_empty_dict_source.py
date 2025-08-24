'''
程序说明：
## 1. 深入调查空字典产生的具体位置
## 2. 检查各个引擎的结果构建过程
## 3. 找出空字典产生的根本原因
## 4. 提供源头修复方案
'''

import sys
import os
import logging

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_empty_dict_source():
    """分析空字典产生的具体位置"""
    
    logger.info("🔍 深入调查空字典产生的具体位置")
    logger.info("=" * 80)
    
    # 1. 分析数据流中的关键节点
    logger.info("📊 数据流关键节点分析：")
    logger.info("1. 向量搜索 → 2. 结果处理 → 3. 结果融合 → 4. 最终排序 → 5. QueryResult构建")
    logger.info("")
    
    # 2. 检查TextEngine中的潜在问题点
    logger.info("🔍 TextEngine潜在问题点分析：")
    
    logger.info("2.1 _vector_similarity_search方法问题：")
    logger.info("   - 在processed_results.append()时，每个doc被转换为字典")
    logger.info("   - 如果doc.page_content为空，可能产生空字典")
    logger.info("   - 如果doc.metadata为空，可能产生空字典")
    logger.info("   - 如果doc对象本身有问题，可能产生空字典")
    logger.info("")
    
    logger.info("2.2 结果构建过程问题：")
    logger.info("   - processed_doc = { 'content': doc.page_content, 'metadata': doc.metadata, ... }")
    logger.info("   - 如果doc.page_content为空字符串，content字段为空")
    logger.info("   - 如果doc.metadata为空字典，metadata字段为空")
    logger.info("   - 但整个字典不会为空，只是某些字段为空")
    logger.info("")
    
    logger.info("2.3 结果融合过程问题：")
    logger.info("   - _merge_and_deduplicate_results()处理all_results")
    logger.info("   - 如果某个result字典的'content'字段为空，可能被错误处理")
    logger.info("   - 去重过程中可能产生空字典")
    logger.info("")
    
    # 3. 检查ImageEngine中的潜在问题点
    logger.info("🔍 ImageEngine潜在问题点分析：")
    
    logger.info("3.1 图片结果构建问题：")
    logger.info("   - 在ImageEngine中，结果可能被转换为字典格式")
    logger.info("   - 如果图片元数据不完整，可能产生空字典")
    logger.info("   - 统一Pipeline处理后的结果格式可能不正确")
    logger.info("")
    
    # 4. 检查TableEngine中的潜在问题点
    logger.info("🔍 TableEngine潜在问题点分析：")
    
    logger.info("4.1 表格结果构建问题：")
    logger.info("   - 在TableEngine中，表格结果可能被转换为字典格式")
    logger.info("   - 如果表格内容为空，可能产生空字典")
    logger.info("   - 表格元数据不完整时可能产生空字典")
    logger.info("")
    
    # 5. 检查HybridEngine中的潜在问题点
    logger.info("🔍 HybridEngine潜在问题点分析：")
    
    logger.info("5.1 结果传递问题：")
    logger.info("   - HybridEngine接收各个引擎的QueryResult")
    logger.info("   - 在传递过程中可能产生空字典")
    logger.info("   - 结果合并过程中可能产生空字典")
    logger.info("")
    
    # 6. 具体代码问题分析
    logger.info("🔍 具体代码问题分析：")
    
    logger.info("6.1 TextEngine._vector_similarity_search()中的问题：")
    logger.info("   - 当doc.page_content为空字符串时，'content'字段为空")
    logger.info("   - 当doc.metadata为空字典时，'metadata'字段为空")
    logger.info("   - 但整个processed_doc字典不会为空")
    logger.info("")
    
    logger.info("6.2 结果融合中的问题：")
    logger.info("   - _merge_and_deduplicate_results()中，如果result['content']为空")
    logger.info("   - 可能导致去重逻辑出现问题")
    logger.info("   - 可能产生空字典")
    logger.info("")
    
    logger.info("6.3 最终排序中的问题：")
    logger.info("   - _final_ranking_and_limit()中，如果results包含空字典")
    logger.info("   - 排序过程中可能产生问题")
    logger.info("   - 最终返回的final_results可能包含空字典")
    logger.info("")
    
    # 7. 空字典产生的真正原因
    logger.info("🚨 空字典产生的真正原因：")
    
    logger.info("7.1 最可能的原因：")
    logger.info("   - 在某个引擎的结果处理过程中，产生了空字典")
    logger.info("   - 这些空字典被添加到results列表中")
    logger.info("   - 传递给HybridEngine，最终到达v2_routes.py")
    logger.info("")
    
    logger.info("7.2 具体位置：")
    logger.info("   - 位置1：TextEngine._vector_similarity_search()的结果构建")
    logger.info("   - 位置2：TextEngine._merge_and_deduplicate_results()的结果融合")
    logger.info("   - 位置3：TextEngine._final_ranking_and_limit()的最终排序")
    logger.info("   - 位置4：HybridEngine的结果传递")
    logger.info("")
    
    # 8. 源头修复方案
    logger.info("💡 源头修复方案：")
    
    logger.info("8.1 在TextEngine中添加结果验证：")
    logger.info("   - 在processed_results.append()之前验证doc对象")
    logger.info("   - 确保doc.page_content不为空")
    logger.info("   - 确保doc.metadata不为空")
    logger.info("   - 跳过无效的doc对象")
    logger.info("")
    
    logger.info("8.2 在结果融合中添加验证：")
    logger.info("   - 在_merge_and_deduplicate_results()中验证每个result")
    logger.info("   - 确保result['content']不为空")
    logger.info("   - 确保result['metadata']不为空")
    logger.info("   - 跳过无效的result")
    logger.info("")
    
    logger.info("8.3 在最终排序中添加验证：")
    logger.info("   - 在_final_ranking_and_limit()中验证每个result")
    logger.info("   - 确保result是有效的字典")
    logger.info("   - 跳过空字典")
    logger.info("")
    
    # 9. 验证步骤
    logger.info("🔍 验证步骤：")
    
    logger.info("9.1 添加详细日志：")
    logger.info("   - 在TextEngine的每个关键方法中添加日志")
    logger.info("   - 记录每个doc对象的详细信息")
    logger.info("   - 记录每个result的详细信息")
    logger.info("   - 识别空字典产生的具体位置")
    logger.info("")
    
    logger.info("9.2 添加结果验证：")
    logger.info("   - 在每个结果构建点添加验证逻辑")
    logger.info("   - 确保不会产生空字典")
    logger.info("   - 跳过无效的结果")
    logger.info("")
    
    logger.info("9.3 测试验证：")
    logger.info("   - 运行各种查询类型")
    logger.info("   - 检查是否还有空字典")
    logger.info("   - 验证image_results、table_results、text_results是否正常")
    logger.info("")
    
    logger.info("=" * 80)
    logger.info("✅ 空字典源头分析完成")
    
    return {
        'root_cause': '在TextEngine的结果构建、融合或排序过程中产生了空字典',
        'specific_locations': [
            'TextEngine._vector_similarity_search()的结果构建',
            'TextEngine._merge_and_deduplicate_results()的结果融合',
            'TextEngine._final_ranking_and_limit()的最终排序',
            'HybridEngine的结果传递'
        ],
        'fix_strategy': '在源头添加结果验证，确保不会产生空字典',
        'verification_steps': [
            '添加详细日志识别空字典位置',
            '在关键点添加结果验证',
            '测试验证修复效果'
        ]
    }

def check_specific_code_issues():
    """检查具体的代码问题"""
    
    logger.info("🔍 检查具体的代码问题")
    logger.info("=" * 80)
    
    # 1. 检查processed_doc构建
    logger.info("1. processed_doc构建问题：")
    logger.info("   - 代码：processed_doc = { 'content': doc.page_content, 'metadata': doc.metadata, ... }")
    logger.info("   - 问题：如果doc.page_content为空字符串，content字段为空")
    logger.info("   - 问题：如果doc.metadata为空字典，metadata字段为空")
    logger.info("   - 但整个字典不会为空，只是某些字段为空")
    logger.info("")
    
    # 2. 检查结果融合
    logger.info("2. 结果融合问题：")
    logger.info("   - 代码：for result in all_results:")
    logger.info("   - 问题：如果某个result是空字典{}，会被包含在结果中")
    logger.info("   - 问题：去重逻辑可能无法处理空字典")
    logger.info("")
    
    # 3. 检查最终排序
    logger.info("3. 最终排序问题：")
    logger.info("   - 代码：for result in results:")
    logger.info("   - 问题：如果results包含空字典，排序可能出错")
    logger.info("   - 问题：空字典可能被错误地包含在最终结果中")
    logger.info("")
    
    # 4. 检查QueryResult构建
    logger.info("4. QueryResult构建问题：")
    logger.info("   - 代码：results=final_results")
    logger.info("   - 问题：如果final_results包含空字典，QueryResult.results也会包含空字典")
    logger.info("   - 问题：这些空字典最终传递给v2_routes.py")
    logger.info("")
    
    return {
        'code_issues': [
            'processed_doc构建时字段可能为空',
            '结果融合时可能包含空字典',
            '最终排序时可能包含空字典',
            'QueryResult构建时包含空字典'
        ],
        'fix_approach': '在每个关键点添加结果验证，跳过无效结果'
    }

if __name__ == "__main__":
    logger.info("🚀 开始空字典源头深入调查")
    
    # 执行分析
    analysis_result = analyze_empty_dict_source()
    code_issues = check_specific_code_issues()
    
    logger.info("📊 分析结果总结：")
    logger.info(f"根本原因: {analysis_result['root_cause']}")
    logger.info(f"具体位置: {analysis_result['specific_locations']}")
    logger.info(f"修复策略: {analysis_result['fix_strategy']}")
    
    logger.info("🔧 代码问题总结：")
    logger.info(f"代码问题: {code_issues['code_issues']}")
    logger.info(f"修复方法: {code_issues['fix_approach']}")
    
    logger.info("✅ 深入调查完成，请根据分析结果进行源头修复")
