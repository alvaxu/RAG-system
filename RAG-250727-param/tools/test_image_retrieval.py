#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
## 1. 图片检索单元测试脚本
## 2. 调低图片检索分数阈值，输出分数分布
## 3. 便于调试图片召回效果
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v2.core.image_engine import ImageEngine
from v2.config.v2_config import ImageEngineConfigV2
from config.config_manager import ConfigManager
from document_processing.vector_generator import VectorGenerator


def test_image_retrieval():
    print("🔍 图片检索单元测试（低阈值模式）")
    config_manager = ConfigManager()
    vector_db_path = config_manager.get_settings().vector_db_dir
    print(f"📁 向量数据库路径: {vector_db_path}")

    # 加载向量数据库
    vector_generator = VectorGenerator(config_manager.get_settings())
    vector_store = vector_generator.load_vector_store(vector_db_path)

    # 设置低阈值图片引擎
    image_config = ImageEngineConfigV2(debug=True)
    image_config.image_similarity_threshold = 0.2
    image_engine = ImageEngine(image_config, vector_store)

    # 典型图片问题
    test_queries = [
        "图4显示了什么内容？",
        "全球部署示意图",
        "中芯国际的图片信息",
        "营业收入相关的图表",
        "产能利用率的图片"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n🔎 测试图片查询 {i}: {query}")
        result = image_engine.process_query(query)
        print(f"  召回图片数: {result.total_count}")
        if result.results:
            for idx, item in enumerate(result.results[:10], 1):
                doc = item.get('doc')
                score = item.get('score', 0)
                caption = doc.metadata.get('img_caption', '') if doc else ''
                title = doc.metadata.get('image_title', '') if doc else ''
                desc = doc.metadata.get('enhanced_description', '') if doc else ''
                print(f"    {idx}. 分数: {score:.3f} | 标题: {title} | Caption: {caption} | 描述: {str(desc)[:40]}")
        else:
            print("  ❌ 未召回任何图片")

if __name__ == "__main__":
    test_image_retrieval()
