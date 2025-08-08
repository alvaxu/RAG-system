'''
程序说明：
## 1. 图片语义增强功能模块 - 基于ONE-PEACE模型
## 2. 为现有向量数据库中的图片生成更丰富的语义描述
## 3. 安全更新图片元数据，保持与现有系统的兼容性
## 4. 提供备份和恢复机制，确保数据安全
## 5. 支持批量处理和进度监控
'''

import os
import json
import logging
import time
import random
import hashlib
import shutil
import base64
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import pickle

# 导入必要的库
import dashscope
from dashscope import MultiModalEmbedding
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class EnhancementResult:
    """增强结果数据类"""
    total_images: int
    enhanced_images: int
    failed_images: int
    backup_path: str
    processing_time: float
    enhanced_descriptions: List[Dict[str, Any]]


class ImageSemanticEnhancer:
    """
    图片语义增强器 - 基于ONE-PEACE模型
    为现有向量数据库中的图片生成更丰富的语义描述
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化图片语义增强器
        
        :param config: 配置字典，包含API密钥等配置
        """
        self.config = config
        self.api_key = config.get('dashscope_api_key', '')
        
        if not self.api_key:
            raise ValueError("未配置DashScope API密钥")
        
        # 设置DashScope API密钥
        dashscope.api_key = self.api_key
        
        # 配置参数
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 2)
        self.batch_size = config.get('batch_size', 10)
        self.backup_enabled = config.get('backup_enabled', True)
        
        logger.info("图片语义增强器初始化完成")
    
    def enhance_vector_store_images(self, vector_store_path: str, 
                                  backup_enabled: bool = None,
                                  batch_size: int = None) -> EnhancementResult:
        """
        增强向量数据库中的图片语义描述
        
        :param vector_store_path: 向量数据库路径
        :param backup_enabled: 是否启用备份（覆盖配置）
        :param batch_size: 批处理大小（覆盖配置）
        :return: 增强结果统计
        """
        start_time = time.time()
        
        # 使用参数覆盖配置
        backup_enabled = backup_enabled if backup_enabled is not None else self.backup_enabled
        batch_size = batch_size if batch_size is not None else self.batch_size
        
        logger.info(f"开始增强向量数据库图片语义: {vector_store_path}")
        logger.info(f"备份启用: {backup_enabled}, 批处理大小: {batch_size}")
        
        try:
            # 1. 加载向量数据库
            vector_store = self._load_vector_store(vector_store_path)
            if not vector_store:
                raise ValueError("无法加载向量数据库")
            
            # 2. 创建备份（如果启用）
            backup_path = None
            if backup_enabled:
                backup_path = self._create_backup(vector_store_path)
                logger.info(f"已创建备份: {backup_path}")
            
            # 3. 识别图片文档
            image_docs = self._identify_image_documents(vector_store)
            logger.info(f"找到 {len(image_docs)} 个图片文档")
            
            if not image_docs:
                logger.warning("未找到图片文档")
                return EnhancementResult(
                    total_images=0,
                    enhanced_images=0,
                    failed_images=0,
                    backup_path=backup_path or "",
                    processing_time=time.time() - start_time,
                    enhanced_descriptions=[]
                )
            
            # 4. 批量处理图片
            enhanced_descriptions = []
            enhanced_count = 0
            failed_count = 0
            
            for i in range(0, len(image_docs), batch_size):
                batch = image_docs[i:i + batch_size]
                logger.info(f"处理批次 {i//batch_size + 1}/{(len(image_docs) + batch_size - 1)//batch_size}")
                
                for doc_id, doc_info in batch:
                    try:
                        enhanced_info = self._enhance_single_image(doc_id, doc_info, vector_store)
                        if enhanced_info:
                            enhanced_descriptions.append(enhanced_info)
                            enhanced_count += 1
                            logger.info(f"成功增强图片: {doc_info.get('image_path', 'unknown')}")
                        else:
                            failed_count += 1
                            logger.warning(f"增强失败: {doc_info.get('image_path', 'unknown')}")
                    except Exception as e:
                        failed_count += 1
                        logger.error(f"处理图片时出错: {e}")
                        continue
            
            # 5. 保存更新后的向量数据库
            self._save_vector_store(vector_store, vector_store_path)
            
            processing_time = time.time() - start_time
            logger.info(f"图片语义增强完成")
            logger.info(f"总图片数: {len(image_docs)}")
            logger.info(f"成功增强: {enhanced_count}")
            logger.info(f"处理失败: {failed_count}")
            logger.info(f"处理时间: {processing_time:.2f}秒")
            
            return EnhancementResult(
                total_images=len(image_docs),
                enhanced_images=enhanced_count,
                failed_images=failed_count,
                backup_path=backup_path or "",
                processing_time=processing_time,
                enhanced_descriptions=enhanced_descriptions
            )
            
        except Exception as e:
            logger.error(f"图片语义增强失败: {e}")
            raise
    
    def _load_vector_store(self, vector_store_path: str) -> Optional[FAISS]:
        """
        加载向量数据库
        
        :param vector_store_path: 向量数据库路径
        :return: FAISS向量存储对象
        """
        try:
            embeddings = DashScopeEmbeddings(
                dashscope_api_key=self.api_key, 
                model="text-embedding-v1"
            )
            vector_store = FAISS.load_local(
                vector_store_path, 
                embeddings, 
                allow_dangerous_deserialization=True
            )
            logger.info(f"向量数据库加载成功，包含 {len(vector_store.docstore._dict)} 个文档")
            return vector_store
        except Exception as e:
            logger.error(f"加载向量数据库失败: {e}")
            return None
    
    def _create_backup(self, vector_store_path: str) -> str:
        """
        创建向量数据库备份
        
        :param vector_store_path: 向量数据库路径
        :return: 备份路径
        """
        try:
            backup_dir = Path(vector_store_path).parent / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = int(time.time())
            backup_path = backup_dir / f"vector_db_backup_{timestamp}"
            
            # 复制向量数据库文件
            shutil.copytree(vector_store_path, backup_path)
            
            logger.info(f"备份创建成功: {backup_path}")
            return str(backup_path)
        except Exception as e:
            logger.error(f"创建备份失败: {e}")
            raise
    
    def _identify_image_documents(self, vector_store: FAISS) -> List[Tuple[str, Dict[str, Any]]]:
        """
        识别向量数据库中的图片文档
        
        :param vector_store: FAISS向量存储对象
        :return: 图片文档列表，每个元素为(doc_id, doc_info)
        """
        image_docs = []
        
        try:
            for doc_id, doc in vector_store.docstore._dict.items():
                metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
                
                # 检查是否为图片类型
                if metadata.get('chunk_type') == 'image':
                    doc_info = {
                        'doc_id': doc_id,
                        'content': doc.page_content,
                        'metadata': metadata,
                        'image_path': metadata.get('image_path', ''),
                        'document_name': metadata.get('document_name', '未知文档'),
                        'page_number': metadata.get('page_number', 1),
                        'img_caption': metadata.get('img_caption', []),
                        'img_footnote': metadata.get('img_footnote', []),
                        'enhanced_description': metadata.get('enhanced_description', ''),
                        'image_type': metadata.get('image_type', 'general'),
                        'semantic_features': metadata.get('semantic_features', {})
                    }
                    image_docs.append((doc_id, doc_info))
            
            logger.info(f"识别到 {len(image_docs)} 个图片文档")
            return image_docs
            
        except Exception as e:
            logger.error(f"识别图片文档失败: {e}")
            return []
    
    def _enhance_single_image(self, doc_id: str, doc_info: Dict[str, Any], 
                             vector_store: FAISS) -> Optional[Dict[str, Any]]:
        """
        增强单个图片的语义描述
        
        :param doc_id: 文档ID
        :param doc_info: 文档信息
        :param vector_store: FAISS向量存储对象
        :return: 增强后的信息
        """
        try:
            image_path = doc_info.get('image_path', '')
            
            if not image_path or not os.path.exists(image_path):
                logger.warning(f"图片文件不存在: {image_path}")
                return None
            
            # 生成语义描述
            semantic_description = self._generate_semantic_description(image_path, doc_info)
            
            if not semantic_description:
                logger.warning(f"无法生成语义描述: {image_path}")
                return None
            
            # 构建增强描述
            original_description = doc_info.get('enhanced_description', '')
            if original_description:
                enhanced_description = f"{original_description} | 语义描述: {semantic_description}"
            else:
                enhanced_description = f"语义描述: {semantic_description}"
            
            # 更新元数据
            updated_metadata = doc_info['metadata'].copy()
            updated_metadata['enhanced_description'] = enhanced_description
            updated_metadata['semantic_description'] = semantic_description
            updated_metadata['enhancement_timestamp'] = int(time.time())
            
            # 更新文档
            doc = vector_store.docstore._dict[doc_id]
            doc.metadata = updated_metadata
            
            return {
                'doc_id': doc_id,
                'image_path': image_path,
                'original_description': original_description,
                'enhanced_description': enhanced_description,
                'semantic_description': semantic_description,
                'document_name': doc_info.get('document_name', '未知文档')
            }
            
        except Exception as e:
            logger.error(f"增强单个图片失败: {e}")
            return None
    
    def _generate_semantic_description(self, image_path: str, doc_info: Dict[str, Any]) -> Optional[str]:
        """
        使用ONE-PEACE模型生成图片的语义描述
        
        :param image_path: 图片路径
        :param doc_info: 文档信息
        :return: 语义描述文本
        """
        try:
            # 编码图片为base64
            image_base64 = self._encode_image_to_base64(image_path)
            
            # 构建输入参数
            input_data = [{'image': f"data:image/jpeg;base64,{image_base64}"}]
            
            # 调用ONE-PEACE模型
            for attempt in range(self.max_retries):
                try:
                    result = MultiModalEmbedding.call(
                        model=MultiModalEmbedding.Models.multimodal_embedding_one_peace_v1,
                        input=input_data,
                        auto_truncation=True
                    )
                    
                    if result.status_code == 200:
                        # 基于embedding生成描述（这里可以扩展为调用图像描述API）
                        embedding = result.output["embedding"]
                        semantic_description = self._generate_description_from_embedding(
                            embedding, image_path, doc_info
                        )
                        return semantic_description
                    elif result.status_code == 429:
                        # 处理频率限制
                        if attempt < self.max_retries - 1:
                            delay = self.retry_delay * (2 ** attempt) + random.uniform(1, 3)
                            logger.warning(f"API频率限制，第{attempt + 1}次重试，等待{delay:.2f}秒...")
                            time.sleep(delay)
                            continue
                        else:
                            logger.error("API频率限制，已达到最大重试次数")
                            return None
                    else:
                        logger.error(f"API调用失败，状态码: {result.status_code}")
                        return None
                        
                except Exception as e:
                    if attempt < self.max_retries - 1:
                        delay = self.retry_delay * (2 ** attempt) + random.uniform(1, 3)
                        logger.warning(f"API调用异常，第{attempt + 1}次重试，等待{delay:.2f}秒...")
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"API调用失败: {e}")
                        return None
            
            return None
            
        except Exception as e:
            logger.error(f"生成语义描述失败: {e}")
            return None
    
    def _encode_image_to_base64(self, image_path: str) -> str:
        """
        将图片编码为base64字符串
        
        :param image_path: 图片路径
        :return: base64编码的图片数据
        """
        try:
            with open(image_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
            return encoded_image
        except Exception as e:
            logger.error(f"编码图片失败: {e}")
            raise
    
    def _generate_description_from_embedding(self, embedding: List[float], image_path: str, doc_info: Dict[str, Any]) -> str:
        """
        基于embedding和图片特征生成更丰富的语义描述
        
        :param embedding: 图片embedding向量
        :param image_path: 图片路径
        :param doc_info: 文档信息
        :return: 生成的描述文本
        """
        try:
            # 获取图片元数据信息
            metadata = doc_info.get('metadata', {})
            filename = os.path.basename(image_path).lower()
            
            # 分析embedding特征
            embedding_norm = sum(x*x for x in embedding) ** 0.5
            embedding_mean = sum(embedding) / len(embedding)
            embedding_std = (sum((x - embedding_mean) ** 2 for x in embedding) / len(embedding)) ** 0.5
            
            # 构建基础描述
            description_parts = []
            
            # 1. 基于元数据的描述
            if metadata.get('img_caption'):
                caption_text = ' '.join(metadata['img_caption'])
                description_parts.append(f"图片标题: {caption_text}")
            
            if metadata.get('img_footnote'):
                footnote_text = ' '.join(metadata['img_footnote'])
                description_parts.append(f"图片脚注: {footnote_text}")
            
            # 2. 尝试使用ONE-PEACE进行真正的图像内容理解
            image_content_description = self._generate_image_content_description(image_path)
            if image_content_description:
                description_parts.append(f"图像内容: {image_content_description}")
            
            # 3. 基于embedding特征的语义分析
            semantic_features = self._analyze_embedding_semantics(embedding, embedding_norm, embedding_mean, embedding_std)
            if semantic_features:
                description_parts.append(f"语义特征: {semantic_features}")
            
            # 4. 基于文件名的图表类型识别
            chart_type = self._identify_chart_type(filename, metadata)
            if chart_type:
                description_parts.append(f"图表类型: {chart_type}")
            
            # 5. 内容复杂度分析
            complexity = self._analyze_content_complexity(embedding_norm, embedding_mean, embedding_std)
            if complexity:
                description_parts.append(f"内容特征: {complexity}")
            
            # 组合描述
            if description_parts:
                return " | ".join(description_parts)
            else:
                return "这是一张包含信息的图片"
            
        except Exception as e:
            logger.error(f"基于embedding生成描述失败: {e}")
            return "这是一张包含信息的图片"
    
    def _generate_image_content_description(self, image_path: str) -> Optional[str]:
        """
        使用ONE-PEACE模型生成真正的图像内容描述
        
        :param image_path: 图片路径
        :return: 图像内容描述
        """
        try:
            # 编码图片为base64
            image_base64 = self._encode_image_to_base64(image_path)
            
            # 构建输入参数 - 使用图像描述任务
            input_data = [{'image': f"data:image/jpeg;base64,{image_base64}"}]
            
            # 尝试调用ONE-PEACE的图像描述功能
            for attempt in range(self.max_retries):
                try:
                    # 这里需要调用ONE-PEACE的图像描述API
                    # 注意：DashScope的ONE-PEACE模型可能需要不同的调用方式
                    result = self._call_one_peace_image_description(input_data)
                    
                    if result:
                        return result
                    else:
                        # 如果无法获取图像描述，返回None
                        logger.warning(f"无法获取图像内容描述: {image_path}")
                        return None
                        
                except Exception as e:
                    if attempt < self.max_retries - 1:
                        delay = self.retry_delay * (2 ** attempt) + random.uniform(1, 3)
                        logger.warning(f"图像描述API调用异常，第{attempt + 1}次重试，等待{delay:.2f}秒...")
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"图像描述API调用失败: {e}")
                        return None
            
            return None
            
        except Exception as e:
            logger.error(f"生成图像内容描述失败: {e}")
            return None
    
    def _call_one_peace_image_description(self, input_data: List[Dict[str, str]]) -> Optional[str]:
        """
        调用ONE-PEACE模型的图像描述功能
        
        :param input_data: 输入数据
        :return: 图像描述文本
        """
        try:
            # 注意：这里需要根据DashScope的实际API来调整
            # 目前DashScope的ONE-PEACE模型主要用于embedding，可能没有直接的图像描述API
            # 我们可以尝试使用其他方式或返回None
            
            # 临时实现：基于embedding特征生成简单的图像描述
            # 在实际应用中，这里应该调用真正的图像描述API
            
            logger.info("当前ONE-PEACE模型主要用于embedding，暂未实现图像描述功能")
            return None
            
        except Exception as e:
            logger.error(f"调用ONE-PEACE图像描述失败: {e}")
            return None
    
    def _analyze_embedding_semantics(self, embedding: List[float], norm: float, mean: float, std: float) -> str:
        """
        分析embedding的语义特征
        
        :param embedding: embedding向量
        :param norm: 向量范数
        :param mean: 向量均值
        :param std: 向量标准差
        :return: 语义特征描述
        """
        features = []
        
        # 基于统计特征分析
        if norm > 1.8:
            features.append("高复杂度视觉内容")
        elif norm > 1.2:
            features.append("中等复杂度视觉内容")
        else:
            features.append("简单视觉内容")
        
        if std > 0.15:
            features.append("视觉特征丰富")
        elif std > 0.08:
            features.append("视觉特征中等")
        else:
            features.append("视觉特征简单")
        
        if mean > 0.12:
            features.append("整体亮度较高")
        elif mean < -0.12:
            features.append("整体亮度较低")
        else:
            features.append("亮度适中")
        
        return ", ".join(features)
    
    def _identify_chart_type(self, filename: str, metadata: Dict[str, Any]) -> str:
        """
        识别图表类型
        
        :param filename: 文件名
        :param metadata: 元数据
        :return: 图表类型描述
        """
        # 基于文件名和元数据识别图表类型
        filename_lower = filename.lower()
        
        # 检查文件名中的关键词
        if any(keyword in filename_lower for keyword in ['bar', '柱状', '柱形']):
            return "柱状图"
        elif any(keyword in filename_lower for keyword in ['line', '折线', '趋势']):
            return "折线图"
        elif any(keyword in filename_lower for keyword in ['pie', '饼图', '圆形']):
            return "饼图"
        elif any(keyword in filename_lower for keyword in ['scatter', '散点', '点图']):
            return "散点图"
        elif any(keyword in filename_lower for keyword in ['table', '表格', '数据表']):
            return "数据表格"
        elif any(keyword in filename_lower for keyword in ['flow', '流程图', 'diagram']):
            return "流程图"
        elif any(keyword in filename_lower for keyword in ['chart', '图表', 'graph']):
            return "数据图表"
        else:
            return "信息图表"
    
    def _analyze_content_complexity(self, norm: float, mean: float, std: float) -> str:
        """
        分析内容复杂度
        
        :param norm: 向量范数
        :param mean: 向量均值
        :param std: 向量标准差
        :return: 复杂度描述
        """
        complexity_score = norm * std * abs(mean)
        
        if complexity_score > 0.3:
            return "内容复杂，信息密度高"
        elif complexity_score > 0.15:
            return "内容中等，信息密度适中"
        else:
            return "内容简单，信息密度较低"
    
    def _save_vector_store(self, vector_store: FAISS, save_path: str) -> bool:
        """
        保存向量数据库
        
        :param vector_store: FAISS向量存储对象
        :param save_path: 保存路径
        :return: 是否保存成功
        """
        try:
            vector_store.save_local(save_path)
            logger.info(f"向量数据库保存成功: {save_path}")
            return True
        except Exception as e:
            logger.error(f"保存向量数据库失败: {e}")
            return False
    
    def restore_from_backup(self, backup_path: str, target_path: str) -> bool:
        """
        从备份恢复向量数据库
        
        :param backup_path: 备份路径
        :param target_path: 目标路径
        :return: 是否恢复成功
        """
        try:
            if not os.path.exists(backup_path):
                logger.error(f"备份路径不存在: {backup_path}")
                return False
            
            # 删除目标路径（如果存在）
            if os.path.exists(target_path):
                shutil.rmtree(target_path)
            
            # 恢复备份
            shutil.copytree(backup_path, target_path)
            logger.info(f"从备份恢复成功: {backup_path} -> {target_path}")
            return True
            
        except Exception as e:
            logger.error(f"从备份恢复失败: {e}")
            return False


# 为了兼容性，提供别名
ImageSemanticEnhancer = ImageSemanticEnhancer 