'''
程序说明：
## 1. 检查表格处理的具体情况
## 2. 分析成功和失败的表格
## 3. 为重新处理失败的表格做准备
'''

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from document_processing.vector_generator import VectorGenerator
from config.settings import Settings
import pickle
from pathlib import Path

def main():
    """主函数"""
    try:
        # 加载配置
        config = Settings.load_from_file('config.json')
        vg = VectorGenerator(config.to_dict())
        
        # 加载向量数据库
        vs = vg.load_vector_store('./central/vector_db')
        if not vs:
            print("❌ 无法加载向量数据库")
            return
        
        # 获取统计信息
        stats = vg.get_vector_store_statistics(vs)
        
        print("="*60)
        print("表格处理详细分析")
        print("="*60)
        
        # 检查表格统计
        if stats['table_types']:
            print(f"表格类型分布:")
            for table_type, count in stats['table_types'].items():
                print(f"  {table_type}: {count}")
        
        # 检查metadata.pkl文件
        metadata_file = Path("central/vector_db/metadata.pkl")
        if metadata_file.exists():
            with open(metadata_file, 'rb') as f:
                metadata = pickle.load(f)
            
            print(f"\n元数据文件包含 {len(metadata)} 个条目")
            
            # 统计表格类型的条目
            table_entries = [m for m in metadata if m.get('chunk_type') == 'table']
            print(f"表格条目数: {len(table_entries)}")
            
            # 显示表格信息
            print("\n表格条目详情:")
            for i, entry in enumerate(table_entries):
                print(f"  {i+1}. 文档: {entry.get('document_name', 'unknown')}")
                print(f"     页码: {entry.get('page_number', 'unknown')}")
                print(f"     表格类型: {entry.get('table_type', '未知表格')}")
                print(f"     内容长度: {len(entry.get('content', ''))} 字符")
                print(f"     来源: {entry.get('source', 'unknown')}")
                print()
        
        # 检查类型分布
        if stats['type_distribution']:
            print("\n类型分布:")
            for chunk_type, count in stats['type_distribution'].items():
                print(f"  {chunk_type}: {count}")
        
        # 分析表格处理情况
        total_docs = stats['total_documents']
        table_docs = stats['type_distribution'].get('table', 0)
        text_docs = stats['type_distribution'].get('text', 0)
        image_docs = stats['type_distribution'].get('image', 0)
        
        print(f"\n表格处理分析:")
        print(f"总文档数: {total_docs}")
        print(f"文本分块: {text_docs}")
        print(f"表格分块: {table_docs}")
        print(f"图片分块: {image_docs}")
        
        # 计算增量添加的内容
        # 原始数据库应该有43个条目（38个文档+5张图片）
        original_count = 43
        incremental_count = total_docs - original_count
        
        print(f"\n增量添加的内容:")
        print(f"  原始条目数: {original_count}")
        print(f"  当前条目数: {total_docs}")
        print(f"  增量添加数: {incremental_count}")
        
        # 分析表格添加情况
        if table_docs > 0:
            # 从日志中我们知道有17个表格分块
            expected_tables = 17
            successful_tables = table_docs
            failed_tables = expected_tables - successful_tables
            
            print(f"\n表格添加情况:")
            print(f"  预期处理表格: {expected_tables}")
            print(f"  成功添加表格: {successful_tables}")
            print(f"  失败表格数: {failed_tables}")
            
            if failed_tables > 0:
                print(f"  失败原因: 需要进一步分析")
        
        # 检查表格内容质量
        if 'table_entries' in locals() and table_entries:
            print(f"\n表格内容质量分析:")
            empty_tables = 0
            short_tables = 0
            normal_tables = 0
            
            for entry in table_entries:
                content = entry.get('content', '')
                content_length = len(content)
                
                if content_length == 0:
                    empty_tables += 1
                elif content_length < 50:
                    short_tables += 1
                else:
                    normal_tables += 1
            
            print(f"  空表格: {empty_tables}")
            print(f"  短表格(<50字符): {short_tables}")
            print(f"  正常表格: {normal_tables}")
        
        print("="*60)
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")

if __name__ == "__main__":
    main() 