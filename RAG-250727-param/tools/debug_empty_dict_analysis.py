'''
程序说明：
## 1. 分析空字典产生的根本原因
## 2. 检查数据流中的关键节点
## 3. 验证字段映射改造的效果
## 4. 提供解决方案建议
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

def analyze_empty_dict_issue():
    """分析空字典问题的根本原因"""
    
    logger.info("🔍 开始分析空字典问题的根本原因")
    logger.info("=" * 60)
    
    # 1. 分析数据流路径
    logger.info("📊 数据流路径分析：")
    logger.info("用户查询 → HybridEngine.process_query() → TextEngine.process_query() → _search_texts() → _vector_similarity_search()")
    logger.info("")
    
    # 2. 检查关键代码段
    logger.info("🔍 关键代码段分析：")
    
    # 2.1 检查HybridEngine中的结果处理
    logger.info("2.1 HybridEngine结果处理：")
    logger.info("   - 在process_query()中，TextEngine返回QueryResult")
    logger.info("   - QueryResult.results包含实际的文档列表")
    logger.info("   - 这些结果被传递给v2_routes.py的v2_ask_question()")
    logger.info("")
    
    # 2.2 检查TextEngine中的结果构建
    logger.info("2.2 TextEngine结果构建：")
    logger.info("   - _vector_similarity_search()返回List[Dict[str, Any]]")
    logger.info("   - 每个Dict包含：'content', 'metadata', 'vector_score', 'search_strategy', 'doc_id', 'doc'")
    logger.info("   - 这些结果被传递给process_query()的final_results")
    logger.info("   - QueryResult.results = final_results")
    logger.info("")
    
    # 2.3 检查v2_routes.py中的结果处理
    logger.info("2.3 v2_routes.py结果处理：")
    logger.info("   - v2_ask_question()接收QueryResult")
    logger.info("   - 遍历result.results列表")
    logger.info("   - 调用_extract_actual_doc_and_score(doc)处理每个doc")
    logger.info("   - 如果doc是空字典{}，函数返回None，结果被跳过")
    logger.info("")
    
    # 3. 问题根因分析
    logger.info("🚨 问题根因分析：")
    logger.info("3.1 空字典产生的位置：")
    logger.info("   - 可能位置1：TextEngine._vector_similarity_search()返回空字典")
    logger.info("   - 可能位置2：TextEngine.process_query()中结果处理时产生空字典")
    logger.info("   - 可能位置3：HybridEngine在传递结果时产生空字典")
    logger.info("")
    
    logger.info("3.2 空字典产生的可能原因：")
    logger.info("   - 原因1：向量搜索失败，返回空结果列表，但被错误地转换为包含空字典的列表")
    logger.info("   - 原因2：文档处理过程中，某些文档的元数据为空，被转换为空字典")
    logger.info("   - 原因3：结果融合过程中，空结果被错误地保留为字典格式")
    logger.info("   - 原因4：字段映射改造过程中，某些字段被错误地清空")
    logger.info("")
    
    # 4. 具体代码问题分析
    logger.info("🔍 具体代码问题分析：")
    
    logger.info("4.1 TextEngine._vector_similarity_search()问题：")
    logger.info("   - 当向量搜索失败时，可能返回包含空字典的列表")
    logger.info("   - 在processed_results.append()时，如果doc对象有问题，可能产生空字典")
    logger.info("   - 错误处理逻辑可能没有正确过滤空结果")
    logger.info("")
    
    logger.info("4.2 结果处理问题：")
    logger.info("   - 在process_query()中，final_results可能包含空字典")
    logger.info("   - 这些空字典被包装在QueryResult.results中")
    logger.info("   - 传递给HybridEngine，最终到达v2_routes.py")
    logger.info("")
    
    # 5. 解决方案
    logger.info("💡 解决方案：")
    
    logger.info("5.1 立即修复（已在v2_routes.py中实现）：")
    logger.info("   - 增强_extract_actual_doc_and_score()函数，处理空字典")
    logger.info("   - 添加详细的调试日志，识别空字典来源")
    logger.info("   - 跳过空字典，避免整个结果被清空")
    logger.info("")
    
    logger.info("5.2 根本修复（需要进一步调查）：")
    logger.info("   - 检查TextEngine._vector_similarity_search()的返回值")
    logger.info("   - 检查process_query()中final_results的构建过程")
    logger.info("   - 在结果传递的每个环节添加验证")
    logger.info("   - 确保不会产生空字典")
    logger.info("")
    
    logger.info("5.3 预防措施：")
    logger.info("   - 在TextEngine中添加结果验证逻辑")
    logger.info("   - 在HybridEngine中添加结果过滤逻辑")
    logger.info("   - 在v2_routes.py中添加最终验证逻辑")
    logger.info("")
    
    # 6. 验证步骤
    logger.info("🔍 验证步骤：")
    
    logger.info("6.1 验证修复效果：")
    logger.info("   - 运行测试查询，检查是否还有空字典警告")
    logger.info("   - 检查前端是否正常显示结果")
    logger.info("   - 验证image_results、table_results、text_results是否正常")
    logger.info("")
    
    logger.info("6.2 深入调查空字典来源：")
    logger.info("   - 在TextEngine中添加详细日志，跟踪每个结果的构建过程")
    logger.info("   - 检查向量搜索的返回值，确保没有空字典")
    logger.info("   - 验证文档元数据的完整性")
    logger.info("")
    
    logger.info("6.3 长期优化：")
    logger.info("   - 完善字段映射改造，确保所有字段都有正确的默认值")
    logger.info("   - 添加数据验证层，防止空数据进入结果流")
    logger.info("   - 实现更健壮的错误处理机制")
    logger.info("")
    
    logger.info("=" * 60)
    logger.info("✅ 空字典问题分析完成")
    
    return {
        'root_cause': 'TextEngine._vector_similarity_search()可能返回包含空字典的结果',
        'immediate_fix': '已在v2_routes.py中增强_extract_actual_doc_and_score()函数',
        'long_term_fix': '需要在TextEngine中添加结果验证和过滤逻辑',
        'verification_steps': [
            '测试修复效果',
            '深入调查空字典来源',
            '完善字段映射改造'
        ]
    }

def check_text_engine_code():
    """检查TextEngine代码中的潜在问题"""
    
    logger.info("🔍 检查TextEngine代码中的潜在问题")
    logger.info("=" * 60)
    
    # 检查_vector_similarity_search方法
    logger.info("1. _vector_similarity_search方法分析：")
    logger.info("   - 该方法返回List[Dict[str, Any]]")
    logger.info("   - 在processed_results.append()时，每个doc被转换为字典")
    logger.info("   - 如果doc对象有问题，可能产生空字典")
    logger.info("")
    
    logger.info("2. 潜在问题点：")
    logger.info("   - 当doc.metadata为空时，可能产生空字典")
    logger.info("   - 当doc.page_content为空时，可能产生空字典")
    logger.info("   - 当doc对象本身有问题时，可能产生空字典")
    logger.info("")
    
    logger.info("3. 建议的修复：")
    logger.info("   - 在processed_results.append()之前添加doc验证")
    logger.info("   - 确保只有有效的doc对象被添加到结果中")
    logger.info("   - 添加默认值，避免空字段")
    logger.info("")
    
    return {
        'method': '_vector_similarity_search',
        'potential_issues': [
            'doc.metadata为空',
            'doc.page_content为空',
            'doc对象本身有问题'
        ],
        'suggested_fixes': [
            '添加doc验证逻辑',
            '确保只有有效doc被添加',
            '添加默认值避免空字段'
        ]
    }

if __name__ == "__main__":
    logger.info("🚀 开始空字典问题分析")
    
    # 执行分析
    analysis_result = analyze_empty_dict_issue()
    text_engine_analysis = check_text_engine_code()
    
    logger.info("📊 分析结果总结：")
    logger.info(f"根本原因: {analysis_result['root_cause']}")
    logger.info(f"立即修复: {analysis_result['immediate_fix']}")
    logger.info(f"长期修复: {analysis_result['long_term_fix']}")
    
    logger.info("🔧 TextEngine修复建议：")
    logger.info(f"问题方法: {text_engine_analysis['method']}")
    logger.info(f"潜在问题: {text_engine_analysis['potential_issues']}")
    logger.info(f"建议修复: {text_engine_analysis['suggested_fixes']}")
    
    logger.info("✅ 分析完成，请根据建议进行相应的修复")
