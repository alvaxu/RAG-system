#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查vector_db文件结构
"""

import pickle
import os
from pathlib import Path

def check_vector_db_files():
    """检查vector_db中的文件"""
    vector_db_path = Path('central/vector_db')
    
    print(f"📁 检查目录: {vector_db_path.absolute()}")
    print(f"目录存在: {vector_db_path.exists()}")
    
    if not vector_db_path.exists():
        return
    
    files = list(vector_db_path.glob('*'))
    print(f"文件数量: {len(files)}")
    
    for file_path in files:
        print(f"\n📄 文件: {file_path.name}")
        print(f"  大小: {file_path.stat().st_size} bytes")
        
        if file_path.suffix == '.pkl':
            try:
                with open(file_path, 'rb') as f:
                    data = pickle.load(f)
                
                print(f"  类型: {type(data)}")
                print(f"  长度: {len(data) if hasattr(data, '__len__') else 'No length'}")
                
                if hasattr(data, '__len__') and len(data) > 0:
                    if isinstance(data, list):
                        print(f"  第一个元素类型: {type(data[0])}")
                        if isinstance(data[0], dict):
                            print(f"  第一个元素键: {list(data[0].keys())}")
                    elif isinstance(data, dict):
                        print(f"  键: {list(data.keys())}")
                        
            except Exception as e:
                print(f"  读取失败: {e}")
        
        elif file_path.suffix == '.faiss':
            print(f"  FAISS索引文件")

if __name__ == "__main__":
    check_vector_db_files()
