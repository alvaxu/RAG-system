# -*- coding: utf-8 -*-
# 运行所有预测模型并比较结果
import subprocess
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 设置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False    # 用来正常显示负号

def run_script(script_name):
    """运行一个Python脚本"""
    print(f"\n正在运行 {script_name}...")
    try:
        result = subprocess.run(['python', script_name], 
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               text=True,
                               encoding='utf-8')
        if result.returncode == 0:
            print(f"{script_name} 运行成功!")
            return True
        else:
            print(f"{script_name} 运行失败!")
            print("错误信息:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"运行 {script_name} 时出错: {e}")
        return False

# 检查依赖库是否已安装
def check_dependencies():
    try:
        import numpy
        import pandas
        import matplotlib
        import statsmodels
        import sklearn
        print("基本依赖库已安装")
        
        try:
            import prophet
            prophet_installed = True
            print("Prophet库已安装")
        except ImportError:
            prophet_installed = False
            print("Prophet库未安装，将跳过Prophet模型")
            print("可以使用以下命令安装Prophet:")
            print("pip install prophet")
        
        return prophet_installed
    except ImportError as e:
        print(f"缺少必要的依赖库: {e}")
        print("请使用以下命令安装基本依赖库:")
        print("pip install numpy pandas matplotlib statsmodels scikit-learn")
        return False

# 主执行函数
def main():
    print("开始运行所有预测模型...")
    
    # 检查依赖库
    prophet_installed = check_dependencies()
    
    # 运行ARIMA模型
    run_script('predict_688692SH.py')
    
    # 运行SARIMA模型
    run_script('predict_688692SH_seasonal.py')
    
    # 运行Prophet模型 (如果已安装)
    if prophet_installed:
        run_script('predict_688692SH_prophet.py')
    
    # 比较各个模型的预测结果
    print("\n比较各个模型的预测结果...")
    
    # 读取各个模型的预测结果
    try:
        # ARIMA模型结果
        df_arima = pd.read_csv('688692_SH_prediction_results.csv')
        df_arima.index = pd.to_datetime(df_arima.index)
        
        # SARIMA模型结果
        df_sarima = pd.read_csv('688692_SH_prediction_seasonal_results.csv')
        df_sarima.index = pd.to_datetime(df_sarima.index)
        
        models = ['ARIMA', 'SARIMA']
        rmse_values = []
        
        # 读取每个模型的RMSE值
        with open('688692_SH_model_comparison.txt', 'w', encoding='utf-8') as f:
            f.write("模型比较结果:\n\n")
            f.write("1. ARIMA模型:\n")
            f.write(f"   - 参数: {df_arima.get('arima_params', ['未知'])[0]}\n")
            arima_rmse = df_arima.get('rmse', None)
            if arima_rmse is not None:
                arima_rmse = float(arima_rmse[0])
                f.write(f"   - RMSE: {arima_rmse:.2f}\n")
                rmse_values.append(arima_rmse)
            else:
                rmse_values.append(np.nan)
                
            f.write("\n2. SARIMA模型:\n")
            f.write(f"   - 参数: {df_sarima.get('sarima_params', ['未知'])[0]}\n")
            sarima_rmse = df_sarima.get('rmse', None)
            if sarima_rmse is not None:
                sarima_rmse = float(sarima_rmse[0])
                f.write(f"   - RMSE: {sarima_rmse:.2f}\n")
                rmse_values.append(sarima_rmse)
            else:
                rmse_values.append(np.nan)
                
            # Prophet模型结果 (如果已安装)
            if prophet_installed and os.path.exists('688692_SH_prediction_prophet_results.csv'):
                df_prophet = pd.read_csv('688692_SH_prediction_prophet_results.csv')
                f.write("\n3. Prophet模型:\n")
                
                # 从之前的运行输出中提取RMSE (这部分需要根据实际情况调整)
                prophet_rmse = None
                try:
                    with open('prophet_results.txt', 'r') as pr:
                        for line in pr:
                            if "RMSE" in line:
                                prophet_rmse = float(line.split(":")[1].strip())
                                break
                except:
                    pass
                
                if prophet_rmse:
                    f.write(f"   - RMSE: {prophet_rmse:.2f}\n")
                    rmse_values.append(prophet_rmse)
                    models.append('Prophet')
                else:
                    f.write(f"   - RMSE: 未知\n")
                
            # 选择最佳模型
            best_model_idx = np.nanargmin(rmse_values)
            f.write(f"\n最佳模型: {models[best_model_idx]} (RMSE: {rmse_values[best_model_idx]:.2f})\n")
            
            # 输出每个模型的预测结果
            f.write("\n各模型未来7天预测结果:\n")
            
            # ARIMA预测结果
            f.write("\nARIMA模型预测:\n")
            f.write(df_arima[['close']].to_string())
            
            # SARIMA预测结果
            f.write("\n\nSARIMA模型预测:\n")
            f.write(df_sarima[['close']].to_string())
            
            # Prophet预测结果
            if prophet_installed and os.path.exists('688692_SH_prediction_prophet_results.csv'):
                f.write("\n\nProphet模型预测:\n")
                f.write(df_prophet.to_string())
        
        print("比较结果已保存到 688692_SH_model_comparison.txt")
        
        # 绘制不同模型的预测结果对比图
        plt.figure(figsize=(14, 7))
        
        # 读取原始数据绘制历史走势
        df_original = pd.read_csv('./688692_SH_daily_data.csv')
        df_original['trade_date'] = pd.to_datetime(df_original['trade_date'])
        df_original.set_index('trade_date', inplace=True)
        
        # 绘制历史数据 (仅显示最近30天)
        plt.plot(df_original.index[-30:], df_original['close'][-30:], 'k-', linewidth=2, label='历史收盘价')
        
        # 绘制各模型的预测结果
        plt.plot(df_arima.index, df_arima['close'], 'b--', label='ARIMA预测')
        plt.plot(df_sarima.index, df_sarima['close'], 'g--', label='SARIMA预测')
        
        if prophet_installed and os.path.exists('688692_SH_prediction_prophet_results.csv'):
            prophet_dates = pd.to_datetime(df_prophet['日期'])
            plt.plot(prophet_dates, df_prophet['预测价格'], 'r--', label='Prophet预测')
        
        # 设置图形属性
        plt.title('688692.SH股票价格预测模型比较', fontsize=15)
        plt.xlabel('日期', fontsize=12)
        plt.ylabel('收盘价(元)', fontsize=12)
        plt.legend(fontsize=10)
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # 保存比较结果图
        plt.savefig('688692_SH_model_comparison.png')
        plt.show()
        
        print("预测模型比较完成!")
        
    except Exception as e:
        print(f"比较模型时出错: {e}")

if __name__ == "__main__":
    main() 