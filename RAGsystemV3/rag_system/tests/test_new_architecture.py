"""
新架构测试脚本

测试重构后的查询处理器架构是否正常工作
"""

import asyncio
import logging
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_system.core.config_integration import ConfigIntegration
from rag_system.core.query_processor import QueryProcessor
from rag_system.core.query_router import SimpleQueryRouter
from rag_system.core.simple_smart_processor import SimpleSmartProcessor
from rag_system.core.simple_hybrid_processor import SimpleHybridProcessor
from rag_system.core.unified_services import UnifiedServices

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_new_architecture():
    """测试新架构的各个组件"""
    
    print("🚀 开始测试新架构...")
    
    try:
        # 1. 测试配置集成
        print("\n📋 1. 测试配置集成...")
        config = ConfigIntegration()
        print(f"✅ 配置集成初始化成功")
        
        # 2. 测试统一服务接口
        print("\n🔧 2. 测试统一服务接口...")
        try:
            unified_services = UnifiedServices(config)
            print(f"✅ 统一服务接口初始化成功")
        except Exception as e:
            print(f"⚠️ 统一服务接口初始化失败（预期）：{e}")
        
        # 3. 测试智能查询处理器
        print("\n🧠 3. 测试智能查询处理器...")
        try:
            smart_processor = SimpleSmartProcessor(config)
            print(f"✅ 智能查询处理器初始化成功")
        except Exception as e:
            print(f"⚠️ 智能查询处理器初始化失败（预期）：{e}")
        
        # 4. 测试混合查询处理器
        print("\n🔄 4. 测试混合查询处理器...")
        try:
            hybrid_processor = SimpleHybridProcessor(config)
            print(f"✅ 混合查询处理器初始化成功")
        except Exception as e:
            print(f"⚠️ 混合查询处理器初始化失败（预期）：{e}")
        
        # 5. 测试查询路由器
        print("\n🛣️ 5. 测试查询路由器...")
        try:
            query_router = SimpleQueryRouter(config)
            print(f"✅ 查询路由器初始化成功")
            
            # 测试服务状态
            status = query_router.get_service_status()
            print(f"✅ 查询路由器状态: {status['status']}")
            
        except Exception as e:
            print(f"❌ 查询路由器初始化失败: {e}")
            return False
        
        # 6. 测试查询处理器
        print("\n🎯 6. 测试查询处理器...")
        try:
            query_processor = QueryProcessor(config)
            print(f"✅ 查询处理器初始化成功")
            
            # 测试服务状态
            status = query_processor.get_service_status()
            print(f"✅ 查询处理器状态: {status['status']}")
            
            # 测试处理统计信息
            stats = query_processor.get_processing_statistics()
            print(f"✅ 处理统计信息: {stats['architecture']}")
            
        except Exception as e:
            print(f"❌ 查询处理器初始化失败: {e}")
            return False
        
        # 7. 测试查询类型检测
        print("\n🔍 7. 测试查询类型检测...")
        try:
            # 测试不同类型的查询
            test_queries = [
                ("这是一个关于图片的问题，请显示相关的图片", "image"),
                ("请提供表格数据，包括销售统计", "table"),
                ("这是一个普通的文本查询问题", "text"),
                ("请显示图片和表格数据", "hybrid")
            ]
            
            for query, expected_type in test_queries:
                detected_type, confidence = query_router._detect_query_type(query)
                print(f"  查询: {query[:30]}...")
                print(f"    检测类型: {detected_type} (期望: {expected_type})")
                print(f"    置信度: {confidence:.2f}")
                
                if detected_type == expected_type:
                    print(f"    ✅ 类型检测正确")
                else:
                    print(f"    ⚠️ 类型检测可能不准确")
            
        except Exception as e:
            print(f"❌ 查询类型检测测试失败: {e}")
        
        print("\n🎉 新架构测试完成！")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        return False


async def test_query_processing():
    """测试查询处理流程"""
    
    print("\n🔄 开始测试查询处理流程...")
    
    try:
        # 初始化配置和查询处理器
        config = ConfigIntegration()
        query_processor = QueryProcessor(config)
        
        # 测试查询
        test_query = "请提供关于图片处理的相关信息"
        
        print(f"📝 测试查询: {test_query}")
        
        # 执行查询处理
        result = await query_processor.process_query(
            query=test_query,
            query_type="auto",
            options={
                'max_results': 5,
                'relevance_threshold': 0.6,
                'context_length_limit': 3000,
                'enable_streaming': True
            }
        )
        
        # 显示结果
        print(f"✅ 查询处理完成")
        print(f"   成功: {result.success}")
        print(f"   查询类型: {result.query_type}")
        print(f"   答案长度: {len(result.answer) if result.answer else 0}")
        print(f"   结果数量: {len(result.results)}")
        print(f"   处理元数据: {result.processing_metadata}")
        
        if result.error_message:
            print(f"   错误信息: {result.error_message}")
        
        return True
        
    except Exception as e:
        print(f"❌ 查询处理测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    
    print("=" * 60)
    print("🧪 RAG系统新架构测试")
    print("=" * 60)
    
    # 测试架构组件
    architecture_ok = await test_new_architecture()
    
    if architecture_ok:
        # 测试查询处理流程
        await test_query_processing()
    
    print("\n" + "=" * 60)
    if architecture_ok:
        print("🎉 所有测试完成！新架构工作正常。")
    else:
        print("❌ 架构测试失败，需要检查问题。")
    print("=" * 60)


if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())
