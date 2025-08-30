#!/usr/bin/env python3
"""
V3版本图片补做程序 - 带用户确认和逻辑控制

功能：
1. 自动发现未完成的图片
2. 用户确认是否执行增强和向量化
3. 确保先增强后向量化的处理顺序
4. 智能检测避免重复向量化
5. 完整的错误处理和状态管理
"""

import os
import logging
import time
from typing import List, Dict, Any
from pathlib import Path

# 添加项目根目录到Python路径
import sys
sys.path.append(str(Path(__file__).parent.parent))

from core.vector_store_manager import LangChainVectorStoreManager
from processors.image_enhancer import ImageEnhancer
from vectorization.image_vectorizer import ImageVectorizer
from config.config_manager import ConfigManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('image_completion.log', encoding='utf-8')
    ]
)

class ImageCompletion:
    """图片补做程序"""
    
    def __init__(self, config_path: str = None):
        """初始化补做程序"""
        try:
            if config_path:
                self.config_manager = ConfigManager(config_path)
            else:
                self.config_manager = ConfigManager()
            self.vector_store_manager = LangChainVectorStoreManager(self.config_manager)
            self.image_enhancer = ImageEnhancer(self.config_manager)
            self.image_vectorizer = ImageVectorizer(self.config_manager)
            
            logging.info("图片补做程序初始化完成")
            
        except Exception as e:
            logging.error(f"初始化失败: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """获取补做程序状态"""
        try:
            return {
                'status': 'ready',
                'components': {
                    'vector_store_manager': 'initialized' if self.vector_store_manager else 'not_initialized',
                    'image_enhancer': 'initialized' if self.image_enhancer else 'not_initialized',
                    'image_vectorizer': 'initialized' if self.image_vectorizer else 'not_initialized'
                },
                'version': '3.0.0',
                'capabilities': [
                    'automatic_discovery',
                    'user_confirmation',
                    'enhancement_first',
                    'smart_vectorization',
                    'duplicate_prevention'
                ]
            }
        except Exception as e:
            logging.error(f"获取状态失败: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def get_unfinished_images(self) -> List[Dict[str, Any]]:
        """获取未完成的图片列表"""
        try:
            # 加载向量数据库
            if not self.vector_store_manager.load():
                logging.warning("无法加载向量数据库")
                return []
            
            # 获取未完成图片
            return self.vector_store_manager.get_unfinished_images()
            
        except Exception as e:
            logging.error(f"获取未完成图片失败: {e}")
            return []
    
    def run(self):
        """运行补做程序"""
        print("🚀 V3版本图片补做程序启动")
        print("="*50)
        
        try:
            # 1. 加载向量数据库
            print("📚 加载向量数据库...")
            if not self.vector_store_manager.load():
                print("❌ 无法加载向量数据库")
                return
            
            # 2. 自动发现未完成的图片
            print("🔍 自动发现未完成的图片...")
            unfinished_images = self.vector_store_manager.get_unfinished_images()
            
            if not unfinished_images:
                print("🎉 所有图片都已处理完成！")
                return
            
            print(f" 发现 {len(unfinished_images)} 张未完成的图片")
            
            # 3. 分类显示
            needs_enhancement = [img for img in unfinished_images if img['needs_enhancement']]
            needs_vectorization = [img for img in unfinished_images if img['needs_vectorization']]
            
            print(f"\n📋 状态摘要:")
            print(f"   🔄 需要增强: {len(needs_enhancement)} 张")
            print(f"   🔤 需要向量化: {len(needs_vectorization)} 张")
            
            # 4. 用户确认
            if not self._get_user_confirmation(needs_enhancement, needs_vectorization):
                print("❌ 用户取消操作")
                return
            
            # 5. 执行补做（按逻辑顺序）
            if needs_enhancement:
                print(f"\n 开始批量增强 {len(needs_enhancement)} 张图片...")
                enhanced_results = self._enhance_images(needs_enhancement)
                print(f"✅ 增强完成: {len(enhanced_results)} 张")
                
                # 增强完成后，重新查询状态，找出新需要向量化的图片
                print("🔍 重新查询状态，找出需要向量化的图片...")
                self.vector_store_manager.load()  # 重新加载以获取最新状态
                updated_unfinished = self.vector_store_manager.get_unfinished_images()
                newly_ready_for_vectorization = [img for img in updated_unfinished 
                                               if not img['needs_enhancement'] and img['needs_vectorization']]
                
                if newly_ready_for_vectorization:
                    print(f" 发现 {len(newly_ready_for_vectorization)} 张新增强完成的图片需要向量化")
                    needs_vectorization = newly_ready_for_vectorization
                else:
                    needs_vectorization = []
            
            # 6. 向量化（只对已增强的，智能检测是否需要）
            if needs_vectorization:
                print(f"\n 智能检测需要向量化的图片...")
                actually_needs_vectorization = self._get_images_needing_vectorization(needs_vectorization)
                
                if actually_needs_vectorization:
                    print(f" 开始批量向量化 {len(actually_needs_vectorization)} 张图片...")
                    vectorized_results = self._vectorize_images(actually_needs_vectorization)
                    print(f"✅ 向量化完成: {len(vectorized_results)} 张")
                else:
                    print("🎉 所有图片都无需重新向量化！")
            
            print("\n🎉 补做程序执行完成！")
            
        except Exception as e:
            logging.error(f"补做程序执行失败: {e}")
            print(f"❌ 程序执行失败: {e}")
            import traceback
            traceback.print_exc()
    
    def run_completion_check(self):
        """运行补做检查（只检查，不执行，需要用户确认）"""
        print("🔍 V3版本图片补做检查")
        print("="*50)
        
        try:
            # 1. 加载向量数据库
            print("📚 加载向量数据库...")
            if not self.vector_store_manager.load():
                print("❌ 无法加载向量数据库")
                return
            
            # 2. 自动发现未完成的图片
            print("🔍 自动发现未完成的图片...")
            unfinished_images = self.vector_store_manager.get_unfinished_images()
            
            if not unfinished_images:
                print("🎉 所有图片都已处理完成！")
                return
            
            print(f" 发现 {len(unfinished_images)} 张未完成的图片")
            
            # 3. 分类显示
            needs_enhancement = [img for img in unfinished_images if img['needs_enhancement']]
            needs_vectorization = [img for img in unfinished_images if img['needs_vectorization']]
            
            print(f"\n📋 状态摘要:")
            print(f"   🔄 需要增强: {len(needs_enhancement)} 张")
            print(f"   🔤 需要向量化: {len(needs_vectorization)} 张")
            
            # 4. 显示详细信息
            if needs_enhancement:
                print(f"\n📷 需要增强的图片:")
                for i, img in enumerate(needs_enhancement[:5]):  # 只显示前5张
                    print(f"   {i+1}. {img.get('image_id', 'N/A')} - {img.get('document_name', 'N/A')}")
                if len(needs_enhancement) > 5:
                    print(f"   ... 还有 {len(needs_enhancement) - 5} 张")
            
            if needs_vectorization:
                print(f"\n🔤 需要向量化的图片:")
                for i, img in enumerate(needs_vectorization[:5]):  # 只显示前5张
                    print(f"   {i+1}. {img.get('image_id', 'N/A')} - {img.get('document_name', 'N/A')}")
                if len(needs_vectorization) > 5:
                    print(f"   ... 还有 {len(needs_vectorization) - 5} 张")
            
            # 5. 询问是否执行补做
            print(f"\n🔧 补做选项:")
            print("  注意：补做操作将修改数据库内容，请确认后再执行")
            
            if needs_enhancement or needs_vectorization:
                choice = input("是否执行补做操作？(y/N): ").strip().lower()
                if choice in ['y', 'yes', '是']:
                    print("🚀 开始执行补做操作...")
                    self.run()  # 调用完整的补做程序
                else:
                    print("❌ 用户取消补做操作")
            else:
                print("🎉 无需补做操作")
            
        except Exception as e:
            logging.error(f"补做检查失败: {e}")
            print(f"❌ 补做检查失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _get_user_confirmation(self, needs_enhancement: List, needs_vectorization: List) -> bool:
        """获取用户确认"""
        print(f"\n🔧 补做选项:")
        
        choices = {'enhance': False, 'vectorize': False}
        
        if needs_enhancement:
            enhance_choice = input(f"是否补做 {len(needs_enhancement)} 张图片的增强处理？(y/N): ").strip().lower()
            choices['enhance'] = enhance_choice in ['y', 'yes', '是']
        
        if needs_vectorization:
            vectorize_choice = input(f"是否补做 {len(needs_vectorization)} 张图片的向量化？(y/N): ").strip().lower()
            choices['vectorize'] = vectorize_choice in ['y', 'yes', '是']
        
        if not choices['enhance'] and not choices['vectorize']:
            print("❌ 未选择任何操作")
            return False
        
        print(f"✅ 用户选择: 增强={choices['enhance']}, 向量化={choices['vectorize']}")
        return True
    
    def _should_revectorize(self, image: Dict[str, Any]) -> bool:
        """
        智能判断是否需要重新向量化（基于现有字段）
        """
        try:
            metadata = image['metadata']
            
            # 检查是否有现有的向量
            has_existing_vectors = (metadata.get('image_embedding') and 
                                   metadata.get('description_embedding'))
            
            if not has_existing_vectors:
                return True  # 没有向量，需要向量化
            
            # 检查向量化时间戳是否晚于增强时间戳
            enhancement_timestamp = metadata.get('enhancement_timestamp', 0)
            vectorization_timestamp = metadata.get('vectorization_timestamp', 0)
            
            if enhancement_timestamp > vectorization_timestamp:
                print(f"🔄 图片 {image['image_id']} 增强时间晚于向量化时间，需要重新向量化")
                return True
            
            # 检查增强描述是否为空或无效
            enhanced_description = metadata.get('enhanced_description', '')
            if not enhanced_description or enhanced_description.strip() == '':
                print(f"⚠️ 图片 {image['image_id']} 增强描述为空，需要先增强，跳过向量化")
                return False  # 不需要向量化，因为需要先增强
            
            # 其他情况不需要重新向量化
            return False
            
        except Exception as e:
            logging.error(f"判断是否需要重新向量化失败: {e}")
            return True  # 出错时保守处理，重新向量化
    
    def _get_images_needing_vectorization(self, images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        获取真正需要向量化的图片（智能过滤）
        """
        needs_vectorization = []
        
        for img in images:
            if self._should_revectorize(img):
                needs_vectorization.append(img)
            else:
                print(f"⏭️ 图片 {img['image_id']} 无需重新向量化")
        
        return needs_vectorization
    
    def _enhance_images(self, images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """增强图片"""
        try:
            # 准备图片信息
            images_for_enhancement = []
            for img in images:
                image_info = {
                    'img_path': img['image_path'],
                    'img_caption': [img['document_name']],
                    'img_footnote': []
                }
                images_for_enhancement.append(image_info)
            
            # 批量增强
            return self.image_enhancer.enhance_images_batch(images_for_enhancement)
            
        except Exception as e:
            logging.error(f"增强图片失败: {e}")
            print(f"❌ 增强失败: {e}")
            return []
    
    def _vectorize_images(self, images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """向量化图片的增强描述文本（只对已增强的）"""
        try:
            # 准备图片信息
            images_for_vectorization = []
            for img in images:
                # 再次确认图片已增强
                if not img['metadata'].get('enhanced_description'):
                    print(f"⚠️ 图片 {img['image_id']} 缺少增强描述，跳过向量化")
                    continue
                
                image_info = {
                    'final_image_path': img['image_path'],
                    'enhanced_description': img['metadata'].get('enhanced_description', ''),
                    'image_id': img['image_id'],
                    'document_name': img['document_name']
                }
                images_for_vectorization.append(image_info)
            
            if not images_for_vectorization:
                print("没有可向量化的图片")
                return []
            
            # 对增强描述进行文本向量化，不是图片向量化
            # 因为图片本身的向量化在主流程中已经完成
            texts = [img['enhanced_description'] for img in images_for_vectorization]
            metadatas = [img['metadata'] for img in images_for_vectorization]
            
            # 调用文本向量化器，不是图片向量化器
            from vectorization.text_vectorizer import LangChainTextVectorizer as TextVectorizer
            text_vectorizer = TextVectorizer(self.config_manager)
            return text_vectorizer.vectorize_batch(texts, metadatas)
            
        except Exception as e:
            logging.error(f"向量化图片失败: {e}")
            print(f"❌ 向量化失败: {e}")
            return []

def main():
    """主函数"""
    try:
        tool = ImageCompletion()
        tool.run()
    except Exception as e:
        print(f"❌ 程序启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
