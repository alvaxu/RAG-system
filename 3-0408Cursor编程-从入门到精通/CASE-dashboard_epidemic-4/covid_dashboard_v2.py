import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Line, Map, Bar, Grid, Timeline, Pie
from pyecharts.globals import ThemeType
import json
from datetime import datetime, timedelta

# 读取数据
def load_data():
    try:
        df = pd.read_excel('香港各区疫情数据_20250322.xlsx')
        df['报告日期'] = pd.to_datetime(df['报告日期'])
        print("数据加载成功！")
        return df
    except Exception as e:
        print(f"数据加载失败：{e}")
        return None

# 1. 总体数据概览和趋势图
def create_left_panel(df):
    # 获取最新日期的数据
    latest_date = df['报告日期'].max()
    latest_data = df[df['报告日期'] == latest_date]
    
    # 计算总体数据
    total_confirmed = latest_data['累计确诊'].max()
    total_recovered = latest_data['累计康复'].max()
    total_deaths = latest_data['累计死亡'].max()
    
    # 按日期统计数据
    daily_stats = df.groupby('报告日期').agg({
        '新增确诊': 'sum',
        '累计确诊': 'max'
    }).reset_index()
    
    # 创建折线图
    line = (
        Line(init_opts=opts.InitOpts(
            theme=ThemeType.DARK,
            width="400px",
            height="300px",
            chart_id="trend_chart"
        ))
        .add_xaxis(daily_stats['报告日期'].dt.strftime('%Y-%m-%d').tolist())
        .add_yaxis(
            "新增确诊",
            daily_stats['新增确诊'].tolist(),
            yaxis_index=0,
            color="#FF6B6B",
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            "累计确诊",
            daily_stats['累计确诊'].tolist(),
            yaxis_index=1,
            color="#4ECDC4",
            label_opts=opts.LabelOpts(is_show=False),
        )
        .extend_axis(
            yaxis=opts.AxisOpts(
                name="累计确诊数",
                type_="value",
                position="right",
                axislabel_opts=opts.LabelOpts(formatter="{value} 例"),
            )
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title="每日新增与累计确诊趋势"),
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross"),
            legend_opts=opts.LegendOpts(pos_left="center"),
            xaxis_opts=opts.AxisOpts(
                type_="category",
                axislabel_opts=opts.LabelOpts(rotate=45),
            ),
            yaxis_opts=opts.AxisOpts(
                name="新增确诊数",
                type_="value",
                axislabel_opts=opts.LabelOpts(formatter="{value} 例"),
            ),
        )
    )
    
    # 创建概览数据HTML
    overview_html = f"""
    <div class="overview-container">
        <div class="overview-item">
            <div class="overview-title">累计确诊</div>
            <div class="overview-value">{total_confirmed:,}</div>
        </div>
        <div class="overview-item">
            <div class="overview-title">累计康复</div>
            <div class="overview-value">{total_recovered:,}</div>
        </div>
        <div class="overview-item">
            <div class="overview-title">累计死亡</div>
            <div class="overview-value">{total_deaths:,}</div>
        </div>
    </div>
    """
    
    return overview_html, line

# 2. 地理分布图（带时间轴）
def create_map_chart(df):
    # 创建时间轴
    timeline = Timeline(
        init_opts=opts.InitOpts(
            theme=ThemeType.DARK,
            width="600px",
            height="500px",
            chart_id="map_chart"
        )
    )
    
    # 获取所有日期
    dates = sorted(df['报告日期'].unique())
    
    # 为每个日期创建地图
    for date in dates:
        date_data = df[df['报告日期'] == date]
        map_data = [
            [name, value] for name, value in zip(
                date_data['地区名称'],
                date_data['累计确诊']
            )
        ]
        
        map_chart = (
            Map()
            .add(
                "累计确诊",
                map_data,
                "香港",
                is_map_symbol_show=False,
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title=f"香港各区疫情分布 ({date.strftime('%Y-%m-%d')})"
                ),
                visualmap_opts=opts.VisualMapOpts(
                    max_=df['累计确诊'].max(),
                    is_piecewise=True,
                    pieces=[
                        {"min": 0, "max": 1000, "label": "0-1000", "color": "#FFE4E1"},
                        {"min": 1000, "max": 5000, "label": "1000-5000", "color": "#FFB6C1"},
                        {"min": 5000, "max": 10000, "label": "5000-10000", "color": "#FF69B4"},
                        {"min": 10000, "max": 20000, "label": "10000-20000", "color": "#FF1493"},
                        {"min": 20000, "label": ">20000", "color": "#8B0000"},
                    ],
                ),
            )
        )
        timeline.add(map_chart, time_point=date.strftime("%Y-%m-%d"))
    
    return timeline

# 3. 康复和死亡趋势图
def create_right_panel(df):
    # 按日期统计数据
    daily_stats = df.groupby('报告日期').agg({
        '新增康复': 'sum',
        '累计康复': 'max',
        '新增死亡': 'sum',
        '累计死亡': 'max'
    }).reset_index()
    
    # 创建康复趋势图
    recovery_chart = (
        Line(init_opts=opts.InitOpts(
            theme=ThemeType.DARK,
            width="400px",
            height="300px",
            chart_id="recovery_chart"
        ))
        .add_xaxis(daily_stats['报告日期'].dt.strftime('%Y-%m-%d').tolist())
        .add_yaxis(
            "新增康复",
            daily_stats['新增康复'].tolist(),
            yaxis_index=0,
            color="#00C853",  # 更鲜艳的绿色
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            "累计康复",
            daily_stats['累计康复'].tolist(),
            yaxis_index=1,
            color="#69F0AE",  # 更亮的绿色
            label_opts=opts.LabelOpts(is_show=False),
        )
        .extend_axis(
            yaxis=opts.AxisOpts(
                name="累计康复数",
                type_="value",
                position="right",
                axislabel_opts=opts.LabelOpts(formatter="{value} 例"),
            )
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title="康复趋势分析"),
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross"),
            legend_opts=opts.LegendOpts(pos_left="center"),
            xaxis_opts=opts.AxisOpts(
                type_="category",
                axislabel_opts=opts.LabelOpts(rotate=45),
            ),
            yaxis_opts=opts.AxisOpts(
                name="新增康复数",
                type_="value",
                axislabel_opts=opts.LabelOpts(formatter="{value} 例"),
            ),
        )
    )
    
    # 创建死亡趋势图
    death_chart = (
        Line(init_opts=opts.InitOpts(
            theme=ThemeType.DARK,
            width="400px",
            height="300px",
            chart_id="death_chart"
        ))
        .add_xaxis(daily_stats['报告日期'].dt.strftime('%Y-%m-%d').tolist())
        .add_yaxis(
            "新增死亡",
            daily_stats['新增死亡'].tolist(),
            yaxis_index=0,
            color="#D50000",  # 更深的红色
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            "累计死亡",
            daily_stats['累计死亡'].tolist(),
            yaxis_index=1,
            color="#FF5252",  # 更亮的红色
            label_opts=opts.LabelOpts(is_show=False),
        )
        .extend_axis(
            yaxis=opts.AxisOpts(
                name="累计死亡数",
                type_="value",
                position="right",
                axislabel_opts=opts.LabelOpts(formatter="{value} 例"),
            )
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title="死亡趋势分析"),
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross"),
            legend_opts=opts.LegendOpts(pos_left="center"),
            xaxis_opts=opts.AxisOpts(
                type_="category",
                axislabel_opts=opts.LabelOpts(rotate=45),
            ),
            yaxis_opts=opts.AxisOpts(
                name="新增死亡数",
                type_="value",
                axislabel_opts=opts.LabelOpts(formatter="{value} 例"),
            ),
        )
    )
    
    return recovery_chart, death_chart

# 4. 风险等级分布饼图
def create_risk_pie_chart(df):
    # 获取最新日期的数据
    latest_date = df['报告日期'].max()
    latest_data = df[df['报告日期'] == latest_date]
    
    # 统计各风险等级的数量
    risk_counts = latest_data['风险等级'].value_counts()
    
    # 定义风险等级的颜色
    risk_colors = {
        '高风险': '#FF5252',  # 红色
        '中风险': '#FFA726',  # 橙色
        '低风险': '#4CAF50',  # 绿色
        '无风险': '#2196F3'   # 蓝色
    }
    
    # 创建饼图
    pie = (
        Pie(init_opts=opts.InitOpts(
            theme=ThemeType.DARK,
            width="600px",
            height="300px",
            chart_id="risk_pie_chart"
        ))
        .add(
            "",
            [list(z) for z in zip(risk_counts.index, risk_counts.values)],
            radius=["40%", "70%"],
            label_opts=opts.LabelOpts(
                formatter="{b}: {c} ({d}%)",
                position="outside"
            ),
            itemstyle_opts=opts.ItemStyleOpts(
                color=lambda x: risk_colors.get(x.data['name'], '#999')
            )
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title="风险等级分布"),
            legend_opts=opts.LegendOpts(
                orient="vertical",
                pos_left="left",
                pos_top="middle"
            )
        )
    )
    
    return pie

def main():
    # 加载数据
    df = load_data()
    if df is None:
        return
    
    # 创建图表
    overview_html, trend_chart = create_left_panel(df)
    map_chart = create_map_chart(df)
    recovery_chart, death_chart = create_right_panel(df)
    risk_pie_chart = create_risk_pie_chart(df)
    
    # 创建页面
    with open("covid_dashboard_v2.html", "w", encoding="utf-8") as f:
        # 写入HTML头部
        f.write('<!DOCTYPE html>\n')
        f.write('<html>\n')
        f.write('<head>\n')
        f.write('    <meta charset="UTF-8">\n')
        f.write('    <title>香港疫情数据大屏</title>\n')
        f.write('    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>\n')
        f.write('    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/map/js/china.js"></script>\n')
        f.write('    <style>\n')
        f.write('        body { margin: 0; padding: 20px; background-color: #1E1E1E; color: white; font-family: Arial, sans-serif; }\n')
        f.write('        .header { text-align: center; margin-bottom: 20px; padding: 20px; background-color: #2D2D2D; border-radius: 10px; }\n')
        f.write('        .header h1 { margin: 0; font-size: 32px; color: #FFFFFF; }\n')
        f.write('        .header p { margin: 10px 0; color: #AAAAAA; }\n')
        f.write('        .container { display: flex; justify-content: space-between; max-width: 1400px; margin: 0 auto; }\n')
        f.write('        .panel { background-color: #2D2D2D; border-radius: 10px; padding: 20px; margin: 10px; }\n')
        f.write('        .left-panel { width: 400px; }\n')
        f.write('        .center-panel { width: 600px; }\n')
        f.write('        .right-panel { width: 400px; display: flex; flex-direction: column; }\n')
        f.write('        .overview-container { display: flex; flex-direction: column; gap: 15px; margin-bottom: 20px; }\n')
        f.write('        .overview-item { background-color: #3D3D3D; padding: 15px; border-radius: 8px; text-align: center; }\n')
        f.write('        .overview-title { font-size: 16px; color: #AAAAAA; margin-bottom: 5px; }\n')
        f.write('        .overview-value { font-size: 24px; font-weight: bold; color: #FFFFFF; }\n')
        f.write('        .chart { width: 100%; height: 300px; }\n')
        f.write('        .chart-container { margin-bottom: 20px; height: 300px; }\n')
        f.write('    </style>\n')
        f.write('</head>\n')
        f.write('<body>\n')
        
        # 写入标题栏
        f.write(f'    <div class="header">\n')
        f.write('        <h1>香港疫情数据大屏</h1>\n')
        f.write(f'        <p>数据更新时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>\n')
        f.write('    </div>\n')
        
        # 写入容器
        f.write('    <div class="container">\n')
        
        # 写入左侧面板
        f.write('        <div class="panel left-panel">\n')
        f.write('            <div class="overview-container">\n')
        f.write(overview_html)
        f.write('            </div>\n')
        f.write('            <div id="trend_chart" class="chart"></div>\n')
        f.write('        </div>\n')
        
        # 写入中间面板
        f.write('        <div class="panel center-panel">\n')
        f.write('            <div id="map_chart" class="chart"></div>\n')
        f.write('            <div id="risk_pie_chart" class="chart"></div>\n')
        f.write('        </div>\n')
        
        # 写入右侧面板
        f.write('        <div class="panel right-panel">\n')
        f.write('            <div class="chart-container">\n')
        f.write('                <div id="recovery_chart" class="chart"></div>\n')
        f.write('            </div>\n')
        f.write('            <div class="chart-container">\n')
        f.write('                <div id="death_chart" class="chart"></div>\n')
        f.write('            </div>\n')
        f.write('        </div>\n')
        
        f.write('    </div>\n')
        
        # 写入图表代码
        f.write(trend_chart.render_embed())
        f.write(map_chart.render_embed())
        f.write(recovery_chart.render_embed())
        f.write(death_chart.render_embed())
        f.write(risk_pie_chart.render_embed())
        
        f.write('</body>\n')
        f.write('</html>\n')
    
    print("可视化大屏已生成！请查看 covid_dashboard_v2.html")

if __name__ == "__main__":
    main() 