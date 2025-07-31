import json
import os
import dashscope
from dashscope.api_entities.dashscope_response import Role
import os
# dashscope.api_key = "sk-dd7ae33a0056483a82660b9392f4eedc "
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
# from openai import OpenAI

# 封装模型响应函数
# def get_response(messages):
#     response = dashscope.MultiModalConversation.call(
#         model='qwen-vl-plus',
#         messages=messages
#     )
#     return response

content = [
    {'type': 'image', 'image': 'https://aiwucai.oss-cn-huhehaote.aliyuncs.com/pdf_table.jpg'},
    {'type': 'text', 'text': '这是一个表格图片，帮我提取里面的内容，输出JSON格式'}
]

messages=[{"role": "user", "content": content}]
# 得到响应
response = dashscope.MultiModalConversation.call(
    model='qwen-vl-plus',
    messages=messages,
    result_format='message', # 将输出设置为message形式
    stream=True, # 是否使用流式输出
    incremental_output=True # 推荐加此参数，获得更好的流式体验
)

# 流式输出，增加健壮性判空
for chunk in response:
    try:
        for part in chunk['output']['choices'][0]['message']['content']:
            print(part['text'], end='', flush=True)
    except Exception as e:
        print("[Debug] Unexpected chunk:", chunk)

