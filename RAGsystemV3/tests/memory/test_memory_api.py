"""
记忆模块API测试脚本

测试记忆模块的RESTful API接口
"""

import sys
import os
import requests
import json
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class MemoryAPITester:
    """记忆模块API测试类"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v3/memory"
        self.session = requests.Session()
        self.test_session_id = None
        self.test_memory_id = None
    
    def test_health_check(self):
        """测试API健康检查"""
        print("\n=== 测试API健康检查 ===")
        
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("✓ API服务正常运行")
                return True
            else:
                print(f"✗ API服务异常: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ API服务连接失败: {e}")
            return False
    
    def test_create_session(self):
        """测试创建会话API"""
        print("\n=== 测试创建会话API ===")
        
        try:
            data = {
                "user_id": "test_user_api",
                "metadata": {
                    "source": "api_test",
                    "test": True
                }
            }
            
            response = self.session.post(
                f"{self.api_base}/sessions",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                result = response.json()
                self.test_session_id = result["session_id"]
                print(f"✓ 会话创建成功: {self.test_session_id}")
                return True
            else:
                print(f"✗ 会话创建失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ 会话创建异常: {e}")
            return False
    
    def test_get_session(self):
        """测试获取会话API"""
        print("\n=== 测试获取会话API ===")
        
        if not self.test_session_id:
            print("✗ 没有可用的测试会话ID")
            return False
        
        try:
            response = self.session.get(f"{self.api_base}/sessions/{self.test_session_id}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ 会话获取成功: {result['session_id']}")
                return True
            else:
                print(f"✗ 会话获取失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ 会话获取异常: {e}")
            return False
    
    def test_list_sessions(self):
        """测试列出会话API"""
        print("\n=== 测试列出会话API ===")
        
        try:
            response = self.session.get(f"{self.api_base}/sessions")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ 会话列表获取成功: 共 {len(result)} 个会话")
                return True
            else:
                print(f"✗ 会话列表获取失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ 会话列表获取异常: {e}")
            return False
    
    def test_add_memory(self):
        """测试添加记忆API"""
        print("\n=== 测试添加记忆API ===")
        
        if not self.test_session_id:
            print("✗ 没有可用的测试会话ID")
            return False
        
        try:
            data = {
                "content": "这是一个API测试记忆",
                "content_type": "text",
                "relevance_score": 0.8,
                "importance_score": 0.7,
                "metadata": {
                    "test": True,
                    "api_test": True
                }
            }
            
            response = self.session.post(
                f"{self.api_base}/sessions/{self.test_session_id}/memories",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                result = response.json()
                self.test_memory_id = result["chunk_id"]
                print(f"✓ 记忆添加成功: {self.test_memory_id}")
                return True
            else:
                print(f"✗ 记忆添加失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ 记忆添加异常: {e}")
            return False
    
    def test_query_memories(self):
        """测试查询记忆API"""
        print("\n=== 测试查询记忆API ===")
        
        if not self.test_session_id:
            print("✗ 没有可用的测试会话ID")
            return False
        
        try:
            data = {
                "query_text": "API测试",
                "max_results": 5,
                "similarity_threshold": 0.5,
                "content_types": ["text"]
            }
            
            response = self.session.post(
                f"{self.api_base}/sessions/{self.test_session_id}/memories/query",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ 记忆查询成功: 找到 {len(result)} 条相关记忆")
                return True
            else:
                print(f"✗ 记忆查询失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ 记忆查询异常: {e}")
            return False
    
    def test_compress_memories(self):
        """测试压缩记忆API"""
        print("\n=== 测试压缩记忆API ===")
        
        if not self.test_session_id:
            print("✗ 没有可用的测试会话ID")
            return False
        
        try:
            data = {
                "strategy": "semantic",
                "threshold": 5,
                "max_ratio": 0.5,
                "force": True
            }
            
            response = self.session.post(
                f"{self.api_base}/sessions/{self.test_session_id}/compress",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ 记忆压缩成功: 压缩比例 {result['compression_ratio']:.2f}")
                return True
            else:
                print(f"✗ 记忆压缩失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ 记忆压缩异常: {e}")
            return False
    
    def test_get_stats(self):
        """测试获取统计信息API"""
        print("\n=== 测试获取统计信息API ===")
        
        try:
            response = self.session.get(f"{self.api_base}/stats")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ 统计信息获取成功:")
                print(f"  总会话数: {result.get('total_sessions', 0)}")
                print(f"  总记忆数: {result.get('total_memories', 0)}")
                print(f"  活跃会话数: {result.get('active_sessions', 0)}")
                return True
            else:
                print(f"✗ 统计信息获取失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ 统计信息获取异常: {e}")
            return False
    
    def test_error_handling(self):
        """测试错误处理"""
        print("\n=== 测试错误处理 ===")
        
        # 测试获取不存在的会话
        try:
            response = self.session.get(f"{self.api_base}/sessions/non_existent_session")
            if response.status_code == 404:
                print("✓ 不存在的会话返回404错误")
            else:
                print(f"✗ 期望404错误，实际得到: {response.status_code}")
        except Exception as e:
            print(f"✗ 错误处理测试异常: {e}")
        
        # 测试向不存在的会话添加记忆
        try:
            data = {"content": "测试内容"}
            response = self.session.post(
                f"{self.api_base}/sessions/non_existent_session/memories",
                json=data
            )
            if response.status_code == 404:
                print("✓ 向不存在的会话添加记忆返回404错误")
            else:
                print(f"✗ 期望404错误，实际得到: {response.status_code}")
        except Exception as e:
            print(f"✗ 错误处理测试异常: {e}")
    
    def run_all_tests(self):
        """运行所有API测试"""
        print("开始记忆模块API测试...")
        print("=" * 50)
        
        tests = [
            ("健康检查", self.test_health_check),
            ("创建会话", self.test_create_session),
            ("获取会话", self.test_get_session),
            ("列出会话", self.test_list_sessions),
            ("添加记忆", self.test_add_memory),
            ("查询记忆", self.test_query_memories),
            ("压缩记忆", self.test_compress_memories),
            ("获取统计", self.test_get_stats),
            ("错误处理", self.test_error_handling)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                print(f"✗ {test_name}测试异常: {e}")
        
        print("\n" + "=" * 50)
        print(f"API测试完成: {passed}/{total} 通过")
        
        if passed == total:
            print("✅ 所有API测试通过！")
            return True
        else:
            print("❌ 部分API测试失败")
            return False


def main():
    """主函数"""
    print("记忆模块API测试程序")
    print("=" * 50)
    
    # 检查API服务是否运行
    tester = MemoryAPITester()
    
    if not tester.test_health_check():
        print("请确保RAG系统API服务正在运行 (http://localhost:8000)")
        return 1
    
    # 运行所有测试
    success = tester.run_all_tests()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
