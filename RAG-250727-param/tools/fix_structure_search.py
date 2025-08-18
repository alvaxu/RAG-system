#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
程序说明：
## 1. 修复TableEngine中结构搜索的评分算法问题
## 2. 降低评分门槛，提高召回率
## 3. 优化评分权重分配
'''

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def fix_structure_search():
    """修复结构搜索的评分算法"""
    print("=" * 60)
    print("修复TableEngine中结构搜索的评分算法问题")
    print("=" * 60)
    
    try:
        # 读取TableEngine文件
        table_engine_path = "v2/core/table_engine.py"
        print(f"🔍 读取文件: {table_engine_path}")
        
        with open(table_engine_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("✅ 文件读取成功")
        
        # 修复1：降低结构搜索阈值
        print("\n🔧 修复1：降低结构搜索阈值...")
        old_threshold = "structure_threshold = layer_config.get('structure_threshold', 0.4)"
        new_threshold = "structure_threshold = layer_config.get('structure_threshold', 0.1)"  # 从0.4降到0.1
        
        if old_threshold in content:
            content = content.replace(old_threshold, new_threshold)
            print("✅ 结构搜索阈值已从0.4降低到0.1")
        else:
            print("⚠️ 未找到结构搜索阈值配置")
        
        # 修复2：优化评分权重
        print("\n🔧 修复2：优化评分权重...")
        
        # 降低列名匹配权重，提高其他匹配权重
        old_weights = [
            ("score += 0.8", "score += 0.6"),  # 表格类型匹配
            ("score += 0.7", "score += 0.5"),  # 业务领域匹配
            ("score += 0.6", "score += 0.4"),  # 主要用途匹配
            ("score += 0.9", "score += 0.8"),  # 列名精确匹配
            ("score += 0.7", "score += 0.6"),  # 列名部分匹配
        ]
        
        for old_weight, new_weight in old_weights:
            if old_weight in content:
                content = content.replace(old_weight, new_weight)
                print(f"✅ 权重调整: {old_weight} -> {new_weight}")
        
        # 修复3：添加基础分数
        print("\n🔧 修复3：添加基础分数...")
        
        # 在评分计算开始处添加基础分数
        old_score_init = "score = 0.0"
        new_score_init = "score = 0.3  # 基础分数，提高召回率"
        
        if old_score_init in content:
            content = content.replace(old_score_init, new_score_init)
            print("✅ 添加基础分数0.3")
        
        # 修复4：优化质量分数权重
        print("\n🔧 修复4：优化质量分数权重...")
        old_quality_weight = "score += quality_score * 0.2"
        new_quality_weight = "score += quality_score * 0.3  # 提高质量分数权重"
        
        if old_quality_weight in content:
            content = content.replace(old_quality_weight, new_quality_weight)
            print("✅ 质量分数权重从0.2提高到0.3")
        
        # 保存修复后的文件
        print("\n💾 保存修复后的文件...")
        with open(table_engine_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 文件保存成功")
        
        # 验证修复
        print("\n🔍 验证修复结果...")
        with open(table_engine_path, 'r', encoding='utf-8') as f:
            new_content = f.read()
        
        # 检查关键修复是否生效
        checks = [
            ("structure_threshold = layer_config.get('structure_threshold', 0.1)", "阈值修复"),
            ("score = 0.3  # 基础分数", "基础分数修复"),
            ("score += quality_score * 0.3", "质量分数权重修复"),
        ]
        
        for check_text, check_name in checks:
            if check_text in new_content:
                print(f"✅ {check_name}验证成功")
            else:
                print(f"❌ {check_name}验证失败")
        
        print("\n🎉 结构搜索评分算法修复完成！")
        return True
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        import traceback
        print(f"详细错误信息: {traceback.format_exc()}")
        return False

def main():
    """主修复函数"""
    print("🚀 开始修复TableEngine结构搜索问题")
    
    success = fix_structure_search()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 修复成功！现在可以测试结构搜索的改进效果")
    else:
        print("❌ 修复失败，请检查问题")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
