#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语法检查脚本：验证image_engine.py的语法是否正确
"""

import os
import sys
import ast

def check_syntax(file_path):
    """检查Python文件的语法"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # 尝试解析AST
        ast.parse(source)
        print(f"✅ {file_path} 语法检查通过")
        return True
        
    except SyntaxError as e:
        print(f"❌ {file_path} 语法错误:")
        print(f"   行 {e.lineno}: {e.text}")
        print(f"   错误: {e.msg}")
        return False
        
    except Exception as e:
        print(f"❌ {file_path} 检查失败: {e}")
        return False

if __name__ == "__main__":
    # 检查image_engine.py
    image_engine_path = "v2/core/image_engine.py"
    
    if os.path.exists(image_engine_path):
        success = check_syntax(image_engine_path)
        if success:
            print("\n🎉 语法检查完成，image_engine.py 语法正确！")
        else:
            print("\n💥 语法检查失败，需要修复语法错误！")
    else:
        print(f"❌ 文件不存在: {image_engine_path}")
