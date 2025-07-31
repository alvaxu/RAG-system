# Embedding与向量数据库

# 今天的学习目标

# 什么是Embedding

CASE：基于内容的推荐  
什么是N-Gram  
余弦相似度计算  
为酒店建立内容推荐系统  
Word Embedding  
什么是Embedding  
Word2Vec进行词向量训练

# 向量数据库

·什么是向量数据库FAISS，Milvus,Pinecone的特点向量数据库与传统数据库的对比

什么是Embedding

# 基于内容的推荐

# 基于内容的推荐：

·依赖性低，不需要动态的用户行为，只要有内容就可以进行推荐

系统不同阶段都可以应用

系统冷启动，内容是任何系统天生的属性，可以从中挖掘到特征，实现推荐系统的冷启动。一个复杂的推荐系统是从基于内容的推荐成长起来的

商品冷启动，不论什么阶段，总会有新的物品加入，这时只要有内容信息，就可以帮它进行推荐

了解Embedding可以从了解物体的特征表达开始

# 基于内容的推荐

![](images/d57eeed57f61c68b73dbd537b904881dd6f5d00622fcfdb998b49decf45be6fe.jpg)

·物品表示 Item Representation:为每个item抽取出features

·特征学习ProfileLearning:

利用一个用户过去喜欢（不喜欢）的item的特征数据，来学习该用户的喜好特征（profile）；

·生成推荐列表Recommendation Generation:

通过用户profile与候选item的特征，推荐相关性最大的item。

# 为酒店建立内容推荐系统

# 西雅图酒店数据集：

·下载地址: https://github.com/susanli2016/Machine-Learning-with-Python/blob/master/Seattle_Hotels.csv  
·字段:name,address,desc  
·基于用户选择的酒店，推荐相似度高的Top10个其他酒店  
·方法：计算当前酒店特征向量与整个酒店特征矩阵的余弦相似度，取相似度最大的Top-k个

<html><body><table><tr><td>nane</td><td>address des c</td><td></td></tr><tr><td>Hilton Garden Seattle Downtown</td><td>1821 Boren Avenue,</td><td>Located on the southern tip of Lake Union, the Hilton Garden The neighhorhood is home to numeros ma ior internationalcomn</td></tr><tr><td>Sheraton Grand Seattle</td><td></td><td>1400 6th Avenue,Se:Located in the city’s vibrant core, the Sheraton Grand Seattl</td></tr><tr><td>Crowne Plaza Seattle Downtown</td><td></td><td>1113 6th Ave, SeatLocated in the heart of downtown Seattle, the award-wining</td></tr><tr><td>Kimpton Hotel Monaco Seattle</td><td></td><td>Crowne Pla7a Hotel Seatt1e ? Downtown offers an_eycentionalh 1101 4th Ave, SeatWhat?s near our hotel downtown Seattlelocation? The better</td></tr><tr><td>The Westin Seattle</td><td></td><td>miestion might he what?s not nearhvTn addition to heing one 1900 5th Avenue, eiSituated amid incredible shopping and iconic attractions,The</td></tr><tr><td>The Paramount Hotel Seattle</td><td></td><td>724 Pine Street, Se:More than just a hotel, The Paramount Hotel Seattle summons t</td></tr><tr><td>Hilton Seattle</td><td></td><td>1301 6th Avenue Sea Enjoy our central location in the heart of downtown at Hilton</td></tr><tr><td>Motif Seattle</td><td></td><td>1415 Fifth Ave SeatiA downtown Seattle destination hotel just steps from everywhe</td></tr><tr><td>Warwick Seattle</td><td></td><td>401 Lenora Street燬(In a city known for setting trends,Warwick Seattle is leadin</td></tr><tr><td>Four Seasons Hotel Seattle</td><td></td><td>99 Union St， SeattliSurrounded by snow-capped mountain peaks, deep-blue waters an</td></tr><tr><td>W Seattle</td><td></td><td>1112 4th Ave, SeattiSoak up the vibrant scene in the Living Room Bar and get in t</td></tr><tr><td>Gand Hyatt Seattle</td><td></td><td>721 Pine St, SeattliExperience an upscale Pacific Northwest getaway at Grand Hyat</td></tr><tr><td>Kimpton Alexis Hotel</td><td></td><td>1007 1st Ave, SeattiIf you拢e ever had the experience of reading a book that you</td></tr><tr><td>Hotel Max</td><td></td><td>620 Stewart St, Sea With a world-class art collection and a floor of curated gues</td></tr><tr><td>Ace Hotel Seattle</td><td></td><td>2423 1st Ave, SeattiWe fell in love with a former maritime workers' hotel in Bell</td></tr><tr><td>Seattle Marriott Waterfront</td><td></td><td>2100 Alaskan Way, SiExperience the best of the city when you stay at Seattle Marr</td></tr><tr><td>The Edgewater Hotel Seattle</td><td></td><td>2411 Alaskan Way, SiWelcome to The Edgewater Hotel, The “Best Hotel in Seattle"（</td></tr><tr><td></td><td></td><td>SpringHill Suites Seattleowntow180 YaleAve,SeatTreat yourself toarewarding stayat the SpringHill Suites S</td></tr><tr><td>Fairmont Olympic Hotel</td><td></td><td>411 University St,iDowntown Seattle premier luxury hotel,he Fairmont Olympic.</td></tr><tr><td></td><td></td><td>La Quinta Irn& Suites Seattle Doi2248th Ave,SeattFora comfortable visit tothe vibrant hubof thecity，our h</td></tr><tr><td></td><td></td><td>Embassy Suites by Hilton Seattlel255 S King St，SeatNestledin Seatle'soriginal neighborhod Pioneer Squareth</td></tr><tr><td>Pan Pacific Seattle</td><td></td><td>2125 Terry Ave, Sea When you are at Pan Pacific Seattle,you can trust us to make</td></tr><tr><td>Kimpton Hotel Vintage Seattle</td><td></td><td>1100 5th Ave, SeattiWondering what担 around Kimpton Hotel Vintage Seattle? A bett</td></tr></table></body></html>

# 为酒店建立内容推荐系统

# 余弦相似度：

·通过测量两个向量的夹角的余弦值来度量它们之间的相似性

·判断两个向量大致方向是否相同，方向相同时，余弦相似度为1；两个向量夹角为90°时，余弦相似度的值为0，方向完全相反时，余弦相似度的值为-1。

·两个向量之间夹角的余弦值为[-1,1]

给定属性向量A和B，A和B之间的夹角0余弦值可以通过点积和向量长度计算得出

![](images/770a6b11a488117e486d129b16e7c28ef3895d3c285600ab4f4ba6d263e2ccfe.jpg)

# 为酒店建立内容推荐系统

# 计算A和B的余弦相似度：

·句子A：这个程序代码太乱，那个代码规范  
·句子B：这个程序代码不规范，那个更规范  
·Step1，分词  
句子A：这个/程序/代码/太乱，那个/代码/规范  
句子B：这个/程序/代码/不/规范，那个/更/规范  
·Step2，列出所有的词  
这个，程序，代码，太乱，那个，规范，不，更  
·Step3，计算词频  
句子A：这个1，程序1，代码2，太乱1，那个1，规范1，不0，更0  
句子B：这个1，程序1，代码1，太乱0，那个1，规范2，不1，更1

# 为酒店建立内容推荐系统

计算A和B的余弦相似度：

Step4，计算词频向量的余弦相似度句子A: (1，1，2，1，1，1，0，0)句子B: $( 1 , \ 1 , \ 1 , \ 0 , \ 1 , \ 2 , \ 1 , \ 1 )$

cos( $g ) = { \frac { 1 \times 1 + 1 \times 1 + 2 \times 1 + 1 \times 0 + 1 \times 1 + 1 \times 2 + 0 \times 1 + 0 \times 1 } { { \sqrt { 1 ^ { 2 } + 1 ^ { 2 } + 2 ^ { 2 } + 1 ^ { 2 } + 1 ^ { 2 } + 1 ^ { 2 } + 0 ^ { 2 } + 0 ^ { 2 } } } \times { \sqrt { 1 ^ { 2 } + 1 ^ { 2 } + 1 ^ { 2 } + 0 ^ { 2 } + 1 ^ { 2 } + 2 ^ { 2 } } } } }$ 2+1²+1² $= 0 . 7 3 8$

结果接近1，说明句子A与句子B是相似的

# 为酒店建立内容推荐系统

什么是N-Gram（N元语法）：

·基于一个假设：第n个词出现与前n-1个词相关，而与其他任何词不相关$N = 1$ 时为unigram， $N = 2$ 为bigram， $N = 3$ 为trigram·N-Gram指的是给定一段文本，其中的N个item的序列比如文本：ABCDE，对应的Bi-Gram为AB,BC,CD,DE

·当一阶特征不够用时，可以用N-Gram做为新的特征。比如在处理文本特征时，一个关键词是一个特征，但有些情况不够用，需要提取更多的特征，采用N-Gram $\Rightarrow$ 可以理解是相邻两个关键词的特征组合

如何了解事物的特征表达？N-Gram就是最基本的一种方式

# 为酒店建立内容推荐系统

plt.rcParams['font.sans-serif'] $\mathbf { \tau } = \mathbf { \tau }$ ['SimHei']#用来正常显示中文标签  
df $\mathbf { \tau } = \mathbf { \tau }$ pd.read_csv('Seattle_Hotels.csv',encoding $\ c =$ "latin-1")  
# 得到酒店描述中n-gram特征中的TopK个  
def get_top_n_words(corpus, $\mathsf { n } = 1$ ， $\mathrel { \mathop : } =$ None):

![](images/7acfe5603f119aeec1e5430da09e66e9c9ee7010ec5133639dbf50cb6926df74.jpg)  
去掉停用词后，酒店描述中的Top20单词

#统计ngram词频矩阵 vec $\mathbf { \tau } = \mathbf { \tau }$ CountVectorizer(ngram_range $\ c =$ (n,n), stop_words $\ c =$ english').fit(corpus) bag_of_words $\mathbf { \tau } = \mathbf { \tau }$ vec.transform(corpus) sum_words $\mathbf { \tau } = \mathbf { \tau }$ bag_of_words.sum(axis ${ \boldsymbol { \mathbf { \mathit { \sigma } } } } = 0$ ） words_freq $\mathbf { \tau } = \mathbf { \tau }$ [(word,sum_words[0, idx]) for word, idx in vec.vocabulary_.items(] #按照词频从大到小排序 words_freq $\mathbf { \tau } = \mathbf { \tau }$ sorted(words_freq, key $\mathbf { \tau } = \mathbf { \tau }$ lambda x: x[1],reverse $\mathbf { \sigma } = \mathbf { \sigma }$ True) return words_freq[:k] common_words $\mathbf { \tau } = \mathbf { \tau }$ get_top_n_words(df['desc'],1, 20) df1 $\mathbf { \tau } = \mathbf { \tau }$ pd.DataFrame(common_words, columns $\mathbf { \tau } = \mathbf { \tau }$ ['desc','count']) df1.groupby('desc').sum()['count'].sort_values().plot(kind $\ c =$ 'barh', title $\ c =$ 去掉停用词后，酒店描述中的Top20单词") plt.show0

# 为酒店建立内容推荐系统

# Bi-Gram

common words  = get top n words(df['des c'], 2, 20)

![](images/311d7a61b864bc69644047af0e60c792669ff36d1e5cb530198c6c34ce04757a.jpg)

# Tri-Gram

common words = get top n words(df['des c'], 3, 20)

# 为酒店建立内容推荐系统

def clean_text(text):

(151. 13732) 0.02288547901274695   
(151, 21971) 0.03682289049851129   
(151. 19896) 0.017052721912118395   
(151, 22212) 0.016660175897670552   
(151, 13482) 0.024148380094538605   
(151, 12132) 0.024170114517665667   
(151, 11079) 0.07169842086767955   
(151. 11324) 0.013227229761895392   
(152, 26879)

#全部小写 text $\mathbf { \tau } = \mathbf { \tau }$ text.lower() return text df['desc_clean'] $\mathbf { \tau } = \mathbf { \tau }$ df['desc'].apply(clean_text) > # 使用TF-IDF提取文本特征 tf $\mathbf { \tau } = \mathbf { \tau }$ TfidfVectorizer(analyzer $\ c =$ word',ngram_range $\ c =$ (1,3),min_df ${ } = 0$ ,stop_words $\ c =$ en tfidf_matrix $\mathbf { \tau } = \mathbf { \tau }$ tf.fit_transform(df['desc_clean']) print(tfidf_matrix) print(tfidf_matrix.shape) # 计算酒店之间的余弦相似度 (线性核函数) cosine_similarities $\mathbf { \tau } = \mathbf { \tau }$ linear_kernel(tfidf_matrix,tfidf_matrix) print(cosine_similarities)

0.01161917 0.02656894 0.01184587 0.00244782 0.005835891 [0.01161917 1 0.015586 0.01625083 0.00313105 0.00797999 [0.02656894 0.015586 1. 0.02071479 0.00748781 0.01028037] [0.01184587 0.01625083 0.02071479 0.01066904 0.0079114 [0.00244782 0.00313105 0.00748781 0.01066904 1. 0.00257955] [0.00583589 0.00797999 0.01028037 0.0079114 0.00257955 1. (152, 152)

152家酒店，之间的相似度矩阵(1-Gram,2-Gram,3-Gram)

# 为酒店建立内容推荐系统

#基于相似度矩阵和指定的酒店name，推荐TOP10酒店   
def recommendations(name,cosine_similarities $\mathbf { \tau } = \mathbf { \tau }$ cosine_similarities): recommended_hotels = [] #找到想要查询酒店名称的idx idx $\mathbf { \tau } = \mathbf { \tau }$ indices[indices $\scriptstyle = =$ name].index[0] print('idx $\ c =$ ,idx) #对于idx酒店的余弦相似度向量按照从大到小进行排序 score_series $\mathbf { \tau } = \mathbf { \tau }$ pd.Series(cosine_similarities[idx]).sort_values(ascending $\mathbf { \tau } = \mathbf { \tau }$ False) # 取相似度最大的前10个 (除了自己以外) top_10_indexes $\mathbf { \tau } = \mathbf { \tau }$ list(score_series.iloc[1:11].index) #放到推荐列表中 for iin top_10_indexes: recommended_hotels.append(list(df.index)[i) return recommended_hotels   
print(recommendations('Hilton Seattle Airport & Conference Center'))   
print(recommendations('The Bacon Mansion Bed and Breakfast'))

# idx= 49

["Enbassy Suites by Hilton Seattle Tacoma International Airport'   
'DoubleTree by Hilton Hotel Seattle Airport', 'Seattle Airport   
Marriott', 'Motel 6 Seattle Sea-Tac Airport South'， "Econo Lodge   
SeaTac Airport North'， Four Points by Sheraton Downtown Seattle   
Center', 'Knights Inn Tukwila', “Econo Lodge Renton-Bellevue'   
'Hampton Inn Seattle/Southcenter", “Radisson Hotel Seattle   
Airport"]   
idx= 116   
['11th Avenue Inn Bed and Breakfast', 'Shafer Baillie Mansion Bed   
& Breakfast'， ‘Chittenden House Bed and Breakfast"， ‘Gaslight   
Inn'， 'Bed and Breakfast Inn Seattle'， 'Silver Cloud Hotel   
Seattle Broadway', ‘Hyatt House Seattle", ‘Mozart Guest House'   
"Quality Inn & Suites Seattle Center', 'MarQueen Hotel"]

# 查找和指定酒店相似度最高的Top10家酒店

# 为酒店建立内容推荐系统

# CountVectorizer:

将文本中的词语转换为词频矩阵  
fittransform：计算各个词语出现的次数  
getfeaturenames：可获得所有文本的关键词  
toarray(：查看词频矩阵的结果。  
vec $\mathbf { \tau } = \mathbf { \tau }$ CountVectorizer(ngram_range=(n,n), stop_words $\mathbf { \Phi } = \mathbf { \Phi } ^ { \prime }$ english').fit(corpus)  
bag_of_words $\mathbf { \tau } = \mathbf { \tau }$ vec.transform(corpus)  
print('feature names:')  
print(vec.get_feature_names())  
print('bag of words:")  
print(bag_of_words.toarray())

# feature names:

['00 night plus', '000 crystals marble', ‘000 sq ft', '000 square feet', ‘000 redesigned venues', '10 unique guestrooms' , '100 meters away', ‘100 non smokin '10best georgetown inn'， '11 km emerald'， "11 km seattle'， “11 miles downtown' '120 luxury guestrooms', '120 sqft 11sqm'， '1200 people range°， "12pm noon dai: minute walk'， ‘15 minutes drive'， “15 minutes water'， ‘15 people doesn'， ‘150 property', '178 guest rooms'， '18 acre retreat'， '18 acres natural'， '188th sti landmark building', “1906 located street'， '1909 cecil bacon', '1910 landmark executive hotel', '1928 inn tucked', '1930s art deco'， "1960s renamed mason'

bag of words: 0 0 0 0 0 0 0 0 0] 00 0 0 0 0] 0 00 0 0 0] [0 0 0 0 0 0]]

# 为酒店建立内容推荐系统

TF-IDF:

单词次数TF  
·TF：Term Frequency，词频 文档中总单词数  
一个单词的重要性和它在文档中出现的次数呈正比。  
· IDF： Inverse Document Frequency，逆向文档频率  
一个单词在文档中的区分度。这个单词出现的文档数越少，区分文档总数  
度越大，IDF越大 IDF =log单词出现的文档数+1

# 为酒店建立内容推荐系统

# TfidfVectorizer:

#使用TF-IDF提取文本特征   
tf $\mathbf { \tau } = \mathbf { \tau }$ TfidfVectorizer(analyzer $= ^ { \mathsf { 1 } }$ word',ngram_range $\mathbf { \sigma } = \mathbf { \sigma }$ (1,3),min_df=0,   
stop_words $\mathbf { \lambda } = \mathbf { \vec { \lambda } }$ english')   
tfidf_matrix $\mathbf { \tau } = \mathbf { \tau }$ tf.fit_transform(df['desc_clean'])   
print(tfidf_matrix)   
print(tfidf_matrix.shape)

将文档集合转化为tf-idf特征值的矩阵构造函数analyzer：word或者char，即定义特征为词（word）或n-gram字符ngram_range:参数为二元组(min_n,max_n)，即要提取的n-gram的下限和上限范围max_df：最大词频，数值为小数[0.0,1.0],或者是整数，默认为1.0min_df：最小词频，数值为小数[0.0,1.0],或者是整数，默认为1.0stop_words：停用词，数据类型为列表

(151. 13732) 0.02288547901274695   
151. 21971) 0.036827:0010851129   
(151. 19896) 0.017052721912118395   
(151, 22212) 0.016660175897670552   
(151, 13482) 0.0241 8380094538605   
(151, 12132) 0.024170114517665667   
(151, 11079) 0.07169842086767955   
(151, 11324) 0.013227220761895392   
(152, 26879)

# 功能函数：

·fit_transform：进行tf-idf训练，学习到一个字典，并返回Document-term的矩阵，也就是词典中的词在该文档中出现的频次

# 为酒店建立内容推荐系统

# 基于内容的推荐：

·Step1，对酒店描述（Desc）进行特征提取·N-Gram，提取N个连续字的集合，作为特征·TF-IDF，按照(min_df,max_df)提取关键词，并生成TFIDF矩阵  
·Step2，计算酒店之间的相似度矩阵·余弦相似度  
·Step3，对于指定的酒店，选择相似度最大的Top-K个酒店进行输出

Thinking :N-Gram $\cdot$ TF-IDF的特征表达会让特征矩阵非常系数，计算量大，有没有更适合的方式？

# Word Embedding

# 什么是Embedding:

·一种降维方式，将不同特征转换为维度相同的向量  
离线变量转换成one-hot $\Rightarrow$ 维度非常高，可以将它转换为固定size的embedding向量  
·任何物体，都可以将它转换成为向量的形式，从Trait#1到#N  
·向量之间，可以使用相似度进行计算  
·当我们进行推荐的时候，可以选择相似度最大的

![](images/b6f45e3edaeb1a735f3a45f04033cc6331cfbb277ce34b538b12685a2485a65c.jpg)

![](images/03a1d11a780cfe7333ad4494baeb8f717d82a0ee072fceb40943fcf8e1c55a9e.jpg)

# Word Embedding

# 将Word进行Embedding:

# ·如果我们将King这个单词，通过维基百科的学习，进行GloVe向量化，可以表示成

[ 0.50451，0.68607，-0.59517，-0.022801，0.60046，-0.13498，-0.08813，0.47377，-0.61798，-0.31012  
-0.076666，1.493，-0.034189，-0.98173，0.68229，0.81722，-0.51874，-0.31503，-0.55809，0.66421，0.1961  
，-0.13495，-0.11476，-0.30344，0.41177，-2.223，-1.0756，-1.0783，-0.34354，0.33505，1.9927  
-0.04234，-0.64319，0.71125，0.49159，0.16754，0.34344，-0.25663，-0.8523，0.1661，0.40102，1.1685  
-1.0137 ， -0.21585， -0.15155，0.78321， -0.91241， -1.6106， -0.64426， -0.51042]

这50维度的权重大小在[-2,2]，按照颜色的方式来表示

![](images/73edd3d9de57b000b2e4463f3e7ec5ad0ad5efa631be430eab59885f254f5e75.jpg)

# Word Embedding

# 将Word进行Embedding:

·我们将King与其他单词进行比较，可以看到Man和Woman更相近同样有了向量，我们还可以进行运算king-man+woman与queen的相似度最高

model.most_similar(positive=["king","woman"]，negative=["man"])

![](images/0fdf09b33a9719a323fbb1023132110f4efe3f95a4bb1ffdc22f52bb870ca9e5.jpg)

# Word Embedding

Softmax ClassifierWord2Vec: Hidden Layer Probabilltythat the word atInputVector LinearNeurons £ ranitimiyhabandn通过Embedding，把原先词所在空间映射到一个新的空间中去，使得语义上相似的单词在该空间内距离相近。 £ ∑ abilityWord Embedding $\Rightarrow$ 学习隐藏层的权重矩阵 ∑A ‘1’ in the £输入测是one-hot编码 correspondi隐藏层的神经元数量为hidden_size(Embedding Size)回 £对于输入层和隐藏层之间的权值矩阵W，大小为 10.,00300 neurons £ one"[vocab_size,hidden_size]10,000neurons输出层为[vocab_size]大小的向量，每一个值代表着输出一个词的概率

# Word Embedding

对于输入的one-hot编码：

在矩阵相乘的时候，选取出矩阵中的某一行，而这一  
行就是输入词语的word2vec表示  
隐含层的节点个数 $\mathbf { \sigma } = \mathbf { \sigma }$ 词向量的维数  
隐层的输出是每个输入单词的Word Embedding  
word2vec，实际上就是一个查找表

![](images/5c904ac67dbf76ba42c8bdfe881ec685ea4032876c18a65a6c93a1e343e0ea17.jpg)

# Word Embedding

Word2Vec的两种模式：

·Skip-Gram，给定inputword预测上下文

![](images/d29ba33ce696a5c0e288936ba4b1e60ea17fe20ca0db2d70bac816e23d410a73.jpg)

.Bereftoflifeherestsinpeace!Ifyouhadn'tnailedhir

CBOW，给定上下文，预测inputword（与 Skip-Gram相反)

![](images/4fb1ceccee3eba7f3fad1b80e0fb6f9fbee1a2275b0514cd104be78b8a8a7373.jpg)

Bereft of life herestsin peace! Ifyouhadn'tnailed hi=..

![](images/ef27e079c376bc70804b3a1cf8fb83239a9775c33a3356607c5a3f6aa8da2963.jpg)

# Word2Vec工具

# Gensim工具

pip install gensim  
开源的Python工具包  
可以从非结构化文本中，无监督地学习到隐层的主题向  
量表达  
每一个向量变换的操作都对应着一个主题模型  
支持TF-IDF，LDA，LSA，Word2vec等多种主题模型算法

# 使用方法：

：建立词向量模型：word2vec.Word2Vec(sentences)window,句子中当前单词和被预测单词的最大距离mincount,需要训练词语的最小出现次数，默认为5size,向量维度，默认为100worker训练使用的线程数，默认为1即不使用多线程

模型保存 model.save(fname) 模型加载 model.load(fname)

# Word2Vec工具

# 数据集：西游记

journey_to_the_west.txt  
计算小说中的人物相似度，比如孙悟空与猪八戒，孙悟空与  
孙行者

# 方案步骤:

Step1，使用分词工具进行分词，比如NLTK,JIEBA：Step2，将训练语料转化成一个sentence的迭代器：Step3，使用word2vec进行训练  
Step4，计算两个单词的相似度

<html><body><table><tr><td>西记(吴承恩) 西游记 作者： 旱承恩 西游记 却以丰官現奇的想字描写了师走四 了取经人排除求雖的战斗精神，小说是人战明 第001回 灵根青孕 原流出 第002回 悟问若提直好理 第003回 四海千山皆拱代 第004回 官封弼马心何足 第005回 第006回 现音赴会问原田 第007回 卦中逃大圣 第008回 我带造生传征乐 附录 第009回 老尤王拙计 卫王亲 第010回 二将车宫门镇电 第011回 度孤乱蒂璃正空门 第012回 第013回 第014回 心猿归正 第015回 蛇盘山诣神暗古 第016回 观音院曾谋宝贝 第017回 孙行者大闹黑口山 孤世音收代主旱 怪 第018回 孤音臨居 留此 第019回 云楼洞悟空收八戒 得居山玄壮寧心紅</td></tr></table></body></html>

# Word2Vec工具

#字词分割，对整个文件内容进行字词分割

def segment_lines(file_list,segment_out_dir,stopwords=[]):for i,file in enumerate(file_list):segment_out_name $\scriptstyle 1 = 0 s$ .path.join(segment_out_dir,'segment_0.txt'.format(i)with open(file,'rb') as f:document $\mathbf { \tau } = \mathbf { \tau }$ f.read()document_cut $\mathbf { \tau } = \mathbf { \tau }$ jieba.cut(document)sentence_segment=[]for word in document_cut:if word not in stopwords:sentence_segment.append(word)result $\mathbf { \tau } = \mathbf { \tau }$ ''join(sentence_segment)result $\mathbf { \tau } = \mathbf { \tau }$ result.encode('utf-8)with open(segment_out_name,'wb') as f2:f2.write(result)  
# 对source中的txt文件进行分词，输出到segment目录中  
file_list $\ c =$ files_processing.get_files_list('./source',postfix $\mathbf { \tau } = \mathbf { \dot { \tau } }$ \*.txt')  
segment_lines(file_list,'./segment')  
西游记（吴承思  
西游记  
作者：吴承思西游记却 以 丰富 瑰奇 的 想象 描写 了 师徒 四众的精怪生动地表现了无情的山川的险阻，并以  
第第第第第第第第附第第第第第第第第第第第第第第 001 回 灵根育孕 源流 出 心性他持大道生002 I回 悟彻 菩提 真 妙理 断 魔 归本 合元神003 回 四海 千山 皆拱伏 九山 十类 尽 除名004 回 官封弼 马心 何足 注 齐 天意 未宁005 I回 乱 蟠桃 大圣 偷丹 反 天宫 诣神 捉 怪006 回 观音 赴 会问 原田 小至  薛 大至007 I回回 八卦 炉中 逃 大圣 五行 山下 定心 猿008 我佛造经传极乐 观音 奉旨 上 长安录 陈光正 赴任 逢文 江流 僧 复九 报士009 回回 袁守迪 过算 无 曲 老 龙王 拙计 犯 天条010 二 将军 宫门 镇鬼 唐大宗 地府 还望011 回 还 受生 唐王 逗香果 度孤魂萧璃正空门012 回 玄里 秉迪里 大= 观音 显象 化 金蝉013 [回回 陷 虎穴 金星 解厄 双此 伯钦 留圖014 心猿 归正 六吨 无踪015 回 蛇 盘山 诸神 暗佑 应 涧 意马 收组016 I回 观音院 僧谋 宝贝 呈日山 怪古017 回 孙行者 大闹 黑凡山 现世音 收代 琵 景 怪018 回 观音院 唐僧脱 难 高老王 行者 薛登019 回 云栈 洞 悟空收 八戒 浮屠 山 玄奘 受心经020 回 昔此 居僧 有主 半山 中 八戒 争先021 回 护法设庄留 大圣 须弥 灵吉定 口度022 回 戒 士战 流」可 木又 奉法收悟净

# Word2Vec工具

#将Word转换成Vec，然后计算相似度   
from gensim.models import word2vec   
import multiprocessing   
#如果目录中有多个文件，可以使用PathLineSentences   
sentences $\mathbf { \tau } = \mathbf { \tau }$ word2vec.PathLineSentences('./segment') 0.96224165 0.98238677   
#设置模型参数，进行训练 0.9193349 0.9293375   
model $\mathbf { \tau } = \mathbf { \tau }$ word2vec.Word2Vec(sentences, size $= 1 0 0$ ,window $^ { \cdot = 3 }$ ,min_count $\mathbf { \tau } = \mathbf { \dot { \tau } }$ 1)   
print(model.wv.similarity('孙悟空'，'猪八戒))   
print(model.wv.similarity('孙悟空'，'孙行者))   
#设置模型参数，进行训练   
model2 $\mathbf { \tau } = \mathbf { \tau }$ word2vec.Word2Vec(sentences, size $\ c =$ 128, window $^ { = 5 }$ min_count=5,   
workers $\ c =$ multiprocessing.cpu_count()   
#保存模型   
model2.save('./models/word2Vec.model")   
print(model2.wv.similarity('孙悟空','猪八戒))   
print(model2.wv.similarity('孙悟空','孙行者))   
print(model2.wv.most_similar(positive $\ c =$ ['孙悟空'，'唐僧'],negative $\ c =$ ['孙行者'))

[(菩萨\*, 0.9546594619750977)， ('何干', 0.9491345286369324)(长老'， 0.9437956809997559)， ('沙 僧见°, 0.943665623664856),(悟净'， 0.9424765706062317)， ('手指', 0.9390666484832764),(银角', 0.937991201877594)， ( 大子 '， 0.9359638690948486)， (',0.9339208006858826), (\*祥师', 0.9319193363189697)]

Thinking: 得到了特征表达 (itemrepresentation），有什么用?

# 基于内容的推荐：

将你看的item，相似的item推荐给你通过物品表示Item Representation $\Rightarrow$ 抽取特征TF-IDF=>返回给某个文本的“关键词-TFIDF值”的词数对TF-IDF可以帮我们抽取文本的重要特征，做成itemembedding

Thinking: 如何使用事物的特征表达， 进行相似推荐？

计算item之间的相似度矩阵对于指定的item，选择相似度最大的Top-K个进行输出

Embedding的理解：

·Embedding指某个对象X被嵌入到另外一个对象Y中，映射 $f : X \to \mathbb { Y }$   
，一种降维方式，转换为维度相同的向量  
·矩阵分解中的User矩阵，第i行可以看成是第i个user的Embedding。Item矩阵中的第j列可以看成是对第j个Item的Embedding

![](images/3558471bf1214361ecf9202590444592d1c9a6bfc06851db5fe599d72a71fc2b.jpg)

# Word2Vec工具的使用：

·Word Embedding就是将Word嵌入到一个数学空间里，Word2vec，就是词嵌入的一种·可以将sentence中的word转换为固定大小的向量表达（Vector Respresentations），·其中意义相近的词将被映射到向量空间中相近的位置。  
·将待解决的问题转换成为单词word和文章doc的对应关系  
大V推荐中，大 $\mathsf { V } = >$ 单词，将每一个用户关注大V的顺序 $\Rightarrow$ 文章  
商品推荐中，商品 $\Rightarrow$ 单词，用户对商品的行为顺序 $\Rightarrow$ 文章

向量数据库

# 向量数据库

Thinking: 什么是向量数据库？

一种专门用于存储和检索高维向量数据的数据库。它将数据（如文本、图像、音频等）通过嵌入模型转换为向量形式，并通过高效的索引和搜索算法实现快速检索。

向量数据库的核心作用是实现相似性搜索，即通过计算向量之间的距离（如欧几里得距离、余弦相似度等）来找到与目标向量最相似的其他向量。它特别适合处理非结构化数据，支持语义搜索、内容推荐等场景。

Thinking: 如何存储和检索嵌入向量？

存储：向量数据库将嵌入向量存储为高维空间中的点，并为每个向量分配唯一标识符（ID），同时支持存储元数据。

检索：通过近似最近邻（ANN）算法（如PQ等）对向量进行索引和快速搜索。比如，FAISS和Milvus等数据库通过高效的索引结构加速检索。

# 常见的向量数据库

# 1.FAISS

特点：由Facebook开发，专注于高性能的相似性搜索，适合大规模静态数据集。

优势：检索速度快，支持多种索引类型

局限性：主要用于静态数据，更新和删除操作较复杂。

# 2.Milvus

特点：开源，支持分布式架构和动态数据更新。

优势：具备强大的扩展性和灵活的数据管理功能，

# 3.Pinecone

特点：托管的云原生向量数据库，支持高性能的向量搜索。

优势：完全托管，易于部署，适合大规模生产环境。

# 向量数据库与传统数据库的对比

# 1.数据类型

传统数据库：存储结构化数据（如表格、行、列）。

向量数据库：存储高维向量数据，适合非结构化数据。

# 2.查询方式

传统数据库：依赖精确匹配（如=、<、>）

向量数据库：基于相似度或距离度量（如欧几里得距离、余弦相似度）。

# 3.应用场景

传统数据库：适合事务记录和结构化信息管理

向量数据库：适合语义搜索、内容推荐等需要相似性计算的场景。

# 讨论与呈现

结合你的业务场景，你认为事物的特征提取重要么？有什么应用场景？

非结构化数据的理解，pdf，word等结构化数据的理解，excel，数据表等

如何对这些特征进行理解？

Thinking1：假设一个小说网站，有N部小说，每部小说都有摘要描述。如何针对该网站制定基于内容的推荐系统，即用户看了某部小说后，推荐其他相关的小说。原理和步骤是怎样的

Thinking2：Word2Vec的应用场景有哪些

Action1：使用Gensim中的Word2Vec对三国演义进行Word Embedding，分析和曹操最相近的词有哪些，曹操+刘备-张飞 $= ?$

数据集：three_kingdoms.txt

# Thank You Using data to solve problems