#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
程序说明：
## 1. 本程序基于ZeroShotAgent实现，显式定义memory和prompt，适配私募基金问答场景。
## 2. 参考agent.md中zeroshotagent模式，功能与fund_qa_langgraph_practice_single.py一致，但采用ZeroShotAgent结构，便于自定义prompt和memory。
'''

import re
from typing import List, Dict, Any
from langchain.agents import Tool, AgentExecutor, ZeroShotAgent
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain_community.llms import Tongyi
from langchain import LLMChain
import os

# 通义千问API密钥
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")

# ================== 数据源与工具定义 ==================
FUND_RULES_DB = [
    {
        "id": "rule001",
        "category": "设立与募集",
        "question": "私募基金的合格投资者标准是什么？",
        "answer": "合格投资者是指具备相应风险识别能力和风险承担能力，投资于单只私募基金的金额不低于100万元且符合下列条件之一的单位和个人：\n1. 净资产不低于1000万元的单位\n2. 金融资产不低于300万元或者最近三年个人年均收入不低于50万元的个人"
    },
    {
        "id": "rule002",
        "category": "设立与募集",
        "question": "私募基金的最低募集规模要求是多少？",
        "answer": "私募证券投资基金的最低募集规模不得低于人民币1000万元。对于私募股权基金、创业投资基金等其他类型的私募基金，监管规定更加灵活，通常需符合基金合同的约定。"
    },
    {
        "id": "rule014",
        "category": "监管规定",
        "question": "私募基金管理人的风险准备金要求是什么？",
        "answer": "私募证券基金管理人应当按照管理费收入的10%计提风险准备金，主要用于赔偿因管理人违法违规、违反基金合同、操作错误等给基金财产或者投资者造成的损失。"
    }
]

class FundRulesDataSource:
    """
    :function: 私募基金规则数据源，提供关键词搜索、类别查询和直接问答
    """
    def __init__(self):
        self.rules_db = FUND_RULES_DB

    def search_rules_by_keywords(self, keywords: str) -> str:
        """
        :function: 通过关键词搜索相关私募基金规则
        :param keywords: 关键词
        :return: 匹配到的规则文本
        """
        keywords = keywords.strip().lower()
        keyword_list = re.split(r'[,，\s]+', keywords)
        matched_rules = []
        for rule in self.rules_db:
            rule_text = (rule["category"] + " " + rule["question"]).lower()
            match_count = sum(1 for kw in keyword_list if kw in rule_text)
            if match_count > 0:
                matched_rules.append((rule, match_count))
        matched_rules.sort(key=lambda x: x[1], reverse=True)
        if not matched_rules:
            return "未找到与关键词相关的规则。"
        result = []
        for rule, _ in matched_rules[:2]:
            result.append(f"类别: {rule['category']}\n问题: {rule['question']}\n答案: {rule['answer']}")
        return "\n\n".join(result)

    def search_rules_by_category(self, category: str) -> str:
        """
        :function: 根据规则类别查询私募基金规则
        :param category: 类别
        :return: 匹配到的规则文本
        """
        category = category.strip()
        matched_rules = []
        for rule in self.rules_db:
            if category.lower() in rule["category"].lower():
                matched_rules.append(rule)
        if not matched_rules:
            return f"未找到类别为 '{category}' 的规则。"
        result = []
        for rule in matched_rules:
            result.append(f"问题: {rule['question']}\n答案: {rule['answer']}")
        return "\n\n".join(result)

    def answer_question(self, query: str) -> str:
        """
        :function: 直接回答用户关于私募基金的问题
        :param query: 用户问题
        :return: 答案
        """
        query = query.strip()
        best_rule = None
        best_score = 0
        for rule in self.rules_db:
            query_words = set(query.lower().split())
            rule_words = set((rule["question"] + " " + rule["category"]).lower().split())
            common_words = query_words.intersection(rule_words)
            score = len(common_words) / max(1, len(query_words))
            if score > best_score:
                best_score = score
                best_rule = rule
        if best_score < 0.2 or best_rule is None:
            missing_topic = self._identify_missing_topic(query)
            prompt = OUTSIDE_KNOWLEDGE_PROMPT.format(
                query=query,
                missing_topic=missing_topic
            )
            # 让LLM生成最终的“知识库外”回答
            return llm(prompt)
        return best_rule["answer"]

    def _identify_missing_topic(self, query: str) -> str:
        """
        :function: 识别查询中缺失的知识主题
        :param query: 用户问题
        :return: 主题
        """
        query = query.lower()
        if "投资" in query and "资产" in query:
            return "私募基金可投资的资产类别"
        elif "公募" in query and "区别" in query:
            return "私募基金与公募基金的区别"
        elif "退出" in query and ("机制" in query or "方式" in query):
            return "创业投资基金的退出机制"
        elif "费用" in query and "结构" in query:
            return "私募基金的费用结构"
        elif "托管" in query:
            return "私募基金资产托管"
        return "您所询问的具体主题"

# ================== 工具函数定义 ==================
fund_rules_source = FundRulesDataSource()

tool_keywords = Tool(
    name="关键词搜索",
    func=fund_rules_source.search_rules_by_keywords,
    description="通过关键词搜索私募基金规则，输入应为相关关键词"
)
tool_category = Tool(
    name="类别查询",
    func=fund_rules_source.search_rules_by_category,
    description="查询特定类别的私募基金规则，输入应为类别名称。类别名称有：设立与募集, 监管规定"
)
tool_answer = Tool(
    name="回答问题",
    func=fund_rules_source.answer_question,
    description="直接回答用户关于私募基金的问题，输入应为完整的用户问题"
)

tools = [tool_keywords, tool_category, tool_answer]
tools_description = "\n".join([
    f"{tool.name}: {tool.description}" for tool in tools
]) + "\n\n特别说明：如果多次查询后仍未获得答案，请务必使用‘回答问题’工具尝试直接获取答案。"

# ================== memory定义 ==================
memory = ConversationBufferMemory(
    memory_key="chat_history",
    input_key="input",
    output_key="output",
    return_messages=True
)

# ================== OUTSIDE_KNOWLEDGE_PROMPT定义 ==================
OUTSIDE_KNOWLEDGE_TMPL = '''
你是私募基金问答助手。用户的问题是关于私募基金的，但我们的知识库中没有直接相关的信息。
请首先明确告知用户"对不起，在我的知识库中没有关于{missing_topic}的详细信息"，
然后，如果你有相关知识，可以以"根据我的经验"或"一般来说"等方式提供一些通用信息，
并建议用户查阅官方资料或咨询专业人士获取准确信息。

用户问题：{query}
缺失的知识主题：{missing_topic}
'''
OUTSIDE_KNOWLEDGE_PROMPT = PromptTemplate(
    input_variables=["query", "missing_topic"],
    template=OUTSIDE_KNOWLEDGE_TMPL,
)

# ================== prompt定义 ==================
prefix = (
    """
你是一个帮助用户解决私募基金相关问题的助手。你可以使用以下工具：

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
5. 回答要专业、简洁、准确
6. 如果工具返回内容中包含“在我的知识库中没有关于”或“超出了我的知识范围”，你必须直接将该 Observation的完整内容原模原样作为 Final Answer，不允许再进行任何总结、润色或补充。

对话历史：
{chat_history}

现在开始：

Question: {input}
"""
)
suffix = """\n{agent_scratchpad}\n"""

prompt = PromptTemplate(
    input_variables=["input", "chat_history", "agent_scratchpad", "tools"],
    template=prefix + suffix
)

# ================== agent定义 ==================
llm = Tongyi(model_name="Qwen-Turbo-2025-04-28", dashscope_api_key=DASHSCOPE_API_KEY)
llm_chain = LLMChain(llm=llm, prompt=prompt)
agent = ZeroShotAgent(
    llm_chain=llm_chain,
    tools=tools,
    verbose=True
)

# ================== agent执行器 ==================
agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=10,
    memory=memory
)

# ================== 主程序 ==================
def print_welcome_message():
    print("\n欢迎使用私募基金运作指引问答助手（ZeroShotAgent版）！我可以帮您：")
    print("1. 查询私募基金相关规则（如合格投资者、募集规模等）")
    print("2. 通过关键词或类别查询规则")
    print("3. 直接提问私募基金相关问题\n")
    print("您可以随时输入 'quit' 或 'exit' 退出对话。")
    print("=" * 50)

def main():
    print_welcome_message()
    while True:
        try:
            user_input = input("\n请输入您的问题: ").strip()
            if user_input.lower() in ['quit', 'exit', '退出']:
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

if __name__ == "__main__":
    main() 