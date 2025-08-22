#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试ImageEngine的日志输出
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from v2.core.image_engine import ImageEngine
from v2.config.v2_config import ImageEngineConfigV2

def test_image_engine_logs():
    """测试ImageEngine的日志输出"""
    
    # 设置日志级别
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("=" * 60)
    print("测试ImageEngine的日志输出")
    print("=" * 60)
    
    try:
        # 创建配置
        config = ImageEngineConfigV2(
            name="test_image_engine",
            version="1.0.0",
            enabled=True,
            image_similarity_threshold=0.3,
            cross_modal_similarity_threshold=0.5,
            max_results=10
        )
        
        print("✅ 配置创建成功")
        
        # 创建ImageEngine（跳过初始化，只测试日志）
        image_engine = ImageEngine.__new__(ImageEngine)
        image_engine.config = config
        image_engine.name = config.name
        image_engine.logger = logging.getLogger(f"v2.core.base_engine.{config.name}")
        image_engine.image_docs = []
        image_engine._docs_loaded = False
        
        print("✅ ImageEngine创建成功")
        print(f"📊 图片文档数量: {len(image_engine.image_docs)}")
        
        # 测试日志输出
        print("\n🔍 测试日志输出...")
        image_engine.logger.info("这是一条测试信息日志")
        image_engine.logger.warning("这是一条测试警告日志")
        image_engine.logger.error("这是一条测试错误日志")
        
        print("✅ 日志输出测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_image_engine_logs()
