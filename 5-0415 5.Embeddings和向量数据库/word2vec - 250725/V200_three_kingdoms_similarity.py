'''
程序说明：
## 1. 本程序用于训练Word2Vec模型并计算人物相似度
## 2. 基于分词结果进行模型训练
## 3. 提供人物相似度查询功能
## 4. 与V100版本不同的是，此版本可以读取V100版本的输出结果
'''

import jieba
from gensim.models import Word2Vec
import re
import json


def load_and_preprocess_text(file_path):
    """
    :function: 加载并预处理文本
    :param file_path: 文件路径
    :return: 句子列表
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # 预处理
    text = re.sub(r'^.*?正文', '正文', text, flags=re.DOTALL)
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'\[.*?\]', '', text)
    
    # 按句子分割（简单按句号分割）
    sentences = text.split('。')
    
    # 分词
    segmented_sentences = []
    for sentence in sentences:
        if len(sentence.strip()) > 5:  # 过滤太短的句子
            words = jieba.lcut(sentence.strip())
            # 过滤掉长度小于2的词
            words = [word for word in words if len(word) >= 2]
            if len(words) > 0:
                segmented_sentences.append(words)
    
    return segmented_sentences


def load_analysis_results(file_path):
    """
    :function: 加载第一个脚本的分析结果
    :param file_path: 分析结果文件路径
    :return: 分析结果字典
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            results = json.load(f)
        return results
    except FileNotFoundError:
        print(f"分析结果文件 {file_path} 不存在，请先运行 V100_three_kingdoms_word_analysis.py")
        return None


def train_word2vec(sentences):
    """
    :function: 训练Word2Vec模型
    :param sentences: 分词后的句子列表
    :return: 训练好的模型
    """
    print("正在训练Word2Vec模型...")
    model = Word2Vec(
        sentences=sentences,
        vector_size=100,      # 词向量维度
        window=5,             # 窗口大小
        min_count=5,          # 最小词频
        workers=4,            # 线程数
        sg=1,                 # 使用Skip-gram模型
        epochs=10             # 训练轮数
    )
    print("模型训练完成！")
    return model


def find_similar_characters(model, character, top_n=10):
    """
    :function: 查找相似人物
    :param model: 训练好的Word2Vec模型
    :param character: 目标人物
    :param top_n: 返回前N个相似人物
    :return: 相似人物列表
    """
    try:
        similar_chars = model.wv.most_similar(character, topn=top_n)
        return similar_chars
    except KeyError:
        print(f"词汇 '{character}' 不在词汇表中")
        return []


def main():
    """
    :function: 主函数
    :return: None
    """
    file_path = r"d:\\cursorprj\\5-0415 5.Embeddings和向量数据库\\word2vec - 250725\\three_kingdoms\\source\\three_kingdoms.txt"
    analysis_results_file = "V110_word_analysis_results.json"
    
    # 首先尝试加载第一个脚本的分析结果
    print("正在加载第一个脚本的分析结果...")
    analysis_results = load_analysis_results(analysis_results_file)
    
    if analysis_results:
        print("成功加载分析结果:")
        print(f"找到的主要人物: {analysis_results['characters']}")
        print(f"高频词数量: {len(analysis_results['word_frequency'])}")
    else:
        print("未找到分析结果，将直接处理原始文本...")
    
    # 加载和预处理文本
    print("正在加载和预处理文本...")
    sentences = load_and_preprocess_text(file_path)
    print(f"共处理 {len(sentences)} 个句子")
    
    # 训练Word2Vec模型
    model = train_word2vec(sentences)
    
    # 保存模型
    model.save("three_kingdoms_word2vec.model")
    print("模型已保存为 three_kingdoms_word2vec.model")
    
    # 查看词汇表大小
    print(f"词汇表大小: {len(model.wv.key_to_index)}")
    
    # 测试相似度计算
    # 如果有分析结果，使用其中的人物；否则使用默认列表
    if analysis_results:
        test_characters = analysis_results['characters'][:5]  # 取前5个人物测试
    else:
        test_characters = ['刘备', '关羽', '张飞', '曹操', '诸葛亮']
    
    for character in test_characters:
        if character in model.wv.key_to_index:
            print(f"\n与 '{character}' 最相似的人物:")
            similar_chars = find_similar_characters(model, character, 5)
            for char, similarity in similar_chars:
                print(f"  {char}: {similarity:.4f}")
        else:
            print(f"\n词汇 '{character}' 不在词汇表中")

if __name__ == "__main__":
    main()