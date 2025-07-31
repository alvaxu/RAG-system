import os
import json
import dashscope
from dashscope.api_entities.dashscope_response import Role

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

# 官方标准 tools 定义
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "必须通过本工具获取指定城市的天气，不能直接回答。",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "城市名，比如上海"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "温度单位，摄氏度或华氏度"
                    }
                },
                "required": ["location"]
            }
        }
    }
]

# 本地函数，参数为 dict
# def get_current_weather(arguments):
#     location = arguments.get("location", "")
#     return f"{location} 当前天气晴天，微风，气温为36摄氏度。"

# 编写你的函数
def get_current_weather(location, unit='celsius'):
    # 获取指定地点的天气
    temperature = -1
    if '大连' in location or 'Dalian' in location:
        temperature = 10
    if '上海' in location or 'Shanghai' in location:
        temperature = 36
    if '深圳' in location or 'Shenzhen' in location:
        temperature = 37
    weather_info = {
        "location": location,
        "temperature": temperature,
        "unit": unit,
        "forecast": ["晴天", "微风"],
    }
    return json.dumps(weather_info, ensure_ascii=False)

# 封装模型响应函数

def get_response(messages):
    response = dashscope.Generation.call(
        model='qwen-turbo',
        messages=messages,
        tools=tools,
        result_format='message'
    )
    return response

# 官方推荐多轮 function_call 主流程
def run_conversation():
    query = "上海的天气怎样？"
    messages=[{"role": "user", "content": query}]
    while True:
        response = get_response(messages)
        if not response or not response.output:
            print("获取响应失败")
            return
        message = response.output.choices[0].message
        print("模型输出：", message)
        messages.append(message)
        # 1. 如果无需调用工具，直接输出内容
        if not message.get("tool_calls"):
            print("最终答案：", message.get("content", ""))
            break
        # 2. 如果需要调用工具
        for tool_call in message["tool_calls"]:
            fn_name = tool_call["function"]["name"]
            fn_args = json.loads(tool_call["function"]["arguments"])
            print("调用本地函数：", fn_name, fn_args)
            # 适配新版本地函数参数
            location = fn_args.get("location", "")
            unit = fn_args.get("unit", "celsius")
            function_mapper = {
                "get_current_weather": get_current_weather
            }
            tool_response = function_mapper[fn_name](location, unit)
            tool_message = {
                "role": "tool",
                "content": tool_response,
                "tool_call_id": tool_call["id"]
            }
            print("本地函数输出：", tool_message)
            messages.append(tool_message)
        # 继续下一轮

if __name__ == "__main__":
    run_conversation()
    
    
'''

模型输出： {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "get_current_weather", "arguments": "{\"location\": \"上海\"}"}, "index": 0, "id": "call_777f5c8aed984a97985b07", "type": "function"}]}
调用本地函数： get_current_weather {'location': '上海'}
本地函数输出： {'role': 'tool', 'content': '{"location": "上海", "temperature": 36, "unit": "celsius", "forecast": ["晴天", "微风"]}', 'tool_call_id': 'call_777f5c8aed984a97985b07'}
模型输出： {"role": "assistant", "content": "上海现在的天气是晴天，温度为36摄氏度，风力微弱。"}
最终答案： 上海现在的天气是晴天，温度为36摄氏度，风力微弱。
'''