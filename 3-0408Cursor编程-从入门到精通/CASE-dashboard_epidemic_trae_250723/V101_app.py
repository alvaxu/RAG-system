'''
程序说明：
## 1. 修复Excel列名匹配问题，解决KeyError错误
## 2. 添加调试输出，显示Excel文件实际列名
## 3. 优化数据读取逻辑，提高兼容性
## 4. 修复地图数据显示问题，只显示最新日期的新增病例数据
'''
from flask import Flask, render_template
import pandas as pd
import json
import os

app = Flask(__name__)

# 读取Excel疫情数据
def get_epidemic_data():
    """
    :function: 读取Excel文件中的疫情数据并返回处理后的字典列表，只保留最新日期的数据
    :return: 包含最新日期疫情数据的字典列表
    """
    excel_path = os.path.join(os.path.dirname(__file__), '香港各区疫情数据_20250322.xlsx')
    
    # 读取Excel文件
    df = pd.read_excel(excel_path, engine='openpyxl')
    
    # 调试输出：打印实际列名，帮助诊断列名不匹配问题
    print(f"Excel文件实际列名: {df.columns.tolist()}")
    
    # 定义标准列名和可能的替代列名
    standard_columns = ["区名", "新增病例", "累计病例", "康复人数", "死亡人数", "风险等级", "日期"]
    # 使用元组列表确保映射顺序（Python 3.6以下字典不保证顺序）
    alternative_columns = [
        ("报告日期", "日期"),
        ("地区名称", "区名"),  # 优先匹配Excel中的"地区名称"
        ("区域名称", "区名"),
        ("地区", "区名"),
        ("区域", "区名"),
        ("新增确诊", "新增病例"),
        ("新增病例数", "新增病例"),
        ("累计确诊", "累计病例"),
        ("累计病例数", "累计病例"),
        ("累计康复", "康复人数"),  # 优先匹配Excel中的"累计康复"
        ("新增康复", "康复人数"),
        ("治愈人数", "康复人数"),
        ("痊愈人数", "康复人数"),
        ("累计死亡", "死亡人数"),  # 优先匹配Excel中的"累计死亡"
        ("新增死亡", "死亡人数"),
        ("死亡人数", "死亡人数"),
        ("风险程度", "风险等级"),
        ("报告日期", "日期"),
        ("数据日期", "日期")
    ]
    
    # 检查哪些标准列名存在
    existing_columns = []
    missing_columns = []
    column_mapping = {}
    
    for col in standard_columns:
        if col in df.columns:
            existing_columns.append(col)
            column_mapping[col] = col
        else:
            missing_columns.append(col)
    
    print(f"找到的标准列名: {existing_columns}")
    print(f"缺失的标准列名: {missing_columns}")
    
    # 尝试用替代列名匹配缺失的标准列名
    for missing_col in missing_columns:
        found = False
        for alt_col, std_col in alternative_columns:
            if std_col == missing_col and alt_col in df.columns:
                column_mapping[alt_col] = std_col
                found = True
                print(f"使用替代列名 '{alt_col}' 匹配缺失列 '{missing_col}'")
                break
        if not found:
            print(f"警告: 无法找到列 '{missing_col}' 的匹配项")
    
    # 方案2：使用所有可用列（如果方案1失败）
    if not column_mapping:
        print("所有标准列名都未找到，将返回所有可用列")
        result_df = df
    else:
        # 重命名列并选择所需列
        result_df = df.rename(columns={k: v for k, v in column_mapping.items()})
        
        # 确保所有标准列都存在
        for col in standard_columns:
            if col not in result_df.columns:
                result_df[col] = 0  # 或其他适当的默认值
                print(f"警告: 添加缺失列 '{col}'，值设为0")
    
    # 筛选最新日期的数据
    if '日期' in result_df.columns:
        try:
            # 转换日期列为datetime类型
            result_df['日期'] = pd.to_datetime(result_df['日期'])
            # 获取最新日期
            latest_date = result_df['日期'].max()
            # 筛选最新日期的数据
            result_df = result_df[result_df['日期'] == latest_date]
            print(f"筛选后的数据日期: {latest_date}, 记录数: {len(result_df)}")
        except Exception as e:
            print(f"筛选日期时发生错误: {str(e)}")
    else:
        print("警告: 数据中没有日期列，无法筛选最新数据")
    
    return result_df.to_dict(orient='records')

# 读取香港地理数据
def get_hongkong_geo_data():
    """
    :function: 读取香港地理数据JSON文件，并确保返回格式包含'regions'键
    :return: 包含香港地理信息的字典，格式为{regions: [...]} 
    """
    json_path = os.path.join(os.path.dirname(__file__), 'hongkong.json')
    
    try:
        # 尝试打开并读取JSON文件
        with open(json_path, 'r', encoding='utf-8') as f:
            try:
                geo_data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"错误: 香港地理数据JSON解析失败 - {str(e)}")
                return {'regions': []}
        
        # 确保返回数据包含'regions'键，适配ECharts地图组件
        if 'regions' not in geo_data:
            # 如果JSON使用'features'键（GeoJSON标准），重命名为'regions'
            if 'features' in geo_data:
                geo_data['features'] = geo_data['features']  # 保持标准GeoJSON键名
                print("信息: 保持GeoJSON标准'features'键名")
            # 如果是其他格式，尝试提取区域数据
            elif 'data' in geo_data and isinstance(geo_data['data'], list):
                geo_data['regions'] = geo_data['data']
                print("信息: 使用'data'字段作为区域数据来源")
            else:
                # 作为最后的备选方案，直接使用顶层数组
                if isinstance(geo_data, list):
                    geo_data = {'features': geo_data}
                    print("信息: 顶层数组已转换为'features'对象")
                else:
                    # 创建空regions数组避免前端错误
                    geo_data['features'] = []
                    print("警告: 香港地理数据格式不支持，已创建空features数组")
        
        return geo_data
    
    except FileNotFoundError:
        print(f"错误: 香港地理数据文件未找到 - {json_path}")
        return {'regions': []}
    except Exception as e:
        print(f"错误: 读取地理数据时发生意外错误 - {str(e)}")
        return {'regions': []}

# 首页路由 - 提供三大模块所需数据
@app.route('/')
def index():
    """
    :function: 处理首页请求，渲染疫情数据大屏
    :return: 渲染后的HTML页面
    """
    # 获取数据
    epidemic_data = get_epidemic_data()
    geo_data = get_hongkong_geo_data()
    print(f"调试: 传递给前端的地理数据结构 - {list(geo_data.keys()) if isinstance(geo_data, dict) else '非字典类型'}")
    print(f"调试: geo_data内容 - {geo_data}")
    
    # 数据预处理 - 提取核心指标
    latest_date = epidemic_data[0]['日期'].strftime('%Y-%m-%d') if epidemic_data and '日期' in epidemic_data[0] else '未知日期'
    
    # 计算最大新增病例数，用于前端热力图visualMap配置
    max_new_cases = 0
    if epidemic_data and '新增病例' in epidemic_data[0]:
        max_new_cases = max(item['新增病例'] for item in epidemic_data) if epidemic_data else 10
        print(f"调试: 最大新增病例数 - {max_new_cases}")
    
    # 使用try-except块处理可能的KeyError
    try:
        total_cases = sum(item['累计病例'] for item in epidemic_data) if '累计病例' in epidemic_data[0] else 0
        new_cases = sum(item['新增病例'] for item in epidemic_data) if '新增病例' in epidemic_data[0] else 0
        recovery_rate = round(sum(item['康复人数'] for item in epidemic_data) / total_cases * 100, 2) if total_cases > 0 and '康复人数' in epidemic_data[0] else 0
    except KeyError as e:
        print(f"计算核心指标时发生KeyError: {str(e)}")
        total_cases = 0
        new_cases = 0
        recovery_rate = 0
    
    # 准备前端数据
    core_indicators = {
        'date': latest_date,
        'total_cases': total_cases,
        'new_cases': new_cases,
        'recovery_rate': recovery_rate,
        'death_rate': round(sum(item['死亡人数'] for item in epidemic_data) / total_cases * 100, 2) if total_cases > 0 and '死亡人数' in epidemic_data[0] else 0
    }
    
    # 按区域整理数据
    district_data = []
    for item in epidemic_data:
        try:
            # 动态计算风险等级
            新增病例数 = item['新增病例']
            if 新增病例数 > 50:
                风险等级 = '高'
            elif 新增病例数 > 10:
                风险等级 = '中'
            else:
                风险等级 = '低'
            district_item = {
                'name': item['区名'],
                'value': 新增病例数,
                'risk_level': 风险等级
            }
            district_data.append(district_item)
        except KeyError as e:
            print(f"处理区域数据时发生KeyError: {str(e)}")
            district_data.append({
                'name': '数据错误',
                'value': 0,
                'risk_level': '错误',
                'error': str(e)
            })
    
    # 趋势分析数据 - 修复日期排序和数据聚合问题
    # 获取所有日期并排序
    if epidemic_data and '日期' in epidemic_data[0]:
        # 提取所有日期并转换为datetime对象以便正确排序
        dates_with_datetime = [(pd.to_datetime(item['日期']), item['日期']) for item in epidemic_data]
        # 按datetime排序并提取原始日期字符串
        sorted_dates = sorted(dates_with_datetime, key=lambda x: x[0])
        unique_dates = []
        seen_dates = set()
        for dt, date_str in sorted_dates:
            if date_str not in seen_dates:
                seen_dates.add(date_str)
                unique_dates.append(date_str)
        dates = unique_dates
    else:
        dates = []
    
    # 按日期聚合新增病例数据
    new_cases = []
    for date in dates:
        try:
            # 累加特定日期的所有新增病例
            daily_cases = sum(i['新增病例'] for i in epidemic_data if i['日期'] == date)
            new_cases.append(daily_cases)
            print(f"日期'{date}'的新增病例: {daily_cases}")  # 添加调试输出
        except KeyError as e:
            # 处理可能的键错误，添加0作为默认值
            new_cases.append(0)
            print(f"警告: 日期'{date}'的新增病例数据缺失 - {str(e)}")
    
    # 确保至少有一些数据可供显示
    if not dates:
        # 如果没有日期数据，创建默认日期范围
        from datetime import datetime, timedelta
        today = datetime.now()
        dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7, -1, -1)]
        new_cases = [0]*8  # 8天的默认数据
        print("警告: 未找到日期数据，使用默认日期范围")
    
    trend_data = {
        'dates': dates,
        'new_cases': new_cases
    }

    # 调试输出趋势数据
    print(f"调试: 趋势数据 - {trend_data}")
    
    return render_template('index.html', 
                          core_indicators=core_indicators,
                          district_data=district_data,
                          geo_data=geo_data,
                          trend_data=trend_data,
                          max_new_cases=max_new_cases)

if __name__ == '__main__':
    print("===== 疫情数据大屏应用 ====")
    print("提示: 应用正在运行调试模式，将显示详细日志信息")
    app.run(debug=True, port=5000)