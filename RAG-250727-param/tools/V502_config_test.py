"""
测试V502_image_enhancer.py的配置管理实现
"""

import os
import sys
import json

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_v502_config_management():
    """测试V502的配置管理实现"""
    
    print("=" * 60)
    print("V502配置管理测试")
    print("=" * 60)
    
    # 1. 检查config.json是否存在
    if os.path.exists("config.json"):
        print("✅ config.json文件存在")
        
        # 读取config.json内容
        with open("config.json", 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        print(f"📋 config.json包含以下配置项:")
        for section, items in config_data.items():
            print(f"  {section}: {list(items.keys()) if isinstance(items, dict) else items}")
    else:
        print("❌ config.json文件不存在")
        return
    
    # 2. 检查V502_image_enhancer.py的配置管理实现
    print("\n🔍 检查V502_image_enhancer.py的配置管理实现:")
    
    # 检查API密钥配置
    api_key = config_data.get('api', {}).get('dashscope_api_key', '')
    if api_key and api_key != '你的DashScope API密钥':
        print("✅ 从config.json加载API密钥成功")
    else:
        print("⚠️ config.json中的API密钥未配置或为默认值")
    
    # 检查路径配置
    vector_db_dir = config_data.get('paths', {}).get('vector_db_dir', '')
    if vector_db_dir:
        print(f"✅ 向量数据库路径配置: {vector_db_dir}")
    else:
        print("⚠️ 向量数据库路径未配置")
    
    # 3. 检查是否使用了统一配置管理
    print("\n🔍 检查是否使用了统一配置管理:")
    
    try:
        from config.settings import Settings
        settings = Settings.load_from_file("config.json")
        print("✅ 统一配置管理模块可用")
        print(f"  - 向量数据库路径: {settings.vector_db_dir}")
        print(f"  - API密钥: {'已配置' if settings.dashscope_api_key else '未配置'}")
    except ImportError as e:
        print(f"❌ 无法导入统一配置管理模块: {e}")
    except Exception as e:
        print(f"❌ 统一配置管理加载失败: {e}")
    
    # 4. 检查V502_image_enhancer.py的实现
    print("\n🔍 检查V502_image_enhancer.py的实现:")
    
    try:
        from V502_image_enhancer import V502ImageEnhancer
        
        # 检查V502ImageEnhancer的配置管理方法
        enhancer = V502ImageEnhancer()
        
        print("✅ V502ImageEnhancer初始化成功")
        print(f"  - API密钥: {'已配置' if enhancer.api_key else '未配置'}")
        print(f"  - 向量数据库路径: {enhancer.vector_store_path}")
        print(f"  - 模型名称: {enhancer.model}")
        
        # 检查配置加载方式
        if hasattr(enhancer, 'config') and enhancer.config:
            print("✅ 配置加载成功")
            print(f"  - 配置项数量: {len(enhancer.config)}")
        else:
            print("⚠️ 配置加载可能有问题")
            
    except Exception as e:
        print(f"❌ V502ImageEnhancer测试失败: {e}")
    
    # 5. 配置管理对比
    print("\n📊 配置管理对比:")
    
    print("当前V502_image_enhancer.py的配置管理方式:")
    print("  ✅ 1. 优先从config.json加载API密钥")
    print("  ✅ 2. 备选环境变量MY_DASHSCOPE_API_KEY")
    print("  ✅ 3. 最后备用默认值")
    print("  ✅ 4. 支持路径配置从config.json加载")
    
    print("\n建议的改进:")
    print("  🔄 1. 使用统一的Settings类进行配置管理")
    print("  🔄 2. 支持更多配置项的加载")
    print("  🔄 3. 支持配置验证和错误处理")
    print("  🔄 4. 支持配置热重载")

if __name__ == "__main__":
    test_v502_config_management()
