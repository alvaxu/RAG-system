'''
程序说明：
## 1. 调试源过滤引擎
## 2. 检查为什么表格数据被过滤掉
## 3. 分析相关性计算逻辑
'''

import logging
from config.config_manager import ConfigManager
from core.source_filter_engine import SourceFilterEngine

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_source_filter():
    """
    调试源过滤引擎
    """
    try:
        # 加载配置
        config_manager = ConfigManager()
        config = config_manager.settings.to_dict()
        
        # 获取QA系统配置
        qa_config = config.get('qa_system', {})
        logger.info(f"QA系统配置: {qa_config}")
        
        # 初始化源过滤引擎
        source_filter_engine = SourceFilterEngine(qa_config)
        
        # 测试数据
        llm_answer = "根据提供的文档内容，没有找到中芯国际2024年营业收入的具体数据。"
        
        # 模拟表格数据源
        table_source = {
            'content': '营业收入 (百万元) | 45,250 | 57,796 | 68,204 | 79,507 | 91,110\n增长比率 (%) | -8.61 | 27.72 | 18.01 | 16.57 | 14.59\n净利润 (百万元) | 4,823 | 3,699 | 5,075 | 6,228 | 7,542',
            'metadata': {
                'chunk_type': 'table',
                'table_id': 'table_835090',
                'table_type': '数据表格'
            }
        }
        
        # 模拟图片数据源
        image_source = {
            'content': '图片标题: 图1：公司单季度营业收入及增速情况 | 图片脚注: 资料来源：Wind，中原证券研究所 | 图表类型: 信息图表',
            'metadata': {
                'chunk_type': 'image',
                'image_id': 'e27d2aad5f5f952e58f7df5272c9c9a4567b605a52dbdff8b678e08699541398'
            }
        }
        
        sources = [table_source, image_source]
        
        logger.info("=== 开始调试源过滤引擎 ===")
        logger.info(f"LLM回答: {llm_answer}")
        logger.info(f"原始源数量: {len(sources)}")
        
        # 测试源过滤
        filtered_sources = source_filter_engine.filter_sources(llm_answer, sources)
        
        logger.info(f"过滤后源数量: {len(filtered_sources)}")
        
        # 详细分析每个源的相关性分数
        for i, source in enumerate(sources):
            logger.info(f"\n源 {i+1}:")
            logger.info(f"  类型: {source['metadata'].get('chunk_type', 'unknown')}")
            logger.info(f"  内容预览: {source['content'][:100]}...")
            
            # 手动计算相关性分数
            relevance_score = source_filter_engine._calculate_source_relevance(llm_answer, source)
            logger.info(f"  相关性分数: {relevance_score:.4f}")
            logger.info(f"  是否保留: {'是' if relevance_score >= source_filter_engine.min_relevance_score else '否'}")
            
            # 详细分析各个子分数
            if source_filter_engine.enable_keyword_matching:
                keyword_score = source_filter_engine._calculate_keyword_relevance(llm_answer, source)
                logger.info(f"  关键词匹配分数: {keyword_score:.4f}")
            
            if source_filter_engine.enable_similarity_filtering:
                similarity_score = source_filter_engine._calculate_similarity_relevance(llm_answer, source)
                logger.info(f"  相似度过滤分数: {similarity_score:.4f}")
            
            logger.info(f"  最终相关性分数: {relevance_score:.4f}")
            logger.info(f"  阈值: {source_filter_engine.min_relevance_score:.4f}")
            logger.info(f"  是否通过过滤: {'是' if relevance_score >= source_filter_engine.min_relevance_score else '否'}")
        
        return True
        
    except Exception as e:
        logger.error(f"调试失败: {e}")
        return False

if __name__ == "__main__":
    debug_source_filter() 