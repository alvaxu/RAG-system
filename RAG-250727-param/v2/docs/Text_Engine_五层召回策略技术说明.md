# Text Engine 五层召回策略技术说明文档

## 概述

Text Engine 采用五层召回策略，通过多层次、多策略的搜索方法，确保在保证召回质量的同时，最大化召回数量。每一层都有其特定的目标和实现方式，从精确匹配到模糊扩展，逐步放宽搜索条件，实现"高召回、高质量"的搜索目标。

---

## 第一层：向量相似度搜索（主要策略）

### 什么是向量相似度搜索？

向量相似度搜索是一种基于语义理解的搜索方法。它将文本转换为高维向量（数字数组），通过计算向量之间的距离来判断文本的相似程度。

### 为什么使用向量相似度搜索？

1. **语义理解**：能够理解"汽车"和"轿车"的相似性，而不仅仅是字面匹配
2. **上下文感知**：考虑词汇在句子中的语义关系
3. **高精度**：通常能返回最相关的结果

### 技术实现方式

#### 1. 向量化过程
```python
# 使用 DashScope Embeddings 模型 (text-embedding-v1)
# 将查询文本转换为 1536 维向量
query_vector = embedding_model.encode(query)
```

#### 2. 相似度计算
```python
# 使用 FAISS 向量数据库进行快速相似度搜索
# 支持多种距离度量：余弦相似度、欧几里得距离等
vector_results = vector_store.similarity_search(query, k=50)
```

#### 3. 分数计算
```python
# 基于内容相关性计算分数
vector_score = calculate_content_relevance(query, doc.content)
```

### 通俗解释

想象一下，我们把每个文档都转换成一个"指纹"（向量），查询也有自己的"指纹"。通过比较这些"指纹"的相似程度，我们就能找到最相关的文档。就像警察通过指纹匹配找到嫌疑人一样，我们通过向量匹配找到最相关的文档。

---

## 第二层：语义关键词搜索（补充策略）

### 什么是语义关键词搜索？

语义关键词搜索是在传统关键词匹配基础上的增强版本，它不仅考虑词汇的字面匹配，还考虑词汇的语义关系和上下文。

### 为什么使用语义关键词搜索？

1. **补充向量搜索**：当向量搜索结果不足时，提供额外结果
2. **精确匹配**：对于特定术语和专有名词，提供精确匹配
3. **多样性**：增加结果的多样性，避免过度依赖单一策略

### 技术实现方式

#### 1. 关键词提取
```python
# 使用 jieba 分词工具，支持多种算法
# 方法1：TF-IDF 算法（基于词频-逆文档频率）
keywords_tfidf = jieba.analyse.extract_tags(query, topK=10)

# 方法2：精确分词
words = jieba.lcut(query, cut_all=False)

# 方法3：TextRank 算法（基于图排序）
keywords_textrank = jieba.analyse.textrank(query, topK=10)
```

#### 2. 停用词过滤
```python
# 过滤无意义的词汇
stop_words = {'的', '是', '在', '有', '和', '与', '或', '但', '而'}
filtered_keywords = [word for word in keywords if word not in stop_words and len(word) > 1]
```

#### 3. 匹配分数计算
```python
# 精确匹配：1.0分
# 部分匹配：0.7分  
# 模糊匹配：基于字符相似度，最高0.6分
```

### 通俗解释

就像我们在图书馆找书时，不仅看书名，还会看目录中的关键词。语义关键词搜索就是这样的过程：先提取查询中的"关键信息"（比如"芯片制造"中的"芯片"和"制造"），然后在文档中寻找包含这些关键词的内容。

---




## 第三层：混合搜索策略（融合策略）

### 什么是混合搜索策略？

混合搜索策略将三种不同的搜索策略进行智能融合，通过权重分配和分数计算，生成更全面的搜索结果。

### 为什么使用混合搜索策略？

1. **策略互补**：结合向量搜索的语义理解、关键词搜索的精确性和语义相似度搜索的语义匹配
2. **结果融合**：避免重复结果，提高结果质量
3. **权重可调**：根据实际需求调整不同策略的重要性

### 技术实现方式

#### 1. 权重配置
```python
# 从配置文件读取权重
vector_weight = 0.4      # 向量搜索权重 40%
keyword_weight = 0.3     # 关键词搜索权重 30%
semantic_weight = 0.3    # 语义相似度搜索权重 30%
```

#### 2. 结果融合
```python
# 为每个结果计算混合分数
for result in vector_results:
    result['hybrid_score'] = result.get('vector_score', 0) * vector_weight

for result in keyword_results:
    result['hybrid_score'] = result.get('keyword_score', 0) * keyword_weight

for result in semantic_results:
    result['hybrid_score'] = result.get('semantic_score', 0) * semantic_weight
```

#### 3. 三种策略的具体实现
```python
# 1. 向量搜索：使用第一层的向量相似度搜索
vector_results = self._vector_similarity_search(query, top_k=20)

# 2. 关键词搜索：使用第二层的语义关键词搜索  
keyword_results = self._semantic_keyword_search(query, top_k=15)

# 3. 语义相似度搜索：基于Jaccard指数的语义匹配
semantic_results = self._semantic_similarity_search(query, top_k=15)
```


## 第三层补充：语义相似度搜索详解

### 什么是语义相似度搜索？

语义相似度搜索是第三层混合搜索策略的重要组成部分，它基于Jaccard指数计算查询和文档之间的语义相似度，通过词汇集合的重叠程度来判断相关性。

### 技术实现方式

#### 1. 关键词提取
```python
# 使用jieba提取查询和文档的关键词
query_keywords = extract_semantic_keywords(query)
doc_keywords = extract_semantic_keywords(doc.content)
```

#### 2. Jaccard相似度计算
```python
# 计算词汇集合的交集和并集
intersection = query_words.intersection(content_words)
union = query_words.union(content_words)

# Jaccard指数 = 交集大小 / 并集大小
jaccard_score = len(intersection) / len(union)
```

#### 3. 阈值过滤
```python
# 设置较低的阈值(0.05)以提高召回率
if jaccard_score > 0.05:
    # 处理并添加结果
```

### 通俗解释

语义相似度搜索就像是在比较两个"词汇包"的相似程度：查询有一个"词汇包"（比如包含"芯片"、"制造"、"技术"），每个文档也有自己的"词汇包"。通过计算这两个"词汇包"有多少共同词汇，以及总共有多少不同词汇，我们就能知道它们的相似程度。就像比较两个购物清单，看看有多少商品是重复的。

---

## 第二层 vs 第三层：算法差异详解

### 核心区别对比

虽然第二层（语义关键词搜索）和第三层（语义相似度搜索）都使用关键词提取，但它们在算法原理、匹配方式和适用场景上有本质区别：

| 方面 | 第二层：语义关键词搜索 | 第三层：语义相似度搜索 |
|------|------------------------|------------------------|
| **算法原理** | 基于**关键词匹配**的分数计算 | 基于**Jaccard指数**的集合相似度 |
| **匹配方式** | 精确匹配 + 部分匹配 + 字符模糊匹配 | 词汇集合的重叠程度计算 |
| **分数计算** | 加权平均：精确(1.0) + 部分(0.7) + 模糊(0.6) | Jaccard指数：交集/并集 |
| **阈值设置** | 0.3（关键词匹配阈值） | 0.05（Jaccard阈值，较低） |
| **召回数量** | top_k=40（较多） | top_k=15（较少） |
| **适用场景** | 精确的关键词查找 | 语义层面的词汇关联性 |

### 技术实现差异

#### 第二层：关键词匹配算法
```python
def _calculate_keyword_match_score(self, keywords: List[str], doc) -> float:
    match_scores = []
    for keyword in keywords:
        # 精确匹配：1.0分
        if keyword in content_lower:
            match_scores.append(1.0)
        # 部分匹配：0.7分  
        elif any(keyword in word for word in content_lower.split()):
            match_scores.append(0.7)
        # 模糊匹配：基于字符相似度，最高0.6分
        else:
            char_similarity = self._calculate_char_similarity(keyword, word)
            match_scores.append(char_similarity * 0.6)
    
    return sum(match_scores) / len(match_scores)  # 平均分数
```

#### 第三层：Jaccard相似度算法
```python
def _semantic_similarity_search(self, query: str, top_k: int = 15):
    # 提取查询和文档的关键词集合
    query_words = set(self._extract_semantic_keywords(query))
    content_words = set(self._extract_semantic_keywords(content))
    
    # 计算Jaccard相似度
    intersection = query_words.intersection(content_words)
    union = query_words.union(content_words)
    jaccard_score = len(intersection) / len(union)
    
    # 阈值过滤：jaccard_score > 0.05
    if jaccard_score > 0.05:
        # 处理并添加结果
```

### 实际应用场景

#### 第二层适合：
- **精确查找**：查找包含特定术语的文档
- **专业术语**：对关键词敏感的技术文档
- **高精度要求**：需要准确匹配的场景

#### 第三层适合：
- **语义关联**：发现词汇集合相似度高的文档
- **概念扩展**：找到概念层面相关的内容
- **知识发现**：通过词汇重叠发现潜在关联

### 通俗理解

**第二层**就像是在**精确查找**：你有一个购物清单，在超市里找到完全匹配的商品。即使商品名称有细微差别，也能通过模糊匹配找到。

**第三层**就像是在**比较相似度**：你有两个购物清单，通过比较它们有多少共同商品来判断相似程度。即使商品不完全一样，但概念相关，也能得到高分。

### 性能考虑

1. **计算复杂度**：第二层需要逐个关键词匹配，第三层需要集合运算
2. **内存使用**：第三层需要维护词汇集合，内存占用稍高
3. **缓存策略**：两层都使用相同的关键词提取函数，可以共享缓存

---

#### 4. 去重和排序
```python
# 基于内容哈希去重
# 按混合分数排序
hybrid_results.sort(key=lambda x: x.get('hybrid_score', 0), reverse=True)
```

### 通俗解释

混合搜索就像做菜时的"三菜一汤"：向量搜索提供"主菜"（语义相关的结果），关键词搜索提供"配菜"（精确匹配的结果），语义相似度搜索提供"汤品"（语义匹配的结果），然后我们按照一定的比例将它们混合在一起，最后去掉重复的，按照"美味程度"排序。

---

## 第四层：智能模糊匹配（容错策略）

### 什么是智能模糊匹配？

智能模糊匹配是一种容错搜索策略，它能够处理拼写错误、同音字、近义词等不精确的查询，提高系统的鲁棒性。

### 为什么使用智能模糊匹配？

1. **容错性**：处理用户的拼写错误和输入偏差
2. **用户体验**：即使查询不完美，也能返回相关结果
3. **召回率**：提高整体召回数量

### 技术实现方式

#### 1. 查询预处理
```python
# 使用 jieba 提取关键词
keywords = extract_semantic_keywords(query)

# 过滤停用词和短词
filtered_words = [word for word in keywords if len(word) > 1 and word not in stop_words]
```

#### 2. 模糊匹配算法
```python
# 1. 精确匹配：1.0分
if term in content_lower:
    term_score = 1.0

# 2. 词内匹配：0.8分  
elif any(term in word for word in content_words):
    term_score = 0.8

# 3. 字符级模糊匹配：基于字符相似度，最高0.6分
else:
    char_similarity = calculate_char_similarity(term, word)
    term_score = char_similarity * 0.6
```

#### 3. 字符相似度计算
```python
# 计算公共字符比例
common_chars = set(term) & set(word)
total_chars = set(term) | set(word)
similarity = len(common_chars) / len(total_chars)
```

### 通俗解释

智能模糊匹配就像是一个"宽容的老师"：即使学生写错了字（比如把"芯片"写成"心片"），老师也能理解学生的意思，找到相关的答案。它通过多种匹配方式，确保即使查询有小的错误，也能找到相关的结果。

---

## 第五层：智能扩展召回（兜底策略）

### 什么是智能扩展召回？

智能扩展召回是最后的"兜底"策略，当前四层召回结果不足时，通过扩展查询词、同义词、相关概念等方式，主动寻找更多相关文档。

### 为什么使用智能扩展召回？

1. **兜底保障**：确保即使前四层结果不足，也能达到最小召回要求
2. **概念扩展**：通过语义扩展，发现用户可能需要的相关内容
3. **知识发现**：帮助用户发现相关但可能没有想到的信息

### 技术实现方式

#### 1. 同义词扩展召回

**什么是同义词扩展？**
通过查找查询词的同义词，扩大搜索范围。

**实现方式：**
```python
# 预定义同义词词典
synonym_dict = {
    '数据': ['数据', '信息', '资料', '记录'],
    '分析': ['分析', '研究', '调查', '检查'],
    '方法': ['方法', '技术', '手段', '途径']
}

# 使用同义词进行搜索
for synonym in synonyms:
    results = vector_store.similarity_search(synonym, k=top_k//len(synonyms))
```

**通俗解释：**
就像我们找"汽车"相关信息时，也会考虑"轿车"、"汽车"、"机动车"等表达方式，这样能找到更多相关内容。

#### 2. 概念扩展召回

**什么是概念扩展？**
通过上位概念（更宽泛）和下位概念（更具体）来扩展搜索。

**实现方式：**
```python
# 上位概念（更宽泛）
hypernym_dict = {
    '芯片': ['半导体', '集成电路', '电子器件'],
    '晶圆': ['半导体材料', '硅片', '基板']
}

# 下位概念（更具体）
hyponym_dict = {
    '半导体': ['芯片', '晶圆', '晶体管'],
    '制造': ['代工', '封装', '测试']
}
```

**通俗解释：**
就像我们找"苹果"时，上位概念可能是"水果"，下位概念可能是"红富士"、"青苹果"等。这样既能找到更广泛的相关信息，也能找到更具体的相关内容。

#### 3. 相关词扩展召回

**什么是相关词扩展？**
通过查找与查询词在语义上相关的词汇来扩展搜索。

**实现方式：**
```python
# 相关词词典
related_dict = {
    '中芯国际': ['SMIC', '晶圆代工', '半导体制造'],
    '芯片': ['集成电路', 'IC', '微处理器'],
    '晶圆': ['硅片', '基板', '半导体材料']
}
```

**通俗解释：**
就像我们找"手机"相关信息时，也会考虑"通讯"、"移动设备"、"智能终端"等相关概念，这样能找到更全面的信息。

#### 4. 领域扩展召回

**什么是领域扩展？**
通过识别查询词的领域标签，在相关领域内进行扩展搜索。

**实现方式：**
```python
# 领域标签词典
domain_dict = {
    '芯片': ['半导体', '集成电路', '电子'],
    '制造': ['工业', '生产', '技术'],
    '技术': ['科技', '创新', '研发']
}
```

**通俗解释：**
就像我们找"医疗"相关信息时，会考虑"健康"、"疾病"、"治疗"等医疗领域的相关概念，这样能确保搜索结果的领域相关性。

---

## 整体架构设计

### 分层策略的优势

1. **渐进式搜索**：从精确到模糊，逐步放宽条件
2. **策略互补**：不同策略覆盖不同的搜索场景
3. **可配置性**：每层的参数都可以根据实际需求调整
4. **容错性**：即使某一层失败，其他层仍能工作

### 结果融合机制

1. **去重处理**：基于内容哈希，避免重复结果
2. **分数归一化**：将不同策略的分数统一到0-1范围
3. **综合排序**：考虑多种因素，生成最终排序

### 性能优化

1. **缓存机制**：缓存文档和搜索结果，提高响应速度
2. **并行处理**：支持多策略并行执行
3. **智能阈值**：根据结果数量动态调整搜索策略

---

## 配置参数说明

### 召回策略配置

```json
{
  "recall_strategy": {
    "layer1_vector_search": {
      "enabled": true,
      "top_k": 50,
      "similarity_threshold": 0.3
    },
    "layer2_semantic_keyword": {
      "enabled": true,
      "top_k": 40,
      "match_threshold": 0.25
    },
    "layer3_hybrid_search": {
      "enabled": true,
      "top_k": 35,
      "vector_weight": 0.4,
      "keyword_weight": 0.3,
      "semantic_weight": 0.3
    },
    "layer4_smart_fuzzy": {
      "enabled": true,
      "top_k": 30,
      "fuzzy_threshold": 0.2
    },
    "layer5_expansion": {
      "enabled": true,
      "top_k": 25,
      "activation_threshold": 20
    }
  }
}
```

### 关键参数说明

- **top_k**：每层最大召回数量
- **threshold**：相似度阈值，控制结果质量
- **weight**：权重分配，控制不同策略的重要性
- **activation_threshold**：第五层激活阈值

---

## 总结

Text Engine 的五层召回策略通过多层次、多策略的搜索方法，实现了"高召回、高质量"的搜索目标。每一层都有其特定的作用和实现方式，从精确的向量搜索到智能的概念扩展，形成了一个完整的搜索体系。

这种设计不仅提高了搜索的召回率和准确性，还增强了系统的鲁棒性和用户体验。通过合理的配置和调优，可以根据实际需求平衡召回数量和质量，为用户提供最佳的搜索体验。
