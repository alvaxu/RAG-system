'''
程序说明：
## 1. 专门调试重排序引擎的问题
## 2. 检查配置是否正确加载
## 3. 分析重排序引擎的处理逻辑
## 4. 验证API调用是否正常
'''

import requests
import json
import time
import logging
from typing import Dict, Any, List

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RerankingEngineDebugger:
    """重排序引擎调试器"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        """
        初始化调试器
        
        :param base_url: API基础URL
        """
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_reranking_engine_status(self):
        """测试重排序引擎状态"""
        print("\n🔍 测试重排序引擎状态...")
        
        url = f"{self.base_url}/api/v2/status"
        
        try:
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status', {})
                
                print(f"重排序引擎状态: {status.get('reranking_engine_ready', '未知')}")
                
                # 检查是否有重排序引擎的详细信息
                if 'engines' in result and 'reranking' in result['engines']:
                    reranking_info = result['engines']['reranking']
                    print(f"重排序引擎详细信息: {json.dumps(reranking_info, ensure_ascii=False, indent=2)}")
                else:
                    print("未找到重排序引擎详细信息")
                    
            else:
                print(f"请求失败: {response.text}")
                
        except Exception as e:
            print(f"测试重排序引擎状态时发生错误: {str(e)}")
    
    def test_image_query_with_debug(self):
        """测试图片查询，重点关注重排序过程"""
        print("\n🔍 测试图片查询，重点关注重排序过程...")
        
        url = f"{self.base_url}/api/v2/qa/ask"
        data = {
            "question": "图4：中芯国际归母净利润情况概览",
            "query_type": "image",
            "max_results": 10
        }
        
        try:
            print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            response = self.session.post(url, json=data, timeout=30)
            print(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"查询成功: {result.get('success')}")
                print(f"来源数量: {len(result.get('sources', []))}")
                
                # 详细分析优化管道
                self._analyze_optimization_pipeline(result)
            else:
                print(f"请求失败: {response.text}")
                
        except Exception as e:
            print(f"测试时发生错误: {str(e)}")
    
    def test_hybrid_query_for_comparison(self):
        """测试混合查询作为对比"""
        print("\n🔍 测试混合查询作为对比...")
        
        url = f"{self.base_url}/api/v2/qa/ask"
        data = {
            "question": "图4：中芯国际归母净利润情况概览",
            "query_type": "hybrid",
            "max_results": 10
        }
        
        try:
            print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            response = self.session.post(url, json=data, timeout=30)
            print(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"查询成功: {result.get('success')}")
                print(f"来源数量: {len(result.get('sources', []))}")
                
                # 对比分析
                self._analyze_optimization_pipeline(result, "混合查询")
            else:
                print(f"请求失败: {response.text}")
                
        except Exception as e:
            print(f"测试时发生错误: {str(e)}")
    
    def _analyze_optimization_pipeline(self, result: Dict[str, Any], query_type: str = "图片查询"):
        """分析优化管道"""
        print(f"\n📊 分析{query_type}的优化管道:")
        
        metadata = result.get('metadata', {})
        optimization_details = metadata.get('optimization_details', {})
        
        if optimization_details:
            print(f"优化管道详情:")
            print(f"  输入结果数量: {optimization_details.get('pipeline_metrics', {}).get('input_count', 0)}")
            print(f"  重排序后数量: {optimization_details.get('reranked_count', 0)}")
            print(f"  过滤后数量: {optimization_details.get('filtered_count', 0)}")
            print(f"  最终来源数量: {optimization_details.get('filtered_sources_count', 0)}")
            
            # 分析重排序过程
            pipeline_metrics = optimization_details.get('pipeline_metrics', {})
            print(f"  重排序耗时: {pipeline_metrics.get('rerank_time', 0):.3f}秒")
            print(f"  重排序数量: {pipeline_metrics.get('rerank_count', 0)}")
            
            # 检查是否有错误信息
            if 'error' in pipeline_metrics:
                print(f"  错误信息: {pipeline_metrics['error']}")
        else:
            print("未找到优化管道详情")
        
        # 检查引擎使用情况
        engines_used = metadata.get('engines_used', [])
        print(f"使用的引擎: {engines_used}")
        
        # 检查查询意图
        query_intent = metadata.get('query_intent', '')
        print(f"查询意图: {query_intent}")
    
    def test_config_loading(self):
        """测试配置是否正确加载"""
        print("\n🔍 测试配置是否正确加载...")
        
        # 通过系统状态检查配置
        url = f"{self.base_url}/api/v2/status"
        
        try:
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                
                # 检查是否有配置信息
                if 'config' in result:
                    config = result['config']
                    print(f"系统配置: {json.dumps(config, ensure_ascii=False, indent=2)}")
                else:
                    print("未找到系统配置信息")
                    
            else:
                print(f"请求失败: {response.text}")
                
        except Exception as e:
            print(f"测试配置加载时发生错误: {str(e)}")
    
    def run_full_debug(self):
        """运行完整调试"""
        print("🚀 开始重排序引擎调试...")
        print("=" * 60)
        
        # 1. 检查重排序引擎状态
        self.test_reranking_engine_status()
        
        # 2. 测试配置加载
        self.test_config_loading()
        
        # 3. 测试图片查询
        self.test_image_query_with_debug()
        
        # 4. 测试混合查询作为对比
        self.test_hybrid_query_for_comparison()
        
        print("\n" + "=" * 60)
        print("🎯 调试完成！")
        print("\n💡 重排序引擎问题分析:")
        print("1. 配置是否正确加载")
        print("2. 重排序引擎是否正常工作")
        print("3. 重排序API调用是否成功")
        print("4. 数据处理逻辑是否有问题")
        print("5. 阈值设置是否生效")

def main():
    """主函数"""
    debugger = RerankingEngineDebugger()
    debugger.run_full_debug()

if __name__ == "__main__":
    main()
