import os
from langchain_community.llms import Tongyi
from langchain_community.tools import Tool
from langchain_community.utilities import SerpAPIWrapper
from langchain.chains import LLMMathChain
from langgraph.graph import Graph
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

# 设置SerpAPI密钥
os.environ["SERPAPI_API_KEY"] = "0d5f2fc3573b1017a130e75b5ce659e9bd7d4badb9bc9246225059820cf1cb9b"

# 设置通义千问API密钥
DASHSCOPE_API_KEY = 'sk-882e296067b744289acf27e6e20f3ec0'

# 加载模型
llm = Tongyi(model_name="qwen-turbo", dashscope_api_key=DASHSCOPE_API_KEY)

# 创建SerpAPI工具
search = SerpAPIWrapper()

# 创建数学计算工具
math_chain = LLMMathChain.from_llm(llm=llm)

# 定义工具列表
tools = [
    Tool(
        name="Search",
        func=search.run,
        description="用于查询当前事件、天气、温度等信息"
    ),
    Tool(
        name="Calculator",
        func=math_chain.run,
        description="用于执行数学计算，特别是温度转换和分数计算"
    )
]

# 创建提示模板
prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="""你是一个助手，可以帮助用户回答问题。当用户的问题需要搜索信息或进行数学计算时，你应该使用相应的工具。
请按照以下格式回答：
1. 如果需要搜索，请使用以下格式：
   SEARCH: [搜索查询]
2. 如果需要计算，请使用以下格式：
   CALCULATE: [计算表达式]

例如：
用户：北京现在的温度是多少？
助手：SEARCH: current temperature in Beijing

用户：计算 20 的 1/4
助手：CALCULATE: 20/4

用户：你好
助手：你好！有什么我可以帮你的吗？"""),
    MessagesPlaceholder(variable_name="messages"),
])

# 创建最终答案生成模板
final_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="""你是一个助手，需要根据搜索结果和计算结果生成一个完整的、友好的回答。
请将信息整合成一个连贯的回答，使用中文回答用户的问题。
如果涉及温度转换，请确保在回答中包含华氏度和摄氏度的换算。"""),
    MessagesPlaceholder(variable_name="messages"),
])

# 创建处理函数
def process_with_llm(state):
    print("LLM节点处理中...")
    messages = state["messages"]
    response = llm.invoke(prompt.format_messages(messages=messages))
    print(f"LLM响应: {response}")
    return {"messages": messages + [AIMessage(content=response)], "should_continue": True}

def process_with_tool(state):
    print("工具节点处理中...")
    messages = state["messages"]
    last_message = messages[-1]
    if isinstance(last_message, AIMessage):
        content = last_message.content.strip()
        print(f"工具节点收到的内容: {content}")
        
        try:
            if content.startswith("SEARCH:"):
                # 提取搜索查询
                query = content[7:].strip()
                print(f"执行搜索查询: {query}")
                tool_response = tools[0].run(query)
                print(f"搜索响应: {tool_response}")
                
            elif content.startswith("CALCULATE:"):
                # 提取计算表达式
                expression = content[10:].strip()
                print(f"执行计算: {expression}")
                tool_response = tools[1].run(expression)
                print(f"计算结果: {tool_response}")
                
            else:
                # 如果不是工具请求，直接返回LLM的回答
                print("不是工具请求，直接返回LLM回答")
                return {"messages": messages + [HumanMessage(content=content)], "should_continue": False}
            
            # 生成最终答案
            final_response = llm.invoke(final_prompt.format_messages(
                messages=messages + [HumanMessage(content=tool_response)]
            ))
            print(f"最终答案: {final_response}")
            
            # 返回最终答案
            return {"messages": messages + [HumanMessage(content=final_response)], "should_continue": False}
            
        except Exception as e:
            print(f"工具执行错误: {str(e)}")
            return {"messages": messages + [HumanMessage(content=f"执行失败: {str(e)}")], "should_continue": False}
            
    return state

def end(state):
    print("工作流结束")
    print(f"最终状态: {state}")
    return state

# 创建LangGraph工作流
workflow = Graph()

# 添加节点
workflow.add_node("llm", process_with_llm)
workflow.add_node("tool", process_with_tool)
workflow.add_node("end", end)

# 设置边
def should_continue(state):
    should = state.get("should_continue", True)
    print(f"检查是否继续: {should}")
    return should

workflow.add_conditional_edges(
    "llm",
    should_continue,
    {
        True: "tool",
        False: "end"
    }
)

workflow.add_conditional_edges(
    "tool",
    should_continue,
    {
        True: "llm",
        False: "end"
    }
)

# 设置入口点
workflow.set_entry_point("llm")

# 编译工作流
app = workflow.compile()

# 运行工作流
print("开始运行工作流...")
result = app.invoke({
    "messages": [
        HumanMessage(content="当前北京的温度是多少华氏度？这个温度的1/4是多少")
    ]
})

# 打印最终状态
print("\n工作流状态:")
print(result)

# 获取最后一条消息
if result and "messages" in result and result["messages"]:
    last_message = result["messages"][-1]
    print("\n最终回答:")
    print(last_message.content)
else:
    print("\n没有获取到有效的回答") 