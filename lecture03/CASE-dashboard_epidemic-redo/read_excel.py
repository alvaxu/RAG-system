import pandas as pd

# 读取Excel文件
file_path = 'CASE-dashboard_epidemic-redo\香港各区疫情数据_20250322.xlsx'
try:
    # 读取Excel文件
    df = pd.read_excel(file_path)
    
    # 显示前20行数据
    print("Excel文件的前20行数据：")
    print(df.head(20))
    
except FileNotFoundError:
    print(f"错误：找不到文件 {file_path}")
except Exception as e:
    print(f"读取文件时发生错误：{str(e)}") 