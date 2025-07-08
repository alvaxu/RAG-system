# 客户经营分析可视化图表方案

## 一、客户转化漏斗图

### 1. 生命周期转化漏斗
```javascript
// 漏斗图示例
{
    title: {
        text: '客户生命周期转化漏斗'
    },
    tooltip: {
        trigger: 'item',
        formatter: '{b}: {c}人 ({d}%)'
    },
    series: [{
        type: 'funnel',
        data: [
            {value: 100000, name: '潜在客户'},
            {value: 80000, name: '新客户'},
            {value: 60000, name: '成长客户'},
            {value: 40000, name: '成熟客户'},
            {value: 20000, name: '忠诚客户'}
        ],
        label: {
            show: true,
            position: 'inside',
            formatter: '{b}: {c}人'
        }
    }]
}
```

### 2. 营销转化漏斗
```javascript
{
    title: {
        text: '营销活动转化漏斗'
    },
    series: [{
        type: 'funnel',
        data: [
            {value: 50000, name: '营销触达'},
            {value: 30000, name: '成功接触'},
            {value: 20000, name: '产品咨询'},
            {value: 10000, name: '达成交易'}
        ]
    }]
}
```

## 二、客户分布图表

### 1. 资产分布饼图
```javascript
{
    title: {
        text: '客户资产等级分布'
    },
    series: [{
        type: 'pie',
        radius: ['50%', '70%'],  // 环形图
        data: [
            {value: 30, name: '高净值'},
            {value: 40, name: '中产阶级'},
            {value: 30, name: '普通客户'}
        ]
    }]
}
```

### 2. 年龄分布条形图
```javascript
{
    title: {
        text: '客户年龄分布'
    },
    xAxis: {
        type: 'category',
        data: ['18-25岁', '26-35岁', '36-45岁', '46-55岁', '56岁以上']
    },
    yAxis: {
        type: 'value'
    },
    series: [{
        type: 'bar',
        data: [5000, 15000, 20000, 18000, 8000]
    }]
}
```

## 三、趋势分析图表

### 1. 资产趋势折线图
```javascript
{
    title: {
        text: '客户资产趋势分析'
    },
    xAxis: {
        type: 'category',
        data: ['1月', '2月', '3月', '4月', '5月', '6月']
    },
    yAxis: {
        type: 'value'
    },
    series: [{
        type: 'line',
        data: [150, 230, 224, 218, 135, 147]
    }]
}
```

### 2. 产品持有堆叠图
```javascript
{
    title: {
        text: '产品持有情况分析'
    },
    xAxis: {
        type: 'category',
        data: ['Q1', 'Q2', 'Q3', 'Q4']
    },
    yAxis: {
        type: 'value'
    },
    series: [
        {
            name: '存款',
            type: 'bar',
            stack: 'total',
            data: [320, 302, 301, 334]
        },
        {
            name: '理财',
            type: 'bar',
            stack: 'total',
            data: [120, 132, 101, 134]
        },
        {
            name: '基金',
            type: 'bar',
            stack: 'total',
            data: [220, 182, 191, 234]
        }
    ]
}
```

## 四、关系分析图表

### 1. 年龄-资产散点图
```javascript
{
    title: {
        text: '年龄与资产关系分析'
    },
    xAxis: {
        type: 'value',
        name: '年龄'
    },
    yAxis: {
        type: 'value',
        name: '资产'
    },
    series: [{
        type: 'scatter',
        data: [[25, 100000], [35, 200000], [45, 300000]]
    }]
}
```

### 2. 产品关联桑基图
```javascript
{
    title: {
        text: '产品购买路径分析'
    },
    series: [{
        type: 'sankey',
        data: [
            {name: '存款'},
            {name: '理财'},
            {name: '基金'}
        ],
        links: [
            {source: '存款', target: '理财', value: 5},
            {source: '理财', target: '基金', value: 3}
        ]
    }]
}
```

## 五、地理分布图表

### 1. 城市分布地图
```javascript
{
    title: {
        text: '客户地理分布'
    },
    series: [{
        type: 'map',
        map: 'china',
        data: [
            {name: '北京', value: 5000},
            {name: '上海', value: 4000},
            {name: '广州', value: 3000}
        ]
    }]
}
```

## 六、营销效果图表

### 1. 营销效果仪表盘
```javascript
{
    title: {
        text: '营销转化率'
    },
    series: [{
        type: 'gauge',
        data: [{value: 50, name: '转化率'}],
        min: 0,
        max: 100,
        detail: {formatter: '{value}%'}
    }]
}
```

### 2. APP行为热力图
```javascript
{
    title: {
        text: 'APP使用时间分布'
    },
    series: [{
        type: 'heatmap',
        data: [[0, 0, 5], [0, 1, 7], [0, 2, 3]],
        label: {
            show: true
        }
    }]
}
```

## 七、交互设计建议

1. **图表联动**
   - 点击饼图扇区，联动显示该类客户的详细信息
   - 选择时间范围，所有图表同步更新

2. **数据钻取**
   - 支持从总体到局部的层层钻取
   - 双击数据点查看详情

3. **动态更新**
   - 关键指标实时刷新
   - 支持数据动态加载

4. **响应式设计**
   - 图表自适应容器大小
   - 移动端优化展示 