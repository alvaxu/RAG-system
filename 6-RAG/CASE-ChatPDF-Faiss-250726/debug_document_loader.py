'''
调试脚本，用于检查文档加载问题
'''

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
root_path = Path(__file__).parent
sys.path.append(str(root_path))

from V100_document_loader_chunker import DocumentLoader, process_documents


def debug_document_loader():
    """
    调试文档加载器
    """
    print("调试文档加载器...")
    
    # 检查md目录是否存在
    md_dir = root_path / "md"
    if not md_dir.exists():
        print(f"错误: md目录不存在: {md_dir}")
        return
    
    print(f"md目录存在: {md_dir}")
    
    # 列出md目录中的文件
    md_files = list(md_dir.glob("*.md"))
    json_files = list(md_dir.glob("*_1.json"))
    
    print(f"找到 {len(md_files)} 个markdown文件")
    print(f"找到 {len(json_files)} 个JSON文件")
    
    # 显示前几个文件作为示例
    print("\n前5个markdown文件:")
    for i, file in enumerate(md_files[:5]):
        print(f"  {i+1}. {file.name}")
        
    print("\n前5个JSON文件:")
    for i, file in enumerate(json_files[:5]):
        print(f"  {i+1}. {file.name}")
    
    # 测试文档加载器
    print("\n测试文档加载器...")
    loader = DocumentLoader("md")
    documents = loader.load_documents()
    print(f"加载了 {len(documents)} 个文档")
    
    # 显示加载的文档信息
    if documents:
        print("\n加载的文档信息:")
        for i, doc in enumerate(documents[:3]):  # 只显示前3个
            print(f"  文档 {i+1}: {doc['name']}")
            print(f"    Markdown内容长度: {len(doc.get('md_content', ''))}")
            print(f"    JSON数据项数: {len(doc.get('json_data', []))}")
    else:
        print("没有加载到任何文档")
        
        # 检查具体文件是否存在
        print("\n检查文件匹配情况:")
        for md_file in md_files[:10]:  # 检查前10个文件
            doc_name = md_file.stem
            json_file = md_file.with_name(f"{doc_name}_1.json")
            exists = "存在" if json_file.exists() else "不存在"
            print(f"  {doc_name}.md -> {doc_name}_1.json ({exists})")


def debug_process_documents():
    """
    调试文档处理函数
    """
    print("\n调试文档处理函数...")
    chunks = process_documents('md')
    print(f'共生成 {len(chunks)} 个文档分块')
    
    if chunks:
        print("\n前3个分块示例:")
        for i, chunk in enumerate(chunks[:3]):
            print(f"  分块 {i+1}:")
            print(f"    文档名: {chunk.document_name}")
            print(f"    页码: {chunk.page_number}")
            print(f"    内容长度: {len(chunk.content)}")
            print(f"    内容预览: {chunk.content[:100]}...")


if __name__ == "__main__":
    debug_document_loader()
    debug_process_documents()