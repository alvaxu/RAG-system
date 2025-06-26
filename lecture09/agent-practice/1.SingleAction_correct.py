from langchain.agents import Tool, LLMSingleActionAgent, AgentExecutor
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
import os

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


# ========== ReAct风格Prompt与Parser ===========
from langchain.prompts import StringPromptTemplate

REACT_AGENT_TMPL = """你是一个帮助用户解决问题的助手。

你可以使用以下工具：

{tools}

按照以下格式回答问题：
---
Question: 用户的问题
Thought: 我需要思考如何回答这个问题
Action: 工具名称
Action Input: 工具的输入
Observation: 工具返回的结果
...（这个思考/行动/行动输入/观察可以重复几次）
Thought: 现在我知道答案了
Final Answer: 给用户的最终答案
---

注意：
1. 回答要专业、简洁、准确
2. 如果需要调用工具请严格按照格式输出，否则直接输出Final Answer

Question: {input}
{agent_scratchpad}
"""
class ReActPromptTemplate(StringPromptTemplate):
    """
    :function: ReActPromptTemplate
    :param template: 模板字符串
    :param tools: 工具列表
    :return: 格式化后的prompt
    """
    template: str
    tools: list

    def format(self, **kwargs) -> str:
        intermediate_steps = kwargs.pop("intermediate_steps")
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += action.log
            thoughts += f"\nObservation: {observation}\nThought: "
        kwargs["agent_scratchpad"] = thoughts
        kwargs["tools"] = "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])
        return self.template.format(**kwargs)

prompt = ReActPromptTemplate(
    template=REACT_AGENT_TMPL,
    tools=tools,
    input_variables=["input", "intermediate_steps"]
)


import re
from langchain.agents import AgentOutputParser
from langchain.schema import AgentAction, AgentFinish
class ReActOutputParser(AgentOutputParser):
    """
    :function: ReActOutputParser
    :param text: LLM输出
    :return: AgentAction 或 AgentFinish
    """
    def parse(self, text: str):
        # 检查Final Answer
        if "Final Answer:" in text:
            return AgentFinish(
                return_values={"output": text.split("Final Answer:")[-1].strip()},
                log=text,
            )
        # 尝试解析Action结构
        match = re.search(r"Action\s*:(.*?)\nAction Input\s*:(.*)", text, re.DOTALL)
        if match:
            action = match.group(1).strip()
            action_input = match.group(2).strip()
            return AgentAction(tool=action, tool_input=action_input, log=text)
        # 兜底：直接输出
        return AgentFinish(return_values={"output": text.strip()}, log=text)


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

output_parser = ReActOutputParser()
# 6. 定义的工具名称
tool_names = [tool.name for tool in tools]

# 7. 定义SingleActionAgent
agent = LLMSingleActionAgent(
    llm_chain=llm_chain,
    output_parser=output_parser,
    allowed_tools=tool_names,
    stop=["\nObservation:"]
)

# 8. 执行时传入工具描述
agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=5,

)

# 9. 运行（确保输入格式正确）
try:
    result = agent_executor.run("单词'hello'的长度是多少？")
    
    print(f"执行结果: {result}")

except Exception as e:
    print(f"执行过程中出现错误: {str(e)}")  
