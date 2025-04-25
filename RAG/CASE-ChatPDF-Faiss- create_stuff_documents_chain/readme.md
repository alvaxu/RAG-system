# 1 
创建document_chain
```python
    document_chain = create_stuff_documents_chain(
        llm=llm,
        prompt=prompt,
        document_variable_name="context"  # 明确指定文档变量名
    )
```
# 2 用similarity_search找相似答案
   docs = vector_store.similarity_search(question, k=6)

# 3 用document_chain.invoke来回答问题
```python
        answer = document_chain.invoke({
            "input": question,
            "context": docs
```