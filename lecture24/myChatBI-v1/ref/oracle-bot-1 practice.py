#导入必要的库
import os
import asyncio
from typing import Optional
import dashscope
from qwen_agent.agents import Assistant
from qwen_agent.gui import WebUI
import pandas as pd
from sqlalchemy import create_engine,text
from sqlalchemy.exc import SQLAlchemyError
from qwen_agent.tools.base import BaseTool, register_tool

#测试oracle连接

db_user = "dbtest"
db_password = "test"
db_host = "192.168.43.11:1521"
service_name = "FREEPDB1"
# 1.连接字符串

oracle_connection_string = f"oracle+cx_oracle://{db_user}:{db_password}@{db_host}/?service_name={service_name}"

# 创建SQLAlchemy引擎

try:
    engine = create_engine(oracle_connection_string)
    connection = engine.connect()
    print("数据库连接成功！")
    result =connection.execute(text("SELECT * FROM products FETCH FIRST 5 ROWS ONLY"))
    # 转换为DataFrame
    df = pd.DataFrame(result.fetchall(), columns=result.keys())
    print(df)  # 以表格形式打印
    connection.close()
except SQLAlchemyError as e:
    print(f"数据库连接失败: {e}")

# 定义资源文件根目录
# ROOT_RESOURCE = os.path.join(os.path.dirname(__file__), 'resource')


# 配置 DashScope
dashscope.api_key = os.getenv('DASHSCOPE_API_KEY', '')  # 从环境变量获取 API Key
dashscope.timeout = 30  # 设置超时时间为 30 秒

# ====== 门票助手 system prompt 和函数描述 ======
system_prompt = """我是电商销售助手，以下是关于电商销售订单表orders,货品表order_items和客户表users的相关字段，我可能会编写对应的SQL，对数据进行查询
-- 电商销售订单表
CREATE TABLE "ORDERS" 
   (	"ORDER_ID" NUMBER, 
	"ORDER_NO" VARCHAR2(50) NOT NULL ENABLE, 
	"USER_ID" NUMBER NOT NULL ENABLE, 
	"ADDRESS_ID" NUMBER NOT NULL ENABLE, 
	"TOTAL_AMOUNT" NUMBER(10,2) NOT NULL ENABLE, 
	"PAYMENT_AMOUNT" NUMBER(10,2) NOT NULL ENABLE, 
	"FREIGHT_AMOUNT" NUMBER(10,2) DEFAULT 0, 
	"ORDER_STATUS" NUMBER(1,0) DEFAULT 0, 
	"PAYMENT_TIME" DATE, 
	"DELIVERY_TIME" DATE, 
	"RECEIVE_TIME" DATE, 
	"CREATE_TIME" DATE DEFAULT SYSDATE, 
	 PRIMARY KEY ("ORDER_ID")
     )
     
--货品表
CREATE TABLE "ORDER_ITEMS" 
   (	"ITEM_ID" NUMBER, 
	"ORDER_ID" NUMBER NOT NULL ENABLE, 
	"PRODUCT_ID" NUMBER NOT NULL ENABLE, 
	"PRODUCT_NAME" VARCHAR2(100) NOT NULL ENABLE, 
	"PRODUCT_IMAGE" VARCHAR2(200), 
	"PRICE" NUMBER(10,2) NOT NULL ENABLE, 
	"QUANTITY" NUMBER NOT NULL ENABLE, 
	"TOTAL_PRICE" NUMBER(10,2) NOT NULL ENABLE, 
	 PRIMARY KEY ("ITEM_ID")
  ）
  
--客户表
CREATE TABLE USERS" 
   (	"USER_ID" NUMBER, 
	"USERNAME" VARCHAR2(50) NOT NULL ENABLE, 
	"PASSWORD" VARCHAR2(100) NOT NULL ENABLE, 
	"EMAIL" VARCHAR2(100) NOT NULL ENABLE, 
	"PHONE" VARCHAR2(20), 
	"REGISTER_DATE" DATE DEFAULT SYSDATE, 
	"STATUS" NUMBER(1,0) DEFAULT 1, 
	 PRIMARY KEY ("USER_ID")
)

"""

# ====== exc_sql 工具类实现 ======
@register_tool('exc_sql')
class ExcSQLTool(BaseTool):
    """
    SQL查询工具，执行传入的SQL语句并返回结果。
    
    功能：
    - 执行SQL查询并返回结果
    - 支持数据库连接和错误处理
    - 限制返回结果数量为10行
    
    参数：
    - sql_input: SQL查询语句
    - database: 数据库名称（可选，默认为'ubr'）
    
    返回：
    - 查询结果（最多10行，以markdown格式返回）
    """
    description = '对于生成的SQL，进行SQL查询'
    parameters = [{
        'name': 'sql_input',
        'type': 'string',
        'description': '生成的SQL语句',
        'required': True
    }]

    def call(self, params: str, **kwargs) -> str:
        """
        执行SQL查询并返回结果
        
        参数：
        - params: JSON格式的参数字符串，包含sql_input和可选的database
        
        返回：
        - 查询结果（最多10行，以markdown格式返回）
        """
        import json
        args = json.loads(params)
        sql_input = args['sql_input']
        database = args.get('database', 'ubr')
        # 创建数据库连接
    
        engine = create_engine(oracle_connection_string)
        try:
            df = pd.read_sql(sql_input, engine)
            # 返回前10行，防止数据过多
            return df.head(10).to_markdown(index=False)
        except Exception as e:
            return f"SQL执行出错: {str(e)}"

# ====== 初始化门票助手服务 ======
def init_agent_service():
    """
    初始化电商销售助手服务
    
    功能：
    - 配置通义千问模型参数
    - 初始化助手实例
    - 注册SQL查询工具
    - 设置助手名称和描述
    
    返回：
    - 配置好的助手实例
    """
    llm_cfg = {
        'model': 'qwen-turbo-2025-04-28',
        'timeout': 30,
        'retry_count': 3,
    }
    try:
        bot = Assistant(
            llm=llm_cfg,
            name='电商销售助手',
            description='订单查询与订单分析',
            system_message=system_prompt,
            function_list=['exc_sql'],  # 只传工具名字符串
        )
        print("助手初始化成功！")
        return bot
    except Exception as e:
        print(f"助手初始化失败: {str(e)}")
        raise

def app_tui():
    """
    终端交互模式
    
    功能：
    - 支持连续对话
    - 支持文件输入
    - 实时响应用户查询
    - 异常处理和错误提示
    """
    try:
        # 初始化助手
        bot = init_agent_service()

        # 对话历史
        messages = []
        while True:
            try:
                # 获取用户输入
                query = input('user question: ')
                # 获取可选的文件输入
                file = input('file url (press enter if no file): ').strip()
                
                # 输入验证
                if not query:
                    print('user question cannot be empty！')
                    continue
                    
                # 构建消息
                if not file:
                    messages.append({'role': 'user', 'content': query})
                else:
                    messages.append({'role': 'user', 'content': [{'text': query}, {'file': file}]})

                print("正在处理您的请求...")
                # 运行助手并处理响应
                response = []
                for response in bot.run(messages):
                    print('bot response:', response)
                messages.extend(response)
            except Exception as e:
                print(f"处理请求时出错: {str(e)}")
                print("请重试或输入新的问题")
    except Exception as e:
        print(f"启动终端模式失败: {str(e)}")


def app_gui():
    """
    图形界面模式
    
    功能：
    - 基于WebUI提供图形界面
    - 预设常用查询建议
    - 支持实时对话
    - 异常处理和错误提示
    """
    try:
        print("正在启动 Web 界面...")
        # 初始化助手
        bot = init_agent_service()
        # 配置聊天界面，列举3个典型门票查询问题
        chatbot_config = {
            'prompt.suggestions': [               
                '帮我查看订单金额排名',
                '帮我从多到小列出前5位购买最多的货物',
                '请帮我查询客户订单金额排名前5的订单信息，包括订单号，订的货物清单以及客户姓名',
                '请帮我查询客户订单金额排名前5的订单信息，包括订单号，订的货物清单以及客户姓名，请按订单为单位显示，一张订单有多个货物的，将货物名称罗列出来'
            ]
        }
        print("Web 界面准备就绪，正在启动服务...")
        # 启动 Web 界面
        WebUI(
            bot,
            chatbot_config=chatbot_config
        ).run()
    except Exception as e:
        print(f"启动 Web 界面失败: {str(e)}")
        print("请检查网络连接和 API Key 配置")


if __name__ == '__main__':
    # 运行模式选择
    app_gui()          # 图形界面模式（默认） 
