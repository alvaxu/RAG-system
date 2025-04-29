#使用LangChain连接远程Oracle数据库尝试LLM 提供的SQL智能助理

为完成此次数据库连接实验，笔者用自己的笔记本电脑搭建了一台linux虚机，安装了oracle 23C，并借助deepseek创建了若干与电商业务有关的表并插入了一些记录。

接着在windows实体机端（作为oracle的客户端）配通了sqlplus连接，然后开始用jupyter调试python调用langchain连接远程oracle的不同方法。

要通过LangChain的`SQLDatabase`连接远程Oracle数据库，需要按照以下步骤操作：

## 1. 安装必要的依赖

首先确保你已安装必要的Python包：
```bash
pip install langchain cx_Oracle sqlalchemy
```

注意：`cx_Oracle`是Oracle官方提供的Python驱动，需要Oracle客户端库支持。

 ***安装时报错，错误表明在安装 `cx_Oracle` 时遇到了问题，主要是因为缺少 Microsoft Visual C++ 编译工具。***

错误信息明确指出需要 **Microsoft Visual C++ 14.0 或更高版本**，这是编译 `cx_Oracle` 所必需的。

下载并安装 Microsoft Visual C++ Build Toolshttps://visualstudio.microsoft.com/zh-hans/visual-cpp-build-tools/

选择以下组件：

- 核心组件：
  "C++ build tools"（C++生成工具）
  "MSVC v142 - VS 2019 C++ x64/x86 build tools"（或最新版本如MSVC v143 - VS 2022）
  "Windows 10 SDK"或"Windows 11 SDK"（根据你的操作系统版本选择）

- 推荐附加组件：
  "C++ CMake tools for Windows"（CMake工具）

***完成安装后，再执行 pip install langchain cx_Oracle sqlalchemy，成功***

```
Looking in indexes: https://pypi.tuna.tsinghua.edu.cn/simple
Requirement already satisfied: langchain in c:\users\administrator\appdata\local\programs\python\python312\lib\site-packages (0.3.24)
Collecting cx_Oracle
  Using cached https://pypi.tuna.tsinghua.edu.cn/packages/e8/16/13c265afc984796fe38ee928733569b599cfd657245ddd1afad238b66656/cx_Oracle-8.3.0.tar.gz (363 kB)
  Installing build dependencies: started
  Installing build dependencies: finished with status 'done'
  Getting requirements to build wheel: started
  Getting requirements to build wheel: finished with status 'done'
  Preparing metadata (pyproject.toml): started
  Preparing metadata (pyproject.toml): finished with status 'done'
Requirement already satisfied: sqlalchemy in c:\users\administrator\appdata\local\programs\python\python312\lib\site-packages (2.0.40)
Requirement already satisfied: langchain-core<1.0.0,>=0.3.55 in c:\users\administrator\appdata\local\programs\python\python312\lib\site-packages (from langchain) (0.3.55)
Requirement already satisfied: langchain-text-splitters<1.0.0,>=0.3.8 in c:\users\administrator\appdata\local\programs\python\python312\lib\site-packages (from langchain) (0.3.8)
Requirement already satisfied: langsmith<0.4,>=0.1.17 in c:\users\administrator\appdata\local\programs\python\python312\lib\site-packages (from langchain) (0.3.32)
Requirement already satisfied: pydantic<3.0.0,>=2.7.4 in c:\users\administrator\appdata\local\programs\python\python312\lib\site-packages (from langchain) (2.11.2)
Requirement already satisfied: requests<3,>=2 in c:\users\administrator\appdata\local\programs\python\python312\lib\site-packages (from langchain) (2.32.3)
Requirement already satisfied: PyYAML>=5.3 in c:\users\administrator\appdata\local\programs\python\python312\lib\site-packages (from langchain) (6.0.2)
Requirement already satisfied: greenlet>=1 in c:\users\administrator\appdata\local\programs\python\python312\lib\site-packages (from sqlalchemy) (3.1.1)
Requirement already satisfied: typing-extensions>=4.6.0 in c:\users\administrator\appdata\local\programs\python\python312\lib\site-packages (from sqlalchemy) (4.13.1)
Requirement already satisfied: tenacity!=8.4.0,<10.0.0,>=8.1.0 in c:\users\administrator\appdata\local\programs\python\python312\lib\site-packages (from langchain-core<1.0.0,>=0.3.55->langchain) (9.1.2)
Requirement already satisfied: jsonpatch<2.0,>=1.33 in c:\users\administrator\appdata\local\programs\python\python312\lib\site-packages (from langchain-core<1.0.0,>=0.3.55->langchain) (1.33)
Requirement already satisfied: packaging<25,>=23.2 in c:\users\administrator\appdata\local\programs\python\python312\lib\site-packages (from langchain-core<1.0.0,>=0.3.55->langchain) (24.2)
Requirement already satisfied: httpx<1,>=0.23.0 in c:\users\administrator\appdata\local\programs\python\python312\lib\site-packages (from langsmith<0.4,>=0.1.17->langchain) (0.28.1)
Requirement already satisfied: orjson<4.0.0,>=3.9.14 in c:\users\administrator\appdata\local\programs\python\python312\lib\site-packages (from langsmith<0.4,>=0.1.17->langchain) (3.10.16)
Requirement already satisfied: requests-toolbelt<2.0.0,>=1.0.0 in c:\users\administrator\appdata\local\programs\python\python312\lib\site-packages (from langsmith<0.4,>=0.1.17->langchain) (1.0.0)
Requirement already satisfied: zstandard<0.24.0,>=0.23.0 in c:\users\administrator\appdata\local\programs\python\python312\lib\site-packages (from langsmith<0.4,>=0.1.17->langchain) (0.23.0)
Requirement already satisfied: annotated-types>=0.6.0 in c:\users\administrator\appdata\local\programs\python\python312\lib\site-packages (from pydantic<3.0.0,>=2.7.4->langchain) (0.7.0)
Requirement already satisfied: pydantic-core==2.33.1 in c:\users\administrator\appdata\local\programs\python\python312\lib\site-packages (from pydantic<3.0.0,>=2.7.4->langchain) (2.33.1)
Requirement already satisfied: typing-inspection>=0.4.0 in c:\users\administrator\appdata\local\programs\python\python312\lib\site-packages (from pydantic<3.0.0,>=2.7.4->langchain) (0.4.0)
Requirement already satisfied: charset-normalizer<4,>=2 in c:\users\administrator\appdata\local\programs\python\python312\lib\site-packages (from requests<3,>=2->langchain) (3.4.1)
Requirement already satisfied: idna<4,>=2.5 in c:\users\administrator\appdata\local\programs\python\python312\lib\site-packages (from requests<3,>=2->langchain) (3.10)
Requirement already satisfied: urllib3<3,>=1.21.1 in c:\users\administrator\appdata\local\programs\python\python312\lib\site-packages (from requests<3,>=2->langchain) (2.3.0)
Requirement already satisfied: certifi>=2017.4.17 in c:\users\administrator\appdata\local\programs\python\python312\lib\site-packages (from requests<3,>=2->langchain) (2025.1.31)
Requirement already satisfied: anyio in c:\users\administrator\appdata\local\programs\python\python312\lib\site-packages (from httpx<1,>=0.23.0->langsmith<0.4,>=0.1.17->langchain) (4.9.0)
Requirement already satisfied: httpcore==1.* in c:\users\administrator\appdata\local\programs\python\python312\lib\site-packages (from httpx<1,>=0.23.0->langsmith<0.4,>=0.1.17->langchain) (1.0.7)
Requirement already satisfied: h11<0.15,>=0.13 in c:\users\administrator\appdata\local\programs\python\python312\lib\site-packages (from httpcore==1.*->httpx<1,>=0.23.0->langsmith<0.4,>=0.1.17->langchain) (0.14.0)
Requirement already satisfied: jsonpointer>=1.9 in c:\users\administrator\appdata\local\programs\python\python312\lib\site-packages (from jsonpatch<2.0,>=1.33->langchain-core<1.0.0,>=0.3.55->langchain) (3.0.0)
Requirement already satisfied: sniffio>=1.1 in c:\users\administrator\appdata\local\programs\python\python312\lib\site-packages (from anyio->httpx<1,>=0.23.0->langsmith<0.4,>=0.1.17->langchain) (1.3.1)
Building wheels for collected packages: cx_Oracle
  Building wheel for cx_Oracle (pyproject.toml): started
  Building wheel for cx_Oracle (pyproject.toml): finished with status 'done'
  Created wheel for cx_Oracle: filename=cx_oracle-8.3.0-cp312-cp312-win_amd64.whl size=224067 sha256=5e15eb2bf6bf1fcc93e7638f63c7625c2e34c010983d374769e8ebc8948e7516
  Stored in directory: c:\users\administrator\appdata\local\pip\cache\wheels\b2\c1\f2\8eb1495ea05272640061605216448697e673ecba3b1ff54bb0
Successfully built cx_Oracle
Installing collected packages: cx_Oracle
Successfully installed cx_Oracle-8.3.0
```


## 2. 准备连接字符串


### **连接字符串变体示例**

|    场景    |                        连接字符串格式                        |
| :--------: | :----------------------------------------------------------: |
| 标准服务名 |       `oracle+cx_oracle://user:pass@host/service_name`       |
|  指定端口  |    `oracle+cx_oracle://user:pass@host:1521/service_name`     |
|  使用SID   |        `oracle+cx_oracle://user:pass@host:1521:ORCL`         |
|  TNS别名   |           `oracle+cx_oracle://user:pass@tns_alias`           |
|  云数据库  | `oracle+cx_oracle://user:pass@host:1521/ORCL?wallet_location=/path/to/wallet` |

## 3. 创建SQLDatabase连接 （三种方法）

### 方法1：创建cx_Oracle连接

```python
from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine

#目前采用可以调通的方法如下：
#1.创建cx_Oracle连接
import cx_Oracle
dsn = cx_Oracle.makedsn('192.168.43.11', 1521, service_name='FREEPDB1')  # 替换实际主机名
conn = cx_Oracle.connect(user="dbtest", password="test", dsn=dsn)

# print(conn.version)  # 输出版本号表示成功
# conn.close()

#2.转换为SQLDatabase实例
db = SQLDatabase.from_uri(f"oracle+cx_oracle://", engine_args={"creator": lambda: conn})

#3. 执行测试查询
result = db.run("SELECT * FROM products")
print(result)
```

### 方法2：用create_engine

```python
from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine
# 和执行端的tnsnames.ora里的配置信息一致
#(DESCRIPTION = (ADDRESS_LIST = (ADDRESS = (PROTOCOL = TCP)(HOST = centos8)(PORT = 1521)) ) (CONNECT_DATA = (SERVICE_NAME = FREEPDB1) ) )
#注意必须明确定义“?service_name={service_name}”，否则总是报
# DatabaseError: (cx_Oracle.DatabaseError) ORA-12505: TNS: 监听程序当前无法识别连接描述符中所给出的 SID
db_user = "dbtest"
db_password = "test"
db_host = "192.168.43.11:1521"
service_name = "FREEPDB1"
# 1.连接字符串
#oracle_connection_string = "oracle+cx_oracle://dbtest:test@192.168.43.11:1521/?service_name=FREEPDB1"
oracle_connection_string = f"oracle+cx_oracle://{db_user}:{db_password}@{db_host}/?service_name={service_name}"
# 创建SQLAlchemy引擎
engine = create_engine(oracle_connection_string)

# 2.创建SQLDatabase实例
db = SQLDatabase(engine)

# 3. 执行测试查询
result = db.run("SELECT * FROM products")
print(result)
```
### 方法3:直接使用SQLDatabase.from_uri,
```python
# 和执行端的tnsnames.ora里的配置信息一致
#(DESCRIPTION = (ADDRESS_LIST = (ADDRESS = (PROTOCOL = TCP)(HOST = centos8)(PORT = 1521)) ) (CONNECT_DATA = (SERVICE_NAME = FREEPDB1) ) )
#注意必须明确定义“?service_name={service_name}”，否则总是报
# DatabaseError: (cx_Oracle.DatabaseError) ORA-12505: TNS: 监听程序当前无法识别连接描述符中所给出的 SID
from langchain_community.utilities import SQLDatabase
db_user = "dbtest"
db_password = "test"
db_host = "192.168.43.11:1521"
service_name = "FREEPDB1"

db = SQLDatabase.from_uri(f"oracle+cx_oracle://{db_user}:{db_password}@{db_host}/?service_name={service_name}")

# 执行测试查询
result = db.run("SELECT * FROM products")
print(result)
```

## 调用agent_excutor 测试LLM大模型提供的 SQL 助理能力

```python
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.llms.openai import OpenAI
from langchain.agents import AgentExecutor
from langchain.chat_models import ChatOpenAI
import os

llm = ChatOpenAI(
    temperature=0.01,
    model="deepseek-chat",  
    openai_api_key = os.getenv('API_KEY'),
    openai_api_base="https://api.deepseek.com"
)

# 需要设置llm
toolkit = SQLDatabaseToolkit(db=db, llm=llm)

agent_executor = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True
)
# Task: 描述数据表
agent_executor.invoke("描述与订单相关的表及其关系")

```
输出如下：
```python
> Entering new SQL Agent Executor chain...
Action: sql_db_list_tables
Action Input: order_items, orders, payment_info, product_categories, product_images, product_reviews, products, shopping_cart, user_addresses, usersI see several tables that might be related to orders. The most relevant ones appear to be "orders", "order_items", and possibly "payment_info" and "users". I should examine their schemas to understand their relationships.

Action: sql_db_schema
Action Input: orders, order_items, payment_info, users
CREATE TABLE order_items (
	item_id NUMBER NOT NULL, 
	order_id NUMBER NOT NULL, 
	product_id NUMBER NOT NULL, 
	product_name VARCHAR(100 CHAR) NOT NULL, 
	product_image VARCHAR(200 CHAR), 
	price NUMBER(10, 2) NOT NULL, 
	quantity NUMBER NOT NULL, 
	total_price NUMBER(10, 2) NOT NULL, 
	CONSTRAINT sys_c008467 PRIMARY KEY (item_id), 
	CONSTRAINT sys_c008468 FOREIGN KEY(order_id) REFERENCES orders (order_id), 
	CONSTRAINT sys_c008469 FOREIGN KEY(product_id) REFERENCES products (product_id)
)
 TABLESPACE "TESTDBSPACE"

/*
3 rows from order_items table:
item_id	order_id	product_id	product_name	product_image	price	quantity	total_price
1.0	1001.0	10001.0	智能手机X	http://example.com/images/10001_1.jpg	5999	1.0	5999
2.0	1001.0	10010.0	男士T恤	http://example.com/images/10010_1.jpg	99	2.0	198
3.0	1002.0	10004.0	轻薄笔记本	http://example.com/images/10004_1.jpg	8999	1.0	8999
*/


CREATE TABLE orders (
	order_id NUMBER NOT NULL, 
	order_no VARCHAR(50 CHAR) NOT NULL, 
	user_id NUMBER NOT NULL, 
	address_id NUMBER NOT NULL, 
	total_amount NUMBER(10, 2) NOT NULL, 
	payment_amount NUMBER(10, 2) NOT NULL, 
	freight_amount NUMBER(10, 2) DEFAULT 0, 
	order_status NUMBER(1, 0) DEFAULT 0, 
	payment_time DATE, 
	delivery_time DATE, 
	receive_time DATE, 
	create_time DATE DEFAULT SYSDATE, 
	CONSTRAINT sys_c008457 PRIMARY KEY (order_id), 
	CONSTRAINT sys_c008459 FOREIGN KEY(user_id) REFERENCES users (user_id), 
	CONSTRAINT sys_c008460 FOREIGN KEY(address_id) REFERENCES user_addresses (address_id)
)
 TABLESPACE "TESTDBSPACE"

/*
3 rows from orders table:
order_id	order_no	user_id	address_id	total_amount	payment_amount	freight_amount	order_status	payment_time	delivery_time	receive_time	create_time
1001.0	ORD20221101001	1.0	101.0	6197	6197	0	4	2022-11-01 10:30:00	2022-11-02 09:15:00	2022-11-03 14:20:00	2022-11-01 10:00:00
1002.0	ORD20221102001	2.0	201.0	9118	9118	0	4	2022-11-02 11:20:00	2022-11-03 10:30:00	2022-11-04 16:45:00	2022-11-02 11:00:00
1003.0	ORD20221103001	3.0	301.0	1598	1598	0	4	2022-11-03 14:45:00	2022-11-04 13:20:00	2022-11-05 10:30:00	2022-11-03 14:30:00
*/


CREATE TABLE payment_info (
	payment_id NUMBER NOT NULL, 
	order_id NUMBER NOT NULL, 
	payment_type NUMBER(1, 0) NOT NULL, 
	trade_no VARCHAR(100 CHAR), 
	payment_amount NUMBER(10, 2) NOT NULL, 
	payment_status NUMBER(1, 0) DEFAULT 0, 
	create_time DATE DEFAULT SYSDATE, 
	callback_time DATE, 
	CONSTRAINT sys_c008473 PRIMARY KEY (payment_id), 
	CONSTRAINT sys_c008474 FOREIGN KEY(order_id) REFERENCES orders (order_id)
)
 TABLESPACE "TESTDBSPACE"

/*
3 rows from payment_info table:
payment_id	order_id	payment_type	trade_no	payment_amount	payment_status	create_time	callback_time
1.0	1001.0	1	PAY202211010001	6197	1	2022-11-01 10:30:00	2022-11-01 10:31:00
2.0	1002.0	2	PAY202211020001	9118	1	2022-11-02 11:20:00	2022-11-02 11:21:00
3.0	1003.0	1	PAY202211030001	1598	1	2022-11-03 14:45:00	2022-11-03 14:46:00
*/


CREATE TABLE users (
	user_id NUMBER NOT NULL, 
	username VARCHAR(50 CHAR) NOT NULL, 
	password VARCHAR(100 CHAR) NOT NULL, 
	email VARCHAR(100 CHAR) NOT NULL, 
	phone VARCHAR(20 CHAR), 
	register_date DATE DEFAULT SYSDATE, 
	status NUMBER(1, 0) DEFAULT 1
, 
	CONSTRAINT sys_c008421 PRIMARY KEY (user_id)
)
 TABLESPACE "TESTDBSPACE"

/*
3 rows from users table:
user_id	username	password	email	phone	register_date	status
1.0	张三	zhangsan123	zhangsan@example.com	13800138001	2022-01-01 00:00:00	1
2.0	李四	lisi456	lisi@example.com	13900139002	2022-01-05 00:00:00	1
3.0	王五	wangwu789	wangwu@example.com	13700137003	2022-01-10 00:00:00	1
*/I now understand the tables related to orders and their relationships. Here's the description:

1. **orders** table: 
   - Contains core order information (order_id, order_no, user_id, address_id, amounts, statuses, timestamps)
   - Relates to:
     - users table via user_id (foreign key)
     - user_addresses table via address_id (foreign key, though we didn't see its schema)

2. **order_items** table:
   - Contains individual items within each order (product details, quantities, prices)
   - Relates to:
     - orders table via order_id (foreign key)
     - products table via product_id (foreign key)

3. **payment_info** table:
   - Contains payment details for orders
   - Relates to:
     - orders table via order_id (foreign key)

The relationships form a hierarchy:
- A user can have multiple orders (one-to-many)
- An order can have multiple items (one-to-many)
- An order has one payment record (one-to-one)

Final Answer: 与订单相关的表主要有orders(订单主表)、order_items(订单商品明细)和payment_info(支付信息)。orders表通过user_id关联users表，通过address_id关联user_addresses表；order_items表通过order_id关联orders表，通过product_id关联products表；payment_info表通过order_id关联orders表。这些表共同构成了订单系统的核心数据结构。

> Finished chain.
```
```python
{'input': '描述与订单相关的表及其关系',
 'output': '与订单相关的表主要有orders(订单主表)、order_items(订单商品明细)和payment_info(支付信息)。orders表通过user_id关联users表，通过address_id关联user_addresses表；order_items表通过order_id关联orders表，通过product_id关联products表；payment_info表通过order_id关联orders表。这些表共同构成了订单系统的核心数据结构。'}
```
```python
# 这个任务，实际上数据库中 没有categories表
agent_executor.run("描述categories表")
```
回答
```python
> Entering new SQL Agent Executor chain...
Action: sql_db_list_tables
Action Input: order_items, orders, payment_info, product_categories, product_images, product_reviews, products, shopping_cart, user_addresses, usersI notice that there isn't a table called "categories" in the database, but there is a table called "product_categories" which might be related. I should check the schema of this table to understand its structure.

Action: sql_db_schema
Action Input: product_categories
CREATE TABLE product_categories (
	category_id NUMBER NOT NULL, 
	category_name VARCHAR(50 CHAR) NOT NULL, 
	parent_id NUMBER, 
	category_level NUMBER(1, 0) NOT NULL, 
	sort_order NUMBER DEFAULT 0, 
	CONSTRAINT sys_c008434 PRIMARY KEY (category_id), 
	CONSTRAINT sys_c008435 FOREIGN KEY(parent_id) REFERENCES product_categories (category_id)
)
 TABLESPACE "TESTDBSPACE"

/*
3 rows from product_categories table:
category_id	category_name	parent_id	category_level	sort_order
1001.0	电子产品	None	1	1.0
1002.0	服装	None	1	2.0
1003.0	家居用品	None	1	3.0
*/I now understand the structure of the product_categories table. It appears to be the table that stores category information for products, even though it's not exactly named "categories". Here's the description:

Final Answer: 
The product_categories table (which serves as the categories table) contains product category information with the following structure:
- category_id: A unique numeric identifier for each category (primary key)
- category_name: The name of the category (up to 50 characters)
- parent_id: References another category as its parent (foreign key to category_id)
- category_level: A numeric value indicating the category's level in the hierarchy
- sort_order: A numeric value used for ordering categories (defaults to 0)

Sample categories include:
- Electronics (category_id: 1001)
- Clothing (category_id: 1002)
- Home Goods (category_id: 1003)

The table supports hierarchical relationships between categories through the parent_id field.

> Finished chain.
```
```python
"The product_categories table (which serves as the categories table) contains product category information with the following structure:\n- category_id: A unique numeric identifier for each category (primary key)\n- category_name: The name of the category (up to 50 characters)\n- parent_id: References another category as its parent (foreign key to category_id)\n- category_level: A numeric value indicating the category's level in the hierarchy\n- sort_order: A numeric value used for ordering categories (defaults to 0)\n\nSample categories include:\n- Electronics (category_id: 1001)\n- Clothing (category_id: 1002)\n- Home Goods (category_id: 1003)\n\nThe table supports hierarchical relationships between categories through the parent_id field."
```







## 注意事项

1. 确保你的网络可以访问远程Oracle服务器
2. 确保Oracle客户端库已正确安装并配置
3. 对于较新的Oracle版本，可能需要使用`service_name`而不是`SID`
4. 如果使用TNS名称，连接字符串格式会有所不同
5. 考虑使用环境变量存储敏感信息，而不是硬编码在代码中

