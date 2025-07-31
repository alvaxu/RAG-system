'''
程序说明：
## 1. 本程序提供一些测试用例来验证词向量运算功能
## 2. 展示如何使用词向量进行各种运算
## 3. 可以作为用户使用参考
'''

from gensim.models import Word2Vec
import os


def load_model_and_test(model_path):
    """
    :function: 加载模型并运行测试用例
    :param model_path: 模型文件路径
    :return: None
    """
    if not os.path.exists(model_path):
        print(f"模型文件 {model_path} 不存在，请先训练模型。")
        return
    
    print("正在加载模型...")
    model = Word2Vec.load(model_path)
    print(f"模型加载完成，词汇表大小: {len(model.wv.key_to_index)}\n")
    
    # 测试用例
    test_cases = [
        {
            "description": "查找与'刘备'相似的词",
            "positive": ["刘备"],
            "negative": [],
            "top_n": 5
        },
        {
            "description": "查找与'曹操'相似的词",
            "positive": ["曹操"],
            "negative": [],
            "top_n": 5
        },
        {
            "description": "查找与'关羽'和'张飞'相似但与'刘备'不相似的词",
            "positive": ["关羽", "张飞"],
            "negative": ["刘备"],
            "top_n": 5
        },
        {
            "description": "查找与'诸葛亮'相似但与'谋士'不相似的词",
            "positive": ["诸葛亮"],
            "negative": ["谋士"],
            "top_n": 5
        },
        {
            "description": "查找与'战争'和'计策'相似但与'和平'不相似的词",
            "positive": ["战争", "计策"],
            "negative": ["和平"],
            "top_n": 5
        }
    ]
    
    # 运行测试用例
    for i, test_case in enumerate(test_cases, 1):
        print(f"测试用例 {i}: {test_case['description']}")
        print(f"运算: {' + '.join(test_case['positive'])} {' - ' + ' - '.join(test_case['negative']) if test_case['negative'] else ''}")
        
        # 过滤有效词
        valid_positive = [word for word in test_case['positive'] if word in model.wv.key_to_index]
        valid_negative = [word for word in test_case['negative'] if word in model.wv.key_to_index]
        
        if not valid_positive and not valid_negative:
            print("  跳过：所有输入词都不在词汇表中\n")
            continue
        
        try:
            similar_words = model.wv.most_similar(
                positive=valid_positive,
                negative=valid_negative,
                topn=test_case['top_n']
            )
            
            print("  结果:")
            for j, (word, similarity) in enumerate(similar_words, 1):
                print(f"    {j}. {word}: {similarity:.4f}")
        except Exception as e:
            print(f"  计算出错: {e}")
        
        print()  # 空行分隔
    
    # 词相似度测试
    print("词相似度测试:")
    similarity_tests = [
        ("刘备", "关羽"),
        ("曹操", "刘备"),
        ("诸葛亮", "周瑜"),
        ("战争", "和平"),
        ("谋士", "武将")
    ]
    
    for word1, word2 in similarity_tests:
        if word1 in model.wv.key_to_index and word2 in model.wv.key_to_index:
            similarity = model.wv.similarity(word1, word2)
            print(f"  '{word1}' 和 '{word2}' 的相似度: {similarity:.4f}")
        else:
            print(f"  跳过: '{word1}' 或 '{word2}' 不在词汇表中")


def main():
    """
    :function: 主函数
    :return: None
    """
    model_path = r"d:\\cursorprj\5-0415 5.Embeddings和向量数据库\word2vec - 250725\three_kingdoms\model\three_kingdoms_word2vec_with_stopwords.model"
    load_model_and_test(model_path)


if __name__ == "__main__":
    main()