import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings('ignore')  # 忽略所有警告

# 设置matplotlib中文字体，防止乱码
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False

# 读取数据
try:
    df = pd.read_csv('二组模拟数据.csv', encoding='utf-8')
except Exception:
    df = pd.read_csv('二组模拟数据.csv', encoding='gbk')

# 选择典型特征用于聚类
features = []
# 从新数据集选择合适的特征
selected_features = ['age', 'total_aum', 'monthly_transaction_amount', 'monthly_transaction_count',
                    'mobile_bank_login_count', 'branch_visit_count']

# 确保特征存在于数据集中
for f in selected_features:
    if f in df.columns:
        features.append(f)

X = df[features].fillna(0)

# 标准化特征
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 选择聚类数（如3类：高复购、中产家庭、年轻高消费）
n_clusters = 3
kmeans = KMeans(n_clusters=n_clusters, random_state=42)
df['cluster'] = kmeans.fit_predict(X_scaled)

# 输出每个群组的客户数和特征均值
print('各群组客户数：')
print(df['cluster'].value_counts().sort_index())
print('\n各群组特征均值：')
print(df.groupby('cluster')[features].mean())

pd.set_option('display.max_columns', None)  # 显示所有列
print('\n各群组用于聚类特征的均值（完整显示）：')
print(df.groupby('cluster')[features].mean())

# 输出每个群组的所有特征均值
print('\n各群组所有特征均值：')
print(df.groupby('cluster').mean(numeric_only=True))

# 可视化聚类结果（前两主成分）
from sklearn.decomposition import PCA
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)
plt.figure(figsize=(8, 6))
for i in range(n_clusters):
    plt.scatter(X_pca[df['cluster']==i, 0], X_pca[df['cluster']==i, 1], label=f'群组{i}')
plt.xlabel('主成分1')
plt.ylabel('主成分2')
plt.title('客户聚类分布（PCA降维可视化）')
plt.legend()
plt.tight_layout()
plt.savefig('customer_clusters.png', dpi=150)
plt.show()

# 保存聚类结果
result_cols = ['customer_id'] + features + ['cluster']
df[result_cols].to_csv('customer_cluster_result.csv', index=False, encoding='utf-8-sig')

# 中文注释：
# 本脚本用于客户聚类分析，输出每个群组的客户数和特征均值，并保存聚类结果和可视化图片。 