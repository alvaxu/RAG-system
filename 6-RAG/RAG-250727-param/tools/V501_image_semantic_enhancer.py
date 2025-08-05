'''
程序说明：
## 1. V501图片语义增强主程序 - 调用document_processing中的增强功能
## 2. 为现有向量数据库中的图片生成更丰富的语义描述
## 3. 提供友好的命令行界面和进度显示
## 4. 支持配置管理和结果统计
## 5. 安全的数据处理和备份机制
'''

import sys
import os
import logging
import json
from pathlib import Path
from typing import Dict, Any

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入配置和功能模块
from config.settings import Settings
from document_processing.image_semantic_enhancer import ImageSemanticEnhancer, EnhancementResult

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config() -> Dict[str, Any]:
    """
    加载配置
    
    :return: 配置字典
    """
    try:
        config = Settings.load_from_file('config.json')
        
        # 构建增强器配置
        enhancer_config = {
            'dashscope_api_key': config.dashscope_api_key,
            'max_retries': 3,
            'retry_delay': 2,
            'batch_size': 10,
            'backup_enabled': True
        }
        
        logger.info("配置加载成功")
        return enhancer_config
        
    except Exception as e:
        logger.error(f"加载配置失败: {e}")
        raise


def display_banner():
    """显示程序横幅"""
    print("="*80)
    print("🔍 V501图片语义增强主程序")
    print("="*80)
    print("功能：为向量数据库中的图片生成更丰富的语义描述")
    print("基于：ONE-PEACE多模态模型")
    print("="*80)


def get_user_confirmation() -> bool:
    """
    获取用户确认
    
    :return: 用户是否确认继续
    """
    print("\n⚠️  重要提示：")
    print("1. 此操作将修改向量数据库中的图片元数据")
    print("2. 建议在操作前备份重要数据")
    print("3. 程序会自动创建备份，但建议手动备份")
    print("4. 处理时间取决于图片数量和网络状况")
    
    while True:
        choice = input("\n是否继续执行图片语义增强？(y/n): ").strip().lower()
        if choice in ['y', 'yes', '是']:
            return True
        elif choice in ['n', 'no', '否']:
            return False
        else:
            print("请输入 y 或 n")


def get_enhancement_options() -> Dict[str, Any]:
    """
    获取增强选项
    
    :return: 增强选项字典
    """
    print("\n🔧 增强选项配置：")
    
    # 批处理大小
    while True:
        try:
            batch_size = input("批处理大小 (默认10): ").strip()
            if not batch_size:
                batch_size = 10
            else:
                batch_size = int(batch_size)
            if batch_size > 0:
                break
            else:
                print("批处理大小必须大于0")
        except ValueError:
            print("请输入有效的数字")
    
    # 是否启用备份
    backup_choice = input("是否启用自动备份？(y/n, 默认y): ").strip().lower()
    backup_enabled = backup_choice not in ['n', 'no', '否']
    
    return {
        'batch_size': batch_size,
        'backup_enabled': backup_enabled
    }


def display_progress(current: int, total: int, message: str = ""):
    """
    显示进度
    
    :param current: 当前进度
    :param total: 总数
    :param message: 消息
    """
    percentage = (current / total * 100) if total > 0 else 0
    bar_length = 30
    filled_length = int(bar_length * current // total)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    
    print(f"\r📊 进度: [{bar}] {percentage:.1f}% ({current}/{total}) {message}", end='', flush=True)


def display_result(result: EnhancementResult):
    """
    显示增强结果
    
    :param result: 增强结果
    """
    print("\n" + "="*80)
    print("📊 图片语义增强结果统计")
    print("="*80)
    
    print(f"📈 总图片数: {result.total_images}")
    print(f"✅ 成功增强: {result.enhanced_images}")
    print(f"❌ 处理失败: {result.failed_images}")
    print(f"⏱️  处理时间: {result.processing_time:.2f}秒")
    
    if result.backup_path:
        print(f"💾 备份路径: {result.backup_path}")
    
    success_rate = (result.enhanced_images / result.total_images * 100) if result.total_images > 0 else 0
    print(f"📊 成功率: {success_rate:.1f}%")
    
    if result.enhanced_descriptions:
        print(f"\n📝 增强描述示例:")
        for i, desc in enumerate(result.enhanced_descriptions[:3], 1):
            print(f"   {i}. {desc.get('document_name', '未知文档')}")
            print(f"      原始: {desc.get('original_description', '无')}")
            print(f"      增强: {desc.get('enhanced_description', '无')}")
            print()
    
    print("="*80)


def save_result_to_file(result: EnhancementResult, output_file: str = "enhancement_result.json"):
    """
    保存结果到文件
    
    :param result: 增强结果
    :param output_file: 输出文件名
    """
    try:
        # 转换为可序列化的格式
        serializable_result = {
            'total_images': result.total_images,
            'enhanced_images': result.enhanced_images,
            'failed_images': result.failed_images,
            'backup_path': result.backup_path,
            'processing_time': result.processing_time,
            'success_rate': (result.enhanced_images / result.total_images * 100) if result.total_images > 0 else 0,
            'enhanced_descriptions': []
        }
        
        # 添加增强描述（限制数量避免文件过大）
        for desc in result.enhanced_descriptions[:10]:
            serializable_desc = {
                'doc_id': str(desc.get('doc_id', '')),
                'image_path': desc.get('image_path', ''),
                'document_name': desc.get('document_name', ''),
                'original_description': desc.get('original_description', ''),
                'enhanced_description': desc.get('enhanced_description', ''),
                'semantic_description': desc.get('semantic_description', '')
            }
            serializable_result['enhanced_descriptions'].append(serializable_desc)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_result, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 结果已保存到: {output_file}")
        
    except Exception as e:
        logger.error(f"保存结果失败: {e}")
        print(f"❌ 保存结果失败: {e}")


def main():
    """主函数"""
    try:
        # 显示横幅
        display_banner()
        
        # 加载配置
        print("\n📋 正在加载配置...")
        config = load_config()
        
        # 检查API密钥
        if not config.get('dashscope_api_key'):
            print("❌ 错误：未配置DashScope API密钥")
            print("请在config.json中配置dashscope_api_key")
            return
        
        # 获取向量数据库路径
        vector_db_path = "./central/vector_db"
        if not os.path.exists(vector_db_path):
            print(f"❌ 错误：向量数据库路径不存在: {vector_db_path}")
            print("请确保向量数据库已正确生成")
            return
        
        print(f"📁 向量数据库路径: {vector_db_path}")
        
        # 获取用户确认
        if not get_user_confirmation():
            print("❌ 用户取消操作")
            return
        
        # 获取增强选项
        options = get_enhancement_options()
        print(f"\n🔧 配置确认:")
        print(f"   批处理大小: {options['batch_size']}")
        print(f"   自动备份: {'启用' if options['backup_enabled'] else '禁用'}")
        
        # 创建增强器
        print("\n🚀 正在初始化图片语义增强器...")
        enhancer = ImageSemanticEnhancer(config)
        
        # 执行增强
        print("\n🔄 开始执行图片语义增强...")
        print("注意：处理时间取决于图片数量和网络状况，请耐心等待...")
        
        result = enhancer.enhance_vector_store_images(
            vector_store_path=vector_db_path,
            backup_enabled=options['backup_enabled'],
            batch_size=options['batch_size']
        )
        
        # 显示结果
        display_result(result)
        
        # 询问是否保存结果
        save_choice = input("\n是否保存详细结果到文件？(y/n): ").strip().lower()
        if save_choice in ['y', 'yes', '是']:
            output_file = input("请输入文件名 (默认: enhancement_result.json): ").strip()
            if not output_file:
                output_file = "enhancement_result.json"
            save_result_to_file(result, output_file)
        
        print("\n✅ 图片语义增强完成！")
        
        # 提供后续建议
        if result.enhanced_images > 0:
            print("\n💡 建议：")
            print("1. 可以使用V607_view_image_descriptions.py查看增强后的图片描述")
            print("2. 测试问答系统，验证语义增强效果")
            print("3. 如有问题，可以使用备份恢复原始数据")
        
    except KeyboardInterrupt:
        print("\n\n❌ 用户中断操作")
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        print(f"\n❌ 程序执行失败: {e}")
        print("请检查配置和网络连接")


if __name__ == "__main__":
    main() 