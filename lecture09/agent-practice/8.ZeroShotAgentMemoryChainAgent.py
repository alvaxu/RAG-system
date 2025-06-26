#给出三轮问题，第三个问题"这两个单词的长度之和是多少？"需要调用前两个问题的结果，实验证明它记住了。
from langchain.agents import Tool, ZeroShotAgent, AgentExecutor
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
import os

# 1. 定义工具函数
def simple_add(expression: str) -> str:
    """简单的加法计算器"""
    try:
        # 移除所有空格和引号
        expression = expression.strip().strip('"\'')
        # 分割数字
        numbers = expression.split('+')
        # 转换为整数并求和
        result = sum(int(num.strip()) for num in numbers)
        return str(result)
    except Exception as e:
        return f"计算失败：{str(e)}"

def get_word_length(word: str) -> str:
    """计算字符串长度"""
    try:
        # 移除所有空格和引号
        word = word.strip().strip('"\'')
        return str(len(word))
    except Exception as e:
        return f"计算失败：{str(e)}"

# 2. 创建工具列表
tools = [
    Tool(
        name="SimpleAdd",
        func=simple_add,
        description="简单的加法计算器，输入格式为'数字+数字'，例如：1+2"
    ),
    Tool(
        name="WordLength",
        func=get_word_length,
        description="计算字符串长度，输入一个字符串，返回它的字符数，例如：'hello'"
    )
]

# 3. 创建ZeroShotAgent的提示模板
prefix = """你是一个帮助用户解决问题的助手。你可以使用以下工具：

{tools}

请使用以下格式：

Question: 输入的问题
Thought: 你需要思考如何解决这个问题
Action: 要使用的工具名称
Action Input: 工具的输入
Observation: 工具的输出
... (这个思考/行动/观察可以重复多次)
Thought: 我现在知道最终答案
Final Answer: 对原始输入问题的最终答案

重要提示：
1. 如果问题涉及多个步骤，你需要一步步思考
2. 可以使用一个工具的输出作为另一个工具的输入
3. 在得到所有需要的结果后，给出最终答案
4. 记住之前的对话历史，可以在需要时使用之前的结果

对话历史：
{chat_history}

现在开始：

Question: {input}
"""

suffix = """
{agent_scratchpad}
"""

# 创建llm
BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL = "qwen-turbo"
API_KEY = os.getenv('DASHSCOPE_API_KEY')
llm = ChatOpenAI(
    model= MODEL,  # 默认的大模型为GPT-3.5-turbo，比较便宜
    openai_api_base= BASE_URL,
    openai_api_key= API_KEY
)

# 创建memory
memory = ConversationBufferMemory(
    memory_key="chat_history",
    input_key="input",
    output_key="output",
    return_messages=True
)

# 创建agent
agent = ZeroShotAgent(
    llm_chain=LLMChain(llm=llm, prompt=PromptTemplate.from_template(prefix + suffix)),
    tools=tools,
    verbose=True
)

# 执行
agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=10,
    memory=memory
)

# 准备工具描述
tools_description = "\n".join([f"{tool.name}: {tool.description}" for tool in tools])

# 运行多轮对话
print("第一轮：计算第一个单词的长度")
result1 = agent_executor.invoke({
    "input": "单词'hello'的长度是多少？",
    "tools": tools_description
})
print("输出：", result1["output"])

print("\n第二轮：计算第二个单词的长度")
result2 = agent_executor.invoke({
    "input": "单词'world'的长度是多少？",
    "tools": tools_description
})
print("输出：", result2["output"])

print("\n第三轮：计算两个单词长度之和")
result3 = agent_executor.invoke({
    "input": "这两个单词的长度之和是多少？",
    "tools": tools_description
})
print("输出：", result3["output"]) 

print("\n第四轮：计算两个单词长度之和")
result3 = agent_executor.invoke({
    "input": "既然已经知道了这两个单词的长度，请直接计算这两个单词的长度之和是多少？",
    "tools": tools_description
})
print("输出：", result3["output"]) 