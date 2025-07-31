# V100_hotel_recommend_api.py
'''
程序说明：
## 1. Flask后端API，提供酒店下拉列表和相似酒店推荐服务。
## 2. /hotels 返回所有酒店名称及编号，/recommend 返回3个最相似酒店。
## 3. 内含数据清洗、TF-IDF建模、相似度计算。
'''

from flask import Flask, request, jsonify, send_from_directory
import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# ===== 数据加载与清洗 =====
df = pd.read_csv('Seattle_Hotels.csv', encoding='latin1')
# 1. 去除desc为空或全空格的行
df = df[df['desc'].notnull() & (df['desc'].str.strip() != '')]
# 2. 去除异常短文本（如长度小于30的简介）
df = df[df['desc'].str.len() >= 30]
# 3. 替换常见乱码和特殊字符
def clean_text(text):
    text = re.sub(r'[?]', ' ', text)  # 替换乱码
    text = re.sub(r'\n|\r|\t', ' ', text)  # 替换转义字符
    text = re.sub(r'\s+', ' ', text)  # 多空格合并
    return text.strip()
df['desc'] = df['desc'].apply(clean_text)
# 4. 去重
df = df.drop_duplicates(subset=['desc'])
# 5. 重新索引
df = df.reset_index(drop=True)
descs = df['desc'].tolist()

# ===== TF-IDF建模 =====
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

# ===== API接口 =====
@app.route('/hotels', methods=['GET'])
def get_hotels():
    """返回所有酒店名称及编号"""
    hotels = [{'id': i, 'name': df.iloc[i]['name']} for i in range(len(df))]
    return jsonify({'hotels': hotels})

@app.route('/recommend', methods=['POST'])
def recommend():
    """根据酒店编号返回3个最相似酒店"""
    data = request.get_json()
    idx = int(data.get('hotel_id', 0))
    sims = cosine_similarity(tfidf_matrix[idx], tfidf_matrix).flatten()
    sims[idx] = -1  # 排除自己
    top3_idx = sims.argsort()[-3:][::-1]
    results = []
    for i in top3_idx:
        results.append({
            'name': df.iloc[i]['name'],
            'desc': df.iloc[i]['desc'][:120] + ('...' if len(df.iloc[i]['desc']) > 120 else ''),
            'similarity': round(float(sims[i]), 3)
        })
    return jsonify({'results': results})

@app.route('/')
def index():
    return send_from_directory('static', 'V100_hotel_recommend_front.html')

if __name__ == '__main__':
    app.run(debug=True) 