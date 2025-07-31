# #本程序调用agent的方式是：agent = initialize_agent(
   
#     agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
#     )

from langchain.agents import Tool, initialize_agent, AgentType
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain_community.utilities import SerpAPIWrapper
from langchain.chains import LLMMathChain
import os


SERPAPI_API_KEY = os.getenv('SERPAPI_API_KEY')

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

# 2. 创建工具列表
# 创建serpapi工具
search = SerpAPIWrapper()
serpapi_tool = Tool(
    name="Search",
    func=search.run,
    description="用于搜索信息的工具，可以查询历史人物、天气等信息"
)

# 创建llm-math工具
BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL = "qwen-turbo"
API_KEY = os.getenv('DASHSCOPE_API_KEY')
llm = ChatOpenAI(
    model= MODEL,  # 默认的大模型为GPT-3.5-turbo，比较便宜
    openai_api_base= BASE_URL,
    openai_api_key= API_KEY
)
math_chain = LLMMathChain.from_llm(llm=llm)
math_tool = Tool(
    name="Calculator",
    func=math_chain.run,
    description="用于进行数学计算的工具，可以处理各种数学运算"
)

# 创建自定义工具
word_length_tool = Tool(
    name="WordLength",
    func=get_word_length,
    description="计算字符串长度，输入一个字符串，返回它的字符数"
)

temp_diff_tool = Tool(
    name="TemperatureDiff",
    func=get_temperature_difference,
    description="计算两个城市的温度差，输入格式为'城市1,城市2'，例如：'北京,上海'"
)

tools = [serpapi_tool, math_tool, word_length_tool, temp_diff_tool]


## 3. 创建ZeroShotAgent的提示模板
# prefix = """你是一个帮助用户解决问题的助手。你可以使用以下工具：

# {tools}

# 请使用以下格式：

# Question: 输入的问题
# Thought: 你需要思考如何解决这个问题
# Action: 要使用的工具名称
# Action Input: 工具的输入
# Observation: 工具的输出
# ... (这个思考/行动/观察可以重复多次)
# Thought: 我现在知道最终答案
# Final Answer: 对原始输入问题的最终答案

# 重要提示：
# 1. 如果问题涉及多个步骤，你需要一步步思考
# 2. 可以使用一个工具的输出作为另一个工具的输入
# 3. 在得到所有需要的结果后，给出最终答案
# 4. 记住之前的对话历史，可以在需要时使用之前的结果
# 5. 使用TemperatureDiff工具时，输入格式必须是'城市1,城市2'，例如：'北京,上海'

# 对话历史：
# {chat_history}

# 现在开始：

# Question: {input}
# """

# suffix = """
# {agent_scratchpad}
# """

# 创建memory
memory = ConversationBufferMemory(
    memory_key="chat_history",
    input_key="input",
    output_key="output",
    return_messages=True
)

# 创建agent

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    memory=memory,
    handle_parsing_errors=True,
    max_iterations=10,
    early_stopping_method="generate",
 )

# 5. 运行交互式对话
def print_welcome_message():
    print("\n欢迎使用智能助手！我可以帮您：")
    print("1. 查询信息（如历史人物、天气等）")
    print("2. 进行数学计算")
    print("3. 计算字符串长度")
    print("4. 计算两个城市之间的温度差")
    print("\n您可以随时输入 'quit' 或 'exit' 退出对话。")
    print("=" * 50)

def main():
    print_welcome_message()
    
    while True:
        try:
            user_input = input("\n请输入您的问题: ").strip()
            
            if user_input.lower() in ['quit', 'exit']:
                print("\n感谢使用，再见！")
                break
                
            if not user_input:
                print("请输入有效的问题！")
                continue
                
            result = agent.invoke({
                "input": user_input
            })
            print("\n助手回答：", result["output"])
            
        except KeyboardInterrupt:
            print("\n\n程序被中断，正在退出...")
            break
        except Exception as e:
            print(f"\n发生错误：{str(e)}")
            print("请重新输入您的问题。")

if __name__ == "__main__":
    main() 