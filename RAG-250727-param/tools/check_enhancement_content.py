'''
程序说明：
## 1. 检查数据库中图片的enhanced_description内容
## 2. 分析是否包含深度处理标记
## 3. 帮助诊断V502_image_enhancer_new.py报告0张已处理的问题
'''

import sys
import os
# 修复路径问题，添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
import logging
import json
from pathlib import Path

# 导入统一的API密钥管理模块
from config.api_key_manager import get_dashscope_api_key

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_vector_store(vector_db_path):
    """加载向量存储"""
    try:
        config = Settings.load_from_file('config.json')
        
        # 使用统一的API密钥管理模块获取API密钥
        config_key = config.dashscope_api_key
        api_key = get_dashscope_api_key(config_key)
        
        if not api_key:
            logger.warning("未找到有效的DashScope API密钥")
            return None
        
        # 初始化DashScope embeddings
        try:
            from config.settings import Settings
            config = Settings.load_from_file('../config.json')
            embedding_model = config.text_embedding_model
        except Exception as e:
            print(f"⚠️ 无法加载配置，使用默认embedding模型: {e}")
            embedding_model = 'text-embedding-v1'
        
        embeddings = DashScopeEmbeddings(dashscope_api_key=api_key, model=embedding_model)
        vector_store = FAISS.load_local(vector_db_path, embeddings, allow_dangerous_deserialization=True)
        logger.info(f"向量存储加载成功，包含 {len(vector_store.docstore._dict)} 个文档")
        return vector_store
    except Exception as e:
        logger.error(f"加载向量存储失败: {e}")
        return None

def check_enhancement_content(vector_store):
    """检查图片的增强描述内容"""
    print("🔍 检查图片增强描述内容...")
    print("="*80)
    
    # 从配置文件获取深度处理标记
    config = Settings.load_from_file('config.json')
    depth_markers = config.depth_processing_markers
    
    print(f"📋 配置的深度处理标记:")
    for i, marker in enumerate(depth_markers, 1):
        print(f"   {i}. {marker}")
    print()
    
    image_count = 0
    has_depth_markers_count = 0
    
    for doc_id, doc in vector_store.docstore._dict.items():
        metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
        
        if metadata.get('chunk_type') == 'image':
            image_count += 1
            enhanced_desc = metadata.get('enhanced_description', '')
            
            print(f"🖼️  图片 {image_count}:")
            print(f"   📄 文档: {metadata.get('document_name', '未知')}")
            print(f"   📖 页码: {metadata.get('page_number', '未知')}")
            print(f"   🆔 ID: {metadata.get('image_id', '未知')[:16]}...")
            print(f"   📝 增强描述长度: {len(enhanced_desc)} 字符")
            
            # 检查是否包含深度处理标记
            found_markers = []
            for marker in depth_markers:
                if marker in enhanced_desc:
                    found_markers.append(marker)
            
            if found_markers:
                has_depth_markers_count += 1
                print(f"   ✅ 包含深度标记: {', '.join(found_markers)}")
            else:
                print(f"   ❌ 未包含深度标记")
            
            # 显示增强描述的前100个字符
            if enhanced_desc:
                preview = enhanced_desc[:100] + "..." if len(enhanced_desc) > 100 else enhanced_desc
                print(f"   📄 描述预览: {preview}")
            else:
                print(f"   📄 描述预览: (空)")
            
            print("-" * 60)
    
    print("="*80)
    print("📊 统计结果:")
    print(f"   📸 总图片数: {image_count}")
    print(f"   ✅ 包含深度标记: {has_depth_markers_count}")
    print(f"   ❌ 未包含深度标记: {image_count - has_depth_markers_count}")
    
    if has_depth_markers_count == 0:
        print("\n⚠️  问题诊断:")
        print("   所有图片的enhanced_description都不包含深度处理标记")
        print("   这说明图片可能只是进行了基础的增强，而不是深度处理")
        print("   或者深度处理的标记与配置中的不匹配")
    
    return has_depth_markers_count > 0

def main():
    """主函数"""
    print("🔍 图片增强描述内容检查器")
    print("="*60)
    
    try:
        config = Settings.load_from_file('config.json')
        vector_db_path = config.vector_db_dir
        
        print(f"📁 向量数据库路径: {vector_db_path}")
        
        vector_store = load_vector_store(vector_db_path)
        if not vector_store:
            print("❌ 无法加载向量存储")
            return
        
        has_depth_content = check_enhancement_content(vector_store)
        
        if has_depth_content:
            print("\n✅ 发现包含深度处理标记的图片")
        else:
            print("\n❌ 没有发现包含深度处理标记的图片")
            print("   这解释了为什么V502_image_enhancer_new.py报告0张已处理")
        
        print("\n💡 建议:")
        print("   1. 检查图片是否真的进行了深度处理")
        print("   2. 确认深度处理标记是否与配置匹配")
        print("   3. 如果需要进行深度处理，运行V502_image_enhancer_new.py")
        
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        print(f"❌ 程序执行失败: {e}")

if __name__ == "__main__":
    main()
