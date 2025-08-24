#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
## 1. 检查向量数据库状态
## 2. 验证文档是否正确加载
## 3. 诊断查询失败的原因
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_vector_db_status():
    """检查向量数据库状态"""
    
    logger.info("🔍 开始检查向量数据库状态...")
    
    try:
        # 导入必要的模块
        from v2.config.v2_config import V2ConfigManager
        from v2.core.vector_store import VectorStore
        
        # 获取配置
        config_manager = V2ConfigManager()
        logger.info("✅ 成功导入V2ConfigManager")
        
        # 检查向量数据库配置
        vector_config = config_manager.get_engine_config('vector_store')
        if vector_config:
            logger.info(f"✅ 向量数据库配置: {vector_config}")
        else:
            logger.error("❌ 无法获取向量数据库配置")
            return
        
        # 尝试创建向量数据库实例
        try:
            vector_store = VectorStore(vector_config)
            logger.info("✅ 成功创建VectorStore实例")
            
            # 检查文档数量
            if hasattr(vector_store, 'docstore') and vector_store.docstore:
                if hasattr(vector_store.docstore, '_dict'):
                    doc_count = len(vector_store.docstore._dict)
                    logger.info(f"📊 向量数据库中的文档数量: {doc_count}")
                    
                    if doc_count > 0:
                        # 显示前几个文档的信息
                        logger.info("📋 前3个文档信息:")
                        for i, (doc_id, doc) in enumerate(list(vector_store.docstore._dict.items())[:3]):
                            logger.info(f"  文档 {i+1}: ID={doc_id}")
                            if hasattr(doc, 'metadata'):
                                metadata = doc.metadata
                                logger.info(f"    类型: {metadata.get('chunk_type', 'unknown')}")
                                logger.info(f"    文档名: {metadata.get('document_name', 'unknown')}")
                                logger.info(f"    页码: {metadata.get('page_number', 'unknown')}")
                            if hasattr(doc, 'page_content'):
                                content_preview = doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
                                logger.info(f"    内容预览: {content_preview}")
                    else:
                        logger.warning("⚠️ 向量数据库中没有文档！")
                else:
                    logger.warning("⚠️ docstore没有_dict属性")
            else:
                logger.warning("⚠️ 向量数据库没有docstore属性")
                
        except Exception as e:
            logger.error(f"❌ 创建VectorStore失败: {e}")
            return
        
        # 检查文本引擎配置
        text_config = config_manager.get_engine_config('text_engine')
        if text_config:
            logger.info(f"✅ 文本引擎配置: {text_config}")
            logger.info(f"  启用状态: {text_config.enabled}")
            logger.info(f"  相似度阈值: {getattr(text_config, 'text_similarity_threshold', 'N/A')}")
            logger.info(f"  使用新管道: {getattr(text_config, 'use_new_pipeline', 'N/A')}")
        else:
            logger.error("❌ 无法获取文本引擎配置")
        
        # 总结
        logger.info("=" * 50)
        logger.info("📊 向量数据库状态检查完成")
        logger.info("如果文档数量为0，说明文档没有正确加载")
        logger.info("如果文档数量正常但查询失败，说明搜索策略有问题")
        
    except Exception as e:
        logger.error(f"❌ 检查过程中发生错误: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")

if __name__ == "__main__":
    check_vector_db_status()
