"""
-*- coding: utf-8 -*-
wordsimilar.py -
Author：Administrator
Date:2025-04-15
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# 示例词库
words = [
    "苹果", "香蕉", "橙子", "葡萄", "菠萝",
    "芒果", "西瓜", "草莓", "蓝莓", "樱桃",
    "苹果手机", "苹果电脑", "苹果汁", "红苹果", "青苹果"
]

# 定义n-gram函数（这里使用2-gram）
def get_ngrams(word, n=2):
    return [word[i:i+n] for i in range(len(word)-n+1)]

# 为每个词生成n-gram特征
word_ngrams = [" ".join(get_ngrams(word)) for word in words]
print("词语的2-gram表示示例:")
for word, ngram in zip(words[:5], word_ngrams[:5]):
    print(f"{word} → {ngram}")

# 使用TF-IDF向量化
vectorizer = TfidfVectorizer(tokenizer=lambda x: x.split())
tfidf_matrix = vectorizer.fit_transform(word_ngrams)

# 定义查找相似词的函数
def find_similar_words(target_word, top_n=5):
    # 生成目标词的n-gram
    target_ngram = " ".join(get_ngrams(target_word))
    # 转换为TF-IDF向量
    target_vec = vectorizer.transform([target_ngram])
    # 计算余弦相似度
    similarities = cosine_similarity(target_vec, tfidf_matrix)
    # 获取最相似的词
    similar_indices = np.argsort(similarities[0])[::-1][1:top_n+1]  # 排除自己
    print(f"\n与'{target_word}'最相似的{top_n}个词:")
    for idx in similar_indices:
        print(f"{words[idx]}: {similarities[0][idx]:.3f}")

# 测试示例
find_similar_words("苹果", top_n=5)
find_similar_words("菠萝", top_n=3)
find_similar_words("苹果手机", top_n=3)