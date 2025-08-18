#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
程序说明：
## 1. 测试DashScope导入和调用
## 2. 验证text_rerank函数是否可用
## 3. 诊断TableRerankingService的问题
'''

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_dashscope_import():
    """测试DashScope导入"""
    print("=" * 60)
    print("测试DashScope导入和调用")
    print("=" * 60)
    
    try:
        # 测试1：基本导入
        print("🔍 测试1：基本导入")
        import dashscope
        print(f"✅ dashscope导入成功，版本: {dashscope.__version__}")
        
        # 测试2：rerank模块导入
        print("\n🔍 测试2：rerank模块导入")
        from dashscope import rerank
        print(f"✅ dashscope.rerank导入成功，类型: {type(rerank)}")
        print(f"✅ rerank模块内容: {dir(rerank)}")
        
        # 测试3：text_rerank函数导入
        print("\n🔍 测试3：text_rerank函数导入")
        from dashscope.rerank import text_rerank
        print(f"✅ text_rerank导入成功，类型: {type(text_rerank)}")
        print(f"✅ text_rerank可调用: {callable(text_rerank)}")
        
        # 测试4：检查text_rerank的签名
        print("\n🔍 测试4：检查text_rerank的签名")
        if hasattr(text_rerank, '__call__'):
            print(f"✅ text_rerank有__call__方法")
            if hasattr(text_rerank, '__doc__'):
                print(f"✅ text_rerank文档: {text_rerank.__doc__[:100]}...")
        
        # 测试5：尝试调用text_rerank（不实际发送请求）
        print("\n🔍 测试5：尝试调用text_rerank")
        try:
            # 只是检查函数签名，不实际调用
            import inspect
            sig = inspect.signature(text_rerank)
            print(f"✅ text_rerank签名: {sig}")
        except Exception as e:
            print(f"❌ 获取函数签名失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(f"详细错误信息: {traceback.format_exc()}")
        return False

def test_table_reranking_service():
    """测试TableRerankingService的导入"""
    print("\n" + "=" * 60)
    print("测试TableRerankingService的导入")
    print("=" * 60)
    
    try:
        # 测试TableRerankingService导入
        print("🔍 测试TableRerankingService导入")
        from v2.core.reranking_services.table_reranking_service import TableRerankingService
        print("✅ TableRerankingService导入成功")
        
        # 测试配置
        print("\n🔍 测试配置")
        config = {
            'use_llm_enhancement': True,
            'model_name': 'gte-rerank-v2',
            'target_count': 10,
            'similarity_threshold': 0.7
        }
        
        # 测试实例化
        print("🔍 测试实例化")
        service = TableRerankingService(config)
        print("✅ TableRerankingService实例化成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(f"详细错误信息: {traceback.format_exc()}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试DashScope导入和TableRerankingService")
    
    success1 = test_dashscope_import()
    success2 = test_table_reranking_service()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 所有测试通过！")
    else:
        print("❌ 部分测试失败，请检查问题")
    
    return success1 and success2

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
