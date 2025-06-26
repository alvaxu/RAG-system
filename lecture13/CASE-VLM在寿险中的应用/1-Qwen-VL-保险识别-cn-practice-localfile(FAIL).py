# 使用本地图片进行推理(尝试失败)
# 云端API不支持file://本地路径，只能用公网URL。
# 你需要先把图片上传到公网，然后用公网URL推理。
# 解决方案
# 方案一：将图片上传到公网（推荐）
# 将本地图片上传到一个公网可访问的存储（如OSS、七牛云、腾讯云COS等）。
# 使用上传后的公网URL作为 image_url。
# 方案二：本地推理（仅限本地模型）
# 如果你用的是本地部署的VLM模型，可以直接读取本地图片路径。
# 但你现在用的是 DashScope 的云端API，只能用公网图片URL。

# 使用方法：
# 1. 把图片放到jpg文件夹中
# 2. 运行脚本
# 3. 结果会保存在prompt_template_cn_result_practice_local.xlsx中

import os

from openai import OpenAI
import pandas as pd

DASHSCOPE_API_KEY= os.getenv('DASHSCOPE_API_KEY')
client = OpenAI(
#    api_key="sk-882e296067b744289acf27e6e20f3ec0", 
    api_key=DASHSCOPE_API_KEY, 
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# 调用VLM，得到推理结果
# user_prompt：用户想要分析的内容
# image_url：想要分析的图片
def get_response(user_prompt, image_url):
    # 得到image_url_list，一张图片也放到[]中
    if image_url.startswith('[') and ',' in image_url:
        # 属于image_url list
        image_url = image_url.strip()
        image_url = image_url[1:-1]
        image_url_list = image_url.split(',')
        image_url_list = [temp_url.strip() for temp_url in image_url_list]
    else:
        image_url_list = [image_url]
    # 得到messages
    content = [{"type": "text", "text": f"{user_prompt}"}]
    for temp_url in image_url_list: 
        # image_url = f"https://vl-image.oss-cn-shanghai.aliyuncs.com/{temp_url}.jpg"
        # content.append({"type": "image_url","image_url": {"url": f"{image_url}"}})        
        # 修改为本地图片路径
        local_image_path = os.path.join(os.path.dirname(__file__), 'jpg', f'{temp_url}.jpg')
        # 检查本地图片是否存在
        if not os.path.exists(local_image_path):
            raise FileNotFoundError(f"图片文件未找到: {local_image_path}")
        content.append({"type": "image_url", "image_url": {"url": f"file://{local_image_path}"}})
    messages=[{
                "role": "user",
                "content": content
            }
        ]

    print(f'messages={messages}')
    completion = client.chat.completions.create(
        model="qwen-vl-max", #qwen-vl-plus
        messages=messages    
        )
    #print(completion.model_dump_json())
    return completion
    
# 识别结果写入execl中
df = pd.read_excel('./prompt_template_cn.xlsx')
df['response'] = ''
for index, row in df.iterrows():
    user_prompt = row['prompt']
    image_url = row['image']
    # 得到VLM推理结果
    completion = get_response(user_prompt, image_url)
    response = completion.choices[0].message.content
    df.loc[index, 'response'] = response
    print(f"{index+1} {user_prompt} {image_url}")
df.to_excel('./prompt_template_cn_result_practice_local.xlsx', index=False)
