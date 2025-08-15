'''
程序说明：

## 1. 测试V2系统退出功能
## 2. 验证优雅关闭流程
## 3. 测试内存清理和资源释放
## 4. 验证API接口的可用性
'''

import requests
import json
import time
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_system_status(base_url="http://localhost:5000"):
    """测试系统状态接口"""
    try:
        print("🔍 测试系统状态接口...")
        response = requests.get(f"{base_url}/api/v2/status")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 系统状态接口正常")
            print(f"   系统名称: {data.get('status', {}).get('system_name', 'N/A')}")
            print(f"   版本: {data.get('status', {}).get('version', 'N/A')}")
            print(f"   混合引擎: {'✅ 就绪' if data.get('status', {}).get('hybrid_engine_ready') else '❌ 未就绪'}")
            return True
        else:
            print(f"❌ 系统状态接口失败: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 系统状态接口异常: {e}")
        return False

def test_system_restart(base_url="http://localhost:5000"):
    """测试系统重启接口"""
    try:
        print("\n🔄 测试系统重启接口...")
        
        # 发送重启请求
        response = requests.post(f"{base_url}/api/v2/system/restart", 
                               json={
                                   "reason": "测试重启功能",
                                   "cleanup_before_restart": True
                               })
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 系统重启接口正常")
            print(f"   消息: {data.get('message', 'N/A')}")
            print(f"   清理完成: {data.get('cleanup_completed', False)}")
            return True
        else:
            print(f"❌ 系统重启接口失败: HTTP {response.status_code}")
            print(f"   响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 系统重启接口异常: {e}")
        return False

def test_system_shutdown(base_url="http://localhost:5000"):
    """测试系统关闭接口"""
    try:
        print("\n🛑 测试系统关闭接口...")
        
        # 发送关闭请求
        response = requests.post(f"{base_url}/api/v2/system/shutdown", 
                               json={
                                   "reason": "测试关闭功能",
                                   "cleanup_memory": True,
                                   "save_state": True
                               })
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 系统关闭接口正常")
            print(f"   消息: {data.get('message', 'N/A')}")
            print(f"   清理完成: {data.get('cleanup_completed', False)}")
            print(f"   状态保存: {data.get('state_saved', False)}")
            return True
        else:
            print(f"❌ 系统关闭接口失败: HTTP {response.status_code}")
            print(f"   响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 系统关闭接口异常: {e}")
        return False

def test_graceful_shutdown_flow(base_url="http://localhost:5000"):
    """测试完整的优雅关闭流程"""
    try:
        print("\n🎯 测试完整的优雅关闭流程...")
        
        # 1. 检查系统状态
        if not test_system_status(base_url):
            print("❌ 系统状态检查失败，无法继续测试")
            return False
        
        # 2. 等待一下
        print("⏳ 等待2秒...")
        time.sleep(2)
        
        # 3. 测试重启功能
        if not test_system_restart(base_url):
            print("⚠️ 系统重启功能测试失败")
        
        # 4. 等待一下
        print("⏳ 等待3秒...")
        time.sleep(3)
        
        # 5. 再次检查系统状态
        if not test_system_status(base_url):
            print("❌ 重启后系统状态检查失败")
            return False
        
        # 6. 测试关闭功能
        if not test_system_shutdown(base_url):
            print("❌ 系统关闭功能测试失败")
            return False
        
        print("\n✅ 优雅关闭流程测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ 优雅关闭流程测试异常: {e}")
        return False

def main():
    """主函数"""
    print("🚀 V2系统退出功能测试")
    print("=" * 50)
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:5000"
    
    print(f"🌐 测试目标: {base_url}")
    print(f"⏰ 开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 执行测试
        success = test_graceful_shutdown_flow(base_url)
        
        if success:
            print("\n🎉 所有测试通过！")
            print("\n💡 使用说明:")
            print("   1. 在Web页面中点击'退出服务'按钮可以优雅关闭系统")
            print("   2. 系统会自动清理内存、缓存等资源")
            print("   3. 也可以使用Ctrl+C强制退出")
            print("   4. 重启功能可以清理缓存并重新初始化系统")
        else:
            print("\n❌ 部分测试失败，请检查系统状态")
            
    except KeyboardInterrupt:
        print("\n\n⏹️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
    
    print(f"\n⏰ 结束时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

if __name__ == '__main__':
    main()
