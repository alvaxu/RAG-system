#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time

def test_query(query, query_type="smart"):
    """测试单个查询"""
    print(f"\n🔍 测试查询: {query}")
    print(f"📝 查询类型: {query_type}")
    
    data = {
        "query": query,
        "query_type": query_type
    }
    
    try:
        start_time = time.time()
        response = requests.post("http://localhost:5000/api/v2/qa/ask", json=data, timeout=60)
        end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            
            # 分析结果
            total_results = result.get("total_results", 0)
            image_results = result.get("image_results", [])
            text_results = result.get("text_results", [])
            table_results = result.get("table_results", [])
            answer = result.get("answer", "")
            
            print(f"✅ 查询成功")
            print(f"⏱️ 响应时间: {end_time - start_time:.2f}秒")
            print(f"📊 总结果数: {total_results}")
            print(f"🖼️ 图片结果: {len(image_results)}")
            print(f"📝 文本结果: {len(text_results)}")
            print(f"📊 表格结果: {len(table_results)}")
            print(f"🤖 LLM答案: {'有' if answer.strip() else '无'}")
            
            # 显示优化管道信息
            if "optimization_details" in result:
                opt = result["optimization_details"]
                print(f"🔄 重排序: {opt.get('reranked_count', 0)}")
                print(f"🧹 过滤后: {opt.get('filtered_count', 0)}")
                print(f"🤖 LLM答案长度: {opt.get('llm_answer_length', 0)}")
            
            # 显示前几个结果
            if image_results:
                print(f"📸 图片结果预览:")
                for i, img in enumerate(image_results[:3]):
                    caption = img.get('caption', 'N/A')
                    score = img.get('score', 0)
                    print(f"  {i+1}. {caption} (分数: {score:.3f})")
            
            if text_results:
                print(f"📝 文本结果预览:")
                for i, text in enumerate(text_results[:3]):
                    content = text.get('content', '')[:100]
                    print(f"  {i+1}. {content}...")
            
            return True
            
        else:
            print(f"❌ 查询失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 开始综合查询测试")
    print("=" * 50)
    
    # 测试用例
    test_cases = [
        ("请显示图4", "图号查询"),
        ("请显示图4：中芯国际归母净利润情况概览", "图号+内容查询"),
        ("有没有与中芯国际股票走势有关的图片", "图片内容查询"),
        ("中芯国际的主要业务和核心技术是什么？", "文本查询"),
        ("中芯国际的财务数据表格", "表格查询"),
        ("中芯国际的营收情况和相关图表", "混合查询"),
        ("测试", "简单测试"),
        ("中芯国际", "公司名称查询")
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for query, description in test_cases:
        print(f"\n📋 测试用例: {description}")
        print("-" * 30)
        
        if test_query(query):
            success_count += 1
        
        time.sleep(1)  # 避免API限流
    
    # 测试报告
    print(f"\n" + "=" * 50)
    print(f"📊 测试报告")
    print(f"=" * 50)
    print(f"总测试数: {total_count}")
    print(f"成功测试: {success_count}")
    print(f"失败测试: {total_count - success_count}")
    print(f"成功率: {success_count/total_count*100:.1f}%")
    
    # 检查系统状态
    print(f"\n🔍 检查系统状态...")
    try:
        status_response = requests.get("http://localhost:5000/api/v2/status", timeout=10)
        if status_response.status_code == 200:
            status = status_response.json()
            print("✅ 系统状态正常")
            for key, value in status.items():
                print(f"  {key}: {value}")
        else:
            print(f"⚠️ 系统状态检查失败: {status_response.status_code}")
    except Exception as e:
        print(f"❌ 系统状态检查异常: {e}")

if __name__ == "__main__":
    main()
