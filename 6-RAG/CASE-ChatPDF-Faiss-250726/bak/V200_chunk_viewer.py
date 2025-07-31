'''
程序说明：
## 1. 该模块用于查看和分析文档分块结果
## 2. 可以显示每个分块的详细信息，包括文档名、页码和内容
## 3. 便于调试和验证分块效果
'''

from V100_document_loader_chunker import process_documents


def view_chunks():
    """
    查看文档分块结果
    """
    print("正在处理文档分块...")
    chunks = process_documents("md")
    
    print(f"\n总共生成 {len(chunks)} 个分块\n")
    
    # 显示所有分块的详细信息
    for i, chunk in enumerate(chunks):
        print(f"=== 分块 {i+1} ===")
        print(f"文档名: {chunk.document_name}")
        print(f"页码: {chunk.page_number}")
        print(f"索引: {chunk.chunk_index}")
        print(f"内容 (前200字符): {chunk.content[:200]}...")
        print("-" * 50)


def save_chunks_to_file():
    """
    将分块结果保存到文件中
    """
    chunks = process_documents("md")
    
    with open("document_chunks.txt", "w", encoding="utf-8") as f:
        f.write(f"总共生成 {len(chunks)} 个分块\n\n")
        
        for i, chunk in enumerate(chunks):
            f.write(f"=== 分块 {i+1} ===\n")
            f.write(f"文档名: {chunk.document_name}\n")
            f.write(f"页码: {chunk.page_number}\n")
            f.write(f"索引: {chunk.chunk_index}\n")
            f.write(f"内容:\n{chunk.content}\n")
            f.write("-" * 50 + "\n\n")
    
    print("分块结果已保存到 document_chunks.txt 文件中")


if __name__ == "__main__":
    # 查看分块结果
    view_chunks()
    
    # 保存分块结果到文件
    save_chunks_to_file()