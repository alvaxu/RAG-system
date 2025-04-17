# ChatPDF-Faiss 系统说明文档

## 1. 系统概述

ChatPDF-Faiss 是一个基于 LangChain 和 OpenAI 的 PDF 文档问答系统。该系统能够读取 PDF 文件，提取文本内容，并使用向量数据库（FAISS）构建知识库，从而实现对 PDF 文档内容的智能问答功能。系统还能够追踪回答来源的页码，提供参考信息。

## 2. 系统架构

系统主要由以下几个部分组成：

1. **PDF 文本提取模块**：使用 PyPDF2 库从 PDF 文件中提取文本内容，并记录每行文本对应的页码。
2. **文本处理与向量化模块**：使用 LangChain 的 RecursiveCharacterTextSplitter 将长文本分割成小块，并通过 OpenAIEmbeddings 将文本块转换为向量表示。
3. **向量存储模块**：使用 FAISS 向量数据库存储文本向量，支持高效的相似度搜索。
4. **问答模块**：基于 OpenAI 语言模型和 LangChain 的问答链，根据用户查询返回相关答案。
5. **来源追踪模块**：记录并显示回答内容来源的页码，提供参考信息。

## 3. 核心功能

### 3.1 PDF 文本提取

```python
def extract_text_with_page_numbers(pdf) -> Tuple[str, List[int]]:
```

该函数从 PDF 文件中提取文本内容，并记录每行文本对应的页码。返回提取的文本内容和页码列表。

### 3.2 文本处理与向量存储创建

```python
def process_text_with_splitter(text: str, page_numbers: List[int]) -> FAISS:
```

该函数处理提取的文本，将其分割成小块，创建向量表示，并构建 FAISS 向量存储。同时，记录每个文本块对应的页码信息。

### 3.3 问答查询

系统使用 OpenAI 语言模型和 LangChain 的问答链处理用户查询：

1. 通过相似度搜索找到与查询相关的文档块
2. 使用 OpenAI 语言模型生成回答
3. 显示回答内容及其来源页码

## 4. 使用流程

1. 读取 PDF 文件：`pdf_reader = PdfReader('./文件路径.pdf')`
2. 提取文本和页码信息：`text, page_numbers = extract_text_with_page_numbers(pdf_reader)`
3. 处理文本并创建知识库：`knowledgeBase = process_text_with_splitter(text, page_numbers)`
4. 设置查询问题：`query = "您的问题"`
5. 执行相似度搜索：`docs = knowledgeBase.similarity_search(query)`
6. 初始化语言模型和问答链
7. 执行问答并获取回答
8. 显示回答内容及其来源页码

## 5. 技术依赖

- PyPDF2：PDF 文件处理
- LangChain：文本处理、向量化和问答链
- OpenAI：语言模型
- FAISS：向量存储和相似度搜索

## 6. 注意事项

- 系统需要 OpenAI API 密钥才能正常工作
- 处理大型 PDF 文件可能需要较长时间
- 系统回答质量取决于 PDF 文本提取质量和语言模型性能

## 7. 参考来源功能

系统在回答用户问题时会提供参考的页码来源。具体实现方式如下：

1. 在 `extract_text_with_page_numbers` 函数中，系统记录了每行文本对应的页码。
2. 在 `process_text_with_splitter` 函数中，系统将页码信息存储在向量数据库的 `page_info` 属性中。
3. 在查询处理部分，系统会显示回答内容后，通过 `unique_pages` 集合记录并显示唯一的页码来源：

```python
# 显示每个文档块的来源页码
for doc in docs:
    text_content = getattr(doc, "page_content", "")
    source_page = knowledgeBase.page_info.get(
        text_content.strip(), "未知"
    )

    if source_page not in unique_pages:
        unique_pages.add(source_page)
        print(f"文本块页码: {source_page}")
```

这样，用户在获得回答的同时，也能看到回答内容来自 PDF 文档的哪些页码，便于进一步查证和参考。系统不仅提供了页码信息，还去除了重复页码，使显示更加清晰。 