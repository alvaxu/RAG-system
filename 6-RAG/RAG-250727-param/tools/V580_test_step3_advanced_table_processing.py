'''
程序说明：
## 1. 测试步骤3的文档分块是否完成了高级表格处理
## 2. 检查enhanced_chunker.py中的高级表格处理功能
## 3. 验证表格是否被转换为结构化文本
## 4. 对比处理前后的表格内容
'''

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入配置管理
from config import ConfigManager
# 导入文档处理管道
from document_processing import DocumentProcessingPipeline

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Step3TableProcessingTester:
    """
    步骤3表格处理测试器
    """
    
    def __init__(self, config_file: str = None):
        """
        初始化测试器
        :param config_file: 配置文件路径
        """
        self.config_manager = ConfigManager(config_file)
        self.pipeline = DocumentProcessingPipeline(self.config_manager.get_config_for_processing())
    
    def test_step3_advanced_table_processing(self) -> bool:
        """
        测试步骤3的高级表格处理
        :return: 是否成功
        """
        try:
            logger.info("开始测试步骤3的高级表格处理...")
            
            # 获取Markdown文件
            md_dir = self.config_manager.settings.md_dir
            md_files = list(Path(md_dir).glob("*.md"))
            md_files = [str(f) for f in md_files]
            
            if not md_files:
                logger.error("没有找到Markdown文件")
                return False
            
            logger.info(f"找到 {len(md_files)} 个Markdown文件")
            
            # 执行步骤3：文档分块
            logger.info("执行步骤3：文档分块处理...")
            chunks = self.pipeline.document_chunker.process_documents(md_files)
            
            if not chunks:
                logger.error("文档分块失败")
                return False
            
            logger.info(f"生成了 {len(chunks)} 个分块")
            
            # 分析表格分块
            table_chunks = [c for c in chunks if c.metadata.get('chunk_type') == 'table']
            text_chunks = [c for c in chunks if c.metadata.get('chunk_type') == 'text']
            
            logger.info(f"  - 文本分块: {len(text_chunks)} 个")
            logger.info(f"  - 表格分块: {len(table_chunks)} 个")
            
            if not table_chunks:
                logger.warning("没有找到表格分块")
                return True
            
            # 详细分析表格分块
            logger.info("\n=== 表格分块详细分析 ===")
            
            for i, chunk in enumerate(table_chunks):
                logger.info(f"\n表格分块 {i+1}:")
                logger.info(f"  - 文档名称: {chunk.metadata.get('document_name', 'unknown')}")
                logger.info(f"  - 页码: {chunk.metadata.get('page_number', 'unknown')}")
                logger.info(f"  - 表格ID: {chunk.metadata.get('table_id', 'unknown')}")
                logger.info(f"  - 表格类型: {chunk.metadata.get('table_type', 'unknown')}")
                logger.info(f"  - 分块索引: {chunk.metadata.get('chunk_index', 'unknown')}")
                
                # 检查内容是否经过高级处理
                content = chunk.page_content
                logger.info(f"  - 内容长度: {len(content)} 字符")
                
                # 检查是否包含结构化文本特征
                advanced_features = self._check_advanced_processing_features(content)
                logger.info(f"  - 高级处理特征: {advanced_features}")
                
                # 显示内容的前200个字符
                preview = content[:200] + "..." if len(content) > 200 else content
                logger.info(f"  - 内容预览: {preview}")
                
                # 检查是否包含表格结构信息
                if "表格类型:" in content or "表格结构说明:" in content or "数据记录:" in content:
                    logger.info("  ✅ 确认：已进行高级表格处理")
                else:
                    logger.warning("  ⚠️  警告：可能未进行高级表格处理")
            
            # 统计高级处理情况
            advanced_processed = 0
            for chunk in table_chunks:
                content = chunk.page_content
                if "表格类型:" in content or "表格结构说明:" in content or "数据记录:" in content:
                    advanced_processed += 1
            
            logger.info(f"\n=== 高级处理统计 ===")
            logger.info(f"总表格分块数: {len(table_chunks)}")
            logger.info(f"高级处理表格数: {advanced_processed}")
            logger.info(f"高级处理比例: {advanced_processed/len(table_chunks)*100:.1f}%")
            
            if advanced_processed == len(table_chunks):
                logger.info("✅ 所有表格分块都经过了高级处理")
                return True
            elif advanced_processed > 0:
                logger.warning(f"⚠️  部分表格分块经过了高级处理 ({advanced_processed}/{len(table_chunks)})")
                return True
            else:
                logger.error("❌ 没有表格分块经过高级处理")
                return False
                
        except Exception as e:
            logger.error(f"测试过程中发生错误: {e}")
            return False
    
    def _check_advanced_processing_features(self, content: str) -> List[str]:
        """
        检查内容中的高级处理特征
        :param content: 内容
        :return: 特征列表
        """
        features = []
        
        if "表格类型:" in content:
            features.append("表格类型标识")
        
        if "表格结构说明:" in content:
            features.append("表格结构说明")
        
        if "数据记录:" in content:
            features.append("数据记录结构化")
        
        if "列标题（字段定义）:" in content:
            features.append("字段定义")
        
        if "表格结构总结:" in content:
            features.append("结构总结")
        
        if "原始表格内容:" in content:
            features.append("原始内容保留")
        
        if "=" in content and ":" in content:
            features.append("键值对格式")
        
        return features
    
    def test_enhanced_chunker_directly(self) -> bool:
        """
        直接测试enhanced_chunker的高级表格处理
        :return: 是否成功
        """
        try:
            logger.info("\n=== 直接测试enhanced_chunker ===")
            
            from document_processing.enhanced_chunker import process_documents_with_tables
            
            md_dir = self.config_manager.settings.md_dir
            chunk_size = self.config_manager.settings.chunk_size
            chunk_overlap = self.config_manager.settings.chunk_overlap
            
            logger.info(f"使用参数: chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
            
            # 直接调用enhanced_chunker
            enhanced_chunks = process_documents_with_tables(
                md_dir=md_dir,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            if not enhanced_chunks:
                logger.error("enhanced_chunker处理失败")
                return False
            
            logger.info(f"enhanced_chunker生成了 {len(enhanced_chunks)} 个分块")
            
            # 分析表格分块
            table_chunks = [c for c in enhanced_chunks if c.chunk_type == 'table']
            text_chunks = [c for c in enhanced_chunks if c.chunk_type == 'text']
            
            logger.info(f"  - 文本分块: {len(text_chunks)} 个")
            logger.info(f"  - 表格分块: {len(table_chunks)} 个")
            
            if not table_chunks:
                logger.warning("enhanced_chunker没有找到表格分块")
                return True
            
            # 检查表格分块的高级处理
            advanced_processed = 0
            for chunk in table_chunks:
                content = chunk.content
                if "表格类型:" in content or "表格结构说明:" in content or "数据记录:" in content:
                    advanced_processed += 1
                    logger.info(f"✅ 表格 {chunk.table_id} 已高级处理")
                else:
                    logger.warning(f"⚠️  表格 {chunk.table_id} 可能未高级处理")
            
            logger.info(f"enhanced_chunker高级处理比例: {advanced_processed}/{len(table_chunks)}")
            
            return advanced_processed > 0
            
        except Exception as e:
            logger.error(f"直接测试enhanced_chunker失败: {e}")
            return False


def main():
    """
    主函数
    """
    try:
        # 创建测试器
        tester = Step3TableProcessingTester()
        
        # 测试步骤3的表格处理
        success1 = tester.test_step3_advanced_table_processing()
        
        # 直接测试enhanced_chunker
        success2 = tester.test_enhanced_chunker_directly()
        
        # 总结结果
        print("\n" + "="*60)
        print("步骤3高级表格处理测试结果")
        print("="*60)
        
        if success1 and success2:
            print("✅ 测试通过：步骤3已完成高级表格处理")
        elif success2:
            print("⚠️  部分通过：enhanced_chunker有高级处理，但步骤3可能有问题")
        else:
            print("❌ 测试失败：高级表格处理可能有问题")
        
        print("="*60)
        
        return success1 and success2
        
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        print(f"\n❌ 程序执行失败: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 