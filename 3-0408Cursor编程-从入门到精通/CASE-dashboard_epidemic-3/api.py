# from flask import Flask, jsonify
# import pandas as pd
# from datetime import datetime, timedelta
# import json

# app = Flask(__name__)

# # 读取Excel数据
# def read_data():
#     try:
#         df = pd.read_excel('香港各区疫情数据_20250322.xlsx', parse_dates=['报告日期'])
#         df['报告日期'] = pd.to_datetime(df['报告日期'])
#         return df
#     except Exception as e:
#         return None

# @app.route('/api/dashboard')
# def get_dashboard_data():
#     df = read_data()
#     if df is None:
#         return jsonify({'error': '数据读取失败'}), 500
    
#     try:
#         latest_data = df
        
#         # 计算关键指标
#         today_new = int(latest_data['新增确诊'].sum())
#         total_cases = int(df['新增确诊'].sum())
#         deaths = int(df['新增死亡'].sum())
        
#         # 计算比率
#         death_rate = float(round((deaths / total_cases) * 100, 2)) if total_cases > 0 else 0.0
        
#         # 准备地图数据
#         map_data = []
#         for _, row in latest_data.iterrows():
#             map_data.append({
#                 'name': str(row['地区名称']),
#                 'value': int(row['新增确诊'])
#             })
        
#         # 准备趋势数据
#         trend_data = df.groupby('报告日期').agg({
#             '新增确诊': 'sum',
#             '累计确诊': 'sum'
#         }).reset_index()
        
#         # 按日期排序
#         trend_data = trend_data.sort_values('报告日期')
        
#         dates = trend_data['报告日期'].dt.strftime('%Y-%m-%d').tolist()
#         new_cases = [int(x) for x in trend_data['新增确诊'].tolist()]
#         total_cases_list = [int(x) for x in trend_data['累计确诊'].tolist()]
        
#         # 计算增长率
#         growth_rates = []
#         for i in range(1, len(new_cases)):
#             prev = new_cases[i-1]
#             current = new_cases[i]
#             growth_rate = float(round(((current - prev) / prev) * 100, 2)) if prev > 0 else 0.0
#             growth_rates.append(growth_rate)
        
#         # 准备区域排名数据
#         area_rank = latest_data.sort_values('新增确诊', ascending=False)
#         areas = [str(x) for x in area_rank['地区名称'].tolist()[:10]]
#         area_cases = [int(x) for x in area_rank['新增确诊'].tolist()[:10]]
        
#         response = {
#             'indicators': {
#                 'todayNew': today_new,
#                 'totalCases': total_cases,
#                 'deathRate': death_rate
#             },
#             'mapData': map_data,
#             'trendData': {
#                 'dates': dates,
#                 'newCases': new_cases,
#                 'totalCases': total_cases_list
#             },
#             'growthData': {
#                 'dates': dates[1:],
#                 'rates': growth_rates
#             },
#             'rankData': {
#                 'areas': areas,
#                 'cases': area_cases
#             }
#         }
        
#         return jsonify(response)
    
#     except Exception as e:
#         return jsonify({'error': f'数据处理失败: {str(e)}'}), 500

# if __name__ == '__main__':
#     app.run(debug=False, port=5000) 

from flask import Flask, jsonify
import pandas as pd
from datetime import datetime, timedelta
import json

app = Flask(__name__)

# 读取Excel数据
def read_data():
    try:
        df = pd.read_excel('香港各区疫情数据_20250322.xlsx', parse_dates=['报告日期'])
        df['报告日期'] = pd.to_datetime(df['报告日期'])
        return df
    except Exception as e:
        return None

@app.route('/api/dashboard')
def get_dashboard_data():
    df = read_data()
    if df is None:
        return jsonify({'error': '数据读取失败'}), 500
    
    try:
        latest_data = df
        
        # 计算关键指标
        today_new = int(latest_data['新增确诊'].sum())
        total_cases = int(df['新增确诊'].sum())
        deaths = int(df['新增死亡'].sum())
        recovered = int(df['治愈人数'].sum())
        
        # 计算比率
        death_rate = float(round((deaths / total_cases) * 100, 2)) if total_cases > 0 else 0.0
        recovery_rate = float(round((recovered / total_cases) * 100, 2)) if total_cases > 0 else 0.0
        
        # 准备地图数据
        map_data = []
        for _, row in latest_data.iterrows():
            map_data.append({
                'name': str(row['地区名称']),
                'value': int(row['新增确诊'])
            })
        
        # 准备趋势数据
        trend_data = df.groupby('报告日期').agg({
            '新增确诊': 'sum',
            '累计确诊': 'sum',
            '治愈人数': 'sum'
        }).reset_index()
        
        # 按日期排序
        trend_data = trend_data.sort_values('报告日期')
        
        dates = trend_data['报告日期'].dt.strftime('%Y-%m-%d').tolist()
        new_cases = [int(x) for x in trend_data['新增确诊'].tolist()]
        total_cases_list = [int(x) for x in trend_data['累计确诊'].tolist()]
        recovered_list = [int(x) for x in trend_data['治愈人数'].tolist()]
        
        # 计算增长率
        growth_rates = []
        for i in range(1, len(new_cases)):
            prev = new_cases[i-1]
            current = new_cases[i]
            growth_rate = float(round(((current - prev) / prev) * 100, 2)) if prev > 0 else 0.0
            growth_rates.append(growth_rate)
        
        # 准备区域排名数据
        area_rank = latest_data.sort_values('新增确诊', ascending=False)
        areas = [str(x) for x in area_rank['地区名称'].tolist()[:10]]
        area_cases = [int(x) for x in area_rank['新增确诊'].tolist()[:10]]
        
        response = {
            'indicators': {
                'todayNew': today_new,
                'totalCases': total_cases,
                'deathRate': death_rate,
                'recoveryRate': recovery_rate
            },
            'mapData': map_data,
            'trendData': {
                'dates': dates,
                'newCases': new_cases,
                'totalCases': total_cases_list,
                'recovered': recovered_list
            },
            'growthData': {
                'dates': dates[1:],
                'rates': growth_rates
            },
            'rankData': {
                'areas': areas,
                'cases': area_cases
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({'error': f'数据处理失败: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=False, port=5000)