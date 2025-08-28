"""
图像向量化器

负责图像内容的双重向量化处理，包括视觉向量和语义向量。
完全符合设计文档规范，位于vectorization模块下。
"""

import os
import time
import logging
from typing import Dict, List, Any

class ImageVectorizer:
    """
    图片向量化器
    实现双重embedding策略：视觉embedding + 语义embedding
    完全符合设计文档规范，位于vectorization模块下
    """
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.config = config_manager.get_all_config()
        self.image_embedding_model = self.config.get('vectorization.image_embedding_model', 'multimodal-embedding-one-peace-v1')
        self.text_embedding_model = self.config.get('vectorization.text_embedding_model', 'text-embedding-v1')
        self.batch_size = self.config.get('api_rate_limiting.image_vectorization_batch_size', 5)
        self.delay_seconds = self.config.get('api_rate_limiting.image_vectorization_delay_seconds', 1)
        self.failure_handler = config_manager.get_failure_handler()
        
        # 初始化ModelCaller
        from utils.model_caller import ModelCaller
        self.model_caller = ModelCaller(config_manager)
        
        logging.info("图片向量化器初始化完成")
    
    def vectorize_image(self, image_path: str, enhanced_description: str) -> Dict[str, Any]:
        """
        对单张图片进行双重向量化 (visual + semantic)
        
        :param image_path: 图片文件路径
        :param enhanced_description: 增强后的图片描述
        :return: 向量化结果字典
        """
        try:
            logging.info(f"开始向量化图片: {os.path.basename(image_path)}")
            
            # 步骤1: 视觉向量化
            visual_embedding = self._vectorize_visual(image_path)
            
            # 步骤2: 语义向量化
            semantic_embedding = self._vectorize_semantic(enhanced_description)
            
            # 步骤3: 生成向量化元数据
            vectorization_metadata = self._generate_vectorization_metadata(
                visual_embedding, semantic_embedding
            )
            
            # 整合结果
            vectorization_result = {
                'vectorization_status': 'success',
                'vectorization_timestamp': int(time.time()),
                'image_embedding': visual_embedding,
                'description_embedding': semantic_embedding,
                'image_embedding_model': self.image_embedding_model,
                'description_embedding_model': self.text_embedding_model,
                'vectorization_metadata': vectorization_metadata,
                'processing_metadata': {
                    'vectorization_version': '3.0.0',
                    'processing_pipeline': 'Dual_Embedding_Pipeline',
                    'optimization_features': [
                        'dual_vectorization',
                        'batch_processing',
                        'api_rate_limiting',
                        'complete_metadata'
                    ]
                }
            }
            
            logging.info(f"图片向量化完成: {os.path.basename(image_path)}")
            return vectorization_result
            
        except Exception as e:
            error_msg = f"图片向量化失败: {str(e)}"
            logging.error(error_msg)
            self.failure_handler.record_failure(image_path, 'image_vectorization', str(e))
            
            # 返回错误结果
            return self._create_error_vectorization_result(str(e))
    
    def _vectorize_visual(self, image_path: str) -> List[float]:
        """
        生成视觉向量
        """
        try:
            # 调用ModelCaller进行视觉向量化
            visual_embedding = self.model_caller.call_visual_embedding(image_path)
            
            if not visual_embedding:
                raise ValueError("视觉向量生成失败")
            
            return visual_embedding
            
        except Exception as e:
            logging.error(f"视觉向量化失败: {e}")
            raise
    
    def _vectorize_semantic(self, enhanced_description: str) -> List[float]:
        """
        生成语义向量
        """
        try:
            if not enhanced_description:
                raise ValueError("增强描述为空，无法生成语义向量")
            
            # 调用ModelCaller进行文本向量化
            semantic_embedding = self.model_caller.call_text_embedding(enhanced_description)
            
            if not semantic_embedding:
                raise ValueError("语义向量生成失败")
            
            return semantic_embedding
            
        except Exception as e:
            logging.error(f"语义向量化失败: {e}")
            raise
    
    def _generate_vectorization_metadata(self, visual_embedding: List[float], semantic_embedding: List[float]) -> Dict[str, Any]:
        """
        生成向量化元数据
        """
        return {
            'visual_vector_dimensions': len(visual_embedding) if visual_embedding else 0,
            'semantic_vector_dimensions': len(semantic_embedding) if semantic_embedding else 0,
            'total_vector_dimensions': (len(visual_embedding) if visual_embedding else 0) + 
                                     (len(semantic_embedding) if semantic_embedding else 0),
            'vector_quality': {
                'visual_quality': self._assess_vector_quality(visual_embedding),
                'semantic_quality': self._assess_vector_quality(semantic_embedding)
            },
            'embedding_models': {
                'visual_model': self.image_embedding_model,
                'semantic_model': self.text_embedding_model
            },
            'vectorization_timestamp': int(time.time())
        }
    
    def _assess_vector_quality(self, vector: List[float]) -> Dict[str, Any]:
        """
        评估向量质量
        """
        if not vector:
            return {'quality_score': 0, 'quality_level': 'poor', 'issues': ['向量为空']}
        
        quality_score = 0.0
        issues = []
        
        # 维度评估
        dimensions = len(vector)
        if dimensions >= 1024:
            quality_score += 0.4
        elif dimensions >= 512:
            quality_score += 0.3
        elif dimensions >= 256:
            quality_score += 0.2
        else:
            issues.append("向量维度较低")
        
        # 数值范围评估
        if vector:
            min_val = min(vector)
            max_val = max(vector)
            range_val = max_val - min_val
            
            if range_val > 10:
                quality_score += 0.3
            elif range_val > 5:
                quality_score += 0.2
            elif range_val > 1:
                quality_score += 0.1
            else:
                issues.append("向量数值范围较小")
            
            # 零值比例评估
            zero_count = sum(1 for v in vector if abs(v) < 1e-6)
            zero_ratio = zero_count / dimensions
            
            if zero_ratio < 0.1:
                quality_score += 0.3
            elif zero_ratio < 0.3:
                quality_score += 0.2
            elif zero_ratio < 0.5:
                quality_score += 0.1
            else:
                issues.append("向量包含过多零值")
        
        # 确定质量级别
        if quality_score >= 0.8:
            quality_level = 'excellent'
        elif quality_score >= 0.6:
            quality_level = 'good'
        elif quality_score >= 0.4:
            quality_level = 'fair'
        else:
            quality_level = 'poor'
        
        return {
            'quality_score': quality_score,
            'quality_level': quality_level,
            'issues': issues,
            'dimensions': dimensions,
            'min_value': min(vector) if vector else 0,
            'max_value': max(vector) if vector else 0,
            'zero_ratio': zero_ratio if vector else 0
        }
    
    def _create_error_vectorization_result(self, error_message: str) -> Dict[str, Any]:
        """
        创建错误向量化结果
        """
        return {
            'vectorization_status': 'failed',
            'vectorization_timestamp': int(time.time()),
            'error_message': error_message,
            'image_embedding': [],
            'description_embedding': [],
            'image_embedding_model': self.image_embedding_model,
            'description_embedding_model': self.text_embedding_model,
            'vectorization_metadata': {
                'visual_vector_dimensions': 0,
                'semantic_vector_dimensions': 0,
                'total_vector_dimensions': 0,
                'vector_quality': {
                    'visual_quality': {'quality_score': 0, 'quality_level': 'poor'},
                    'semantic_quality': {'quality_score': 0, 'quality_level': 'poor'}
                },
                'embedding_models': {
                    'visual_model': self.image_embedding_model,
                    'semantic_model': self.text_embedding_model
                },
                'vectorization_timestamp': int(time.time())
            },
            'processing_metadata': {
                'vectorization_version': '3.0.0',
                'processing_pipeline': 'Error_Handling_Pipeline',
                'optimization_features': ['error_handling', 'graceful_degradation']
            }
        }
    
    def vectorize_images_batch(self, images: List[Dict]) -> List[Dict[str, Any]]:
        """
        批量向量化图片
        """
        vectorized_images = []
        
        for i, image in enumerate(images):
            try:
                # 获取图片信息
                image_path = image.get('final_image_path', '')
                enhanced_description = image.get('enhanced_description', '')
                
                if not image_path:
                    logging.warning(f"图片 {i+1} 缺少路径信息")
                    continue
                
                if not os.path.exists(image_path):
                    logging.warning(f"图片文件不存在: {image_path}")
                    continue
                
                if not enhanced_description:
                    logging.warning(f"图片 {i+1} 缺少增强描述")
                    continue
                
                # 执行向量化
                vectorization_result = self.vectorize_image(image_path, enhanced_description)
                
                # 更新图片信息
                image.update(vectorization_result)
                vectorized_images.append(image)
                
                # API限流控制
                if (i + 1) % self.batch_size == 0 and i < len(images) - 1:
                    logging.info(f"批量向量化进度: {i+1}/{len(images)}，等待 {self.delay_seconds} 秒...")
                    time.sleep(self.delay_seconds)
                
            except Exception as e:
                error_msg = f"批量向量化图片 {i+1} 失败: {str(e)}"
                logging.error(error_msg)
                self.failure_handler.record_failure(image, 'batch_image_vectorization', str(e))
                
                # 创建错误结果
                error_result = self._create_error_vectorization_result(str(e))
                image.update(error_result)
                vectorized_images.append(image)
        
        logging.info(f"批量图片向量化完成: {len(vectorized_images)}/{len(images)} 成功")
        return vectorized_images
    
    def get_vectorization_status(self) -> Dict[str, Any]:
        """
        获取向量化状态信息
        """
        return {
            'vectorizer_type': 'image_vectorizer',
            'status': 'ready',
            'image_embedding_model': self.image_embedding_model,
            'text_embedding_model': self.text_embedding_model,
            'batch_size': self.batch_size,
            'delay_seconds': self.delay_seconds,
            'capabilities': [
                'dual_vectorization',
                'visual_embedding',
                'semantic_embedding',
                'batch_processing',
                'api_rate_limiting',
                'quality_assessment'
            ],
            'version': '3.0.0'
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        """
        return {
            'visual_model': {
                'name': self.image_embedding_model,
                'type': 'multimodal_embedding',
                'provider': 'dashscope',
                'capabilities': ['image_understanding', 'visual_feature_extraction']
            },
            'semantic_model': {
                'name': self.text_embedding_model,
                'type': 'text_embedding',
                'provider': 'dashscope',
                'capabilities': ['text_understanding', 'semantic_feature_extraction']
            }
        }
    
    def validate_vectorization_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证向量化结果
        """
        validation_result = {
            'is_valid': True,
            'issues': [],
            'warnings': [],
            'recommendations': []
        }
        
        # 检查向量化状态
        if result.get('vectorization_status') != 'success':
            validation_result['is_valid'] = False
            validation_result['issues'].append("向量化状态异常")
        
        # 检查视觉向量
        visual_embedding = result.get('image_embedding', [])
        if not visual_embedding:
            validation_result['is_valid'] = False
            validation_result['issues'].append("视觉向量为空")
        elif len(visual_embedding) < 256:
            validation_result['warnings'].append("视觉向量维度较低")
        
        # 检查语义向量
        semantic_embedding = result.get('description_embedding', [])
        if not semantic_embedding:
            validation_result['is_valid'] = False
            validation_result['issues'].append("语义向量为空")
        elif len(semantic_embedding) < 256:
            validation_result['warnings'].append("语义向量维度较低")
        
        # 检查模型信息
        if not result.get('image_embedding_model'):
            validation_result['warnings'].append("缺少视觉模型信息")
        
        if not result.get('description_embedding_model'):
            validation_result['warnings'].append("缺少语义模型信息")
        
        # 生成建议
        if validation_result['warnings']:
            validation_result['recommendations'].append("考虑使用更高维度的向量模型")
        
        if not validation_result['is_valid']:
            validation_result['recommendations'].append("检查向量化流程和模型配置")
        
        return validation_result
    
    def get_vectorization_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取向量化统计信息
        """
        if not results:
            return {
                'total_images': 0,
                'successful_vectorizations': 0,
                'failed_vectorizations': 0,
                'success_rate': 0.0
            }
        
        total_images = len(results)
        successful = sum(1 for r in results if r.get('vectorization_status') == 'success')
        failed = total_images - successful
        success_rate = successful / total_images if total_images > 0 else 0
        
        # 向量维度统计
        visual_dimensions = []
        semantic_dimensions = []
        
        for result in results:
            if result.get('vectorization_status') == 'success':
                visual_embedding = result.get('image_embedding', [])
                semantic_embedding = result.get('description_embedding', [])
                
                if visual_embedding:
                    visual_dimensions.append(len(visual_embedding))
                if semantic_embedding:
                    semantic_dimensions.append(len(semantic_embedding))
        
        # 质量统计
        quality_scores = []
        for result in results:
            if result.get('vectorization_status') == 'success':
                metadata = result.get('vectorization_metadata', {})
                visual_quality = metadata.get('vector_quality', {}).get('visual_quality', {})
                semantic_quality = metadata.get('vector_quality', {}).get('semantic_quality', {})
                
                avg_quality = (visual_quality.get('quality_score', 0) + semantic_quality.get('quality_score', 0)) / 2
                quality_scores.append(avg_quality)
        
        return {
            'total_images': total_images,
            'successful_vectorizations': successful,
            'failed_vectorizations': failed,
            'success_rate': success_rate,
            'vector_dimensions': {
                'visual': {
                    'count': len(visual_dimensions),
                    'min': min(visual_dimensions) if visual_dimensions else 0,
                    'max': max(visual_dimensions) if visual_dimensions else 0,
                    'average': sum(visual_dimensions) / len(visual_dimensions) if visual_dimensions else 0
                },
                'semantic': {
                    'count': len(semantic_dimensions),
                    'min': min(semantic_dimensions) if semantic_dimensions else 0,
                    'max': max(semantic_dimensions) if semantic_dimensions else 0,
                    'average': sum(semantic_dimensions) / len(semantic_dimensions) if semantic_dimensions else 0
                }
            },
            'quality_statistics': {
                'count': len(quality_scores),
                'min': min(quality_scores) if quality_scores else 0,
                'max': max(quality_scores) if quality_scores else 0,
                'average': sum(quality_scores) / len(quality_scores) if quality_scores else 0
            }
        }
