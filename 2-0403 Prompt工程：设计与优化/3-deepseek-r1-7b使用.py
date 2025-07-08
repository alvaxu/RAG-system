#!/usr/bin/env python
# coding: utf-8

# In[1]:


from modelscope import AutoModelForCausalLM, AutoTokenizer
# model_name = "/root/autodl-tmp/models/deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
# model_name="C:\\Users\\Administrator\\AInewModels\\deepseek-ai\\DeepSeek-R1-Distill-Qwen-7B"
model_name="D:\\AInewModels\\deepseek-ai\\DeepSeek-R1-Distill-Qwen-1___5B"
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    # device_map="cuda" # auto
    device_map="auto" # auto
)
tokenizer = AutoTokenizer.from_pretrained(model_name)
prompt = "帮我写一个二分查找法"
# prompt = "请从伊利集团最新的财务报表中提取以下信息，包括：公司名称，股票代码，营收，净利润，毛利，总资产，总负债。并以JSON格式返回"
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": prompt}
]
text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
)
model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
generated_ids = model.generate(
    **model_inputs,
    max_new_tokens=2000
)
generated_ids = [
    output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
]
response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
print(response)

