# #本程序调用agent的方式是：agent = initialize_agent(
   
#      agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
#     )
from langchain.agents import AgentType, initialize_agent
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory
import math,os
from typing import Dict, List, Union
import json

# 1. 定义结构化工具集
def get_employee_info(employee_id: str) -> Dict[str, str]:
    """获取员工基本信息"""
    employee_db = {
        "1001": {"name": "张三", "department": "研发部", "position": "高级工程师"},
        "1002": {"name": "李四", "department": "市场部", "position": "市场经理"},
        "1003": {"name": "王五", "department": "财务部", "position": "会计"}
    }
    return employee_db.get(employee_id, {"error": "员工不存在"})

def calculate_salary(base: float, bonus: float, tax_rate: float) -> Dict[str, float]:
    """计算薪资"""
    gross = base + bonus
    tax = gross * tax_rate
    net = gross - tax
    return {
        "gross_salary": round(gross, 2),
        "tax": round(tax, 2),
        "net_salary": round(net, 2)
    }

def get_department_employees(department: str) -> List[Dict[str, str]]:
    """获取部门员工列表"""
    department_db = {
        "研发部": [
            {"id": "1001", "name": "张三", "position": "高级工程师"},
            {"id": "1004", "name": "赵六", "position": "初级工程师"}
        ],
        "市场部": [
            {"id": "1002", "name": "李四", "position": "市场经理"},
            {"id": "1005", "name": "钱七", "position": "市场专员"}
        ],
        "财务部": [
            {"id": "1003", "name": "王五", "position": "会计"}
        ]
    }
    return department_db.get(department, [])

# 2. 创建工具实例
def parse_department_input(input_str: str) -> str:
    """解析部门输入参数"""
    try:
        # 尝试解析JSON输入
        params = json.loads(input_str)
        if isinstance(params, dict) and "department" in params:
            return params["department"]
        elif isinstance(params, dict) and "department_name" in params:
            return params["department_name"]
        return input_str
    except:
        # 如果不是JSON，直接返回输入字符串
        return input_str

tools = [
    Tool(
        name="GetEmployeeInfo",
        func=lambda x: str(get_employee_info(x)),
        description="根据员工ID获取员工详细信息，输入应为员工ID字符串"
    ),
    Tool(
        name="CalculateSalary",
        func=lambda x: str(calculate_salary(**eval(x))),
        description="计算薪资，输入应为字典格式的JSON字符串，包含base(基本工资), bonus(奖金), tax_rate(税率)字段"
    ),
    Tool(
        name="GetDepartmentEmployees",
        func=lambda x: str(get_department_employees(parse_department_input(x))),
        description="获取部门所有员工列表，输入可以是部门名称字符串或JSON格式（包含department或department_name字段）"
    )
]

# 3. 初始化记忆和LLM
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
    input_key="input",
    output_key="output"
)

BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL = "qwen-turbo"
API_KEY = os.getenv('DASHSCOPE_API_KEY')
llm = ChatOpenAI(
    model=MODEL,
    openai_api_base=BASE_URL,
    openai_api_key=API_KEY,
    temperature=0  # 降低随机性
)

# 4. 创建结构化聊天代理
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    memory=memory,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=3
)

# 5. 执行多轮结构化对话
print("===== 第一轮：查询员工信息 =====")
response1 = agent.run({"input": "请查询员工ID 1001的信息"})
print(response1)

print("\n===== 第二轮：薪资计算 =====")
response2 = agent.run({"input": "假设这位员工的基本工资是15000，奖金3000，税率0.2，请计算他的税后薪资"})
print(response2)

print("\n===== 第三轮：部门查询 =====")
response3 = agent.run({"input": "请列出研发部的所有员工"})
print(response3)

print("\n===== 第四轮：综合问题 =====")
response4 = agent.run({"input": "根据之前查询的研发部员工信息，计算研发部所有员工的基本工资总和，假设每人基本工资都是15000"})
print(response4)