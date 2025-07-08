import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Line, Map, Bar, Grid, Timeline
from pyecharts.globals import ThemeType
import json

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

# 2. 地理分布图
def create_map_chart(df):
    # 获取最新日期的数据
    latest_date = df['报告日期'].max()
    latest_data = df[df['报告日期'] == latest_date]
    
    # 准备地图数据
    map_data = [
        [name, value] for name, value in zip(
            latest_data['地区名称'],
            latest_data['累计确诊']
        )
    ]
    
    # 创建地图
    map_chart = (
        Map(init_opts=opts.InitOpts(
            theme=ThemeType.DARK,
            width="600px",
            height="500px",
            chart_id="map_chart"
        ))
        .add(
            "累计确诊",
            map_data,
            "香港",
            is_map_symbol_show=False,
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title="香港各区疫情分布"),
            visualmap_opts=opts.VisualMapOpts(
                max_=max(latest_data['累计确诊']),
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
    return map_chart

# 3. 增长率分析图
def create_growth_chart(df):
    # 按日期统计数据
    daily_stats = df.groupby('报告日期').agg({
        '新增确诊': 'sum',
        '累计确诊': 'max'
    }).reset_index()
    
    # 计算增长率
    daily_stats['增长率'] = daily_stats['新增确诊'].pct_change() * 100
    
    # 创建柱状图
    bar = (
        Bar(init_opts=opts.InitOpts(
            theme=ThemeType.DARK,
            width="400px",
            height="500px",
            chart_id="growth_chart"
        ))
        .add_xaxis(daily_stats['报告日期'].dt.strftime('%Y-%m-%d').tolist())
        .add_yaxis(
            "增长率",
            daily_stats['增长率'].tolist(),
            color="#FFA07A",
            label_opts=opts.LabelOpts(is_show=False),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title="每日增长率变化"),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            xaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(rotate=45),
            ),
            yaxis_opts=opts.AxisOpts(
                name="增长率(%)",
                axislabel_opts=opts.LabelOpts(formatter="{value}%"),
            ),
        )
    )
    return bar

def main():
    # 加载数据
    df = load_data()
    if df is None:
        return
    
    # 创建图表
    overview_html, trend_chart = create_left_panel(df)
    map_chart = create_map_chart(df)
    growth_chart = create_growth_chart(df)
    
    # 创建页面
    with open("covid_dashboard.html", "w", encoding="utf-8") as f:
        f.write("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>香港疫情数据大屏</title>
            <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/map/js/china.js"></script>
            <style>
                body {
                    margin: 0;
                    padding: 20px;
                    background-color: #1E1E1E;
                    color: white;
                    font-family: Arial, sans-serif;
                }
                .container {
                    display: flex;
                    justify-content: space-between;
                    max-width: 1400px;
                    margin: 0 auto;
                }
                .panel {
                    background-color: #2D2D2D;
                    border-radius: 10px;
                    padding: 20px;
                    margin: 10px;
                }
                .left-panel {
                    width: 400px;
                }
                .center-panel {
                    width: 600px;
                }
                .right-panel {
                    width: 400px;
                }
                .overview-container {
                    display: flex;
                    flex-direction: column;
                    gap: 15px;
                    margin-bottom: 20px;
                }
                .overview-item {
                    background-color: #3D3D3D;
                    padding: 15px;
                    border-radius: 8px;
                    text-align: center;
                }
                .overview-title {
                    font-size: 16px;
                    color: #AAAAAA;
                    margin-bottom: 5px;
                }
                .overview-value {
                    font-size: 24px;
                    font-weight: bold;
                    color: #FFFFFF;
                }
                .chart {
                    width: 100%;
                    height: 100%;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="panel left-panel">
                    <div class="overview-container">
        """)
        
        # 写入概览数据
        f.write(overview_html)
        
        f.write("""
                    </div>
                    <div id="trend_chart" class="chart"></div>
                </div>
                <div class="panel center-panel">
                    <div id="map_chart" class="chart"></div>
                </div>
                <div class="panel right-panel">
                    <div id="growth_chart" class="chart"></div>
                </div>
            </div>
        """)
        
        # 获取每个图表的HTML和JavaScript代码
        trend_html = trend_chart.render_embed()
        map_html = map_chart.render_embed()
        growth_html = growth_chart.render_embed()
        
        # 写入图表代码
        f.write(trend_html)
        f.write(map_html)
        f.write(growth_html)
        
        f.write("""
            </body>
        </html>
        """)
    
    print("可视化大屏已生成！请查看 covid_dashboard.html")

if __name__ == "__main__":
    main() 