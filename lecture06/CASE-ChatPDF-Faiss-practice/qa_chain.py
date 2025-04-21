"""
问答处理模块
"""
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_community.llms import Tongyi
from langchain.prompts import ChatPromptTemplate
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
        
        # 创建提示模板
        prompt = ChatPromptTemplate.from_template("""
        基于以下上下文回答问题。如果无法从上下文中得到答案，请说明。

        上下文：
        {context}

        问题：{input}

        回答：""")
        
        # 创建文档链
        self.document_chain = create_stuff_documents_chain(
            llm=self.llm,
            prompt=prompt
        )
        
        # 创建检索链
        self.retrieval_chain = create_retrieval_chain(
            self.vector_store.vector_store.as_retriever(),
            self.document_chain
        )

    def generate_answer(self, question: str) -> Tuple[str, List[Dict]]:
        """
        生成回答
        """
        # 使用检索链生成回答
        result = self.retrieval_chain.invoke({"input": question})
        
        # 获取回答和来源
        answer = result["answer"]
        sources = [doc.metadata for doc in result["context"]]
        
        return answer, sources 