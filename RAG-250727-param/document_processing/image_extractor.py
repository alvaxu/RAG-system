'''
程序说明：
## 1. 图片提取器，整合现有的extract_images_from_md.py功能
## 2. 从Markdown文件和JSON文件中提取图片并保存到本地
## 3. 统一图片提取接口和错误处理
## 4. 为后续的图片向量化提供基础
'''

import os
import logging
import zipfile
import re
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import shutil

# 导入现有的图片提取功能
# from .extract_images_from_md import extract_images_from_md

# 配置日志
logger = logging.getLogger(__name__)


class ImageExtractor:
    """
    图片提取器，从Markdown文件和JSON文件中提取图片
    """
    
    def __init__(self, config):
        """
        初始化图片提取器
        :param config: 配置对象
        """
        self.config = config
    
    def extract_images(self, md_files: List[str]) -> Optional[List[Dict[str, Any]]]:
        """
        从Markdown文件中提取图片
        :param md_files: Markdown文件列表
        :return: 提取的图片信息列表
        """
        try:
            if not md_files:
                logger.warning("没有提供Markdown文件")
                return None
            
            extracted_images = []
            seen_images = set()  # 用于去重
            
            for md_file in md_files:
                try:
                    # 获取Markdown文件所在目录
                    md_path = Path(md_file)
                    md_dir = md_path.parent
                    
                    # 调用现有的图片提取功能
                    images = self._extract_images_from_single_file(md_file)
                    
                    if images:
                        # 去重处理
                        for image in images:
                            image_hash = image.get('image_hash', '')
                            if image_hash and image_hash not in seen_images:
                                extracted_images.append(image)
                                seen_images.add(image_hash)
                                logger.debug(f"添加图片: {image_hash}")
                            else:
                                logger.debug(f"跳过重复图片: {image_hash}")
                        
                        logger.info(f"从文件 {md_path.name} 提取了 {len(images)} 张图片（去重后）")
                    else:
                        logger.info(f"文件 {md_path.name} 中没有找到图片")
                        
                except Exception as e:
                    logger.warning(f"处理文件 {md_file} 时出错: {e}")
                    continue
            
            if extracted_images:
                logger.info(f"总共提取了 {len(extracted_images)} 张图片（去重后）")
                return extracted_images
            else:
                logger.info("没有找到任何图片")
                return None
                
        except Exception as e:
            logger.error(f"图片提取失败: {e}")
            return None
    
    def extract_images_from_json_files(self, md_files: List[str]) -> Optional[List[Dict[str, Any]]]:
        """
        从JSON文件中提取图片信息
        :param md_files: Markdown文件列表（用于找到对应的JSON文件）
        :return: 提取的图片信息列表
        """
        try:
            if not md_files:
                logger.warning("没有提供Markdown文件")
                return None
            
            extracted_images = []
            seen_images = set()  # 用于去重
            
            for md_file in md_files:
                try:
                    # 获取Markdown文件所在目录和文件名
                    md_path = Path(md_file)
                    md_dir = md_path.parent
                    doc_name = md_path.stem
                    
                    # 查找对应的JSON文件
                    json_file = md_dir / f"{doc_name}_1.json"
                    
                    if not json_file.exists():
                        logger.info(f"找不到对应的JSON文件: {json_file}")
                        continue
                    
                    # 读取JSON文件
                    with open(json_file, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                    
                    # 提取图片信息
                    images = self._extract_images_from_json_data(json_data, doc_name, md_dir)
                    
                    if images:
                        # 去重处理
                        for image in images:
                            image_hash = image.get('image_hash', '')
                            if image_hash and image_hash not in seen_images:
                                extracted_images.append(image)
                                seen_images.add(image_hash)
                                logger.debug(f"从JSON添加图片: {image_hash}")
                            else:
                                logger.debug(f"跳过重复图片: {image_hash}")
                        
                        logger.info(f"从JSON文件 {json_file.name} 提取了 {len(images)} 张图片信息（去重后）")
                    else:
                        logger.info(f"JSON文件 {json_file.name} 中没有找到图片信息")
                        
                except Exception as e:
                    logger.warning(f"处理JSON文件时出错: {e}")
                    continue
            
            if extracted_images:
                logger.info(f"总共从JSON文件提取了 {len(extracted_images)} 张图片信息（去重后）")
                return extracted_images
            else:
                logger.info("没有从JSON文件找到任何图片信息")
                return None
                
        except Exception as e:
            logger.error(f"从JSON文件提取图片失败: {e}")
            return None
    
    def _extract_images_from_json_data(self, json_data: List[Dict[str, Any]], doc_name: str, md_dir: Path) -> List[Dict[str, Any]]:
        """
        从JSON数据中提取图片信息，如下所示：
            {
                "type": "image",
                "img_path": "images/242e38820aba0d1ca2a2c6cbc8e6c48d8d895158a84374618069527ceb403f99.jpg",
                "img_caption": [
                    "最近一年股票与沪深300比较"
                ],
                "img_footnote": [],
                "page_idx": 0
            },
        :param json_data: JSON数据
        :param doc_name: 文档名称
        :param md_dir: Markdown文件目录
        :return: 图片信息列表
        """
        images = []
        
        try:
            # 创建图片输出目录
            images_dir = md_dir / "images"
            images_dir.mkdir(exist_ok=True)
            
            # 创建统一图片存储目录
            central_images_dir = Path(self.config.central_images_dir)
            central_images_dir.mkdir(parents=True, exist_ok=True)
            
            for item in json_data:
                if item.get("type") == "image":
                    img_path = item.get("img_path", "")
                    # 修复字段名映射：JSON中是image_caption和image_footnote，需要映射到img_caption和img_footnote
                    # 注意：minerU现在把所有信息都放在image_caption中，image_footnote为空
                    image_caption = item.get("image_caption", [])  # 从image_caption映射到img_caption
                    image_footnote = item.get("image_footnote", [])  # 从image_footnote映射到img_footnote
                    
                    # 处理新的逻辑：优先使用image_footnote，如果为空且image_caption包含多个元素，则分离
                    if image_footnote and len(image_footnote) > 0:
                        # 如果image_footnote有内容，优先使用它
                        img_caption = image_caption
                        img_footnote = image_footnote
                    elif len(image_caption) > 1:
                        # 如果image_footnote为空但image_caption包含多个元素，分离处理
                        img_caption = [image_caption[0]]  # 第一个元素作为标题
                        img_footnote = image_caption[1:]  # 其余元素作为脚注
                    else:
                        # 其他情况保持原样
                        img_caption = image_caption
                        img_footnote = image_footnote
                    page_idx = item.get("page_idx", 0)
                    
                    if img_path:
                        # 提取图片文件名
                        img_filename = Path(img_path).name
                        
                        # 检查图片文件是否存在
                        img_file_path = images_dir / img_filename
                        
                        # 检查图片文件是否存在
                        if img_file_path.exists():
                            # 移动图片到统一存储目录
                            central_image_path = central_images_dir / img_filename
                            
                            # 检查是否已存在相同文件名的图片
                            if central_image_path.exists():
                                logger.info(f"图片已存在，跳过复制: {img_filename}")
                            else:
                                # 复制图片到统一目录
                                shutil.copy2(str(img_file_path), str(central_image_path))
                                logger.info(f"复制图片到统一目录: {img_filename}")
                            
                            # 构建图片信息（路径指向统一目录）
                            image_info = {
                                'original_file': str(md_dir / f"{doc_name}.md"),
                                'image_hash': img_filename.split('.')[0],  # 假设文件名是哈希值
                                'image_filename': img_filename,
                                'image_path': str(central_image_path),  # 指向统一目录
                                'extension': central_image_path.suffix[1:],  # 去掉点号
                                'document_name': doc_name,
                                'page_number': page_idx + 1,  # 转换为1索引
                                'img_caption': img_caption,
                                'img_footnote': img_footnote,
                                'source_zip': 'json_extraction'
                            }
                            
                            images.append(image_info)
                            logger.debug(f"提取图片信息: {img_filename} - caption: {len(img_caption)} - footnote: {len(img_footnote)}")
                        else:
                            logger.warning(f"图片文件不存在且无法从ZIP提取: {img_file_path}")
            
            return images
            
        except Exception as e:
            logger.error(f"从JSON数据提取图片信息失败: {e}")
            return []
    
    def _extract_images_from_single_file(self, md_file: str) -> List[Dict[str, Any]]:
        """
        从单个Markdown文件中提取图片，原pdf中识别成表格的图片也已经不在md文件中，所以和json中的记录是一致的,如下所示：
            {
                "type": "table",
                "img_path": "images/23ea24fd4ac752d628f8608b282247ecb023c4dffd56b08567dbfde2291d390f.jpg",
                "table_caption": [],
                "table_footnote": [],
                "table_body": "<html><body><table><tr><td colspan=\"2\">基本数据</td></tr><tr><td>最新收盘价 (元)</td><td>91.35</td></tr><tr><td rowspan=\"2\">12mthA股价格区间（元）</td><td>41.03- 104.98</td></tr><tr><td>7,985.65</td></tr><tr><td>总股本 (百万股) 无限售A股/总股本</td><td>24.90%</td></tr><tr><td>流通市值 (亿元)</td><td>7,294.89</td></tr></table></body></html>",
                "page_idx": 0
            },
            {
                "type": "image",
                "img_path": "images/242e38820aba0d1ca2a2c6cbc8e6c48d8d895158a84374618069527ceb403f99.jpg",
                "img_caption": [
                    "最近一年股票与沪深300比较"
                ],
                "img_footnote": [],
                "page_idx": 0
            },
                
        :param md_file: Markdown文件路径
        :return: 提取的图片信息列表
        """
        try:
            md_path = Path(md_file)
            md_dir = md_path.parent
            
            # 创建图片输出目录
            images_dir = md_dir / "images"
            images_dir.mkdir(exist_ok=True)
            
            # 创建统一图片存储目录
            central_images_dir = Path(self.config.central_images_dir)
            central_images_dir.mkdir(parents=True, exist_ok=True)
            
            # 读取Markdown内容
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找图片引用
            image_pattern = r'!\[.*?\]\(images/([a-f0-9]{64})\.(jpg|jpeg|png|gif)\)'
            matches = re.findall(image_pattern, content)
            
            extracted_images = []
            
            for image_hash, extension in matches:
                image_filename = f"{image_hash}.{extension}"
                
                # 检查图片文件是否存在
                img_file_path = images_dir / image_filename
                
                if img_file_path.exists():
                    # 移动图片到统一存储目录
                    central_image_path = central_images_dir / image_filename
                    
                    # 检查是否已存在相同文件名的图片
                    if central_image_path.exists():
                        logger.info(f"图片已存在，跳过复制: {image_filename}")
                    else:
                        # 复制图片到统一目录
                        shutil.copy2(str(img_file_path), str(central_image_path))
                        logger.info(f"复制图片到统一目录: {image_filename}")
                    
                    extracted_images.append({
                        'original_file': str(md_file),
                        'image_hash': image_hash,
                        'image_filename': image_filename,
                        'image_path': str(central_image_path),  # 指向统一目录
                        'extension': extension,
                        'source_zip': 'markdown_extraction'
                    })
                    
                    logger.debug(f"成功提取图片: {image_filename}")
                else:
                    logger.warning(f"未找到图片: {image_filename}")
            
            return extracted_images
            
        except Exception as e:
            logger.error(f"从文件 {md_file} 提取图片失败: {e}")
            return []
    
    # 注释原因：此函数未被调用，图片验证和统计功能由VectorGenerator.get_vector_store_statistics提供
    # 保留作为备用实现或示例代码
    # def validate_images(self, image_files: List[Dict[str, Any]]) -> Dict[str, Any]:
    #     """
    #     验证提取的图片
    #     :param image_files: 图片文件信息列表
    #     :return: 验证结果
    #     """
    #     try:
    #         valid_images = []
    #         invalid_images = []
    #         
    #         for image_info in image_files:
    #             image_path = Path(image_info['image_path'])
    #             
    #             if image_path.exists():
    #                 # 检查文件大小
    #                 file_size = image_path.stat().st_size
    #                 if file_size > 0:
    #                     valid_images.append(image_info)
    #                     image_info['file_size'] = file_size
    #                 else:
    #                     invalid_images.append(image_info)
    #                     image_info['error'] = '文件大小为0'
    #             else:
    #                 invalid_images.append(image_info)
    #                 image_info['error'] = '文件不存在'
    #         
    #         return {
    #             'total_images': len(image_files),
    #             'valid_images': len(valid_images),
    #             'invalid_images': len(invalid_images),
    #             'valid_image_list': valid_images,
    #             'invalid_image_list': invalid_images
    #         }
    #         
    #     except Exception as e:
    #         logger.error(f"验证图片失败: {e}")
    #         return {'error': str(e)}
    
    # 注释原因：此函数未被调用，图片统计功能由VectorGenerator.get_vector_store_statistics提供
    # 保留作为备用实现或示例代码
    # def get_image_statistics(self, image_files: List[Dict[str, Any]]) -> Dict[str, Any]:
    #     """
    #     获取图片统计信息
    #     :param image_files: 图片文件信息列表
    #     :return: 统计信息
    #     """
    #     try:
    #         if not image_files:
    #             return {'total_images': 0}
    #         
    #         # 按扩展名统计
    #         extension_stats = {}
    #         total_size = 0
    #         
    #         for image_info in image_files:
    #             extension = image_info.get('extension', 'unknown')
    #             extension_stats[extension] = extension_stats.get(extension, 0) + 1
    #             
    #             file_size = image_info.get('file_size', 0)
    #             total_size += file_size
    #         
    #         return {
    #             'total_images': len(image_files),
    #             'extension_distribution': extension_stats,
    #             'total_size_bytes': total_size,
    #             'total_size_mb': total_size / (1024 * 1024),
    #             'average_size_bytes': total_size / len(image_files) if image_files else 0
    #         }
    #         
    #     except Exception as e:
    #         logger.error(f"获取图片统计信息失败: {e}")
    #         return {'error': str(e)}
    
    # 注释原因：此函数未被调用，临时文件清理功能在当前处理流程中未使用
    # 保留作为备用实现或示例代码
    # def cleanup_temp_files(self, temp_dir: str):
    #     """
    #     清理临时文件
    #     :param temp_dir: 临时目录
    #     """
    #     try:
    #         temp_path = Path(temp_dir)
    #         if temp_path.exists():
    #             shutil.rmtree(temp_path)
    #             logger.info(f"清理临时目录: {temp_dir}")
    #     except Exception as e:
    #         logger.warning(f"清理临时文件失败: {e}") 