#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
## 1. 分析改造前后的差异，找出空字典产生的根本原因
## 2. 检查字段映射的一致性
## 3. 分析数据流的每个环节
"""

import sys
import os
import json
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from v2.core.text_engine import TextEngine
from v2.core.hybrid_engine import HybridEngine
from v2.core.base_engine import QueryResult, QueryType, EngineConfig

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_text_engine_config():
    """创建文本引擎配置"""
    # 直接创建配置对象
    config = EngineConfig(
        enabled=True,
        name="text_engine",
        version="2.0.0",
        debug=True,
        max_results=10,
        timeout=30.0,
        cache_enabled=True,
        cache_ttl=300
    )
    
    # 添加文本引擎特有的配置
    config.text_similarity_threshold = 0.7
    config.keyword_weight = 0.3
    config.semantic_weight = 0.4
    config.vector_weight = 0.3
    config.enable_semantic_search = True
    config.enable_vector_search = True
    config.min_required_results = 20
    config.use_new_pipeline = True
    config.enable_enhanced_reranking = True
    
    # 添加召回策略配置
    config.recall_strategy = {
        'layer1_vector_search': {
            'enabled': True,
            'top_k': 50,
            'similarity_threshold': 0.3,
            'description': '第一层：向量相似度搜索（主要策略）'
        },
        'layer2_semantic_keyword': {
            'enabled': True,
            'top_k': 40,
            'match_threshold': 0.25,
            'description': '第二层：语义关键词搜索（补充策略）'
        },
        'layer3_hybrid_search': {
            'enabled': True,
            'top_k': 35,
            'vector_weight': 0.4,
            'keyword_weight': 0.3,
            'semantic_weight': 0.3,
            'description': '第三层：混合搜索策略（融合策略）'
        },
        'layer4_smart_fuzzy': {
            'enabled': True,
            'top_k': 30,
            'fuzzy_threshold': 0.2,
            'description': '第四层：智能模糊匹配（容错策略）'
        },
        'layer5_expansion': {
            'enabled': True,
            'top_k': 25,
            'activation_threshold': 20,
            'description': '第五层：智能扩展召回（兜底策略）'
        }
    }
    
    return config

def analyze_refactoring_impact():
    """分析改造前后的差异"""
    
    logger.info("🔍 开始分析改造前后的差异...")
    
    try:
        # 1. 创建配置
        text_config = create_text_engine_config()
        logger.info(f"📊 文本引擎配置: {text_config}")
        
        # 2. 检查字段映射配置
        field_mapping_config = getattr(text_config, 'field_mapping', {})
        logger.info(f"🔧 字段映射配置: {field_mapping_config}")
        
        # 3. 检查向量数据库状态
        text_engine = TextEngine(text_config)
        text_engine._ensure_docs_loaded()
        
        logger.info(f"📚 文本文档数量: {len(text_engine.text_docs)}")
        
        # 4. 检查向量搜索的返回结果
        test_query = "中芯国际的主要业务"
        logger.info(f"🧪 测试查询: {test_query}")
        
        # 执行向量搜索
        vector_results = text_engine._vector_similarity_search(test_query, top_k=5)
        logger.info(f"🔍 向量搜索结果数量: {len(vector_results)}")
        
        # 分析每个结果的字段
        for i, result in enumerate(vector_results):
            logger.info(f"📋 结果 {i}:")
            logger.info(f"  类型: {type(result)}")
            logger.info(f"  键: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
            logger.info(f"  内容长度: {len(str(result.get('content', ''))) if isinstance(result, dict) else 'N/A'}")
            logger.info(f"  元数据键数: {len(result.get('metadata', {})) if isinstance(result, dict) else 'N/A'}")
            
            # 检查是否有空字典
            if isinstance(result, dict) and len(result) == 0:
                logger.error(f"❌ 发现空字典结果 {i}!")
            
            # 检查必要字段
            if isinstance(result, dict):
                required_fields = ['content', 'metadata']
                for field in required_fields:
                    if field not in result:
                        logger.warning(f"⚠️ 缺少必要字段: {field}")
                    elif not result[field]:
                        logger.warning(f"⚠️ 字段 {field} 为空")
        
        # 5. 检查合并和去重过程
        if vector_results:
            merged_results = text_engine._merge_and_deduplicate_results(vector_results)
            logger.info(f"🔄 合并去重后结果数量: {len(merged_results)}")
            
            # 分析合并后的结果
            for i, result in enumerate(merged_results):
                logger.info(f"📋 合并后结果 {i}:")
                logger.info(f"  类型: {type(result)}")
                logger.info(f"  键: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
                logger.info(f"  内容长度: {len(str(result.get('content', ''))) if isinstance(result, dict) else 'N/A'}")
                
                # 检查是否有空字典
                if isinstance(result, dict) and len(result) == 0:
                    logger.error(f"❌ 合并后发现空字典结果 {i}!")
        
        # 6. 检查最终排序和限制
        if merged_results:
            final_results = text_engine._final_ranking_and_limit(test_query, merged_results)
            logger.info(f"🏆 最终结果数量: {len(final_results)}")
            
            # 分析最终结果
            for i, result in enumerate(final_results):
                logger.info(f"📋 最终结果 {i}:")
                logger.info(f"  类型: {type(result)}")
                logger.info(f"  键: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
                logger.info(f"  内容长度: {len(str(result.get('content', ''))) if isinstance(result, dict) else 'N/A'}")
                
                # 检查是否有空字典
                if isinstance(result, dict) and len(result) == 0:
                    logger.error(f"❌ 最终结果中发现空字典 {i}!")
        
        # 7. 检查完整流程
        logger.info("🔄 检查完整流程...")
        try:
            complete_result = text_engine.process_query(test_query)
            logger.info(f"✅ 完整流程成功，结果数量: {len(complete_result.results)}")
            
            # 分析完整流程的结果
            for i, result in enumerate(complete_result.results):
                logger.info(f"📋 完整流程结果 {i}:")
                logger.info(f"  类型: {type(result)}")
                if isinstance(result, dict):
                    logger.info(f"  键: {list(result.keys())}")
                    logger.info(f"  内容长度: {len(str(result.get('content', '')))}")
                    
                    # 检查是否有空字典
                    if len(result) == 0:
                        logger.error(f"❌ 完整流程中发现空字典 {i}!")
                else:
                    logger.info(f"  非字典类型: {result}")
                    
        except Exception as e:
            logger.error(f"❌ 完整流程失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
        
        # 8. 总结分析结果
        logger.info("=" * 50)
        logger.info("📊 分析总结:")
        logger.info("1. 检查了向量搜索的返回结果")
        logger.info("2. 检查了合并去重过程")
        logger.info("3. 检查了最终排序和限制")
        logger.info("4. 检查了完整流程")
        logger.info("5. 识别了空字典产生的环节")
        
    except Exception as e:
        logger.error(f"❌ 分析过程中发生错误: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")

if __name__ == "__main__":
    analyze_refactoring_impact()
