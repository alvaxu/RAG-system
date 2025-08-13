'''
程序说明：
## 1. 调试图片查询返回0结果的问题
## 2. 分析优化管道中各个步骤的结果
## 3. 检查智能过滤和源过滤引擎的过滤逻辑
## 4. 提供详细的调试信息和解决方案
'''

import requests
import json
import time
import logging
from typing import Dict, Any, List

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImageQueryDebugger:
    """图片查询调试器"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        """
        初始化调试器
        
        :param base_url: API基础URL
        """
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_image_query_api(self):
        """测试图片查询API"""
        print("\n🔍 测试图片查询API...")
        
        # 测试直接图片查询
        url = f"{self.base_url}/api/v2/query/image"
        data = {
            "question": "图4：中芯国际归母净利润情况概览",
            "max_results": 10
        }
        
        try:
            print(f"请求URL: {url}")
            print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            response = self.session.post(url, json=data, timeout=30)
            print(f"响应状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                # 分析结果
                self._analyze_image_query_result(result)
            else:
                print(f"请求失败: {response.text}")
                
        except Exception as e:
            print(f"测试图片查询API时发生错误: {str(e)}")
    
    def test_hybrid_query_with_image_type(self):
        """测试混合查询API，指定图片类型"""
        print("\n🔍 测试混合查询API，指定图片类型...")
        
        url = f"{self.base_url}/api/v2/qa/ask"
        data = {
            "question": "图4：中芯国际归母净利润情况概览",
            "query_type": "image",
            "max_results": 10
        }
        
        try:
            print(f"请求URL: {url}")
            print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            response = self.session.post(url, json=data, timeout=30)
            print(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                # 分析结果
                self._analyze_hybrid_query_result(result)
            else:
                print(f"请求失败: {response.text}")
                
        except Exception as e:
            print(f"测试混合查询API时发生错误: {str(e)}")
    
    def test_hybrid_query_with_hybrid_type(self):
        """测试混合查询API，指定混合类型"""
        print("\n🔍 测试混合查询API，指定混合类型...")
        
        url = f"{self.base_url}/api/v2/qa/ask"
        data = {
            "question": "图4：中芯国际归母净利润情况概览",
            "query_type": "hybrid",
            "max_results": 10
        }
        
        try:
            print(f"请求URL: {url}")
            print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            response = self.session.post(url, json=data, timeout=30)
            print(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                # 分析结果
                self._analyze_hybrid_query_result(result)
            else:
                print(f"请求失败: {response.text}")
                
        except Exception as e:
            print(f"测试混合查询API时发生错误: {str(e)}")
    
    def test_system_status(self):
        """测试系统状态"""
        print("\n🔍 测试系统状态...")
        
        url = f"{self.base_url}/api/v2/status"
        
        try:
            response = self.session.get(url, timeout=10)
            print(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"系统状态: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                # 检查图片引擎状态
                if 'engines' in result and 'image' in result['engines']:
                    image_status = result['engines']['image']
                    print(f"图片引擎状态: {image_status}")
                else:
                    print("未找到图片引擎状态信息")
                    
            else:
                print(f"请求失败: {response.text}")
                
        except Exception as e:
            print(f"测试系统状态时发生错误: {str(e)}")
    
    def _analyze_image_query_result(self, result: Dict[str, Any]):
        """分析图片查询结果"""
        print("\n📊 分析图片查询结果:")
        
        if 'success' in result:
            print(f"查询成功: {result['success']}")
        
        if 'results' in result:
            results = result['results']
            print(f"结果数量: {len(results)}")
            
            if results:
                print("前3个结果:")
                for i, res in enumerate(results[:3]):
                    print(f"  结果 {i+1}:")
                    if isinstance(res, dict):
                        for key, value in res.items():
                            if key == 'content' and len(str(value)) > 100:
                                print(f"    {key}: {str(value)[:100]}...")
                            else:
                                print(f"    {key}: {value}")
                    else:
                        print(f"    {res}")
            else:
                print("没有找到结果")
        
        if 'metadata' in result:
            metadata = result['metadata']
            print(f"元数据: {metadata}")
    
    def _analyze_hybrid_query_result(self, result: Dict[str, Any]):
        """分析混合查询结果"""
        print("\n📊 分析混合查询结果:")
        
        if 'success' in result:
            print(f"查询成功: {result['success']}")
        
        if 'answer' in result:
            answer = result['answer']
            print(f"LLM答案: {answer[:200] if answer else '无'}...")
        
        if 'sources' in result:
            sources = result['sources']
            print(f"来源数量: {len(sources)}")
            
            if sources:
                print("前3个来源:")
                for i, source in enumerate(sources[:3]):
                    print(f"  来源 {i+1}:")
                    if isinstance(source, dict):
                        for key, value in source.items():
                            if key == 'content' and len(str(value)) > 100:
                                print(f"    {key}: {str(value)[:100]}...")
                            else:
                                print(f"    {key}: {value}")
                    else:
                        print(f"    {source}")
            else:
                print("没有找到来源")
        
        if 'metadata' in result:
            metadata = result['metadata']
            print(f"元数据: {metadata}")
            
            # 检查优化管道详情
            if 'optimization_details' in metadata:
                opt_details = metadata['optimization_details']
                print(f"优化管道详情: {opt_details}")
    
    def run_full_debug(self):
        """运行完整调试"""
        print("🚀 开始图片查询问题调试...")
        print("=" * 60)
        
        # 1. 检查系统状态
        self.test_system_status()
        
        # 2. 测试直接图片查询
        self.test_image_query_api()
        
        # 3. 测试混合查询，指定图片类型
        self.test_hybrid_query_with_image_type()
        
        # 4. 测试混合查询，指定混合类型
        self.test_hybrid_query_with_hybrid_type()
        
        print("\n" + "=" * 60)
        print("🎯 调试完成！")
        print("\n💡 可能的问题分析:")
        print("1. 图片引擎配置问题")
        print("2. 优化管道过滤过于严格")
        print("3. 智能过滤引擎阈值设置过高")
        print("4. 源过滤引擎相关性判断问题")
        print("5. 图片内容格式问题")

def main():
    """主函数"""
    debugger = ImageQueryDebugger()
    debugger.run_full_debug()

if __name__ == "__main__":
    main()
