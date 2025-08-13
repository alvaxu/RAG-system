'''
程序说明：

## 1. 综合查询测试程序
## 2. 测试各种查询场景：图号查询、内容查询、混合查询等
## 3. 对比不同查询类型的结果差异
## 4. 帮助诊断系统问题

'''

import requests
import json
import time
from typing import Dict, Any, List
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveQueryTester:
    """综合查询测试器"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        """
        初始化测试器
        
        :param base_url: API基础URL
        """
        self.base_url = base_url
        self.session_id = None
        self.test_results = []
        
    def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """发送API请求"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.post(url, json=data, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败 {endpoint}: {e}")
            return {"error": str(e)}
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败 {endpoint}: {e}")
            return {"error": "JSON解析失败"}
    
    def _test_query(self, query: str, query_type: str = "smart") -> Dict[str, Any]:
        """测试单个查询"""
        logger.info(f"🔍 测试查询: {query}")
        logger.info(f"📝 查询类型: {query_type}")
        
        data = {
            "query": query,
            "query_type": query_type,
            "session_id": self.session_id
        }
        
        start_time = time.time()
        result = self._make_request("/api/v2/qa/ask", data)
        end_time = time.time()
        
        # 分析结果
        analysis = self._analyze_result(result, query, query_type, end_time - start_time)
        
        # 记录测试结果
        test_result = {
            "query": query,
            "query_type": query_type,
            "result": result,
            "analysis": analysis,
            "response_time": end_time - start_time
        }
        self.test_results.append(test_result)
        
        return test_result
    
    def _analyze_result(self, result: Dict[str, Any], query: str, query_type: str, response_time: float) -> Dict[str, Any]:
        """分析查询结果"""
        analysis = {
            "success": False,
            "total_results": 0,
            "image_results": 0,
            "text_results": 0,
            "table_results": 0,
            "has_llm_answer": False,
            "llm_answer_length": 0,
            "has_sources": False,
            "source_count": 0,
            "response_time": response_time,
            "issues": [],
            "optimization_metrics": {}
        }
        
        try:
            # 检查基本成功状态
            if "error" in result:
                analysis["issues"].append(f"API错误: {result['error']}")
                return analysis
            
            # 检查结果数量
            total_results = result.get("total_results", 0)
            analysis["total_results"] = total_results
            
            # 检查图片结果
            image_results = result.get("image_results", [])
            analysis["image_results"] = len(image_results)
            
            # 检查文本结果
            text_results = result.get("text_results", [])
            analysis["text_results"] = len(text_results)
            
            # 检查表格结果
            table_results = result.get("table_results", [])
            analysis["table_results"] = len(table_results)
            
            # 检查LLM答案
            answer = result.get("answer", "")
            if answer and answer.strip():
                analysis["has_llm_answer"] = True
                analysis["llm_answer_length"] = len(answer)
            else:
                analysis["issues"].append("LLM答案为空")
            
            # 检查来源信息
            sources = result.get("sources", [])
            if sources:
                analysis["has_sources"] = True
                analysis["source_count"] = len(sources)
            else:
                analysis["issues"].append("来源信息为空")
            
            # 检查优化管道指标
            if "optimization_details" in result:
                opt_details = result["optimization_details"]
                analysis["optimization_metrics"] = {
                    "reranked_count": opt_details.get("reranked_count", 0),
                    "filtered_count": opt_details.get("filtered_count", 0),
                    "llm_answer_length": opt_details.get("llm_answer_length", 0),
                    "pipeline_metrics": opt_details.get("pipeline_metrics", {})
                }
            
            # 判断是否成功
            if total_results > 0 or analysis["has_llm_answer"]:
                analysis["success"] = True
            
            # 检查潜在问题
            if total_results == 0 and not analysis["has_llm_answer"]:
                analysis["issues"].append("查询结果为0且无LLM答案")
            
            if response_time > 30:
                analysis["issues"].append(f"响应时间过长: {response_time:.2f}秒")
                
        except Exception as e:
            analysis["issues"].append(f"结果分析失败: {str(e)}")
        
        return analysis
    
    def run_comprehensive_tests(self):
        """运行综合测试"""
        logger.info("🚀 开始综合查询测试")
        logger.info("=" * 60)
        
        # 测试用例定义
        test_cases = [
            # 图号查询测试
            ("请显示图4", "smart", "图号精确查询"),
            ("请显示图4：中芯国际归母净利润情况概览", "smart", "图号+内容查询"),
            ("请显示两张图4", "smart", "图号+数量查询"),
            ("请显示所有图4", "smart", "图号+全部查询"),
            
            # 内容查询测试
            ("有没有与中芯国际股票走势有关的图片", "smart", "图片内容查询"),
            ("中芯国际的主要业务和核心技术是什么？", "smart", "文本内容查询"),
            ("中芯国际的财务数据表格", "smart", "表格内容查询"),
            
            # 混合查询测试
            ("中芯国际的营收情况和相关图表", "smart", "混合查询"),
            ("请分析中芯国际的发展历程，包括图表和表格", "smart", "综合分析查询"),
            
            # 边界情况测试
            ("", "smart", "空查询"),
            ("测试", "smart", "简单测试查询"),
            ("中芯国际", "smart", "公司名称查询"),
        ]
        
        # 执行测试
        for query, query_type, description in test_cases:
            logger.info(f"\n📋 测试用例: {description}")
            logger.info("-" * 40)
            
            result = self._test_query(query, query_type)
            
            # 显示结果摘要
            self._display_result_summary(result)
            
            # 短暂延迟，避免API限流
            time.sleep(1)
        
        # 生成测试报告
        self._generate_test_report()
    
    def _display_result_summary(self, test_result: Dict[str, Any]):
        """显示测试结果摘要"""
        query = test_result["query"]
        analysis = test_result["analysis"]
        
        logger.info(f"查询: {query}")
        logger.info(f"响应时间: {analysis['response_time']:.2f}秒")
        logger.info(f"总结果数: {analysis['total_results']}")
        logger.info(f"图片结果: {analysis['image_results']}")
        logger.info(f"文本结果: {analysis['text_results']}")
        logger.info(f"表格结果: {analysis['table_results']}")
        logger.info(f"LLM答案: {'✅' if analysis['has_llm_answer'] else '❌'}")
        logger.info(f"来源信息: {'✅' if analysis['has_sources'] else '❌'}")
        
        if analysis["issues"]:
            logger.warning(f"⚠️ 发现的问题: {', '.join(analysis['issues'])}")
        
        # 显示优化管道指标
        if analysis["optimization_metrics"]:
            opt_metrics = analysis["optimization_metrics"]
            logger.info(f"🔄 重排序: {opt_metrics.get('reranked_count', 0)}")
            logger.info(f"🧹 过滤后: {opt_metrics.get('filtered_count', 0)}")
            logger.info(f"🤖 LLM答案长度: {opt_metrics.get('llm_answer_length', 0)}")
    
    def _generate_test_report(self):
        """生成测试报告"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 综合测试报告")
        logger.info("=" * 60)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r["analysis"]["success"])
        failed_tests = total_tests - successful_tests
        
        logger.info(f"总测试数: {total_tests}")
        logger.info(f"成功测试: {successful_tests}")
        logger.info(f"失败测试: {failed_tests}")
        logger.info(f"成功率: {successful_tests/total_tests*100:.1f}%")
        
        # 分析问题
        all_issues = []
        for result in self.test_results:
            all_issues.extend(result["analysis"]["issues"])
        
        if all_issues:
            logger.info(f"\n🚨 发现的问题:")
            issue_counts = {}
            for issue in all_issues:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
            
            for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"  - {issue}: {count}次")
        
        # 性能分析
        response_times = [r["analysis"]["response_time"] for r in self.test_results]
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        
        logger.info(f"\n⏱️ 性能分析:")
        logger.info(f"  平均响应时间: {avg_time:.2f}秒")
        logger.info(f"  最快响应时间: {min_time:.2f}秒")
        logger.info(f"  最慢响应时间: {max_time:.2f}秒")
        
        # 结果分布分析
        logger.info(f"\n📈 结果分布分析:")
        zero_results = sum(1 for r in self.test_results if r["analysis"]["total_results"] == 0)
        logger.info(f"  零结果查询: {zero_results}/{total_tests}")
        
        if zero_results > 0:
            logger.warning(f"⚠️ 有 {zero_results} 个查询返回0结果，需要进一步调查")
    
    def test_specific_scenarios(self):
        """测试特定场景"""
        logger.info("\n🎯 特定场景测试")
        logger.info("=" * 40)
        
        # 测试1: 图号查询的详细分析
        logger.info("\n🔍 测试1: 图号查询详细分析")
        result = self._test_query("请显示图4", "smart")
        if "image_results" in result["result"]:
            image_results = result["result"]["image_results"]
            logger.info(f"找到 {len(image_results)} 张图片")
            for i, img in enumerate(image_results[:3]):
                logger.info(f"  图片 {i+1}: {img.get('caption', 'N/A')} (分数: {img.get('score', 0):.3f})")
        
        # 测试2: 内容查询的详细分析
        logger.info("\n🔍 测试2: 内容查询详细分析")
        result = self._test_query("中芯国际的主要业务", "smart")
        if "text_results" in result["result"]:
            text_results = result["result"]["text_results"]
            logger.info(f"找到 {len(text_results)} 个文本结果")
            for i, text in enumerate(text_results[:3]):
                content = text.get('content', '')[:100]
                logger.info(f"  文本 {i+1}: {content}...")
        
        # 测试3: 优化管道状态检查
        logger.info("\n🔍 测试3: 优化管道状态检查")
        try:
            status_response = requests.get(f"{self.base_url}/api/v2/status", timeout=10)
            if status_response.status_code == 200:
                status_data = status_response.json()
                logger.info("系统状态:")
                for key, value in status_data.items():
                    logger.info(f"  {key}: {value}")
            else:
                logger.warning(f"状态检查失败: {status_response.status_code}")
        except Exception as e:
            logger.error(f"状态检查异常: {e}")

def main():
    """主函数"""
    logger.info("🧪 综合查询测试程序启动")
    
    # 创建测试器
    tester = ComprehensiveQueryTester()
    
    try:
        # 运行综合测试
        tester.run_comprehensive_tests()
        
        # 运行特定场景测试
        tester.test_specific_scenarios()
        
        logger.info("\n✅ 所有测试完成！")
        
    except KeyboardInterrupt:
        logger.info("\n⏹️ 测试被用户中断")
    except Exception as e:
        logger.error(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
