"""
程序说明：

## 1. 使用pandas库读取customer_base.csv和customer_behavior_assets.csv文件的前5行数据
## 2. 展示两个文件的字段结构和数据样例

"""

import pandas as pd
import os

def read_csv_head():
    """
    读取CSV文件的前5行数据并打印字段信息
    :function: 读取并展示CSV文件的结构和数据样例
    :return: None
    """
    # 确保文件存在
    files = ['customer_base.csv', 'customer_behavior_assets.csv']
    for file in files:
        if not os.path.exists(file):
            print(f"错误：文件 {file} 不存在！")
            return

    try:
        # 读取customer_base.csv
        print("\n=== customer_base.csv 数据结构 ===")
        df_base = pd.read_csv('customer_base.csv', nrows=5)
        print("\n字段列表：")
        for col in df_base.columns:
            print(f"- {col}")
        print("\n前5行数据：")
        print(df_base)

        # 读取customer_behavior_assets.csv
        print("\n\n=== customer_behavior_assets.csv 数据结构 ===")
        df_behavior = pd.read_csv('customer_behavior_assets.csv', nrows=5)
        print("\n字段列表：")
        for col in df_behavior.columns:
            print(f"- {col}")
        print("\n前5行数据：")
        print(df_behavior)

    except Exception as e:
        print(f"读取文件时发生错误：{str(e)}")

if __name__ == "__main__":
    read_csv_head() 