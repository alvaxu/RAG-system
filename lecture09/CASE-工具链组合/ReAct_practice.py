from langchain.agents import create_react_agent, AgentExecutor
from langchain.tools import BaseTool
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain_community.llms import Tongyi
import json
import csv
from io import StringIO
from typing import Dict, Any, List, Optional, Type
import os

# 文本分析工具
class TextAnalysisTool(BaseTool):
    name: str = "text_analysis"
    description: str = "分析文本内容，提取统计信息和情感倾向"

    def _run(self, text: str) -> str:
        # 统计信息
        char_count = len(text)
        word_count = len(text.split())
        line_count = len(text.split('\n'))
        
        # 简单情感分析（示例实现）
        positive_words = ['好', '喜欢', '棒', '推荐', '合理']
        negative_words = ['差', '讨厌', '糟糕', '贵', '不推荐']
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            sentiment = "积极"
        elif negative_count > positive_count:
            sentiment = "消极"
        else:
            sentiment = "中性"
            
        return f"""统计信息：
- 字符数：{char_count}
- 词数：{word_count}
- 行数：{line_count}
情感倾向：{sentiment}"""

# 数据转换工具
class DataConversionTool(BaseTool):
    name: str = "data_conversion"
    description: str = "在JSON和CSV格式之间转换数据"

    def _run(self, data: str, target_format: str) -> str:
        if target_format.lower() == "json":
            # CSV转JSON
            csv_file = StringIO(data)
            reader = csv.DictReader(csv_file)
            json_data = json.dumps(list(reader), ensure_ascii=False, indent=2)
            return json_data
        elif target_format.lower() == "csv":
            # JSON转CSV
            json_data = json.loads(data)
            if not json_data:
                return ""
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=json_data[0].keys())
            writer.writeheader()
            writer.writerows(json_data)
            return output.getvalue()
        else:
            return "不支持的格式转换"

# 文本处理工具
class TextProcessingTool(BaseTool):
    name: str = "text_processing"
    description: str = "提供文本处理功能，如统计行数、查找文本和替换文本"

    def _run(self, text: str, operation: str, **kwargs) -> str:
        if operation == "count_lines":
            return str(len(text.split('\n')))
        elif operation == "find_text":
            search_text = kwargs.get('search_text', '')
            return str(text.count(search_text))
        elif operation == "replace_text":
            old_text = kwargs.get('old_text', '')
            new_text = kwargs.get('new_text', '')
            return text.replace(old_text, new_text)
        else:
            return "不支持的操作"

def create_tool_chain():
    # 创建工具实例
    tools = [
        TextAnalysisTool(),
        DataConversionTool(),
        TextProcessingTool()
    ]
    
    # 初始化大语言模型
    DASHSCOPE_API_KEY = 'sk-882e296067b744289acf27e6e20f3ec0'
    llm = Tongyi(
        model_name="qwen-turbo",
        dashscope_api_key=DASHSCOPE_API_KEY 
    )
    
    # 创建提示模板
    template = """你是一个有用的AI助手，可以使用以下工具:
    {tools}
    可用工具名称: {tool_names}

    使用以下格式:
    问题: 你需要回答的问题
    思考: 你应该始终思考要做什么
    行动: 要使用的工具名称，必须是 [{tool_names}] 中的一个
    行动输入: 工具的输入
    观察: 工具的结果
    ... (这个思考/行动/行动输入/观察可以重复 N 次)
    思考: 我现在已经有了最终答案
    回答: 对原始问题的最终回答

    开始!
    问题: {input}
    思考: {agent_scratchpad}"""
    
    prompt = PromptTemplate.from_template(template)
    
    # 创建agent
    agent = create_react_agent(llm, tools, prompt)
    
    # 创建代理执行器
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
        handle_parsing_errors=False  # 关闭自动重试, True会严格检查重试
    )
    
    return agent_executor

def process_task(task_description: str) -> str:
    try:
        agent_executor = create_tool_chain()
        result = agent_executor.invoke({"input": task_description})
        return result["output"]
    except Exception as e:
        return f"处理任务时出错: {str(e)}"

if __name__ == "__main__":
    # 示例任务
    task1 = """分析以下文本的情感倾向，并统计其中的行数：
    '这个产品非常好用，我很喜欢它的设计，使用体验非常棒！
    价格也很合理，推荐大家购买。
    客服态度也很好，解答问题很及时。'"""
    print("任务1:", task1)
    result = process_task(task1)
    print("任务执行结果：")
    print(result) 