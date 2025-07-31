'''
程序说明：
## 1. 该模块实现了基于FAISS向量存储的RAG问答系统，修复了文档索引计算错误的问题
## 2. 相比V301版本，主要改进了文档元数据的存储和检索方式，确保文档引用的准确性
## 3. 通过在向量存储中直接关联文档标识符和元数据，避免了索引计算错误导致的文档引用问题
'''

import os
import pickle
import time
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.llms import Tongyi
from langchain.chains.question_answering import load_qa_chain
from langchain.callbacks import get_openai_callback

# 添加项目根目录到Python路径
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入文档分块数据结构
from V100_document_loader_chunker import DocumentChunk


class VectorStoreManager:
    """
    向量存储管理器类，用于创建和加载FAISS向量数据库
    """
    
    def __init__(self, api_key: str):
        """
        初始化向量存储管理器
        :param api_key: DashScope API密钥
        """
        self.embeddings = DashScopeEmbeddings(
            model="text-embedding-v1",
            dashscope_api_key=api_key,
        )
    
    def create_vector_store(self, chunks: List[DocumentChunk], save_path: str = None) -> FAISS:
        """
        从文档分块创建向量存储
        :param chunks: 文档分块列表
        :param save_path: 可选，保存向量数据库的路径
        :return: FAISS向量存储对象
        """
        # 提取文档分块的内容
        texts = [chunk.content for chunk in chunks]
        
        # 从文本创建向量存储
        vector_store = FAISS.from_texts(texts, self.embeddings)
        
        # 存储额外的元数据（文档名、页码等）
        # 修改：使用文档内容的哈希值作为唯一标识符，确保索引准确性
        metadata = {}
        for i, chunk in enumerate(chunks):
            # 使用文档内容和文档名的组合作为唯一标识符
            identifier = f"{hash(chunk.content)}_{chunk.document_name}_{chunk.page_number}"
            metadata[identifier] = {
                'document_name': chunk.document_name,
                'page_number': chunk.page_number,
                'chunk_index': chunk.chunk_index,
                'content': chunk.content  # 添加内容用于匹配验证
            }
        vector_store.metadata = metadata
        
        # 如果提供了保存路径，则保存向量数据库
        if save_path:
            # 确保目录存在
            os.makedirs(save_path, exist_ok=True)
            
            # 保存FAISS向量数据库
            vector_store.save_local(save_path)
            
            # 保存元数据到同一目录
            with open(os.path.join(save_path, "metadata.pkl"), "wb") as f:
                pickle.dump(metadata, f)
        
        return vector_store
    
    def load_vector_store(self, load_path: str) -> FAISS:
        """
        从磁盘加载向量数据库和元数据
        :param load_path: 向量数据库的保存路径
        :return: 加载的FAISS向量数据库对象
        """
        # 加载FAISS向量数据库
        # 尝试使用不同的加载方法
        try:
            vector_store = FAISS.load_local(load_path, self.embeddings, allow_dangerous_deserialization=True, index_name="index")
        except Exception as e:
            # 如果使用index_name加载失败，则尝试不指定index_name加载
            try:
                vector_store = FAISS.load_local(load_path, self.embeddings, allow_dangerous_deserialization=True)
            except Exception as e2:
                # 重新抛出最后一个异常
                raise e2
        
        # 加载元数据
        metadata_path = os.path.join(load_path, "metadata.pkl")
        if os.path.exists(metadata_path):
            with open(metadata_path, "rb") as f:
                metadata = pickle.load(f)
            vector_store.metadata = metadata
        
        return vector_store


class QuestionAnsweringSystem:
    """
    问答系统类，用于基于向量存储进行问答
    """
    
    def __init__(self, vector_store: FAISS, api_key: str):
        """
        初始化问答系统
        :param vector_store: FAISS向量存储对象
        :param api_key: DashScope API密钥
        """
        self.vector_store = vector_store
        self.api_key = api_key
        
        # 初始化语言模型
        self.llm = Tongyi(
            model_name="qwen-turbo", 
            dashscope_api_key=api_key
        )
        
        # 加载问答链
        self.qa_chain = load_qa_chain(self.llm, chain_type="stuff")
    
    def answer_question(self, question: str, k: int = 10) -> Dict[str, Any]:
        """
        回答问题
        :param question: 用户问题
        :param k: 检索的相似文档数量
        :return: 包含答案和相关信息的字典
        """
        # 执行相似度搜索
        docs = self.vector_store.similarity_search(question, k=k)
        
        # 准备输入数据
        input_data = {"input_documents": docs, "question": question}
        
        # 使用回调函数跟踪API调用成本
        with get_openai_callback() as cost:
            # 执行问答链
            start_time = time.time()
            response = self.qa_chain.invoke(input=input_data)
            end_time = time.time()
            
            # 提取答案
            answer = response["output_text"]
            
            # 收集来源信息
            sources = []
            unique_sources = set()
            
            # 修改：使用文档内容匹配来查找正确的元数据
            for doc in docs:
                # 通过匹配文档内容来查找对应的元数据
                found_metadata = None
                for identifier, metadata in self.vector_store.metadata.items():
                    # 检查内容是否匹配
                    if metadata['content'] == doc.page_content:
                        found_metadata = metadata
                        break
                
                if found_metadata:
                    source_key = (found_metadata['document_name'], found_metadata['page_number'])
                    
                    if source_key not in unique_sources:
                        unique_sources.add(source_key)
                        sources.append({
                            'document_name': found_metadata['document_name'],
                            'page_number': found_metadata['page_number'],
                            'content': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                        })
                else:
                    # 如果找不到匹配的元数据，则使用默认值
                    sources.append({
                        'document_name': 'Unknown',
                        'page_number': 0,
                        'content': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                    })
            
            return {
                'question': question,
                'answer': answer,
                'sources': sources,
                'processing_time': end_time - start_time,
                'cost': cost.total_cost,
                'retrieved_documents': len(docs)
            }


def create_vector_store_from_documents(md_dir: str = "md", api_key: str = "", save_path: str = "./vector_db", chunks: List[DocumentChunk] = None) -> FAISS:
    """
    从文档创建向量存储的主函数
    :param md_dir: markdown文件目录路径
    :param api_key: DashScope API密钥
    :param save_path: 保存向量数据库的路径
    :param chunks: 可选的预处理文档分块列表
    :return: FAISS向量存储对象
    """
    # 如果没有提供预处理的chunks，则处理文档分块
    if chunks is None:
        # 导入文档处理函数
        from V100_document_loader_chunker import process_documents
        chunks = process_documents(md_dir)
    
    # 创建向量存储管理器
    vector_manager = VectorStoreManager(api_key)
    
    # 创建向量存储
    vector_store = vector_manager.create_vector_store(chunks, save_path)
    
    return vector_store


def load_vector_store_and_answer_questions(vector_db_path: str = "./vector_db", api_key: str = ""):
    """
    加载向量存储并启动问答交互
    :param vector_db_path: 向量数据库路径
    :param api_key: DashScope API密钥
    """
    # 创建向量存储管理器
    vector_manager = VectorStoreManager(api_key)
    
    # 加载向量存储
    vector_store = vector_manager.load_vector_store(vector_db_path)
    
    # 创建问答系统
    qa_system = QuestionAnsweringSystem(vector_store, api_key)
    
    while True:
        question = input("\n请输入您的问题: ").strip()
        
        if question.lower() == 'quit':
            print("感谢使用问答系统！")
            break
        
        if not question:
            print("请输入有效问题。")
            continue
        
        # 回答问题
        result = qa_system.answer_question(question)
        
        # 显示答案
        print(f"\n问题: {result['question']}")
        print(f"答案: {result['answer']}")
        
        # 显示来源
        print("\n相关信息来源:")
        for i, source in enumerate(result['sources'], 1):
            print(f"{i}. 文档: {source['document_name']}, 页码: {source['page_number']}")
            print(f"   内容: {source['content']}")


# 调试和测试代码
if __name__ == "__main__":
    # 加载环境变量
    load_dotenv()
    
    # 从环境变量中获取API密钥
    DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY', '你的APIKEY')
    
    # 从文档创建向量存储
    vector_store = create_vector_store_from_documents("md", DASHSCOPE_API_KEY)
    
    # 保存路径
    save_path = "./vector_db"
    
    # 加载向量存储并启动问答交互
    # load_vector_store_and_answer_questions(save_path, DASHSCOPE_API_KEY)