#### 1. 采用zeroshotagent，需要显式定义memory、prompt.

基本步骤：

​	(1)  定义工具函数：

```python
# 计算字符串长度的工具
def get_word_length(word: str) -> str:
    """计算字符串长度"""
    try:
        # 移除所有空格和引号
        word = word.strip().strip('"\'')
        return str(len(word))
    except Exception as e:
        return f"计算失败：{str(e)}"
# SerpAPI 网址查询工具   
from langchain_community.utilities import SerpAPIWrapper
search = SerpAPIWrapper() 
# 计算温差工具
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
```



​	(2) 描述工具

```python
word_length_tool = Tool(
    name="WordLength",
    func=get_word_length,
    description="计算字符串长度，输入一个字符串，返回它的字符数"
)
serpapi_tool = Tool(
    name="Search",
    func=search.run,
    description="用于搜索信息的工具，可以查询历史人物、天气等信息"
)
temp_diff_tool = Tool(
    name="TemperatureDiff",
    func=get_temperature_difference,
    description="计算两个城市的温度差，输入格式为'城市1,城市2'，例如：'北京,上海'"
)
```



​	(3) 定义工具列表

```python
tools = [word_length_tool,serpapi_tool,temp_diff_tool]
tools_description = "\n".join([f"{tool.name}: {tool.description}" for tool in tools])
```



​	(4) 定义memory

```python
# 创建memory
memory = ConversationBufferMemory(
    memory_key="chat_history",
    input_key="input",
    output_key="output",
    return_messages=True
)
```



​	(5) 定义prompt

```python
# 创建建ZeroShotAgent的提示模板
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
5. 使用TemperatureDiff工具时，输入格式必须是'城市1,城市2'，例如：'北京,上海'

对话历史：
{chat_history}

现在开始：

Question: {input}
"""

suffix = """
{agent_scratchpad}
"""
```



​	(6) 创建agent

```python
# 创建agent
agent = ZeroShotAgent(
    llm_chain=LLMChain(llm=llm, prompt=PromptTemplate.from_template(prefix + suffix)),
    tools=tools,
    verbose=True
)

```



​	(7) 定义agent 执行的方法和参数

```python
agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=10,
    memory=memory
)
```



​	(8) invoke agent

```python
def print_welcome_message():
    print("\n欢迎使用智能助手！我可以帮您：")
    print("1. 查询信息（如历史人物、天气等）")
    print("2. 计算字符串长度")
    print("3. 计算两个城市之间的温度差")
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
                
            result = agent_executor.invoke({
                "input": user_input,
                "tools": tools_description
            })
            print("\n助手回答：", result["output"])
            
        except KeyboardInterrupt:
            print("\n\n程序被中断，正在退出...")
            break
        except Exception as e:
            print(f"\n发生错误：{str(e)}")
            print("请重新输入您的问题。")
```

​	(9) 主程序

```python
if __name__ == "__main__":
    main() 
```

#### 2. 采用ZeroshotReactDescription，无须显式定义prompt.


基本步骤：

​	(1)  定义工具函数(同上）：

​	(2) 描述工具(同上)

​	(3) 定义工具列表(同上)

​	(4) 定义memory

​	(5) 定义prompt(无需定义)：使用的默认prompt为

```python
PREFIX = """Answer the following questions as best you can. You have access to the following tools:"""
FORMAT_INSTRUCTIONS = """Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question"""
SUFFIX = """Begin!

Question: {input}
Thought:{agent_scratchpad}"""
```

可以通过自定义Prompt ，并在initial agent时通过参数传递prompt,具体方法可以问AI。

​	(6) 创建agent(不同)

```python
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

```



​	(7) 定义agent 执行的方法和参数(无此步骤)

​	(8) invoke agent

```python
def print_welcome_message():
    print("\n欢迎使用智能助手！我可以帮您：")
    print("1. 查询信息（如历史人物、天气等）")
    print("2. 计算字符串长度")
    print("3. 计算两个城市之间的温度差")
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
                
            # result = agent_executor.invoke({
            #    "input": user_input,
            #    "tools": tools_description
            # })
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
```

​	(9) 主程序

```python
if __name__ == "__main__":
    main() 
```