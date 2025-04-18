"""
问答处理模块
"""
from langchain.chains.question_answering import load_qa_chain
from langchain_community.llms import Tongyi
from typing import List, Dict, Tuple
from config import LLM_MODEL, DASHSCOPE_API_KEY

class QAChat:
    """
    功能：处理用户问题，生成回答
    """
    def __init__(self, vector_store, model_name: str = LLM_MODEL):
        self.llm = Tongyi(
            model_name=model_name,
            temperature=0.7,
            dashscope_api_key=DASHSCOPE_API_KEY
        )
        self.vector_store = vector_store
        self.qa_chain = load_qa_chain(
            llm=self.llm,
            chain_type="stuff"
        )

    def generate_answer(self, question: str) -> Tuple[str, List[Dict]]:
        """
        生成回答
        """
        # 获取相关文档
        docs = self.vector_store.vector_store.similarity_search(question)
        
        # 生成回答
        result = self.qa_chain.run(input_documents=docs, question=question)
        
        # 获取来源
        sources = [doc.metadata for doc in docs]
        
        return result, sources 