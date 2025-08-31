"""
模型调用器

负责统一管理各种AI模型的调用，为ImageProcessor、TextProcessor和TableProcessor提供一致的模型调用接口。
"""

import os
import json
import time
import logging
import requests
from typing import List, Dict, Any, Optional
import base64
from pathlib import Path

class ModelCaller:
    """
    简化的模型调用器主类

    功能：
    - 统一管理各种AI模型的调用
    - 为所有处理器提供一致的接口
    - 基本的错误处理和重试机制
    - 配置验证和管理
    """

    def __init__(self, config_manager):
        """
        初始化模型调用器

        :param config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        self.config = config_manager.get_all_config()
        self._validate_configuration()

        # DASHSCOPE API配置
        self.api_base_url = "https://dashscope.aliyuncs.com/api/v1"

        # 重试配置
        self.max_retries = 3
        self.retry_delay = 1

        logging.info("ModelCaller初始化完成")

    def _validate_configuration(self):
        """验证配置"""
        required_configs = [
            'vectorization.text_embedding_model',
            'vectorization.image_embedding_model',
            'image_processing.enhancement_model'
        ]

        for config_path in required_configs:
            value = self.config
            for key in config_path.split('.'):
                value = value.get(key, {})
            if not value:
                raise ValueError(f"配置中缺少必需参数: {config_path}")

        # 验证环境变量
        if not os.getenv('DASHSCOPE_API_KEY'):
            raise ValueError("环境变量 DASHSCOPE_API_KEY 未设置")

        logging.info("ModelCaller配置验证通过")

    def call_text_embedding(self, text: str, metadata: Dict = None) -> List[float]:
        """
        调用文本嵌入模型

        :param text: 待向量化的文本
        :param metadata: 相关元数据
        :return: 文本向量
        """
        try:
            # 获取模型配置
            model_name = self.config.get('vectorization', {}).get('text_embedding_model', 'text-embedding-v1')
            api_key = os.getenv('DASHSCOPE_API_KEY')

            if not api_key:
                raise ValueError("DASHSCOPE_API_KEY环境变量未设置")

            # 文本预处理
            processed_text = self._preprocess_text(text)

            # 调用DASHSCOPE API
            response = self._call_dashscope_text_api(model_name, processed_text, api_key)
            embedding = self._extract_text_embedding(response)

            return embedding

        except Exception as e:
            self._handle_error(e, 'text_embedding')
            raise

    def call_image_enhancement(self, image_path: str, metadata: Dict = None) -> str:
        """
        调用图片增强模型

        :param image_path: 图片文件路径
        :param metadata: 相关元数据
        :return: 增强描述文本
        """
        try:
            # 获取模型配置
            model_name = self.config.get('image_processing', {}).get('enhancement_model', 'qwen-vl-plus')
            api_key = os.getenv('DASHSCOPE_API_KEY')

            if not api_key:
                raise ValueError("DASHSCOPE_API_KEY环境变量未设置")

            # 图片文件验证
            self._validate_image_file(image_path)

            # 调用DASHSCOPE API
            response = self._call_dashscope_image_api(model_name, image_path, api_key)
            description = self._extract_image_description(response)

            return description

        except Exception as e:
            self._handle_error(e, 'image_enhancement')
            raise

    # 移除所有测试模式相关方法，现在只使用真实API

    def call_visual_embedding(self, image_path: str, metadata: Dict = None) -> List[float]:
        """
        调用视觉向量模型

        :param image_path: 图片文件路径
        :param metadata: 相关元数据
        :return: 视觉向量
        """
        try:
            # 获取模型配置
            model_name = self.config.get('vectorization', {}).get('image_embedding_model', 'multimodal-embedding-one-peace-v1')
            api_key = os.getenv('DASHSCOPE_API_KEY')

            if not api_key:
                raise ValueError("DASHSCOPE_API_KEY环境变量未设置")

            # 图片文件验证
            self._validate_image_file(image_path)

            # 调用DASHSCOPE API
            response = self._call_dashscope_visual_api(model_name, image_path, api_key)
            embedding = self._extract_visual_embedding(response)

            return embedding

        except Exception as e:
            self._handle_error(e, 'visual_embedding')
            raise

    def get_model_info(self, model_type: str) -> Dict[str, Any]:
        """
        获取模型信息

        :param model_type: 模型类型 (text_embedding, image_enhancement, visual_embedding)
        :return: 模型信息
        """
        model_configs = {
            'text_embedding': {
                'model_name': self.config.get('vectorization', {}).get('text_embedding_model', 'text-embedding-v1'),
                'type': 'text_embedding'
            },
            'image_enhancement': {
                'model_name': self.config.get('image_processing', {}).get('enhancement_model', 'qwen-vl-plus'),
                'type': 'image_enhancement'
            },
            'visual_embedding': {
                'model_name': self.config.get('vectorization', {}).get('image_embedding_model', 'multimodal-embedding-one-peace-v1'),
                'type': 'visual_embedding'
            }
        }

        return model_configs.get(model_type, {})

    def _preprocess_text(self, text: str) -> str:
        """文本预处理"""
        if not text:
            return ""

        # 移除多余的空白字符
        text = ' '.join(text.split())

        # 限制文本长度（DASHSCOPE API限制）
        max_length = 2000
        if len(text) > max_length:
            text = text[:max_length]
            logging.warning(f"文本过长，已截断到{max_length}字符")

        return text

    def _validate_image_file(self, image_path: str):
        """验证图片文件"""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片文件不存在: {image_path}")

        if not os.path.isfile(image_path):
            raise ValueError(f"路径不是文件: {image_path}")

        # 检查文件扩展名
        valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.webp']
        file_ext = Path(image_path).suffix.lower()

        if file_ext not in valid_extensions:
            raise ValueError(f"不支持的图片格式: {file_ext}，支持格式: {valid_extensions}")

        # 检查文件大小（限制为10MB）
        file_size = os.path.getsize(image_path)
        max_size = 10 * 1024 * 1024  # 10MB

        if file_size > max_size:
            raise ValueError(f"图片文件过大: {file_size} bytes，最大限制: {max_size} bytes")

    def _call_dashscope_text_api(self, model_name: str, text: str, api_key: str) -> Dict:
        """调用DASHSCOPE文本API"""
        url = f"{self.api_base_url}/services/embeddings/text-embedding/text-embedding"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": model_name,
            "input": {
                "texts": [text]
            }
        }

        return self._make_request(url, headers, data)

    def _call_dashscope_image_api(self, model_name: str, image_path: str, api_key: str) -> Dict:
        """调用DASHSCOPE图片API"""
        url = f"{self.api_base_url}/services/aigc/multimodal-generation/generation"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # 读取图片并编码为base64
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

        data = {
            "model": model_name,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"image": f"data:image/jpeg;base64,{encoded_image}"},
                            {"text": "请详细描述这张图片的内容，包括场景、物体、颜色、布局等信息。"}
                        ]
                    }
                ]
            }
        }

        return self._make_request(url, headers, data)

    def _call_dashscope_visual_api(self, model_name: str, image_path: str, api_key: str) -> Dict:
        """调用DASHSCOPE视觉向量API"""
        url = f"{self.api_base_url}/services/embeddings/multimodal-embedding/multimodal-embedding"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # 读取图片并编码为base64
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

        data = {
            "model": model_name,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"image": f"data:image/jpeg;base64,{encoded_image}"}
                        ]
                    }
                ]
            }
        }

        return self._make_request(url, headers, data)

    def _make_request(self, url: str, headers: Dict, data: Dict, max_retries: int = None) -> Dict:
        """发送HTTP请求"""
        if max_retries is None:
            max_retries = self.max_retries

        last_exception = None

        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=headers, json=data, timeout=60)

                if response.status_code == 200:
                    return response.json()
                else:
                    error_msg = f"API请求失败，状态码: {response.status_code}, 响应: {response.text}"
                    logging.error(error_msg)
                    raise Exception(error_msg)

            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < max_retries - 1:
                    logging.warning(f"API请求失败，重试中 ({attempt + 1}/{max_retries}): {e}")
                    time.sleep(self.retry_delay)
                else:
                    logging.error(f"API请求失败，已达到最大重试次数: {e}")
                    raise e
            except Exception as e:
                last_exception = e
                logging.error(f"请求处理出错: {e}")
                raise e

        if last_exception:
            raise last_exception

    def _extract_text_embedding(self, response: Dict) -> List[float]:
        """提取文本嵌入向量"""
        try:
            if response.get('code') != 0:
                raise Exception(f"API响应错误: {response.get('message', '未知错误')}")

            embeddings = response.get('data', {}).get('embeddings', [])
            if not embeddings:
                raise Exception("响应中未找到嵌入向量")

            return embeddings[0].get('embedding', [])

        except Exception as e:
            logging.error(f"提取文本嵌入向量失败: {e}")
            raise

    def _extract_image_description(self, response: Dict) -> str:
        """提取图片描述"""
        try:
            if response.get('code') != 0:
                raise Exception(f"API响应错误: {response.get('message', '未知错误')}")

            choices = response.get('data', {}).get('choices', [])
            if not choices:
                raise Exception("响应中未找到生成结果")

            return choices[0].get('message', {}).get('content', '')

        except Exception as e:
            logging.error(f"提取图片描述失败: {e}")
            raise

    def _extract_visual_embedding(self, response: Dict) -> List[float]:
        """提取视觉嵌入向量"""
        try:
            if response.get('code') != 0:
                raise Exception(f"API响应错误: {response.get('message', '未知错误')}")

            embeddings = response.get('data', {}).get('embeddings', [])
            if not embeddings:
                raise Exception("响应中未找到嵌入向量")

            return embeddings[0].get('embedding', [])

        except Exception as e:
            logging.error(f"提取视觉嵌入向量失败: {e}")
            raise

    def _handle_error(self, error: Exception, operation: str):
        """错误处理"""
        error_msg = f"ModelCaller {operation} 失败: {str(error)}"
        logging.error(error_msg)

        # 记录到失败处理器（如果配置了）
        try:
            failure_handler = self.config_manager.get_failure_handler()
            if failure_handler:
                failure_handler.record_failure(
                    image_info={'operation': operation},
                    error_type=f'{operation}_error',
                    error_message=str(error)
                )
        except Exception as e:
            logging.warning(f"记录失败信息时出错: {e}")


if __name__ == "__main__":
    # 测试ModelCaller
    from v3.config.config_manager import ConfigManager

    config_manager = ConfigManager()
    if config_manager.load_config():
        try:
            model_caller = ModelCaller(config_manager)

            # 测试文本嵌入
            text = "这是一个测试文本"
            embedding = model_caller.call_text_embedding(text)
            print(f"文本嵌入向量维度: {len(embedding)}")

        except Exception as e:
            print(f"ModelCaller测试失败: {e}")
    else:
        print("配置加载失败，无法测试ModelCaller")
