'''
程序说明：

## 1. 修复图片字段名不匹配问题
## 2. 将JSON中的image_caption和image_footnote正确映射到img_caption和img_footnote
## 3. 重新生成向量数据库以包含正确的图片标题和脚注信息
'''

import pickle
import os
import sys
import json
from pathlib import Path
from collections import defaultdict

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from config.settings import Settings

def fix_image_field_mapping():
    """修复图片字段名不匹配问题"""
    
    print("🔧 修复图片字段名不匹配问题")
    print("=" * 80)
    
    try:
        # 加载配置
        config = Settings.load_from_file('config.json')
        embeddings = DashScopeEmbeddings(dashscope_api_key=config.dashscope_api_key, model="text-embedding-v1")
        
        # 加载向量数据库
        vector_db_path = "./central/vector_db"
        vector_store = FAISS.load_local(vector_db_path, embeddings, allow_dangerous_deserialization=True)
        
        print(f"✅ 向量数据库加载成功")
        print(f"📊 总文档数: {len(vector_store.docstore._dict)}")
        
        # 分析当前图片文档的字段情况
        image_docs = []
        for doc_id, doc in vector_store.docstore._dict.items():
            metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
            if metadata.get('chunk_type') == 'image':
                image_docs.append((doc_id, doc))
        
        print(f"🖼️ 发现 {len(image_docs)} 个图片文档")
        
        # 检查字段映射问题
        print(f"\n🔍 检查字段映射问题:")
        print("-" * 60)
        
        field_mapping_issues = []
        for doc_id, doc in image_docs:
            metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
            
            # 检查当前字段
            current_img_caption = metadata.get('img_caption', [])
            current_img_footnote = metadata.get('img_footnote', [])
            
            # 检查是否为空
            if not current_img_caption and not current_img_footnote:
                field_mapping_issues.append((doc_id, doc))
        
        print(f"❌ 发现 {len(field_mapping_issues)} 个图片文档存在字段映射问题")
        
        if not field_mapping_issues:
            print(f"✅ 所有图片文档的字段映射都正确")
            return
        
        # 从JSON文件中重新提取正确的字段信息
        print(f"\n🔧 从JSON文件中重新提取字段信息:")
        print("-" * 60)
        
        # 获取所有JSON文件
        json_dir = Path("./document/md")
        json_files = list(json_dir.glob("*_1.json"))
        
        print(f"📁 发现 {len(json_files)} 个JSON文件")
        
        # 构建图片ID到字段信息的映射
        image_field_mapping = {}
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                doc_name = json_file.stem.replace('_1', '')
                
                for item in json_data:
                    if item.get("type") == "image":
                        img_path = item.get("img_path", "")
                        if img_path:
                            # 提取图片文件名（去掉images/前缀）
                            img_filename = Path(img_path).name
                            
                            # 获取正确的字段名
                            image_caption = item.get("image_caption", [])  # JSON中的字段名
                            image_footnote = item.get("image_footnote", [])  # JSON中的字段名
                            
                            # 映射到正确的字段名
                            img_caption = image_caption  # 映射到img_caption
                            img_footnote = image_footnote  # 映射到img_footnote
                            
                            image_field_mapping[img_filename] = {
                                'img_caption': img_caption,
                                'img_footnote': img_footnote,
                                'document_name': doc_name
                            }
                            
                            print(f"  📄 {img_filename}: caption={len(img_caption)}, footnote={len(img_footnote)}")
                
            except Exception as e:
                print(f"❌ 处理JSON文件失败 {json_file}: {e}")
        
        print(f"✅ 从JSON文件中提取了 {len(image_field_mapping)} 个图片的字段信息")
        
        # 修复向量数据库中的字段
        print(f"\n🔧 修复向量数据库中的字段:")
        print("-" * 60)
        
        fixed_count = 0
        for doc_id, doc in field_mapping_issues:
            metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
            
            # 获取图片文件名
            image_filename = metadata.get('image_filename', '')
            if not image_filename:
                continue
            
            # 查找对应的字段信息
            if image_filename in image_field_mapping:
                field_info = image_field_mapping[image_filename]
                
                # 更新元数据
                metadata['img_caption'] = field_info['img_caption']
                metadata['img_footnote'] = field_info['img_footnote']
                
                # 更新文档的元数据
                doc.metadata = metadata
                
                fixed_count += 1
                print(f"  ✅ 修复 {image_filename}: caption={len(field_info['img_caption'])}, footnote={len(field_info['img_footnote'])}")
            else:
                print(f"  ❌ 未找到 {image_filename} 的字段信息")
        
        print(f"✅ 修复了 {fixed_count} 个图片文档的字段")
        
        # 保存修复后的向量数据库
        if fixed_count > 0:
            print(f"\n💾 保存修复后的向量数据库:")
            print("-" * 60)
            
            # 备份原数据库
            backup_path = vector_db_path + "_backup"
            if os.path.exists(vector_db_path):
                import shutil
                shutil.copytree(vector_db_path, backup_path)
                print(f"📦 已备份原数据库到: {backup_path}")
            
            # 保存修复后的数据库
            vector_store.save_local(vector_db_path)
            print(f"✅ 已保存修复后的向量数据库")
        
        # 验证修复结果
        print(f"\n🔍 验证修复结果:")
        print("-" * 60)
        
        # 重新加载数据库验证
        vector_store_verify = FAISS.load_local(vector_db_path, embeddings, allow_dangerous_deserialization=True)
        
        image_docs_verify = []
        for doc_id, doc in vector_store_verify.docstore._dict.items():
            metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
            if metadata.get('chunk_type') == 'image':
                image_docs_verify.append((doc_id, doc))
        
        # 检查修复后的字段
        fixed_issues = 0
        for doc_id, doc in image_docs_verify:
            metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
            
            img_caption = metadata.get('img_caption', [])
            img_footnote = metadata.get('img_footnote', [])
            
            if img_caption or img_footnote:
                fixed_issues += 1
        
        print(f"✅ 验证结果: {fixed_issues}/{len(image_docs_verify)} 个图片文档字段已修复")
        
        # 总结
        print(f"\n📊 修复总结:")
        print("=" * 80)
        print(f"  总图片文档数: {len(image_docs)}")
        print(f"  需要修复的文档数: {len(field_mapping_issues)}")
        print(f"  成功修复的文档数: {fixed_count}")
        print(f"  验证修复成功的文档数: {fixed_issues}")
        
        if fixed_count > 0:
            print(f"\n🎉 字段映射问题修复完成！")
            print(f"现在图片文档的 img_caption 和 img_footnote 字段已正确填充")
        else:
            print(f"\n⚠️  未发现需要修复的字段映射问题")
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_image_field_mapping()
