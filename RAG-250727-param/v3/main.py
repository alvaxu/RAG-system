#!/usr/bin/env python3
"""
V3版本向量数据库构建系统主程序

主程序入口，负责解析命令行参数并启动相应的处理流程。
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# 修复导入路径问题
# 获取main.py文件所在的目录（v3目录）
v3_dir = Path(__file__).parent
# 将v3目录添加到Python路径中
sys.path.insert(0, str(v3_dir))

from db_system.core.v3_main_processor import V3MainProcessor
from config.config_manager import ConfigManager

def setup_logging(log_level: str = "INFO"):
    """设置日志配置"""
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"无效的日志级别: {log_level}")

    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('./logs/v3_processing.log', encoding='utf-8')
        ]
    )

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='V3版本向量数据库构建系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 默认方式：从PDF开始处理，使用配置默认路径
  python main.py

  # 明确指定从PDF开始处理
  python main.py --input-type pdf

  # 从minerU输出开始处理
  python main.py --input-type mineru_output

  # 指定自定义路径
  python main.py --input-type pdf --input-path ./custom_pdf_dir --output-path ./custom_vector_db

  # 查看详细日志
  python main.py --log-level DEBUG
        """
    )

    # 输入类型参数
    parser.add_argument(
        '--input-type',
        choices=['pdf', 'mineru_output'],
        default='pdf',
        help='输入类型：pdf（从PDF开始）或mineru_output（从minerU输出开始）'
    )

    # 路径参数
    parser.add_argument(
        '--input-path',
        help='输入路径，如果不指定则使用配置默认值'
    )

    parser.add_argument(
        '--output-path',
        help='输出路径（向量数据库路径），如果不指定则使用配置默认值'
    )

    parser.add_argument(
        '--config-path',
        help='配置文件路径，如果不指定则使用默认路径'
    )

    # 日志参数
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='日志级别（默认：INFO）'
    )

    # 其他参数
    parser.add_argument(
        '--version',
        action='version',
        version='V3版本向量数据库构建系统 v3.0.0',
        help='显示版本信息'
    )
    
    # 补做检查参数
    parser.add_argument(
        '--check-completion',
        action='store_true',
        help='检查并询问是否进行图片增强和向量化补做'
    )
    
    # 数据库诊断参数
    parser.add_argument(
        '--diagnose-db',
        action='store_true',
        help='输出数据库结构和内容分析'
    )

    return parser.parse_args()

def validate_environment():
    """验证运行环境"""
    print("🔍 验证运行环境...")

    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 错误：需要Python 3.8或更高版本")
        print(f"   当前版本: {sys.version}")
        return False

    print("✅ Python版本检查通过")
    # 检查必要的环境变量
    required_vars = ['DASHSCOPE_API_KEY']
    missing_vars = []

    for var in required_vars:
        import os
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print("❌ 错误：缺少必要的环境变量:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n请设置以下环境变量：")
        print("   Windows:")
        for var in missing_vars:
            print(f"   set {var}=your_api_key_here")
        return False

    print("✅ 环境变量检查通过")
    return True

def main():
    """主函数"""
    try:
        # 解析命令行参数
        args = parse_arguments()

        # 设置日志
        setup_logging(args.log_level)

        # 显示程序信息
        print("=" * 60)
        print("           V3版本向量数据库构建系统")
        print("=" * 60)
        print(f"输入类型: {args.input_type}")
        print(f"日志级别: {args.log_level}")

        if args.input_path:
            print(f"输入路径: {args.input_path}")
        if args.output_path:
            print(f"输出路径: {args.output_path}")
        if args.config_path:
            print(f"配置文件: {args.config_path}")

        # 验证环境
        if not validate_environment():
            sys.exit(1)

        # 初始化主处理器
        print("\n🏗️  初始化系统...")
        processor = V3MainProcessor(args.config_path)

        # 如果是数据库诊断模式，跳过文档处理
        if args.diagnose_db:
            print("\n🔍 数据库诊断模式，跳过文档处理...")
            result = {'success': True, 'mode': 'diagnostic_only'}
        else:
            # 处理文档
            print("\n🚀 开始处理文档...")
            result = processor.process_documents(
                input_type=args.input_type,
                input_path=args.input_path,
                output_path=args.output_path
            )

            # 显示结果
            print("\n" + "=" * 60)
            if result.get('success'):
                print("✅ 处理完成！")
                print(f"处理模式: {result.get('mode', 'unknown')}")
                # 显示目标数据库信息
                storage_path = result.get('storage_path', 'unknown')
                if storage_path != 'unknown':
                    # 提取数据库名称，去掉路径前缀
                    db_name = os.path.basename(storage_path)
                    if db_name == 'vector_db':
                        db_name = 'central/vector_db'
                    print(f"目标数据库: {db_name}")
                else:
                    print("目标数据库: 未指定")

                # 显示统计信息
                stats = result.get('processing_stats', {})
                if stats:
                    print("\n📊 处理统计:")
                    for key, value in stats.items():
                        print(f"   {key}: {value}")

            else:
                print("❌ 处理失败！")
                print(f"错误信息: {result.get('error', '未知错误')}")

                # 显示详细错误信息
                if 'validation_result' in result:
                    validation = result['validation_result']
                    if not validation.get('valid'):
                        print(f"验证错误: {validation.get('message', '未知验证错误')}")


            print("=" * 60)
        
        # 补做检查（如果指定了参数）
        if args.check_completion and result.get('success'):
            print("\n🔍 开始补做检查...")
            try:
                from db_system.utils.image_completion import ImageCompletion
                completion_tool = ImageCompletion(args.config_path)
                completion_tool.run_completion_check()
            except Exception as e:
                print(f"⚠️  补做检查失败: {e}")
        
        # 数据库诊断（如果指定了参数）
        if args.diagnose_db:
            print("\n🔍 开始数据库诊断...")
            try:
                from db_system.utils.db_diagnostic_tool import DatabaseDiagnosticTool
                diagnostic_tool = DatabaseDiagnosticTool(args.config_path)
                
                # 询问是否使用交互式模式
                print("\n🎯 选择诊断模式:")
                print("1. 📋 运行完整诊断（传统模式）")
                print("2. 🎮 交互式诊断模式（新功能）")
                
                try:
                    mode_choice = input("请选择 (1/2): ").strip()
                    if mode_choice == '2':
                        print("\n🚀 启动交互式诊断模式...")
                        diagnostic_tool.run_interactive_mode()
                    else:
                        print("\n📋 运行完整诊断...")
                        diagnostic_tool.run_diagnostic()
                except KeyboardInterrupt:
                    print("\n👋 用户中断，使用默认模式")
                    diagnostic_tool.run_diagnostic()
                except:
                    print("\n📋 使用默认模式运行完整诊断...")
                    diagnostic_tool.run_diagnostic()
                    
            except Exception as e:
                print(f"⚠️  数据库诊断失败: {e}")
                import traceback
                traceback.print_exc()

        # 返回适当的退出码
        sys.exit(0 if result.get('success') else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断处理")
        sys.exit(130)

    except Exception as e:
        print(f"\n❌ 程序执行出错: {e}")
        logging.error("程序执行出错", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
