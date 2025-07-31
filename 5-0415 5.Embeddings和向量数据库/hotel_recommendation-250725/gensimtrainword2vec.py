from gensim.models import Word2Vec

# 示例数据（已分词的句子）
sentences = [
    ["我", "爱", "自然", "语言", "处理"],
    ["深度", "学习", "真", "有趣"]
]

# 训练模型（Skip-gram + 负采样）
model = Word2Vec(
    sentences,
    vector_size=100,  # 词向量维度
    window=5,         # 上下文窗口大小
    min_count=1,      # 忽略低频词
    sg=1,             # 1=Skip-gram, 0=CBOW
    negative=5,       # 负采样数
    epochs=10         # 训练轮次
)

# 获取词向量
vector = model.wv["自然"]  # "自然"的词向量
print(vector)

# 找相似词
similar_words = model.wv.most_similar("自然", topn=3)
print(similar_words)  # 输出：[('语言', 0.92), ('学习', 0.88), ...]