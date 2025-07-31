'''
程序说明：
## 1. 本程序用于对《三国演义》文本进行分词处理
## 2. 提取关键人物并计算相似度
## 3. 使用jieba进行分词，gensim训练word2vec模型
'''

import jieba
import jieba.posseg as pseg
from collections import Counter
import re
import json


def load_text(file_path):
    """
    :function: 加载文本文件
    :param file_path: 文件路径
    :return: 文本内容
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    return text


def preprocess_text(text):
    """
    :function: 预处理文本，去除无关内容
    :param text: 原始文本
    :return: 处理后的文本
    """
    # 去除开头的标题和作者信息
    text = re.sub(r'^.*?正文', '正文', text, flags=re.DOTALL)
    # 去除注释和特殊符号
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'\[.*?\]', '', text)
    # 去除多余的空白字符
    text = re.sub(r'\s+', '', text)
    return text


def extract_character_names(text):
    """
    :function: 提取文本中的人物名称
    :param text: 文本内容
    :return: 人物名称列表
    """
    # 定义主要人物
    main_characters = [
        '刘备', '关羽', '张飞', '诸葛亮', '曹操', '孙权',
        '赵云', '吕布', '周瑜', '黄忠', '马超', '魏延',
        '张角', '张宝', '张梁', '董卓', '袁绍', '袁术'
    ]
    
    # 在文本中查找这些人物
    found_characters = []
    for character in main_characters:
        if character in text:
            found_characters.append(character)
    
    return found_characters


def segment_text(text):
    """
    :function: 对文本进行分词
    :param text: 文本内容
    :return: 分词结果
    """
    # 使用jieba进行分词
    words = jieba.lcut(text)
    # 过滤掉长度小于2的词
    words = [word for word in words if len(word) >= 2]
    return words


def get_word_frequency(words, top_n=100):
    """
    :function: 获取词频统计
    :param words: 分词结果
    :param top_n: 返回前N个高频词
    :return: 高频词列表
    """
    word_freq = Counter(words)
    return word_freq.most_common(top_n)


def save_results(characters, word_freq, output_file):
    """
    :function: 保存分析结果到文件
    :param characters: 人物列表
    :param word_freq: 词频统计
    :param output_file: 输出文件路径
    :return: None
    """
    results = {
        'characters': characters,
        'word_frequency': word_freq[:50]  # 只保存前50个高频词
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"分析结果已保存到 {output_file}")


def analyze_text(file_path, output_file):
    """
    :function: 主要分析函数
    :param file_path: 文件路径
    :param output_file: 输出文件路径
    :return: None
    """
    print("正在加载文本...")
    text = load_text(file_path)
    
    print("正在预处理文本...")
    text = preprocess_text(text)
    
    print("正在提取人物名称...")
    characters = extract_character_names(text)
    print(f"找到的主要人物: {characters}")
    
    print("正在进行分词...")
    words = segment_text(text)
    
    print("正在统计词频...")
    word_freq = get_word_frequency(words, 50)
    print("高频词前10个:")
    for word, freq in word_freq[:10]:
        print(f"{word}: {freq}")
    
    print("正在保存结果...")
    save_results(characters, word_freq, output_file)
    
    print("\n文本分析完成！")


if __name__ == "__main__":
    # 文件路径
    file_path = r"d:\\cursorprj\\5-0415 5.Embeddings和向量数据库\\word2vec - 250725\\three_kingdoms\\source\\three_kingdoms.txt"
    output_file = "V110_word_analysis_results.json"
    
    # 执行分析
    analyze_text(file_path, output_file)