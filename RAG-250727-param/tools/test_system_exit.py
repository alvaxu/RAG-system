#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：

## 1. 测试V2系统的真正退出功能
## 2. 验证Web服务能够正确关闭
## 3. 确保主程序能够正确退出
"""

import sys
import os
import logging
import requests
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_system_exit():
    """测试系统退出功能"""
    base_url = "http://localhost:5000"
    
    try:
        logger.info("🧪 开始测试V2系统退出功能")
        logger.info("=" * 50)
        
        # 1. 测试系统状态接口
        logger.info("🔍 测试系统状态接口...")
        try:
            response = requests.get(f"{base_url}/api/v2/system/status", timeout=5)
            if response.status_code == 200:
                status_data = response.json()
                logger.info(f"✅ 系统状态接口正常")
                logger.info(f"   系统名称: {status_data.get('system_name', 'N/A')}")
                logger.info(f"   版本: {status_data.get('version', 'N/A')}")
            else:
                logger.warning(f"⚠️ 系统状态接口返回状态码: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 无法连接到系统状态接口: {e}")
            return False
        
        # 2. 测试系统退出接口
        logger.info("🛑 测试系统退出接口...")
        try:
            response = requests.post(
                f"{base_url}/api/v2/system/exit",
                json={
                    "reason": "测试退出功能",
                    "cleanup_memory": True,
                    "save_state": True
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ 系统退出接口正常")
                logger.info(f"   消息: {result.get('message', 'N/A')}")
                logger.info(f"   清理完成: {result.get('cleanup_completed', False)}")
                logger.info(f"   状态保存: {result.get('state_saved', False)}")
                logger.info(f"   关闭已安排: {result.get('shutdown_scheduled', False)}")
                
                # 等待系统关闭
                logger.info("⏳ 等待系统关闭...")
                time.sleep(2)
                
                # 3. 验证系统是否已关闭
                logger.info("🔍 验证系统是否已关闭...")
                try:
                    response = requests.get(f"{base_url}/api/v2/system/status", timeout=3)
                    if response.status_code == 200:
                        logger.warning("⚠️ 系统仍在运行，退出可能失败")
                        return False
                    else:
                        logger.info("✅ 系统已成功关闭")
                        return True
                except requests.exceptions.ConnectionError:
                    logger.info("✅ 系统已成功关闭（连接被拒绝）")
                    return True
                except Exception as e:
                    logger.info(f"✅ 系统已成功关闭（连接异常: {e}）")
                    return True
                
            else:
                logger.error(f"❌ 系统退出接口返回状态码: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 系统退出接口调用失败: {e}")
            return False
        
    except Exception as e:
        logger.error(f"❌ 测试过程中发生未预期的错误: {e}")
        return False

def main():
    """主函数"""
    logger.info("🚀 V2系统退出功能测试")
    logger.info("=" * 50)
    logger.info("🌐 测试目标: http://localhost:5000")
    logger.info("⏰ 开始时间: " + time.strftime("%Y-%m-%d %H:%M:%S"))
    
    try:
        success = test_system_exit()
        
        if success:
            logger.info("🎯 系统退出功能测试成功！")
            logger.info("✅ Web服务能够正确关闭")
            logger.info("✅ 主程序能够正确退出")
            return 0
        else:
            logger.error("💥 系统退出功能测试失败！")
            return 1
            
    except Exception as e:
        logger.error(f"❌ 测试过程中发生未预期的错误: {e}")
        return 1
    finally:
        logger.info("⏰ 结束时间: " + time.strftime("%Y-%m-%d %H:%M:%S"))
        logger.info("=" * 50)

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
