import json
import pandas as pd
import folium

def load_geojson():
    """加载香港地理数据"""
    with open('hongkong.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def load_covid_data():
    """加载疫情数据"""
    df = pd.read_excel('香港各区疫情数据_20250322.xlsx')
    # 获取最新日期的数据
    latest_date = df['报告日期'].max()
    latest_data = df[df['报告日期'] == latest_date]
    return latest_data

def create_simple_map(geojson_data, covid_data):
    """创建简化的疫情地图"""
    # 创建香港中心位置的地图
    hk_center = [22.3193, 114.1694]  # 香港大致中心坐标
    m = folium.Map(location=hk_center, zoom_start=11)

    # 创建疫情数据字典
    covid_dict = dict(zip(covid_data['地区名称'], covid_data['现存确诊']))

    # 添加区域边界和疫情数据
    for feature in geojson_data['features']:
        district = feature['properties']['name']
        if district in covid_dict:
            cases = covid_dict[district]
            # 根据病例数设置颜色
            if cases > 100:
                color = '#ff0000'  # 红色
            elif cases > 50:
                color = '#ff6600'  # 橙色
            elif cases > 20:
                color = '#ffff00'  # 黄色
            else:
                color = '#00ff00'  # 绿色

            # 添加区域
            folium.GeoJson(
                feature,
                style_function=lambda x, color=color: {
                    'fillColor': color,
                    'color': 'black',
                    'weight': 1,
                    'fillOpacity': 0.5
                },
                tooltip=f'{district}: {cases}例现存确诊'
            ).add_to(m)

    # 添加图例
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 150px; height: 90px; 
                border:2px solid grey; z-index:9999; background-color:white;
                padding: 10px;
                font-size: 14px;">
        <p><i style="background: #ff0000; width: 20px; height: 20px; display: inline-block;"></i> >100例</p>
        <p><i style="background: #ff6600; width: 20px; height: 20px; display: inline-block;"></i> 50-100例</p>
        <p><i style="background: #ffff00; width: 20px; height: 20px; display: inline-block;"></i> 20-50例</p>
        <p><i style="background: #00ff00; width: 20px; height: 20px; display: inline-block;"></i> <20例</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

def main():
    print("开始处理数据...")
    
    # 加载数据
    geojson_data = load_geojson()
    covid_data = load_covid_data()
    
    print("开始创建地图...")
    # 创建地图
    m = create_simple_map(geojson_data, covid_data)
    
    # 保存地图
    m.save('hk_covid_map.html')
    print("地图已生成，请查看 hk_covid_map.html")

if __name__ == "__main__":
    main() 