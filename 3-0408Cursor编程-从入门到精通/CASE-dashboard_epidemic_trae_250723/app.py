from flask import Flask, render_template
import pandas as pd
import json
import os

app = Flask(__name__)

# 读取Excel疫情数据
def get_epidemic_data():
    excel_path = os.path.join(os.path.dirname(__file__), '香港各区疫情数据_20250322.xlsx')
    df = pd.read_excel(excel_path, engine='openpyxl')
    # 提取需要的字段并转换为字典格式
    return df[["日期", "区名", "新增病例", "累计病例", "康复人数", "死亡人数", "风险等级"]].to_dict(orient='records')

# 读取香港地理数据
def get_hongkong_geo_data():
    json_path = os.path.join(os.path.dirname(__file__), 'hongkong.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# 首页路由 - 提供三大模块所需数据
@app.route('/')
def index():
    # 获取数据
    epidemic_data = get_epidemic_data()
    geo_data = get_hongkong_geo_data()
    
    # 数据预处理 - 提取核心指标
    latest_date = epidemic_data[0]['日期'] if epidemic_data else '未知日期'
    total_cases = sum(item['累计病例'] for item in epidemic_data)
    new_cases = sum(item['新增病例'] for item in epidemic_data)
    recovery_rate = round(sum(item['康复人数'] for item in epidemic_data) / total_cases * 100, 2) if total_cases > 0 else 0
    
    # 准备前端数据
    core_indicators = {
        'date': latest_date,
        'total_cases': total_cases,
        'new_cases': new_cases,
        'recovery_rate': recovery_rate,
        'death_rate': round(sum(item['死亡人数'] for item in epidemic_data) / total_cases * 100, 2) if total_cases > 0 else 0
    }
    
    # 按区域整理数据
    district_data = [{
        'name': item['区名'],
        'value': item['新增病例'],
        'risk_level': item['风险等级']
    } for item in epidemic_data]
    
    # 趋势分析数据
    trend_data = {
        'dates': list(set(item['日期'] for item in epidemic_data)),
        'new_cases': [sum(i['新增病例'] for i in epidemic_data if i['日期'] == date) for date in list(set(item['日期'] for item in epidemic_data))]
    }
    
    return render_template('index.html', 
                          core_indicators=core_indicators,
                          district_data=district_data,
                          geo_data=geo_data,
                          trend_data=trend_data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)