#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
私募基金运作指引问答助手 - 反应式智能体实现

适合反应式架构的私募基金问答助手，使用Agent模式实现主动思考和工具选择。
"""

import re
from typing import List, Dict, Any, Union
from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent, AgentOutputParser, initialize_agent, AgentType
from langchain.prompts import StringPromptTemplate
from langchain_community.llms import Tongyi
from langchain import LLMChain
from langchain.schema import AgentAction, AgentFinish
from langchain.prompts import PromptTemplate
from langchain.llms.base import BaseLLM
from langchain.memory import ConversationBufferMemory
import os
# 通义千问API密钥
# DASHSCOPE_API_KEY = 'sk-882e296067b744289acf27e6e20f3ec0'
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
# 简化的私募基金规则数据库
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

# 定义上下文QA模板
CONTEXT_QA_TMPL = """
你是私募基金问答助手。请根据以下信息回答问题：

信息：{context}
问题：{query}
"""
CONTEXT_QA_PROMPT = PromptTemplate(
    input_variables=["query", "context"],
    template=CONTEXT_QA_TMPL,
)

# 定义超出知识库范围问题的回答模板
OUTSIDE_KNOWLEDGE_TMPL = """
你是私募基金问答助手。用户的问题是关于私募基金的，但我们的知识库中没有直接相关的信息。
请首先明确告知用户"对不起，在我的知识库中没有关于[具体主题]的详细信息"，
然后，如果你有相关知识，可以以"根据我的经验"或"一般来说"等方式提供一些通用信息，
并建议用户查阅官方资料或咨询专业人士获取准确信息。

用户问题：{query}
缺失的知识主题：{missing_topic}
"""
OUTSIDE_KNOWLEDGE_PROMPT = PromptTemplate(
    input_variables=["query", "missing_topic"],
    template=OUTSIDE_KNOWLEDGE_TMPL,
)

# 私募基金问答数据源
class FundRulesDataSource:
    def __init__(self, llm: BaseLLM):
        self.llm = llm
        self.rules_db = FUND_RULES_DB

    # 工具1：通过关键词搜索相关规则
    def search_rules_by_keywords(self, keywords: str) -> str:
        """通过关键词搜索相关私募基金规则"""
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

    # 工具2：根据规则类别查询
    def search_rules_by_category(self, category: str) -> str:
        """根据规则类别查询私募基金规则"""
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

    # 工具3：直接回答用户问题
    def answer_question(self, query: str) -> str:
        """直接回答用户关于私募基金的问题"""
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
            # 识别问题主题
            missing_topic = self._identify_missing_topic(query)
            prompt = OUTSIDE_KNOWLEDGE_PROMPT.format(
                query=query,
                missing_topic=missing_topic
            )
            # 直接通过LLM获取回答可能导致输出格式与Agent期望不符
            # 将回答包装为AgentFinish格式而不是返回给Agent处理
            response = self.llm(prompt)
            # 返回格式化后的回答，让Agent直接返回最终结果
            return f"这个问题超出了知识库范围。\n\n{response}"
        
        context = best_rule["answer"]
        prompt = CONTEXT_QA_PROMPT.format(query=query, context=context)
        
        return self.llm(prompt)
    
    def _identify_missing_topic(self, query: str) -> str:
        """识别查询中缺失的知识主题"""
        # 简单的主题提取逻辑
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
        # 如果无法确定具体主题，使用通用表述
        return "您所询问的具体主题"


def create_fund_qa_agent():
    # 定义LLM
    llm = Tongyi(model_name="Qwen-Turbo-2025-04-28", dashscope_api_key=DASHSCOPE_API_KEY)
    
    # 创建数据源
    fund_rules_source = FundRulesDataSource(llm)
    
    # 定义工具
    tools = [
        Tool(
            name="关键词搜索",
            func=fund_rules_source.search_rules_by_keywords,
            description="当需要通过关键词搜索私募基金规则时使用，输入应为相关关键词",
        ),
        Tool(
            name="类别查询",
            func=fund_rules_source.search_rules_by_category,
            description="当需要查询特定类别的私募基金规则时使用，输入应为类别名称。类别名称有两种：设立与募集, 监管规定",
        ),
        Tool(
            name="回答问题",
            func=fund_rules_source.answer_question,
            description="当能够直接回答用户问题时使用，输入应为完整的用户问题",
        ),
    ]
    # 创建会话记忆
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    # 使用CONVERSATIONAL_REACT_DESCRIPTION类型初始化Agent
    agent_executor = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        verbose=True,
        memory=memory,
        handle_parsing_errors=True
    )
    return agent_executor


if __name__ == "__main__":
    # 创建Agent
    fund_qa_agent = create_fund_qa_agent()
    
    print("=== 私募基金运作指引问答助手（反应式智能体）===\n")
    print("使用模型：Qwen-Turbo-2025-04-28\n")
    print("您可以提问关于私募基金的各类问题，输入'退出'结束对话\n")
    
    # 主循环
    while True:
        try:
            user_input = input("请输入您的问题：")
            if user_input.lower() in ['退出', 'exit', 'quit']:
                print("感谢使用，再见！")
                break
            
            response = fund_qa_agent.run(user_input)
            print(f"回答: {response}\n")
            print("-" * 40)
        except KeyboardInterrupt:
            print("\n程序已中断，感谢使用！")
            break
        except Exception as e:
            print(f"发生错误：{e}")
            print("请尝试重新提问或更换提问方式。") 