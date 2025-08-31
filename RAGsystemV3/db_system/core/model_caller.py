"""
LangChain模型调用器

基于LangChain框架的模型调用接口，重构原有的自开发版本。
支持文本和图片的embedding生成，集成DashScope API。
"""

import os
import time
import logging
import random
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

try:
    from langchain_community.embeddings import DashScopeEmbeddings
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logging.warning("LangChain未安装，模型调用功能将不可用")

try:
    import dashscope
    from dashscope import MultiModalEmbedding
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False
    logging.warning("DashScope未安装，多模态功能将不可用")

class LangChainModelCaller:
    """
    LangChain模型调用器主类
    
    功能：
    - 集成LangChain的DashScope Embeddings
    - 支持文本和图片的向量化
    - 提供API调用重试和错误处理
    - 支持批量处理和限流控制
    """

    def __init__(self, config_manager):
        """
        初始化LangChain模型调用器
        
        :param config_manager: 配置管理器
        """
        if not LANGCHAIN_AVAILABLE:
            raise RuntimeError("LangChain未安装，无法初始化模型调用器")
        
        self.config_manager = config_manager
        self.config = config_manager.get_all_config()
        
        # 获取配置参数
        self.text_embedding_model = self.config.get('vectorization', {}).get('text_embedding_model', 'text-embedding-v1')
        self.image_embedding_model = self.config.get('vectorization', {}).get('image_embedding_model', 'multimodal-embedding-one-peace-v1')
        
        # API限流配置
        self.batch_size = self.config.get('api_rate_limiting', {}).get('vectorization_batch_size', 10)
        self.delay_seconds = self.config.get('api_rate_limiting', {}).get('vectorization_delay_seconds', 1)
        self.max_retries = self.config.get('api_rate_limiting', {}).get('max_retries', 3)
        
        # 初始化embedding模型
        self._initialize_models()
        
        logging.info("LangChain模型调用器初始化完成")

    def _initialize_models(self):
        """初始化embedding模型"""
        try:
            # 获取API密钥
            api_key = self.config_manager.get_environment_manager().get_required_var('DASHSCOPE_API_KEY')
            if not api_key:
                raise ValueError("未找到有效的DashScope API密钥")
            
            # 设置DashScope API密钥
            dashscope.api_key = api_key
            
            # 初始化文本embedding模型
            self.text_embeddings = DashScopeEmbeddings(
                dashscope_api_key=api_key,
                model=self.text_embedding_model
            )
            
            # 图片embedding模型不需要LangChain包装，直接使用dashscope.MultiModalEmbedding
            # 检查DashScope是否可用
            if DASHSCOPE_AVAILABLE:
                logging.info(f"图片embedding模型将直接使用: {self.image_embedding_model}")
            else:
                logging.warning("DashScope不可用，图片embedding功能将不可用")
            
            logging.info(f"文本embedding模型初始化成功: {self.text_embedding_model}")
            
        except Exception as e:
            logging.error(f"Embedding模型初始化失败: {e}")
            raise

    def call_text_embedding(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        调用文本embedding模型
        
        :param text: 输入文本
        :param kwargs: 其他参数
        :return: 调用结果字典
        """
        try:
            if not text or not text.strip():
                raise ValueError("输入文本为空")
            
            logging.info(f"开始调用文本embedding模型: {text[:50]}...")
            
            # 使用LangChain的embed_query方法
            embedding = self.text_embeddings.embed_query(text)
            
            result = {
                'success': True,
                'embedding': embedding,
                'model': self.text_embedding_model,
                'dimension': len(embedding),
                'input_text': text,
                'timestamp': time.time()
            }
            
            logging.info(f"文本embedding调用成功: {len(embedding)} 维向量")
            return result
            
        except Exception as e:
            error_msg = f"文本embedding调用失败: {str(e)}"
            logging.error(error_msg)
            
            return {
                'success': False,
                'error': str(e),
                'model': self.text_embedding_model,
                'input_text': text,
                'timestamp': time.time()
            }

    def call_image_embedding(self, image_input: Union[str, bytes], **kwargs) -> Dict[str, Any]:
        """
        调用图片embedding模型
        
        :param image_input: 图片输入（路径、URL或base64）
        :param kwargs: 其他参数
        :return: 调用结果字典
        """
        if not DASHSCOPE_AVAILABLE:
            return {
                'success': False,
                'error': "DashScope不可用，无法调用图片embedding模型",
                'model': self.image_embedding_model,
                'input_image': str(image_input)[:100] if image_input else None,
                'timestamp': time.time()
            }
        
        if not image_input:
            return {
                'success': False,
                'error': "图片输入为空",
                'model': self.image_embedding_model,
                'input_image': None,
                'timestamp': time.time()
            }
        
        logging.info(f"开始调用图片embedding模型: {str(image_input)[:50]}...")
        
        try:
            # 构建输入参数
            input_data = []
            
            if isinstance(image_input, str):
                if image_input.startswith('http'):
                    # URL图片
                    input_data.append({'image': image_input})
                elif image_input.startswith('data:image'):
                    # base64编码图片
                    input_data.append({'image': image_input})
                else:
                    # 本地图片路径
                    if not os.path.exists(image_input):
                        raise FileNotFoundError(f"图片文件不存在: {image_input}")
                    
                    # 转换为base64
                    image_base64 = self._encode_image_to_base64(image_input)
                    input_data.append({'image': f"data:image/jpeg;base64,{image_base64}"})
            else:
                # 二进制数据
                image_base64 = self._encode_bytes_to_base64(image_input)
                input_data.append({'image': f"data:image/jpeg;base64,{image_base64}"})
            
            # 调用DashScope API，添加重试机制（使用老系统的延迟策略）
            max_retries = self.max_retries
            retry_delay = 5  # 使用老系统的初始延迟：5秒
            
            for attempt in range(max_retries):
                try:
                    result = MultiModalEmbedding.call(
                        model=self.image_embedding_model,
                        input=input_data,
                        auto_truncation=True
                    )
                    
                    if result.status_code == 200:
                        embedding = result.output["embedding"]
                        
                        return {
                            'success': True,
                            'embedding': embedding,
                            'model': self.image_embedding_model,
                            'dimension': len(embedding),
                            'input_image': str(image_input)[:100],
                            'timestamp': time.time()
                        }
                    elif result.status_code == 429:
                        # 处理API频率限制（使用老系统的延迟策略）
                        if attempt < max_retries - 1:  # 不是最后一次尝试
                            # 指数退避 + 随机抖动：5 * (2^attempt) + random.uniform(2, 5)
                            delay = retry_delay * (2 ** attempt) + random.uniform(2, 5)
                            logging.warning(f"API频率限制，第{attempt + 1}次重试，等待{delay:.2f}秒...")
                            time.sleep(delay)
                            continue
                        else:
                            # 最后一次尝试仍然失败
                            error_msg = f"API频率限制，重试{max_retries}次后仍然失败"
                            logging.error(error_msg)
                            return {
                                'success': False,
                                'error': error_msg,
                                'model': self.image_embedding_model,
                                'input_image': str(image_input)[:100],
                                'timestamp': time.time()
                            }
                    else:
                        # 其他错误状态码
                        error_msg = f"API调用失败，状态码: {result.status_code}"
                        logging.error(error_msg)
                        return {
                            'success': False,
                            'error': error_msg,
                            'model': self.image_embedding_model,
                            'input_image': str(image_input)[:100],
                            'timestamp': time.time()
                        }
                        
                except Exception as e:
                    if attempt < max_retries - 1:  # 不是最后一次尝试
                        delay = retry_delay * (2 ** attempt) + random.uniform(2, 5)
                        logging.warning(f"调用图片embedding模型时发生异常，第{attempt + 1}次重试，等待{delay:.2f}秒... 错误: {e}")
                        time.sleep(delay)
                        continue
                    else:
                        # 最后一次尝试仍然失败
                        error_msg = f"调用图片embedding模型失败: {str(e)}"
                        logging.error(error_msg)
                        return {
                            'success': False,
                            'error': error_msg,
                            'model': self.image_embedding_model,
                            'input_image': str(image_input)[:100],
                            'timestamp': time.time()
                        }
                
        except Exception as e:
            error_msg = f"图片embedding调用失败: {str(e)}"
            logging.error(error_msg)
            return {
                'success': False,
                'error': str(e),
                'model': self.image_embedding_model,
                'input_image': str(image_input)[:100] if image_input else None,
                'timestamp': time.time()
            }

    def _encode_image_to_base64(self, image_path: str) -> str:
        """
        将图片文件编码为base64
        
        :param image_path: 图片文件路径
        :return: base64编码字符串
        """
        try:
            import base64
            
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
                base64_string = base64.b64encode(image_data).decode('utf-8')
                return base64_string
                
        except Exception as e:
            logging.error(f"图片base64编码失败: {e}")
            raise

    def _encode_bytes_to_base64(self, image_bytes: bytes) -> str:
        """
        将二进制数据编码为base64
        
        :param image_bytes: 图片二进制数据
        :return: base64编码字符串
        """
        try:
            import base64
            
            base64_string = base64.b64encode(image_bytes).decode('utf-8')
            return base64_string
            
        except Exception as e:
            logging.error(f"二进制数据base64编码失败: {e}")
            raise

    def call_text_embedding_batch(self, texts: List[str], **kwargs) -> List[Dict[str, Any]]:
        """
        批量调用文本embedding模型
        
        :param texts: 文本列表
        :param kwargs: 其他参数
        :return: 调用结果列表
        """
        try:
            if not texts:
                return []
            
            logging.info(f"开始批量调用文本embedding模型: {len(texts)} 个文本")
            
            results = []
            for i, text in enumerate(texts):
                try:
                    # 调用单个文本embedding
                    result = self.call_text_embedding(text, **kwargs)
                    results.append(result)
                    
                    # 批量大小控制和延迟
                    if (i + 1) % self.batch_size == 0 and i < len(texts) - 1:
                        time.sleep(self.delay_seconds)
                        logging.info(f"已处理 {i + 1}/{len(texts)} 个文本")
                    
                except Exception as e:
                    logging.error(f"批量处理第 {i} 个文本失败: {e}")
                    error_result = {
                        'success': False,
                        'error': str(e),
                        'model': self.text_embedding_model,
                        'input_text': text,
                        'timestamp': time.time()
                    }
                    results.append(error_result)
            
            success_count = len([r for r in results if r['success']])
            logging.info(f"批量文本embedding完成，成功处理 {success_count}/{len(texts)} 个文本")
            return results
            
        except Exception as e:
            logging.error(f"批量文本embedding失败: {e}")
            return [{
                'success': False,
                'error': str(e),
                'model': self.text_embedding_model,
                'input_text': text,
                'timestamp': time.time()
            } for text in texts]

    def call_image_embedding_batch(self, image_inputs: List[Union[str, bytes]], **kwargs) -> List[Dict[str, Any]]:
        """
        批量调用图片embedding模型
        
        :param image_inputs: 图片输入列表
        :param kwargs: 其他参数
        :return: 调用结果列表
        """
        try:
            if not DASHSCOPE_AVAILABLE:
                raise RuntimeError("DashScope不可用，无法调用图片embedding模型")
            
            if not image_inputs:
                return []
            
            logging.info(f"开始批量调用图片embedding模型: {len(image_inputs)} 个图片")
            
            results = []
            for i, image_input in enumerate(image_inputs):
                try:
                    # 调用单个图片embedding
                    result = self.call_image_embedding(image_input, **kwargs)
                    results.append(result)
                    
                    # 批量大小控制和延迟
                    if (i + 1) % self.batch_size == 0 and i < len(image_inputs) - 1:
                        time.sleep(self.delay_seconds)
                        logging.info(f"已处理 {i + 1}/{len(image_inputs)} 个图片")
                    
                except Exception as e:
                    logging.error(f"批量处理第 {i} 个图片失败: {e}")
                    error_result = {
                        'success': False,
                        'error': str(e),
                        'model': self.image_embedding_model,
                        'input_image': str(image_input)[:100] if image_input else None,
                        'timestamp': time.time()
                    }
                    results.append(error_result)
            
            success_count = len([r for r in results if r['success']])
            logging.info(f"批量图片embedding完成，成功处理 {success_count}/{len(image_inputs)} 个图片")
            return results
            
        except Exception as e:
            logging.error(f"批量图片embedding失败: {e}")
            return [{
                'success': False,
                'error': str(e),
                'model': self.image_embedding_model,
                'input_image': str(img)[:100] if img else None,
                'timestamp': time.time()
            } for img in image_inputs]

    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        :return: 模型信息字典
        """
        return {
            'text_embedding_model': self.text_embedding_model,
            'image_embedding_model': self.image_embedding_model,
            'langchain_available': LANGCHAIN_AVAILABLE,
            'dashscope_available': DASHSCOPE_AVAILABLE,
            'batch_size': self.batch_size,
            'delay_seconds': self.delay_seconds,
            'max_retries': self.max_retries
        }

    def test_connection(self) -> Dict[str, Any]:
        """
        测试API连接
        
        :return: 连接测试结果
        """
        try:
            # 测试文本embedding
            test_text = "测试连接"
            text_result = self.call_text_embedding(test_text)
            
            # 测试图片embedding（如果可用）
            image_result = None
            if DASHSCOPE_AVAILABLE:
                # 创建一个简单的测试图片或使用默认图片
                test_image_path = self._find_test_image()
                if test_image_path:
                    image_result = self.call_image_embedding(test_image_path)
            
            return {
                'success': True,
                'text_embedding_test': text_result,
                'image_embedding_test': image_result,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logging.error(f"连接测试失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': time.time()
            }

    def _find_test_image(self) -> Optional[str]:
        """
        查找测试图片
        
        :return: 测试图片路径或None
        """
        try:
            # 常见的测试图片路径
            test_paths = [
                './test_images/test.jpg',
                './images/test.png',
                './assets/test_image.jpg'
            ]
            
            for path in test_paths:
                if os.path.exists(path):
                    return path
            
            return None
            
        except Exception:
            return None
