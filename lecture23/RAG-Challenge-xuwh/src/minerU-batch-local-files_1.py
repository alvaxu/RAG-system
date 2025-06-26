#参考:https://mineru.net/apiManage
#批量数据上传解析

import requests
import os
import time
import zipfile

api_key = 'eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiI3NDkwMTA0NSIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc1MDc0MTU5NywiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiIiwib3BlbklkIjpudWxsLCJ1dWlkIjoiYTFiNmY0ZTAtZmYzYy00MTE5LWI4YmMtNDhlYTU3YjliMjczIiwiZW1haWwiOiJhbHBoYV94dXdoQG91dGxvb2suY29tIiwiZXhwIjoxNzUxOTUxMTk3fQ.q1NXWQkkfM5FWb3nYIKheVRqhvrenywE0SZwbC6p-PBiEYm779AR8GoiMQQCpNvwmZH8m-ENeZytahPWWiTEPA'

#参考https://mineru.net/apiManage
url='https://mineru.net/api/v4/file-urls/batch'
header = {
    'Content-Type':'application/json',
    "Authorization":f"Bearer {api_key}".format(api_key)
}
# ===================== 自动遍历pdf_reports目录并生成files和file_path =====================
pdf_dir = 'data/test_set/pdf_reports'  # 修正为相对项目根目录的路径
pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
output_dir = 'data/test_set/debug_data/03_reports_markdown'  # 修正为相对项目根目录的路径
os.makedirs(output_dir, exist_ok=True)

files = []
file_path = []
for idx, fname in enumerate(pdf_files):
    files.append({
        "name": fname,
        "is_ocr": True,
        "data_id": f"auto_{idx+1}"
    })
    file_path.append(os.path.join(pdf_dir, fname))

# 生成data字典
data = {
    "enable_formula": True,
    "language": "ch",
    "enable_table": True,
    "files": files
}

try:
    response = requests.post(url,headers=header,json=data)
    # print(response)
    if response.status_code == 200:
        result = response.json()
        # print('response success. result:{}'.format(result))
        if result["code"] == 0:
            batch_id = result["data"]["batch_id"]
            urls = result["data"]["file_urls"]
            # print('batch_id:{},urls:{}'.format(batch_id, urls))
            for i in range(0, len(urls)):
                with open(file_path[i], 'rb') as f:
                    res_upload = requests.put(urls[i], data=f)
                    if res_upload.status_code == 200:
                        print(f"{urls[i]} upload success")
                    else:
                        print(f"{urls[i]} upload failed")
        else:
            print('apply upload url failed,reason:{}'.format(result.msg))
    else:
        print('response not success. status:{} ,result:{}'.format(response.status_code, response))
except Exception as err:
    print(err)

## 批量获取任务结果

url = f'https://mineru.net/api/v4/extract-results/batch/{batch_id}'
header = {
    'Content-Type':'application/json',
    "Authorization":f"Bearer {api_key}".format(api_key)
}


def all_done_or_failed(results):
    """判断所有文件是否都已完成或失败"""
    for item in results:
        if item['state'] not in ['done', 'failed']:
            return False
    return True

# 轮询等待所有文件解析完成
print("开始轮询等待所有文件解析完成...")
while True:
    res = requests.get(url, headers=header)
    result = res.json()["data"]
    extract_result = result['extract_result']
    # 输出当前进度
    state_count = {"done":0, "running":0, "failed":0, "converting":0}
    for item in extract_result:
        state_count[item['state']] = state_count.get(item['state'], 0) + 1
    print(f"当前进度：{state_count}，时间：{time.strftime('%H:%M:%S')}")
    if all_done_or_failed(extract_result):
        print("全部文件已完成解析！")
        break
    time.sleep(5)  # 每5秒轮询一次

# 下载并解压所有已完成的zip文件
for item in extract_result:
    if item['state'] == 'done' and item.get('full_zip_url'):
        zip_url = item['full_zip_url']
        file_name = item['file_name']
        local_zip = os.path.join(output_dir, file_name + '.zip')
        pdf_prefix = os.path.splitext(file_name)[0]  # 获取上传pdf文件名的前缀
        print(f"正在下载: {file_name} -> {zip_url}")
        try:
            r = requests.get(zip_url)
            with open(local_zip, 'wb') as f:
                f.write(r.content)
            print(f"下载完成: {local_zip}")
            # 只解压md文件，并重命名
            with zipfile.ZipFile(local_zip, 'r') as zip_ref:
                for member in zip_ref.namelist():
                    if member.lower().endswith('.md'):
                        # 新文件名：pdf前缀
                        # md_name = os.path.basename(member)
                        # new_md_name = f"{pdf_prefix}_{md_name}"
                        new_md_name = f"{pdf_prefix}.md"
                        target_path = os.path.join(output_dir, new_md_name)
                        with zip_ref.open(member) as source, open(target_path, 'wb') as target:
                            target.write(source.read())
                        print(f"已解压并重命名: {target_path}")
            os.remove(local_zip)  # 可选：删除zip包
        except Exception as e:
            print(f"下载或解压失败: {file_name}, 错误信息: {e}")
    elif item['state'] == 'failed':
        print(f"文件解析失败: {item['file_name']}，错误信息: {item.get('err_msg', '')}")

print("全部下载与解压流程结束。")