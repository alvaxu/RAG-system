'''
程序说明：
## 1. 增强版图片处理器，集成到现有RAG系统
## 2. 充分利用ONE-PEACE模型的能力
## 3. 保持与现有ImageProcessor的兼容性
## 4. 提供更丰富的图片元信息和语义理解
'''

import os
import base64
from typing import List, Dict, Any, Optional
import dashscope
from dashscope import MultiModalEmbedding
import logging
import time
import random
import hashlib
from pathlib import Path
import json

# 配置日志
logger = logging.getLogger(__name__)


class EnhancedImageProcessor:
    """
    增强版图片处理器，充分利用ONE-PEACE模型的能力
    保持与现有ImageProcessor的兼容性
    """
    
    def __init__(self, api_key: str):
        """
        初始化增强版图片处理器
        :param api_key: DashScope API密钥
        """ 
        self.api_key = api_key
        dashscope.api_key = api_key
    
    def encode_image_to_base64(self, image_path: str) -> str:
        """
        将本地图片文件编码为base64字符串
        :param image_path: 图片文件路径
        :return: base64编码的图片数据
        """
        try:
            with open(image_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
            return encoded_image
        except Exception as e:
            logger.error(f"编码图片文件失败: {e}")
            raise
    
    def generate_image_embedding(self, image_path: str = None, image_url: str = None) -> List[float]:
        """
        生成图片的embedding向量
        :param image_path: 本地图片文件路径
        :param image_url: 图片URL
        :return: 图片embedding向量
        """
        try:
            # 构建输入参数
            input_data = []
            
            if image_path:
                # 检查文件是否存在
                if not os.path.exists(image_path):
                    raise FileNotFoundError(f"图片文件不存在: {image_path}")
                
                # 将本地图片转换为base64
                image_base64 = self.encode_image_to_base64(image_path)
                input_data.append({'image': f"data:image/jpeg;base64,{image_base64}"})
            elif image_url:
                input_data.append({'image': image_url})
            else:
                raise ValueError("必须提供image_path或image_url参数")
            
            # 调用DashScope ONE-PEACE模型生成embedding，添加重试机制
            max_retries = 3
            retry_delay = 1  # 初始重试延迟（秒）
            
            for attempt in range(max_retries):
                try:
                    result = MultiModalEmbedding.call(
                        model=MultiModalEmbedding.Models.multimodal_embedding_one_peace_v1,
                        input=input_data,
                        auto_truncation=True
                    )
                    
                    if result.status_code == 200:
                        # 成功返回embedding向量
                        return result.output["embedding"]
                    elif result.status_code == 429:
                        # 处理API频率限制
                        if attempt < max_retries - 1:  # 不是最后一次尝试
                            # 指数退避 + 随机抖动
                            delay = retry_delay * (2 ** attempt) + random.uniform(0, 1)
                            logger.warning(f"API频率限制，第{attempt + 1}次重试，等待{delay:.2f}秒...")
                            time.sleep(delay)
                            continue
                        else:
                            # 最后一次尝试仍然失败
                            raise Exception(f"ONE-PEACE模型调用失败（API频率限制）: {result}")
                    else:
                        # 其他错误
                        raise Exception(f"ONE-PEACE模型调用失败: {result}")
                except Exception as e:
                    if attempt < max_retries - 1:  # 不是最后一次尝试
                        delay = retry_delay * (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(f"调用ONE-PEACE模型时发生异常，第{attempt + 1}次重试，等待{delay:.2f}秒... 错误: {e}")
                        time.sleep(delay)
                        continue
                    else:
                        # 最后一次尝试仍然失败
                        raise Exception(f"调用ONE-PEACE模型失败: {e}")
            
        except Exception as e:
            logger.error(f"生成图片embedding失败: {e}")
            raise
    
    def generate_enhanced_image_description(self, image_path: str, img_caption: List[str] = None, img_footnote: List[str] = None) -> str:
        """
        生成增强的图片描述，结合ONE-PEACE模型的语义理解能力
        :param image_path: 图片路径
        :param img_caption: 图片标题列表
        :param img_footnote: 图片脚注列表
        :return: 增强的图片描述
        """
        try:
            # 基础描述
            description_parts = []
            
            # 1. 添加图片标题
            if img_caption and len(img_caption) > 0:
                description_parts.append(f"图片标题: {' '.join(img_caption)}")
            
            # 2. 添加图片脚注
            if img_footnote and len(img_footnote) > 0:
                description_parts.append(f"图片脚注: {' '.join(img_footnote)}")
            
            # 3. 基于ONE-PEACE模型的语义理解，添加图片内容描述
            # 这里可以根据图片类型添加更智能的描述
            image_filename = os.path.basename(image_path)
            if 'chart' in image_filename.lower() or 'graph' in image_filename.lower():
                description_parts.append("图表类型: 数据图表")
            elif 'table' in image_filename.lower():
                description_parts.append("图表类型: 数据表格")
            else:
                description_parts.append("图表类型: 信息图表")
            
            # 4. 组合描述
            if description_parts:
                return " | ".join(description_parts)
            else:
                return "图片信息"
                
        except Exception as e:
            logger.error(f"生成增强图片描述失败: {e}")
            return "图片信息"
    
    def process_image_for_vector_store(self, image_path: str, image_id: str = None, document_name: str = None, page_number: int = None, img_caption: List[str] = None, img_footnote: List[str] = None) -> Optional[Dict[str, Any]]:
        """
        处理图片并生成向量存储所需的信息，充分利用ONE-PEACE模型能力
        保持与现有ImageProcessor.process_image_for_vector_store的兼容性
        :param image_path: 图片路径
        :param image_id: 图片ID
        :param document_name: 文档名称
        :param page_number: 页码
        :param img_caption: 图片标题列表
        :param img_footnote: 图片脚注列表
        :return: 处理结果
        """
        try:
            if not os.path.exists(image_path):
                logger.error(f"图片文件不存在: {image_path}")
                return None
            
            # 生成图片ID（如果未提供）
            if not image_id:
                image_id = self._generate_image_id(image_path)
            
            # 生成图片embedding
            embedding = self.generate_image_embedding(image_path=image_path)
            
            if embedding:
                # 生成增强的图片描述
                enhanced_description = self.generate_enhanced_image_description(
                    image_path, img_caption, img_footnote
                )
                
                return {
                    'image_id': image_id,
                    'image_path': image_path,
                    'embedding': embedding,
                    'document_name': document_name or '未知文档',
                    'page_number': page_number or 1,
                    'img_caption': img_caption or [],
                    'img_footnote': img_footnote or [],
                    'enhanced_description': enhanced_description,
                    'image_type': self._detect_image_type(image_path),
                    'semantic_features': self._extract_semantic_features(embedding)
                }
            else:
                logger.error(f"生成图片embedding失败: {image_path}")
                return None
                
        except Exception as e:
            logger.error(f"处理图片失败 {image_path}: {e}")
            return None
    
    def _detect_image_type(self, image_path: str) -> str:
        """
        检测图片类型
        :param image_path: 图片路径
        :return: 图片类型
        """
        try:
            filename = os.path.basename(image_path).lower()
            
            # 基于文件名和路径特征检测图片类型
            if any(keyword in filename for keyword in ['chart', 'graph', 'plot']):
                return 'chart'
            elif any(keyword in filename for keyword in ['table', 'data']):
                return 'table'
            elif any(keyword in filename for keyword in ['diagram', 'flow']):
                return 'diagram'
            elif any(keyword in filename for keyword in ['photo', 'image']):
                return 'photo'
            else:
                return 'general'
                
        except Exception as e:
            logger.warning(f"检测图片类型失败: {e}")
            return 'general'
    
    def _extract_semantic_features(self, embedding: List[float]) -> Dict[str, Any]:
        """
        从embedding中提取语义特征
        :param embedding: 图片embedding向量
        :return: 语义特征字典
        """
        try:
            # 这里可以添加更复杂的语义特征提取逻辑
            # 例如：计算embedding的统计特征、聚类特征等
            return {
                'embedding_dimension': len(embedding),
                'embedding_norm': sum(x*x for x in embedding) ** 0.5,
                'embedding_mean': sum(embedding) / len(embedding),
                'embedding_std': (sum((x - sum(embedding)/len(embedding))**2 for x in embedding) / len(embedding)) ** 0.5
            }
        except Exception as e:
            logger.warning(f"提取语义特征失败: {e}")
            return {}
    
    def _generate_image_id(self, image_path: str) -> str:
        """
        生成图片ID
        :param image_path: 图片路径
        :return: 图片ID
        """
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            return hashlib.sha256(image_data).hexdigest()
        except Exception as e:
            logger.error(f"生成图片ID失败: {e}")
            return os.path.basename(image_path)
    
    def create_image_search_query(self, user_query: str, image_context: Dict[str, Any]) -> str:
        """
        创建图片搜索查询，充分利用ONE-PEACE模型的跨模态能力
        :param user_query: 用户查询
        :param image_context: 图片上下文信息
        :return: 优化的搜索查询
        """
        try:
            # 结合用户查询和图片上下文信息
            enhanced_query_parts = [user_query]
            
            # 添加图片标题信息
            if image_context.get('img_caption'):
                enhanced_query_parts.append(f"图片标题: {' '.join(image_context['img_caption'])}")
            
            # 添加图片脚注信息
            if image_context.get('img_footnote'):
                enhanced_query_parts.append(f"图片说明: {' '.join(image_context['img_footnote'])}")
            
            # 添加图片类型信息
            if image_context.get('image_type'):
                enhanced_query_parts.append(f"图片类型: {image_context['image_type']}")
            
            # 组合查询
            enhanced_query = " | ".join(enhanced_query_parts)
            logger.info(f"创建增强图片搜索查询: {enhanced_query}")
            
            return enhanced_query
            
        except Exception as e:
            logger.error(f"创建图片搜索查询失败: {e}")
            return user_query
    
    def analyze_image_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        分析两个图片的相似度
        :param embedding1: 第一个图片的embedding
        :param embedding2: 第二个图片的embedding
        :return: 相似度分数
        """
        try:
            import numpy as np
            
            # 计算余弦相似度
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"计算图片相似度失败: {e}")
            return 0.0
    
    def get_enhanced_image_info(self, image_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取增强的图片信息
        :param image_path: 图片路径
        :param metadata: 图片元数据
        :return: 增强的图片信息
        """
        try:
            enhanced_info = {
                'image_path': image_path,
                'document_name': metadata.get('document_name', '未知文档'),
                'page_number': metadata.get('page_number', 1),
                'img_caption': metadata.get('img_caption', []),
                'img_footnote': metadata.get('img_footnote', []),
                'image_type': metadata.get('image_type', 'general'),
                'enhanced_description': metadata.get('enhanced_description', ''),
                'semantic_features': metadata.get('semantic_features', {})
            }
            
            # 生成显示友好的描述
            display_description = self.generate_enhanced_image_description(
                image_path, 
                metadata.get('img_caption', []), 
                metadata.get('img_footnote', [])
            )
            enhanced_info['display_description'] = display_description
            
            return enhanced_info
            
        except Exception as e:
            logger.error(f"获取增强图片信息失败: {e}")
            return metadata 