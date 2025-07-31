import pandas as pd
import re

# 读取数据
df = pd.read_csv('Seattle_Hotels.csv', encoding='latin1')

# 1. 去除desc为空或全空格的行
df = df[df['desc'].notnull() & (df['desc'].str.strip() != '')]

# 2. 去除异常短文本（如长度小于30的简介）
df = df[df['desc'].str.len() >= 30]

# 3. 替换常见乱码和特殊字符
def clean_text(text):
    text = re.sub(r'[�?]', ' ', text)  # 替换乱码
    text = re.sub(r'\\n|\\r|\\t', ' ', text)  # 替换转义字符
    text = re.sub(r'\\s+', ' ', text)  # 多空格合并
    return text.strip()

df['desc'] = df['desc'].apply(clean_text)

# 4. 可选：去重
df = df.drop_duplicates(subset=['desc'])

# 5. 重新索引
df = df.reset_index(drop=True)

# 6. desc列表
descs = df['desc'].tolist()
print(f"清洗后desc数量: {len(descs)}")
print("前3个desc示例：", descs[:3])