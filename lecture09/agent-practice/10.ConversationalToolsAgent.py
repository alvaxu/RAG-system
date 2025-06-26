# #本程序调用agent的方式是：agent = initialize_agent(
   
#     agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
#     )
from langchain.agents import Tool, AgentExecutor, initialize_agent
from langchain.agents.agent_types import AgentType
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain_community.utilities import SerpAPIWrapper
from langchain.chains import LLMMathChain
from langchain.agents import load_tools
import os

os.environ["SERPAPI_API_KEY"] = 'ffa9e338c18a30be872535b13b1c4366eaa6ccf0f6625533b1a1dc84cfe99c04' 

# 1. 定义自定义工具函数
def get_word_length(word: str) -> str:
    """计算字符串长度"""
    try:
        # 移除所有空格和引号
        word = word.strip().strip('"\'')
        return str(len(word))
    except Exception as e:
        return f"计算失败：{str(e)}"

def get_temperature_difference(cities: str) -> str:
    """计算两个城市的温度差"""
    try:
        # 分割输入字符串获取两个城市名
        city1, city2 = [city.strip() for city in cities.split(',')]
        
        # 使用serpapi查询两个城市的温度
        search = SerpAPIWrapper()
        temp1 = search.run(f"{city1} 今天温度")
        temp2 = search.run(f"{city2} 今天温度")
        
        # 提取温度数值（假设温度格式为"XX°C"）
        temp1 = int(temp1.split('°')[0])
        temp2 = int(temp2.split('°')[0])
        
        # 计算温度差
        diff = abs(temp1 - temp2)
        return f"{city1}和{city2}的温度差是{diff}°C"
    except Exception as e:
        return f"计算温度差失败：{str(e)}"

# 2. 创建LLM
BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL = "qwen-turbo"
API_KEY = os.getenv('DASHSCOPE_API_KEY')
llm = ChatOpenAI(
    model= MODEL,  # 默认的大模型为GPT-3.5-turbo，比较便宜
    openai_api_base= BASE_URL,
    openai_api_key= API_KEY
)

# 3. 加载内置工具
builtin_tools = load_tools(
    ["serpapi", "llm-math"],
    llm=llm
)

# 4. 创建自定义工具
custom_tools = [
    Tool(
        name="WordLength",
        func=get_word_length,
        description="计算字符串长度，输入一个字符串，返回它的字符数"
    ),
    Tool(
        name="TemperatureDiff",
        func=get_temperature_difference,
        description="计算两个城市的温度差，输入格式为'城市1,城市2'，例如：'北京,上海'"
    )
]

# 5. 合并所有工具
tools = builtin_tools + custom_tools

# 6. 创建memory
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

# 7. 创建agent
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    verbose=True,
    memory=memory,
    handle_parsing_errors=True
)

# 8. 打印欢迎信息和使用说明
print("欢迎使用智能助手！我可以帮你：")
print("1. 查询历史人物信息（使用serpapi）")
print("2. 进行数学计算（使用llm-math）")
print("3. 计算字符串长度（使用WordLength工具）")
print("4. 计算两个城市的温度差（使用TemperatureDiff工具）")
print("5. 回答其他问题（如果工具可用）")
print("\n示例问题：")
print("- 历史上今天出生的两个最重要的人是谁？")
print("- 计算 123 + 456 等于多少？")
print("- 单词'hello'的长度是多少？")
print("- 北京和上海今天的温度差是多少？")
print("\n输入 'quit' 或 'exit' 退出对话")
print("-" * 50)

# 9. 开始对话循环
while True:
    try:
        # 获取用户输入
        user_input = input("\n请输入你的问题: ").strip()
        
        # 检查是否退出
        if user_input.lower() in ['quit', 'exit']:
            print("感谢使用，再见！")
            break
        
        # 如果输入为空，继续下一轮
        if not user_input:
            continue
        
        # 执行agent
        result = agent.invoke({"input": user_input})
        print("\n助手:", result["output"])
        
    except KeyboardInterrupt:
        print("\n\n程序被中断，正在退出...")
        break
    except Exception as e:
        print(f"\n发生错误：{str(e)}")
        print("请尝试用其他方式提问，或输入 'quit' 退出程序") 