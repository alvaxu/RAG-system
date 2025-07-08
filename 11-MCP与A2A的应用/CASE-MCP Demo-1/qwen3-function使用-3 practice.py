import requests
from http import HTTPStatus
import dashscope
import os

# 设置 DashScope API Key，从环境变量获取API密钥
dashscope.api_key = os.getenv('DASHSCOPE_API_KEY', '')  # 从环境变量获取 API Key

# 定义工具接口规范（JSON格式）
tools = [
    {
        "type": "function",  # 指定这是一个函数类型的工具
        "function": {
            "name": "get_current_weather",  # 工具名称
            "description": "Get the current weather in a given location",  # 工具描述
            "parameters": {
                "type": "object",  # 参数类型为对象
                "properties": {
                    "location": {  # 城市名称参数
                        "type": "string",
                        "description": "The city name, e.g. 北京",
                    },
                    "adcode": {  # 城市编码参数
                        "type": "string",
                        "description": "The city code, e.g. 110000 (北京)",
                    }
                },
                "required": ["location"],  # 指定必填参数
            },
        },
    },
    {
        "type": "function",  # 指定这是一个函数类型的工具
        "function": {
            "name": "get_ip_location",  # 工具名称
            "description": "Get the geographical location information of an IP address",  # 工具描述
            "parameters": {
                "type": "object",  # 参数类型为对象
                "properties": {
                    "ip": {  # IP地址参数
                        "type": "string",
                        "description": "The IP address to query, e.g. 114.247.50.2",
                    }
                },
                "required": ["ip"],  # 指定必填参数
            },
        },
    }
]

def get_weather_from_gaode(location: str, adcode: str = None):
    """
    调用高德地图API查询天气
    :param location: 城市名称
    :param adcode: 城市编码（可选）
    :return: 天气信息的JSON数据
    """
    gaode_api_key = "96e6841038817fab25821697f44d15c8"  # 高德API Key
    base_url = "https://restapi.amap.com/v3/weather/weatherInfo"  # API接口地址
    
    # 构建请求参数
    params = {
        "key": gaode_api_key,  # API密钥
        "city": adcode if adcode else location,  # 优先使用城市编码
        "extensions": "base",  # 查询类型：base为实时天气，all为天气预报
    }
    
    # 发送GET请求并处理响应
    response = requests.get(base_url, params=params)
    if response.status_code == 200:  # 请求成功
        return response.json()  # 返回JSON格式的天气数据
    else:
        return {"error": f"Failed to fetch weather: {response.status_code}"}  # 返回错误信息

def get_ip_location(ip: str):
    """
    调用高德地图API查询IP地址的地理位置
    :param ip: IP地址
    :return: 地理位置信息的JSON数据
    """
    gaode_api_key = "96e6841038817fab25821697f44d15c8"  # 高德API Key
    base_url = "https://restapi.amap.com/v3/ip"  # API接口地址
    
    # 构建请求参数
    params = {
        "key": gaode_api_key,  # API密钥
        "ip": ip,  # IP地址
    }
    
    # 发送GET请求并处理响应
    response = requests.get(base_url, params=params)
    if response.status_code == 200:  # 请求成功
        return response.json()  # 返回JSON格式的地理位置数据
    else:
        return {"error": f"Failed to fetch IP location: {response.status_code}"}  # 返回错误信息

def run_query():
    """
    使用通义千问模型查询天气和IP地理位置，并生成自然语言响应
    实现完整的对话流程：
    1. 初始化对话
    2. 调用模型
    3. 处理工具调用
    4. 生成最终响应
    """
    # 初始化对话上下文
    messages = [
        {"role": "system", "content": "你是一个智能助手，可以查询天气信息，也可以查询IP地址的地理定位。"},  # 系统提示
        # {"role": "user", "content": "北京现在天气怎么样？"}  # 用户问题
        # {"role": "user", "content": "114.247.50.2的IP地址在哪个城市？"}  # 用户问题
        # {"role": "user", "content": "114.247.50.2的IP地址所在城市的天气情况怎样？"}  # 用户问题

    ]
    
    print("第一次调用大模型...")
    # 第一次调用通义千问模型
    response = dashscope.Generation.call(
        model="qwen-turbo",  # 使用通义千问模型
        messages=messages,  # 传入对话历史
        tools=tools,  # 传入工具定义
        tool_choice="auto",  # 让模型自动决定是否调用工具
    )
    
    if response.status_code == HTTPStatus.OK:  # 请求成功
        # 定义工具映射表
        tool_map = {
            "get_current_weather": get_weather_from_gaode,  # 映射天气查询函数
            "get_ip_location": get_ip_location,  # 映射IP地理位置查询函数
        }
        
        # 获取助手回复
        assistant_message = response.output.choices[0].message
        
        # 检查是否需要调用工具
        if hasattr(assistant_message, "tool_calls") and assistant_message.tool_calls:
            print("检测到工具调用...")
            
            # 转换助手消息为标准字典格式
            assistant_dict = {
                "role": "assistant",
                "content": assistant_message.content if hasattr(assistant_message, "content") else None
            }
            
            # 处理工具调用
            if hasattr(assistant_message, "tool_calls"):
                assistant_dict["tool_calls"] = assistant_message.tool_calls
                
                # 处理每个工具调用
                tool_response_messages = []
                import json
                for tool_call in assistant_message.tool_calls:
                    print(f"处理工具调用: {tool_call['function']['name']}, ID: {tool_call['id']}, Args: {tool_call['function']['arguments']}")
                    
                    # 获取函数名和参数
                    func_name = tool_call["function"]["name"]
                    func_args = json.loads(tool_call["function"]["arguments"])
                    
                    if func_name in tool_map:
                        # 调用对应的工具函数
                        from inspect import signature
                        sig = signature(tool_map[func_name])
                        # 过滤有效参数
                        valid_args = {k: v for k, v in func_args.items() if k in sig.parameters}
                        print(f"有效参数: {valid_args}")
                        result = tool_map[func_name](**valid_args)
                        
                        # 创建工具调用响应消息
                        tool_response = {
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "name": func_name,
                            "content": json.dumps(result, ensure_ascii=False)
                        }
                        tool_response_messages.append(tool_response)
                
                # 组装完整的消息列表
                updated_messages = messages + [assistant_dict] + tool_response_messages
                
                print(f"完整消息列表: {updated_messages}")
                
                # 第二次调用大模型生成最终响应
                print("第二次调用大模型...")
                response2 = dashscope.Generation.call(
                    model="qwen-turbo",
                    messages=updated_messages,
                    tools=tools,
                    tool_choice="auto",
                )
                
                if response2.status_code == HTTPStatus.OK:
                    final_response = response2.output.choices[0].message.content
                    print("最终回复:", final_response)
                else:
                    print(f"请求失败: {response2.code} - {response2.message}")
            else:
                print("assistant 消息中没有 tool_calls 字段")
                print(assistant_message)
        else:
            # 如果没有工具调用，直接输出模型回复
            print("无工具调用，直接输出回复:", assistant_message.content)
    else:
        print(f"请求失败: {response.code} - {response.message}")

if __name__ == "__main__":
    run_query()  # 运行查询程序 