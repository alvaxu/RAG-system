// 初始化所有图表
let trendChart, districtChart, recoveryChart, deathChart, hkMap;
let currentDistrict = 'all';

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initCharts();
    loadData();
    setupEventListeners();
});

// 初始化所有图表
function initCharts() {
    // 设置图表主题
    const chartTheme = {
        backgroundColor: 'transparent',
        textStyle: {
            color: '#fff'
        },
        title: {
            textStyle: {
                color: '#fff'
            }
        },
        legend: {
            textStyle: {
                color: '#fff'
            }
        },
        xAxis: {
            axisLine: {
                lineStyle: {
                    color: '#fff'
                }
            },
            axisLabel: {
                color: '#fff'
            }
        },
        yAxis: {
            axisLine: {
                lineStyle: {
                    color: '#fff'
                }
            },
            axisLabel: {
                color: '#fff'
            }
        }
    };

    // 趋势图
    trendChart = echarts.init(document.getElementById('trendChart'));
    trendChart.setOption(chartTheme);

    // 地区对比图
    districtChart = echarts.init(document.getElementById('districtChart'));
    districtChart.setOption(chartTheme);

    // 康复率图
    recoveryChart = echarts.init(document.getElementById('recoveryChart'));
    recoveryChart.setOption(chartTheme);

    // 死亡率图
    deathChart = echarts.init(document.getElementById('deathChart'));
    deathChart.setOption(chartTheme);

    // 地图
    hkMap = echarts.init(document.getElementById('hkMap'));
    hkMap.setOption(chartTheme);
    
    // 窗口大小改变时重绘图表
    window.addEventListener('resize', function() {
        trendChart.resize();
        districtChart.resize();
        recoveryChart.resize();
        deathChart.resize();
        hkMap.resize();
    });
}

// 设置事件监听器
function setupEventListeners() {
    // 地区选择
    document.getElementById('districtSelect').addEventListener('change', function(e) {
        currentDistrict = e.target.value;
        // 更新图表标题
        const chartTitles = {
            'trendChart': document.querySelector('.left-panel .chart-container:first-child h3'),
            'recoveryChart': document.querySelector('.right-panel .chart-container:first-child h3'),
            'deathChart': document.querySelector('.right-panel .chart-container:last-child h3')
        };
        
        const districtText = currentDistrict === 'all' ? '全部地区' : currentDistrict;
        chartTitles.trendChart.textContent = `${districtText}疫情趋势`;
        chartTitles.recoveryChart.textContent = `${districtText}康复趋势`;
        chartTitles.deathChart.textContent = `${districtText}死亡趋势`;
        
        loadData();
    });
    
    // 导出数据按钮
    document.getElementById('exportData').addEventListener('click', exportData);
}

// 处理API请求
async function fetchAPI(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        if (data.error) {
            throw new Error(data.error);
        }
        return data;
    } catch (error) {
        console.error(`请求失败: ${url}`, error);
        showError(`数据加载失败: ${error.message}`);
        return null;
    }
}

// 加载所有数据
async function loadData() {
    // 显示加载状态
    document.body.classList.add('loading');
    
    try {
        // 加载总体数据
        const summaryData = await fetchAPI('/api/summary');
        if (summaryData) updateSummary(summaryData);
        
        // 加载趋势数据
        const trendData = await fetchAPI(`/api/trend?district=${currentDistrict}`);
        if (trendData) {
            updateTrendChart(trendData);
            updateRecoveryChart(trendData);
            updateDeathChart(trendData);
        }
        
        // 加载地区对比数据
        const districtData = await fetchAPI('/api/district_comparison');
        if (districtData) {
            updateDistrictChart(districtData);
            // 更新地区选择器选项
            const districtSelect = document.getElementById('districtSelect');
            if (districtSelect.options.length <= 1) {
                districtData.districts.forEach(district => {
                    const option = document.createElement('option');
                    option.value = district;
                    option.textContent = district;
                    districtSelect.appendChild(option);
                });
            }
        }
        
        // 加载地图数据
        const mapData = await fetchAPI('/api/map');
        if (mapData) updateMap(mapData);
        
    } catch (error) {
        console.error('数据加载失败:', error);
        showError('数据加载失败，请刷新页面重试');
    } finally {
        // 移除加载状态
        document.body.classList.remove('loading');
    }
}

// 更新总体数据
function updateSummary(data) {
    if (!data) return;
    
    document.getElementById('totalConfirmed').textContent = data.total_confirmed.toLocaleString();
    document.getElementById('newConfirmed').textContent = data.new_confirmed.toLocaleString();
    document.getElementById('totalRecovered').textContent = data.total_recovered.toLocaleString();
    document.getElementById('newRecovered').textContent = data.new_recovered.toLocaleString();
    document.getElementById('totalDeaths').textContent = data.total_deaths.toLocaleString();
    document.getElementById('newDeaths').textContent = data.new_deaths.toLocaleString();
    document.getElementById('updateTime').textContent = data.update_time;
}

// 更新趋势图
function updateTrendChart(data) {
    if (!data) return;
    
    const option = {
        title: {
            text: '疫情趋势',
            textStyle: {
                color: '#fff'
            }
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross'
            },
            backgroundColor: 'rgba(0,0,0,0.7)',
            borderColor: '#ccc',
            textStyle: {
                color: '#fff'
            },
            formatter: function(params) {
                let result = params[0].axisValue + '<br/>';
                params.forEach(param => {
                    const value = param.value.toLocaleString();
                    result += `${param.marker} ${param.seriesName}: ${value}<br/>`;
                });
                return result;
            }
        },
        legend: {
            data: ['每日新增确诊', '累计确诊'],
            textStyle: {
                color: '#fff'
            }
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: data.dates,
            axisLabel: {
                color: '#fff',
                rotate: 45
            }
        },
        yAxis: [
            {
                type: 'value',
                name: '新增确诊',
                position: 'left',
                axisLine: {
                    lineStyle: {
                        color: '#ff5252'
                    }
                },
                axisLabel: {
                    color: '#fff',
                    formatter: value => value.toLocaleString()
                }
            },
            {
                type: 'value',
                name: '累计确诊',
                position: 'right',
                axisLine: {
                    lineStyle: {
                        color: '#d32f2f'
                    }
                },
                axisLabel: {
                    color: '#fff',
                    formatter: value => value.toLocaleString()
                }
            }
        ],
        series: [
            {
                name: '每日新增确诊',
                type: 'bar',
                data: data.new_confirmed,
                itemStyle: {
                    color: '#ff5252'
                }
            },
            {
                name: '累计确诊',
                type: 'line',
                yAxisIndex: 1,
                smooth: true,
                data: data.total_confirmed,
                itemStyle: {
                    color: '#d32f2f'
                }
            }
        ]
    };
    trendChart.setOption(option);
}

// 更新地区对比图
function updateDistrictChart(data) {
    if (!data) return;
    
    const option = {
        title: {
            text: '地区确诊对比',
            textStyle: {
                color: '#fff'
            }
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'shadow'
            },
            backgroundColor: 'rgba(0,0,0,0.7)',
            borderColor: '#ccc',
            textStyle: {
                color: '#fff'
            }
        },
        legend: {
            data: ['累计确诊', '新增确诊'],
            textStyle: {
                color: '#fff'
            }
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: data.districts,
            axisLabel: {
                color: '#fff',
                interval: 0,
                rotate: 45
            }
        },
        yAxis: {
            type: 'value',
            axisLabel: {
                color: '#fff'
            }
        },
        series: [
            {
                name: '累计确诊',
                type: 'bar',
                data: data.confirmed,
                itemStyle: {
                    color: '#ff5252'
                }
            },
            {
                name: '新增确诊',
                type: 'bar',
                data: data.new_confirmed,
                itemStyle: {
                    color: '#ff8a80'
                }
            }
        ]
    };
    districtChart.setOption(option);
}

// 更新地图
function updateMap(data) {
    if (!data) return;
    
    // 注册地图
    echarts.registerMap('HK', data);
    
    const option = {
        title: {
            text: '香港疫情分布',
            textStyle: {
                color: '#fff'
            }
        },
        tooltip: {
            trigger: 'item',
            formatter: function(params) {
                if (!params.data) return params.name;
                return `${params.name}<br/>
                        累计确诊：${params.data.confirmed.toLocaleString()}<br/>
                        新增确诊：${params.data.new_confirmed.toLocaleString()}<br/>
                        风险等级：${getRiskLevelText(params.data.risk_level)}`;
            },
            backgroundColor: 'rgba(0,0,0,0.7)',
            borderColor: '#ccc',
            textStyle: {
                color: '#fff'
            }
        },
        visualMap: {
            min: 0,
            max: 1000,
            text: ['高', '低'],
            realtime: false,
            calculable: true,
            inRange: {
                color: ['#50a3ba', '#eac736', '#d94e5d']
            },
            textStyle: {
                color: '#fff'
            }
        },
        series: [{
            name: '香港',
            type: 'map',
            map: 'HK',
            emphasis: {
                label: {
                    show: true,
                    color: '#fff'
                }
            },
            data: data.features.map(feature => ({
                name: feature.properties.name,
                value: feature.properties.confirmed,
                confirmed: feature.properties.confirmed,
                new_confirmed: feature.properties.new_confirmed,
                risk_level: feature.properties.risk_level
            }))
        }]
    };
    hkMap.setOption(option);
}

// 获取风险等级文本
function getRiskLevelText(level) {
    const levelMap = {
        'high': '高风险',
        'medium': '中风险',
        'low': '低风险'
    };
    return levelMap[level] || '未知';
}

// 导出数据
function exportData() {
    const data = {
        summary: {
            total_confirmed: document.getElementById('totalConfirmed').textContent,
            new_confirmed: document.getElementById('newConfirmed').textContent,
            total_recovered: document.getElementById('totalRecovered').textContent,
            new_recovered: document.getElementById('newRecovered').textContent,
            total_deaths: document.getElementById('totalDeaths').textContent,
            new_deaths: document.getElementById('newDeaths').textContent,
            update_time: document.getElementById('updateTime').textContent
        }
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `hk_covid_data_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// 更新康复趋势图
function updateRecoveryChart(data) {
    if (!data) return;
    
    const option = {
        title: {
            text: '康复趋势',
            textStyle: {
                color: '#fff'
            }
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross'
            },
            backgroundColor: 'rgba(0,0,0,0.7)',
            borderColor: '#ccc',
            textStyle: {
                color: '#fff'
            },
            formatter: function(params) {
                let result = params[0].axisValue + '<br/>';
                params.forEach(param => {
                    const value = param.value.toLocaleString();
                    result += `${param.marker} ${param.seriesName}: ${value}<br/>`;
                });
                return result;
            }
        },
        legend: {
            data: ['每日新增康复', '累计康复'],
            textStyle: {
                color: '#fff'
            }
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: data.dates,
            axisLabel: {
                color: '#fff',
                rotate: 45
            }
        },
        yAxis: [
            {
                type: 'value',
                name: '新增康复',
                position: 'left',
                axisLine: {
                    lineStyle: {
                        color: '#4caf50'
                    }
                },
                axisLabel: {
                    color: '#fff',
                    formatter: value => value.toLocaleString()
                }
            },
            {
                type: 'value',
                name: '累计康复',
                position: 'right',
                axisLine: {
                    lineStyle: {
                        color: '#2e7d32'
                    }
                },
                axisLabel: {
                    color: '#fff',
                    formatter: value => value.toLocaleString()
                }
            }
        ],
        series: [
            {
                name: '每日新增康复',
                type: 'bar',
                data: data.new_recovered,
                itemStyle: {
                    color: '#4caf50'
                }
            },
            {
                name: '累计康复',
                type: 'line',
                yAxisIndex: 1,
                smooth: true,
                data: data.total_recovered,
                itemStyle: {
                    color: '#2e7d32'
                }
            }
        ]
    };
    recoveryChart.setOption(option);
}

// 更新死亡趋势图
function updateDeathChart(data) {
    if (!data) return;
    
    const option = {
        title: {
            text: '死亡趋势',
            textStyle: {
                color: '#fff'
            }
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross'
            },
            backgroundColor: 'rgba(0,0,0,0.7)',
            borderColor: '#ccc',
            textStyle: {
                color: '#fff'
            },
            formatter: function(params) {
                let result = params[0].axisValue + '<br/>';
                params.forEach(param => {
                    const value = param.value.toLocaleString();
                    result += `${param.marker} ${param.seriesName}: ${value}<br/>`;
                });
                return result;
            }
        },
        legend: {
            data: ['每日新增死亡', '累计死亡'],
            textStyle: {
                color: '#fff'
            }
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: data.dates,
            axisLabel: {
                color: '#fff',
                rotate: 45
            }
        },
        yAxis: [
            {
                type: 'value',
                name: '新增死亡',
                position: 'left',
                axisLine: {
                    lineStyle: {
                        color: '#9e9e9e'
                    }
                },
                axisLabel: {
                    color: '#fff',
                    formatter: value => value.toLocaleString()
                }
            },
            {
                type: 'value',
                name: '累计死亡',
                position: 'right',
                axisLine: {
                    lineStyle: {
                        color: '#616161'
                    }
                },
                axisLabel: {
                    color: '#fff',
                    formatter: value => value.toLocaleString()
                }
            }
        ],
        series: [
            {
                name: '每日新增死亡',
                type: 'bar',
                data: data.new_deaths,
                itemStyle: {
                    color: '#9e9e9e'
                }
            },
            {
                name: '累计死亡',
                type: 'line',
                yAxisIndex: 1,
                smooth: true,
                data: data.total_deaths,
                itemStyle: {
                    color: '#616161'
                }
            }
        ]
    };
    deathChart.setOption(option);
} 