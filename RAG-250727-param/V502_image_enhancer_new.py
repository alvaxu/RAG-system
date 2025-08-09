#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片增强新程序 - 查询、确认和深度处理

功能说明：
1. 查询数据库中的图片是否做了深度处理，列出哪些没做
2. 根据用户确认决定是否补做深度处理
3. 处理方式要和主程序 image_enhancer.py 一致
4. 字段和逻辑以现有数据库结构和 image_enhancer.py 为准
5. 可以调用 image_enhancer.py 中的相应模块
"""

import os
import sys
import json
import time
import logging
from typing import List, Dict, Any, Optional

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from langchain_community.vectorstores import FAISS
    from langchain_community.embeddings import DashScopeEmbeddings
    from config.settings import Settings
    from document_processing.image_enhancer import ImageEnhancer
    from document_processing.vector_generator import VectorGenerator
    from document_processing.image_processor import ImageProcessor
except ImportError as e:
    print(f"❌ 缺少必要的依赖包: {e}")
    print("请确保项目依赖已正确安装")
    sys.exit(1)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImageEnhanceNew:
    """图片增强新程序 - 查询、确认和深度处理"""
    
    def __init__(self):
        """初始化程序"""
        try:
            # 加载配置
            self.config = Settings.load_from_file('config.json')
            self.api_key = self.config.dashscope_api_key
            
            # 使用主程序中的ImageProcessor来管理配置和初始化
            self.image_processor = ImageProcessor(self.api_key, self.config.__dict__)
            
            # 初始化图像增强器（通过ImageProcessor）
            if self.image_processor.enhancement_enabled:
                self.image_enhancer = self.image_processor.image_enhancer
            else:
                # 如果ImageProcessor中没有启用，则手动初始化
                image_config = {
                    'enable_enhancement': self.config.enable_enhancement,
                    'enhancement_model': self.config.enhancement_model,
                    'enhancement_max_tokens': self.config.enhancement_max_tokens,
                    'enhancement_temperature': self.config.enhancement_temperature,
                    'enhancement_batch_size': self.config.enhancement_batch_size,
                    'enable_progress_logging': self.config.enable_progress_logging
                }
                self.image_enhancer = ImageEnhancer(
                    api_key=self.api_key,
                    config=image_config
                )
            
            # 初始化向量生成器（用于保存数据库）
            self.vector_generator = VectorGenerator(self.config.__dict__)
            
            # 向量数据库路径 - 使用配置管理
            self.vector_db_path = self.config.vector_db_dir
            
            logger.info("图片增强新程序初始化完成")
            
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            raise
    
    def load_vector_store(self) -> Optional[FAISS]:
        """加载向量数据库"""
        try:
            # 使用配置中的嵌入模型，如果没有配置则使用默认值
            embedding_model = getattr(self.config, 'text_embedding_model', 'text-embedding-v1')
            embeddings = DashScopeEmbeddings(
                dashscope_api_key=self.api_key, 
                model=embedding_model
            )
            # 使用配置中的安全设置，如果没有配置则使用默认值
            allow_dangerous_deserialization = getattr(self.config, 'allow_dangerous_deserialization', True)
            vector_store = FAISS.load_local(
                self.vector_db_path, 
                embeddings, 
                allow_dangerous_deserialization=allow_dangerous_deserialization
            )
            logger.info(f"向量数据库加载成功，包含 {len(vector_store.docstore._dict)} 个文档")
            return vector_store
            
        except Exception as e:
            logger.error(f"加载向量数据库失败: {e}")
            return None
    
    def query_image_status(self) -> Dict[str, List[Dict[str, Any]]]:
        """查询数据库中图片的处理状态"""
        print("🔍 正在查询数据库中的图片状态...")
        
        vector_store = self.load_vector_store()
        if not vector_store:
            return {'processed': [], 'unprocessed': []}
        
        processed_images = []
        unprocessed_images = []
        
        for doc_id, doc in vector_store.docstore._dict.items():
            metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
            
            # 检查是否为图片文档
            if metadata.get('chunk_type') == 'image':
                image_path = metadata.get('image_path', '')
                image_type = 'unknown'
                
                # 使用主程序中的函数检测图片类型
                if image_path and os.path.exists(image_path):
                    try:
                        image_type = self._detect_image_type(image_path)
                    except Exception as e:
                        logger.warning(f"检测图片类型失败: {e}")
                
                image_info = {
                    'doc_id': doc_id,
                    'image_path': image_path,
                    'document_name': metadata.get('document_name', '未知文档'),
                    'page_number': metadata.get('page_number', 1),
                    'image_id': metadata.get('image_id', 'unknown'),
                    'image_type': image_type,
                    'enhanced_description': metadata.get('enhanced_description', ''),
                    'has_layered': 'layered_descriptions' in metadata,
                    'has_structured': 'structured_info' in metadata,
                    'has_timestamp': 'enhancement_timestamp' in metadata,
                    'has_enabled': 'enhancement_enabled' in metadata
                }
                
                # 判断是否已深度处理
                if self._is_deep_processed(metadata):
                    processed_images.append(image_info)
                else:
                    unprocessed_images.append(image_info)
        
        print(f"📊 查询完成:")
        print(f"   ✅ 已深度处理: {len(processed_images)} 张")
        print(f"   ⏳ 未深度处理: {len(unprocessed_images)} 张")
        
        return {
            'processed': processed_images,
            'unprocessed': unprocessed_images
        }
    
    def _is_deep_processed(self, metadata: Dict[str, Any]) -> bool:
        """判断图片是否已深度处理"""
        # 主要检查enhanced_description是否包含深度处理标注
        enhanced_desc = metadata.get('enhanced_description', '')
        
        # 检查是否包含主程序添加的深度处理标注 - 使用配置管理
        depth_markers = getattr(self.config, 'depth_processing_markers', [
            '基础视觉描述:', '内容理解描述:', '数据趋势描述:', '语义特征描述:',
            'chart_type:', 'data_points:', 'trends:', 'key_insights:',
            'enhancement_enabled'
        ])
        
        has_depth_markers = any(marker in enhanced_desc for marker in depth_markers)
        
        # 如果enhanced_description包含深度标记，说明已深度处理
        if has_depth_markers:
            return True
        
        # 备用检查：元数据字段（如果存在的话）
        has_layered = 'layered_descriptions' in metadata
        has_structured = 'structured_info' in metadata
        
        if has_layered and has_structured:
            return True
        
        # 如果都不满足，说明未深度处理
        return False
    
    def _detect_image_type(self, image_path: str) -> str:
        """检测图片类型 - 使用主程序中的函数"""
        try:
            return self.image_processor._detect_image_type(image_path)
        except Exception as e:
            logger.warning(f"检测图片类型失败: {e}")
            return 'general'
    
    def _extract_semantic_features(self, image_path: str) -> Dict[str, Any]:
        """提取图片语义特征 - 使用主程序中的函数"""
        try:
            # 这里可以调用主程序中的语义特征提取函数
            # 如果需要生成embedding，可以使用 self.image_processor.generate_image_embedding(image_path)
            # 然后调用语义特征提取
            return {}
        except Exception as e:
            logger.warning(f"提取语义特征失败: {e}")
            return {}
    
    def display_image_status(self, image_status: Dict[str, List[Dict[str, Any]]]):
        """显示图片状态信息"""
        print("\n" + "="*80)
        print("📊 图片处理状态详情")
        print("="*80)
        
        # 显示已处理的图片
        processed = image_status['processed']
        if processed:
            print(f"\n✅ 已深度处理的图片 ({len(processed)} 张):")
            for i, img in enumerate(processed[:5], 1):  # 只显示前5张
                image_type_info = f" [{img.get('image_type', 'unknown')}]" if img.get('image_type') != 'unknown' else ""
                print(f"   {i}. {img['document_name']} - 第{img['page_number']}页 - {img['image_id']}{image_type_info}")
            if len(processed) > 5:
                print(f"   ... 还有 {len(processed) - 5} 张已处理图片")
        else:
            print("\n✅ 已深度处理的图片: 0 张")
        
        # 显示未处理的图片
        unprocessed = image_status['unprocessed']
        if unprocessed:
            print(f"\n⏳ 未深度处理的图片 ({len(unprocessed)} 张):")
            for i, img in enumerate(unprocessed[:10], 1):  # 显示前10张
                image_type_info = f" [{img.get('image_type', 'unknown')}]" if img.get('image_type') != 'unknown' else ""
                print(f"   {i}. {img['document_name']} - 第{img['page_number']}页 - {img['image_id']}{image_type_info}")
            if len(unprocessed) > 10:
                print(f"   ... 还有 {len(unprocessed) - 10} 张未处理图片")
        else:
            print("\n⏳ 未深度处理的图片: 0 张")
        
        print("\n" + "="*80)
    
    def get_user_confirmation(self, unprocessed_count: int) -> bool:
        """获取用户确认是否进行深度处理"""
        if unprocessed_count == 0:
            print("🎉 所有图片都已深度处理完成！")
            return False
        
        print(f"\n❓ 发现 {unprocessed_count} 张图片未深度处理")
        print("请选择操作:")
        print("   1. 进行深度处理")
        print("   2. 退出程序")
        
        while True:
            try:
                choice = input("\n请输入选择 (1 或 2): ").strip()
                if choice == '1':
                    return True
                elif choice == '2':
                    return False
                else:
                    print("❌ 无效选择，请输入 1 或 2")
            except KeyboardInterrupt:
                print("\n\n👋 程序已退出")
                return False
    
    def process_unprocessed_images(self, unprocessed_images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理未深度处理的图片"""
        print(f"\n🔄 开始深度处理 {len(unprocessed_images)} 张图片...")
        
        # 加载向量数据库
        vector_store = self.load_vector_store()
        if not vector_store:
            print("❌ 无法加载向量数据库，处理终止")
            return []
        
        # 准备批量处理的数据格式
        image_batch = []
        for img_info in unprocessed_images:
            # 检查图片文件是否存在
            image_path = img_info['image_path']
            if not os.path.exists(image_path):
                print(f"⚠️ 图片文件不存在: {image_path}")
                continue
            
            # 使用主程序中的函数检测图片类型和生成图片ID
            image_type = self._detect_image_type(image_path)
            if not img_info.get('image_id') or img_info['image_id'] == 'unknown':
                try:
                    generated_image_id = self.image_processor._generate_image_id(image_path)
                    img_info['image_id'] = generated_image_id
                except Exception as e:
                    logger.warning(f"生成图片ID失败: {e}")
                
            image_batch.append({
                'image_path': image_path,
                'enhanced_description': img_info.get('enhanced_description', ''),
                'doc_id': img_info['doc_id'],
                'document_name': img_info['document_name'],
                'page_number': img_info['page_number'],
                'image_id': img_info['image_id'],
                'image_type': image_type
            })
        
        if not image_batch:
            print("❌ 没有有效的图片文件可以处理")
            return []
        
        # 调用主程序中的批量处理函数
        print(f"📷 准备处理 {len(image_batch)} 张有效图片...")
        enhanced_results = self.image_enhancer.enhance_batch_images(image_batch)
        
        # 处理结果并更新数据库
        results = []
        for i, (img_info, enhanced_info) in enumerate(zip(image_batch, enhanced_results), 1):
            try:
                print(f"\n📷 处理进度: {i}/{len(image_batch)}")
                print(f"   文档: {img_info['document_name']}")
                print(f"   页码: {img_info['page_number']}")
                print(f"   图片ID: {img_info['image_id']}")
                
                # 更新向量数据库中的元数据
                if enhanced_info and 'enhanced_description' in enhanced_info:
                    try:
                        # 获取文档对象
                        doc = vector_store.docstore._dict[img_info['doc_id']]
                        
                        # 更新元数据
                        updated_metadata = doc.metadata.copy()
                        updated_metadata['enhanced_description'] = enhanced_info['enhanced_description']
                        updated_metadata['enhancement_timestamp'] = int(time.time())
                        updated_metadata['enhancement_enabled'] = True
                        
                        # 如果有分层描述，也保存
                        if 'layered_descriptions' in enhanced_info:
                            updated_metadata['layered_descriptions'] = enhanced_info['layered_descriptions']
                        
                        # 如果有结构化信息，也保存
                        if 'structured_info' in enhanced_info:
                            updated_metadata['structured_info'] = enhanced_info['structured_info']
                        
                        # 添加图片类型信息（使用主程序中的检测结果）
                        if 'image_type' in img_info:
                            updated_metadata['image_type'] = img_info['image_type']
                        
                        # 更新文档元数据
                        doc.metadata = updated_metadata
                        
                        print(f"   ✅ 数据库更新完成")
                        
                    except Exception as e:
                        print(f"   ⚠️ 数据库更新失败: {e}")
                        enhanced_info = {'enhanced_description': img_info['enhanced_description']}
                
                # 记录处理结果
                results.append({
                    'doc_id': img_info['doc_id'],
                    'status': 'success',
                    'enhanced_info': enhanced_info,
                    'image_path': img_info['image_path']
                })
                
                print(f"   ✅ 处理完成")
                    
            except Exception as e:
                logger.error(f"处理图片失败 {img_info['image_id']}: {e}")
                results.append({
                    'doc_id': img_info['doc_id'],
                    'status': 'failed',
                    'error': str(e),
                    'image_path': img_info['image_path']
                })
                print(f"   ❌ 处理失败: {e}")
        
        # 保存更新后的向量数据库
        try:
            print(f"\n💾 正在保存更新后的向量数据库...")
            # 使用主程序中的保存函数，保持一致性
            self.vector_generator._save_vector_store_with_metadata(vector_store, self.vector_db_path)
            print(f"✅ 向量数据库保存成功")
        except Exception as e:
            print(f"❌ 保存向量数据库失败: {e}")
            logger.error(f"保存向量数据库失败: {e}")
        
        print(f"\n✅ 深度处理完成，共处理 {len(image_batch)} 张图片")
        return results
    
    def display_processing_results(self, results: List[Dict[str, Any]]):
        """显示处理结果"""
        print("\n" + "="*80)
        print("📊 深度处理结果统计")
        print("="*80)
        
        success_count = len([r for r in results if r['status'] == 'success'])
        failed_count = len([r for r in results if r['status'] == 'failed'])
        
        print(f"✅ 成功处理: {success_count} 张")
        print(f"❌ 处理失败: {failed_count} 张")
        print(f"📊 成功率: {success_count/(success_count+failed_count)*100:.1f}%")
        
        if failed_count > 0:
            print(f"\n❌ 失败详情:")
            for result in results:
                if result['status'] == 'failed':
                    print(f"   - {result['image_path']}: {result['error']}")
        
        print("\n" + "="*80)
    
    def run(self):
        """运行主程序"""
        try:
            print("🚀 图片增强新程序启动")
            print("="*50)
            
            # 1. 查询图片状态
            image_status = self.query_image_status()
            
            # 2. 显示状态信息
            self.display_image_status(image_status)
            
            # 3. 获取用户确认
            unprocessed_count = len(image_status['unprocessed'])
            if not self.get_user_confirmation(unprocessed_count):
                print("👋 程序退出")
                return
            
            # 4. 进行深度处理
            results = self.process_unprocessed_images(image_status['unprocessed'])
            
            # 5. 显示处理结果
            self.display_processing_results(results)
            
            print("🎉 程序执行完成！")
            
        except Exception as e:
            logger.error(f"程序执行失败: {e}")
            print(f"❌ 程序执行失败: {e}")
            import traceback
            traceback.print_exc()


def main():
    """主函数"""
    try:
        enhancer = ImageEnhanceNew()
        enhancer.run()
    except Exception as e:
        print(f"❌ 程序启动失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
