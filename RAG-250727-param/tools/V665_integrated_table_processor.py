"""
程序说明：

## 1. 集成表格处理器 - 替换原有简单截断处理
## 2. 与现有系统无缝集成，保持API兼容性
## 3. 智能处理表格内容，提升数据质量
"""

import json
import re
import os
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import logging
from datetime import datetime

# 导入智能表格处理器
from V665_smart_table_processor import SmartTableProcessor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntegratedTableProcessor:
    """
    集成表格处理器
    替换原有的简单截断处理，提供智能表格处理能力
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化集成表格处理器
        
        :param config: 配置参数
        """
        self.config = config or {}
        self.smart_processor = SmartTableProcessor()
        self.processing_stats = {
            'total_tables': 0,
            'successful_processing': 0,
            'failed_processing': 0,
            'processing_time': 0.0
        }
        
    def process_document_tables(self, document_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        处理文档中的所有表格
        
        :param document_data: 文档数据列表
        :return: 处理后的文档数据
        """
        start_time = datetime.now()
        
        try:
            processed_document = []
            
            for item in document_data:
                if item.get('type') == 'table':
                    # 处理表格类型
                    processed_item = self._process_table_item(item)
                    self.processing_stats['total_tables'] += 1
                    
                    if 'error' not in processed_item:
                        self.processing_stats['successful_processing'] += 1
                    else:
                        self.processing_stats['failed_processing'] += 1
                        
                else:
                    # 保持非表格项目不变
                    processed_item = item
                
                processed_document.append(processed_item)
            
            # 计算处理时间
            end_time = datetime.now()
            self.processing_stats['processing_time'] = (end_time - start_time).total_seconds()
            
            logger.info(f"表格处理完成: 总计 {self.processing_stats['total_tables']} 个表格")
            logger.info(f"成功处理: {self.processing_stats['successful_processing']} 个")
            logger.info(f"处理失败: {self.processing_stats['failed_processing']} 个")
            logger.info(f"总耗时: {self.processing_stats['processing_time']:.2f} 秒")
            
            return processed_document
            
        except Exception as e:
            logger.error(f"文档表格处理失败: {e}")
            return document_data
    
    def _process_table_item(self, table_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理单个表格项目
        
        :param table_item: 表格项目数据
        :return: 处理后的表格项目
        """
        try:
            # 获取表格内容
            table_body = table_item.get('table_body', '')
            table_caption = table_item.get('table_caption', [])
            table_footnote = table_item.get('table_footnote', [])
            
            if not table_body:
                return {
                    **table_item,
                    'error': '表格内容为空',
                    'processing_status': 'failed'
                }
            
            # 使用智能处理器处理表格内容
            processed_result = self.smart_processor.process_table_content(table_body)
            
            # 构建处理后的表格项目
            processed_table = {
                **table_item,
                'processed_table_data': processed_result,
                'processing_status': 'success' if 'error' not in processed_result else 'failed',
                'processing_timestamp': datetime.now().isoformat()
            }
            
            # 如果处理成功，添加智能摘要
            if 'error' not in processed_result:
                processed_table['smart_summary'] = self._generate_smart_summary(processed_result, table_caption)
            
            return processed_table
            
        except Exception as e:
            logger.error(f"表格项目处理失败: {e}")
            return {
                **table_item,
                'error': str(e),
                'processing_status': 'failed',
                'processing_timestamp': datetime.now().isoformat()
            }
    
    def _generate_smart_summary(self, processed_result: Dict[str, Any], caption: List[str]) -> Dict[str, Any]:
        """
        生成智能表格摘要
        
        :param processed_result: 处理结果
        :param caption: 表格标题
        :return: 智能摘要
        """
        summary = {
            'table_type': 'unknown',
            'key_insights': [],
            'data_quality': 'unknown',
            'recommendations': []
        }
        
        try:
            # 根据处理结果生成摘要
            if 'table_data' in processed_result:
                table_data = processed_result['table_data']
                
                # 确定表格类型
                if 'type' in table_data:
                    summary['table_type'] = table_data['type']
                
                # 生成关键洞察
                if 'key_metrics' in table_data:
                    summary['key_insights'].extend(table_data['key_metrics'][:3])  # 取前3个关键指标
                
                # 评估数据质量
                if 'structure' in table_data:
                    structure = table_data['structure']
                    if structure.get('row_count', 0) > 0 and structure.get('column_count', 0) > 0:
                        summary['data_quality'] = 'good'
                    else:
                        summary['data_quality'] = 'poor'
                
                # 生成建议
                if summary['data_quality'] == 'poor':
                    summary['recommendations'].append('表格结构不完整，建议检查数据源')
                elif summary['table_type'] == 'financial_table':
                    summary['recommendations'].append('财务数据表格，建议关注关键指标趋势')
                elif summary['table_type'] == 'time_series_table':
                    summary['recommendations'].append('时间序列数据，建议分析周期性变化')
            
        except Exception as e:
            logger.error(f"生成智能摘要失败: {e}")
            summary['error'] = str(e)
        
        return summary
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """
        获取处理统计信息
        
        :return: 处理统计信息
        """
        return {
            **self.processing_stats,
            'success_rate': (
                self.processing_stats['successful_processing'] / 
                max(self.processing_stats['total_tables'], 1) * 100
            ),
            'average_processing_time': (
                self.processing_stats['processing_time'] / 
                max(self.processing_stats['total_tables'], 1)
            )
        }
    
    def export_processing_report(self, output_path: str) -> bool:
        """
        导出处理报告
        
        :param output_path: 输出路径
        :return: 是否成功导出
        """
        try:
            report = {
                'processing_summary': self.get_processing_statistics(),
                'timestamp': datetime.now().isoformat(),
                'processor_version': 'V665_Integrated_Table_Processor_v1.0',
                'config': self.config
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"处理报告已导出到: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"导出处理报告失败: {e}")
            return False

def process_single_document(file_path: str, output_path: Optional[str] = None) -> bool:
    """
    处理单个文档文件
    
    :param file_path: 文档文件路径
    :param output_path: 输出文件路径（可选）
    :return: 是否处理成功
    """
    try:
        # 读取文档
        with open(file_path, 'r', encoding='utf-8') as f:
            document_data = json.load(f)
        
        # 创建处理器
        processor = IntegratedTableProcessor()
        
        # 处理表格
        processed_document = processor.process_document_tables(document_data)
        
        # 保存结果
        if output_path is None:
            output_path = file_path.replace('.json', '_processed.json')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(processed_document, f, ensure_ascii=False, indent=2)
        
        # 导出处理报告
        report_path = output_path.replace('.json', '_report.json')
        processor.export_processing_report(report_path)
        
        # 打印统计信息
        stats = processor.get_processing_statistics()
        print(f"\n=== 表格处理完成 ===")
        print(f"总表格数: {stats['total_tables']}")
        print(f"成功处理: {stats['successful_processing']}")
        print(f"处理失败: {stats['failed_processing']}")
        print(f"成功率: {stats['success_rate']:.1f}%")
        print(f"总耗时: {stats['processing_time']:.2f} 秒")
        print(f"平均处理时间: {stats['average_processing_time']:.3f} 秒/表格")
        
        return True
        
    except Exception as e:
        logger.error(f"处理文档失败: {e}")
        return False

def batch_process_documents(input_dir: str, output_dir: Optional[str] = None) -> bool:
    """
    批量处理文档目录
    
    :param input_dir: 输入目录
    :param output_dir: 输出目录（可选）
    :return: 是否处理成功
    """
    try:
        input_path = Path(input_dir)
        if output_dir is None:
            output_path = input_path.parent / f"{input_path.name}_processed"
        else:
            output_path = Path(output_dir)
        
        output_path.mkdir(exist_ok=True)
        
        # 查找所有JSON文件
        json_files = list(input_path.glob("*.json"))
        
        if not json_files:
            logger.warning(f"在目录 {input_dir} 中未找到JSON文件")
            return False
        
        logger.info(f"找到 {len(json_files)} 个JSON文件，开始批量处理...")
        
        success_count = 0
        for json_file in json_files:
            try:
                output_file = output_path / f"{json_file.stem}_processed.json"
                if process_single_document(str(json_file), str(output_file)):
                    success_count += 1
                    logger.info(f"成功处理: {json_file.name}")
                else:
                    logger.error(f"处理失败: {json_file.name}")
            except Exception as e:
                logger.error(f"处理文件 {json_file.name} 时出错: {e}")
        
        logger.info(f"批量处理完成: {success_count}/{len(json_files)} 个文件处理成功")
        return success_count > 0
        
    except Exception as e:
        logger.error(f"批量处理失败: {e}")
        return False

if __name__ == "__main__":
    # 示例用法
    print("=== 集成表格处理器测试 ===")
    
    # 测试单个文档处理
    test_file = "document/add_md/【光大证券】中芯国际2025年一季度业绩点评：1Q突发生产问题，2Q业绩有望筑底，自主可控趋势不改_1.json"
    
    if os.path.exists(test_file):
        print(f"测试处理文件: {test_file}")
        success = process_single_document(test_file)
        if success:
            print("✅ 文档处理成功")
        else:
            print("❌ 文档处理失败")
    else:
        print(f"测试文件不存在: {test_file}")
    
    # 测试批量处理
    print("\n=== 测试批量处理 ===")
    test_dir = "document/add_md"
    if os.path.exists(test_dir):
        print(f"测试批量处理目录: {test_dir}")
        success = batch_process_documents(test_dir)
        if success:
            print("✅ 批量处理成功")
        else:
            print("❌ 批量处理失败")
    else:
        print(f"测试目录不存在: {test_dir}")
