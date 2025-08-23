'''
程序说明：
## 1. 全面的表格信息检查程序
## 2. 分析向量数据库中的表格文档状态
## 3. 检查HTML内容、纯文本内容的分布
## 4. 提供详细的诊断报告
## 5. 帮助确认主程序修复是否生效

## 主要功能：
- 检查向量数据库中的表格文档数量
- 分析HTML内容和纯文本内容的分布
- 检查元数据字段的完整性
- 提供修复建议
'''

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import pickle

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TableInfoChecker:
    """
    表格信息检查器
    """
    
    def __init__(self, vector_db_path: str = None):
        """
        初始化表格信息检查器
        :param vector_db_path: 向量数据库路径
        """
        if vector_db_path:
            self.vector_db_path = Path(vector_db_path)
        else:
            # 使用默认路径
            self.vector_db_path = Path("central/vector_db")
        
        self.metadata_file = self.vector_db_path / "metadata.pkl"
        self.index_file = self.vector_db_path / "index.faiss"
        
    def check_vector_db_structure(self) -> Dict[str, Any]:
        """
        检查向量数据库结构
        :return: 数据库结构信息
        """
        result = {
            'vector_db_exists': False,
            'metadata_exists': False,
            'index_exists': False,
            'metadata_count': 0,
            'index_count': 0
        }
        
        try:
            # 检查目录是否存在
            if self.vector_db_path.exists():
                result['vector_db_exists'] = True
                logger.info(f"✅ 向量数据库目录存在: {self.vector_db_path}")
            else:
                logger.error(f"❌ 向量数据库目录不存在: {self.vector_db_path}")
                return result
            
            # 检查metadata.pkl文件
            if self.metadata_file.exists():
                result['metadata_exists'] = True
                try:
                    with open(self.metadata_file, 'rb') as f:
                        metadata = pickle.load(f)
                    result['metadata_count'] = len(metadata) if metadata else 0
                    logger.info(f"✅ metadata.pkl文件存在，包含 {result['metadata_count']} 个文档")
                except Exception as e:
                    logger.error(f"❌ 读取metadata.pkl失败: {e}")
            else:
                logger.error(f"❌ metadata.pkl文件不存在: {self.metadata_file}")
            
            # 检查index.faiss文件
            if self.index_file.exists():
                result['index_exists'] = True
                try:
                    import faiss
                    index = faiss.read_index(str(self.index_file))
                    result['index_count'] = index.ntotal
                    logger.info(f"✅ index.faiss文件存在，包含 {result['index_count']} 个向量")
                except Exception as e:
                    logger.error(f"❌ 读取index.faiss失败: {e}")
            else:
                logger.error(f"❌ index.faiss文件不存在: {self.index_file}")
            
            return result
            
        except Exception as e:
            logger.error(f"检查向量数据库结构失败: {e}")
            return result
    
    def analyze_table_documents(self) -> Dict[str, Any]:
        """
        分析表格文档
        :return: 表格文档分析结果
        """
        result = {
            'total_documents': 0,
            'table_documents': 0,
            'text_documents': 0,
            'other_documents': 0,
            'table_details': [],
            'html_content_stats': {
                'with_html': 0,
                'without_html': 0,
                'html_content_lengths': []
            },
            'text_content_stats': {
                'with_text': 0,
                'without_text': 0,
                'text_content_lengths': []
            }
        }
        
        try:
            if not self.metadata_file.exists():
                logger.error("metadata.pkl文件不存在，无法分析文档")
                return result
            
            # 加载元数据
            with open(self.metadata_file, 'rb') as f:
                metadata_list = pickle.load(f)
            
            if not metadata_list:
                logger.warning("metadata.pkl文件为空")
                return result
            
            result['total_documents'] = len(metadata_list)
            logger.info(f"开始分析 {result['total_documents']} 个文档...")
            
            for i, metadata in enumerate(metadata_list):
                try:
                    chunk_type = metadata.get('chunk_type', 'unknown')
                    
                    if chunk_type == 'table':
                        result['table_documents'] += 1
                        table_info = self._analyze_table_document(metadata, i)
                        result['table_details'].append(table_info)
                        
                        # 统计HTML内容
                        if table_info['has_html_content']:
                            result['html_content_stats']['with_html'] += 1
                            result['html_content_stats']['html_content_lengths'].append(table_info['html_content_length'])
                        else:
                            result['html_content_stats']['without_html'] += 1
                        
                        # 统计文本内容
                        if table_info['has_text_content']:
                            result['text_content_stats']['with_text'] += 1
                            result['text_content_stats']['text_content_lengths'].append(table_info['text_content_length'])
                        else:
                            result['text_content_stats']['without_text'] += 1
                            
                    elif chunk_type == 'text':
                        result['text_documents'] += 1
                    else:
                        result['other_documents'] += 1
                        
                except Exception as e:
                    logger.warning(f"分析文档 {i} 时出错: {e}")
                    continue
            
            return result
            
        except Exception as e:
            logger.error(f"分析表格文档失败: {e}")
            return result
    
    def _analyze_table_document(self, metadata: Dict[str, Any], doc_index: int) -> Dict[str, Any]:
        """
        分析单个表格文档
        :param metadata: 文档元数据
        :param doc_index: 文档索引
        :return: 表格文档详细信息
        """
        table_info = {
            'doc_index': doc_index,
            'document_name': metadata.get('document_name', '未知文档'),
            'page_number': metadata.get('page_number', 'N/A'),
            'table_id': metadata.get('table_id', 'unknown'),
            'table_type': metadata.get('table_type', '未知表格'),
            'has_html_content': False,
            'html_content_length': 0,
            'html_content_preview': '',
            'has_text_content': False,
            'text_content_length': 0,
            'text_content_preview': '',
            'metadata_fields': list(metadata.keys()),
            'issues': []
        }
        
        try:
            # 检查HTML内容
            html_content = metadata.get('page_content', '')
            if html_content and isinstance(html_content, str) and len(html_content.strip()) > 0:
                table_info['has_html_content'] = True
                table_info['html_content_length'] = len(html_content)
                table_info['html_content_preview'] = html_content[:200] + '...' if len(html_content) > 200 else html_content
            else:
                table_info['issues'].append('缺少HTML内容')
            
            # 检查文本内容
            text_content = metadata.get('processed_table_content', '')
            if text_content and isinstance(text_content, str) and len(text_content.strip()) > 0:
                table_info['has_text_content'] = True
                table_info['text_content_length'] = len(text_content)
                table_info['text_content_preview'] = text_content[:200] + '...' if len(text_content) > 200 else text_content
            else:
                table_info['issues'].append('缺少文本内容')
            
            # 检查其他重要字段
            if not metadata.get('table_id'):
                table_info['issues'].append('缺少table_id')
            if not metadata.get('table_type'):
                table_info['issues'].append('缺少table_type')
            
        except Exception as e:
            table_info['issues'].append(f'分析出错: {e}')
        
        return table_info
    
    def generate_report(self, structure_info: Dict[str, Any], analysis_info: Dict[str, Any]) -> str:
        """
        生成检查报告
        :param structure_info: 数据库结构信息
        :param analysis_info: 文档分析信息
        :return: 格式化的报告
        """
        report = []
        report.append("=" * 80)
        report.append("📊 表格信息检查报告")
        report.append("=" * 80)
        
        # 数据库结构信息
        report.append("\n🔍 数据库结构检查:")
        report.append(f"  ✅ 向量数据库目录: {'存在' if structure_info['vector_db_exists'] else '不存在'}")
        report.append(f"  ✅ metadata.pkl文件: {'存在' if structure_info['metadata_exists'] else '不存在'}")
        report.append(f"  ✅ index.faiss文件: {'存在' if structure_info['index_exists'] else '不存在'}")
        report.append(f"  📊 元数据文档数量: {structure_info['metadata_count']}")
        report.append(f"  📊 向量索引数量: {structure_info['index_count']}")
        
        # 文档类型统计
        report.append("\n📋 文档类型统计:")
        report.append(f"  📊 总文档数量: {analysis_info['total_documents']}")
        report.append(f"  📋 表格文档数量: {analysis_info['table_documents']}")
        report.append(f"  📝 文本文档数量: {analysis_info['text_documents']}")
        report.append(f"  🔍 其他文档数量: {analysis_info['other_documents']}")
        
        # HTML内容统计
        report.append("\n🌐 HTML内容统计:")
        report.append(f"  ✅ 有HTML内容的表格: {analysis_info['html_content_stats']['with_html']}")
        report.append(f"  ❌ 无HTML内容的表格: {analysis_info['html_content_stats']['without_html']}")
        
        if analysis_info['html_content_stats']['html_content_lengths']:
            avg_html_length = sum(analysis_info['html_content_stats']['html_content_lengths']) / len(analysis_info['html_content_stats']['html_content_lengths'])
            report.append(f"  📏 平均HTML内容长度: {avg_html_length:.0f} 字符")
        
        # 文本内容统计
        report.append("\n📝 文本内容统计:")
        report.append(f"  ✅ 有文本内容的表格: {analysis_info['text_content_stats']['with_text']}")
        report.append(f"  ❌ 无文本内容的表格: {analysis_info['text_content_stats']['without_text']}")
        
        if analysis_info['text_content_stats']['text_content_lengths']:
            avg_text_length = sum(analysis_info['text_content_stats']['text_content_lengths']) / len(analysis_info['text_content_stats']['text_content_lengths'])
            report.append(f"  📏 平均文本内容长度: {avg_text_length:.0f} 字符")
        
        # 问题分析
        if analysis_info['table_details']:
            report.append("\n⚠️ 问题分析:")
            issues_count = {}
            for table_info in analysis_info['table_details']:
                for issue in table_info['issues']:
                    issues_count[issue] = issues_count.get(issue, 0) + 1
            
            for issue, count in issues_count.items():
                report.append(f"  ❌ {issue}: {count} 个表格")
        
        # 修复建议
        report.append("\n💡 修复建议:")
        if analysis_info['html_content_stats']['without_html'] > 0:
            report.append("  1. 🔧 主程序已修复，但现有数据库中的表格文档仍缺少HTML内容")
            report.append("  2. 🚀 建议重新生成向量数据库，使用修复后的主程序")
            report.append("  3. 📝 命令: python V501_simplified_document_processor.py --mode markdown")
        else:
            report.append("  ✅ 所有表格文档都有HTML内容，无需修复")
        
        report.append("\n" + "=" * 80)
        return "\n".join(report)
    
    def save_detailed_analysis(self, analysis_info: Dict[str, Any], output_file: str = "table_analysis_detailed.json"):
        """
        保存详细分析结果到JSON文件
        :param analysis_info: 分析信息
        :param output_file: 输出文件名
        """
        try:
            # 准备要保存的数据（移除过长的内容预览）
            save_data = analysis_info.copy()
            for table_detail in save_data['table_details']:
                if len(table_detail['html_content_preview']) > 100:
                    table_detail['html_content_preview'] = table_detail['html_content_preview'][:100] + '...'
                if len(table_detail['text_content_preview']) > 100:
                    table_detail['text_content_preview'] = table_detail['text_content_preview'][:100] + '...'
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"详细分析结果已保存到: {output_file}")
            
        except Exception as e:
            logger.error(f"保存详细分析结果失败: {e}")


def main():
    """
    主函数
    """
    import argparse
    
    # 创建参数解析器
    parser = argparse.ArgumentParser(description='表格信息检查程序')
    parser.add_argument('--vector-db', type=str, help='向量数据库路径（可选）')
    args = parser.parse_args()
    
    print("🔍 开始检查表格信息...")
    
    # 创建检查器
    checker = TableInfoChecker(args.vector_db)
    
    # 检查数据库结构
    print("\n1️⃣ 检查向量数据库结构...")
    structure_info = checker.check_vector_db_structure()
    
    if not structure_info['vector_db_exists']:
        print("❌ 向量数据库不存在，请先创建向量数据库")
        return
    
    # 分析表格文档
    print("\n2️⃣ 分析表格文档...")
    analysis_info = checker.analyze_table_documents()
    
    # 生成报告
    print("\n3️⃣ 生成检查报告...")
    report = checker.generate_report(structure_info, analysis_info)
    print(report)
    
    # 保存详细分析结果
    if analysis_info['table_documents'] > 0:
        print("\n4️⃣ 保存详细分析结果...")
        checker.save_detailed_analysis(analysis_info)
    
    print("\n✅ 表格信息检查完成！")


if __name__ == "__main__":
    main()
