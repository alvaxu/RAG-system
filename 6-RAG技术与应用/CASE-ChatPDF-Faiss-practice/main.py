"""
主程序入口
"""
import os
from pdf_processor import PDFProcessor
from vector_store import VectorStore
from qa_chain import QAChat

def main():
    # 初始化组件
    pdf_processor = PDFProcessor()
    vector_store = VectorStore()
    
    # 处理PDF
    pdf_path = input("请输入PDF文件路径：")
    texts, metadata = pdf_processor.process_pdf(pdf_path)
    
    # 存储到向量数据库
    vector_store.add_vectors(texts, metadata)
    
    # 初始化问答系统
    qa_chat = QAChat(vector_store)
    
    # 问答循环
    print("\n系统已准备就绪，可以开始提问了。输入'退出'结束对话。")
    while True:
        question = input("\n请输入问题：")
        if question.lower() == '退出':
            break
            
        # 生成回答
        answer, sources = qa_chat.generate_answer(question)
        
        # 输出结果
        print("\n回答：")
        print(answer)
        print("\n来源：")
        print(sources)
        """
        [{'page': 5, 'source': '浦发上海浦东发展银行西安分行个金客户经理考核办法.pdf'}, {'page': 8, 'source': '浦发上海浦东发展银行西安分行个金客户经理考核办法.pdf'}, {'page': 9, 'source': '浦发上海浦东发展银行西安分行个金客户经理考核办法.pdf'}, {'page': 6, 'source': '浦发上海浦东发展银行西安分行个金客户经理考核办法.pdf'}]
        """
        for source in sources:
            print(f"- 页码：{source.get('page', '未知')}, 来源：{source.get('source', '未知')}")

if __name__ == "__main__":
    main() 