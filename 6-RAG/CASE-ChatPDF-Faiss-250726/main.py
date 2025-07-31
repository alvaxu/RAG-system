# Qwen-Turbo API的基础限流设置为每分钟不超过500次API调用（QPM）。同时，Token消耗限流为每分钟不超过500,000 Tokens
from dataclasses import dataclass
from pathlib import Path
from pyprojroot import here
import logging
import os
import json
import pandas as pd
import shutil
import time
from collections import defaultdict
import re
from dotenv import load_dotenv

from minerU_batch_local_files import run_mineru_batch_export
from V100_document_loader_chunker import process_documents
from V303_vector_store_qa_with_cost import create_vector_store_from_documents, load_vector_store_and_answer_questions

if __name__ == "__main__":
    # 加载环境变量
    load_dotenv()
    
    root_path = Path(__file__).parent
    print('root_path:', root_path)
   
    # 以下方法可按需取消注释，逐步运行各流程：
   
    # # 1-4. 直接运行minerU 解析pdf 报告为纯markdown文本
    # #    新文件在 md目录下
    # print('1-4.直接运行minerU 解析pdf 报告为纯markdown文本')

    # minerU_api_key ='eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiI3NDkwMTA0NSIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc1MzQ5NzU2MiwiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiIiwib3BlbklkIjpudWxsLCJ1dWlkIjoiYTJjYjk5OGItMDJkZi00MGMxLWEyYTgtNDAzMDhlMjMxOTRjIiwiZW1haWwiOiJhbHBoYV94dXdoQG91dGxvb2suY29tIiwiZXhwIjoxNzU0NzA3MTYyfQ.3DskHQZcZoMa2HcjMx7HZ9qIoydqN01zlabFu47lkMGbj5_Jk4gbfkAQXuUjXi2vTX7ZB2fYDG2orDH-Vj0hnA'

    # run_mineru_batch_export(
    #     pdf_dir='pdf',
    #     output_dir='md',
    #     api_key=minerU_api_key,
    #     language='ch'
    # )
    
    # 5. 加载文档并进行分块处理
    print('5. 加载文档并进行分块处理')
    chunks = process_documents('md')
    print(f'共生成 {len(chunks)} 个文档分块')
    
    # 6. 从文档分块创建向量数据库
    print('6. 从文档分块创建向量数据库')
    # 从环境变量中获取API密钥
    DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY', '你的APIKEY')
    # 如果有有效的API密钥，则创建向量数据库
    if DASHSCOPE_API_KEY and DASHSCOPE_API_KEY != '你的APIKEY':
        vector_store = create_vector_store_from_documents(md_dir='md', api_key=DASHSCOPE_API_KEY, save_path='./vector_db', chunks=chunks)
        print('向量数据库创建完成')
    else:
        print('向量数据库创建功能已跳过（需要有效的API密钥）')
    
    print('完成')
