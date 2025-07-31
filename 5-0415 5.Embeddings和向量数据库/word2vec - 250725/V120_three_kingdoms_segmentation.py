'''
程序说明：
## 1. 本程序用于对《三国演义》文本进行全面的分词处理
## 2. 保存分词结果供后续Word2Vec模型训练使用
## 3. 相比V100版本，此版本专注于完整的文本分词，不进行人物提取等额外分析
'''

import jieba
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
    # 去除多余的空白字符，但保留句号用于句子分割
    text = re.sub(r'\s+', '', text)
    return text


def segment_text_comprehensive(text):
    """
    :function: 对文本进行全面分词，按句子组织
    :param text: 文本内容
    :return: 分词结果列表
    """
    print("正在进行全面分词处理...")
    
    # 按句子分割（按句号分割）
    sentences = text.split('。')
    
    # 对每个句子进行分词
    segmented_sentences = []
    total_words = 0
    
    for i, sentence in enumerate(sentences):
        # if len(sentence.strip()) > 2:  # 过滤太短的句子
            # 使用jieba进行分词
        words = jieba.lcut(sentence.strip())
        # 过滤掉长度小于1的词
        words = [word for word in words if len(word) >= 1]
            
        if len(words) > 0:
            segmented_sentences.append(words)
            total_words += len(words)
            
        # 显示进度
        if (i + 1) % 1000 == 0:
            print(f"已处理 {i + 1} 个句子，共 {total_words} 个词")
    
    print(f"分词完成！共处理 {len(segmented_sentences)} 个句子，{total_words} 个词")
    return segmented_sentences


def save_segmented_results(segmented_sentences, output_file):
    """
    :function: 保存分词结果到文件
    :param segmented_sentences: 分词结果
    :param output_file: 输出文件路径
    :return: None
    """
    print(f"正在保存分词结果到 {output_file}...")
    
    # 保存为JSON格式
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(segmented_sentences, f, ensure_ascii=False)
    
    print("分词结果保存完成！")


def main():
    """
    :function: 主函数
    :return: None
    """
    # 文件路径
    input_file = r"d:\\cursorprj\\5-0415 5.Embeddings和向量数据库\\word2vec - 250725\\three_kingdoms\\source\\three_kingdoms.txt"
    output_file =r"d:\\cursorprj\\5-0415 5.Embeddings和向量数据库\\word2vec - 250725\\three_kingdoms\\segments\\V130_segmented_results.json"
    
    print("开始处理《三国演义》文本...")
    
    # 加载文本
    print("正在加载文本...")
    text = load_text(input_file)
    print(f"文本加载完成，共 {len(text)} 个字符")
    
    # 预处理文本
    print("正在预处理文本...")
    text = preprocess_text(text)
    
    # 分词
    segmented_sentences = segment_text_comprehensive(text)
    
    # 保存结果
    save_segmented_results(segmented_sentences, output_file)
    
    print("\n全部处理完成！")


if __name__ == "__main__":
    main()