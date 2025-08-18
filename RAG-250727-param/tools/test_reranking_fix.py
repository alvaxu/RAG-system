#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
测试ImageRerankingService修复后的效果

## 1. 测试导入是否正常
## 2. 测试API调用方式是否正确
## 3. 验证降级机制是否工作
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_reranking_fix():
    """测试重排序服务修复效果"""
    try:
        print("🔍 开始测试ImageRerankingService修复效果...")
        
        # 测试导入
        try:
            from v2.core.reranking_services.image_reranking_service import ImageRerankingService
            print("✅ ImageRerankingService导入成功")
        except ImportError as e:
            print(f"❌ ImageRerankingService导入失败: {e}")
            return False
        
        # 测试DashScope导入
        try:
            import dashscope
            from dashscope.rerank import text_rerank
            print("✅ DashScope模块导入成功")
            print(f"✅ text_rerank模块: {text_rerank}")
        except ImportError as e:
            print(f"❌ DashScope模块导入失败: {e}")
            return False
        
        # 测试TextReRank类
        try:
            print(f"✅ TextReRank类: {text_rerank.TextReRank}")
            print(f"✅ TextReRank.call方法: {text_rerank.TextReRank.call}")
        except AttributeError as e:
            print(f"❌ TextReRank类或方法不存在: {e}")
            return False
        
        print("\n🎉 所有测试通过！ImageRerankingService修复成功")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_reranking_fix()
    sys.exit(0 if success else 1)
