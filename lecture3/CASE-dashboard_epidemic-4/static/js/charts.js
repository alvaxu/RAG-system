// 初始化所有图表
let trendChart = echarts.init(document.getElementById('trend-chart'));
let growthRateChart = echarts.init(document.getElementById('growth-rate-chart'));
let mapChart = echarts.init(document.getElementById('map-chart'));
let riskChart = echarts.init(document.getElementById('risk-chart'));
let recoveryChart = echarts.init(document.getElementById('recovery-chart'));
let deathChart = echarts.init(document.getElementById('death-chart'));

// 窗口大小改变时重绘图表
window.addEventListener('resize', function() {
    trendChart.resize();
    growthRateChart.resize();
    mapChart.resize();
    riskChart.resize();
    recoveryChart.resize();
    deathChart.resize();
});

// 更新概览数据
function updateOverview(data) {
    document.getElementById('total-confirmed').textContent = data.total_confirmed.toLocaleString();
    document.getElementById('new-confirmed').textContent = data.new_confirmed.toLocaleString();
    document.getElementById('total-recovered').textContent = data.total_recovered.toLocaleString();
    document.getElementById('new-recovered').textContent = data.new_recovered.toLocaleString();
    document.getElementById('total-deaths').textContent = data.total_deaths.toLocaleString();
    document.getElementById('new-deaths').textContent = data.new_deaths.toLocaleString();
    document.getElementById('update-time').textContent = data.update_time;
}

// 更新趋势图
function updateTrendChart(data) {
    const option = {
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross'
            }
        },
        legend: {
            data: ['新增确诊', '累计确诊'],
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
            boundaryGap: false,
            data: data.dates,
            axisLabel: {
                color: '#fff',
                rotate: 45
            }
        },
        yAxis: [
            {
                type: 'value',
                name: '新增确诊数',
                axisLabel: {
                    formatter: '{value} 例',
                    color: '#fff'
                }
            },
            {
                type: 'value',
                name: '累计确诊数',
                axisLabel: {
                    formatter: '{value} 例',
                    color: '#fff'
                }
            }
        ],
        series: [
            {
                name: '新增确诊',
                type: 'line',
                data: data.new_confirmed,
                itemStyle: {
                    color: '#FF6B6B'
                }
            },
            {
                name: '累计确诊',
                type: 'line',
                yAxisIndex: 1,
                data: data.total_confirmed,
                itemStyle: {
                    color: '#4ECDC4'
                }
            }
        ]
    };
    trendChart.setOption(option);
    document.getElementById('trend-chart').textContent = ''; // 清除占位符
}

// 更新增长率图表
function updateGrowthRateChart(data) {
    const option = {
        tooltip: {
            trigger: 'axis',
            formatter: '{b}<br/>{a}: {c}%'
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            boundaryGap: false,
            data: data.dates,
            axisLabel: {
                color: '#fff',
                rotate: 45
            }
        },
        yAxis: {
            type: 'value',
            name: '增长率',
            axisLabel: {
                formatter: '{value}%',
                color: '#fff'
            }
        },
        series: [{
            name: '增长率',
            type: 'line',
            data: data.growth_rate,
            itemStyle: {
                color: '#FFD700'
            },
            areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: 'rgba(255, 215, 0, 0.3)' },
                    { offset: 1, color: 'rgba(255, 215, 0, 0.1)' }
                ])
            }
        }]
    };
    growthRateChart.setOption(option);
    document.getElementById('growth-rate-chart').textContent = ''; // 清除占位符
}

// 获取风险等级对应的颜色
function getRiskColor(level) {
    const colors = {
        '高风险': '#FF0000',
        '中风险': '#FFA500',
        '低风险': '#00FF00'
    };
    return colors[level] || '#999';
}

// 更新风险等级饼图
function updateRiskChart(data) {
    const option = {
        tooltip: {
            trigger: 'item',
            formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
            orient: 'vertical',
            left: 'left',
            textStyle: {
                color: '#fff'
            }
        },
        series: [{
            name: '风险等级分布',
            type: 'pie',
            radius: ['30%', '70%'],
            avoidLabelOverlap: false,
            itemStyle: {
                borderRadius: 10,
                borderColor: '#fff',
                borderWidth: 2
            },
            label: {
                show: true,
                position: 'outside',
                formatter: '{b}: {c} ({d}%)',
                color: '#fff'
            },
            emphasis: {
                label: {
                    show: true,
                    fontSize: '20',
                    fontWeight: 'bold'
                }
            },
            labelLine: {
                show: true
            },
            data: data.map(item => ({
                name: item.name,
                value: item.value,
                itemStyle: {
                    color: getRiskColor(item.name)
                }
            }))
        }]
    };
    riskChart.setOption(option);
    document.getElementById('risk-chart').textContent = ''; // 清除占位符
}

// 更新康复趋势图
function updateRecoveryChart(data) {
    const option = {
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross'
            }
        },
        legend: {
            data: ['新增康复', '累计康复'],
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
            boundaryGap: false,
            data: data.dates,
            axisLabel: {
                color: '#fff',
                rotate: 45
            }
        },
        yAxis: {
            type: 'value',
            name: '康复人数',
            axisLabel: {
                formatter: '{value} 例',
                color: '#fff'
            }
        },
        series: [
            {
                name: '新增康复',
                type: 'line',
                data: data.new_recovered,
                itemStyle: {
                    color: '#00C853'
                },
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: 'rgba(0, 200, 83, 0.3)' },
                        { offset: 1, color: 'rgba(0, 200, 83, 0.1)' }
                    ])
                }
            },
            {
                name: '累计康复',
                type: 'line',
                data: data.total_recovered,
                itemStyle: {
                    color: '#69F0AE'
                }
            }
        ]
    };
    recoveryChart.setOption(option);
    document.getElementById('recovery-chart').textContent = ''; // 清除占位符
}

// 更新死亡趋势图
function updateDeathChart(data) {
    const option = {
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross'
            }
        },
        legend: {
            data: ['新增死亡', '累计死亡'],
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
            boundaryGap: false,
            data: data.dates,
            axisLabel: {
                color: '#fff',
                rotate: 45
            }
        },
        yAxis: {
            type: 'value',
            name: '死亡人数',
            axisLabel: {
                formatter: '{value} 例',
                color: '#fff'
            }
        },
        series: [
            {
                name: '新增死亡',
                type: 'line',
                data: data.new_deaths,
                itemStyle: {
                    color: '#FF1744'
                },
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: 'rgba(255, 23, 68, 0.3)' },
                        { offset: 1, color: 'rgba(255, 23, 68, 0.1)' }
                    ])
                }
            },
            {
                name: '累计死亡',
                type: 'line',
                data: data.total_deaths,
                itemStyle: {
                    color: '#D50000'
                }
            }
        ]
    };
    deathChart.setOption(option);
    document.getElementById('death-chart').textContent = ''; // 清除占位符
}

// 获取数据并更新图表
async function fetchData() {
    try {
        const [overview, trend, risk, growth] = await Promise.all([
            fetch('/api/overview').then(res => res.json()),
            fetch('/api/trend').then(res => res.json()),
            fetch('/api/risk').then(res => res.json()),
            fetch('/api/growth_rate').then(res => res.json())
        ]);

        updateOverview(overview);
        updateTrendChart(trend);
        updateGrowthRateChart(growth);
        updateRiskChart(risk);
        updateRecoveryChart(trend);
        updateDeathChart(trend);
    } catch (error) {
        console.error('数据获取失败:', error);
    }
}

// 初始加载数据
fetchData();

// 每5分钟更新一次数据
setInterval(fetchData, 5 * 60 * 1000); 