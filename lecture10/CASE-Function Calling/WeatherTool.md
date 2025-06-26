# WeatherTool类详细解析

## 1. 类定义与装饰器
```python
@register_tool('get_current_weather')
class WeatherTool(BaseTool):
```
- `@register_tool`装饰器用于将WeatherTool类注册为工具，使其可以被通义千问助手调用
- 类继承自`BaseTool`基类，这是通义千问工具框架的基础类

## 2. 类属性
```python
description = '获取指定位置的当前天气情况'
```
- 定义工具的描述信息，用于在助手界面显示工具的功能说明

```python
parameters = [{
    'name': 'location',
    'type': 'string',
    'description': '城市名称，例如：北京',
    'required': True
}, {
    'name': 'adcode',
    'type': 'string',
    'description': '城市编码，例如：110000（北京）',
    'required': False
}]
```
- 定义工具的参数列表
- `location`: 必填参数，用于指定要查询天气的城市名称
- `adcode`: 可选参数，用于指定城市编码，提高查询准确性

## 3. 核心方法

### 3.1 call方法
```python
def call(self, params: str, **kwargs) -> str:
```
- 工具的主要调用方法，由通义千问助手框架调用
- 参数：
  - `params`: JSON格式的参数字符串
  - `**kwargs`: 其他可选参数
- 返回值：天气信息的字符串

实现步骤：
1. 解析JSON参数字符串
2. 提取location和adcode参数
3. 调用get_weather_from_gaode方法获取天气信息

### 3.2 get_weather_from_gaode方法
```python
def get_weather_from_gaode(self, location: str, adcode: str = None) -> str:
```
- 实际调用高德地图API获取天气信息的方法
- 参数：
  - `location`: 城市名称
  - `adcode`: 可选的城市编码
- 返回值：格式化的天气信息字符串

实现步骤：
1. 设置API请求参数
2. 发送HTTP GET请求到高德地图API
3. 解析API响应
4. 格式化天气信息
5. 错误处理和异常捕获

## 4. 天气信息格式
返回的天气信息包含以下字段：
- 城市名称
- 天气状况
- 温度（摄氏度）
- 风向
- 风力
- 湿度（百分比）
- 发布时间

## 5. 错误处理
- API请求失败处理
- 响应解析错误处理
- 网络异常处理
- 参数验证处理

## 6. 使用示例
```python
# 使用城市名称查询
weather = WeatherTool().call('{"location": "北京"}')

# 使用城市编码查询
weather = WeatherTool().call('{"location": "北京", "adcode": "110000"}')
```

## 7. 注意事项
1. 需要有效的高德地图API密钥
2. 城市名称建议使用标准名称
3. 城市编码可以提高查询准确性
4. 需要处理网络超时情况
5. API调用频率可能有限制 