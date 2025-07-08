# LightGBM模型优化实现指南

## 一、数据质量优化实现方法

### 1. 特征相关性分析
```python
# 使用pandas和seaborn实现
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# 计算相关性矩阵
correlation_matrix = df.corr()

# 绘制热力图
plt.figure(figsize=(12, 10))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0)
plt.title('特征相关性热力图')
plt.show()

# 移除高度相关特征（相关系数>0.8）
def remove_highly_correlated_features(df, threshold=0.8):
    corr_matrix = df.corr().abs()
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    to_drop = [column for column in upper.columns if any(upper[column] > threshold)]
    return df.drop(to_drop, axis=1)
```

### 2. 缺失值处理
```python
# 缺失值分析
missing_values = df.isnull().sum()
missing_ratio = missing_values / len(df)

# 不同填充方法对比
from sklearn.impute import SimpleImputer, KNNImputer

# 均值填充
mean_imputer = SimpleImputer(strategy='mean')
# 中位数填充
median_imputer = SimpleImputer(strategy='median')
# KNN填充
knn_imputer = KNNImputer(n_neighbors=5)

# 对比不同填充方法的效果
def compare_imputation_methods(df, target_col):
    results = {}
    for method in ['mean', 'median', 'knn']:
        if method == 'knn':
            imputed_df = pd.DataFrame(knn_imputer.fit_transform(df), columns=df.columns)
        else:
            imputer = SimpleImputer(strategy=method)
            imputed_df = pd.DataFrame(imputer.fit_transform(df), columns=df.columns)
        
        # 评估填充效果（可以使用模型评分或其他指标）
        score = evaluate_model(imputed_df, target_col)
        results[method] = score
    return results
```

### 3. 异常值处理
```python
# IQR方法检测异常值
def detect_outliers_iqr(df, column):
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)]
    return outliers

# 隔离森林检测异常值
from sklearn.ensemble import IsolationForest
def detect_outliers_isolation_forest(df):
    iso_forest = IsolationForest(contamination=0.1, random_state=42)
    yhat = iso_forest.fit_predict(df)
    return df[yhat == -1]
```

## 二、模型优化方法

### 1. 特征交叉验证
```python
# 自动特征交叉
def create_interaction_features(df, numerical_cols):
    for i in range(len(numerical_cols)):
        for j in range(i+1, len(numerical_cols)):
            col1, col2 = numerical_cols[i], numerical_cols[j]
            # 乘积交互
            df[f'{col1}_{col2}_mult'] = df[col1] * df[col2]
            # 比率交互
            df[f'{col1}_{col2}_ratio'] = df[col1] / (df[col2] + 1e-6)
    return df

# 类别特征交叉
def create_categorical_interactions(df, cat_cols):
    for i in range(len(cat_cols)):
        for j in range(i+1, len(cat_cols)):
            col1, col2 = cat_cols[i], cat_cols[j]
            df[f'{col1}_{col2}'] = df[col1].astype(str) + '_' + df[col2].astype(str)
    return df
```

### 2. 参数优化
```python
# 网格搜索
from sklearn.model_selection import GridSearchCV
param_grid = {
    'num_leaves': [31, 50, 100],
    'max_depth': [5, 7, 9],
    'learning_rate': [0.01, 0.05, 0.1],
    'n_estimators': [100, 200, 300],
    'min_child_samples': [20, 30, 50]
}

grid_search = GridSearchCV(
    estimator=lgb.LGBMClassifier(),
    param_grid=param_grid,
    cv=5,
    scoring='roc_auc',
    n_jobs=-1
)

# 贝叶斯优化
from sklearn.model_selection import cross_val_score
from bayes_opt import BayesianOptimization

def lgb_evaluate(**params):
    params = {
        'num_leaves': int(params['num_leaves']),
        'max_depth': int(params['max_depth']),
        'learning_rate': params['learning_rate']
    }
    clf = lgb.LGBMClassifier(**params)
    return cross_val_score(clf, X, y, cv=5, scoring='roc_auc').mean()

optimizer = BayesianOptimization(
    f=lgb_evaluate,
    pbounds={
        'num_leaves': (10, 100),
        'max_depth': (3, 10),
        'learning_rate': (0.01, 0.1)
    }
)
```

### 3. SHAP值分析
```python
import shap

# 计算SHAP值
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X)

# 特征重要性可视化
shap.summary_plot(shap_values, X)

# 单个预测解释
shap.force_plot(explainer.expected_value, shap_values[0,:], X.iloc[0,:])

# 特征交互分析
shap.dependence_plot("feature_name", shap_values, X)
```

## 三、业务分析实现

### 1. 客群细分
```python
# K-means聚类
from sklearn.cluster import KMeans
def customer_segmentation(df, n_clusters=5):
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    df['cluster'] = kmeans.fit_predict(df)
    
    # 分析各群体特征
    cluster_stats = df.groupby('cluster').agg({
        'total_assets': 'mean',
        'monthly_income': 'mean',
        'age': 'mean',
        'target': 'mean'
    })
    return cluster_stats

# 按群体建模
def train_models_by_segment(df, segments):
    models = {}
    for segment in segments:
        segment_data = df[df['cluster'] == segment]
        model = train_lightgbm(segment_data)
        models[segment] = model
    return models
```

### 2. 时间序列分析
```python
# 趋势分析
from statsmodels.tsa.seasonal import seasonal_decompose
def analyze_time_series(df, date_column, value_column):
    df = df.set_index(date_column)
    decomposition = seasonal_decompose(df[value_column], period=12)
    
    # 绘制趋势、季节性和残差
    fig, (ax1,ax2,ax3,ax4) = plt.subplots(4,1, figsize=(15,12))
    decomposition.observed.plot(ax=ax1)
    decomposition.trend.plot(ax=ax2)
    decomposition.seasonal.plot(ax=ax3)
    decomposition.resid.plot(ax=ax4)
```

## 四、模型监控实现

### 1. 性能监控
```python
def monitor_model_performance(predictions, actuals, timestamp):
    metrics = {
        'timestamp': timestamp,
        'auc': roc_auc_score(actuals, predictions),
        'accuracy': accuracy_score(actuals, predictions),
        'precision': precision_score(actuals, predictions),
        'recall': recall_score(actuals, predictions)
    }
    
    # 保存监控指标
    save_metrics_to_db(metrics)
    
    # 检查是否需要报警
    check_metrics_threshold(metrics)
```

### 2. 特征漂移检测
```python
from scipy.stats import ks_2samp

def detect_feature_drift(reference_data, current_data, threshold=0.05):
    drift_features = []
    for feature in reference_data.columns:
        statistic, p_value = ks_2samp(
            reference_data[feature],
            current_data[feature]
        )
        if p_value < threshold:
            drift_features.append(feature)
    return drift_features
```

## 五、风险控制实现

### 1. 预测稳定性评估
```python
def assess_prediction_stability(model, data, n_iterations=100):
    predictions = []
    for _ in range(n_iterations):
        # 添加随机噪声
        noisy_data = add_noise(data.copy())
        pred = model.predict_proba(noisy_data)
        predictions.append(pred)
    
    # 计算预测方差
    prediction_std = np.std(predictions, axis=0)
    return prediction_std

def identify_unstable_predictions(prediction_std, threshold=0.1):
    return np.where(prediction_std > threshold)[0]
```

### 2. 错误案例分析
```python
def analyze_error_cases(y_true, y_pred, data):
    # 找出预测错误的案例
    errors = (y_true != y_pred)
    error_cases = data[errors]
    
    # 统计错误案例的特征分布
    error_stats = {
        'feature_distributions': error_cases.describe(),
        'feature_importance': analyze_feature_importance(error_cases)
    }
    
    # 聚类错误案例
    error_clusters = cluster_error_cases(error_cases)
    return error_stats, error_clusters
```

### 3. 风险预警机制
```python
def risk_warning_system(predictions, thresholds):
    warnings = {
        'high_risk': predictions[predictions > thresholds['high']],
        'medium_risk': predictions[(predictions > thresholds['medium']) & 
                                 (predictions <= thresholds['high'])],
        'low_risk': predictions[predictions <= thresholds['medium']]
    }
    
    # 生成风险报告
    generate_risk_report(warnings)
    
    # 触发预警通知
    if len(warnings['high_risk']) > 0:
        send_risk_alert(warnings['high_risk'])
``` 