#!/usr/bin/env python
# coding: utf-8

# In[2]:

from PrintNestDict import print_nested_dict
import dashscope
from dashscope.api_entities.dashscope_response import Role
# dashscope.api_key = "sk-dd7ae33a0056483a82660b9392f4eedc "
dashscope.api_key = "sk-da635dce04da45779b76d549568126f0"
# 封装模型响应函数
def get_response(messages):
    response = dashscope.Generation.call(
        model='qwen-turbo',
        #model="deepseek-r1",
        messages=messages,
        #result_format='message'  # 将输出设置为message形式
        result_format='text'    # 将输出设置为text形式
    )
    return response
    
# review = '这款音效特别好 给你意想不到的音质。'
review = '这本书写得很烂，读也读不懂。'
messages=[
    {"role": "system", "content": "你是一名舆情分析师，帮我判断产品口碑的正负向，回复请用一个词语：正向 或者 负向"},
    {"role": "user", "content": review}
  ]

response = get_response(messages)
print_nested_dict(response,4)
# 对应message格式的content输出
# print(response.output.choices[0].message.content)
#对应text格式的输出
print(response.output.text)



