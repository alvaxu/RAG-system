# V100_hotel_content_recommend.py
'''
程序说明：
## 1. 本程序实现基于酒店简介(desc)内容的相似酒店推荐。
## 2. 用户可选择一个酒店，系统推荐3个最相似的其他酒店。
## 3. 使用TF-IDF向量化和余弦相似度，支持英文内容。
'''

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

if __name__ == '__main__':
    # 读取数据
    df = pd.read_csv('Seattle_Hotels.csv', encoding='latin1')

    # ===== 数据清洗开始 =====
    # 1. 去除desc为空或全空格的行
    df = df[df['desc'].notnull() & (df['desc'].str.strip() != '')]
    # 2. 去除异常短文本（如长度小于30的简介）
    df = df[df['desc'].str.len() >= 30]
    # 3. 替换常见乱码和特殊字符
    def clean_text(text):
        text = re.sub(r'[?]', ' ', text)  # 替换乱码
        text = re.sub(r'\\n|\\r|\\t', ' ', text)  # 替换转义字符
        text = re.sub(r'\s+', ' ', text)  # 多空格合并
        return text.strip()
    df['desc'] = df['desc'].apply(clean_text)
    # 4. 可选：去重
    df = df.drop_duplicates(subset=['desc'])
    # 5. 重新索引
    df = df.reset_index(drop=True)
    # 6. desc列表
    descs = df['desc'].tolist()
    print(f"清洗后desc数量: {len(descs)}")
    print("前3个desc示例：", descs[:3])
    # ===== 数据清洗结束 =====

    # TF-IDF向量化，显式写出主要默认参数，便于调整
    vectorizer = TfidfVectorizer(
        input='content',
        encoding='utf-8',
        decode_error='strict',
        strip_accents=None,
        lowercase=True,
        preprocessor=None,
        tokenizer=None,
        stop_words='english',
        # token_pattern=r"(?u)\\b\\w\\w+\\b",   #只有长度大于等于2的单词才会被当作token。单个字母（如"a"、"I"）会被忽略，不会被统计为特征。
        ngram_range=(1, 3),                     #默认只统计1-gram（单词），可设为(1,2)统计1-gram和2-gram。
        analyzer='word',
        max_df=1.0,                             #不过滤高频词（所有词都保留）。   
        min_df=0.01,                            #只保留在至少1%文档中出现过的词，过滤极少见的“冷门词”。
        max_features=None,
        vocabulary=None,
        binary=False,
        dtype=float,
        norm='l2',
        use_idf=True,
        smooth_idf=True,
        sublinear_tf=False
    )
    tfidf_matrix = vectorizer.fit_transform(descs)

    # 展示所有酒店名称供用户选择
    print("可选酒店列表：")
    for idx, name in enumerate(df['name']):
        print(f"{idx}: {name}")

    # 用户输入选择的酒店编号
    while True:
        try:
            selected_idx = int(input("\n请输入你感兴趣的酒店编号: "))
            if 0 <= selected_idx < len(df):
                break
            else:
                print("编号超出范围，请重新输入。")
        except ValueError:
            print("请输入有效的数字编号。")

    print(f"\n你选择的酒店是: {df.iloc[selected_idx]['name']}")

    # 计算与其他酒店的相似度
    sims = cosine_similarity(tfidf_matrix[selected_idx], tfidf_matrix).flatten()
    sims[selected_idx] = -1  # 排除自己
    top3_idx = sims.argsort()[-3:][::-1]

    print("\n推荐的3个相似酒店：")
    for idx in top3_idx:
        print(f"酒店名称: {df.iloc[idx]['name']}")
        print(f"简介: {df.iloc[idx]['desc'][:60]}...")
        print(f"相似度: {sims[idx]:.3f}\n") 