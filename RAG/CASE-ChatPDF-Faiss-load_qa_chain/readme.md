# 1 用load_qa_chain来创建qa链
```python
    qa_chain = load_qa_chain(
        llm=llm,
        chain_type="stuff",
    )
```

# 2 直接接使用检索器获取相关文档，验证可以查出相关文档来

docs = vector_store.similarity_search(question, k=6)

# 3 用qa_chain.run来从docs中找到答案。
```python
#生成回答
result = qa_chain.run(
    input_documents=docs, 
    question=question,
)
```