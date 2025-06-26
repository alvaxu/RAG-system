# 688692.SH 股票价格预测

本项目使用多种时间序列预测模型对688692.SH股票价格进行预测，包括：

1. ARIMA模型 - 自回归积分滑动平均模型
2. SARIMA模型 - 季节性自回归积分滑动平均模型
3. Prophet模型 - Facebook开发的时间序列预测库

## 文件说明

- `download_688692SH.py` - 使用Tushare下载股票历史数据
- `predict_688692SH.py` - 使用ARIMA模型预测未来7天股价
- `predict_688692SH_seasonal.py` - 使用SARIMA模型预测未来7天股价
- `predict_688692SH_prophet.py` - 使用Prophet模型预测未来7天股价
- `run_all_predictions.py` - 运行所有模型并比较结果

## 安装依赖

运行以下命令安装所需依赖：

```bash
# 基本依赖库
pip install numpy pandas matplotlib statsmodels scikit-learn

# 如果需要使用Prophet模型
pip install prophet
```

## 使用方法

1. 首先下载股票数据（如果尚未下载）：

```bash
python download_688692SH.py
```

2. 运行单个预测模型：

```bash
# ARIMA模型
python predict_688692SH.py

# SARIMA模型
python predict_688692SH_seasonal.py

# Prophet模型
python predict_688692SH_prophet.py
```

3. 运行所有模型并比较结果：

```bash
python run_all_predictions.py
```

## 预测结果

- 各模型的预测结果会保存为CSV文件
- 预测结果图表会保存为PNG文件
- 模型比较结果会保存在`688692_SH_model_comparison.txt`文件中

## 模型选择

- ARIMA模型：适合非季节性时间序列数据
- SARIMA模型：适合具有季节性特征的时间序列数据
- Prophet模型：适合处理有季节性、节假日效应的数据，且对异常值具有较强的鲁棒性

## 注意事项

1. 股票预测本质上具有一定的不确定性，模型预测结果仅供参考
2. 实际交易决策应结合多种因素综合考虑
3. 各模型参数可以根据实际需求进行调整
4. 对于不同股票，最佳模型可能有所不同

## 扩展功能

如需扩展，可考虑实现以下功能：

1. 增加更多预测模型（LSTM、XGBoost等）
2. 添加交易策略回测功能
3. 增加更多技术指标作为特征
4. 实现自动参数优化 