#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
## 1. 调试TableEngine中table_docs的Document对象结构
## 2. 检查page_content字段是否缺失，以及metadata中的page_content状态
## 3. 验证字段补充逻辑是否正确执行

## 主要功能：
- 检查table_docs中Document对象的结构
- 验证page_content字段的状态
- 测试字段补充逻辑
"""

import sys
import os
import logging

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from v2.core.table_engine import TableEngine
from v2.config.v2_config import V2ConfigManager

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_table_docs_structure():
    """调试table_docs中Document对象的结构"""
    try:
        logger.info("开始调试TableEngine中table_docs的结构...")
        
        # 创建配置管理器
        config_manager = V2ConfigManager()
        
        # 获取配置对象
        table_config = config_manager.config.table_engine
        logger.info(f"TableEngine配置: {table_config}")
        
        # 创建TableEngine实例
        table_engine = TableEngine(config=table_config)
        
        # 确保文档已加载
        table_engine._ensure_docs_loaded()
        
        logger.info(f"✅ 文档加载完成，table_docs数量: {len(table_engine.table_docs)}")
        
        if not table_engine.table_docs:
            logger.warning("❌ table_docs为空！")
            return
        
        # 检查前5个文档的结构
        for i, doc in enumerate(table_engine.table_docs[:5]):
            logger.info(f"\n🔍 检查文档 {i+1}:")
            logger.info(f"  文档类型: {type(doc)}")
            logger.info(f"  文档ID: {getattr(doc, 'id', 'N/A')}")
            
            # 检查page_content字段
            if hasattr(doc, 'page_content'):
                page_content = doc.page_content
                logger.info(f"  page_content字段存在，类型: {type(page_content)}")
                logger.info(f"  page_content长度: {len(page_content) if page_content else 0}")
                logger.info(f"  page_content前100字符: {str(page_content)[:100] if page_content else 'N/A'}")
            else:
                logger.warning(f"  ❌ page_content字段不存在！")
            
            # 检查metadata字段
            if hasattr(doc, 'metadata'):
                metadata = doc.metadata
                logger.info(f"  metadata字段存在，类型: {type(metadata)}")
                if isinstance(metadata, dict):
                    logger.info(f"  metadata键: {list(metadata.keys())}")
                    
                    # 检查metadata中是否有page_content
                    if 'page_content' in metadata:
                        meta_page_content = metadata['page_content']
                        logger.info(f"  metadata['page_content']存在，类型: {type(meta_page_content)}")
                        logger.info(f"  metadata['page_content']长度: {len(meta_page_content) if meta_page_content else 0}")
                        logger.info(f"  metadata['page_content']前100字符: {str(meta_page_content)[:100] if meta_page_content else 'N/A'}")
                        
                        # 如果page_content为空但metadata中有，尝试补充
                        if hasattr(doc, 'page_content') and (not doc.page_content or len(doc.page_content.strip()) == 0):
                            if meta_page_content and len(meta_page_content.strip()) > 0:
                                logger.info(f"  🔧 尝试补充page_content字段...")
                                doc.page_content = meta_page_content
                                logger.info(f"  ✅ 已补充page_content字段，新长度: {len(doc.page_content)}")
                            else:
                                logger.warning(f"  ❌ metadata['page_content']也为空，无法补充")
                        elif not hasattr(doc, 'page_content'):
                            logger.warning(f"  ❌ Document对象没有page_content属性，无法补充")
                    else:
                        logger.warning(f"  ❌ metadata中没有page_content字段")
                else:
                    logger.warning(f"  ❌ metadata不是字典类型")
            else:
                logger.warning(f"  ❌ metadata字段不存在！")
            
            # 检查其他重要字段
            important_fields = ['document_name', 'page_number', 'chunk_type', 'table_id']
            for field in important_fields:
                if hasattr(doc, field):
                    value = getattr(doc, field)
                    logger.info(f"  {field}: {value}")
                elif hasattr(doc, 'metadata') and isinstance(doc.metadata, dict) and field in doc.metadata:
                    value = doc.metadata[field]
                    logger.info(f"  {field} (从metadata): {value}")
                else:
                    logger.warning(f"  ❌ {field}字段不存在")
        
        # 测试第一层召回
        logger.info(f"\n🧪 测试第一层召回...")
        test_query = "中芯国际的营业收入"
        
        # 调用第一层召回方法
        if hasattr(table_engine, '_table_structure_precise_search'):
            layer1_results = table_engine._table_structure_precise_search(test_query, top_k=3)
            logger.info(f"第一层召回返回 {len(layer1_results)} 个结果")
            
            for i, result in enumerate(layer1_results):
                logger.info(f"\n🔍 第一层召回结果 {i+1}:")
                logger.info(f"  结果类型: {type(result)}")
                logger.info(f"  结果键: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
                
                if 'doc' in result and result['doc']:
                    doc = result['doc']
                    logger.info(f"  doc类型: {type(doc)}")
                    
                    if hasattr(doc, 'page_content'):
                        page_content = doc.page_content
                        logger.info(f"  doc.page_content长度: {len(page_content) if page_content else 0}")
                        logger.info(f"  doc.page_content前100字符: {str(page_content)[:100] if page_content else 'N/A'}")
                    else:
                        logger.warning(f"  ❌ doc.page_content字段不存在！")
                    
                    if hasattr(doc, 'metadata') and doc.metadata and 'page_content' in doc.metadata:
                        meta_page_content = doc.metadata['page_content']
                        logger.info(f"  doc.metadata['page_content']长度: {len(meta_page_content) if meta_page_content else 0}")
                    else:
                        logger.warning(f"  ❌ doc.metadata中没有page_content字段")
                else:
                    logger.warning(f"  ❌ 结果中没有doc字段")
        else:
            logger.warning("❌ _table_structure_precise_search方法不存在")
        
        logger.info("\n✅ 调试完成")
        
    except Exception as e:
        logger.error(f"调试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_table_docs_structure()
