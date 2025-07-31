import pandas as pd
import chardet

# 先检测文件编码
with open('Seattle_Hotels.csv', 'rb') as f:
    result = chardet.detect(f.read(10000))
    print("检测到的编码为：", result['encoding'])

# 读取CSV文件前5行
df = pd.read_csv('Seattle_Hotels.csv', nrows=5, encoding='latin1')
print(df)

# 输出读取到的内容
print("\n读取到的前5行内容如下：")
for idx, row in df.iterrows():
    print(f"{idx+1}. 酒店名称: {row['name']}, 地址: {row['address']}, 简介: {row['desc'][:30]}...")  # 简介只显示前30字
