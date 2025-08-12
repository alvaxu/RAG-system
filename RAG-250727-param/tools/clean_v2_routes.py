#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理V2 API路由文件中的重复函数定义
"""

import re
import os

def clean_v2_routes():
    """清理v2_routes.py中的重复函数定义"""
    
    # 文件路径
    routes_file = 'v2/api/v2_routes.py'
    backup_file = 'v2/api/v2_routes_backup.py'
    
    if not os.path.exists(routes_file):
        print(f"错误：文件 {routes_file} 不存在")
        return False
    
    # 读取原文件
    with open(routes_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 创建备份
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"已创建备份文件：{backup_file}")
    
    # 分析文件结构，找到重复的函数
    lines = content.split('\n')
    
    # 找到所有函数定义的位置
    function_positions = {}
    current_function = None
    function_start = None
    
    for i, line in enumerate(lines):
        # 检查是否是函数定义
        if line.strip().startswith('def '):
            func_name = line.strip().split('(')[0].replace('def ', '')
            if func_name not in function_positions:
                function_positions[func_name] = []
            function_positions[func_name].append(i)
            
            # 如果这是第一个函数，记录开始位置
            if len(function_positions[func_name]) == 1:
                current_function = func_name
                function_start = i
            else:
                # 这是重复的函数，需要删除前面的版本
                print(f"发现重复函数：{func_name}")
                print(f"  第一个位置：{function_start}")
                print(f"  重复位置：{i}")
                
                # 找到第一个函数的结束位置（下一个函数定义之前）
                end_pos = i
                for j in range(function_start + 1, len(lines)):
                    if lines[j].strip().startswith('def ') or lines[j].strip().startswith('@v2_api_bp.route'):
                        if j < i:  # 确保是下一个函数，不是当前重复的函数
                            end_pos = j
                            break
                
                print(f"  第一个函数结束位置：{end_pos}")
                
                # 删除第一个函数（从开始到结束）
                if function_start is not None and end_pos > function_start:
                    # 删除从function_start到end_pos-1的行
                    del lines[function_start:end_pos]
                    print(f"  已删除第一个函数定义（行 {function_start} 到 {end_pos-1}）")
                    
                    # 更新行号
                    i -= (end_pos - function_start)
                
                # 重置位置
                function_start = i
                current_function = func_name
    
    # 写回清理后的内容
    cleaned_content = '\n'.join(lines)
    
    with open(routes_file, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)
    
    print(f"已清理文件：{routes_file}")
    print("重复函数定义已删除")
    
    return True

if __name__ == "__main__":
    print("开始清理V2 API路由文件...")
    if clean_v2_routes():
        print("清理完成！")
    else:
        print("清理失败！")
