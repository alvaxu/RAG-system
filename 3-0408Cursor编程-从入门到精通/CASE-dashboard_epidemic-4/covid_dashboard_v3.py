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
            color="#00C853",
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            "累计康复",
            daily_stats['累计康复'].tolist(),
            yaxis_index=1,
            color="#69F0AE",
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
            title_opts=opts.TitleOpts(title="", is_show=False),
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
    
    # 创建死亡趋势图 - 使用更深的红色系
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
            color="#FF1744",
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            "累计死亡",
            daily_stats['累计死亡'].tolist(),
            yaxis_index=1,
            color="#D50000",
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
            title_opts=opts.TitleOpts(title="", is_show=False),
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

# 4. 风险等级饼图
def create_risk_pie_chart(df):
    # 获取最新日期的数据
    latest_date = df['报告日期'].max()
    latest_data = df[df['报告日期'] == latest_date]
    
    # 计算风险等级分布
    risk_levels = latest_data['风险等级'].value_counts()
    
    # 创建饼图数据
    pie_data = [
        {"value": count, "name": level}
        for level, count in risk_levels.items()
    ]
    
    # 创建饼图
    pie = (
        Pie(init_opts=opts.InitOpts(
            theme=ThemeType.DARK,
            width="600px",
            height="300px",
            chart_id="risk_pie_chart"
        ))
        .add(
            "风险等级分布",
            pie_data,
            radius=["30%", "70%"],
            center=["50%", "50%"],
            label_opts=opts.LabelOpts(
                formatter="{b}: {c} ({d}%)",
                position="outside",
                is_show=True
            ),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title="", is_show=False),
            legend_opts=opts.LegendOpts(
                orient="vertical",
                pos_left="left",
                is_show=True
            ),
        )
        .set_series_opts(
            label_opts=opts.LabelOpts(
                formatter="{b}: {c} ({d}%)",
                position="outside",
                is_show=True
            ),
        )
    )
    
    return pie

def main():
    # 加载数据
    df = load_data()
    if df is None:
        return
    
    # 创建各个图表
    overview_html, trend_chart = create_left_panel(df)
    map_chart = create_map_chart(df)
    recovery_chart, death_chart = create_right_panel(df)
    risk_pie_chart = create_risk_pie_chart(df)
    
    # 生成HTML文件
    with open("covid_dashboard_v3.html", "w", encoding="utf-8") as f:
        f.write("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>香港疫情数据大屏</title>
            <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/map/js/china.js"></script>
            <style>
                body { margin: 0; padding: 20px; background-color: #1E1E1E; color: white; font-family: Arial, sans-serif; }
                .header { text-align: center; margin-bottom: 20px; padding: 20px; background-color: #2D2D2D; border-radius: 10px; }
                .header h1 { margin: 0; font-size: 32px; color: #FFFFFF; }
                .header p { margin: 10px 0; color: #AAAAAA; }
                .container { display: flex; justify-content: space-between; max-width: 1400px; margin: 0 auto; }
                .panel { background-color: #2D2D2D; border-radius: 10px; padding: 20px; margin: 10px; }
                .left-panel { width: 400px; }
                .center-panel { width: 600px; }
                .right-panel { width: 400px; display: flex; flex-direction: column; }
                .overview-container { display: flex; flex-direction: column; gap: 15px; margin-bottom: 20px; }
                .overview-item { background-color: #3D3D3D; padding: 15px; border-radius: 8px; text-align: center; }
                .overview-title { font-size: 16px; color: #AAAAAA; margin-bottom: 5px; }
                .overview-value { font-size: 24px; font-weight: bold; color: #FFFFFF; }
                .chart { width: 100%; height: 300px; }
                .chart-container { margin-bottom: 20px; height: 300px; }
                .chart-title { font-size: 18px; color: #FFFFFF; margin-bottom: 10px; text-align: center; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>香港疫情数据大屏</h1>
                <p>数据更新时间：""" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
            </div>
            <div class="container">
                <div class="panel left-panel">
                    """ + overview_html + """
                    <div class="chart-title">每日新增与累计确诊趋势</div>
                    <div id="trend_chart" class="chart"></div>
                </div>
                <div class="panel center-panel">
                    <div class="chart-title">香港各区疫情分布</div>
                    <div id="map_chart" class="chart"></div>
                    <div class="chart-title">各区风险等级分布</div>
                    <div id="risk_pie_chart" class="chart"></div>
                </div>
                <div class="panel right-panel">
                    <div class="chart-container">
                        <div class="chart-title">康复趋势分析</div>
                        <div id="recovery_chart" class="chart"></div>
                    </div>
                    <div class="chart-container">
                        <div class="chart-title">死亡趋势分析</div>
                        <div id="death_chart" class="chart"></div>
                    </div>
                </div>
            </div>
        """)
        
        # 添加图表配置
        f.write(trend_chart.render_embed())
        f.write(map_chart.render_embed())
        f.write(recovery_chart.render_embed())
        f.write(death_chart.render_embed())
        f.write(risk_pie_chart.render_embed())
        
        f.write("""
        </body>
        </html>
        """)

if __name__ == "__main__":
    main() 