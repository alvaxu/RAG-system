'''
程序说明：
## 1. 本程序用于收集逻辑回归模型的特征系数，并进行可视化和解释。
## 2. 输出系数条形图，并将重要特征及其解释写入md文件。
'''
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
import matplotlib

# 设置matplotlib支持中文
matplotlib.rcParams['font.sans-serif'] = ['SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False

# 读取归一化特征数据
train = pd.read_csv('V102_train_feature_norm.csv', encoding='utf-8')
X = train.drop(columns=['user_id', 'EmployeeNumber', 'Attrition'])
y = train['Attrition']

# 重新训练LR模型，保证与提交一致
model = LogisticRegression(max_iter=1000, random_state=42)
model.fit(X, y)

# 获取特征名和系数
coef = model.coef_[0]
features = X.columns
coef_df = pd.DataFrame({'feature': features, 'coef': coef})
coef_df = coef_df.sort_values('coef', key=abs, ascending=False)

# 可视化
plt.figure(figsize=(10, 8))
coef_df.head(20).set_index('feature')['coef'].plot(kind='barh', color=coef_df.head(20)['coef'].apply(lambda x: 'red' if x>0 else 'blue'))
plt.title('逻辑回归特征系数（前20，正为易离职，负为不易离职）')
plt.xlabel('系数')
plt.tight_layout()
plt.savefig('V104_lr_coef_top20.png', dpi=200)
plt.close()

# 生成解释md
with open('V104_lr_coef_analysis.md', 'w', encoding='utf-8') as f:
    f.write('''
程序说明：
## 1. 本文档分析逻辑回归模型的特征系数，解释哪些特征影响员工离职。
## 2. 系数为正，表示该特征越大越容易离职；系数为负，表示该特征越大越不易离职。
''')
    f.write('\n![](V104_lr_coef_top20.png)\n')
    f.write('\n### 主要特征及解释：\n')
    for _, row in coef_df.head(20).iterrows():
        direction = '越大越容易离职' if row['coef'] > 0 else '越大越不易离职'
        f.write(f"- {row['feature']}: 系数={row['coef']:.4f}，{direction}\n")
    f.write('\n### 综合分析：\n')
    f.write('根据系数，正系数特征（如加班、某些岗位、低满意度等）更易导致离职，负系数特征（如高满意度、高收入、某些岗位等）更易留任。具体请结合业务理解进一步分析。\n')

print('LR系数分析及可视化已完成，结果见V104_lr_coef_analysis.md和V104_lr_coef_top20.png。') 