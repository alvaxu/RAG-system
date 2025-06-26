#参考:https://mineru.net/apiManage
#批量数据上传解析

import requests

api_key = 'eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiI3NDkwMTA0NSIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc0NzYyODY2OSwiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiIiwib3BlbklkIjpudWxsLCJ1dWlkIjoiYjcyMjkzMDItMWRjYS00NmQ1LTk2NDktZjQ3NmY1N2Y0ZTRhIiwiZW1haWwiOiJhbHBoYV94dXdoQG91dGxvb2suY29tIiwiZXhwIjoxNzQ4ODM4MjY5fQ.FCOBgovyNoVRBbl9i04HHTrFrjMzn25GJAJlBwo4lxVB9Nvqc6MuSKGFukRmb02iiwgsYEeTysxIMpsHY3WkRg'

#参考https://mineru.net/apiManage
url='https://mineru.net/api/v4/file-urls/batch'
header = {
    'Content-Type':'application/json',
    "Authorization":f"Bearer {api_key}".format(api_key)
}
data = {
    "enable_formula": True,
    "language": "ch",
    "enable_table": True,
    "files": [
        {"name":"1.1-AI大模型原理与DeepSeek使用.pdf", "is_ocr": True, "data_id": "train1.1"},
        {"name":"1.2-API使用.pdf", "is_ocr": True, "data_id": "train1.2"},
        {"name":"2.1-DeepSeek使用.pdf", "is_ocr": True, "data_id": "train2.1"},
        {"name":"2.2-提示词工程.pdf", "is_ocr": True, "data_id": "train2.2"},
        {"name":"3.0【课前准备】AI编程工具安装.pdf", "is_ocr": True, "data_id": "train3.0"},
        {"name":"3.1-Cursor编程.pdf", "is_ocr": True, "data_id": "train3.1"},
        {"name":"3.2【补充】CASE-病床使用情况.pdf", "is_ocr": True, "data_id": "train3.2"},
        {"name":"4.1-Cursor数据可视化与洞察.pdf", "is_ocr": True, "data_id": "train4.1"},
        {"name":"4.2-CASE-客户续保预测.pdf", "is_ocr": True, "data_id": "train4.2"},
        {"name":"5-Embedding与向量数据库.pdf", "is_ocr": True, "data_id": "train5"},
        {"name":"6.1-RAG技术与应用.pdf", "is_ocr": True, "data_id": "train6.1"},
        {"name":"6.2-NotebookLM使用.pdf", "is_ocr": True, "data_id": "train6.2"},
        {"name":"7-RAG高级技术与实践.pdf", "is_ocr": True, "data_id": "train7"},
        {"name":"8.1-Text2SQL：自助式数据报表开发.pdf", "is_ocr": True, "data_id": "train8.1"},
        {"name":"8.2-vanna使用.pdf", "is_ocr": True, "data_id": "train8.2"},
        {"name":"9-LangChain：多任务应用开发.pdf", "is_ocr": True, "data_id": "train9"},
        {"name":"10-Function Calling与协作.pdf", "is_ocr": True, "data_id": "train10"},
        {"name":"11-MCP与A2A的应用.pdf", "is_ocr": True, "data_id": "train11"}
    ]
}
file_path = ["1.1-AI大模型原理与DeepSeek使用.pdf", "1.2-API使用.pdf", "2.1-DeepSeek使用.pdf", "2.2-提示词工程.pdf", "3.0【课前准备】AI编程工具安装.pdf", "3.1-Cursor编程.pdf", "3.2【补充】CASE-病床使用情况.pdf", "4.1-Cursor数据可视化与洞察.pdf", "4.2-CASE-客户续保预测.pdf", "5-Embedding与向量数据库.pdf", "6.1-RAG技术与应用.pdf", "6.2-NotebookLM使用.pdf", "7-RAG高级技术与实践.pdf", "8.1-Text2SQL：自助式数据报表开发.pdf", "8.2-vanna使用.pdf", "9-LangChain：多任务应用开发.pdf", "10-Function Calling与协作.pdf", "11-MCP与A2A的应用.pdf" ]
try:
    response = requests.post(url,headers=header,json=data)
    print(response)
    if response.status_code == 200:
        result = response.json()
        print('response success. result:{}'.format(result))
        if result["code"] == 0:
            batch_id = result["data"]["batch_id"]
            urls = result["data"]["file_urls"]
            print('batch_id:{},urls:{}'.format(batch_id, urls))
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
import requests

url = f'https://mineru.net/api/v4/extract-results/batch/{batch_id}'
header = {
    'Content-Type':'application/json',
    "Authorization":f"Bearer {api_key}".format(api_key)
}

res = requests.get(url, headers=header)
print(res.status_code)
print(res.json())
print(res.json()["data"])

res = requests.get(url, headers=header)
print(res.status_code)
print(res.json())
print(res.json()["data"])
result=res.json()["data"]
# 遍历 extract_result 列表
for item in result['extract_result']:
    file_name = item.get('file_name', 'N/A')  # 获取 file_name，如果没有则返回 'N/A'
    full_zip_url = item.get('full_zip_url', 'N/A')  # 获取 full_zip_url，如果没有则返回 'N/A'
    
    print(f"文件名: {file_name}")
    print(f"下载链接: {full_zip_url}")
    print("-" * 50)  # 分隔线