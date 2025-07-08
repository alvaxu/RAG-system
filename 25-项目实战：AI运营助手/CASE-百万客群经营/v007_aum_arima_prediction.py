"""
程序说明：

## 1. 使用ARIMA模型预测客户资产变动趋势
   - 按季度/月度汇总客户总资产(AUM)
   - 使用网格搜索自动选择最优ARIMA参数
   - 分析资产时间序列的平稳性和季节性
   - 使用ARIMA模型预测未来趋势
   - 可视化预测结果并输出置信区间

## 2. 特点
   - 支持季度/月度等多种时间粒度分析
   - 自动选择最优ARIMA参数
   - 包含数据平稳性检验和季节性分析
   - 提供模型评估指标和置信区间
   - 支持调试模式和完整数据分析模式
"""

import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import adfuller, acf, pacf
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.seasonal import seasonal_decompose
from sklearn.metrics import mean_squared_error, mean_absolute_error
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import itertools
import warnings
from matplotlib.dates import YearLocator, DateFormatter
warnings.filterwarnings('ignore')

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

class AUMPrediction:
    """
    客户资产预测分析类
    """
    def __init__(self, behavior_file='customer_behavior_assets.csv', debug_mode=False):
        """
        初始化函数
        :param behavior_file: 客户行为数据文件路径
        :param debug_mode: 是否为调试模式，True则只分析部分数据
        """
        self.debug_mode = debug_mode
        self.data = self._load_data(behavior_file)
        self.best_model = None
        self.best_order = None
        
    def _load_data(self, file_path):
        """
        加载数据并进行预处理
        :param file_path: 数据文件路径
        :return: DataFrame对象
        """
        df = pd.read_csv(file_path)
        if self.debug_mode:
            print("调试模式：只分析前1000条数据")
            df = df.head(1000)
            
        # 将stat_month转换为日期格式
        df['stat_month'] = pd.to_datetime(df['stat_month'])
        return df
    
    def prepare_time_series(self, freq='Q'):
        """
        准备时间序列数据
        :param freq: 时间频率，Q为季度，M为月度
        :return: 时间序列数据
        """
        # 按时间汇总总资产
        ts_data = self.data.groupby('stat_month')['total_assets'].sum().reset_index()
        
        # 确保时间格式正确
        ts_data['stat_month'] = pd.to_datetime(ts_data['stat_month'])
        ts_data = ts_data.sort_values('stat_month')
        ts_data.set_index('stat_month', inplace=True)
        
        # 重采样到指定频率
        if freq == 'Q':
            ts_data = ts_data.resample(freq).mean()
            ts_data.index = ts_data.index + pd.offsets.QuarterEnd(0)
        else:
            ts_data = ts_data.resample(freq).mean()
        
        return ts_data
    
    def analyze_seasonality(self, ts_data):
        """
        分析时间序列的季节性
        :param ts_data: 时间序列数据
        :return: 季节性分解结果
        """
        print("\n进行季节性分析:")
        
        # 检查数据量是否足够进行季节性分解
        if len(ts_data) < 24:
            print("警告：数据量不足以进行季节性分解分析（需要至少24个观测值）")
            print(f"当前数据量：{len(ts_data)}个观测值")
            return None
            
        decomposition = seasonal_decompose(ts_data, period=12)
        
        plt.figure(figsize=(12, 10))
        plt.subplot(411)
        plt.plot(ts_data.index, ts_data.values)
        plt.title('原始时间序列')
        plt.subplot(412)
        plt.plot(decomposition.trend)
        plt.title('趋势')
        plt.subplot(413)
        plt.plot(decomposition.seasonal)
        plt.title('季节性')
        plt.subplot(414)
        plt.plot(decomposition.resid)
        plt.title('残差')
        plt.tight_layout()
        plt.savefig('v007_seasonality_analysis.png')
        plt.close()
        
        return decomposition
    
    def check_stationarity(self, ts_data):
        """
        检查时间序列的平稳性
        :param ts_data: 时间序列数据
        :return: ADF检验结果
        """
        print("\n进行ADF平稳性检验:")
        adf_result = adfuller(ts_data)
        
        adf_output = {
            'ADF统计量': adf_result[0],
            'p值': adf_result[1],
            '滞后阶数': adf_result[2],
            '观测数量': adf_result[3]
        }
        
        for key, value in adf_output.items():
            print(f'{key}: {value}')
            
        # 根据数据量自动调整滞后阶数
        max_lags = min(40, int(len(ts_data) * 0.4))  # 使用数据长度的40%作为最大滞后阶数
        
        # 绘制ACF和PACF图
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        acf_values = acf(ts_data, nlags=max_lags)
        pacf_values = pacf(ts_data, nlags=max_lags)
        
        ax1.stem(range(len(acf_values)), acf_values)
        ax1.set_title('自相关函数(ACF)')
        ax1.axhline(y=0, linestyle='--', color='gray')
        
        ax2.stem(range(len(pacf_values)), pacf_values)
        ax2.set_title('偏自相关函数(PACF)')
        ax2.axhline(y=0, linestyle='--', color='gray')
        
        plt.tight_layout()
        plt.savefig('v007_acf_pacf_analysis.png')
        plt.close()
        
        return adf_result[1] < 0.05
    
    def grid_search_arima(self, ts_data):
        """
        网格搜索最优ARIMA参数
        :param ts_data: 时间序列数据
        :return: 最优参数
        """
        print("\n开始网格搜索最优ARIMA参数...")
        
        # 定义参数范围
        p = range(0, 3)
        d = range(0, 2)
        q = range(0, 3)
        
        best_aic = float('inf')
        best_order = None
        
        # 网格搜索
        for param in itertools.product(p, d, q):
            try:
                model = ARIMA(ts_data, order=param)
                results = model.fit()
                
                if results.aic < best_aic:
                    best_aic = results.aic
                    best_order = param
                    
                if self.debug_mode:
                    print(f"ARIMA{param} AIC: {results.aic}")
                    
            except:
                continue
                
        print(f"最优ARIMA参数: {best_order}")
        return best_order
    
    def train_arima_model(self, ts_data, order=None):
        """
        训练ARIMA模型
        :param ts_data: 时间序列数据
        :param order: ARIMA模型的阶数(p,d,q)
        :return: 训练好的模型
        """
        if order is None:
            order = self.grid_search_arima(ts_data)
        
        print(f"\n训练ARIMA{order}模型")
        
        # 计算平均增长量
        diff = ts_data.diff().dropna()
        avg_growth = float(diff.mean())
        print(f"平均增长量: {avg_growth:,.2f}")
        
        # 分割训练集和测试集
        train_size = int(len(ts_data) * 0.8)
        train = ts_data[:train_size]
        test = ts_data[train_size:]
        
        # 训练模型
        model = ARIMA(train, order=order)
        model_fit = model.fit()
        
        # 对测试集进行预测
        forecast = model_fit.forecast(steps=len(test))
        
        # 计算评估指标
        rmse = np.sqrt(mean_squared_error(test, forecast))
        mae = mean_absolute_error(test, forecast)
        mape = np.mean(np.abs((test - forecast) / test)) * 100
        
        print(f"\n模型评估指标:")
        print(f"RMSE: {rmse:,.2f}")
        print(f"MAE: {mae:,.2f}")
        print(f"MAPE: {mape:.2f}%")
        
        # 保存最优模型
        self.best_model = model_fit
        self.best_order = order
        
        return model_fit, forecast, test
    
    def predict_future(self, model, periods=12, confidence_interval=0.95):
        """
        预测未来趋势
        :param model: 训练好的ARIMA模型
        :param periods: 预测期数
        :param confidence_interval: 置信区间
        :return: 预测结果和置信区间
        """
        # 使用ARIMA模型进行预测
        forecast = model.forecast(steps=periods)
        
        # 计算置信区间
        forecast_mean = forecast
        forecast_std = np.std(model.resid)
        z_value = 1.96  # 95% 置信区间
        
        conf_int = pd.DataFrame({
            'lower': forecast_mean - z_value * forecast_std,
            'upper': forecast_mean + z_value * forecast_std
        })
        
        return forecast_mean, conf_int
    
    def visualize_results(self, ts_data, test_data, forecast, future_forecast, conf_int, freq='Q'):
        """
        可视化分析结果
        :param ts_data: 原始时间序列数据
        :param test_data: 测试集数据
        :param forecast: 测试集预测结果
        :param future_forecast: 未来预测结果
        :param conf_int: 置信区间
        :param freq: 时间频率
        """
        plt.figure(figsize=(12, 6))
        
        # 绘制历史数据
        plt.plot(ts_data.index, ts_data.values/1e6, 
                label='历史AUM', color='#1f77b4', 
                marker='o', markersize=4)
        
        # 绘制测试集预测结果
        plt.plot(test_data.index, forecast/1e6,
                label='测试集预测', color='#2ca02c',
                linestyle='--')
        
        # 绘制未来预测
        future_index = pd.date_range(start=ts_data.index[-1],
                                   periods=len(future_forecast)+1,
                                   freq=freq)[1:]
        
        plt.plot(future_index, future_forecast/1e6,
                label='未来预测', color='#ff7f0e',
                marker='o', markersize=4)
        
        # 绘制置信区间
        plt.fill_between(future_index,
                        conf_int.iloc[:, 0]/1e6,
                        conf_int.iloc[:, 1]/1e6,
                        color='#ff7f0e', alpha=0.2,
                        label='95%置信区间')
        
        # 设置标题和标签
        plt.title(f'客户AUM趋势预测 (ARIMA{self.best_order})', fontsize=12)
        plt.xlabel('时间')
        plt.ylabel('总资产 (百万)')
        
        # 设置图例
        plt.legend(loc='upper left')
        
        # 设置网格
        plt.grid(True, linestyle='--', alpha=0.3)
        
        # 调整x轴标签角度
        plt.xticks(rotation=45)
        
        # 自动调整布局
        plt.tight_layout()
        
        # 保存图片
        plt.savefig('v007_aum_arima_prediction.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 保存预测结果
        results_df = pd.DataFrame({
            '时间': future_index,
            '预测资产值(百万)': future_forecast/1e6,
            '置信区间下限(百万)': conf_int.iloc[:, 0]/1e6,
            '置信区间上限(百万)': conf_int.iloc[:, 1]/1e6
        })
        results_df.to_csv('v007_aum_arima_forecast.csv', index=False, encoding='utf-8')

def main():
    """
    主函数
    """
    # 交互式输入参数
    print("\n=== 客户资产ARIMA预测分析参数设置 ===")
    
    # 调试模式选择
    debug_input = input("是否启用调试模式？(y/n，默认n): ").strip().lower()
    debug_mode = debug_input == 'y'
    
    # 时间频率选择
    freq_input = input("选择时间频率 (Q-季度/M-月度，默认M): ").strip().upper()
    freq = freq_input if freq_input in ['Q', 'M'] else 'M'
    
    # 预测期数设置
    while True:
        try:
            periods = input("请输入预测期数 (默认12): ").strip()
            periods = int(periods) if periods else 12
            if periods > 0:
                break
            print("预测期数必须大于0！")
        except ValueError:
            print("请输入有效的数字！")
    
    print("\n=== 参数设置完成 ===")
    print(f"调试模式: {'是' if debug_mode else '否'}")
    print(f"时间频率: {'季度' if freq=='Q' else '月度'}")
    print(f"预测期数: {periods}")
    
    # 创建分析器实例
    predictor = AUMPrediction(debug_mode=debug_mode)
    
    # 准备时间序列数据
    print("\n准备时间序列数据...")
    ts_data = predictor.prepare_time_series(freq=freq)
    
    # 分析季节性
    print("\n分析季节性特征...")
    seasonal_decomp = predictor.analyze_seasonality(ts_data)
    if seasonal_decomp is not None:
        print("季节性分析完成，结果已保存到: v007_seasonality_analysis.png")
    
    # 检查平稳性
    is_stationary = predictor.check_stationarity(ts_data)
    print(f"时间序列是否平稳: {is_stationary}")
    
    # 训练模型
    model, forecast, test_data = predictor.train_arima_model(ts_data)
    
    # 预测未来趋势
    print(f"\n预测未来{periods}期趋势...")
    future_forecast, conf_int = predictor.predict_future(model, periods=periods)
    
    # 可视化结果
    print("\n生成可视化结果...")
    predictor.visualize_results(ts_data, test_data, forecast, future_forecast, conf_int, freq=freq)
    
    print("\n分析完成！")
    print(f"- 预测结果已保存到: v007_aum_arima_forecast.csv")
    print(f"- 趋势图已保存到: v007_aum_arima_prediction.png")
    if seasonal_decomp is not None:
        print(f"- 季节性分析图已保存到: v007_seasonality_analysis.png")
    print(f"- ACF/PACF分析图已保存到: v007_acf_pacf_analysis.png")

if __name__ == "__main__":
    main() 