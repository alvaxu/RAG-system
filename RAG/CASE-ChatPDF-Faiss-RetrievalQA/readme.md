# 1 如果检索器设了score_threshold，就会出现docs返回空值,任何问题的回答都是不知道。这个问题花了我1整天还多的时间才弄明白。cursor一直在和我搞query和input的键的问题。
```
retriever = vector_store.as_retriever(search_kwargs={'k': 5,'score_threshold': 0.65})  # 如果设了score_threshold，就会出现docs返回空值
docs = retriever.invoke("客服经理的职责是什么")  # 或 get_relevant_documents()
docs

```
```
[]
```
 

 # 2 用RetrievalQA.from_chain_type 建QA链
```python
     # 构建问答链
    qa_chain = RetrievalQA.from_chain_type(
       llm=llm,  # 控制生成稳定性
       chain_type="stuff",
       chain_type_kwargs={
       "prompt": QA_PROMPT,
#       "document_variable_name": "context"  # 必须与模板变量名一致，context 的值是自动从检索器（retriever）获取并注入到 prompt 
        },
       retriever=vector_store.as_retriever(
#            search_kwargs={"k": 5, "score_threshold": 0.65}  # 如果设了score_threshold，就会出现docs返回空值
           search_kwargs={"k": 5}  # 控制检索质量
        ),
       # input_key="query",  # 显式声明输入键名
       # document_variable_name="context",  # 明确指定文档变量名
       return_source_documents=True
    )
```
# 3 调用qa_chain的invoke来回答问题
 
 
 answer = qa_chain.invoke({"query":question})