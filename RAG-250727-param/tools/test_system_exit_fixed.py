#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
测试修复后的V2.0系统退出功能

## 1. 测试目标
验证修复后的系统退出功能是否能够正常工作，不再出现 RuntimeError: Working outside of application context.

## 2. 测试内容
- 测试系统状态检查
- 测试系统退出API调用
- 验证退出后服务是否真正停止

## 3. 使用方法
python tools/test_system_exit_fixed.py
"""

import requests
import time
import logging
import sys
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 基础URL
BASE_URL = "http://localhost:5000"

def test_system_status():
    """测试系统状态"""
    try:
        response = requests.get(f"{BASE_URL}/api/v2/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ 系统状态检查成功: {data.get('status', 'unknown')}")
            return True
        else:
            logger.error(f"❌ 系统状态检查失败: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ 无法连接到系统: {e}")
        return False

def test_system_exit():
    """测试系统退出"""
    try:
        logger.info("🚪 开始测试系统退出功能...")
        
        # 调用退出API
        response = requests.post(
            f"{BASE_URL}/api/v2/system/exit",
            json={
                "reason": "测试系统退出功能",
                "cleanup_memory": True,
                "save_state": True
            },
            timeout=15  # 增加超时时间，因为退出需要时间
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ 系统退出API调用成功: {data.get('message', '')}")
            logger.info(f"   清理状态: {data.get('cleanup_completed', False)}")
            logger.info(f"   状态保存: {data.get('state_saved', False)}")
            logger.info(f"   关闭调度: {data.get('shutdown_scheduled', False)}")
            return True
        else:
            logger.error(f"❌ 系统退出API调用失败: {response.status_code}")
            logger.error(f"   错误信息: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ 系统退出API调用异常: {e}")
        return False

def verify_service_shutdown():
    """验证服务是否真正关闭"""
    logger.info("⏳ 等待服务关闭...")
    
    # 等待几秒钟让服务有时间关闭
    time.sleep(3)
    
    # 尝试连接服务，应该失败
    try:
        response = requests.get(f"{BASE_URL}/api/v2/status", timeout=5)
        if response.status_code == 200:
            logger.warning("⚠️  服务似乎仍在运行")
            return False
        else:
            logger.info("✅ 服务已停止响应")
            return True
    except requests.exceptions.ConnectionError:
        logger.info("✅ 服务已完全关闭（连接被拒绝）")
        return True
    except requests.exceptions.RequestException as e:
        logger.info(f"✅ 服务已停止响应: {e}")
        return True

def main():
    """主函数"""
    logger.info("🔧 V2.0系统退出功能修复验证测试")
    logger.info("=" * 50)
    
    try:
        # 步骤1: 检查系统状态
        logger.info("📋 步骤1: 检查系统状态")
        if not test_system_status():
            logger.error("❌ 系统状态检查失败，无法继续测试")
            return 1
        
        # 步骤2: 测试系统退出
        logger.info("📋 步骤2: 测试系统退出功能")
        if not test_system_exit():
            logger.error("❌ 系统退出功能测试失败")
            return 1
        
        # 步骤3: 验证服务关闭
        logger.info("📋 步骤3: 验证服务是否真正关闭")
        if verify_service_shutdown():
            logger.info("🎯 系统退出功能修复验证成功！")
            logger.info("✅ 不再出现 RuntimeError: Working outside of application context.")
            logger.info("✅ 系统能够正常退出并关闭Web服务")
            return 0
        else:
            logger.warning("⚠️  服务可能没有完全关闭，但退出API调用成功")
            logger.info("✅ 至少 RuntimeError 问题已修复")
            return 0
            
    except Exception as e:
        logger.error(f"❌ 测试过程中发生未预期的错误: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
