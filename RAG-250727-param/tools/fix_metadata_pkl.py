#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复metadata.pkl文件

功能说明：
1. 从index.pkl中提取所有文档的元数据
2. 重新生成正确的metadata.pkl文件
3. 确保FAISS能正常工作
"""

import os
import sys
import pickle
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def fix_metadata_pkl():
    """修复metadata.pkl文件"""
    vector_db_path = "central/vector_db"
    index_pkl_path = os.path.join(vector_db_path, "index.pkl")
    metadata_pkl_path = os.path.join(vector_db_path, "metadata.pkl")
    
    print("🔧 开始修复metadata.pkl文件...")
    
    # 1. 检查文件是否存在
    if not os.path.exists(index_pkl_path):
        print(f"❌ index.pkl文件不存在: {index_pkl_path}")
        return False
    
    if not os.path.exists(metadata_pkl_path):
        print(f"⚠️ metadata.pkl文件不存在，将创建新文件")
    
    try:
        # 2. 加载index.pkl
        print("📖 正在加载index.pkl...")
        with open(index_pkl_path, 'rb') as f:
            index_data = pickle.load(f)
        
        # index.pkl是一个tuple: (docstore, metadata_dict)
        if isinstance(index_data, tuple) and len(index_data) == 2:
            docstore = index_data[0]  # InMemoryDocstore
            metadata_dict = index_data[1]  # 字典
            print(f"✅ 成功加载index.pkl，包含docstore和metadata_dict")
        else:
            print(f"❌ index.pkl格式不正确: {type(index_data)}")
            return False
        
        print(f"✅ 成功加载docstore，包含 {len(docstore._dict)} 个文档")
        print(f"✅ metadata_dict包含 {len(metadata_dict)} 个键")
        
        # 3. 提取所有元数据
        print("🔍 正在提取所有文档的元数据...")
        all_metadata = []
        
        for doc_id, doc in docstore._dict.items():
            if hasattr(doc, 'metadata') and doc.metadata:
                # 复制元数据，添加文档ID
                metadata = doc.metadata.copy()
                metadata['doc_id'] = doc_id
                all_metadata.append(metadata)
            else:
                print(f"⚠️ 文档 {doc_id} 没有元数据")
        
        print(f"✅ 成功提取 {len(all_metadata)} 个文档的元数据")
        
        # 4. 备份原metadata.pkl
        if os.path.exists(metadata_pkl_path):
            backup_path = metadata_pkl_path + ".backup"
            print(f"💾 备份原metadata.pkl到: {backup_path}")
            os.rename(metadata_pkl_path, backup_path)
        
        # 5. 保存新的metadata.pkl
        print("💾 正在保存新的metadata.pkl...")
        with open(metadata_pkl_path, 'wb') as f:
            pickle.dump(all_metadata, f)
        
        print(f"✅ 成功保存metadata.pkl，包含 {len(all_metadata)} 个文档的元数据")
        
        # 6. 验证保存结果
        print("🔍 验证保存结果...")
        with open(metadata_pkl_path, 'rb') as f:
            saved_metadata = pickle.load(f)
        
        print(f"✅ 验证成功: 保存了 {len(saved_metadata)} 个元数据")
        
        # 7. 显示元数据统计
        chunk_types = {}
        for metadata in saved_metadata:
            chunk_type = metadata.get('chunk_type', 'unknown')
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
        
        print("\n📊 元数据统计:")
        for chunk_type, count in sorted(chunk_types.items()):
            print(f"   {chunk_type}: {count} 个")
        
        return True
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 metadata.pkl修复工具启动")
    print("="*50)
    
    success = fix_metadata_pkl()
    
    if success:
        print("\n🎉 metadata.pkl修复完成！")
        print("现在FAISS应该能正常工作了。")
    else:
        print("\n❌ metadata.pkl修复失败！")
        print("请检查错误信息并手动修复。")

if __name__ == "__main__":
    main()
