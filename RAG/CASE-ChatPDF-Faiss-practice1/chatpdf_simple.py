"""
ChatPDF 简化版本
使用 LangChain 标准组件实现 PDF 文档问答系统
"""
import os
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import create_qa_with_sources_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain.prompts import PromptTemplate
from langchain_community.llms import Tongyi
from typing import List, Dict, Tuple

# 配置参数
CHUNK_SIZE = 1000  # 分块大小
CHUNK_OVERLAP = 200  # 重叠
EMBEDDING_MODEL = "text-embedding-v1"
LLM_MODEL = "qwen-turbo"
DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')

if not DASHSCOPE_API_KEY:
    raise ValueError("请设置 DASHSCOPE_API_KEY 环境变量")

def process_pdf(pdf_path: str) -> Tuple[List[str], List[Dict]]:
    """
    处理PDF文件，返回文本块和元数据
    """
    # 读取PDF
    reader = PdfReader(pdf_path)
    
    # 收集所有页面的文本和位置信息
    all_text = []
    page_positions = []  # 记录每个字符属于哪一页
    
    for page_num, page in enumerate(reader.pages, 1):
        page_text = page.extract_text()
        if not page_text:
            continue
            
        # 清理文本
        page_text = page_text.replace("百度文库", "").replace("好好学习，天天向上", "").strip()
        
        # 记录当前页面的所有字符位置
        for _ in range(len(page_text)):
            page_positions.append(page_num)
            
        all_text.append(page_text)
    
    # 合并所有文本
    full_text = "".join(all_text)
    
    # 使用LangChain的文本分割器
    text_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""],  # 添加中文标点
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        is_separator_regex=False
    )
    
    # 分割文本
    chunks = text_splitter.split_text(full_text)
    
    # 为每个文本块创建元数据
    chunk_metadata = []
    for chunk in chunks:
        # 找到这个chunk在原始文本中的位置
        start_pos = full_text.find(chunk)
        if start_pos == -1:
            # 如果找不到精确匹配，使用第一个字符的位置
            start_pos = 0
            
        # 获取这个chunk的起始页码
        start_page = page_positions[start_pos] if start_pos < len(page_positions) else 1
        
        # 获取这个chunk的结束页码
        end_pos = start_pos + len(chunk)
        end_page = page_positions[min(end_pos, len(page_positions)-1)] if end_pos < len(page_positions) else start_page
        
        # 如果chunk跨越了多页，使用起始页码
        chunk_metadata.append({
            "page": start_page,
            "source": pdf_path
        })
    
    return chunks, chunk_metadata

def create_vector_store(texts: List[str], metadata: List[Dict]):
    """
    创建向量存储
    """
    # 创建embeddings
    embeddings = DashScopeEmbeddings(
        model=EMBEDDING_MODEL,
        dashscope_api_key=DASHSCOPE_API_KEY
    )
    
    # 创建向量存储
    vector_store = FAISS.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadata
    )
    # print(vector_store)
    return vector_store

def create_qa_chain(vector_store):
    """
    创建问答链
    """
    # 创建LLM
    llm = Tongyi(
        model_name=LLM_MODEL,
        temperature=0.7,
        dashscope_api_key=DASHSCOPE_API_KEY
    )
    
    # 创建提示模板
    prompt = PromptTemplate.from_template(
        """你是一个专业的文档问答助手。请根据提供的上下文来回答问题。
如果上下文中包含问题的答案，请直接回答。
如果上下文中没有相关信息，请明确回答"不知道"。

上下文：
{context}

问题：{input}

请仔细分析上下文，确保答案准确。回答："""
    )
    
    # 创建文档链
    document_chain = create_stuff_documents_chain(
        llm=llm,
        prompt=prompt,
        document_variable_name="context"  # 明确指定文档变量名
    )
    
    return document_chain, vector_store

def main():
    # 处理PDF
    pdf_path = './浦发上海浦东发展银行西安分行个金客户经理考核办法.pdf'
    texts, metadata = process_pdf(pdf_path)
    
    print(f"\n处理完成，共生成 {len(texts)} 个文本块")
    # print("文本块示例：")
    # for i, text in enumerate(texts[:2]):  # 显示前两个文本块
    #     print(f"\n文本块 {i+1}:")
    #     print(text[:200] + "..." if len(text) > 200 else text)
    
    # 创建向量存储
    vector_store = create_vector_store(texts, metadata)
    
    # 创建问答链
    qa_chain, vector_store = create_qa_chain(vector_store)
    
    # 问答循环
    print("\n系统已准备就绪，可以开始提问了。输入'退出'结束对话。")
    while True:
        question = input("\n请输入问题：")
        if question.lower() == '退出':
            break
            
        # 直接使用检索器获取相关文档
        docs = vector_store.similarity_search(question, k=6)
        print(f"\n检索到的文档数量：{len(docs)}")
        if docs:
            print("检索到的文档内容：")
            for doc in docs:
                print(f"- {doc.page_content[:200]}...")
        
            # 生成回答
            answer = qa_chain.invoke({
                "input": question,
                "context": docs
            })
            
            # 输出结果
            print("\n回答：")
            print(answer)  # 直接打印返回的字符串
            
            # 显示来源
            print("\n来源：")
            for doc in docs:
                print(f"- 页码：{doc.metadata.get('page', '未知')}, 来源：{doc.metadata.get('source', '未知')}")
                print(f"  内容：{doc.page_content[:50]}...")  # 显示文档内容的前50个字符
        else:
            print("\n未找到相关文档。")

if __name__ == "__main__":
    main() 