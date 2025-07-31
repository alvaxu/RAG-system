'''
程序说明：
## 1. 本程序用于进行词向量的加减运算并查找相似词
## 2. 使用训练好的Word2Vec模型
## 3. 支持多种词运算模式，如 king - man + woman = queen
'''

from gensim.models import Word2Vec
import os


def load_trained_model(model_path):
    """
    :function: 加载训练好的Word2Vec模型
    :param model_path: 模型文件路径
    :return: 训练好的模型
    """
    print(f"正在加载Word2Vec模型 {model_path}...")
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"模型文件 {model_path} 不存在，请先运行 V210_three_kingdoms_word2vec_training.py")
    
    model = Word2Vec.load(model_path)
    print("模型加载完成！")
    print(f"词汇表大小: {len(model.wv.key_to_index)}")
    
    return model


def find_similar_words(model, positive_words=None, negative_words=None, top_n=10):
    """
    :function: 查找相似词，支持正负词组合
    :param model: Word2Vec模型
    :param positive_words: 正向词列表
    :param negative_words: 负向词列表
    :param top_n: 返回前N个相似词
    :return: 相似词列表
    """
    # 处理默认值
    if positive_words is None:
        positive_words = []
    if negative_words is None:
        negative_words = []
    
    # 过滤掉不在词汇表中的词
    valid_positive = [word for word in positive_words if word in model.wv.key_to_index]
    valid_negative = [word for word in negative_words if word in model.wv.key_to_index]
    
    # 检查是否有无效词
    invalid_positive = set(positive_words) - set(valid_positive)
    invalid_negative = set(negative_words) - set(valid_negative)
    
    if invalid_positive:
        print(f"警告：以下正向词不在词汇表中: {invalid_positive}")
    if invalid_negative:
        print(f"警告：以下负向词不在词汇表中: {invalid_negative}")
    
    # 如果没有有效的词，返回空列表
    if not valid_positive and not valid_negative:
        print("没有有效的词用于计算相似度")
        return []
    
    try:
        # 使用gensim的most_similar方法进行词运算
        similar_words = model.wv.most_similar(
            positive=valid_positive,
            negative=valid_negative,
            topn=top_n
        )
        return similar_words
    except Exception as e:
        print(f"计算相似词时出错: {e}")
        return []


def get_word_similarity(model, word1, word2):
    """
    :function: 计算两个词之间的相似度
    :param model: Word2Vec模型
    :param word1: 第一个词
    :param word2: 第二个词
    :return: 相似度值
    """
    if word1 not in model.wv.key_to_index:
        print(f"词汇 '{word1}' 不在词汇表中")
        return None
    
    if word2 not in model.wv.key_to_index:
        print(f"词汇 '{word2}' 不在词汇表中")
        return None
    
    similarity = model.wv.similarity(word1, word2)
    return similarity


def main():
    """
    :function: 主函数
    :return: None
    """
    # 模型路径
    model_path = r"d:\\cursorprj\5-0415 5.Embeddings和向量数据库\word2vec - 250725\three_kingdoms\model\three_kingdoms_word2vec_with_stopwords.model"
    
    print("开始加载《三国演义》Word2Vec模型...")
    
    # 加载模型
    model = load_trained_model(model_path)
    
    print("\n模型加载完成！现在可以进行词向量运算和相似词查询。")
    print("输入示例：")
    print("1. 查找与'刘备'相似的词: positive=刘备, negative=, top_n=5")
    print("2. 词运算'关羽 + 张飞 - 刘备': positive=关羽,张飞, negative=刘备, top_n=5")
    print("3. 计算两词相似度: similarity=刘备,关羽")
    print("4. 输入'quit'退出程序\n")
    
    while True:
        try:
            user_input = input("请输入您的查询 (格式: positive=词1,词2,... negative=词3,词4,... top_n=5 或 similarity=词1,词2): ").strip()
            
            if user_input.lower() == 'quit':
                print("程序退出。")
                break
            
            # 处理相似度计算请求
            if user_input.startswith('similarity='):
                words = user_input[11:].split(',')
                if len(words) == 2:
                    word1, word2 = words[0].strip(), words[1].strip()
                    similarity = get_word_similarity(model, word1, word2)
                    if similarity is not None:
                        print(f"'{word1}' 和 '{word2}' 的相似度: {similarity:.4f}")
                else:
                    print("相似度计算格式错误，请使用: similarity=词1,词2")
                continue
            
            # 处理词运算请求
            positive_words = []
            negative_words = []
            top_n = 5
            
            parts = user_input.split()
            for part in parts:
                if part.startswith('positive='):
                    positive_str = part[9:]  # 跳过'positive='
                    if positive_str:
                        positive_words = [word.strip() for word in positive_str.split(',')]
                elif part.startswith('negative='):
                    negative_str = part[9:]  # 跳过'negative='
                    if negative_str:
                        negative_words = [word.strip() for word in negative_str.split(',')]
                elif part.startswith('top_n='):
                    try:
                        top_n = int(part[6:])  # 跳过'top_n='
                    except ValueError:
                        print("top_n参数必须是整数")
                        continue
            
            # 执行词运算
            similar_words = find_similar_words(model, positive_words, negative_words, top_n)
            
            if similar_words:
                print(f"\n词运算结果: {' + '.join(positive_words)} {' - ' + ' - '.join(negative_words) if negative_words else ''}")
                print("相似词列表:")
                for i, (word, similarity) in enumerate(similar_words, 1):
                    print(f"  {i}. {word}: {similarity:.4f}")
            else:
                print("未找到相似词或所有输入词都不在词汇表中。")
            
            print()  # 空行分隔
            
        except KeyboardInterrupt:
            print("\n程序被用户中断。")
            break
        except Exception as e:
            print(f"处理输入时出错: {e}")
            print("请检查输入格式是否正确。\n")


if __name__ == "__main__":
    main()