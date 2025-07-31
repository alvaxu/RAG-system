'''
程序说明：
## 1. 本程序用于训练《三国演义》的Word2Vec模型
## 2. 使用V120版本生成的分词结果进行训练
## 3. 相比V200版本，此版本专注于模型训练，不进行相似度计算
'''

import json
from gensim.models import Word2Vec
import os


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
    print(f"参数设置：vector_size=100, window=5, min_count=3, workers=4, epochs=15")
    
    # 训练Word2Vec模型
    model = Word2Vec(
        sentences=segmented_sentences,
        vector_size=100,      # 词向量维度
        window=5,             # 窗口大小
        min_count=3,          # 最小词频
        workers=4,            # 线程数
        sg=1,                 # 使用Skip-gram模型
        epochs=15             # 训练轮数
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
    segmented_data_file = r"d:\\cursorprj\\5-0415 5.Embeddings和向量数据库\\word2vec - 250725\\three_kingdoms\\segments\\V130_segmented_results.json"
    model_save_path = r"d:\\cursorprj\\5-0415 5.Embeddings和向量数据库\\word2vec - 250725\\three_kingdoms\\model\\V220_three_kingdoms_word2vec.model"
    
    print("开始训练《三国演义》Word2Vec模型...")
    
    # 加载分词结果
    segmented_sentences = load_segmented_data(segmented_data_file)
    
    # 训练模型
    model = train_word2vec_model(segmented_sentences, model_save_path)
    
    print("\nWord2Vec模型训练和保存全部完成！")


if __name__ == "__main__":
    main()