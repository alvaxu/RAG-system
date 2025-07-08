#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd

# 数据加载
df = pd.read_csv('./voice.csv')
df


# In[2]:


# 查看数据是否有缺失值
df.isnull().sum()


# In[3]:


print('样本个数：{}'.format(df.shape[0]))
print('男性个数：{}'.format(df[df['label'] == 'male'].shape[0]))
print('女性个数：{}'.format(df[df['label'] == 'female'].shape[0]))


# In[4]:


# 切分特征 与 Label
y = df.iloc[:, -1] # -1代表最后一列
x = df.iloc[:, :-1] #  :-1，从第0列一直到最后一列
x


# In[15]:


# 通过数据类型进行筛选
#df.select_dtypes(include='object')


# In[5]:


# 标签编码
from sklearn.preprocessing import LabelEncoder
#df.select_dtypes(include='O')
le = LabelEncoder()
y = le.fit_transform(y)
y


# In[6]:


# 需要对特征，进行归一化
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
# fit_transform = 先fit, 再transform
x = scaler.fit_transform(x)
x


# In[7]:


# 切分数据集
from sklearn.model_selection import train_test_split
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=2022)


# In[8]:


from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

lr_model = LogisticRegression()
lr_model.fit(x_train, y_train)
y_pred = lr_model.predict(x_test)
print('LR 预测结果：', y_pred)
print('LR 准确率：', accuracy_score(y_test, y_pred))


# In[9]:


# y = -0.03x1 + 0.18x2 + ... + w20x20
lr_model.coef_


# In[10]:


from sklearn.svm import SVC

svc_model = SVC()
svc_model.fit(x_train, y_train)
y_pred = svc_model.predict(x_test)
print('SVC 预测结果：', y_pred)
print('SVC 准确率：', accuracy_score(y_test, y_pred))


# In[11]:


import xgboost as xgb

param = {'boosting_type':'gbdt',
                         'objective' : 'binary:logistic', #任务目标
                         'eval_metric' : 'auc', #评估指标
                         'eta' : 0.001, #学习率
                         'max_depth' : 9, #树最大深度
                         'colsample_bytree':0.8, #设置在每次迭代中使用特征的比例
                         'subsample': 0.9, #样本采样比例
                         'subsample_freq': 8, #bagging的次数
                         'alpha': 0.5, #L1正则
                         'lambda': 0.5, #L2正则
        }
train_data = xgb.DMatrix(x_train, label=y_train)
test_data = xgb.DMatrix(x_test, label=y_test)
model = xgb.train(param, train_data, evals=[(train_data, 'train'), (test_data, 'test')], num_boost_round = 10000, early_stopping_rounds=200, verbose_eval=25)
y_pred = model.predict(test_data)
y_pred


# In[12]:


y_pred = [0 if x<0.5 else 1 for x in y_pred]
print('XGB 预测结果：', y_pred)
print('XGB 准确率：', accuracy_score(y_test, y_pred))


# In[13]:


import matplotlib.pyplot as plt
from xgboost import plot_importance

plot_importance(model)


# In[14]:


#help(model)
model.get_score()

