import json
import os
import dashscope
from dashscope.api_entities.dashscope_response import Role
from dashscope import MultiModalConversation
DASHSCOPE_API_KEY= os.getenv('DASHSCOPE_API_KEY')
dashscope.api_key = DASHSCOPE_API_KEY

local_file_path = 'file://甘斌斌一家美国合影.jpg'
messages = [{
    'role': 'system',
    'content': [{
        'text': 'You are a helpful assistant.'
    }]
}, {
    'role':
    'user',
    'content': [
        {
            'image': local_file_path
        },
        {
            'text': '图片里有什么东西?'
        },
    ]
}]
response = MultiModalConversation.call(model='qwen-vl-max', messages=messages)
print(response.output.choices[0].message.content[0]['text'])