from langchain.agents import Tool, LLMSingleActionAgent, AgentExecutor
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import os
from typing import Union

# 1. 准确定义工具（名称和描述要清晰）
def get_word_length(word: str) -> int:
    return len(word)

tools = [
    Tool(
        name="字符串长度计算",  # 工具名称必须唯一且明确
        func=get_word_length,
        description="计算英文单词的长度，输入一个单词，返回它的字符数"
    )
]
# 2. 重构Prompt模板（强制要求Final Answer）
prompt = PromptTemplate.from_template("""
你是一个帮助用户解决问题的助手。你可以使用以下工具：

{tools}

你必须严格按照以下格式回答，每个步骤都必须包含，不能跳过任何步骤：

Question: {input}

Thought: 分析问题
Action: 工具名称
Action Input: 输入内容
Observation: 工具返回结果
Final Answer: 最终答案

重要规则：
1. 必须按照上述格式一步一步回答
2. 每个步骤都必须包含，不能跳过
3. 在得到工具输出后，必须立即给出Final Answer
4. 不要重复使用工具
5. 每个问题只需要使用一次工具
6. 如果看到工具的输出，必须给出Final Answer
7. 不要等待或思考，直接给出Final Answer

示例：
Question: 单词'hello'的长度是多少？

Thought: 这是一个简单的字符串长度计算问题，我需要使用字符串长度计算工具来计算
Action: 字符串长度计算
Action Input: 'hello'
Observation: 5
Final Answer: 单词'hello'的长度是5

现在开始：

Question: {input}
""")

# 3. 创建llm
BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL = "qwen-turbo"
API_KEY = os.getenv('DASHSCOPE_API_KEY')
llm = ChatOpenAI(
    model= MODEL,  # 默认的大模型为GPT-3.5-turbo，比较便宜
    openai_api_base= BASE_URL,
    openai_api_key= API_KEY
)


#4. Create LLMChain first
llm_chain = LLMChain(llm=llm, prompt=prompt)


# 5. Create output parser
from langchain.agents.output_parsers import ReActSingleInputOutputParser
output_parser = ReActSingleInputOutputParser()

# 6. 定义的工具名称
tool_names = [tool.name for tool in tools]

# 7. 定义SingleActionAgent
agent = LLMSingleActionAgent(
    llm_chain=llm_chain,
    output_parser=output_parser,
    allowed_tools=tool_names,
    stop=["\nObservation:", "\nFinal Answer:", "Observation:", "Final Answer:"]
)

# 8. 执行时传入工具描述
agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=3,
    handle_parsing_errors=True  # 添加错误处理
)

# 9. 运行（确保输入格式正确）
try:
    result = agent_executor.invoke({
        "input": "单词'hello'的长度是多少？",
        "tools": "\n".join([f"{tool.name}: {tool.description}" for tool in tools])
    })

    # 10. 处理输出
    if "output" in result:
        print(f"执行结果: {result['output']}")
    else:
        print("未能获取到结果")
except Exception as e:
    print(f"执行过程中出现错误: {str(e)}")  