"""
图片处理器

负责处理文档中的图片内容，包括图片增强描述生成、双重向量化（视觉向量和语义向量）、
以及图片元数据管理等。完全符合设计文档规范。
"""

import os
import time
import logging
import shutil
from typing import Dict, List, Any
from PIL import Image

class ImageProcessor:
    """
    图片处理器
    整合：复制 → 增强 → 向量化 → 存储
    完全符合设计文档规范，位于processors模块下
    """
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        
        # 初始化各个组件（符合设计文档规范）
        from .image_enhancer import ImageEnhancer
        from db_system.vectorization.image_vectorizer import ImageVectorizer
        self.image_enhancer = ImageEnhancer(config_manager)
        self.image_vectorizer = ImageVectorizer(config_manager)
        
        # 使用失败处理（符合设计文档规范）
        self.failure_handler = config_manager.get_failure_handler()
        
        logging.info("图片处理器初始化完成")
    
    def process_images(self, images: List[Dict]) -> List[Dict]:
        """
        完整的图片处理流程
        """
        try:
            print(f" 开始处理 {len(images)} 张图片...")
            
            # 步骤1: 图片复制到最终目录
            print("步骤1: 图片复制...")
            copied_images = self._copy_images_to_final_dir(images)
            success_count = sum(1 for img in copied_images if img.get('copy_status') == 'success')
            print(f"✅ 图片复制完成: {success_count}/{len(images)} 成功")
            
            # 步骤2: 一次性生成完整增强信息（避免重复）
            print("步骤2: 图片增强描述...")
            enhanced_images = []
            for i, image in enumerate(copied_images):
                if image.get('copy_status') == 'success':
                    print(f"  🖼️ 增强图片 {i+1}/{len(copied_images)}: {os.path.basename(image.get('final_image_path', ''))}")
                    
                    # 一次性生成完整增强信息
                    enhancement_result = self.image_enhancer.enhance_image_complete(
                        image.get('final_image_path', ''),
                        {
                            'img_caption': image.get('img_caption', []),
                            'img_footnote': image.get('img_footnote', []),
                            'img_path': image.get('img_path', '')
                        }
                    )
                    
                    # 更新图片信息
                    image.update(enhancement_result)
                    enhanced_images.append(image)
                    
                    print(f"  ✅ 图片增强完成: {os.path.basename(image.get('final_image_path', ''))}")
                else:
                    enhanced_images.append(image)
            
            success_count = sum(1 for img in enhanced_images if img.get('enhancement_status') == 'success')
            print(f"✅ 图片增强完成: {success_count}/{len(images)} 成功")
            
            # 步骤3: 图片双重向量化
            print("步骤3: 图片双重向量化...")
            vectorized_images = self.image_vectorizer.vectorize_images_batch(enhanced_images)
            success_count = sum(1 for img in vectorized_images if img.get('vectorization_status') == 'success')
            print(f"✅ 图片向量化完成: {success_count}/{len(images)} 成功")
            
            # 步骤4: 生成完整元数据
            print("步骤4: 生成完整元数据...")
            final_images = []
            for image in vectorized_images:
                complete_metadata = self._create_complete_image_metadata(image)
                final_images.append(complete_metadata)
            
            print(f"✅ 图片处理流程完成: {len(final_images)} 张图片")
            return final_images
            
        except Exception as e:
            error_msg = f"图片处理流程失败: {e}"
            logging.error(error_msg)
            self.failure_handler.record_failure('image_pipeline', 'image_processing_pipeline', str(e))
            raise RuntimeError(error_msg)
    
    def _copy_images_to_final_dir(self, images: List[Dict]) -> List[Dict]:
        """
        将图片复制到最终目录
        """
        copied_images = []
        
        for image in images:
            try:
                source_path = image.get('source_image_path', '')
                target_path = image.get('final_image_path', '')
                
                if os.path.exists(source_path):
                    # 确保目标目录存在
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    
                    # 复制图片
                    shutil.copy2(source_path, target_path)
                    
                    # 更新图片信息
                    image['copy_status'] = 'success'
                    image['final_image_path'] = target_path
                    image['image_size'] = os.path.getsize(target_path)
                    
                    # 获取图片尺寸
                    image['image_dimensions'] = self._get_image_dimensions(target_path)
                    
                    copied_images.append(image)
                    logging.info(f"图片复制成功: {os.path.basename(source_path)}")
                else:
                    image['copy_status'] = 'failed'
                    image['error'] = '源文件不存在'
                    self.failure_handler.record_failure(source_path, 'image_copy', '源文件不存在')
                    
            except Exception as e:
                image['copy_status'] = 'failed'
                image['error'] = str(e)
                self.failure_handler.record_failure(source_path, 'image_copy', str(e))
                logging.error(f"图片复制失败: {source_path}, 错误: {e}")
        
        return copied_images
    
    def _get_image_dimensions(self, image_path: str) -> Dict[str, int]:
        """获取图片尺寸"""
        try:
            with Image.open(image_path) as img:
                return {
                    'width': img.width,
                    'height': img.height
                }
        except Exception as e:
            logging.warning(f"获取图片尺寸失败: {e}")
            return {'width': 0, 'height': 0}
    
    def _create_complete_image_metadata(self, image: Dict) -> Dict[str, Any]:
        """
        创建完整的图片元数据，完全符合设计文档的IMAGE_METADATA_SCHEMA规范
        返回包含'metadata'字段的对象，与文本/表格向量器保持一致
        """
        # 创建完整的metadata字典
        complete_metadata = {
            # 基础标识字段（符合COMMON_METADATA_FIELDS）
            'chunk_id': image.get('chunk_id', ''),
            'chunk_type': 'image',
            'source_type': 'pdf',
            'document_name': image.get('document_name', ''),
            'document_path': image.get('document_path', ''),
            'page_number': image.get('page_number', 1),
            'page_idx': image.get('page_idx', 1),
            'created_timestamp': image.get('created_timestamp', int(time.time())),
            'updated_timestamp': int(time.time()),
            'processing_version': '3.0.0',

            # 向量化信息字段
            'vectorized': image.get('vectorization_status') == 'success',
            'vectorization_timestamp': image.get('vectorization_timestamp'),
            'embedding_model': f"{image.get('image_embedding_model', '')}+{image.get('description_embedding_model', '')}" if image.get('image_embedding_model') and image.get('description_embedding_model') else None,

            # 图片特有字段（符合IMAGE_METADATA_SCHEMA）
            'image_id': image.get('image_id', ''),
            'image_path': image.get('final_image_path', ''),
            'image_filename': image.get('image_filename', ''),
            'image_type': image.get('image_type', 'general'),
            'image_format': image.get('image_format', 'UNKNOWN'),
            'image_dimensions': image.get('image_dimensions', {'width': 0, 'height': 0}),

            # 内容描述字段（保留现有系统的优秀部分）
            'basic_description': image.get('basic_description', ''),
            'enhanced_description': image.get('enhanced_description', ''),
            'layered_descriptions': image.get('layered_descriptions', {}),
            'structured_info': image.get('structured_info', {}),

            # 图片标题和脚注（保留现有系统的优秀部分）
            'img_caption': image.get('img_caption', []),
            'img_footnote': image.get('img_footnote', []),

            # 增强处理字段（支持失败处理和补做）
            'enhancement_enabled': image.get('enhancement_enabled', True),
            'enhancement_model': image.get('enhancement_model', ''),
            'enhancement_status': image.get('enhancement_status', 'unknown'),
            'enhancement_timestamp': image.get('enhancement_timestamp'),
            'enhancement_error': image.get('enhancement_error', ''),

            # 双重embedding字段（符合设计文档规范）
            'image_embedding': image.get('image_embedding', []),
            'description_embedding': image.get('description_embedding', []),
            'image_embedding_model': image.get('image_embedding_model', ''),
            'description_embedding_model': image.get('description_embedding_model', ''),

            # 关联信息字段
            'related_text_chunks': image.get('related_text_chunks', []),
            'related_table_chunks': image.get('related_table_chunks', []),
            'parent_document_id': image.get('parent_document_id', ''),

            # 处理状态信息
            'copy_status': image.get('copy_status', 'unknown'),
            'enhancement_status': image.get('enhancement_status', 'unknown'),
            'vectorization_status': image.get('vectorization_status', 'unknown'),

            # 原始信息
            'mineru_original': image.get('mineru_original', {}),
            'vision_analysis': image.get('vision_analysis', {}),

            # 架构标识
            'metadata_schema': 'IMAGE_METADATA_SCHEMA',
            'metadata_version': '3.0.0',
            'processing_pipeline': 'MinerU_Enhancement_Pipeline',
            'optimization_features': [
                'one_time_enhancement',
                'smart_deduplication',
                'complete_metadata',
                'dual_vectorization'
            ]
        }

        # 返回包含'metadata'字段的对象，与文本/表格向量器保持一致
        # 只保留必要的向量信息，metadata已在complete_metadata中
        return {
            'metadata': complete_metadata,  # 完整的metadata信息
            'image_embedding': image.get('image_embedding', []),  # 图像向量
            'description_embedding': image.get('description_embedding', []),  # 描述向量
            'vectorization_status': image.get('vectorization_status', 'unknown'),  # 向量化状态
            'vectorization_timestamp': image.get('vectorization_timestamp'),  # 向量化时间戳
            'embedding_model': image.get('embedding_model', '')  # 嵌入模型信息
        }
    
    def get_processing_status(self) -> Dict[str, Any]:
        """
        获取处理状态
        """
        return {
            'enhancer_status': self.image_enhancer.get_status() if hasattr(self.image_enhancer, 'get_status') else 'unknown',
            'vectorizer_status': self.image_vectorizer.get_vectorization_status(),
            'total_images_processed': 0  # 可以添加计数器
        }
