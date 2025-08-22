#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证配置文件更新是否成功
"""

import os
import sys
import json

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def verify_config():
    """验证配置文件更新"""
    print("="*60)
    print("验证配置文件更新")
    print("="*60)
    
    try:
        # 1. 验证 v2_config.json
        print("\n1. 验证 v2_config.json...")
        v2_config_path = os.path.join(project_root, 'v2', 'config', 'v2_config.json')
        
        with open(v2_config_path, 'r', encoding='utf-8') as f:
            v2_config = json.load(f)
        
        image_engine_config = v2_config.get('image_engine', {})
        cross_modal_threshold = image_engine_config.get('cross_modal_similarity_threshold')
        semantic_threshold = image_engine_config.get('semantic_similarity_threshold')
        
        print(f"   策略1阈值 (semantic_similarity_threshold): {semantic_threshold}")
        print(f"   策略2阈值 (cross_modal_similarity_threshold): {cross_modal_threshold}")
        
        if cross_modal_threshold == 0.5:
            print("   ✅ 策略2阈值更新成功！")
        else:
            print("   ❌ 策略2阈值更新失败！")
        
        # 2. 验证 v2_config.py
        print("\n2. 验证 v2_config.py...")
        v2_config_py_path = os.path.join(project_root, 'v2', 'config', 'v2_config.py')
        
        with open(v2_config_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'cross_modal_similarity_threshold: float = 0.5' in content:
            print("   ✅ Python配置文件更新成功！")
        else:
            print("   ❌ Python配置文件更新失败！")
        
        # 3. 总结
        print("\n" + "="*60)
        print("配置验证总结")
        print("="*60)
        
        if cross_modal_threshold == 0.5:
            print("🎉 所有配置文件更新成功！")
            print(f"📊 当前阈值设置：")
            print(f"   策略1 (语义相似度): {semantic_threshold}")
            print(f"   策略2 (跨模态相似度): {cross_modal_threshold}")
            print("\n💡 建议：")
            print("   - 策略1阈值0.3：保证基本语义相关性")
            print("   - 策略2阈值0.5：提供高精度跨模态搜索")
        else:
            print("❌ 配置文件更新存在问题，请检查！")
        
        return True
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    verify_config()
