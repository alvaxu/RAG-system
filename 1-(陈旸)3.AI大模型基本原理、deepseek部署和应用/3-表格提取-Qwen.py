import json
import os
import dashscope
from dashscope.api_entities.dashscope_response import Role
import os
# dashscope.api_key = "sk-dd7ae33a0056483a82660b9392f4eedc "
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
# from openai import OpenAI

# 封装模型响应函数
def get_response(messages):
    response = dashscope.MultiModalConversation.call(
        model='qwen-vl-plus',
        messages=messages
    )
    return response

content = [
    {'type': 'image', 'image': 'https://aiwucai.oss-cn-huhehaote.aliyuncs.com/pdf_table.jpg'},
    {'type': 'text', 'text': '这是一个表格图片，帮我提取里面的内容，输出JSON格式'}
]

messages=[{"role": "user", "content": content}]
# 得到响应
response = get_response(messages)
print(response)


# In[2]:


print(response.output.choices[0].message.content[0]['text'])

