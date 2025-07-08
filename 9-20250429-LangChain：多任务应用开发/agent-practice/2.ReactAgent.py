from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import os

# 1. 定义一个简单的加法计算器工具
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

tools = [
    Tool(
        name="SimpleAdd",
        func=simple_add,
        description="简单的加法计算器，输入格式为'数字+数字'，例如：1+2"
    )
]

# 2. 重构Prompt模板
prompt = PromptTemplate.from_template("""
你是一个帮助用户解决问题的助手。你可以使用以下工具：

{tools}

可用工具: {tool_names}

请严格按照以下格式回答，每个步骤都必须包含：

1. 首先分析问题（Thought）
2. 然后选择工具（Action）
3. 提供工具输入（Action Input）
4. 观察工具输出（Observation）
5. 最后给出最终答案（Final Answer）

重要提示：
- 在得到工具的输出后，必须立即给出Final Answer
- 不要重复使用工具
- 每个问题只需要使用一次工具
- 如果看到工具的输出，必须给出Final Answer
- 不要等待或思考，直接给出Final Answer

示例格式：
Question: 计算 1 + 2 等于多少？

Thought: 这是一个简单的加法问题，我需要使用SimpleAdd工具来计算
Action: SimpleAdd
Action Input: 1+2
Observation: 3
Thought: 工具已经给出了结果3，现在我可以给出最终答案
Final Answer: 1加2等于3

{agent_scratchpad}

现在开始：

Question: {input}
""")

# 创建llm
BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL = "qwen-turbo"
API_KEY = os.getenv('DASHSCOPE_API_KEY')
llm = ChatOpenAI(
    model= MODEL,  # 默认的大模型为GPT-3.5-turbo，比较便宜
    openai_api_base= BASE_URL,
    openai_api_key= API_KEY
)

# 创建agent
agent = create_react_agent(
    llm=llm,
    tools=tools,
    prompt=prompt
)

# 执行
agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=1,  # 限制为1次迭代
    handle_parsing_errors=True,  # 添加错误处理
    return_intermediate_steps=True  # 返回中间步骤
)

# 运行
result = agent_executor.invoke({
    "input": "计算 1 + 2 等于多少？",
    "tools": "\n".join([f"{tool.name}: {tool.description}" for tool in tools]),
    "tool_names": ", ".join([tool.name for tool in tools])
})

print("最终输出：", result["output"])
print("\n中间步骤：")
for step in result.get("intermediate_steps", []):
    print(step) 