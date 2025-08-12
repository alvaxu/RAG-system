#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
程序说明：

## 1. V2系统完整测试计划执行器
## 2. 按阶段执行测试，自动生成测试报告
## 3. 支持单模块测试和完整系统测试
## 4. 提供详细的测试结果和错误信息
'''

import os
import sys
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestPlanExecutor:
    """测试计划执行器"""
    
    def __init__(self):
        """初始化测试执行器"""
        self.test_results = {}
        self.start_time = None
        self.end_time = None
        
    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def run_command(self, command: str, description: str) -> Tuple[bool, str]:
        """执行命令并返回结果"""
        self.log(f"执行: {description}")
        self.log(f"命令: {command}")
        
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=60
            )
            
            if result.returncode == 0:
                self.log(f"✅ {description} - 成功", "SUCCESS")
                return True, result.stdout
            else:
                self.log(f"❌ {description} - 失败", "ERROR")
                self.log(f"错误输出: {result.stderr}", "ERROR")
                return False, result.stderr
                
        except subprocess.TimeoutExpired:
            self.log(f"⏰ {description} - 超时", "WARNING")
            return False, "执行超时"
        except Exception as e:
            self.log(f"💥 {description} - 异常: {e}", "ERROR")
            return False, str(e)
    
    def test_stage_1_basic_modules(self) -> Dict[str, bool]:
        """第一阶段：基础模块测试"""
        self.log("🚀 开始第一阶段：基础模块测试", "STAGE")
        
        results = {}
        
        # 1.1 API密钥管理模块测试
        success, output = self.run_command(
            "python tools/test_api_key_manager.py",
            "API密钥管理模块测试"
        )
        results["api_key_manager"] = success
        
        # 1.2 真实LLM功能测试
        success, output = self.run_command(
            "python tools/test_real_llm.py",
            "真实LLM功能测试"
        )
        results["real_llm"] = success
        
        # 1.3 配置管理测试
        success, output = self.run_command(
            "python -c \"from v2.config.v2_config import V2ConfigManager; print('✅ V2配置模块导入成功')\"",
            "V2配置管理测试"
        )
        results["v2_config"] = success
        
        return results
    
    def test_stage_2_core_engines(self) -> Dict[str, bool]:
        """第二阶段：核心引擎测试"""
        self.log("🚀 开始第二阶段：核心引擎测试", "STAGE")
        
        results = {}
        
        # 2.1 基础引擎测试
        success, output = self.run_command(
            "python -c \"from v2.core.base_engine import BaseEngine; from v2.core.text_engine import TextEngine; from v2.core.table_engine import TableEngine; from v2.core.image_engine import ImageEngine; print('✅ 所有引擎模块导入成功')\"",
            "基础引擎模块导入测试"
        )
        results["base_engines"] = success
        
        # 2.2 DashScope引擎测试
        success, output = self.run_command(
            "python -c \"from v2.core.dashscope_llm_engine import DashScopeLLMEngine; from v2.core.dashscope_reranking_engine import DashScopeRerankingEngine; print('✅ DashScope引擎模块导入成功')\"",
            "DashScope引擎模块导入测试"
        )
        results["dashscope_engines"] = success
        
        # 2.3 智能过滤引擎测试
        success, output = self.run_command(
            "python -c \"from v2.core.smart_filter_engine import SmartFilterEngine; from v2.core.source_filter_engine import SourceFilterEngine; print('✅ 过滤引擎模块导入成功')\"",
            "智能过滤引擎模块导入测试"
        )
        results["filter_engines"] = success
        
        return results
    
    def test_stage_3_hybrid_engine(self) -> Dict[str, bool]:
        """第三阶段：混合引擎集成测试"""
        self.log("🚀 开始第三阶段：混合引擎集成测试", "STAGE")
        
        results = {}
        
        # 3.1 混合引擎测试
        success, output = self.run_command(
            "python -c \"from v2.core.hybrid_engine import HybridEngine; print('✅ 混合引擎模块导入成功')\"",
            "混合引擎模块导入测试"
        )
        results["hybrid_engine"] = success
        
        # 3.2 完整流程测试（如果有测试模式）
        if os.path.exists("V800_v2_main.py"):
            success, output = self.run_command(
                "python V800_v2_main.py --help",
                "V2主程序测试模式检查"
            )
            results["v2_main_program"] = success
        else:
            results["v2_main_program"] = False
            self.log("⚠️ V800_v2_main.py 文件不存在", "WARNING")
        
        return results
    
    def test_stage_4_api_interface(self) -> Dict[str, bool]:
        """第四阶段：API接口测试"""
        self.log("🚀 开始第四阶段：API接口测试", "STAGE")
        
        results = {}
        
        # 4.1 V2 API路由测试
        success, output = self.run_command(
            "python -c \"from v2.api.v2_routes import app; print('✅ V2 API应用创建成功')\"",
            "V2 API路由测试"
        )
        results["v2_api_routes"] = success
        
        # 4.2 API配置测试
        success, output = self.run_command(
            "python -c \"from v2.api.v2_routes import app; print('应用配置:', app.config.get('ENV', 'production'))\"",
            "API配置测试"
        )
        results["api_config"] = success
        
        return results
    
    def test_stage_5_frontend_integration(self) -> Dict[str, bool]:
        """第五阶段：前后端集成测试"""
        self.log("🚀 开始第五阶段：前后端集成测试", "STAGE")
        
        results = {}
        
        # 5.1 前端页面文件检查
        frontend_files = [
            "v2/web/v2_index.html",
            "v2/web/__init__.py"
        ]
        
        for file_path in frontend_files:
            if os.path.exists(file_path):
                self.log(f"✅ 前端文件存在: {file_path}", "SUCCESS")
                results[f"frontend_{Path(file_path).stem}"] = True
            else:
                self.log(f"❌ 前端文件不存在: {file_path}", "ERROR")
                results[f"frontend_{Path(file_path).stem}"] = False
        
        # 5.2 文档文件检查
        doc_files = [
            "v2/docs/README.md",
            "v2/docs/V200_architecture_design.md"
        ]
        
        for file_path in doc_files:
            if os.path.exists(file_path):
                self.log(f"✅ 文档文件存在: {file_path}", "SUCCESS")
                results[f"docs_{Path(file_path).stem}"] = True
            else:
                self.log(f"❌ 文档文件不存在: {file_path}", "ERROR")
                results[f"docs_{Path(file_path).stem}"] = False
        
        return results
    
    def test_stage_6_performance(self) -> Dict[str, bool]:
        """第六阶段：性能测试"""
        self.log("🚀 开始第六阶段：性能测试", "STAGE")
        
        results = {}
        
        # 6.1 模块导入性能测试
        start_time = time.time()
        try:
            import v2.core.base_engine
            import v2.core.hybrid_engine
            import v2.config.v2_config
            import_time = time.time() - start_time
            
            if import_time < 2.0:  # 2秒内导入成功
                self.log(f"✅ 模块导入性能良好: {import_time:.2f}秒", "SUCCESS")
                results["import_performance"] = True
            else:
                self.log(f"⚠️ 模块导入较慢: {import_time:.2f}秒", "WARNING")
                results["import_performance"] = False
        except Exception as e:
            self.log(f"❌ 模块导入失败: {e}", "ERROR")
            results["import_performance"] = False
        
        # 6.2 内存使用测试
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            if memory_mb < 100:  # 内存使用小于100MB
                self.log(f"✅ 内存使用正常: {memory_mb:.1f}MB", "SUCCESS")
                results["memory_usage"] = True
            else:
                self.log(f"⚠️ 内存使用较高: {memory_mb:.1f}MB", "WARNING")
                results["memory_usage"] = False
        except ImportError:
            self.log("⚠️ 未安装psutil，跳过内存测试", "WARNING")
            results["memory_usage"] = None
        
        return results
    
    def generate_test_report(self) -> str:
        """生成测试报告"""
        self.log("📊 生成测试报告", "REPORT")
        
        total_tests = 0
        passed_tests = 0
        
        report = []
        report.append("# 🧪 V2系统完整测试报告")
        report.append(f"**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**测试耗时**: {self.end_time - self.start_time:.2f}秒")
        report.append("")
        
        for stage_name, stage_results in self.test_results.items():
            report.append(f"## {stage_name}")
            report.append("")
            
            stage_total = len(stage_results)
            stage_passed = sum(1 for result in stage_results.values() if result)
            total_tests += stage_total
            passed_tests += stage_passed
            
            for test_name, test_result in stage_results.items():
                status = "✅ 通过" if test_result else "❌ 失败"
                report.append(f"- {test_name}: {status}")
            
            report.append(f"**通过率**: {stage_passed}/{stage_total} ({stage_passed/stage_total*100:.1f}%)")
            report.append("")
        
        # 总体统计
        overall_rate = passed_tests / total_tests * 100 if total_tests > 0 else 0
        report.append("## 📈 总体测试结果")
        report.append(f"**总测试数**: {total_tests}")
        report.append(f"**通过数**: {passed_tests}")
        report.append(f"**失败数**: {total_tests - passed_tests}")
        report.append(f"**总体通过率**: {overall_rate:.1f}%")
        
        if overall_rate >= 90:
            report.append("**🎉 测试结果优秀！系统运行良好！**")
        elif overall_rate >= 70:
            report.append("**⚠️ 测试结果良好，但有一些问题需要关注**")
        else:
            report.append("**🚨 测试结果不理想，需要重点修复问题**")
        
        return "\n".join(report)
    
    def run_full_test_plan(self):
        """运行完整测试计划"""
        self.log("🚀 开始执行V2系统完整测试计划", "START")
        self.start_time = time.time()
        
        # 执行各个阶段的测试
        self.test_results["第一阶段：基础模块测试"] = self.test_stage_1_basic_modules()
        self.test_results["第二阶段：核心引擎测试"] = self.test_stage_2_core_engines()
        self.test_results["第三阶段：混合引擎集成测试"] = self.test_stage_3_hybrid_engine()
        self.test_results["第四阶段：API接口测试"] = self.test_stage_4_api_interface()
        self.test_results["第五阶段：前后端集成测试"] = self.test_stage_5_frontend_integration()
        self.test_results["第六阶段：性能测试"] = self.test_stage_6_performance()
        
        self.end_time = time.time()
        
        # 生成测试报告
        report = self.generate_test_report()
        
        # 保存测试报告
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.log(f"📄 测试报告已保存到: {report_file}", "REPORT")
        
        # 打印测试报告
        print("\n" + "="*80)
        print(report)
        print("="*80)
        
        return report


def main():
    """主函数"""
    print("🧪 V2系统完整测试计划执行器")
    print("="*50)
    
    executor = TestPlanExecutor()
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        stage = sys.argv[1].lower()
        
        if stage == "stage1":
            results = executor.test_stage_1_basic_modules()
            print(f"第一阶段测试结果: {results}")
        elif stage == "stage2":
            results = executor.test_stage_2_core_engines()
            print(f"第二阶段测试结果: {results}")
        elif stage == "stage3":
            results = executor.test_stage_3_hybrid_engine()
            print(f"第三阶段测试结果: {results}")
        elif stage == "stage4":
            results = executor.test_stage_4_api_interface()
            print(f"第四阶段测试结果: {results}")
        elif stage == "stage5":
            results = executor.test_stage_5_frontend_integration()
            print(f"第五阶段测试结果: {results}")
        elif stage == "stage6":
            results = executor.test_stage_6_performance()
            print(f"第六阶段测试结果: {results}")
        else:
            print("❌ 无效的阶段参数")
            print("可用参数: stage1, stage2, stage3, stage4, stage5, stage6, full")
            return
    else:
        # 运行完整测试计划
        executor.run_full_test_plan()


if __name__ == "__main__":
    main()
