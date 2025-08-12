'''
程序说明：
## 1. 查看向量数据库中图片的具体描述信息
## 2. 显示图片的元数据、增强描述、语义特征等详细信息
## 3. 支持按图片类型、文档名称等条件筛选
## 4. 提供友好的显示格式
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
        
        embeddings = DashScopeEmbeddings(dashscope_api_key=api_key, model="text-embedding-v1")
        vector_store = FAISS.load_local(vector_db_path, embeddings, allow_dangerous_deserialization=True)
        logger.info(f"向量存储加载成功，包含 {len(vector_store.docstore._dict)} 个文档")
        return vector_store
    except Exception as e:
        logger.error(f"加载向量存储失败: {e}")
        return None

def extract_image_descriptions(vector_store):
    """提取图片描述信息"""
    image_descriptions = []
    try:
        for doc_id, doc in vector_store.docstore._dict.items():
            metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
            if metadata.get('chunk_type') == 'image':
                image_info = {
                    'doc_id': doc_id,
                    'content': doc.page_content,
                    'metadata': metadata,
                    'image_id': metadata.get('image_id', 'unknown'),
                    'image_path': metadata.get('image_path', ''),
                    'document_name': metadata.get('document_name', '未知文档'),
                    'page_number': metadata.get('page_number', 1),
                    'img_caption': metadata.get('img_caption', []),
                    'img_footnote': metadata.get('img_footnote', []),
                    'enhanced_description': metadata.get('enhanced_description', ''),
                    'image_type': metadata.get('image_type', 'general'),
                    'semantic_features': metadata.get('semantic_features', {}),
                    'image_filename': metadata.get('image_filename', ''),
                    'extension': metadata.get('extension', ''),
                    'source_zip': metadata.get('source_zip', '')
                }
                image_descriptions.append(image_info)
        logger.info(f"提取了 {len(image_descriptions)} 张图片的描述信息")
        return image_descriptions
    except Exception as e:
        logger.error(f"提取图片描述失败: {e}")
        return []

def display_image_descriptions(image_descriptions, filter_type=None, filter_document=None):
    """显示图片描述信息"""
    print("="*80)
    print("🖼️  向量数据库中的图片描述信息")
    print("="*80)
    
    filtered_descriptions = image_descriptions
    
    if filter_type:
        filtered_descriptions = [desc for desc in filtered_descriptions if desc['image_type'] == filter_type]
        print(f"📊 筛选条件: 图片类型 = {filter_type}")
    
    if filter_document:
        filtered_descriptions = [desc for desc in filtered_descriptions if filter_document.lower() in desc['document_name'].lower()]
        print(f"📊 筛选条件: 文档名称包含 = {filter_document}")
    
    print(f"📊 找到 {len(filtered_descriptions)} 张图片")
    print("="*80)
    
    for i, desc in enumerate(filtered_descriptions, 1):
        print(f"\n🖼️  图片 {i}:")
        print(f"   📄 文档名称: {desc['document_name']}")
        print(f"   📖 页码: {desc['page_number']}")
        print(f"   🆔 图片ID: {desc['image_id']}")
        print(f"   📁 图片路径: {desc['image_path']}")
        print(f"   📝 文件名: {desc['image_filename']}")
        print(f"   🔧 扩展名: {desc['extension']}")
        print(f"   📦 来源: {desc['source_zip']}")
        print(f"   🏷️  图片类型: {desc['image_type']}")
        
        if desc['img_caption']:
            print(f"   📋 图片标题: {' | '.join(desc['img_caption'])}")
        
        if desc['img_footnote']:
            print(f"   📝 图片脚注: {' | '.join(desc['img_footnote'])}")
        
        if desc['enhanced_description']:
            print(f"   🎯 增强描述: {desc['enhanced_description']}")
        
        if desc['content']:
            print(f"   📄 原始内容: {desc['content']}")
        
        if desc['semantic_features']:
            print(f"   🧠 语义特征:")
            for key, value in desc['semantic_features'].items():
                if isinstance(value, float):
                    print(f"      {key}: {value:.4f}")
                else:
                    print(f"      {key}: {value}")
        
        print("-" * 60)

def show_statistics(image_descriptions):
    """显示统计信息"""
    print("\n" + "="*80)
    print("📊 图片信息统计")
    print("="*80)
    
    doc_stats = {}
    for desc in image_descriptions:
        doc_name = desc['document_name']
        doc_stats[doc_name] = doc_stats.get(doc_name, 0) + 1
    
    print("📄 按文档统计:")
    for doc_name, count in sorted(doc_stats.items()):
        print(f"   {doc_name}: {count} 张图片")
    
    type_stats = {}
    for desc in image_descriptions:
        img_type = desc['image_type']
        type_stats[img_type] = type_stats.get(img_type, 0) + 1
    
    print("\n🏷️  按图片类型统计:")
    for img_type, count in sorted(type_stats.items()):
        print(f"   {img_type}: {count} 张图片")
    
    ext_stats = {}
    for desc in image_descriptions:
        ext = desc['extension']
        if ext:
            ext_stats[ext] = ext_stats.get(ext, 0) + 1
    
    print("\n📁 按扩展名统计:")
    for ext, count in sorted(ext_stats.items()):
        print(f"   {ext}: {count} 张图片")
    
    with_caption = sum(1 for desc in image_descriptions if desc['img_caption'])
    with_footnote = sum(1 for desc in image_descriptions if desc['img_footnote'])
    
    print(f"\n📋 有图片标题: {with_caption} 张")
    print(f"📝 有图片脚注: {with_footnote} 张")
    print(f"🎯 有增强描述: {sum(1 for desc in image_descriptions if desc['enhanced_description'])} 张")

def save_descriptions_to_file(image_descriptions, output_file: str):
    """保存描述信息到文件"""
    try:
        serializable_descriptions = []
        for desc in image_descriptions:
            serializable_desc = {
                'doc_id': str(desc['doc_id']),
                'content': desc['content'],
                'image_id': desc['image_id'],
                'image_path': desc['image_path'],
                'document_name': desc['document_name'],
                'page_number': desc['page_number'],
                'img_caption': desc['img_caption'],
                'img_footnote': desc['img_footnote'],
                'enhanced_description': desc['enhanced_description'],
                'image_type': desc['image_type'],
                'semantic_features': desc['semantic_features'],
                'image_filename': desc['image_filename'],
                'extension': desc['extension'],
                'source_zip': desc['source_zip']
            }
            serializable_descriptions.append(serializable_desc)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_descriptions, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 描述信息已保存到: {output_file}")
        
    except Exception as e:
        logger.error(f"保存描述信息失败: {e}")

def main():
    """主函数"""
    print("🔍 向量数据库图片描述查看器")
    print("="*60)
    
    try:
        config = Settings.load_from_file('config.json')
        vector_db_path = config.vector_db_dir
        
        print(f"📁 向量数据库路径: {vector_db_path}")
        
        # 检查路径是否存在，如果不存在尝试其他可能的路径
        if not os.path.exists(vector_db_path):
            # 尝试其他可能的路径
            possible_paths = [
                "./central/vector_db",
                "./vector_db",
                "./central/vector_db_test",
                "./vector_db_test"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    vector_db_path = path
                    print(f"✅ 找到向量数据库路径: {vector_db_path}")
                    break
            else:
                print(f"❌ 向量数据库路径不存在，尝试过的路径:")
                for path in possible_paths:
                    print(f"   - {path}")
                return
        
        vector_store = load_vector_store(vector_db_path)
        if not vector_store:
            print("❌ 无法加载向量存储")
            return
        
        image_descriptions = extract_image_descriptions(vector_store)
        
        if not image_descriptions:
            print("❌ 没有找到图片信息")
            return
        
        show_statistics(image_descriptions)
        
        print("\n" + "="*60)
        print("🔍 筛选选项:")
        print("1. 显示所有图片")
        print("2. 按图片类型筛选")
        print("3. 按文档名称筛选")
        print("4. 组合筛选")
        
        choice = input("\n请选择筛选方式 (1-4): ").strip()
        
        filter_type = None
        filter_document = None
        
        if choice == "2":
            types = set(desc['image_type'] for desc in image_descriptions)
            print("\n可用的图片类型:")
            for t in sorted(types):
                print(f"   - {t}")
            filter_type = input("请输入图片类型: ").strip()
            
        elif choice == "3":
            docs = set(desc['document_name'] for desc in image_descriptions)
            print("\n可用的文档名称:")
            for doc in sorted(docs):
                print(f"   - {doc}")
            filter_document = input("请输入文档名称关键词: ").strip()
            
        elif choice == "4":
            types = set(desc['image_type'] for desc in image_descriptions)
            print("\n可用的图片类型:")
            for t in sorted(types):
                print(f"   - {t}")
            filter_type = input("请输入图片类型: ").strip()
            
            docs = set(desc['document_name'] for desc in image_descriptions)
            print("\n可用的文档名称:")
            for doc in sorted(docs):
                print(f"   - {doc}")
            filter_document = input("请输入文档名称关键词: ").strip()
        
        display_image_descriptions(image_descriptions, filter_type, filter_document)
        
        save_choice = input("\n是否保存描述信息到文件? (y/n): ").strip().lower()
        if save_choice == 'y':
            output_file = "image_descriptions.json"
            save_descriptions_to_file(image_descriptions, output_file)
        
        print("\n✅ 图片描述查看完成！")
        
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        print(f"❌ 程序执行失败: {e}")

if __name__ == "__main__":
    main()
