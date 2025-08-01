'''
程序说明：
## 1. 新增文档处理全流程执行程序
## 2. 使用优化后的AddDocumentProcessor处理新增PDF文档
## 3. 支持临时处理目录，最终迁移到原有目录结构
## 4. 重用现有的DocumentProcessingPipeline和底层组件
## 5. 确保metadata记录正确的值，保持和原来一样的处理逻辑
## 6. 实现真正的增量更新，避免重建向量数据库
'''

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from config.settings import Settings
from document_processing.add_document_processor import AddDocumentProcessor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """
    新增文档处理主程序
    """
    print("=" * 80)
    print("新增文档处理全流程执行程序")
    print("=" * 80)
    
    try:
        # 步骤1: 加载配置
        print("\n📋 步骤1: 加载配置")
        print("-" * 50)
        
        config = Settings.load_from_file('config.json')
        print("✓ 配置加载成功")
        
        # 检查必要的路径配置
        required_paths = [
            'add_pdf_dir',
            'temp_processing_dir',
            'temp_markdown_dir',
            'temp_json_dir',
            'temp_zip_dir',
            'temp_images_dir',
            'pdf_dir',
            'md_dir',
            'images_dir',
            'vector_db_dir'
        ]
        
        for path_name in required_paths:
            path_value = getattr(config, path_name, None)
            if path_value:
                print(f"✓ {path_name}: {path_value}")
            else:
                print(f"✗ {path_name}: 未配置")
                return False
        
        # 步骤2: 创建新增文档处理器
        print("\n🔧 步骤2: 创建新增文档处理器")
        print("-" * 50)
        
        processor = AddDocumentProcessor(config)
        print("✓ 新增文档处理器创建成功")
        
        # 步骤3: 检查新增PDF文件
        print("\n📄 步骤3: 检查新增PDF文件")
        print("-" * 50)
        
        pdf_files = processor.get_new_pdf_files()
        if not pdf_files:
            print("ℹ 没有找到新增PDF文件")
            print(f"请将PDF文件放入目录: {config.add_pdf_dir}")
            return False
        
        print(f"✓ 找到 {len(pdf_files)} 个新增PDF文件:")
        for pdf_file in pdf_files:
            print(f"  - {pdf_file}")
        
        # 步骤4: 创建临时目录
        print("\n📁 步骤4: 创建临时目录")
        print("-" * 50)
        
        success = processor.create_temp_directories()
        if not success:
            print("✗ 临时目录创建失败")
            return False
        
        print("✓ 临时目录创建成功")
        
        # 步骤5: 处理新增PDF文档
        print("\n⚙️ 步骤5: 处理新增PDF文档")
        print("-" * 50)
        
        processing_result = processor.process_add_documents()
        
        if processing_result.get('success'):
            print("✓ 新增文档处理成功")
            print(f"  处理的PDF文件数量: {processing_result.get('processed_pdfs', 0)}")
            print(f"  迁移的文件数量: {processing_result.get('total_migrated_files', 0)}")
            print(f"  向量数据库更新: {'成功' if processing_result.get('vector_db_updated', False) else '失败'}")
            
            # 显示详细结果
            if 'processed_files' in processing_result:
                print("\n📊 处理详情:")
                for file_info in processing_result['processed_files']:
                    pdf_name = file_info.get('pdf_name', '未知')
                    migrated_count = len(file_info.get('migrated_files', []))
                    print(f"  - {pdf_name}: 迁移了 {migrated_count} 个文件")
        else:
            print("✗ 新增文档处理失败")
            if 'errors' in processing_result:
                for error in processing_result['errors']:
                    print(f"  - 错误: {error}")
            return False
        
        # 步骤6: 清理临时目录
        print("\n🧹 步骤6: 清理临时目录")
        print("-" * 50)
        
        cleanup_success = processor.cleanup_temp_directories()
        if cleanup_success:
            print("✓ 临时目录清理成功")
        else:
            print("⚠ 临时目录清理失败，但不影响处理结果")
        
        # 步骤7: 显示处理状态
        print("\n📈 步骤7: 处理状态总结")
        print("-" * 50)
        
        status = processor.get_processing_status()
        for step, completed in status.items():
            status_icon = "✓" if completed else "✗"
            status_text = "完成" if completed else "未完成"
            print(f"{status_icon} {step}: {status_text}")
        
        # 最终总结
        print("\n" + "=" * 80)
        print("🎉 新增文档处理全流程执行完成！")
        print("=" * 80)
        
        print("\n📋 处理结果总结:")
        print(f"  - 处理的PDF文件: {len(pdf_files)} 个")
        print(f"  - 处理状态: {'成功' if processing_result.get('success') else '失败'}")
        print(f"  - 向量数据库: {'已更新' if processing_result.get('vector_db_updated') else '未更新'}")
        
        print("\n📁 文件位置:")
        print(f"  - 原始PDF文件: {config.pdf_dir}")
        print(f"  - Markdown文件: {config.md_dir}")
        print(f"  - 图片文件: {config.images_dir}")
        print(f"  - 向量数据库: {config.vector_db_dir}")
        
        print("\n🚀 下一步操作:")
        print("1. 检查处理后的文件是否正确")
        print("2. 验证向量数据库是否包含新文档")
        print("3. 测试问答功能是否正常工作")
        
        return True
        
    except Exception as e:
        logger.error(f"新增文档处理失败: {e}")
        print(f"\n❌ 处理过程中发生错误: {e}")
        return False


if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ 程序执行成功！")
    else:
        print("\n❌ 程序执行失败！")
        sys.exit(1) 