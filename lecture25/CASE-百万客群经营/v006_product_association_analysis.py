"""
程序说明：

## 1. 使用Apriori算法分析客户产品组合模式
   - 分析存款/理财/基金/保险的频繁组合
   - 计算关联规则的支持度、置信度和提升度
   - 可视化分析结果

## 2. 特点
   - 使用mlxtend库实现Apriori算法
   - 支持调试模式和完整数据分析模式
   - 结果输出到CSV文件便于后续分析
"""

import pandas as pd
import numpy as np
from mlxtend.frequent_patterns import apriori
from mlxtend.frequent_patterns import association_rules
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')


# 设置中文显示
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

class ProductAssociationAnalysis:
    """
    产品关联分析类
    """
    def __init__(self, behavior_file='customer_behavior_assets.csv', debug_mode=False):
        """
        初始化函数
        :param behavior_file: 客户行为数据文件路径
        :param debug_mode: 是否为调试模式，True则只分析部分数据
        """
        self.debug_mode = debug_mode
        self.data = self._load_data(behavior_file)
        self.product_columns = ['deposit_flag', 'financial_flag', 'fund_flag', 'insurance_flag']
        
    def _load_data(self, file_path):
        """
        加载数据
        :param file_path: 数据文件路径
        :return: DataFrame对象
        """
        df = pd.read_csv(file_path)
        if self.debug_mode:
            print("调试模式：只分析前1000条数据")
            df = df.head(1000)
        return df
    
    def prepare_transaction_data(self):
        """
        准备交易数据，将标志位转换为0/1格式
        :return: 处理后的DataFrame
        """
        # 确保标志位为数值型
        for col in self.product_columns:
            self.data[col] = self.data[col].fillna(0).astype(int)
        
        return self.data[self.product_columns]
    
    def run_apriori_analysis(self, min_support=0.1, min_confidence=0.5):
        """
        运行Apriori分析
        :param min_support: 最小支持度
        :param min_confidence: 最小置信度
        :return: 频繁项集和关联规则
        """
        print(f"开始Apriori分析 (最小支持度={min_support}, 最小置信度={min_confidence})")
        
        # 准备交易数据
        transaction_data = self.prepare_transaction_data()
        
        # 发现频繁项集
        frequent_itemsets = apriori(transaction_data, 
                                  min_support=min_support, 
                                  use_colnames=True)
        
        # 生成关联规则
        rules = association_rules(frequent_itemsets, 
                                metric="confidence", 
                                min_threshold=min_confidence)
        
        return frequent_itemsets, rules
    
    def visualize_results(self, rules):
        """
        可视化分析结果
        :param rules: 关联规则DataFrame
        """
        # 创建散点图：支持度vs置信度
        plt.figure(figsize=(10, 6))
        plt.scatter(rules['support'], rules['confidence'], alpha=0.5)
        plt.xlabel('支持度')
        plt.ylabel('置信度')
        plt.title('关联规则支持度vs置信度分布')
        plt.savefig('v006_association_rules_scatter.png')
        plt.close()
        
        # 创建热力图：产品组合频率
        pivot = pd.crosstab(index=self.data['deposit_flag'],
                           columns=self.data['financial_flag'])
        plt.figure(figsize=(8, 6))
        sns.heatmap(pivot, annot=True, fmt='d', cmap='YlOrRd')
        plt.title('存款-理财产品组合频率')
        plt.savefig('v006_product_combination_heatmap.png')
        plt.close()
    
    def save_results(self, rules, output_file='v006_association_rules.csv'):
        """
        保存分析结果
        :param rules: 关联规则DataFrame
        :param output_file: 输出文件路径
        """
        # 格式化规则输出
        rules['antecedents'] = rules['antecedents'].apply(lambda x: ', '.join(list(x)))
        rules['consequents'] = rules['consequents'].apply(lambda x: ', '.join(list(x)))
        
        # 按照提升度排序
        rules = rules.sort_values('lift', ascending=False)
        
        # 保存到CSV文件
        rules.to_csv(output_file, index=False, encoding='utf-8')
        print(f"分析结果已保存到: {output_file}")

def main():
    """
    主函数
    """
    print("\n=== 产品关联分析参数设置 ===")
    
    # 调试模式选择
    debug_input = input("是否启用调试模式？(y/n，默认n): ").strip().lower()
    debug_mode = debug_input == 'y'
    
    # 最小支持度设置
    while True:
        try:
            support = input("请输入最小支持度 (0-1之间，默认0.1): ").strip()
            min_support = float(support) if support else 0.1
            if 0 <= min_support <= 1:
                break
            print("支持度必须在0到1之间！")
        except ValueError:
            print("请输入有效的数字！")
    
    # 最小置信度设置
    while True:
        try:
            confidence = input("请输入最小置信度 (0-1之间，默认0.5): ").strip()
            min_confidence = float(confidence) if confidence else 0.5
            if 0 <= min_confidence <= 1:
                break
            print("置信度必须在0到1之间！")
        except ValueError:
            print("请输入有效的数字！")
    
    print("\n=== 参数设置完成 ===")
    print(f"调试模式: {'是' if debug_mode else '否'}")
    print(f"最小支持度: {min_support}")
    print(f"最小置信度: {min_confidence}")
    
    # 创建分析器实例
    analyzer = ProductAssociationAnalysis(debug_mode=debug_mode)
    
    # 运行分析
    print("\n正在进行产品关联分析...")
    frequent_itemsets, rules = analyzer.run_apriori_analysis(
        min_support=min_support,
        min_confidence=min_confidence
    )
    
    # 可视化结果
    print("\n正在生成可视化图表...")
    analyzer.visualize_results(rules)
    
    # 保存结果
    analyzer.save_results(rules)
    
    # 打印一些关键发现
    print("\n关键发现:")
    print(f"- 共发现 {len(frequent_itemsets)} 个频繁项集")
    print(f"- 共生成 {len(rules)} 条关联规则")
    print("- 前3个最强关联规则:")
    top_rules = rules.nlargest(3, 'lift')[['antecedents', 'consequents', 'support', 'confidence', 'lift']]
    print(top_rules.to_string(index=False))

if __name__ == "__main__":
    main() 