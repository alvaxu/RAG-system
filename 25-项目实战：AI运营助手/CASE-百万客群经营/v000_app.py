"""
程序说明：

## 1. Flask应用主文件，提供Web服务和数据API
## 2. 包含数据处理和图表数据生成的逻辑

"""

from flask import Flask, render_template, jsonify
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

app = Flask(__name__)

def load_data():
    """
    加载并处理CSV数据
    :function: 读取CSV文件并进行基础处理
    :return: 处理后的DataFrame
    """
    try:
        # 读取数据
        df_base = pd.read_csv('customer_base.csv')
        df_behavior = pd.read_csv('customer_behavior_assets.csv')
        
        # 合并数据
        df = pd.merge(df_base, df_behavior, on='customer_id', how='inner')
        return df
    except Exception as e:
        print(f"数据加载错误: {str(e)}")
        return None

def get_kpi_data(df):
    """
    计算KPI指标
    :function: 计算总览页面所需的KPI数据
    :param df: 数据DataFrame
    :return: KPI指标字典
    """
    try:
        total_assets = df['total_assets'].sum() / 100000000  # 转换为亿
        customer_count = df['customer_id'].nunique()
        
        # 计算月度环比
        current_month = df[df['stat_month'] == df['stat_month'].max()]
        last_month = df[df['stat_month'] == df['stat_month'].unique()[-2]]
        
        mom_assets = ((current_month['total_assets'].sum() / last_month['total_assets'].sum()) - 1) * 100
        mom_customers = ((current_month['customer_id'].nunique() / last_month['customer_id'].nunique()) - 1) * 100

        return {
            'total_assets': round(total_assets, 2),
            'total_assets_mom': round(mom_assets, 1),
            'customer_count': customer_count,
            'customer_count_mom': round(mom_customers, 1),
            'conversion_rate': 23.8,  # 示例数据，实际需要根据具体业务逻辑计算
            'conversion_rate_mom': 2.1,
            'churn_rate': 3.2,
            'churn_rate_mom': -0.5
        }
    except Exception as e:
        print(f"KPI计算错误: {str(e)}")
        return None

def get_asset_distribution(df):
    """
    计算资产分布数据
    :function: 统计不同资产等级的客户分布
    :param df: 数据DataFrame
    :return: 资产分布数据
    """
    try:
        # 根据total_assets进行分层
        df['asset_level'] = pd.cut(df['total_assets'], 
                                 bins=[0, 100000, 500000, float('inf')],
                                 labels=['普通客户', '中产客户', '高净值客户'])
        
        distribution = df['asset_level'].value_counts()
        
        return [{
            'name': level,
            'value': int(count)
        } for level, count in distribution.items()]
    except Exception as e:
        print(f"资产分布计算错误: {str(e)}")
        return []

def get_lifecycle_funnel(df):
    """
    计算生命周期漏斗图数据
    :function: 统计不同生命周期阶段的客户数量
    :param df: 数据DataFrame
    :return: 漏斗图数据
    """
    try:
        lifecycle_order = ['潜在客户', '新客户', '成长客户', '成熟客户', '忠诚客户']
        stage_counts = df['lifecycle_stage'].value_counts()
        
        # 确保按照正确的顺序排序
        funnel_data = []
        for stage in lifecycle_order:
            count = stage_counts.get(stage, 0)
            funnel_data.append({
                'name': stage,
                'value': int(count)
            })
        
        return funnel_data
    except Exception as e:
        print(f"生命周期漏斗图计算错误: {str(e)}")
        return []

def get_age_distribution(df):
    """
    计算年龄分布数据
    :function: 统计不同年龄段的客户分布
    :param df: 数据DataFrame
    :return: 年龄分布数据
    """
    try:
        df['age_group'] = pd.cut(df['age'],
                                bins=[0, 25, 35, 45, 55, 120],
                                labels=['18-25', '26-35', '36-45', '46-55', '56+'])
        
        age_dist = df['age_group'].value_counts().sort_index()
        
        return {
            'categories': age_dist.index.tolist(),
            'values': age_dist.values.tolist()
        }
    except Exception as e:
        print(f"年龄分布计算错误: {str(e)}")
        return {'categories': [], 'values': []}

def get_occupation_distribution(df):
    """
    计算职业分布数据
    :function: 统计职业分布TOP10
    :param df: 数据DataFrame
    :return: 职业分布数据
    """
    try:
        occupation_counts = df['occupation'].value_counts().head(10)
        
        return {
            'categories': occupation_counts.index.tolist(),
            'values': occupation_counts.values.tolist()
        }
    except Exception as e:
        print(f"职业分布计算错误: {str(e)}")
        return {'categories': [], 'values': []}

def get_asset_trend(df):
    """
    计算资产趋势数据
    :function: 统计月度资产变化趋势
    :param df: 数据DataFrame
    :return: 资产趋势数据
    """
    try:
        monthly_assets = df.groupby('stat_month')['total_assets'].sum() / 100000000  # 转换为亿
        
        return {
            'months': monthly_assets.index.tolist(),
            'values': monthly_assets.values.tolist()
        }
    except Exception as e:
        print(f"资产趋势计算错误: {str(e)}")
        return {'months': [], 'values': []}

@app.route('/')
def index():
    """
    渲染主页面
    :function: 返回大屏展示的HTML页面
    :return: 渲染后的模板
    """
    return render_template('dashboard.html')

@app.route('/api/dashboard-data')
def dashboard_data():
    """
    获取仪表板所需的所有数据
    :function: 返回大屏所需的所有数据
    :return: JSON格式的数据
    """
    try:
        df = load_data()
        if df is None:
            return jsonify({'error': '数据加载失败'})

        data = {
            'kpi': get_kpi_data(df),
            'asset_distribution': get_asset_distribution(df),
            'lifecycle_funnel': get_lifecycle_funnel(df),
            'age_distribution': get_age_distribution(df),
            'occupation_distribution': get_occupation_distribution(df),
            'asset_trend': get_asset_trend(df)
        }
        
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000) 