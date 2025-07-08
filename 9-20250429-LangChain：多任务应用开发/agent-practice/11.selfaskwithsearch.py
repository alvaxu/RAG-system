# #本程序调用agent的方式是：agent = initialize_agent(
   
#      agent=AgentType.SELF_ASK_WITH_SEARCH,
#     )

from langchain.agents import initialize_agent, AgentType
from langchain_community.utilities import SerpAPIWrapper
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from langchain.prompts import PromptTemplate
import os

# 需要设置SerpAPI的API key
#os.environ["SERPAPI_API_KEY"] = "your_api_key"  # 替换为实际key
os.environ["SERPAPI_API_KEY"] = 'ffa9e338c18a30be872535b13b1c4366eaa6ccf0f6625533b1a1dc84cfe99c04' 

# 1. 创建llm
BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL = "qwen-turbo"
API_KEY = os.getenv('DASHSCOPE_API_KEY')
llm = ChatOpenAI(
    model=MODEL,
    openai_api_base=BASE_URL,
    openai_api_key=API_KEY,
    temperature=0  # 降低随机性
)

# 2. 配置搜索工具（需 SerpAPI Key）
search = SerpAPIWrapper() 
tools = [
    Tool(
        name="Intermediate Answer",
        func=search.run,
        description="用于搜索事实性问题的答案。输入应该是一个具体的搜索查询。",
    )
]

# 3. 定义自定义Prompt模板
template = """问题: {input}

让我们一步一步地思考这个问题。

首先，我们需要确定需要搜索的具体问题。
然后，使用搜索工具来获取信息。
最后，基于搜索结果给出完整的答案。

搜索工具: {agent_scratchpad}

请按照以下格式回答：

思考: [你的思考过程]
搜索: [具体的搜索查询]
中间答案: [搜索结果]
最终答案: [完整的答案]

注意：
- 确保搜索查询具体且明确
- 如果信息不完整，继续提出新的搜索查询
- 最终答案必须包含所有重要信息

最终答案:"""

prompt = PromptTemplate(
    input_variables=["input", "agent_scratchpad"],
    template=template
)

# 4. 创建Agent
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.SELF_ASK_WITH_SEARCH,
    verbose=True,
    handle_parsing_errors=True,  # 添加错误处理
    max_iterations=5,  # 增加迭代次数以支持更多轮次的问答
    early_stopping_method="generate",  # 添加提前停止方法
    prompt=prompt  # 使用自定义prompt
)

# 5. 执行示例
print("=== 搜索任务 ===")
try:
    result = agent.invoke({
        "input": "特斯拉的CEO是谁？他目前还领导哪些公司？"
    })
    print("\n最终答案：", result["output"])
except Exception as e:
    print(f"\n执行过程中出现错误: {str(e)}")
