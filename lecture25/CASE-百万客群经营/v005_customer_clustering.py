'''
程序说明：

## 1. 本程序实现客户分群分析,将客户分为不同的群组(如高复购、中产家庭、年轻高消费等)
## 2. 使用K-means聚类算法,结合客户的人口统计学特征、资产情况和行为特征进行分群
## 3. 对每个群组进行特征分析,生成群组画像
## 4. 支持调试模式和完整数据分析模式
'''

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

class CustomerClustering:
    """
    客户分群分析类
    """
    def __init__(self, is_debug=False):
        """
        初始化客户分群分析类
        :param is_debug: 是否为调试模式,默认False
        """
        self.is_debug = is_debug
        self.customer_base = None
        self.customer_behavior = None
        self.merged_data = None
        self.scaled_features = None
        self.feature_columns = None
        self.cluster_labels = None
        self.cluster_profiles = None
        
    def load_data(self):
        """
        加载客户数据
        :return: None
        """
        print("正在加载数据...")
        # 读取客户基础信息表
        self.customer_base = pd.read_csv('customer_base.csv')
        # 读取客户行为与资产表
        self.customer_behavior = pd.read_csv('customer_behavior_assets.csv')
        
        # 调试模式下只使用部分数据
        if self.is_debug:
            print("调试模式: 使用部分数据进行分析")
            self.customer_base = self.customer_base.head(1000)
            self.customer_behavior = self.customer_behavior.head(1000)
            
        print(f"加载完成: 基础信息表 {len(self.customer_base)} 条记录")
        print(f"加载完成: 行为资产表 {len(self.customer_behavior)} 条记录")

    def preprocess_data(self):
        """
        数据预处理:合并数据、处理缺失值、编码分类变量
        :return: None
        """
        print("正在进行数据预处理...")
        
        # 合并两张表
        self.merged_data = pd.merge(
            self.customer_base,
            self.customer_behavior,
            on='customer_id',
            how='inner'
        )
        
        # 选择用于聚类的特征
        self.feature_columns = [
            'age',                              # 年龄
            'monthly_income',                   # 月收入
            'total_assets',                     # 总资产
            'financial_repurchase_count',       # 理财复购次数
            'credit_card_monthly_expense',      # 信用卡月消费
            'investment_monthly_count',         # 月投资次数
            'app_login_count',                  # APP登录次数
            'product_count'                     # 产品持有数
        ]
        
        # 处理缺失值
        for col in self.feature_columns:
            self.merged_data[col].fillna(self.merged_data[col].median(), inplace=True)
        
        # 标准化特征
        scaler = StandardScaler()
        self.scaled_features = scaler.fit_transform(self.merged_data[self.feature_columns])
        
        print("数据预处理完成")

    def find_optimal_clusters(self, max_clusters=10):
        """
        使用轮廓系数找到最优的聚类数
        :param max_clusters: 最大聚类数
        :return: 最优聚类数
        """
        print("正在寻找最优聚类数...")
        silhouette_scores = []
        
        for n_clusters in range(2, max_clusters + 1):
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            cluster_labels = kmeans.fit_predict(self.scaled_features)
            score = silhouette_score(self.scaled_features, cluster_labels)
            silhouette_scores.append(score)
            print(f"聚类数 {n_clusters}: 轮廓系数 = {score:.3f}")
        
        optimal_clusters = silhouette_scores.index(max(silhouette_scores)) + 2
        print(f"最优聚类数: {optimal_clusters}")
        return optimal_clusters

    def perform_clustering(self, n_clusters):
        """
        执行聚类分析
        :param n_clusters: 聚类数量
        :return: None
        """
        print(f"正在执行{n_clusters}群聚类分析...")
        
        # 执行K-means聚类
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        self.cluster_labels = kmeans.fit_predict(self.scaled_features)
        
        # 将聚类标签添加到数据中
        self.merged_data['cluster'] = self.cluster_labels
        
        print("聚类分析完成")

    def analyze_clusters(self):
        """
        分析各个群组的特征
        :return: None
        """
        print("正在分析群组特征...")
        
        # 计算每个群组的特征均值
        self.cluster_profiles = self.merged_data.groupby('cluster')[self.feature_columns].mean()
        
        # 计算每个群组的规模
        cluster_sizes = self.merged_data['cluster'].value_counts()
        
        # 为每个群组生成画像
        cluster_descriptions = {}
        for cluster in range(len(self.cluster_profiles)):
            profile = self.cluster_profiles.loc[cluster]
            size = cluster_sizes[cluster]
            
            # 根据特征值确定群组特点
            characteristics = []
            if profile['age'] < 35:
                characteristics.append("年轻")
            elif profile['age'] > 50:
                characteristics.append("成熟")
                
            if profile['monthly_income'] > self.merged_data['monthly_income'].mean():
                characteristics.append("高收入")
            
            if profile['financial_repurchase_count'] > self.merged_data['financial_repurchase_count'].mean():
                characteristics.append("高复购")
                
            if profile['credit_card_monthly_expense'] > self.merged_data['credit_card_monthly_expense'].mean():
                characteristics.append("高消费")
                
            if profile['app_login_count'] > self.merged_data['app_login_count'].mean():
                characteristics.append("线上活跃")
                
            cluster_descriptions[cluster] = {
                'size': size,
                'percentage': size / len(self.merged_data) * 100,
                'characteristics': characteristics
            }
            
        # 打印群组描述
        print("\n群组画像分析结果:")
        for cluster, desc in cluster_descriptions.items():
            print(f"\n群组 {cluster}:")
            print(f"群组规模: {desc['size']} ({desc['percentage']:.1f}%)")
            print(f"特点: {', '.join(desc['characteristics'])}")
            print("\n主要指标均值:")
            for feature in self.feature_columns:
                print(f"{feature}: {self.cluster_profiles.loc[cluster, feature]:.2f}")

    def visualize_clusters(self):
        """
        可视化聚类结果
        :return: None
        """
        print("正在生成可视化图表...")
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 1. 群组规模分布
        plt.figure(figsize=(10, 6))
        cluster_sizes = self.merged_data['cluster'].value_counts()
        cluster_sizes.plot(kind='bar')
        plt.title('客户群组规模分布')
        plt.xlabel('群组')
        plt.ylabel('客户数量')
        plt.savefig('v005_cluster_sizes.png')
        plt.close()
        
        # 2. 特征雷达图
        cluster_means = self.merged_data.groupby('cluster')[self.feature_columns].mean()
        
        # 标准化数据用于雷达图
        scaler = StandardScaler()
        cluster_means_scaled = pd.DataFrame(
            scaler.fit_transform(cluster_means),
            columns=self.feature_columns,
            index=cluster_means.index
        )
        
        # 绘制雷达图
        angles = np.linspace(0, 2*np.pi, len(self.feature_columns), endpoint=False)
        angles = np.concatenate((angles, [angles[0]]))  # 闭合图形
        
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        
        for cluster in cluster_means_scaled.index:
            values = cluster_means_scaled.loc[cluster].values
            values = np.concatenate((values, [values[0]]))  # 闭合图形
            ax.plot(angles, values, 'o-', linewidth=2, label=f'群组 {cluster}')
            ax.fill(angles, values, alpha=0.25)
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(self.feature_columns)
        plt.title('客户群组特征雷达图')
        plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
        plt.savefig('v005_cluster_radar.png')
        plt.close()
        
        print("可视化图表已保存")

def main():
    """
    主函数
    """
    # 创建CustomerClustering实例
    clustering = CustomerClustering(is_debug=False)  # 默认使用调试模式
    
    # 加载数据
    clustering.load_data()
    
    # 数据预处理
    clustering.preprocess_data()
    
    # 寻找最优聚类数
    optimal_clusters = clustering.find_optimal_clusters()
    
    # 执行聚类
    clustering.perform_clustering(optimal_clusters)
    
    # 分析群组特征
    clustering.analyze_clusters()
    
    # 可视化结果
    clustering.visualize_clusters()

if __name__ == "__main__":
    main() 