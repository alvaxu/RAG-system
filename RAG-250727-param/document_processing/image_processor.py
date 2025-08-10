'''
程序说明：
## 1. 该模块用于处理图片embedding，支持将图片转换为向量表示
## 2. 使用DashScope的ONE-PEACE多模态embedding模型
## 3. 支持本地图片文件和URL图片的处理
## 4. 与现有向量存储系统集成
## 5. 保持与现有系统的兼容性
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

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImageProcessor:
    """
    图片处理器类，用于处理图片embedding
    """
    
    def __init__(self, api_key: str, config: Dict[str, Any] = None):
        """
        初始化图片处理器
        :param api_key: DashScope API密钥
        :param config: 配置字典，如果为None则从配置文件加载
        """ 
        self.api_key = api_key
        dashscope.api_key = api_key
        
        # 存储配置对象
        self.config = config
        
        # 检查是否启用图像增强功能
        self.enhancement_enabled = self._check_enhancement_config(config)
        self.enhancement_config = self._load_enhancement_config(config)
        
        if self.enhancement_enabled:
            try:
                from .image_enhancer import ImageEnhancer
                self.image_enhancer = ImageEnhancer(api_key, self.enhancement_config)
                print("🚀 图像增强功能已启用")
            except Exception as e:
                logger.warning(f"图像增强功能初始化失败: {e}")
                self.enhancement_enabled = False
    
    def _check_enhancement_config(self, config: Dict[str, Any] = None) -> bool:
        """
        检查是否启用图像增强功能
        :param config: 配置字典，如果为None则从配置文件加载
        :return: 是否启用增强功能
        """
        try:
            if config is not None:
                # 使用传入的配置，支持嵌套的image_processing节点
                if 'image_processing' in config:
                    return config['image_processing'].get('enable_enhancement', False)
                else:
                    return config.get('enable_enhancement', False)
            else:
                # 从配置文件加载（备用方案）
                from config.settings import Settings
                settings = Settings.load_from_file("config.json")
                return settings.enable_enhancement
        except Exception as e:
            logger.warning(f"检查增强配置失败: {e}")
            return False  # 默认禁用
    
    def _load_enhancement_config(self, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        加载图像增强配置
        :param config: 配置字典，如果为None则从配置文件加载
        :return: 增强配置字典
        """
        try:
            if config is not None:
                # 使用传入的配置，支持嵌套的image_processing节点
                if 'image_processing' in config:
                    image_config = config['image_processing']
                    return {
                        'enable_enhancement': image_config.get('enable_enhancement', False),
                        'enhancement_model': image_config.get('enhancement_model', 'qwen-vl-plus'),
                        'enhancement_max_tokens': image_config.get('enhancement_max_tokens', 1000),
                        'enhancement_temperature': image_config.get('enhancement_temperature', 0.1),
                        'enhancement_batch_size': image_config.get('enhancement_batch_size', 5),
                        'enable_progress_logging': image_config.get('enable_progress_logging', True)
                    }
                else:
                    # 使用传入的配置
                    return {
                        'enable_enhancement': config.get('enable_enhancement', False),
                        'enhancement_model': config.get('enhancement_model', 'qwen-vl-plus'),
                        'enhancement_max_tokens': config.get('enhancement_max_tokens', 1000),
                        'enhancement_temperature': config.get('enhancement_temperature', 0.1),
                        'enhancement_batch_size': config.get('enhancement_batch_size', 5),
                        'enable_progress_logging': config.get('enable_progress_logging', True)
                    }
            else:
                # 从配置文件加载（备用方案）
                from config.settings import Settings
                settings = Settings.load_from_file("config.json")
                return {
                    'enable_enhancement': settings.enable_enhancement,
                    'enhancement_model': settings.enhancement_model,
                    'enhancement_max_tokens': settings.enhancement_max_tokens,
                    'enhancement_temperature': settings.enhancement_temperature,
                    'enhancement_batch_size': settings.enhancement_batch_size,
                    'enable_progress_logging': settings.enable_progress_logging
                }
        except Exception as e:
            logger.warning(f"加载增强配置失败: {e}")
            return {}
    
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
            retry_delay = 5  # 增加初始重试延迟到5秒
            
            # 从配置中获取图像嵌入模型名称
            image_embedding_model = getattr(self.config, 'image_embedding_model', 'multimodal_embedding_one_peace_v1')
            
            for attempt in range(max_retries):
                try:
                    result = MultiModalEmbedding.call(
                        model=getattr(MultiModalEmbedding.Models, image_embedding_model),
                        input=input_data,
                        auto_truncation=True
                    )
                    
                    if result.status_code == 200:
                        # 成功返回embedding向量
                        return result.output["embedding"]
                    elif result.status_code == 429:
                        # 处理API频率限制
                        if attempt < max_retries - 1:  # 不是最后一次尝试
                            # 指数退避 + 随机抖动，增加等待时间
                            delay = retry_delay * (2 ** attempt) + random.uniform(2, 5)
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
                        delay = retry_delay * (2 ** attempt) + random.uniform(2, 5)
                        logger.warning(f"调用ONE-PEACE模型时发生异常，第{attempt + 1}次重试，等待{delay:.2f}秒... 错误: {e}")
                        time.sleep(delay)
                        continue
                    else:
                        # 最后一次尝试仍然失败
                        raise Exception(f"调用ONE-PEACE模型失败: {e}")
            
        except Exception as e:
            logger.error(f"生成图片embedding失败: {e}")
            raise
    
    def process_image_for_vector_store(self, image_path: str, image_id: str = None, document_name: str = None, page_number: int = None, img_caption: List[str] = None, img_footnote: List[str] = None) -> Optional[Dict[str, Any]]:
        """
        处理图片并生成向量存储所需的信息，增强版支持完整的图片元信息
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
                # 生成基础增强的图片描述
                enhanced_description = self._generate_enhanced_image_description(
                    image_path, img_caption, img_footnote
                )
                
                # 如果启用增强功能，添加深度分析
                if self.enhancement_enabled:
                    try:
                        enhancement_result = self.image_enhancer.enhance_image_description(
                            image_path, 
                            enhanced_description
                        )
                        enhanced_description = enhancement_result['enhanced_description']
                        
                        # 添加增强相关的元数据
                        result = {
                            'image_id': image_id,
                            'image_path': image_path,
                            'embedding': embedding,
                            'document_name': document_name or '未知文档',
                            'page_number': page_number or 1,
                            'img_caption': img_caption or [],
                            'img_footnote': img_footnote or [],
                            'enhanced_description': enhanced_description,
                            'image_type': self._detect_image_type(image_path),
                            'semantic_features': self._extract_semantic_features(embedding),
                            'layered_descriptions': enhancement_result.get('layered_descriptions', {}),
                            'structured_info': enhancement_result.get('structured_info', {}),
                            'enhancement_timestamp': enhancement_result.get('enhancement_timestamp'),
                            'enhancement_enabled': enhancement_result.get('enhancement_enabled', True)
                        }
                    except Exception as e:
                        logger.warning(f"图像增强失败，使用基础描述: {e}")
                        result = {
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
                    # 使用基础处理结果
                    result = {
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
                
                return result
            else:
                logger.error(f"生成图片embedding失败: {image_path}")
                return None
                
        except Exception as e:
            logger.error(f"处理图片失败 {image_path}: {e}")
            return None
    
    def _generate_enhanced_image_description(self, image_path: str, img_caption: List[str] = None, img_footnote: List[str] = None) -> str:
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
    
    def process_images_from_directory(self, image_dir: str) -> List[Dict[str, Any]]:
        """
        处理目录中的所有图片
        :param image_dir: 图片目录
        :return: 处理结果列表
        """
        results = []
        
        try:
            image_dir_path = Path(image_dir)
            if not image_dir_path.exists():
                logger.error(f"图片目录不存在: {image_dir}")
                return results
            
            # 支持的图片格式
            image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
            
            for image_file in image_dir_path.rglob('*'):
                if image_file.suffix.lower() in image_extensions:
                    result = self.process_image_for_vector_store(str(image_file))
                    if result:
                        results.append(result)
            
            logger.info(f"处理了 {len(results)} 张图片")
            return results
            
        except Exception as e:
            logger.error(f"处理图片目录失败: {e}")
            return results
    
    def extract_images_from_json_files(self, json_files: List[str]) -> List[Dict[str, Any]]:
        """
        从JSON文件中提取图片信息
        :param json_files: JSON文件路径列表
        :return: 图片信息列表
        """
        import json
        
        image_info_list = []
        seen_images = set()  # 用于去重
        
        for json_file in json_files:
            try:
                if not os.path.exists(json_file):
                    logger.warning(f"JSON文件不存在: {json_file}")
                    continue
                
                # 从文件名提取文档名称
                doc_name = os.path.basename(json_file).replace('_1.json', '').replace('.json', '')
                
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for item in data:
                    if item.get('type') == 'image':
                        img_path = item.get('img_path', '')
                        img_caption = item.get('img_caption', [])
                        img_footnote = item.get('img_footnote', [])
                        page_idx = item.get('page_idx', 0)
                        
                        # 构建完整的图片路径
                        if img_path.startswith('images/'):
                            full_img_path = os.path.join(os.path.dirname(json_file), img_path)
                        else:
                            full_img_path = img_path
                        
                        # 生成图片哈希用于去重
                        image_hash = self._generate_image_id(full_img_path) if os.path.exists(full_img_path) else img_path
                        
                        if image_hash not in seen_images:
                            seen_images.add(image_hash)
                            
                            image_info = {
                                'image_path': full_img_path,
                                'image_id': image_hash,
                                'document_name': doc_name,
                                'page_number': page_idx + 1,  # page_idx从0开始，转换为从1开始
                                'img_caption': img_caption,
                                'img_footnote': img_footnote,
                                'chunk_type': 'image'
                            }
                            image_info_list.append(image_info)
                
                logger.info(f"从 {json_file} 中提取了 {len([item for item in data if item.get('type') == 'image'])} 张图片")
                
            except Exception as e:
                logger.error(f"处理JSON文件失败 {json_file}: {e}")
        
        logger.info(f"总共提取了 {len(image_info_list)} 张唯一图片")
        return image_info_list
    
    def extract_images(self, md_files: List[str]) -> List[Dict[str, Any]]:
        """
        从Markdown文件中提取图片信息
        :param md_files: Markdown文件路径列表
        :return: 图片信息列表
        """
        import re
        
        image_info_list = []
        seen_images = set()  # 用于去重
        
        for md_file in md_files:
            try:
                if not os.path.exists(md_file):
                    logger.warning(f"Markdown文件不存在: {md_file}")
                    continue
                
                # 从文件名提取文档名称
                doc_name = os.path.basename(md_file).replace('.md', '')
                
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 查找图片链接
                image_pattern = r'!\[.*?\]\((.*?)\)'
                matches = re.findall(image_pattern, content)
                
                for img_path in matches:
                    # 构建完整的图片路径
                    if img_path.startswith('images/'):
                        full_img_path = os.path.join(os.path.dirname(md_file), img_path)
                    else:
                        full_img_path = img_path
                    
                    # 生成图片哈希用于去重
                    image_hash = self._generate_image_id(full_img_path) if os.path.exists(full_img_path) else img_path
                    
                    if image_hash not in seen_images:
                        seen_images.add(image_hash)
                        
                        image_info = {
                            'image_path': full_img_path,
                            'image_id': image_hash,
                            'document_name': doc_name,
                            'page_number': 1,  # Markdown中无法确定页码，默认为1
                            'chunk_type': 'image'
                        }
                        image_info_list.append(image_info)
                
                logger.info(f"从 {md_file} 中提取了 {len(matches)} 张图片")
                
            except Exception as e:
                logger.error(f"处理Markdown文件失败 {md_file}: {e}")
        
        logger.info(f"总共提取了 {len(image_info_list)} 张唯一图片")
        return image_info_list 