
# 直接读取本地 jpg 目录下的图片（支持批量，支持多图片）。
# 使用 dashscope.MultiModalConversation.call 方法推理，图片路径用 file:// 前缀。。
# 使用方法：
# 1. 把图片放到jpg文件夹中
# 2. 运行脚本
# 3. 结果会保存在prompt_template_cn_result_practice_local.xlsx中

import os
import pandas as pd
import dashscope
from dashscope.api_entities.dashscope_response import Role
from dashscope import MultiModalConversation

DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')
dashscope.api_key = DASHSCOPE_API_KEY

def get_response(user_prompt, image_url):
    """
    :function: 调用VLM，得到推理结果
    :param user_prompt: 用户想要分析的内容
    :param image_url: 想要分析的图片（图片名或逗号分隔的图片名列表）
    :return: VLM返回的内容
    """
    # 得到image_url_list，一张图片也放到[]中
    if image_url.startswith('[') and ',' in image_url:
        image_url = image_url.strip()
        image_url = image_url[1:-1]
        image_url_list = image_url.split(',')
        image_url_list = [temp_url.strip() for temp_url in image_url_list]
    else:
        image_url_list = [image_url]
    # 构造content
    content = []
    for temp_url in image_url_list:
        local_image_path = os.path.join(os.path.dirname(__file__), 'jpg', f'{temp_url}.jpg')
        if not os.path.exists(local_image_path):
            raise FileNotFoundError(f"图片文件未找到: {local_image_path}")
        content.append({'image': f'file://{local_image_path}'})
    content.append({'text': user_prompt})
    messages = [
        {
            'role': 'user',
            'content': content
        }
    ]
    # 调用dashscope本地图片推理
    response = MultiModalConversation.call(model='qwen-vl-plus', messages=messages)
    # 兼容返回格式
    if hasattr(response, 'output') and hasattr(response.output, 'choices'):
        result = response.output.choices[0].message.content[0]['text']
    else:
        result = str(response)
    print(result)
    return result

# 识别结果写入excel中
if __name__ == '__main__':
    df = pd.read_excel('./prompt_template_cn.xlsx')
    df['response'] = ''
    for index, row in df.iterrows():
        user_prompt = row['prompt']
        image_url = row['image']
        try:
            response = get_response(user_prompt, image_url)
        except Exception as e:
            response = f'识别出错: {e}'
        df.loc[index, 'response'] = response
        print(f"{index+1} {user_prompt} {image_url}")
    df.to_excel('./prompt_template_cn_result_practice_local.xlsx', index=False)
