#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG系统V3快速启动脚本
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

# 添加项目路径以导入PathManager
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'db_system'))
from config.path_manager import PathManager

def check_rag_installation():
    """检查RAG系统是否已安装"""
    try:
        import rag_system
        print("[成功] RAG系统V3已安装")
        return True
    except ImportError:
        print("[错误] RAG系统V3未安装，请先运行: pip install -e .")
        return False

def start_backend():
    """启动后端API服务"""
    print("[启动] RAG系统后端API服务...")
    
    try:
        # 设置启动参数
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "rag_system.api.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ]
        
        # 在Windows上创建新窗口运行后端服务
        if os.name == 'nt':
            # Windows: 创建新控制台窗口
            subprocess.Popen(
                cmd,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            # Linux/Mac: 后台运行
            subprocess.Popen(cmd)
        
        print("[成功] 后端API服务启动中...")
        print("📍 服务地址: http://localhost:8000")
        print("📖 API文档: http://localhost:8000/docs")
        print("💡 后端服务日志将在新窗口中显示")
        
        # 等待服务启动
        time.sleep(3)
        
        # 检查服务是否启动成功
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("[成功] 后端API服务启动成功！")
                return True
            else:
                print("⚠️ 后端API服务启动中，请稍等...")
                return True
        except requests.exceptions.RequestException:
            print("⚠️ 后端API服务启动中，请稍等...")
            return True
            
    except Exception as e:
        print(f"[错误] 后端API服务启动失败: {e}")
        return False

def start_frontend():
    """启动前端开发服务器"""
    print("🎨 启动RAG系统前端界面...")
    
    # 使用PathManager管理路径，设置正确的基础目录
    project_root = os.path.dirname(__file__)
    path_manager = PathManager(project_root)
    frontend_dir = path_manager.get_absolute_path("frontend")
    os.chdir(frontend_dir)
    
    try:
        # 检查package.json是否存在
        package_json_path = path_manager.join_paths(frontend_dir, "package.json")
        if not os.path.exists(package_json_path):
            print("[错误] 前端目录不存在package.json文件")
            return False
        
        # 检查npm是否可用
        try:
            # 在Windows上使用npm.cmd
            npm_cmd = "npm.cmd" if os.name == 'nt' else "npm"
            result = subprocess.run([npm_cmd, "--version"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                print("[错误] npm命令不可用")
                print("💡 请确保已安装Node.js和npm，并将其添加到系统PATH中")
                return False
            print(f"[成功] 检测到npm版本: {result.stdout.strip()}")
        except FileNotFoundError:
            print("[错误] 未找到npm命令")
            print("💡 请确保已安装Node.js和npm，并将其添加到系统PATH中")
            print("💡 或者手动运行: cd frontend && npm run dev")
            return False
        
        # 检查node_modules是否存在
        node_modules_path = path_manager.join_paths(frontend_dir, "node_modules")
        if not os.path.exists(node_modules_path):
            print("⚠️ 未找到node_modules目录，正在安装依赖...")
            try:
                install_result = subprocess.run([npm_cmd, "install"], 
                                              capture_output=True, text=True, timeout=300)
                if install_result.returncode != 0:
                    print(f"[错误] 依赖安装失败: {install_result.stderr}")
                    return False
                print("[成功] 依赖安装完成")
            except Exception as e:
                print(f"[错误] 依赖安装失败: {e}")
                return False
        
        # 启动前端开发服务器
        print("[启动] 启动前端开发服务器...")
        
        # 在Windows上创建新窗口运行前端服务
        if os.name == 'nt':
            # Windows: 创建新控制台窗口
            subprocess.Popen(
                [npm_cmd, "run", "dev"],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            # Linux/Mac: 后台运行
            subprocess.Popen([npm_cmd, "run", "dev"])
        
        print("[成功] 前端开发服务器启动中...")
        print("📍 前端地址: http://localhost:3000")
        print("💡 前端服务日志将在新窗口中显示")
        print("💡 如果浏览器没有自动打开，请手动访问: http://localhost:3000")
        
        return True
        
    except Exception as e:
        print(f"[错误] 前端启动失败: {e}")
        print("💡 请确保已安装Node.js和npm")
        print("💡 或者手动运行: cd frontend && npm run dev")
        return False

def run_backend_tests():
    """运行后端功能测试"""
    print("🧪 运行RAG系统后端功能测试...")
    
    # 使用PathManager管理路径，设置正确的基础目录
    project_root = os.path.dirname(__file__)
    path_manager = PathManager(project_root)
    tests_dir = path_manager.join_paths("rag_system", "tests")
    tests_abs_dir = path_manager.get_absolute_path(tests_dir)
    os.chdir(tests_abs_dir)
    
    try:
        # 设置环境变量以支持UTF-8编码
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        # 直接运行测试，不捕获输出（避免编码问题）
        print("正在运行后端功能测试，请稍等...")
        result = subprocess.run([sys.executable, "run_backend_tests.py"], 
                              env=env, timeout=300)
        
        # 根据退出码判断结果
        if result.returncode == 0:
            print("[成功] 所有后端功能测试通过！")
        else:
            print("⚠️ 部分后端功能测试失败")
            
    except subprocess.TimeoutExpired:
        print("[错误] 后端功能测试超时")
    except Exception as e:
        print(f"[错误] 后端功能测试运行失败: {e}")

def run_api_tests():
    """运行API接口测试"""
    print("🌐 运行RAG系统API接口测试...")
    
    # 使用PathManager管理路径，设置正确的基础目录
    project_root = os.path.dirname(__file__)
    path_manager = PathManager(project_root)
    tests_dir = path_manager.join_paths("rag_system", "tests")
    tests_abs_dir = path_manager.get_absolute_path(tests_dir)
    os.chdir(tests_abs_dir)
    
    try:
        # 设置环境变量以支持UTF-8编码
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        # 直接运行API测试，不捕获输出（避免编码问题）
        print("正在运行API接口测试，请稍等...")
        result = subprocess.run([sys.executable, "test_rag_api.py"], 
                              env=env, timeout=300)
        
        # 根据退出码判断结果
        if result.returncode == 0:
            print("[成功] 所有API接口测试通过！")
        else:
            print("⚠️ 部分API接口测试失败")
            
    except subprocess.TimeoutExpired:
        print("[错误] API接口测试超时")
    except Exception as e:
        print(f"[错误] API接口测试运行失败: {e}")
        print("💡 请确保 test_rag_api.py 文件存在于 rag_system/tests/ 目录")

def show_status():
    """显示系统状态"""
    print("\n" + "="*50)
    print("🎯 RAG系统V3状态")
    print("="*50)
    
    # 检查后端服务
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("[成功] 后端API服务: 运行中 (http://localhost:8000)")
        else:
            print("[错误] 后端API服务: 未运行")
    except:
        print("[错误] 后端API服务: 未运行")
    
    # 检查前端服务
    try:
        response = requests.get("http://localhost:3000", timeout=2)
        if response.status_code == 200:
            print("[成功] 前端界面: 运行中 (http://localhost:3000)")
        else:
            print("[错误] 前端界面: 未运行")
    except:
        print("[错误] 前端界面: 未运行")
    
    print("\n[指南] 使用指南:")
    print("• API文档: http://localhost:8000/docs")
    print("• 健康检查: http://localhost:8000/health")
    print("• 系统配置: http://localhost:8000/api/v3/rag/config")
    print("• 系统统计: http://localhost:8000/api/v3/rag/stats")

def main():
    """主函数"""
    print("RAG系统V3快速启动工具")
    print("="*50)
    
    # 检查安装
    if not check_rag_installation():
        return
    
    while True:
        print("\n请选择操作:")
        print("1. 启动后端API服务")
        print("2. 启动前端界面")
        print("3. 启动完整系统 (后端+前端)")
        print("4. 运行API接口测试")
        print("5. 运行后端功能测试")
        print("6. 查看系统状态")
        print("7. 退出")
        
        choice = input("\n请输入选择 (1-7): ").strip()
        
        if choice == "1":
            start_backend()
        elif choice == "2":
            start_frontend()
        elif choice == "3":
            start_backend()
            time.sleep(2)
            start_frontend()
        elif choice == "4":
            run_api_tests()
        elif choice == "5":
            run_backend_tests()
        elif choice == "6":
            show_status()
        elif choice == "7":
            print("👋 再见！")
            break
        else:
            print("[错误] 无效选择，请重新输入")

if __name__ == "__main__":
    main()
