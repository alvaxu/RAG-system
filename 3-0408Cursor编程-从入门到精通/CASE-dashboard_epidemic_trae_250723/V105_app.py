'''程序说明：
## 1. 修复趋势图无法显示每日变化的问题，现在能正确展示所有日期的新增病例趋势
## 2. 分离地图和趋势图数据来源，地图使用最新日期数据，趋势图使用所有日期数据
## 3. 优化日期数据处理逻辑，确保趋势图日期排序正确
## 4. 修复每日新增病例汇总逻辑错误
'''
from flask import Flask, render_template
from datetime import timedelta  
import pandas as pd
import json
import os

app = Flask(__name__)

# 读取Excel疫情数据
def get_epidemic_data():
    """
    :function: 读取Excel文件中的疫情数据并返回所有日期的原始数据，不做日期筛选
    :return: 包含所有日期疫情数据的字典列表
    """
    excel_path = os.path.join(os.path.dirname(__file__), '香港各区疫情数据_20250322.xlsx')
    
    # 读取Excel文件
    df = pd.read_excel(excel_path, engine='openpyxl')
    
    # 调试输出：打印实际列名，帮助诊断列名不匹配问题
    print(f"Excel文件实际列名: {df.columns.tolist()}")
    
    # 定义标准列名和可能的替代列名
    standard_columns = ["区名", "新增病例", "累计病例", "康复人数", "死亡人数", "风险等级", "日期"]
    # 使用元组列表确保映射顺序
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
    
    # 转换日期列为datetime类型（不移除任何日期数据）
    if '日期' in result_df.columns:
        try:
            result_df['日期'] = pd.to_datetime(result_df['日期'])
            print(f"日期列转换成功，数据包含 {len(result_df['日期'].unique())} 个不同日期")
        except Exception as e:
            print(f"日期列转换错误: {str(e)}")
    else:
        print("警告: 数据中没有日期列，趋势图将无法正常显示")
    
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
    # 获取所有疫情数据
    all_epidemic_data = get_epidemic_data()
    geo_data = get_hongkong_geo_data()
    
    # 新增：获取最新日期和前一天日期数据
    if all_epidemic_data and '日期' in all_epidemic_data[0]:
        try:
            # 修复1：使用趋势分析相同的日期提取方法
            dates_with_datetime = [(pd.to_datetime(item['日期'], errors='coerce'), item['日期']) for item in all_epidemic_data]
            valid_dates = [(dt, date_str) for dt, date_str in dates_with_datetime if not pd.isna(dt)]
            
            if not valid_dates:
                print("错误：没有有效日期数据，无法计算环比变化")
                latest_data = []
                previous_data = []
            else:
                # 按日期排序（与趋势图逻辑一致）
                sorted_dates = sorted(valid_dates, key=lambda x: x[0])
                unique_dates = []
                seen_dates = set()
                for dt, date_str in sorted_dates:
                    if date_str not in seen_dates:
                        seen_dates.add(date_str)
                        unique_dates.append((dt, date_str))
                
                # 获取最新日期和前一天日期（从已排序的唯一日期列表中）
                if len(unique_dates) >= 2:
                    latest_dt, latest_date_str = unique_dates[-1]
                    prev_dt, prev_date_str = unique_dates[-2]
                else:
                    # 如果只有一个日期，使用同一天作为比较基准
                    latest_dt, latest_date_str = unique_dates[-1]
                    prev_dt, prev_date_str = unique_dates[-1]
                    print("警告：只有一个日期数据可用，环比变化将为0")
                
                # 筛选最新日期和前一天数据
                latest_data = [item for item in all_epidemic_data 
                              if pd.to_datetime(item['日期'], errors='coerce').date() == latest_dt.date()]
                previous_data = [item for item in all_epidemic_data 
                                if pd.to_datetime(item['日期'], errors='coerce').date() == prev_dt.date()]
                
                print(f"筛选最新日期 {latest_dt.date()} 的数据: {len(latest_data)}条")
                print(f"筛选前一天日期 {prev_dt.date()} 的数据: {len(previous_data)}条")
        except Exception as e:
            print(f"日期筛选错误: {str(e)}")
            # 异常处理：使用最新数据作为替代
            latest_data = all_epidemic_data
            previous_data = latest_data  # 使用最新数据作为前一天数据，确保环比变化为0
            # 删除错误代码：previous_data = []
            previous_data = []
    else:
        latest_data = all_epidemic_data
        previous_data = []
    
    # 初始化环比变化变量为默认值0
    total_change = 0
    new_change = 0
    recovery_rate_change = 0
    death_rate_change = 0
    latest_total = latest_new = recovery_rate = death_rate = 0
    prev_total = prev_new = prev_recovery = prev_death = 0
    prev_recovery_rate = prev_death_rate = 0
    total_change = new_change = recovery_rate_change = death_rate_change = 0
    
    # 筛选最新日期数据的渲染
    if all_epidemic_data and '日期' in all_epidemic_data[0]:
        try:
            # 转换日期并找到最新日期
            dates = [pd.to_datetime(item['日期']) for item in all_epidemic_data]
            latest_date = max(dates)
            # 筛选最新日期的数据
            epidemic_data = [item for item in all_epidemic_data if pd.to_datetime(item['日期']) == latest_date]
            print(f"筛选最新日期 {latest_date} 的数据，共 {len(epidemic_data)} 条记录")
        except Exception as e:
            print(f"筛选最新日期数据时出错: {str(e)}")
            epidemic_data = all_epidemic_data
    else:
        epidemic_data = all_epidemic_data

    
    # 计算核心指标及环比变化
    try:
        # 最新数据指标
        latest_total = sum(item['累计病例'] for item in latest_data) if '累计病例' in latest_data[0] else 0
        latest_new = sum(item['新增病例'] for item in latest_data) if '新增病例' in latest_data[0] else 0
        latest_recovery = sum(item['康复人数'] for item in latest_data) if '康复人数' in latest_data[0] else 0
        latest_death = sum(item['死亡人数'] for item in latest_data) if '死亡人数' in latest_data[0] else 0
        
        # 前一天数据指标
        prev_total = sum(item['累计病例'] for item in previous_data) if previous_data and '累计病例' in previous_data[0] else 0
        prev_new = sum(item['新增病例'] for item in previous_data) if previous_data and '新增病例' in previous_data[0] else 0
        prev_recovery = sum(item['康复人数'] for item in previous_data) if previous_data and '康复人数' in previous_data[0] else 0
        prev_death = sum(item['死亡人数'] for item in previous_data) if previous_data and '死亡人数' in previous_data[0] else 0
        
        # 计算环比变化
        total_change = latest_total - prev_total
        new_change = latest_new - prev_new
        recovery_rate = round(latest_recovery / latest_total * 100, 2) if latest_total > 0 else 0
        prev_recovery_rate = round(prev_recovery / prev_total * 100, 2) if prev_total > 0 else 0
        recovery_rate_change = recovery_rate - prev_recovery_rate
        
        death_rate = round(latest_death / latest_total * 100, 2) if latest_total > 0 else 0
        prev_death_rate = round(prev_death / prev_total * 100, 2) if prev_total > 0 else 0
        death_rate_change = death_rate - prev_death_rate
    except KeyError as e:
        print(f"指标计算KeyError: {str(e)}")
        # 保留原有异常处理逻辑并添加所有变化量的初始化
        latest_total = latest_new = recovery_rate = death_rate = 0
        total_change = new_change = recovery_rate_change = death_rate_change = 0
    
    # 准备核心指标数据（包含环比变化）
    core_indicators = {
        'date': epidemic_data[0]['日期'].strftime('%Y-%m-%d') if epidemic_data and '日期' in epidemic_data[0] else '未知日期',
        'total_cases': latest_total,
        'new_cases': latest_new,
        'recovery_rate': recovery_rate,
        'death_rate': death_rate,
        # 确保所有变化属性被显式定义
        'total_change': total_change,
        'new_change': new_change,
        'recovery_rate_change': round(recovery_rate_change, 2),
        'death_rate_change': round(death_rate_change, 2)
    }
    
    # 趋势分析使用所有数据
    trend_epidemic_data = all_epidemic_data
    print(f"调试: 传递给前端的地理数据结构 - {list(geo_data.keys()) if isinstance(geo_data, dict) else '非字典类型'}")
    
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
    # core_indicators = {
    #     'date': latest_date,
    #     'total_cases': total_cases,
    #     'new_cases': new_cases,
    #     'recovery_rate': recovery_rate,
    #     'death_rate': round(sum(item['死亡人数'] for item in epidemic_data) / total_cases * 100, 2) if total_cases > 0 and '死亡人数' in epidemic_data[0] else 0
    # }
    
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
    if trend_epidemic_data and '日期' in trend_epidemic_data[0]:
        # 提取所有日期并转换为datetime对象以便正确排序
        dates_with_datetime = [(pd.to_datetime(item['日期']), item['日期']) for item in trend_epidemic_data]
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
    
    # 按日期聚合新增病例数据 - 关键修复：使用trend_epidemic_data而非epidemic_data
    new_cases = []
    for date in dates:
        try:
            # 累加特定日期的所有新增病例（从所有区域数据中）
            daily_cases = sum(i['新增病例'] for i in trend_epidemic_data if pd.to_datetime(i['日期']) == pd.to_datetime(date))
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