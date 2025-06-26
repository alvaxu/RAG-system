import os
import asyncio
import requests
from typing import Optional
import dashscope
from qwen_agent.agents import Assistant
from qwen_agent.gui import WebUI
import pandas as pd
from sqlalchemy import create_engine
from qwen_agent.tools.base import BaseTool, register_tool

# 定义资源文件根目录
ROOT_RESOURCE = os.path.join(os.path.dirname(__file__), 'resource')

# 配置 DashScope
dashscope.api_key = os.getenv('DASHSCOPE_API_KEY', '')  # 从环境变量获取 API Key
dashscope.timeout = 30  # 设置超时时间为 30 秒


# 定义工具描述，用于通义千问助手理解工具的功能和参数
# '''
# 1. 这个 `functions_desc` 变量定义了一个工具的描述信息，包括：
#    - 工具名称
#    - 功能描述
#    - 参数定义
#    - 必填参数列表

# 2. 在实际使用中，这些信息已经被整合到了 `WeatherTool` 类中：
#    ```python
#    @register_tool('get_current_weather')
#    class WeatherTool(BaseTool):
#        description = '获取指定位置的当前天气情况'
#        parameters = [{
#            'name': 'location',
#            'type': 'string',
#            'description': '城市名称，例如：北京',
#            'required': True
#        }, {
#            'name': 'adcode',
#            'type': 'string',
#            'description': '城市编码，例如：110000（北京）',
#            'required': False
#        }]
#    ```

# 3. 当使用 `@register_tool` 装饰器注册 `WeatherTool` 类时，这些信息已经被包含在类的定义中，所以 `functions_desc` 变量是多余的。

# 建议：
# 1. 可以安全地删除 `functions_desc` 变量，因为它没有被使用
# 2. 如果需要定义工具描述，直接使用 `WeatherTool` 类中的定义就足够了
# 3. 这种重复定义可能会造成维护困难，因为需要同时维护两处相似的代码

# '''

# functions_desc = [
#     {
#         "name": "get_current_weather",  # 工具名称
#         "description": "获取指定位置的当前天气情况",  # 工具功能描述
#         "parameters": {
#             "type": "object",  # 参数类型为对象
#             "properties": {
#                 "location": {  # 城市名称参数
#                     "type": "string",
#                     "description": "城市名称，例如：北京",
#                 },
#                 "adcode": {  # 城市编码参数
#                     "type": "string",
#                     "description": "城市编码，例如：110000（北京）",
#                 }
#             },
#             "required": ["location"],  # 必填参数列表
#         },
#     }
# ]

# ====== 天气查询工具实现 ======
@register_tool('get_current_weather')  # 注册工具，使其可被通义千问助手调用
class WeatherTool(BaseTool):
    """
    天气查询工具，通过高德地图API查询指定位置的天气情况。
    """
    description = '获取指定位置的当前天气情况'  # 工具描述
    parameters = [{  # 工具参数定义
        'name': 'location',  # 参数名称
        'type': 'string',  # 参数类型
        'description': '城市名称，例如：北京',  # 参数描述
        'required': True  # 是否必填
    }, {
        'name': 'adcode',  # 参数名称
        'type': 'string',  # 参数类型
        'description': '城市编码，例如：110000（北京）',  # 参数描述
        'required': False  # 是否必填
    }]

    def call(self, params: str, **kwargs) -> str:
        """
        工具的主要调用方法，由通义千问助手框架调用
        :param params: JSON格式的参数字符串
        :param kwargs: 其他可选参数
        :return: 天气信息的字符串
        """
        import json
        args = json.loads(params)  # 解析JSON参数字符串
        location = args['location']  # 获取城市名称
        adcode = args.get('adcode', None)  # 获取城市编码（可选）
        
        return self.get_weather_from_gaode(location, adcode)  # 调用天气查询方法
    
    def get_weather_from_gaode(self, location: str, adcode: str = None) -> str:
        """
        调用高德地图API查询天气
        :param location: 城市名称
        :param adcode: 城市编码（可选）
        :return: 格式化的天气信息字符串
        """
        gaode_api_key = "96e6841038817fab25821697f44d15c8"  # 高德API Key
        base_url = "https://restapi.amap.com/v3/weather/weatherInfo"  # API接口地址
        
        params = {
            "key": gaode_api_key,  # API密钥
            "city": adcode if adcode else location,  # 优先使用城市编码
            "extensions": "base",  # 查询类型：base为实时天气，all为天气预报
        }
        
        try:
            response = requests.get(base_url, params=params)  # 发送GET请求
            if response.status_code == 200:  # 请求成功
                data = response.json()  # 解析JSON响应
                if data.get('status') == '1' and data.get('lives'):  # 数据获取成功
                    weather_info = data['lives'][0]  # 获取天气信息
                    # 格式化天气信息
                    result = f"天气查询结果：\n城市：{weather_info.get('city')}\n天气：{weather_info.get('weather')}\n温度：{weather_info.get('temperature')}°C\n风向：{weather_info.get('winddirection')}\n风力：{weather_info.get('windpower')}\n湿度：{weather_info.get('humidity')}%\n发布时间：{weather_info.get('reporttime')}"
                    return result
                else:
                    return f"获取天气信息失败：{data.get('info', '未知错误')}"  # 返回错误信息
            else:
                return f"请求失败：HTTP状态码 {response.status_code}"  # 返回HTTP错误
        except Exception as e:
            return f"获取天气信息出错：{str(e)}"  # 返回异常信息

# ====== 初始化助手服务 ======
def init_agent_service():
    """初始化助手服务"""
    llm_cfg = {
        'model': 'qwen-turbo-2025-04-28',
        'timeout': 30,
        'retry_count': 3,
    }
    try:
        bot = Assistant(
            llm=llm_cfg,
            name='天气助手',
            description='天气助手，查询天气',
            system_message="你是一名有用的助手",
            function_list=['get_current_weather'],  # 增加天气工具
        )
        print("助手初始化成功！")
        return bot
    except Exception as e:
        print(f"助手初始化失败: {str(e)}")
        raise

def app_tui():
    """终端交互模式
    
    提供命令行交互界面，支持：
    - 连续对话
    - 文件输入
    - 实时响应
    """
    try:
        # 初始化助手
        bot = init_agent_service()

        # 对话历史
        messages = []
        while True:
            try:
                # 获取用户输入
                query = input('user question: ')
                # 获取可选的文件输入
                file = input('file url (press enter if no file): ').strip()
                
                # 输入验证
                if not query:
                    print('user question cannot be empty！')
                    continue
                    
                # 构建消息
                if not file:
                    messages.append({'role': 'user', 'content': query})
                else:
                    messages.append({'role': 'user', 'content': [{'text': query}, {'file': file}]})

                print("正在处理您的请求...")
                # 运行助手并处理响应
                response = []
                for response in bot.run(messages):
                    print('bot response:', response)
                messages.extend(response)
            except Exception as e:
                print(f"处理请求时出错: {str(e)}")
                print("请重试或输入新的问题")
    except Exception as e:
        print(f"启动终端模式失败: {str(e)}")


def app_gui():
    """图形界面模式，提供 Web 图形界面"""
    try:
        print("正在启动 Web 界面...")
        # 初始化助手
        bot = init_agent_service()
        # 配置聊天界面，列举3个典型门票查询问题
        chatbot_config = {
            'prompt.suggestions': [
                '北京今天的天气怎么样？',
            ]
        }
        print("Web 界面准备就绪，正在启动服务...")
        # 启动 Web 界面
        WebUI(
            bot,
            chatbot_config=chatbot_config
        ).run()
    except Exception as e:
        print(f"启动 Web 界面失败: {str(e)}")
        print("请检查网络连接和 API Key 配置")


if __name__ == '__main__':
    # 运行模式选择
    app_gui()          # 图形界面模式（默认）