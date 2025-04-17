import pandas as pd
from sklearn.metrics.pairwise import linear_kernel
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
import re
pd.options.display.max_columns = 30
import matplotlib.pyplot as plt
# 支持中文
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
df = pd.read_csv('Seattle_Hotels.csv', encoding="latin-1")
# 数据探索
# print(df.head())
print('数据集中的酒店个数：', len(df))

# 创建英文停用词列表
ENGLISH_STOPWORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've", "you'll", "you'd", 'your', 
    'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', 
    "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 
    'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 
    'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 
    'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 
    'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 
    'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 
    'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 
    "don't", 'should', "should've", 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', 
    "couldn't", 'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn', 
    "isn't", 'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't", 
    'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't"
}

def print_description(index):
    example = df[df.index == index][['desc', 'name']].values[0]
    if len(example) > 0:
        print('Name:', example[1])
        print(example[0])
print('第10个酒店的描述：')
print_description(10)

# 得到酒店描述中n-gram特征中的TopK个特征,默认n=1即1-gram,k=None，表示所有的特征)
"""
函数功能
输入一个文本列表（corpus），返回其中词频最高的前 k 个 N-gram 词汇（默认 n=1 是单词，n=2 是二元词组，依此类推）。

参数说明
参数名	类型	默认值	说明
corpus	list[str]	无	文本列表（如 ["I love Python", "Python is awesome"]）
n	int	1	N-gram 的 N（1=单词，2=二元词组，如 "love Python"）
k	int	None	返回前 k 个高频词（若为 None 则返回全部，按词频排序）
代码逻辑分解：
"""
def get_top_n_words(corpus, n=1, k=None):
    # 1.统计 N-gram 词频矩阵
    # 用 CountVectorizer 将文本转换为词频矩阵：
    # ngram_range=(n, n)：指定提取的 N-gram 范围（如 n=2 时只提取二元词组）。
    # stop_words=list(ENGLISH_STOPWORDS)：过滤英文停用词（如 "the", "is"）。
    vec = CountVectorizer(ngram_range=(n, n), stop_words=list(ENGLISH_STOPWORDS)).fit(corpus)

    # 2.生成词袋（Bag-of-Words）模型
    # vec.transform(corpus)：将文本转换为稀疏矩阵（每行代表一个文本，每列代表一个 N-gram 的出现次数）。
    bag_of_words = vec.transform(corpus)
    # """
    # print('feature names:')
    # print(vec.get_feature_names())
    # print('bag of words:\n',bag_of_words)
    # print(bag_of_words.toarray())

    # """
    # 3.计算词频总和
    # sum_words = bag_of_words.sum(axis=0)：对所有文本的 N-gram 频率求和（得到每个 N-gram 的总出现次数）。
    sum_words = bag_of_words.sum(axis=0)
    # 4.提取词汇和频率
    # 通过 vec.vocabulary_（词汇表字典）将列索引映射回实际词汇，生成 (word, frequency)元组列表[('located southern tip', 1), ('southern tip lake', 1)...。
    words_freq = [(word, sum_words[0, idx]) for word, idx in vec.vocabulary_.items()]
    #print(words_freq[:10])
    # 5.按词频排序并返回前 k 个
    # sorted(..., key=lambda x: x[1], reverse=True)：按词频降序排序。
    # lambda x: x[1]等同于
    # def get_freq(x):
    #     return x[1]  # 返回元组的第二个元素（词频）
    # words_freq[:k]：切片返回前 k 个高频词。
    words_freq =sorted(words_freq, key = lambda x: x[1], reverse=True)
    return words_freq[:k]
# 生成n=1.k=20的可视图
# n_gram=1
# common_words = get_top_n_words(df['desc'], n=n_gram,k=20)
# # 生成n=3.k=20的可视图
n_gram=3
common_words = get_top_n_words(df['desc'], n=n_gram,k=20)
# common_words = get_top_n_words(df['desc'], 3, 20)
print(f"comon_words are \n {common_words}")
df1 = pd.DataFrame(common_words, columns = ['desc' , 'count'])
df1.groupby('desc').sum()['count'].sort_values().plot(kind='barh', title=f'去掉停用词后，酒店描述中的Top20-{n_gram}单词')
plt.savefig(f'./top20-{n_gram}words.png')
plt.show()


# 文本预处理
REPLACE_BY_SPACE_RE = re.compile(r'[/(){}\[\]\|@,;]')
BAD_SYMBOLS_RE = re.compile('[^0-9a-z #+_]')
# 使用自定义的英文停用词列表替代nltk的stopwords
STOPWORDS = ENGLISH_STOPWORDS
# 对文本进行清洗
def clean_text(text):
    # 全部小写
    text = text.lower()
    # 用空格替代一些特殊符号，如标点
    text = REPLACE_BY_SPACE_RE.sub(' ', text)
    # 移除BAD_SYMBOLS_RE
    text = BAD_SYMBOLS_RE.sub('', text)
    # 从文本中去掉停用词
    text = ' '.join(word for word in text.split() if word not in STOPWORDS)
    return text
# 对desc字段进行清理，apply针对某列
df['desc_clean'] = df['desc'].apply(clean_text)
# print('==============desc_clean=========')
# print(df['desc_clean'])
# print('============desc==========')
# print(df['desc'])
# 建模
df.set_index('name', inplace = True)
# 使用TF-IDF提取文本特征，使用自定义停用词列表,min_df=0.01：如果有1000篇文档，只保留至少在10篇文档中出现的词(1000×1%)
# tf = TfidfVectorizer(
#     analyzer='word',      # 按单词分词（默认）
#     ngram_range=(1, 3),  # 提取1到3元的N-gram（如单词、二元词组、三元词组）
#     min_df=0.01,         # 忽略文档频率低于1%的词（过滤罕见词）
#     stop_words=list(ENGLISH_STOPWORDS)  # 过滤英文停用词（如"the", "is"）
# )
tf = TfidfVectorizer(analyzer='word', ngram_range=(1, 3), min_df=0.01, stop_words=list(ENGLISH_STOPWORDS))
# 针对desc_clean提取tfidf
# 学习词汇表（fit）：根据输入的文本数据建立所有可能的N-gram词汇表。
# 生成TF-IDF矩阵（transform）：将文本转换为稀疏矩阵（每行代表一个文档，每列代表一个N-gram的TF-IDF权重）。
tfidf_matrix = tf.fit_transform(df['desc_clean'])
# print('TFIDF feature names:')
# print(tf.get_feature_names_out())
print('length of feature_names_out:')
print(len(tf.get_feature_names_out()))
# print('tfidf_matrix:')
# print(tfidf_matrix)
print('tfidf_matrix shape=')
print(tfidf_matrix.shape)
# 计算酒店之间的余弦相似度（线性核函数）
cosine_similarities = linear_kernel(tfidf_matrix, tfidf_matrix)
# print(f'cosine_similarities为\n {cosine_similarities}')
print("conine_similarities.shape=")
print(cosine_similarities.shape)
indices = pd.Series(df.index) #df.index是酒店名称

# 基于相似度矩阵和指定的酒店name，推荐TOP10酒店
def recommendations(name, cosine_similarities = cosine_similarities):
    recommended_hotels = []
    # 找到想要查询酒店名称的idx
    idx = indices[indices == name].index[0]
    # print('idx=', idx)
    # 对于idx酒店的余弦相似度向量按照从大到小进行排序
    score_series = pd.Series(cosine_similarities[idx]).sort_values(ascending = False)
    # 取相似度最大的前10个（除了自己以外）
    top_10_indexes = list(score_series.iloc[1:11].index)
    # 放到推荐列表中
    for i in top_10_indexes:
        recommended_hotels.append(list(df.index)[i])
    return recommended_hotels
hotel_name='Hilton Seattle Airport & Conference Center'
recommended=recommendations(hotel_name)
print(f"top 10 similar to {hotel_name} are\n")
for i in range(len(recommended)):
    print (f"top{(i+1):02d}        {recommended[i]}")
# print(recommendations('Hilton Seattle Airport & Conference Center'))
# print(recommendations('The Bacon Mansion Bed and Breakfast'))
# #print(result)
