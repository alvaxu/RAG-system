"""
程序说明：

## 1. 使用简单增长预测模型预测客户资产变动趋势
   - 按月度/季度汇总客户总资产(AUM)
   - 分析资产时间序列的平稳性
   - 基于历史平均增长量预测未来趋势
   - 可视化预测结果

## 2. 特点
   - 支持月度/季度等多种时间粒度分析
   - 包含数据平稳性检验（ADF检验）
   - 使用简单增长模型进行预测
   - 提供基础模型评估指标（RMSE、MAE）
   - 支持调试模式和完整数据分析模式

## 3. 预测方法
   - 计算历史数据的平均增长量
   - 基于最后一个观测值和平均增长量进行线性外推
   - 适用于短期趋势预测

## 4. 注意事项
   - 这是一个简单的线性增长预测模型
   - 不考虑季节性和周期性因素
   - 适合相对稳定增长的场景
   - 对于波动较大的数据，建议使用v007_aum_arima_prediction.py
"""

import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_squared_error, mean_absolute_error
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
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
        ts_data = ts_data.sort_values('stat_month')  # 确保时间序列有序
        ts_data.set_index('stat_month', inplace=True)
        
        # 重采样到指定频率
        if freq == 'Q':
            # 将月度数据转换为季度数据，并确保季度末对齐
            ts_data = ts_data.resample(freq).mean()
            # 设置季度末日期
            ts_data.index = ts_data.index + pd.offsets.QuarterEnd(0)
        else:
            ts_data = ts_data.resample(freq).mean()
        
        return ts_data
    
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
            
        return adf_result[1] < 0.05
    
    def train_arima_model(self, ts_data, order=(1,1,0)):
        """
        训练ARIMA模型
        :param ts_data: 时间序列数据
        :param order: ARIMA模型的阶数(p,d,q)
        :return: 训练好的模型
        """
        print(f"\n训练ARIMA({order[0]},{order[1]},{order[2]})模型")
        
        # 计算平均增长量
        diff = ts_data.diff().dropna()
        avg_growth = float(diff.mean())
        print(f"平均月度增长量: {avg_growth:,.2f}")
        
        # 使用全部数据进行训练
        model = ARIMA(ts_data, order=order)
        model_fit = model.fit()
        
        # 对最后一个点进行预测，用于评估模型
        last_point = ts_data.iloc[-1:]
        forecast = model_fit.forecast(steps=1)
        
        # 计算评估指标
        rmse = np.sqrt(mean_squared_error(last_point, forecast))
        mae = mean_absolute_error(last_point, forecast)
        
        print(f"模型评估指标:")
        print(f"RMSE: {rmse:.2f}")
        print(f"MAE: {mae:.2f}")
        
        return model_fit, forecast, last_point
    
    def predict_future(self, model, periods=12):
        """
        预测未来趋势
        :param model: 训练好的ARIMA模型
        :param periods: 预测期数
        :return: 预测结果
        """
        # 获取最后一个观测值
        last_value = model.model.endog[-1][0]  # 获取标量值
        
        # 获取历史数据的平均增长量
        historical_data = pd.Series(model.model.endog.ravel())  # 展平数组
        avg_growth = historical_data.diff().dropna().mean()
        
        # 使用平均增长量进行预测
        future_values = np.array([last_value + avg_growth * (i+1) for i in range(periods)])
        
        return future_values
    
    def visualize_results(self, ts_data, last_point, forecast, future_forecast, freq='Q'):
        """
        可视化分析结果
        :param ts_data: 原始时间序列数据
        :param last_point: 最后一个实际数据点
        :param forecast: 预测结果
        :param future_forecast: 未来预测结果
        :param freq: 时间频率
        """
        plt.figure(figsize=(12, 6))
        
        # 绘制历史数据
        plt.plot(ts_data.index, ts_data.values/1e6, 
                label='历史AUM', color='#1f77b4', 
                marker='o', markersize=4)
        
        # 绘制未来预测
        if freq == 'Q':
            future_index = pd.date_range(start=ts_data.index[-1],
                                       periods=len(future_forecast)+1,
                                       freq=freq)[1:]
        else:
            future_index = pd.date_range(start=ts_data.index[-1],
                                       periods=len(future_forecast)+1,
                                       freq=freq)[1:]
        
        plt.plot(future_index, future_forecast/1e6,
                label='预测AUM', color='#ff7f0e',
                marker='o', markersize=4)
        
        # 设置标题和标签
        plt.title('客户未来季度AUM增长趋势预测（ARIMA）', fontsize=12)
        plt.xlabel('季度')
        plt.ylabel('总资产 (百万)')
        
        # 设置图例
        plt.legend(['历史AUM', '预测AUM'], loc='upper left')
        
        # 设置网格
        plt.grid(True, linestyle='--', alpha=0.3)
        
        # 设置x轴范围
        all_dates = pd.date_range(start=ts_data.index.min(), 
                                end=future_index[-1], 
                                freq=freq)
        plt.xlim(all_dates[0], all_dates[-1])
        
        # 调整x轴标签角度
        plt.xticks(rotation=45)
        
        # 自动调整布局以防止标签被切割
        plt.tight_layout()
        
        # 保存图片
        plt.savefig('v007_aum_prediction.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 保存预测结果
        results_df = pd.DataFrame({
            '时间': future_index,
            '预测资产值(百万)': future_forecast/1e6
        })
        results_df.to_csv('v007_aum_forecast.csv', index=False, encoding='utf-8')

def main():
    """
    主函数
    """
    # 交互式输入参数
    print("\n=== 客户资产预测分析参数设置 ===")
    
    # 调试模式选择
    debug_input = input("是否启用调试模式？(y/n，默认n): ").strip().lower()
    debug_mode = debug_input == 'y'
    
    # 时间频率选择
    freq = 'M'  # 固定使用月度数据
    print("使用月度数据进行分析")
    
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
    print(f"时间频率: 月度")
    print(f"预测期数: {periods}")
    
    # 创建分析器实例
    predictor = AUMPrediction(debug_mode=debug_mode)
    
    # 准备时间序列数据
    print("\n准备时间序列数据...")
    ts_data = predictor.prepare_time_series(freq=freq)
    
    # 检查平稳性
    is_stationary = predictor.check_stationarity(ts_data)
    print(f"时间序列是否平稳: {is_stationary}")
    
    # 训练模型
    model, forecast, last_point = predictor.train_arima_model(ts_data)
    
    # 预测未来趋势
    print(f"\n预测未来{periods}期趋势...")
    future_forecast = predictor.predict_future(model, periods=periods)
    
    # 可视化结果
    print("\n生成可视化结果...")
    predictor.visualize_results(ts_data, last_point, forecast, future_forecast, freq=freq)
    
    print("\n分析完成！")
    print(f"- 预测结果已保存到: v007_aum_forecast.csv")
    print(f"- 趋势图已保存到: v007_aum_prediction.png")

if __name__ == "__main__":
    main() 