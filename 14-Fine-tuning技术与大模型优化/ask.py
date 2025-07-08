# 导入微调模型
from unsloth import FastLanguageModel
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "lora_model_medical",  # 保存的模型
    max_seq_length = max_seq_length,
    dtype = dtype,
    load_in_4bit = load_in_4bit,
)
FastLanguageModel.for_inference(model)  # 启用原生2倍速推理

# 生成医疗回答的函数
"""
:function: generate_medical_response
:param question: str，用户输入的问题
:return: None，直接输出模型回答
"""
def generate_medical_response(question):
    """生成医疗回答"""
    FastLanguageModel.for_inference(model)  # 启用原生2倍速推理
    inputs = tokenizer(
        [medical_prompt.format(question, "")],
        return_tensors="pt"
    ).to("cuda")
    from transformers import TextStreamer
    text_streamer = TextStreamer(tokenizer)
    _ = model.generate(
        **inputs,
        streamer=text_streamer,
        max_new_tokens=256,
        temperature=0.7,
        top_p=0.9,
        repetition_penalty=1.1
    )

# 10个中医求诊相关的示例问题
example_questions = [
    "我最近总是感觉头晕，应该怎么办？",
    "晚上经常失眠，有什么中医调理的方法？",
    "经常口干口苦，是身体哪里出了问题？",
    "最近食欲不振，容易腹胀，有什么建议？",
    "女性月经不调，中医如何调理？",
    "经常腰膝酸软，是肾虚吗？",
    "小孩经常咳嗽，有什么中医食疗方？",
    "体质虚弱，容易感冒，如何增强体质？",
    "皮肤经常过敏发痒，中医怎么看？",
    "老年人夜尿频多，有什么中医建议？"
]

# 打印示例问题供用户选择
print("请选择或输入您的中医求诊问题（输入'exit'或'退出'结束）：")
for idx, q in enumerate(example_questions, 1):
    print(f"{idx}. {q}")

# 循环询问用户问题，直到输入exit或退出
while True:
    user_input = input("\n请输入您的问题（可输入序号或自定义问题）：\n")
    if user_input.strip().lower() in ["exit", "退出"]:
        print("感谢您的咨询，再见！")
        break
    # 如果输入为数字序号，自动选择示例问题
    if user_input.isdigit():
        idx = int(user_input)
        if 1 <= idx <= len(example_questions):
            question = example_questions[idx-1]
        else:
            print("无效的序号，请重新输入。")
            continue
    else:
        question = user_input
    generate_medical_response(question) 