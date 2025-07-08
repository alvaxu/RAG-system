import pandas as pd

"""
:function: 读取二手车训练集的前5行数据并输出，并保存到Excel文件
:param 无
:return: 无
"""
def read_head5():
    # 读取csv文件，分隔符为空格
    df = pd.read_csv('used_car_train_20200313.csv', sep=' ')
    # 输出前5行数据
    head5 = df.head(5)
    print(head5)
    # 保存前5行到Excel文件
    head5.to_excel('head5.xlsx', index=False)
    print('前5行数据已保存到head5.xlsx')

if __name__ == "__main__":
    read_head5() 