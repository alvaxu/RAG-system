'''
程序说明：

## 1. 测试优化引擎状态显示功能
## 2. 验证V2RAGSystem的优化引擎初始化
## 3. 检查系统状态信息的完整性
## 4. 用于调试和验证优化引擎集成
'''

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from V800_v2_main import V2RAGSystem

def test_optimization_status():
    """测试优化引擎状态显示功能"""
    print("🧪 开始测试优化引擎状态显示功能...")
    
    try:
        # 初始化V2系统
        print("\n🚀 初始化V2 RAG系统...")
        v2_rag_system = V2RAGSystem()
        
        # 获取系统状态
        print("\n📊 获取系统状态...")
        status = v2_rag_system.get_system_status()
        
        # 显示完整状态
        print("\n🔍 完整系统状态:")
        import json
        print(json.dumps(status, indent=2, ensure_ascii=False))
        
        # 检查优化引擎状态
        print("\n🎯 优化引擎状态检查:")
        if 'optimization_engines' in status:
            opt_status = status['optimization_engines']
            
            print("✅ 优化引擎状态信息存在")
            print(f"  - 管道启用: {opt_status.get('pipeline_enabled', False)}")
            print(f"  - 重排序引擎就绪: {opt_status.get('reranking_engine_ready', False)}")
            print(f"  - LLM引擎就绪: {opt_status.get('llm_engine_ready', False)}")
            print(f"  - 智能过滤引擎就绪: {opt_status.get('smart_filter_engine_ready', False)}")
            print(f"  - 源过滤引擎就绪: {opt_status.get('source_filter_engine_ready', False)}")
            
            # 检查配置状态
            print(f"  - 重排序配置: {opt_status.get('reranking_enabled', False)}")
            print(f"  - LLM生成配置: {opt_status.get('llm_generation_enabled', False)}")
            print(f"  - 智能过滤配置: {opt_status.get('smart_filtering_enabled', False)}")
            print(f"  - 源过滤配置: {opt_status.get('source_filtering_enabled', False)}")
        else:
            print("❌ 优化引擎状态信息缺失")
        
        # 检查混合引擎状态
        print("\n🔧 混合引擎状态检查:")
        if status.get('hybrid_engine_ready'):
            print("✅ 混合引擎已就绪")
            
            # 检查混合引擎实例
            if v2_rag_system.hybrid_engine:
                hybrid = v2_rag_system.hybrid_engine
                print(f"  - 重排序引擎: {'✅ 存在' if hasattr(hybrid, 'reranking_engine') and hybrid.reranking_engine else '❌ 不存在'}")
                print(f"  - LLM引擎: {'✅ 存在' if hasattr(hybrid, 'llm_engine') and hybrid.llm_engine else '❌ 不存在'}")
                print(f"  - 智能过滤引擎: {'✅ 存在' if hasattr(hybrid, 'smart_filter_engine') and hybrid.smart_filter_engine else '❌ 不存在'}")
                print(f"  - 源过滤引擎: {'✅ 存在' if hasattr(hybrid, 'source_filter_engine') and hybrid.source_filter_engine else '❌ 不存在'}")
            else:
                print("❌ 混合引擎实例不存在")
        else:
            print("❌ 混合引擎未就绪")
        
        print("\n✅ 测试完成！")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_optimization_status()
    sys.exit(0 if success else 1)
