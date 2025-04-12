from flask import Flask, render_template, jsonify, request
import pandas as pd
import json
from datetime import datetime, timedelta
from functools import lru_cache
import numpy as np

app = Flask(__name__)

# 使用缓存装饰器优化数据加载
@lru_cache(maxsize=1)
def load_data():
    try:
        # 读取疫情数据
        df = pd.read_excel('香港各区疫情数据_20250322.xlsx')
        # 转换日期列
        df['报告日期'] = pd.to_datetime(df['报告日期'])
        # 读取地图数据
        with open('hongkong.json', 'r', encoding='utf-8') as f:
            map_data = json.load(f)
        return df, map_data
    except Exception as e:
        print(f"数据加载错误: {str(e)}")
        return None, None

# 首页路由
@app.route('/')
def index():
    return render_template('index.html')

# API路由：获取总体统计数据
@app.route('/api/summary')
def get_summary():
    try:
        df, _ = load_data()
        if df is None:
            return jsonify({"error": "数据加载失败"}), 500
            
        # 获取最新日期的数据
        latest_date = df['报告日期'].max()
        latest_data = df[df['报告日期'] == latest_date].copy()
        
        summary = {
            'total_confirmed': int(latest_data['累计确诊'].sum()),
            'total_recovered': int(latest_data['累计康复'].sum()),
            'total_deaths': int(latest_data['累计死亡'].sum()),
            'new_confirmed': int(latest_data['新增确诊'].sum()),
            'new_recovered': int(latest_data['新增康复'].sum()),
            'new_deaths': int(latest_data['新增死亡'].sum()),
            'update_time': latest_date.strftime('%Y-%m-%d %H:%M:%S')
        }
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API路由：获取地图数据
@app.route('/api/map')
def get_map_data():
    try:
        df, map_data = load_data()
        if df is None or map_data is None:
            return jsonify({"error": "数据加载失败"}), 500
            
        latest_date = df['报告日期'].max()
        latest_data = df[df['报告日期'] == latest_date].copy()
        
        # 计算风险等级
        def calculate_risk(row):
            if row['新增确诊'] >= 50:
                return 'high'
            elif row['新增确诊'] >= 10:
                return 'medium'
            return 'low'
        
        latest_data.loc[:, 'risk_level'] = latest_data.apply(calculate_risk, axis=1)
        
        # 组装地图数据
        for feature in map_data['features']:
            district_name = feature['properties']['name']
            district_data = latest_data[latest_data['地区名称'] == district_name]
            if not district_data.empty:
                district_data = district_data.iloc[0]
                feature['properties'].update({
                    'confirmed': int(district_data['累计确诊']),
                    'new_confirmed': int(district_data['新增确诊']),
                    'risk_level': district_data['risk_level']
                })
        
        return jsonify(map_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API路由：获取趋势数据
@app.route('/api/trend')
def get_trend_data():
    try:
        df, _ = load_data()
        if df is None:
            return jsonify({"error": "数据加载失败"}), 500
            
        # 获取地区参数
        district = request.args.get('district', 'all')
        
        # 如果选择了特定地区，则筛选数据
        if district != 'all':
            df = df[df['地区名称'] == district]
        
        # 按日期聚合数据
        daily_data = df.groupby('报告日期').agg({
            '新增确诊': 'sum',
            '新增康复': 'sum',
            '新增死亡': 'sum',
            '累计确诊': 'sum',
            '累计康复': 'sum',
            '累计死亡': 'sum'
        }).reset_index()
        
        # 计算7日移动平均
        daily_data['新增确诊_7日均值'] = daily_data['新增确诊'].rolling(window=7, min_periods=1).mean().round(2)
        daily_data['新增康复_7日均值'] = daily_data['新增康复'].rolling(window=7, min_periods=1).mean().round(2)
        daily_data['新增死亡_7日均值'] = daily_data['新增死亡'].rolling(window=7, min_periods=1).mean().round(2)
        
        # 计算各项指标
        daily_data['确诊率'] = (daily_data['新增确诊'] / daily_data['新增确诊'].rolling(window=7, min_periods=1).sum() * 100).round(2)
        daily_data['康复率'] = (daily_data['累计康复'] / daily_data['累计确诊'] * 100).round(2)
        daily_data['死亡率'] = (daily_data['累计死亡'] / daily_data['累计确诊'] * 100).round(2)
        
        # 填充空值
        daily_data = daily_data.fillna(0)
        
        return jsonify({
            'dates': daily_data['报告日期'].dt.strftime('%Y-%m-%d').tolist(),
            'new_confirmed': daily_data['新增确诊'].astype(int).tolist(),
            'new_confirmed_ma7': daily_data['新增确诊_7日均值'].tolist(),
            'total_confirmed': daily_data['累计确诊'].astype(int).tolist(),
            'confirmation_rate': daily_data['确诊率'].tolist(),
            'new_recovered': daily_data['新增康复'].astype(int).tolist(),
            'new_recovered_ma7': daily_data['新增康复_7日均值'].tolist(),
            'total_recovered': daily_data['累计康复'].astype(int).tolist(),
            'recovery_rate': daily_data['康复率'].tolist(),
            'new_deaths': daily_data['新增死亡'].astype(int).tolist(),
            'new_deaths_ma7': daily_data['新增死亡_7日均值'].tolist(),
            'total_deaths': daily_data['累计死亡'].astype(int).tolist(),
            'death_rate': daily_data['死亡率'].tolist()
        })
    except Exception as e:
        print(f"趋势数据处理错误: {str(e)}")
        return jsonify({"error": str(e)}), 500

# API路由：获取康复率分析
@app.route('/api/recovery_analysis')
def get_recovery_analysis():
    try:
        df, _ = load_data()
        if df is None:
            return jsonify({"error": "数据加载失败"}), 500
            
        latest_date = df['报告日期'].max()
        latest_data = df[df['报告日期'] == latest_date].copy()
        
        # 计算各区康复率
        latest_data['康复率'] = (latest_data['累计康复'] / latest_data['累计确诊'] * 100).round(2)
        
        # 按康复率排序
        latest_data = latest_data.sort_values('康复率', ascending=False)
        
        return jsonify({
            'districts': latest_data['地区名称'].tolist(),
            'recovery_rates': latest_data['康复率'].tolist(),
            'total_recovered': latest_data['累计康复'].tolist(),
            'total_confirmed': latest_data['累计确诊'].tolist()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API路由：获取死亡率分析
@app.route('/api/death_analysis')
def get_death_analysis():
    try:
        df, _ = load_data()
        if df is None:
            return jsonify({"error": "数据加载失败"}), 500
            
        latest_date = df['报告日期'].max()
        latest_data = df[df['报告日期'] == latest_date].copy()
        
        # 计算各区死亡率
        latest_data['死亡率'] = (latest_data['累计死亡'] / latest_data['累计确诊'] * 100).round(2)
        
        # 按死亡率排序
        latest_data = latest_data.sort_values('死亡率', ascending=False)
        
        return jsonify({
            'districts': latest_data['地区名称'].tolist(),
            'death_rates': latest_data['死亡率'].tolist(),
            'total_deaths': latest_data['累计死亡'].tolist(),
            'total_confirmed': latest_data['累计确诊'].tolist()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API路由：获取地区对比数据
@app.route('/api/district_comparison')
def get_district_comparison():
    try:
        df, _ = load_data()
        if df is None:
            return jsonify({"error": "数据加载失败"}), 500
            
        latest_date = df['报告日期'].max()
        latest_data = df[df['报告日期'] == latest_date].copy()
        
        return jsonify({
            'districts': latest_data['地区名称'].tolist(),
            'confirmed': latest_data['累计确诊'].tolist(),
            'new_confirmed': latest_data['新增确诊'].tolist()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API路由：获取地区详情
@app.route('/api/district_detail')
def get_district_detail():
    df, _ = load_data()
    district = request.args.get('district')
    days = int(request.args.get('days', 7))
    
    latest_date = df['报告日期'].max()
    start_date = latest_date - timedelta(days=days)
    district_data = df[(df['地区名称'] == district) & (df['报告日期'] >= start_date)]
    
    return jsonify({
        'dates': district_data['报告日期'].dt.strftime('%Y-%m-%d').tolist(),
        'new_confirmed': district_data['新增确诊'].tolist(),
        'new_recovered': district_data['新增康复'].tolist(),
        'new_deaths': district_data['新增死亡'].tolist()
    })

if __name__ == '__main__':
    app.run(debug=True) 