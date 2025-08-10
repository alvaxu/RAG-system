#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：

## 1. 检查向量数据库中内容的长度分布
## 2. 识别可能超过2048字符限制的超长内容
## 3. 分析不同类型内容（文本、表格、图片）的长度特征
"""

import os
import sys
import json
from typing import Dict, List, Tuple
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from core.vector_store import VectorStoreManager

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_content_lengths():
    """检查向量数据库中内容的长度分布"""
    try:
        # 加载配置
        settings = Settings.load_from_file('./config.json')
        
        # 加载向量数据库
        vector_manager = VectorStoreManager(api_key=settings.dashscope_api_key, config=settings.to_dict())
        vector_store = vector_manager.load_vector_store(settings.vector_db_dir)
        
        if not vector_store:
            print("❌ 无法加载向量数据库")
            return None, None
        
        print("=== 检查向量数据库内容长度分布 ===\n")
        
        # 获取所有文档
        all_docs = list(vector_store.docstore._dict.values())
        
        if not all_docs:
            print("❌ 向量数据库中没有找到文档")
            return
        
        print(f"📊 总文档数: {len(all_docs)}")
        
        # 按类型统计长度
        length_stats = {
            'text': {'count': 0, 'lengths': [], 'max_length': 0, 'max_content': ''},
            'table': {'count': 0, 'lengths': [], 'max_length': 0, 'max_content': ''},
            'image': {'count': 0, 'lengths': [], 'max_length': 0, 'max_content': ''}
        }
        
        # 超长内容统计（超过2048字符）
        long_content = {
            'text': [],
            'table': [],
            'image': []
        }
        
        # 分析每个文档
        for doc in all_docs:
            content = doc.page_content
            content_length = len(content)
            
            # 获取文档类型
            doc_type = doc.metadata.get('chunk_type', 'unknown')
            if doc_type not in length_stats:
                doc_type = 'text'  # 默认为文本类型
            
            # 更新统计
            length_stats[doc_type]['count'] += 1
            length_stats[doc_type]['lengths'].append(content_length)
            
            if content_length > length_stats[doc_type]['max_length']:
                length_stats[doc_type]['max_length'] = content_length
                length_stats[doc_type]['max_content'] = content[:100] + "..." if len(content) > 100 else content
            
            # 检查是否超长
            if content_length > 2048:
                long_content[doc_type].append({
                    'length': content_length,
                    'content_preview': content[:200] + "..." if len(content) > 200 else content,
                    'metadata': doc.metadata
                })
        
        # 输出统计结果
        for doc_type, stats in length_stats.items():
            if stats['count'] > 0:
                avg_length = sum(stats['lengths']) / len(stats['lengths'])
                print(f"📋 {doc_type.upper()} 类型文档:")
                print(f"   数量: {stats['count']}")
                print(f"   平均长度: {avg_length:.1f} 字符")
                print(f"   最大长度: {stats['max_length']} 字符")
                print(f"   最小长度: {min(stats['lengths'])} 字符")
                print(f"   最大内容预览: {stats['max_content']}")
                print()
        
        # 输出超长内容统计
        total_long = sum(len(content_list) for content_list in long_content.values())
        if total_long > 0:
            print(f"⚠️  发现 {total_long} 个超长内容（超过2048字符）:")
            for doc_type, content_list in long_content.items():
                if content_list:
                    print(f"   {doc_type.upper()}: {len(content_list)} 个")
                    for i, item in enumerate(content_list[:3]):  # 只显示前3个
                        print(f"     {i+1}. 长度: {item['length']} 字符")
                        print(f"        预览: {item['content_preview']}")
                        print(f"        来源: {item['metadata'].get('document_name', 'Unknown')}")
                        print()
        else:
            print("✅ 没有发现超过2048字符的超长内容")
        
        # 分析可能的问题源
        print("🔍 长度分析建议:")
        for doc_type, stats in length_stats.items():
            if stats['count'] > 0:
                max_len = stats['max_length']
                if max_len > 1500:  # 接近限制
                    print(f"   {doc_type.upper()}: 最大长度 {max_len} 接近2048限制，建议关注")
                elif max_len > 1000:
                    print(f"   {doc_type.upper()}: 最大长度 {max_len} 适中")
                else:
                    print(f"   {doc_type.upper()}: 最大长度 {max_len} 安全")
        
        return length_stats, long_content
        
    except Exception as e:
        logger.error(f"检查内容长度时出错: {e}")
        print(f"❌ 检查失败: {e}")
        return None, None

if __name__ == "__main__":
    check_content_lengths()
