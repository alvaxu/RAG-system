import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from scipy.stats import norm
from sklearn.covariance import EllipticEnvelope
from sklearn.datasets import make_blobs

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 1. 生成带离群点的数据并保存
X, y = make_blobs(n_samples=300, centers=2, cluster_std=1.0, random_state=42)
X[-10:] += 5  # 添加10个离群点
df = pd.DataFrame(X, columns=["x1", "x2"])
df.to_excel("abnormal.xlsx", index=False)
print("数据生成完成并保存为abnormal.xlsx")

# 2. 读取数据
data = pd.read_excel('abnormal.xlsx')
print("\n数据前5行:")
print(data.head())

# 3. 原始数据分布可视化
plt.figure(figsize=(10, 10))
plt.scatter(data['x1'], data['x2'])
plt.title('原始数据分布')
plt.xlabel('x1')
plt.ylabel('x2')
plt.savefig('original.png', dpi=300, bbox_inches='tight')
plt.close()

# 4. 特征分布直方图
x1 = data['x1']
x2 = data['x2']

plt.figure(figsize=(20, 10))
plt.subplot(121)
plt.hist(x1, bins=100)
plt.title('x1 分布直方图')
plt.xlabel('x1')
plt.ylabel('频数')

plt.subplot(122)
plt.hist(x2, bins=100)
plt.title('x2 分布直方图')
plt.xlabel('x2')
plt.ylabel('频数')

plt.savefig('distribution.png', dpi=300, bbox_inches='tight')
plt.close()

# 5. 高斯分布概率密度函数可视化
x1_mean, x1_sigma = x1.mean(), x1.std()
x2_mean, x2_sigma = x2.mean(), x2.std()

x1_range = np.linspace(x1.min(), x1.max(), 300)
x1_normal = norm.pdf(x1_range, x1_mean, x1_sigma)
x2_range = np.linspace(x2.min(), x2.max(), 300)
x2_normal = norm.pdf(x2_range, x2_mean, x2_sigma)

plt.figure(figsize=(20, 10))
plt.subplot(121)
plt.plot(x1_range, x1_normal)
plt.title('x1 的高斯分布概率密度')
plt.xlabel('x1 值')
plt.ylabel('概率密度')

plt.subplot(122)
plt.plot(x2_range, x2_normal)
plt.title('x2 的高斯分布概率密度')
plt.xlabel('x2 值')
plt.ylabel('概率密度')

plt.savefig('normal.png', dpi=300, bbox_inches='tight')
plt.close()

# 6. 异常检测模型训练与预测
# 尝试不同的contamination值（异常点比例）
contamination_values = [0.03, 0.05, 0.1]  # 可调整的阈值

for i, contamination in enumerate(contamination_values):
    # 构建模型
    ad_model = EllipticEnvelope(contamination=contamination, random_state=42)
    ad_model.fit(data)
    y_predict = ad_model.predict(data)
    
    # 打印检测结果
    print(f"\n当contamination={contamination}时，检测结果:")
    print(pd.Series(y_predict).value_counts())
    print(f"异常点数量: {sum(y_predict == -1)}")
    
    # 可视化预测结果
    plt.figure(figsize=(10, 10))
    # 正常点
    plt.scatter(data['x1'][y_predict == 1], data['x2'][y_predict == 1], 
                marker='D', label='正常点')
    # 异常点
    plt.scatter(data['x1'][y_predict == -1], data['x2'][y_predict == -1], 
                marker='*', facecolor='none', edgecolor='red', s=150, label='异常点')
    
    plt.title(f'异常检测结果 (contamination={contamination})')
    plt.xlabel('x1')
    plt.ylabel('x2')
    plt.legend()
    plt.savefig(f'abnormal_detect_{contamination}.png', dpi=300, bbox_inches='tight')
    plt.close()

print("\n所有结果已保存为图片文件")
