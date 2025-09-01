"""
配置验证测试脚本

测试配置验证器的各项功能，确保符合技术规范要求
"""

import json
import logging
from core.config_validator import ConfigValidator
from core.exceptions import ConfigurationError, ValidationError

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_valid_config():
    """测试有效配置"""
    print("\n🧪 测试有效配置...")
    
    valid_config = {
        "enabled": True,
        "version": "3.0.0",
        "models": {
            "llm": {
                "model_name": "qwen-turbo",
                "max_tokens": 2048,
                "temperature": 0.7
            },
            "reranking": {
                "model_name": "gte-rerank-v2",
                "batch_size": 32,
                "similarity_threshold": 0.7
            }
        },
        "query_processing": {
            "max_context_length": 4000,
            "max_results": 10,
            "relevance_threshold": 0.5
        },
        "engines": {
            "text_engine": {
                "enabled": True,
                "max_results": 10,
                "similarity_threshold": 0.7
            },
            "image_engine": {
                "enabled": True,
                "max_results": 20,
                "similarity_threshold": 0.3
            },
            "table_engine": {
                "enabled": True,
                "max_results": 15,
                "similarity_threshold": 0.65
            }
        },
        "performance": {
            "max_concurrent_queries": 10,
            "query_timeout": 60,
            "enable_monitoring": True
        }
    }
    
    try:
        validator = ConfigValidator()
        result = validator.validate_config(valid_config)
        print(f"✅ 有效配置验证通过: {result}")
        return True
    except Exception as e:
        print(f"❌ 有效配置验证失败: {e}")
        return False


def test_invalid_config():
    """测试无效配置"""
    print("\n🧪 测试无效配置...")
    
    invalid_configs = [
        {
            "name": "缺少必需字段",
            "config": {
                "enabled": True
                # 缺少其他必需字段
            }
        },
        {
            "name": "字段类型错误",
            "config": {
                "enabled": "not_a_boolean",  # 应该是布尔值
                "version": "3.0.0",
                "models": {},
                "query_processing": {},
                "engines": {},
                "performance": {}
            }
        },
        {
            "name": "值超出范围",
            "config": {
                "enabled": True,
                "version": "3.0.0",
                "models": {},
                "query_processing": {
                    "max_context_length": 500,  # 低于最小值1000
                    "max_results": 150,         # 超出最大值100
                    "relevance_threshold": 1.5  # 超出范围[0.0, 1.0]
                },
                "engines": {},
                "performance": {}
            }
        }
    ]
    
    validator = ConfigValidator()
    all_tests_passed = True
    
    for test_case in invalid_configs:
        print(f"\n  测试: {test_case['name']}")
        try:
            validator.validate_config(test_case['config'])
            print(f"    ❌ 应该失败但通过了验证")
            all_tests_passed = False
        except (ConfigurationError, ValidationError) as e:
            print(f"    ✅ 正确捕获到错误: {type(e).__name__}: {e}")
        except Exception as e:
            print(f"    ⚠️ 捕获到未知错误: {type(e).__name__}: {e}")
            all_tests_passed = False
    
    return all_tests_passed


def test_config_issues():
    """测试配置问题检测"""
    print("\n🧪 测试配置问题检测...")
    
    config_with_issues = {
        "enabled": True,
        "version": "3.0.0",
        "models": {},
        "query_processing": {
            "max_context_length": 500,  # 问题：低于最小值
            "max_results": 150,         # 问题：超出最大值
            "relevance_threshold": 1.5  # 问题：超出范围
        },
        "engines": {},
        "performance": {}
    }
    
    try:
        validator = ConfigValidator()
        
        # 获取配置问题
        issues = validator.get_config_issues(config_with_issues)
        print(f"✅ 检测到配置问题: {len(issues)} 个")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        
        # 获取修复建议
        suggestions = validator.suggest_config_fixes(config_with_issues)
        print(f"\n🔧 修复建议: {len(suggestions)} 个")
        for field, suggestion in suggestions.items():
            print(f"  {field}: {suggestion}")
        
        return True
    except Exception as e:
        print(f"❌ 配置问题检测失败: {e}")
        return False


def test_rag_config_validation():
    """测试RAG配置验证"""
    print("\n🧪 测试RAG配置验证...")
    
    rag_config = {
        "rag_system": {
            "enabled": True,
            "version": "3.0.0",
            "models": {
                "llm": {"model_name": "qwen-turbo"},
                "reranking": {"model_name": "gte-rerank-v2"}
            },
            "query_processing": {
                "max_context_length": 4000,
                "max_results": 10,
                "relevance_threshold": 0.5
            },
            "engines": {
                "text_engine": {"enabled": True, "similarity_threshold": 0.7},
                "image_engine": {"enabled": True, "similarity_threshold": 0.3},
                "table_engine": {"enabled": True, "similarity_threshold": 0.65}
            },
            "performance": {"max_concurrent_queries": 10}
        }
    }
    
    try:
        validator = ConfigValidator()
        result = validator.validate_rag_config(rag_config)
        print(f"✅ RAG配置验证通过: {result}")
        return True
    except Exception as e:
        print(f"❌ RAG配置验证失败: {e}")
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("🧪 RAG系统配置验证测试")
    print("=" * 60)
    
    # 运行各项测试
    tests = [
        ("有效配置验证", test_valid_config),
        ("无效配置验证", test_invalid_config),
        ("配置问题检测", test_config_issues),
        ("RAG配置验证", test_rag_config_validation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！配置验证器工作正常。")
    else:
        print("⚠️ 部分测试失败，需要检查问题。")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
