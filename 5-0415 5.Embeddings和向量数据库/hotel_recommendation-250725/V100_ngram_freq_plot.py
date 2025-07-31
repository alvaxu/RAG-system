# V100_ngram_freq_plot.py
'''
程序说明：
## 1. 本程序用于统计Seattle_Hotels.csv中酒店描述(desc)字段的n-gram词频，并画出TopK的柱状图。
## 2. 支持1-gram、2-gram、3-gram，结果可视化，便于后续文本分析和特征工程。
'''

import pandas as pd
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import CountVectorizer

def get_topk_ngrams(texts, ngram_range=(1,1), topk=20):
    """
    :function: 统计文本列表中的n-gram词频，返回TopK
    :param texts: 文本列表
    :param ngram_range: ngram范围，如(1,1)为1-gram，(2,2)为2-gram
    :param topk: 返回的TopK数量
    :return: [(ngram, 频次), ...]，按频次降序排列
    """
    vectorizer = CountVectorizer(ngram_range=ngram_range, stop_words='english')
    X = vectorizer.fit_transform(texts)
    sum_words = X.sum(axis=0)
    words_freq = [(word, int(sum_words[0, idx])) for word, idx in vectorizer.vocabulary_.items()]
    words_freq = sorted(words_freq, key=lambda x: x[1], reverse=True)
    return words_freq[:topk]

def plot_ngrams(ngrams, title, save_path=None):
    """
    :function: 绘制n-gram词频柱状图，并可选择保存图片
    :param ngrams: [(ngram, 频次), ...]
    :param title: 图表标题
    :param save_path: 图片保存路径（可选）
    :return: None
    """
    words = [x[0] for x in ngrams]
    freqs = [x[1] for x in ngrams]
    plt.figure(figsize=(12,5))
    plt.bar(words, freqs)
    plt.title(title)
    plt.xlabel('ngram')
    plt.ylabel('频次')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=200, bbox_inches='tight')
        print(f"图片已保存到: {save_path}")
    plt.show()

if __name__ == '__main__':
    # 读取数据
    df = pd.read_csv('Seattle_Hotels.csv', encoding='latin1')
    descs = df['desc'].fillna('').tolist()
    # 支持中文
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
    # 1-gram
    top1 = get_topk_ngrams(descs, ngram_range=(1,1), topk=20)
    print("1-gram Top20:")
    for w, f in top1:
        print(f"{w}: {f}")
    plot_ngrams(top1, "酒店描述 1-gram 词频Top20", save_path="1gram_top20.png")

    # 2-gram
    top2 = get_topk_ngrams(descs, ngram_range=(2,2), topk=20)
    print("\n2-gram Top20:")
    for w, f in top2:
        print(f"{w}: {f}")
    plot_ngrams(top2, "酒店描述 2-gram 词频Top20", save_path="2gram_top20.png")

    # 3-gram
    top3 = get_topk_ngrams(descs, ngram_range=(3,3), topk=20)
    print("\n3-gram Top20:")
    for w, f in top3:
        print(f"{w}: {f}")
    plot_ngrams(top3, "酒店描述 3-gram 词频Top20", save_path="3gram_top20.png") 