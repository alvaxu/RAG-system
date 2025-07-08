from flask import Flask, render_template, jsonify, redirect
import pandas as pd
from datetime import datetime, timedelta
import json
import re
import folium

app = Flask(__name__)

def load_data():
    try:
        df = pd.read_excel('香港各区疫情数据_20250322.xlsx')
        df['报告日期'] = pd.to_datetime(df['报告日期'])
        return df
    except Exception as e:
        print(f"数据加载失败：{e}")
        return None

def load_geojson():
    with open('hongkong.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def create_map():
    df = load_data()
    if df is None:
        return None
    
    latest_date = df['报告日期'].max()
    latest_data = df[df['报告日期'] == latest_date]
    
    geojson_data = load_geojson()
    hk_center = [22.3193, 114.1694]
    m = folium.Map(location=hk_center, zoom_start=11)
    
    covid_dict = dict(zip(latest_data['地区名称'], latest_data['累计死亡']))
    
    for feature in geojson_data['features']:
        district = feature['properties']['name']
        if district in covid_dict:
            cases = covid_dict[district]
            color = '#ff0000' if cases > 100 else '#ff6600' if cases > 50 else '#ffff00' if cases > 20 else '#00ff00'
            
            folium.GeoJson(
                feature,
                style_function=lambda x, color=color: {
                    'fillColor': color,
                    'color': 'black',
                    'weight': 1,
                    'fillOpacity': 0.5
                },
                tooltip=f'{district}: {cases}例累计死亡'
            ).add_to(m)
    
    return m

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/overview')
def get_overview():
    df = load_data()
    #调试1
    # print(df.columns)   
    if df is None:
        return jsonify({"error": "数据加载失败"}), 500
    
    latest_date = df['报告日期'].max()
    latest_data = df[df['报告日期'] == latest_date]
    
    overview = {
        "total_confirmed": int(latest_data['累计确诊'].max()),
        "total_recovered": int(latest_data['累计康复'].max()),
        "total_deaths": int(latest_data['累计死亡'].max()),
        "new_confirmed": int(latest_data['新增确诊'].sum()),
        "new_recovered": int(latest_data['新增康复'].sum()),
        "new_deaths": int(latest_data['新增死亡'].sum()),
        "update_time": latest_date.strftime("%Y-%m-%d %H:%M:%S")
    }
    return jsonify(overview)

@app.route('/api/trend')
def get_trend():
    df = load_data()
    #调试2
    # print(df.columns)   
    if df is None:
        return jsonify({"error": "数据加载失败"}), 500
    
    daily_stats = df.groupby('报告日期').agg({
        '新增确诊': 'sum',
        '累计确诊': 'max',
        '新增康复': 'sum',
        '累计康复': 'max',
        '新增死亡': 'sum',
        '累计死亡': 'max'
    }).reset_index()
    
    trend_data = {
        "dates": daily_stats['报告日期'].dt.strftime('%Y-%m-%d').tolist(),
        "new_confirmed": daily_stats['新增确诊'].tolist(),
        "total_confirmed": daily_stats['累计确诊'].tolist(),
        "new_recovered": daily_stats['新增康复'].tolist(),
        "total_recovered": daily_stats['累计康复'].tolist(),
        "new_deaths": daily_stats['新增死亡'].tolist(),
        "total_deaths": daily_stats['累计死亡'].tolist()
    }
    return jsonify(trend_data)

@app.route('/api/risk')
def get_risk_data():
    df = load_data()
    #调试4
    # print(df.columns)
    
    if df is None:
        return jsonify({"error": "数据加载失败"}), 500
    
    latest_date = df['报告日期'].max()
    latest_data = df[df['报告日期'] == latest_date]
    
    risk_levels = latest_data['风险等级'].value_counts()
    risk_data = [
        {"name": level, "value": int(count)}
        for level, count in risk_levels.items()
    ]
    
    return jsonify(risk_data)

@app.route('/api/growth_rate')
def get_growth_rate():
    df = load_data()
    #调试5
    #   print(df.columns)
    if df is None:
        return jsonify({"error": "数据加载失败"}), 500
    
    daily_stats = df.groupby('报告日期').agg({
        '新增确诊': 'sum',
        '累计确诊': 'max'
    }).reset_index()
    
    # 计算增长率
    daily_stats['增长率'] = daily_stats['新增确诊'] / daily_stats['累计确诊'].shift(1) * 100
    daily_stats['增长率'] = daily_stats['增长率'].fillna(0)
    
    growth_data = {
        "dates": daily_stats['报告日期'].dt.strftime('%Y-%m-%d').tolist(),
        "growth_rate": daily_stats['增长率'].tolist()
    }
    return jsonify(growth_data)

@app.route('/api/hongkong_map')
def redirect_to_map():
    return redirect('/map')

@app.route('/map')
def map_view():
    m = create_map()
    if m is None:
        return "地图生成失败", 500
    m.save('templates/hk_covid_map.html')
    return render_template('hk_covid_map.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 