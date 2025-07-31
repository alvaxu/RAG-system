import json
import os
import dashscope
from dashscope.api_entities.dashscope_response import Role
# from openai import OpenAI #这里没用openai所以注释掉

import os
# dashscope.api_key = "sk-dd7ae33a0056483a82660b9392f4eedc "
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
# function call 的函数列表，用于让模型调用
functions = [
    {
      'name': 'get_current_weather',
      'description': 'Get the current weather in a given location.',
      'parameters': {
            'type': 'object',
            'properties': {
                'location': {
                    'type': 'string',
                    'description': 'The city and state, e.g. San Francisco, CA'
                },
                'unit': {'type': 'string', 'enum': ['celsius', 'fahrenheit']}
            },
        'required': ['location']
      }
    }
]
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
    return json.dumps(weather_info)

# 封装模型响应函数
def get_response(messages):
    try:
        response = dashscope.Generation.call(
            model='qwen-max',       ## 也可以用qwen-turbo,但是语法不同,并未调用function call
            
            messages=messages,
            functions=functions,
            result_format='message'
        )
        return response
    except Exception as e:
        print(f"API调用出错: {str(e)}")
        return None

# 使用function call进行QA
def run_conversation():
    query = "上海的天气怎样？"
    messages=[{"role": "user", "content": query}]

    
    # 得到第一次响应
    response = get_response(messages)
    if not response or not response.output:
        print("获取响应失败")
        return None
        
    print('first time response=', response)
    
    message = response.output.choices[0].message
    messages.append(message)
    print(' message before function call=', message)
    
    # Step 2, 判断用户是否要call function
   # if hasattr(message, 'function_call') and message.function_call: # 用qwen-max
    if 'function_call' in message and message['function_call']:   # 用qwen-turbo，并未进入这个分支
        function_call = message.function_call
        tool_name = function_call['name']
        # Step 3, 执行function call
        arguments = json.loads(function_call['arguments'])
        print('function call arguments=', arguments)
        tool_response = get_current_weather(
            location=arguments.get('location'),
            unit=arguments.get('unit'),
        )
        tool_info = {"role": "function", "name": tool_name, "content": tool_response}
        print('tool_info=', tool_info)
        messages.append(tool_info)
        print('second time messages=', messages)
        
        #Step 4, 得到第二次响应
        response = get_response(messages)
        if not response or not response.output:
            print("获取第二次响应失败")
            return None
            
        print('second time  response=', response)
        message = response.output.choices[0].message
        return message
    return message



if __name__ == "__main__":
    result = run_conversation()
    if result:
        print("最终结果:", result)
    else:
        print("对话执行失败")

'''
1.用qwen-max
PS D:\cursorprj\1-(陈旸)3.AI大模型基本原理、deepseek部署和应用> & C:/Users/Administrator/AppData/Local/Programs/Python/Python312/python.exe "d:/cursorprj/1-(陈旸)3.AI大模型基本原理、deepseek部署和应用/2-天气Function-Qwen.py"
first time response= {"status_code": 200, "request_id": "8e7a92d6-be1f-9183-a5d3-658a04368b61", "code": "", "message": "", "output": {"text": null, "finish_reason": null, "choices": [{"finish_reason": "function_call", "message": {"role": "assistant", "content": "", "function_call": {"name": "get_current_weather", "arguments": "{\"location\": \"上海\", \"unit\": \"celsius\"}"}}}]}, "usage": {"input_tokens": 207, "output_tokens": 26, "total_tokens": 233, "prompt_tokens_details": {"cached_tokens": 0}}}
 message before function call= {"role": "assistant", "content": "", "function_call": {"name": "get_current_weather", "arguments": "{\"location\": \"上海\", \"unit\": \"celsius\"}"}}
function call arguments= {'location': '上海', 'unit': 'celsius'}
tool_info= {'role': 'function', 'name': 'get_current_weather', 'content': '{"location": "\\u4e0a\\u6d77", "temperature": 36, "unit": "celsius", "forecast": ["\\u6674\\u5929", "\\u5fae\\u98ce"]}'}
second time messages= [{'role': 'user', 'content': '上海的天气怎样？'}, Message({'role': 'assistant', 'content': '', 'function_call': {'name': 'get_current_weather', 'arguments': '{"location": "上海", "unit": "celsius"}'}}), {'role': 'function', 'name': 'get_current_weather', 'content': '{"location": "\\u4e0a\\u6d77", "temperature": 36, "unit": "celsius", "forecast": ["\\u6674\\u5929", "\\u5fae\\u98ce"]}'}]
second time  response= {"status_code": 200, "request_id": "c01c1f82-2913-9d6b-897a-6f385e38113f", "code": "", "message": "", "output": {"text": null, "finish_reason": null, "choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": "上海当前的温度是36摄氏度，天气晴朗伴有微风。"}}]}, "usage": {"input_tokens": 294, "output_tokens": 20, "total_tokens": 314, "prompt_tokens_details": {"cached_tokens": 0}}}
最终结果: {"role": "assistant", "content": "上海当前的温度是36摄氏度，天气晴朗伴有微风。"}
2.用qwen-turbo
PS D:\cursorprj\1-(陈旸)3.AI大模型基本原理、deepseek部署和应用> & C:/Users/Administrator/AppData/Local/Programs/Python/Python312/python.exe "d:/cursorprj/1-(陈旸)3.AI大模型基本原理、deepseek部署和应用/2-天气Function-Qwen.py"
first time response= {"status_code": 200, "request_id": "44dafc56-6e90-9afe-9e47-66a7c0ffcec7", "code": "", "message": "", "output": {"text": null, "finish_reason": null, "choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": "上海的天气目前是多云，气温为25摄氏度。"}}]}, "usage": {"input_tokens": 195, "output_tokens": 16, "total_tokens": 211, "prompt_tokens_details": {"cached_tokens": 0}}}
 message before function call= {"role": "assistant", "content": "上海的天气目前是多云，气温为25摄氏度。"}
最终结果: {"role": "assistant", "content": "上海的天气目前是多云，气温为25摄氏度。"}
'''