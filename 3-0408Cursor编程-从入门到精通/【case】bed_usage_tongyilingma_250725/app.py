import pandas as pd
from flask import Flask, render_template, jsonify
from datetime import datetime
import numpy as np

app = Flask(__name__)

# 加载数据
def load_data():
    try:
        df = pd.read_excel('hospital_bed_usage_data.xlsx')
        print("Data loaded successfully.")
        print(df.head())  # 打印前五行数据以便检查
        print(df.columns)  # 打印列名以便检查
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

# 获取总体统计数据
def get_overview_stats(df):
    total_beds = df['total_beds'].sum()
    occupied_beds = df['occupied_beds'].sum()
    available_beds = df['available_beds'].sum()
    occupancy_rate = round((occupied_beds / total_beds) * 100, 2) if total_beds > 0 else 0
    
    # 获取最新时间戳
    latest_timestamp = df['timestamp'].max()
    
    return {
        'total_beds': int(total_beds),
        'occupied_beds': int(occupied_beds),
        'available_beds': int(available_beds),
        'occupancy_rate': occupancy_rate,
        'latest_timestamp': latest_timestamp.strftime('%Y-%m-%d %H:%M:%S') if not pd.isnull(latest_timestamp) else 'N/A'
    }

# 获取各医院床位占用率
def get_hospital_occupancy(df):
    hospital_stats = df.groupby('hospital_name').agg({
        'total_beds': 'sum',
        'occupied_beds': 'sum'
    }).reset_index()
    
    hospital_stats['occupancy_rate'] = (
        hospital_stats['occupied_beds'] / hospital_stats['total_beds'] * 100
    ).round(2)
    
    result = []
    for _, row in hospital_stats.iterrows():
        result.append({
            'hospital_name': row['hospital_name'],
            'total_beds': int(row['total_beds']),
            'occupied_beds': int(row['occupied_beds']),
            'occupancy_rate': row['occupancy_rate']
        })
    
    return result

# 获取各科室床位占用率
def get_department_occupancy(df):
    dept_stats = df.groupby('department_name').agg({
        'total_beds': 'sum',
        'occupied_beds': 'sum'
    }).reset_index()
    
    dept_stats['occupancy_rate'] = (
        dept_stats['occupied_beds'] / dept_stats['total_beds'] * 100
    ).round(2)
    
    # 只返回前10个科室
    dept_stats = dept_stats.sort_values('occupancy_rate', ascending=False).head(10)
    
    result = []
    for _, row in dept_stats.iterrows():
        result.append({
            'department_name': row['department_name'],
            'total_beds': int(row['total_beds']),
            'occupied_beds': int(row['occupied_beds']),
            'occupancy_rate': row['occupancy_rate']
        })
    
    return result

# 获取地区分布数据
def get_district_distribution(df):
    district_stats = df.groupby('hospital_district').agg({
        'available_beds': 'sum'
    }).reset_index()
    
    result = []
    for _, row in district_stats.iterrows():
        result.append({
            'district': row['hospital_district'],
            'available_beds': int(row['available_beds'])
        })
    
    return result

# 获取特殊状态统计
def get_special_status_stats(df):
    status_counts = df['special_status'].value_counts().to_dict()
    result = []
    for status, count in status_counts.items():
        result.append({
            'status': status,
            'count': int(count)
        })
    return result

# 主页路由
@app.route('/')
def index():
    return render_template('index.html')

# API路由
@app.route('/api/overview')
def overview():
    df = load_data()
    stats = get_overview_stats(df)
    return jsonify(stats)

@app.route('/api/hospital_occupancy')
def hospital_occupancy():
    df = load_data()
    data = get_hospital_occupancy(df)
    return jsonify(data)

@app.route('/api/department_occupancy')
def department_occupancy():
    df = load_data()
    data = get_department_occupancy(df)
    return jsonify(data)

@app.route('/api/district_distribution')
def district_distribution():
    df = load_data()
    data = get_district_distribution(df)
    return jsonify(data)

@app.route('/api/special_status')
def special_status():
    df = load_data()
    data = get_special_status_stats(df)
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)