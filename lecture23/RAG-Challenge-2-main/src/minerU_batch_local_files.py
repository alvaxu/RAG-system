#参考:https://mineru.net/apiManage
#批量数据上传解析

import requests
import os
import time
import zipfile

def run_mineru_batch_export(
    pdf_dir='data/test_set/pdf_reports',
    output_dir='data/test_set/debug_data/03_reports_markdown',
    api_key='',
    language='auto'
):
    """
    :function: 批量上传PDF到minerU平台并下载解析后的markdown
    :param pdf_dir: PDF文件目录
    :param output_dir: markdown输出目录
    :param api_key: minerU平台API密钥
    :param language: 解析语言
    :return: None
    """
    url='https://mineru.net/api/v4/file-urls/batch'
    header = {
        'Content-Type':'application/json',
        "Authorization":f"Bearer {api_key}"
    }
    pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
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

    data = {
        "enable_formula": True,
        "language": language,
        "enable_table": True,
        "files": files
    }

    batch_id = None
    try:
        response = requests.post(url,headers=header,json=data)
        if response.status_code == 200:
            result = response.json()
            if result["code"] == 0:
                batch_id = result["data"]["batch_id"]
                urls = result["data"]["file_urls"]
                for i in range(0, len(urls)):
                    with open(file_path[i], 'rb') as f:
                        res_upload = requests.put(urls[i], data=f)
                        if res_upload.status_code == 200:
                            print(f"{urls[i]} upload success")
                        else:
                            print(f"{urls[i]} upload failed")
            else:
                print('apply upload url failed,reason:{}'.format(result.get('msg','')))
        else:
            print('response not success. status:{} ,result:{}'.format(response.status_code, response))
    except Exception as err:
        print(err)
        return

    if not batch_id:
        print('未获取到batch_id，流程终止')
        return

    # 批量获取任务结果
    url_result = f'https://mineru.net/api/v4/extract-results/batch/{batch_id}'
    header = {
        'Content-Type':'application/json',
        "Authorization":f"Bearer {api_key}"
    }

    def all_done_or_failed(results):
        for item in results:
            if item['state'] not in ['done', 'failed']:
                return False
        return True

    print("开始轮询等待所有文件解析完成...")
    while True:
        res = requests.get(url_result, headers=header)
        result = res.json()["data"]
        extract_result = result['extract_result']
        state_count = {"done":0, "running":0, "failed":0, "converting":0}
        for item in extract_result:
            state_count[item['state']] = state_count.get(item['state'], 0) + 1
        print(f"当前进度：{state_count}，时间：{time.strftime('%H:%M:%S')}")
        if all_done_or_failed(extract_result):
            print("全部文件已完成解析！")
            break
        time.sleep(5)

    for item in extract_result:
        if item['state'] == 'done' and item.get('full_zip_url'):
            zip_url = item['full_zip_url']
            file_name = item['file_name']
            local_zip = os.path.join(output_dir, file_name + '.zip')
            pdf_prefix = os.path.splitext(file_name)[0]
            print(f"正在下载: {file_name} -> {zip_url}")
            try:
                r = requests.get(zip_url)
                with open(local_zip, 'wb') as f:
                    f.write(r.content)
                print(f"下载完成: {local_zip}")
                with zipfile.ZipFile(local_zip, 'r') as zip_ref:
                    for member in zip_ref.namelist():
                        if member.lower().endswith('.md'):
                            new_md_name = f"{pdf_prefix}.md"
                            target_path = os.path.join(output_dir, new_md_name)
                            with zip_ref.open(member) as source, open(target_path, 'wb') as target:
                                target.write(source.read())
                            print(f"已解压并重命名: {target_path}")
                os.remove(local_zip)
            except Exception as e:
                print(f"下载或解压失败: {file_name}, 错误信息: {e}")
        elif item['state'] == 'failed':
            print(f"文件解析失败: {item['file_name']}，错误信息: {item.get('err_msg', '')}")
    print("全部下载与解压流程结束。")

# 保留命令行可运行性
if __name__ == "__main__":
    # 这里可自定义参数或从环境变量读取
    run_mineru_batch_export(
        pdf_dir='data/test_set/pdf_reports',
        output_dir='data/test_set/debug_data/03_reports_markdown',
        api_key='你的APIKEY',
        language='auto'
    )