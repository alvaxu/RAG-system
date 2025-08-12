#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
程序说明：

## 1. V2系统快速测试脚本
## 2. 快速验证各个模块的基本功能
## 3. 提供详细的错误信息和修复建议
## 4. 支持单模块测试和批量测试
'''

import os
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_module_import(module_path: str, module_name: str) -> bool:
    """测试模块导入"""
    try:
        __import__(module_path)
        print(f"✅ {module_name} 模块导入成功")
        return True
    except ImportError as e:
        print(f"❌ {module_name} 模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"💥 {module_name} 模块导入异常: {e}")
        return False


def test_file_exists(file_path: str, description: str) -> bool:
    """测试文件是否存在"""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} (文件不存在)")
        return False


def test_stage_1_basic_modules():
    """第一阶段：基础模块测试"""
    print("\n🚀 第一阶段：基础模块测试")
    print("=" * 50)
    
    results = []
    
    # 1.1 API密钥管理模块
    results.append(test_module_import("config.api_key_manager", "API密钥管理"))
    
    # 1.2 真实LLM功能测试
    results.append(test_file_exists("tools/test_real_llm.py", "真实LLM测试脚本"))
    
    # 1.3 V2配置管理
    results.append(test_module_import("v2.config.v2_config", "V2配置管理"))
    
    return results


def test_stage_2_core_engines():
    """第二阶段：核心引擎测试"""
    print("\n🚀 第二阶段：核心引擎测试")
    print("=" * 50)
    
    results = []
    
    # 2.1 基础引擎
    results.append(test_module_import("v2.core.base_engine", "基础引擎"))
    results.append(test_module_import("v2.core.text_engine", "文本引擎"))
    results.append(test_module_import("v2.core.table_engine", "表格引擎"))
    results.append(test_module_import("v2.core.image_engine", "图像引擎"))
    
    # 2.2 DashScope引擎
    results.append(test_module_import("v2.core.dashscope_llm_engine", "DashScope LLM引擎"))
    results.append(test_module_import("v2.core.dashscope_reranking_engine", "DashScope重排序引擎"))
    
    # 2.3 智能过滤引擎
    results.append(test_module_import("v2.core.smart_filter_engine", "智能过滤引擎"))
    results.append(test_module_import("v2.core.source_filter_engine", "源过滤引擎"))
    
    return results


def test_stage_3_hybrid_engine():
    """第三阶段：混合引擎集成测试"""
    print("\n🚀 第三阶段：混合引擎集成测试")
    print("=" * 50)
    
    results = []
    
    # 3.1 混合引擎
    results.append(test_module_import("v2.core.hybrid_engine", "混合引擎"))
    
    # 3.2 V2主程序
    results.append(test_file_exists("V800_v2_main.py", "V2主程序"))
    
    return results


def test_stage_4_api_interface():
    """第四阶段：API接口测试"""
    print("\n🚀 第四阶段：API接口测试")
    print("=" * 50)
    
    results = []
    
    # 4.1 V2 API路由
    results.append(test_module_import("v2.api.v2_routes", "V2 API路由"))
    
    # 4.2 API配置文件
    results.append(test_file_exists("v2/api/v2_routes.py", "V2 API路由文件"))
    
    return results


def test_stage_5_frontend_integration():
    """第五阶段：前后端集成测试"""
    print("\n🚀 第五阶段：前后端集成测试")
    print("=" * 50)
    
    results = []
    
    # 5.1 前端文件
    results.append(test_file_exists("v2/web/v2_index.html", "V2前端页面"))
    results.append(test_file_exists("v2/web/__init__.py", "V2前端模块"))
    
    # 5.2 文档文件
    results.append(test_file_exists("v2/docs/README.md", "V2文档README"))
    results.append(test_file_exists("v2/docs/V200_architecture_design.md", "V2架构设计文档"))
    
    return results


def test_stage_6_performance():
    """第六阶段：性能测试"""
    print("\n🚀 第六阶段：性能测试")
    print("=" * 50)
    
    results = []
    
    # 6.1 模块导入性能
    start_time = time.time()
    try:
        import v2.core.base_engine
        import v2.config.v2_config
        import_time = time.time() - start_time
        
        if import_time < 2.0:
            print(f"✅ 模块导入性能良好: {import_time:.2f}秒")
            results.append(True)
        else:
            print(f"⚠️ 模块导入较慢: {import_time:.2f}秒")
            results.append(False)
    except Exception as e:
        print(f"❌ 模块导入性能测试失败: {e}")
        results.append(False)
    
    # 6.2 内存使用测试
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        
        if memory_mb < 100:
            print(f"✅ 内存使用正常: {memory_mb:.1f}MB")
            results.append(True)
        else:
            print(f"⚠️ 内存使用较高: {memory_mb:.1f}MB")
            results.append(False)
    except ImportError:
        print("⚠️ 未安装psutil，跳过内存测试")
        results.append(None)
    
    return results


def run_quick_test():
    """运行快速测试"""
    print("🧪 V2系统快速测试")
    print("=" * 50)
    
    start_time = time.time()
    all_results = []
    
    # 执行各个阶段的测试
    all_results.extend(test_stage_1_basic_modules())
    all_results.extend(test_stage_2_core_engines())
    all_results.extend(test_stage_3_hybrid_engine())
    all_results.extend(test_stage_4_api_interface())
    all_results.extend(test_stage_5_frontend_integration())
    all_results.extend(test_stage_6_performance())
    
    end_time = time.time()
    
    # 统计结果
    total_tests = len(all_results)
    passed_tests = sum(1 for result in all_results if result is True)
    failed_tests = sum(1 for result in all_results if result is False)
    skipped_tests = sum(1 for result in all_results if result is None)
    
    print("\n" + "=" * 50)
    print("📊 快速测试结果")
    print("=" * 50)
    print(f"总测试数: {total_tests}")
    print(f"通过: {passed_tests}")
    print(f"失败: {failed_tests}")
    print(f"跳过: {skipped_tests}")
    print(f"通过率: {passed_tests/total_tests*100:.1f}%")
    print(f"测试耗时: {end_time - start_time:.2f}秒")
    
    if passed_tests/total_tests >= 0.9:
        print("\n🎉 测试结果优秀！系统运行良好！")
    elif passed_tests/total_tests >= 0.7:
        print("\n⚠️ 测试结果良好，但有一些问题需要关注")
    else:
        print("\n🚨 测试结果不理想，需要重点修复问题")
    
    return all_results


def main():
    """主函数"""
    if len(sys.argv) > 1:
        stage = sys.argv[1].lower()
        
        if stage == "stage1":
            test_stage_1_basic_modules()
        elif stage == "stage2":
            test_stage_2_core_engines()
        elif stage == "stage3":
            test_stage_3_hybrid_engine()
        elif stage == "stage4":
            test_stage_4_api_interface()
        elif stage == "stage5":
            test_stage_5_frontend_integration()
        elif stage == "stage6":
            test_stage_6_performance()
        else:
            print("❌ 无效的阶段参数")
            print("可用参数: stage1, stage2, stage3, stage4, stage5, stage6")
            return
    else:
        # 运行完整快速测试
        run_quick_test()


if __name__ == "__main__":
    main()
