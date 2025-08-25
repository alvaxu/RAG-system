#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
## 1. 测试添加日志后的TableEngine
## 2. 查看self.table_docs的状态和Document对象的结构
## 3. 验证字段补充逻辑的执行情况

## 主要功能：
- 运行简单的table查询
- 查看详细的日志输出
- 分析Document对象的状态
"""

import sys
import os
import logging

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from v2.core.hybrid_engine import HybridEngine
from v2.config.v2_config import V2ConfigManager

# 配置日志级别为DEBUG，显示所有日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_table_query_with_logs():
    """测试table查询，查看详细日志"""
    try:
        logger.info("开始测试TableEngine查询，查看详细日志...")
        
        # 创建配置管理器
        config_manager = V2ConfigManager()
        
        # 创建HybridEngine实例
        hybrid_engine = HybridEngine(config=config_manager.config)
        
        # 执行table查询
        query = "中芯国际的营业收入"
        logger.info(f"执行查询: {query}")
        
        # 调用query方法
        result = hybrid_engine.query(query, query_type='table')
        
        if result.success:
            logger.info("✅ 查询成功")
            logger.info(f"结果数量: {len(result.results)}")
            
            # 检查前3个结果
            for i, res in enumerate(result.results[:3]):
                logger.info(f"\n🔍 结果 {i+1}:")
                logger.info(f"  类型: {type(res)}")
                logger.info(f"  键: {list(res.keys()) if isinstance(res, dict) else 'N/A'}")
                
                if isinstance(res, dict) and 'doc' in res:
                    doc = res['doc']
                    logger.info(f"  doc类型: {type(doc)}")
                    
                    if hasattr(doc, 'page_content'):
                        page_content = doc.page_content
                        logger.info(f"  doc.page_content长度: {len(page_content) if page_content else 0}")
                        if page_content and len(page_content) > 100:
                            logger.info(f"  doc.page_content前100字符: {page_content[:100]}")
                    else:
                        logger.warning(f"  ❌ doc.page_content字段不存在！")
                    
                    if hasattr(doc, 'metadata') and doc.metadata and 'page_content' in doc.metadata:
                        meta_page_content = doc.metadata['page_content']
                        logger.info(f"  doc.metadata['page_content']长度: {len(meta_page_content) if meta_page_content else 0}")
                    else:
                        logger.warning(f"  ❌ doc.metadata中没有page_content字段")
        else:
            logger.error(f"❌ 查询失败: {result.error_message}")
        
        logger.info("✅ 测试完成")
        
    except Exception as e:
        logger.error(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_table_query_with_logs()
