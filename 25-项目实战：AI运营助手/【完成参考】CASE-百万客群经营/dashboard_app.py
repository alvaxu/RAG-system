import pandas as pd
from flask import Flask, render_template, jsonify
import os

app = Flask(__name__)

# 读取数据
base_path = os.path.dirname(os.path.abspath(__file__))
data_file = os.path.join(base_path, '二组模拟数据.csv')

def read_data():
    try:
        df = pd.read_csv(data_file, encoding='utf-8')
    except Exception:
        df = pd.read_csv(data_file, encoding='gbk')
    return df

@app.route('/')
def index():
    # 渲染主页面
    return render_template('dashboard.html')

@app.route('/api/indicators')
def api_indicators():
    """核心指标卡片数据接口"""
    df = read_data()
    total_customers = df['customer_id'].nunique()
    total_assets = df['total_aum'].sum()
    avg_assets = df['total_aum'].mean()
    # 活跃客户数定义：近期有手机银行登录
    if 'last_mobile_login' in df.columns:
        active_count = df['last_mobile_login'].notnull().sum()
    else:
        active_count = None
    # 产品复购率定义：每月交易次数大于平均值的客户占比
    if 'monthly_transaction_count' in df.columns:
        avg_transaction_count = df['monthly_transaction_count'].mean()
        repurchase_rate = (df['monthly_transaction_count'] > avg_transaction_count).mean()
    else:
        repurchase_rate = None
    return jsonify({
        'total_customers': int(total_customers),
        'total_assets': float(total_assets),
        'avg_assets': float(avg_assets),
        'active_customers': int(active_count) if active_count is not None else None,
        'repurchase_rate': float(repurchase_rate) if repurchase_rate is not None else None
    })

@app.route('/api/lifecycle')
def api_lifecycle():
    """客户结构分布（生命周期）"""
    df = read_data()
    # 使用客户等级作为生命周期代理变量
    if 'customer_tier' in df.columns:
        data = df['customer_tier'].value_counts().to_dict()
    else:
        # 从年龄数据划分生命周期
        if 'age' in df.columns:
            df['lifecycle_stage'] = pd.cut(
                df['age'], 
                bins=[0, 30, 45, 60, 100], 
                labels=['青年', '中年', '中老年', '老年']
            )
            data = df['lifecycle_stage'].value_counts().to_dict()
        else:
            data = {}
    return jsonify(data)

@app.route('/api/asset_level')
def api_asset_level():
    """客户资产等级分布"""
    df = read_data()
    # 使用total_aum进行资产等级划分
    if 'total_aum' in df.columns:
        df['asset_level'] = pd.cut(
            df['total_aum'], 
            bins=[0, 100000, 500000, 1000000, float('inf')], 
            labels=['低资产', '中等资产', '高资产', '超高资产']
        )
        data = df['asset_level'].value_counts().to_dict()
    else:
        data = {}
    return jsonify(data)

@app.route('/api/product_holdings')
def api_product_holdings():
    """产品持有情况统计"""
    df = read_data()
    # 根据余额创建产品持有标志
    df['deposit_flag'] = (df['deposit_balance'] > 0).astype(int)
    df['financial_flag'] = (df['wealth_management_balance'] > 0).astype(int)
    df['fund_flag'] = (df['fund_balance'] > 0).astype(int)
    df['insurance_flag'] = (df['insurance_balance'] > 0).astype(int)
    
    product_types = ['deposit_flag', 'financial_flag', 'fund_flag', 'insurance_flag']
    result = {}
    for p in product_types:
        result[p] = int((df[p] == 1).sum())
    return jsonify(result)

@app.route('/api/app_active_trend')
def api_app_active_trend():
    """客户行为与活跃度（按登录次数分组统计）"""
    df = read_data()
    if 'mobile_bank_login_count' in df.columns:
        # 按登录次数分组统计客户数
        df['login_group'] = pd.cut(
            df['mobile_bank_login_count'], 
            bins=[0, 5, 10, 15, 20, float('inf')], 
            labels=['0-5次', '6-10次', '11-15次', '16-20次', '20次以上']
        )
        trend = df['login_group'].value_counts().sort_index().to_dict()
    else:
        trend = {}
    return jsonify(trend)

@app.route('/api/risk')
def api_risk():
    """风险与预警分析（根据交易频率判断）"""
    df = read_data()
    # 使用交易频率作为风险指标代理
    if 'monthly_transaction_count' in df.columns:
        # 将客户按交易频率分为三类风险
        avg_count = df['monthly_transaction_count'].mean()
        std_count = df['monthly_transaction_count'].std()
        
        def risk_level(val):
            if pd.isnull(val) or val == 0:
                return '高风险'
            elif val < avg_count - 0.5 * std_count:
                return '中风险'
            else:
                return '低风险'
                
        df['risk_level'] = df['monthly_transaction_count'].apply(risk_level)
        data = df['risk_level'].value_counts().to_dict()
    else:
        data = {}
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, port=5001) 