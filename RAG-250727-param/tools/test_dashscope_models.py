#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：

## 1. 测试DashScope API的可用模型
## 2. 验证multimodal-embedding-one-peace-v1模型是否存在
## 3. 测试其他可能的模型名称
## 4. 提供API调用测试功能
"""

import os
import sys
import logging
import json
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.api_key_manager import APIKeyManager

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_api_key():
    """测试API密钥获取"""
    logger.info("=== 测试API密钥获取 ===")
    
    # 测试环境变量
    env_key = os.getenv('MY_DASHSCOPE_API_KEY', '')
    logger.info(f"环境变量MY_DASHSCOPE_API_KEY: {'已设置' if env_key else '未设置'}")
    
    # 测试API密钥管理器
    api_key = APIKeyManager.get_dashscope_api_key()
    if api_key:
        logger.info(f"API密钥管理器返回密钥: {'已设置' if api_key else '未设置'}")
        # 隐藏密钥内容，只显示前8位和后4位
        masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
        logger.info(f"密钥格式: {masked_key}")
    else:
        logger.error("未找到有效的DashScope API密钥")
        return False
    
    return True

def test_dashscope_import():
    """测试DashScope模块导入"""
    logger.info("=== 测试DashScope模块导入 ===")
    
    try:
        import dashscope
        logger.info(f"DashScope版本: {dashscope.__version__}")
        return True
    except ImportError as e:
        logger.error(f"DashScope模块导入失败: {e}")
        return False
    except Exception as e:
        logger.error(f"DashScope模块导入异常: {e}")
        return False

def test_available_models():
    """测试可用的模型"""
    logger.info("=== 测试可用模型 ===")
    
    try:
        import dashscope
        from dashscope import MultiModalEmbedding
        
        # 检查MultiModalEmbedding.Models
        if hasattr(MultiModalEmbedding, 'Models'):
            logger.info("MultiModalEmbedding.Models 属性存在")
            models = MultiModalEmbedding.Models
            logger.info(f"可用模型: {dir(models)}")
            
            # 尝试获取模型列表
            for attr in dir(models):
                if not attr.startswith('_'):
                    try:
                        model_value = getattr(models, attr)
                        logger.info(f"模型 {attr}: {model_value}")
                    except Exception as e:
                        logger.warning(f"获取模型 {attr} 失败: {e}")
        else:
            logger.warning("MultiModalEmbedding.Models 属性不存在")
            
        return True
        
    except Exception as e:
        logger.error(f"测试可用模型失败: {e}")
        return False

def test_model_names():
    """测试可能的模型名称"""
    logger.info("=== 测试可能的模型名称 ===")
    
    # 可能的模型名称列表
    possible_models = [
        'multimodal-embedding-one-peace-v1',
        'multimodal_embedding_one_peace_v1',
        'multimodal-embedding-one-peace',
        'multimodal-embedding-v1',
        'multimodal-embedding',
        'one-peace-v1',
        'one_peace_v1'
    ]
    
    try:
        import dashscope
        from dashscope import MultiModalEmbedding
        
        api_key = APIKeyManager.get_dashscope_api_key()
        if not api_key:
            logger.error("未找到API密钥，无法测试模型")
            return False
            
        dashscope.api_key = api_key
        
        for model_name in possible_models:
            logger.info(f"测试模型: {model_name}")
            try:
                # 测试文本输入
                result = MultiModalEmbedding.call(
                    model=model_name,
                    input=[{'text': '测试文本'}]
                )
                
                if result.status_code == 200:
                    logger.info(f"✓ 模型 {model_name} 可用")
                    logger.info(f"  状态码: {result.status_code}")
                    logger.info(f"  输出格式: {list(result.output.keys()) if hasattr(result, 'output') else '无输出'}")
                    
                    # 检查向量维度
                    if hasattr(result, 'output') and result.output:
                        if "embedding" in result.output:
                            embedding = result.output["embedding"]
                            logger.info(f"  向量维度: {len(embedding)}")
                        elif "embeddings" in result.output and len(result.output["embeddings"]) > 0:
                            embedding = result.output["embeddings"][0]["embedding"]
                            logger.info(f"  向量维度: {len(embedding)}")
                    
                    return model_name  # 返回第一个可用的模型
                else:
                    logger.warning(f"✗ 模型 {model_name} 不可用: {result.status_code}")
                    if hasattr(result, 'message'):
                        logger.warning(f"  错误信息: {result.message}")
                        
            except Exception as e:
                logger.warning(f"✗ 模型 {model_name} 测试失败: {e}")
                
    except Exception as e:
        logger.error(f"测试模型名称失败: {e}")
        
    return None

def test_text_embedding_fallback():
    """测试文本embedding作为备选方案"""
    logger.info("=== 测试文本embedding备选方案 ===")
    
    try:
        import dashscope
        from dashscope import TextEmbedding
        
        api_key = APIKeyManager.get_dashscope_api_key()
        if not api_key:
            logger.error("未找到API密钥，无法测试文本embedding")
            return False
            
        dashscope.api_key = api_key
        
        # 测试text-embedding-v1
        result = TextEmbedding.call(
            model='text-embedding-v1',
            input=['测试文本']
        )
        
        if result.status_code == 200:
            logger.info("✓ text-embedding-v1 可用")
            logger.info(f"  状态码: {result.status_code}")
            
            if hasattr(result, 'output') and result.output:
                if "embeddings" in result.output and len(result.output["embeddings"]) > 0:
                    embedding = result.output["embeddings"][0]["embedding"]
                    logger.info(f"  向量维度: {len(embedding)}")
                    return True
        else:
            logger.warning(f"✗ text-embedding-v1 不可用: {result.status_code}")
            if hasattr(result, 'message'):
                logger.warning(f"  错误信息: {result.message}")
                
    except Exception as e:
        logger.error(f"测试文本embedding失败: {e}")
        
    return False

def main():
    """主函数"""
    logger.info("开始测试DashScope API")
    
    # 1. 测试API密钥
    if not test_api_key():
        logger.error("API密钥测试失败，退出")
        return
    
    # 2. 测试模块导入
    if not test_dashscope_import():
        logger.error("模块导入测试失败，退出")
        return
    
    # 3. 测试可用模型
    test_available_models()
    
    # 4. 测试模型名称
    working_model = test_model_names()
    
    # 5. 测试文本embedding备选方案
    text_embedding_available = test_text_embedding_fallback()
    
    # 6. 总结
    logger.info("=== 测试总结 ===")
    if working_model:
        logger.info(f"✓ 找到可用的多模态模型: {working_model}")
    else:
        logger.warning("✗ 未找到可用的多模态模型")
        
    if text_embedding_available:
        logger.info("✓ text-embedding-v1 可用，可作为备选方案")
    else:
        logger.warning("✗ text-embedding-v1 不可用")
    
    # 7. 建议
    logger.info("=== 建议 ===")
    if working_model:
        logger.info(f"建议更新配置文件中的模型名称为: {working_model}")
    else:
        logger.info("建议检查DashScope官方文档，确认最新的模型名称")
        logger.info("或者暂时使用text-embedding-v1作为备选方案")

if __name__ == "__main__":
    main()
