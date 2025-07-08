import pandas as pd
import dashscope
import time

# 请替换为你的API Key, 使用行内的大模型进行推理
dashscope.api_key = "sk-00b7c296f942498cb70c9b021e97b170"  

# 封装Qwen-Turbo调用
def get_explanation(prompt):
    messages = [
        # 可以修改system prompt，让它针对某些列，进行解释和推理
        {"role": "system", "content": "你是一名银行客户资产分析师，请根据输入内容，简明扼要地用中文解释影响客户未来3个月资产是否能达到100万的最重要因素。"},
        {"role": "user", "content": prompt}
    ]
    try:
        response = dashscope.Generation.call(
            model='qwen-turbo',
            messages=messages,
            result_format='message'
        )
        return response.output.choices[0].message.content
    except Exception as e:
        return f"解释生成失败: {e}"

# 读取客户数据
file_path = 'simulated_customers.xlsx'
df = pd.read_excel(file_path)

# 需要分析的特征
features = [
    'total_assets', 'monthly_income', 'product_count', 'app_login_count',
    'financial_repurchase_count', 'investment_monthly_count'
]

# 为每个客户生成解释
explanations = []
for idx, row in df.iterrows():
    pred = row['预测结果']
    print('pred:', pred)
    shap_cols = [f'SHAP_{f}' for f in features]
    shap_vals = row[shap_cols].values
    # 找到绝对值最大的特征
    max_idx = abs(shap_vals).argmax()
    key_feat = features[max_idx]
    shap_val = shap_vals[max_idx]
    # 构造prompt
    prompt = f"客户特征：{', '.join([f'{f}={row[f]}' for f in features])}\n预测结果：{pred}\n最重要特征：{key_feat} (SHAP值={shap_val:.2f})。请用一句话解释该客户为何{pred}。"
    explanation = get_explanation(prompt)
    explanations.append(explanation)
    time.sleep(0.5)  # 防止QPS超限

df['客户解释'] = explanations
df.to_excel('simulated_customers_with_explain.xlsx', index=False)
print('已生成带客户解释的Excel：simulated_customers_with_explain.xlsx')

# 中文注释：
# 本脚本自动为每个客户生成资产预测解释，调用Qwen-Turbo，写入新Excel。 