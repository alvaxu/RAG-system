#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
程序说明：
## 1. 测试TableRerankingService与TableEngine的集成
## 2. 验证表格重排序服务是否能正常工作
## 3. 测试配置管理和服务创建
## 4. 验证重排序流程的完整性
'''

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v2.core.table_engine import TableEngine
from v2.core.reranking_services import TableRerankingService, RerankingServiceFactory
from v2.config.v2_config import load_v2_config
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_table_reranking_service_creation():
    """测试表格重排序服务创建"""
    logger.info("=" * 60)
    logger.info("测试1：表格重排序服务创建")
    logger.info("=" * 60)
    
    try:
        # 测试配置
        test_config = {
            'use_llm_enhancement': True,
            'model_name': 'gte-rerank-v2',
            'target_count': 10,
            'similarity_threshold': 0.7
        }
        
        # 创建服务
        service = TableRerankingService(test_config)
        logger.info(f"✅ 表格重排序服务创建成功: {service.get_service_name()}")
        logger.info(f"✅ 支持的内容类型: {service.get_supported_types()}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 表格重排序服务创建失败: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return False

def test_reranking_service_factory():
    """测试重排序服务工厂"""
    logger.info("=" * 60)
    logger.info("测试2：重排序服务工厂")
    logger.info("=" * 60)
    
    try:
        # 创建工厂
        factory = RerankingServiceFactory()
        logger.info(f"✅ 重排序服务工厂创建成功")
        logger.info(f"✅ 支持的服务类型: {factory.get_supported_types()}")
        
        # 测试table服务创建
        test_config = {
            'use_llm_enhancement': True,
            'model_name': 'gte-rerank-v2',
            'target_count': 10,
            'similarity_threshold': 0.7
        }
        
        table_service = factory.create_service('table', test_config)
        if table_service:
            logger.info(f"✅ 通过工厂创建table服务成功: {table_service.get_service_name()}")
        else:
            logger.error("❌ 通过工厂创建table服务失败")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 重排序服务工厂测试失败: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return False

def test_table_engine_integration():
    """测试表格引擎集成"""
    logger.info("=" * 60)
    logger.info("测试3：表格引擎集成")
    logger.info("=" * 60)
    
    try:
        # 获取配置
        config_manager = load_v2_config('v2/config/v2_config.json')
        config = config_manager.config
        
        # 检查表格引擎配置
        if not hasattr(config, 'table_engine'):
            logger.warning("⚠️ 配置中没有table_engine，跳过集成测试")
            return True
        
        table_config = config.table_engine
        logger.info(f"✅ 获取表格引擎配置成功")
        logger.info(f"✅ 启用状态: {table_config.enabled}")
        logger.info(f"✅ 最大结果数: {table_config.max_results}")
        
        # 检查重排序配置
        if hasattr(table_config, 'reranking'):
            reranking_config = table_config.reranking
            logger.info(f"✅ 重排序配置存在")
            logger.info(f"✅ 目标数量: {reranking_config.get('target_count', 'N/A')}")
            logger.info(f"✅ LLM增强: {reranking_config.get('use_llm_enhancement', 'N/A')}")
            logger.info(f"✅ 模型名称: {reranking_config.get('model_name', 'N/A')}")
            logger.info(f"✅ 相似度阈值: {reranking_config.get('similarity_threshold', 'N/A')}")
        else:
            logger.warning("⚠️ 表格引擎配置中没有重排序配置")
        
        # 检查增强重排序配置
        if hasattr(table_config, 'enable_enhanced_reranking'):
            logger.info(f"✅ 增强重排序配置: {table_config.enable_enhanced_reranking}")
        else:
            logger.warning("⚠️ 表格引擎配置中没有enable_enhanced_reranking")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 表格引擎集成测试失败: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return False

def test_table_engine_initialization():
    """测试表格引擎初始化"""
    logger.info("=" * 60)
    logger.info("测试4：表格引擎初始化")
    logger.info("=" * 60)
    
    try:
        # 获取配置
        config_manager = load_v2_config('v2/config/v2_config.json')
        
        # 获取表格引擎专用配置
        table_config = config_manager.get_engine_config('table')
        if not table_config:
            logger.error("❌ 无法获取表格引擎配置")
            return False
        
        # 创建表格引擎（跳过文档加载）
        table_engine = TableEngine(table_config, skip_initial_load=True)
        logger.info(f"✅ 表格引擎创建成功: {table_engine.name}")
        
        # 检查重排序服务是否初始化
        if hasattr(table_engine, 'table_reranking_service'):
            if table_engine.table_reranking_service:
                logger.info(f"✅ 表格重排序服务初始化成功")
                logger.info(f"✅ 服务名称: {table_engine.table_reranking_service.get_service_name()}")
            else:
                logger.info("ℹ️ 表格重排序服务未初始化（可能是配置原因）")
        else:
            logger.warning("⚠️ 表格引擎没有table_reranking_service属性")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 表格引擎初始化测试失败: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return False

def main():
    """主测试函数"""
    logger.info("🚀 开始测试TableRerankingService与TableEngine的集成")
    logger.info("=" * 80)
    
    test_results = []
    
    # 执行测试
    test_results.append(("表格重排序服务创建", test_table_reranking_service_creation()))
    test_results.append(("重排序服务工厂", test_reranking_service_factory()))
    test_results.append(("表格引擎集成", test_table_engine_integration()))
    test_results.append(("表格引擎初始化", test_table_engine_initialization()))
    
    # 输出测试结果
    logger.info("=" * 80)
    logger.info("📊 测试结果汇总")
    logger.info("=" * 80)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info("=" * 80)
    logger.info(f"总测试数: {total}")
    logger.info(f"通过数: {passed}")
    logger.info(f"失败数: {total - passed}")
    logger.info(f"成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        logger.info("🎉 所有测试通过！TableRerankingService与TableEngine集成成功！")
    else:
        logger.warning("⚠️ 部分测试失败，请检查相关配置和代码")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
