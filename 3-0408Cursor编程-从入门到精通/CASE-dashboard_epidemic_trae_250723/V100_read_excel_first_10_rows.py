'''程序说明：
## 1. 读取Excel文件的前10行数据并打印输出
## 2. 使用pandas库处理Excel文件，支持.xlsx格式
## 3. 包含详细的函数注释和使用说明
'''

import pandas as pd


def read_excel_first_10_rows(file_path):
    """
    :function: 读取Excel文件的前10行数据
    :param file_path: Excel文件的绝对路径
    :return: 包含前10行数据的DataFrame对象
    """
    # 读取Excel文件的前10行数据
    # 使用openpyxl作为引擎以支持xlsx格式
    df = pd.read_excel(file_path, nrows=10, engine='openpyxl')
    return df


if __name__ == "__main__":
    # 定义Excel文件路径
    excel_file_path = r"d:\cursorprj\3-0408Cursor编程-从入门到精通\CASE-dashboard_epidemic-250723\香港各区疫情数据_20250322.xlsx"
    
    # 读取数据并处理可能的异常
    try:
        print("开始读取Excel文件...")
        result_df = read_excel_first_10_rows(excel_file_path)
        
        print("\n成功读取Excel文件前10行数据：")
        print(result_df)
        
        # 提供数据基本信息
        print("\n数据基本信息：")
        print(f"行数: {len(result_df)}, 列数: {len(result_df.columns)}")
        print("列名: ", list(result_df.columns))
    except FileNotFoundError:
        print(f"错误: 文件 '{excel_file_path}' 未找到")
    except Exception as e:
        print(f"读取文件时发生错误: {str(e)}")