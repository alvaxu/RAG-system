'''
程序说明：
## 1. 本程序用于训练《三国演义》的Word2Vec模型
## 2. 使用V120版本生成的分词结果进行训练
## 3. 相比V210版本，此版本增加了停用词过滤功能
## 4. 停用词包括标点符号和常见虚词，以提高模型质量
'''

import json
from gensim.models import Word2Vec
import os


def load_stopwords(file_path):
    """
    :function: 加载停用词列表
    :param file_path: 停用词文件路径
    :return: 停用词集合
    """
    print(f"正在加载停用词 {file_path}...")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"停用词文件 {file_path} 不存在")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        stopwords = set(line.strip() for line in f if line.strip())
    
    print(f"停用词加载完成，共 {len(stopwords)} 个停用词")
    return stopwords


def filter_stopwords(segmented_sentences, stopwords):
    """
    :function: 过滤分词结果中的停用词
    :param segmented_sentences: 分词结果
    :param stopwords: 停用词集合
    :return: 过滤后的分词结果
    """
    print("开始过滤停用词...")
    
    # 统计过滤前的词数
    total_words_before = sum(len(sentence) for sentence in segmented_sentences)
    
    # 过滤停用词
    filtered_sentences = [
        [word for word in sentence if word not in stopwords]
        for sentence in segmented_sentences
    ]
    
    # 统计过滤后的词数
    total_words_after = sum(len(sentence) for sentence in filtered_sentences)
    
    print(f"停用词过滤完成")
    print(f"过滤前词数: {total_words_before}")
    print(f"过滤后词数: {total_words_after}")
    print(f"过滤掉的词数: {total_words_before - total_words_after}")
    
    return filtered_sentences


def load_segmented_data(file_path):
    """
    :function: 加载分词结果数据
    :param file_path: 分词结果文件路径
    :return: 分词结果列表
    """
    print(f"正在加载分词结果 {file_path}...")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"分词结果文件 {file_path} 不存在，请先运行 V120_three_kingdoms_segmentation.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        segmented_sentences = json.load(f)
    
    print(f"分词结果加载完成，共 {len(segmented_sentences)} 个句子")
    return segmented_sentences


def train_word2vec_model(segmented_sentences, model_save_path):
    """
    :function: 训练Word2Vec模型
    :param segmented_sentences: 分词结果
    :param model_save_path: 模型保存路径
    :return: 训练好的模型
    """
    print("开始训练Word2Vec模型...")
    # print(f"参数设置：vector_size=100, window=5, min_count=3, workers=4, epochs=15")
    print(f"参数设置：vector_size=200, window=5, min_count=3, workers=4, epochs=30")
    # 训练Word2Vec模型
    model = Word2Vec(
        sentences=segmented_sentences,
        vector_size=500,      # 词向量维度
        window=5,             # 窗口大小
        min_count=3,          # 最小词频
        workers=4,            # 线程数
        sg=1,                 # 使用Skip-gram模型
        epochs=50             # 训练轮数
    )
    
    print("模型训练完成！")
    
    # 保存模型
    print(f"正在保存模型到 {model_save_path}...")
    model.save(model_save_path)
    print("模型保存完成！")
    
    # 输出模型信息
    print(f"词汇表大小: {len(model.wv.key_to_index)}")
    
    return model


def main():
    """
    :function: 主函数
    :return: None
    """
    # 文件路径
    segmented_data_file = r"d:\\cursorprj\5-0415 5.Embeddings和向量数据库\word2vec - 250725\three_kingdoms\segments\V130_segmented_results.json"
    model_save_path = r"d:\\cursorprj\5-0415 5.Embeddings和向量数据库\word2vec - 250725\three_kingdoms\model\three_kingdoms_word2vec_with_stopwords.model"
    stopwords_file = r"d:\\cursorprj\5-0415 5.Embeddings和向量数据库\word2vec - 250725\stopwords.txt"
    
    print("开始训练《三国演义》Word2Vec模型（过滤停用词版本）...")
    
    # 加载分词结果
    segmented_sentences = load_segmented_data(segmented_data_file)
    
    # 加载停用词
    stopwords = load_stopwords(stopwords_file)
    
    # 过滤停用词
    filtered_sentences = filter_stopwords(segmented_sentences, stopwords)
    
    # 训练模型
    model = train_word2vec_model(filtered_sentences, model_save_path)
    
    print("\nWord2Vec模型训练和保存全部完成！")


if __name__ == "__main__":
    main()