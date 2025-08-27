"""
图片处理器

负责处理图片内容，包括图片增强、双重向量化和元数据生成。
完全符合设计文档规范，使用配置管理和ModelCaller。
"""

import os
import logging
import shutil
from typing import List, Dict, Any, Optional
from pathlib import Path

class ImageProcessor:
    """
    图片处理器
    
    功能：
    - 图片增强处理（使用Qwen-VL-Plus）
    - 双重向量化（视觉向量和语义向量）
    - 元数据生成和管理
    - 图片文件复制和整理
    """
    
    def __init__(self, config_manager, model_caller):
        """
        初始化图片处理器
        
        :param config_manager: 配置管理器实例
        :param model_caller: 模型调用器实例
        """
        self.config_manager = config_manager
        self.config = config_manager.get_all_config()
        self.model_caller = model_caller
        
        # 配置路径
        self.final_image_dir = self.config_manager.get_path('final_image_dir')
        self.mineru_output_dir = self.config_manager.get_path('mineru_output_dir')
        
        # 图片处理配置
        self.enable_enhancement = self.config.get('image_processing.enable_enhancement', True)
        self.enhancement_model = self.config.get('image_processing.enhancement_model', 'qwen-vl-plus')
        
        # 向量化配置
        self.image_embedding_model = self.config.get('vectorization.image_embedding_model', 'multimodal-embedding-one-peace-v1')
        self.text_embedding_model = self.config.get('vectorization.text_embedding_model', 'text-embedding-v1')
        
        logging.info("ImageProcessor初始化完成")
    
    def process_images_from_json(self, json_file_path: str) -> List[Dict[str, Any]]:
        """
        从JSON文件处理图片
        
        :param json_file_path: JSON文件路径
        :return: 处理后的图片信息列表
        """
        try:
            logging.info(f"开始处理JSON文件中的图片: {json_file_path}")
            
            # 1. 解析JSON文件，提取图片信息
            image_info_list = self._extract_image_info_from_json(json_file_path)
            
            if not image_info_list:
                logging.warning(f"JSON文件中未找到图片信息: {json_file_path}")
                return []
            
            # 2. 处理每张图片
            processed_images = []
            for image_info in image_info_list:
                try:
                    processed_image = self._process_single_image(image_info)
                    if processed_image:
                        processed_images.append(processed_image)
                except Exception as e:
                    logging.error(f"处理图片失败: {image_info.get('image_path', 'unknown')}, 错误: {e}")
                    continue
            
            logging.info(f"图片处理完成: {len(processed_images)} 张图片")
            return processed_images
            
        except Exception as e:
            logging.error(f"处理JSON文件中的图片失败: {json_file_path}, 错误: {e}")
            return []
    
    def _extract_image_info_from_json(self, json_file_path: str) -> List[Dict[str, Any]]:
        """
        从JSON文件提取图片信息
        
        :param json_file_path: JSON文件路径
        :return: 图片信息列表
        """
        try:
            import json
            
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            image_info_list = []
            
            # 查找图片类型的内容
            if 'content_list' in data:
                for item in data['content_list']:
                    if item.get('type') == 'image':
                        image_info = {
                            'image_path': item.get('img_path', ''),
                            'image_caption': item.get('image_caption', []),
                            'image_footnote': item.get('image_footnote', []),
                            'page': item.get('page', 1),
                            'confidence': item.get('confidence', 0.9),
                            'position': item.get('position', {}),
                            'original_type': 'image'
                        }
                        image_info_list.append(image_info)
            
            # 如果没有找到content_list，尝试其他字段
            if not image_info_list and 'images' in data:
                for item in data['images']:
                    image_info = {
                        'image_path': item.get('path', item.get('img_path', '')),
                        'image_caption': item.get('caption', item.get('image_caption', [])),
                        'image_footnote': item.get('footnote', item.get('image_footnote', [])),
                        'page': item.get('page', 1),
                        'confidence': item.get('confidence', 0.9),
                        'position': item.get('position', {}),
                        'original_type': 'image'
                    }
                    image_info_list.append(image_info)
            
            logging.info(f"从JSON文件提取到 {len(image_info_list)} 张图片信息")
            return image_info_list
            
        except Exception as e:
            logging.error(f"提取JSON文件中的图片信息失败: {e}")
            return []
    
    def _process_single_image(self, image_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        处理单张图片
        
        :param image_info: 图片信息
        :return: 处理后的图片信息
        """
        try:
            # 1. 获取图片路径
            image_path = image_info.get('image_path', '')
            if not image_path:
                logging.warning("图片路径为空，跳过处理")
                return None
            
            # 2. 构建完整的图片路径
            full_image_path = self._build_full_image_path(image_path)
            if not full_image_path or not os.path.exists(full_image_path):
                logging.warning(f"图片文件不存在: {full_image_path}")
                return None
            
            # 3. 复制图片到最终目录
            final_image_path = self._copy_image_to_final_dir(full_image_path, image_info)
            if not final_image_path:
                logging.error(f"复制图片失败: {full_image_path}")
                return None
            
            # 4. 图片增强处理
            enhanced_description = ""
            if self.enable_enhancement:
                enhanced_description = self._enhance_image(final_image_path, image_info)
            
            # 5. 生成双重向量
            visual_embedding = self._generate_visual_embedding(final_image_path)
            semantic_embedding = self._generate_semantic_embedding(enhanced_description or self._build_basic_description(image_info))
            
            # 6. 构建最终结果
            processed_image = {
                'image_path': final_image_path,
                'original_path': full_image_path,
                'image_caption': image_info.get('image_caption', []),
                'image_footnote': image_info.get('image_footnote', []),
                'page': image_info.get('page', 1),
                'confidence': image_info.get('confidence', 0.9),
                'position': image_info.get('position', {}),
                'enhanced_description': enhanced_description,
                'visual_embedding': visual_embedding,
                'semantic_embedding': semantic_embedding,
                'original_type': 'image',
                'processing_status': 'completed'
            }
            
            logging.info(f"图片处理完成: {os.path.basename(final_image_path)}")
            return processed_image
            
        except Exception as e:
            logging.error(f"处理单张图片失败: {e}")
            return None
    
    def _build_full_image_path(self, image_path: str) -> Optional[str]:
        """
        构建完整的图片路径
        
        :param image_path: 相对图片路径
        :return: 完整图片路径
        """
        try:
            # 尝试多种可能的路径组合
            possible_paths = [
                os.path.join(self.mineru_output_dir, image_path),
                os.path.join(self.mineru_output_dir, 'images', image_path),
                os.path.join(self.mineru_output_dir, '..', 'images', image_path),
                image_path  # 如果已经是绝对路径
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    return path
            
            # 如果都找不到，尝试在mineru_output_dir下递归搜索
            for root, dirs, files in os.walk(self.mineru_output_dir):
                for file in files:
                    if file == os.path.basename(image_path):
                        return os.path.join(root, file)
            
            return None
            
        except Exception as e:
            logging.error(f"构建图片路径失败: {e}")
            return None
    
    def _copy_image_to_final_dir(self, source_path: str, image_info: Dict[str, Any]) -> Optional[str]:
        """
        复制图片到最终目录
        
        :param source_path: 源图片路径
        :param image_info: 图片信息
        :return: 目标图片路径
        """
        try:
            # 确保目标目录存在
            os.makedirs(self.final_image_dir, exist_ok=True)
            
            # 生成目标文件名
            source_filename = os.path.basename(source_path)
            base_name, ext = os.path.splitext(source_filename)
            
            # 使用页码和原始文件名构建目标文件名
            page = image_info.get('page', 1)
            target_filename = f"{base_name}_p{page}{ext}"
            target_path = os.path.join(self.final_image_dir, target_filename)
            
            # 如果文件已存在，添加序号
            counter = 1
            while os.path.exists(target_path):
                target_filename = f"{base_name}_p{page}_{counter}{ext}"
                target_path = os.path.join(self.final_image_dir, target_filename)
                counter += 1
            
            # 复制文件
            shutil.copy2(source_path, target_path)
            
            logging.info(f"图片复制完成: {source_path} -> {target_path}")
            return target_path
            
        except Exception as e:
            logging.error(f"复制图片失败: {e}")
            return None
    
    def _enhance_image(self, image_path: str, image_info: Dict[str, Any]) -> str:
        """
        图片增强处理
        
        :param image_path: 图片路径
        :param image_info: 图片信息
        :return: 增强后的描述
        """
        try:
            if not self.enable_enhancement:
                return ""
            
            logging.info(f"开始图片增强: {os.path.basename(image_path)}")
            
            # 调用模型进行图片增强
            enhanced_description = self.model_caller.call_image_enhancement(image_path, image_info)
            
            logging.info(f"图片增强完成: {os.path.basename(image_path)}")
            return enhanced_description
            
        except Exception as e:
            logging.error(f"图片增强失败: {image_path}, 错误: {e}")
            return ""
    
    def _generate_visual_embedding(self, image_path: str) -> List[float]:
        """
        生成视觉向量
        
        :param image_path: 图片路径
        :return: 视觉向量
        """
        try:
            logging.info(f"开始生成视觉向量: {os.path.basename(image_path)}")
            
            # 调用模型生成视觉向量
            visual_embedding = self.model_caller.call_visual_embedding(image_path)
            
            logging.info(f"视觉向量生成完成: {os.path.basename(image_path)}")
            return visual_embedding
            
        except Exception as e:
            logging.error(f"生成视觉向量失败: {image_path}, 错误: {e}")
            return []
    
    def _generate_semantic_embedding(self, text: str) -> List[float]:
        """
        生成语义向量
        
        :param text: 文本内容
        :return: 语义向量
        """
        try:
            if not text:
                return []
            
            logging.info("开始生成语义向量")
            
            # 调用模型生成语义向量
            semantic_embedding = self.model_caller.call_text_embedding(text)
            
            logging.info("语义向量生成完成")
            return semantic_embedding
            
        except Exception as e:
            logging.error(f"生成语义向量失败: {e}")
            return []
    
    def _build_basic_description(self, image_info: Dict[str, Any]) -> str:
        """
        构建基础图片描述
        
        :param image_info: 图片信息
        :return: 基础描述
        """
        try:
            description_parts = []
            
            # 添加图片标题
            caption = image_info.get('image_caption', [])
            if caption and len(caption) > 0:
                description_parts.append(f"图片标题: {' '.join(caption)}")
            
            # 添加图片脚注
            footnote = image_info.get('image_footnote', [])
            if footnote and len(footnote) > 0:
                description_parts.append(f"图片脚注: {' '.join(footnote)}")
            
            # 添加页码信息
            page = image_info.get('page', 1)
            description_parts.append(f"页码: {page}")
            
            return " | ".join(description_parts) if description_parts else "图片内容"
            
        except Exception as e:
            logging.error(f"构建基础图片描述失败: {e}")
            return "图片内容"
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        获取处理统计信息
        
        :return: 统计信息
        """
        try:
            # 统计最终目录中的图片数量
            image_count = 0
            total_size = 0
            
            if os.path.exists(self.final_image_dir):
                for file in os.listdir(self.final_image_dir):
                    file_path = os.path.join(self.final_image_dir, file)
                    if os.path.isfile(file_path) and file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        image_count += 1
                        try:
                            total_size += os.path.getsize(file_path)
                        except OSError:
                            pass
            
            return {
                'total_images': image_count,
                'total_size_bytes': total_size,
                'total_size_mb': total_size / (1024 * 1024) if total_size > 0 else 0,
                'final_image_dir': self.final_image_dir,
                'enhancement_enabled': self.enable_enhancement,
                'enhancement_model': self.enhancement_model,
                'image_embedding_model': self.image_embedding_model,
                'text_embedding_model': self.text_embedding_model
            }
            
        except Exception as e:
            logging.error(f"获取处理统计信息失败: {e}")
            return {}


if __name__ == "__main__":
    # 测试ImageProcessor
    from v3.config.config_manager import ConfigManager
    from v3.utils.model_caller import ModelCaller
    
    config_manager = ConfigManager()
    if config_manager.load_config():
        try:
            model_caller = ModelCaller(config_manager)
            processor = ImageProcessor(config_manager, model_caller)
            
            # 获取统计信息
            stats = processor.get_processing_stats()
            print(f"图片处理器统计信息: {stats}")
            
        except Exception as e:
            print(f"ImageProcessor测试失败: {e}")
    else:
        print("配置加载失败，无法测试ImageProcessor")
