import pandas as pd

def read_excel_first_rows():
    """
    读取hospital_bed_usage_data.xlsx文件的前五行并打印出来
    """
    # 读取Excel文件
    df = pd.read_excel('hospital_bed_usage_data.xlsx')
    
    # 打印前五行
    print("Excel文件的前五行数据：")
    print(df.head())
    
    # 获取表格的基本信息
    print("\n表格的基本信息：")
    print(f"表格形状: {df.shape}")
    print(f"列名: {list(df.columns)}")
    
    return df

if __name__ == "__main__":
    # 执行函数
    data = read_excel_first_rows()