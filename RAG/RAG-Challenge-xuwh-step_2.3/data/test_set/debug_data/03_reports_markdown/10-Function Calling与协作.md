# Function Calling与协作

# 今天的学习目标

# Function Calling与协作

·什么是Function Calling  
CASE：天气调用 (Qwen3 Function Calling)  
CASE：门票助手

# Function Calling

Thinking：FunctionCalling在大模型中的作用是什么？

·扩展模型能力

大模型本身无法直接操作外部系统（如数据库、计算工具），但通过调用预设函数，可以完成：  
实时数据获取 (天气、股价、新闻)  
复杂计算 (数学运算、代码执行)  
操作外部系统 (发送邮件、控制智能设备)

# ·结构化输出

模型可将用户自然语言请求转化为结构化参数，传递给函数。例如：用户说"明天北京天气如何？ $" $ 模型调用 get_weather(location="北京",date="2025-05-06")

·动态决策流程

模型可根据上下文决定是否/何时调用函数，甚至链式调用多个函数（如先查天气，再推荐穿搭）。

FunctionCall是大模型与真实世界交互的"桥梁"，从语言理解 $\Rightarrow$ 具体行动

Thinking: Function Calling与MCP的区别?

<html><body><table><tr><td>维度</td><td>Function Calling</td><td>MCP</td></tr><tr><td>定位</td><td>模型厂商私有接口 (如OpenAl,Qwen)</td><td>开放协议 (类似 HTTP/USB-C)</td></tr><tr><td>扩展性</td><td>需为每个模型单独适配</td><td>一次开发，多模型兼容</td></tr><tr><td>复杂性</td><td>适合简单、单次调用任务</td><td>支持多轮对话、复杂上下文管理</td></tr><tr><td>生态依赖</td><td>依赖特定模型 (如 GPT-4)</td><td>跨模型、跨平台 (如 Claude、Cursor)</td></tr><tr><td>安全性</td><td>依赖云端API密钥</td><td>支持本地化数据控制</td></tr></table></body></html>

# Function Calling

Thinking: 已经有了MCP还需要FunctionCalling么？

简单、原子化任务使用FunctionCalling会更方便

·查询天气get_weather(city $u = 1$ "北京")·计算数学公式calculate(expression="3+5")·发送单条通知 send_email(to="user@example.com")

优势:

开发快捷：无需配置MCPServer，直接通过模型API调用预定义函数。  
低延迟：单次请求-响应，无需协议层开销。

MCP可能成为主流，但FunctionCalling作为底层能力仍将存在

CASE：天气调用 ( Function Calling)

# Qwen3:

于2025年4月29日发布，包含8种不同规模的模型，涵盖密集（Dense）和混合专家（MoE）架构，全部基于Apache2.0开源协议，支持免费商用

MoE模型 （高效推理）：

·Qwen3-235B-A22B（总参数2350亿，激活 220亿）一一旗舰级模型，性能接近 Gemini 2.5 Pro。·Qwen3-30B-A3B（总参数300亿，激活30亿）一一高效推理，仅需 $10 \%$ 激活参数即可超越前代QwQ-32B。密集模型（全参数激活）：

·Qwen3-32B、14B、8B、4B、1.7B、0.6B，其中Qwen3-4B性能媲美前代Qwen2.5-72B开源了两个MoE模型的权重此外，6个Dense 模型也已开源，包括Qwen3-32B、Qwen3-14B、 Qwen3-8B、 Qwen3-4B、 Qwen3-1.7B 和Qwen3-0.6B，均在Apache2.0许可下开源。

<html><body><table><tr><td rowspan="2"></td><td rowspan="2">Qwen3-235B-A22B MoE</td><td rowspan="2">Qwen3-32B Dense</td><td rowspan="2">OpenAl-o1 2024-12-17</td><td rowspan="2">Deepseek-R1</td><td rowspan="2">Grok3Beta Think</td><td rowspan="2">Gemini2.5-Pro</td><td rowspan="2">OpenAl-o3-mini Medium</td></tr><tr><td></td></tr><tr><td>ArenaHard</td><td>95.6</td><td>93.8</td><td>92.1</td><td>93.2</td><td></td><td>96.4</td><td>89.0</td></tr><tr><td>AIME'24</td><td>85.7</td><td>81.4</td><td>74.3</td><td>79.8</td><td>83.9</td><td>92.0</td><td>79.6</td></tr><tr><td>AIME'25</td><td>81.5</td><td>72.9</td><td>79.2</td><td>70.0</td><td>77.3</td><td>86.7</td><td>74.8</td></tr><tr><td>LiveCodeBench</td><td>70.7</td><td>65.7</td><td>63.9</td><td>64.3</td><td>70.6</td><td>70.4</td><td>66.3</td></tr><tr><td>CodeForces Elo Rating</td><td>2056</td><td>1977</td><td>1891</td><td>2029</td><td></td><td>2001</td><td>2036</td></tr><tr><td>Aider Pass@2</td><td>61.8</td><td>50.2</td><td>61.7</td><td>56.9</td><td>53.3</td><td>72.9</td><td>53.8</td></tr><tr><td>LiveBench</td><td>77.1</td><td>74.9</td><td>75.7</td><td>71.6</td><td></td><td>82.4</td><td>70.0</td></tr><tr><td>BFCL 3</td><td>70.8</td><td>70.3</td><td>67.8</td><td>56.9</td><td></td><td>62.9</td><td>64.6</td></tr><tr><td>MultilF 8 Languages</td><td>71.9</td><td>73.0</td><td>48.8</td><td>67.7</td><td></td><td>77.8</td><td>48.4</td></tr></table></body></html>

开源了两个MoE模型的权重：Qwen3-235B-A22B，以及Qwen3-30B-A3B

Qwen3-4B这样的小模型也能匹敌Qwen2.5-72B-Instruct的性能  

<html><body><table><tr><td rowspan="2"></td><td rowspan="2">Qwen3-30B-A3B</td><td rowspan="2">QwQ-32B</td><td rowspan="2">Qwen3-4B</td><td colspan="4"></td></tr><tr><td>Qwen2.5-72B-lnstruct</td><td>Gemma3-27B-IT</td><td>DeepSeek-V3</td><td>G2T-40</td></tr><tr><td>ArenaHard</td><td>91.0</td><td>89.5</td><td>76.6</td><td>81.2</td><td>86.8</td><td>85.5</td><td>85.3</td></tr><tr><td>AIME'24</td><td>80.4</td><td>79.5</td><td>73.8</td><td>18.9</td><td>32.6</td><td>39.2</td><td>11.1</td></tr><tr><td>AIME'25</td><td>70.9</td><td>69.5</td><td>65.6</td><td>15.0</td><td>24.0</td><td>28.8</td><td>7.6</td></tr><tr><td>LiveCodeBench</td><td>62.6</td><td>62.7</td><td>54.2</td><td>30.7</td><td>26.9</td><td>33.1</td><td>32.7</td></tr><tr><td>CodeForces</td><td>1974</td><td>1982</td><td>1671</td><td>859</td><td>1063</td><td>1134</td><td>864</td></tr><tr><td>GPQA</td><td>65.8</td><td>65.6</td><td>55.9</td><td>49.0</td><td>42.4</td><td>59.1</td><td>46.0</td></tr><tr><td>LiveBench</td><td>74.3</td><td>72.0</td><td>63.6</td><td>51.4</td><td>49.2</td><td>60.5</td><td>52.2</td></tr><tr><td>BFCL v3</td><td>69.1</td><td>66.4</td><td>65.9</td><td>63.4</td><td>59.1</td><td>57.6</td><td>72.5</td></tr><tr><td>MultilF 8 Languages</td><td>72.2</td><td>68.3</td><td>66.3</td><td>65.3</td><td>69.8</td><td>55.6</td><td>65.6</td></tr></table></body></html>

<html><body><table><tr><td>Models</td><td>Layers</td><td>Heads (Q/ KV)</td><td>Tie Embedding Context Length</td><td></td></tr><tr><td>Qwen3-0.6B</td><td>28</td><td>16/8</td><td>Yes</td><td>32K</td></tr><tr><td>Qwen3-1.7B</td><td>28</td><td>16/8</td><td>Yes</td><td>32K</td></tr><tr><td>Qwen3-4B</td><td>36</td><td>32/8</td><td>Yes</td><td>32K</td></tr><tr><td>Qwen3-8B</td><td>36</td><td>32/8</td><td>No</td><td>128K</td></tr><tr><td>Qwen3-14B</td><td>40</td><td>40/8</td><td>No</td><td>128K</td></tr><tr><td>Qwen3-32B</td><td>64</td><td>64/8</td><td>No</td><td>128K</td></tr></table></body></html>

<html><body><table><tr><td>Models</td><td>Layers</td><td></td><td>Heads (Q / KV) # Experts (Total / Activated)</td><td>Context Length</td></tr><tr><td>Qwen3-30B-A3B</td><td>48</td><td>32/4</td><td>128/8</td><td>128K</td></tr><tr><td>Qwen3-235B-A22B</td><td>94</td><td>64/4</td><td>128/8</td><td>128K</td></tr></table></body></html>

Qwen3具有广泛的应用场景：

Apache2.0协议是一种宽松的自由软件许可协议：

自由使用：允许用户免费使用、修改、分发软件，适用于商业或非商业项目。

企业级AI (金融分析、智能客服)端侧AI (手机、loT设备本地部署)代码生成&AI编程助手·多语言翻译&全球化应用

专利授权：明确授予用户与软件相关的专利权利（贡献者自动授权，避免专利诉讼风险）。

衍生作品：允许修改代码并闭源发布 （需遵守协议条款）。

Qwen3具有广泛的应用场景，且具有商业友好性，允许将授权代码融入专有软件，无需公开衍生作品代码，适合企业使用。

# CASE: 天气调用 (Function Calling)

TO DO：使用Qwen3调用高德Function Calling，查询天气实现通过Qwen3与天气工具集成，自动调用高德地图天气API查询指定城市的实时天气信息，并输出结果。

Thinking: 关键步骤都有哪些？Step1，设置 DashScope APl Keydashscope.api_key $\mathbf { \tau } = \mathbf { \tau }$ "sk-xxxxxx'设置通义千问的API Key，用于身份认证可以调用的模型APi列表https://help.aliyun.com/zh/model-studio/models

<html><body><table><tr><td>qwen-turbo-latest 始终等同最新快照版 Batch调用半价</td><td>最新版</td><td>思考模 式</td><td>思考模 式 129,024</td><td>8,192</td><td></td><td>思考模式 0.006元 非思考模</td><td>各100万 Token 有效期：百炼 开通后180天</td></tr><tr><td>qwen-turbo-2025-04-28 又称 qwen-turbo-0428、 Qwen3</td><td></td><td>非思考 式模 1,000,0 00</td><td>非思考 模式 1,000,0 00</td><td>思维链 最长 38,912</td><td>0.0003元</td><td>式 0.0006 元</td><td>内</td></tr></table></body></html>

# CASE: 天气调用 (Function Calling)

Step2，定义FunctionTool工具 (高德天气API)   
weather_tool ={ "type": "function", "function": { "name":"get_current_weather", 'description": "Get the current weather in a given   
location", "parameters": { "type": "object", "properties": { "location": { "type": "string", "description": "The city name, e.g. 北京",

}, "adcode": { "type": "string", "description": "The city code,e.g. 110000 (北京)", } }, "required": ["location"], }, }, }

定义了get_current_weather\`工具，描述了参数（城市名和城市代码），用于让Qwen3知道如何调用外部天气查询工具。

# CASE: 天气调用 (Function Calling)

Step3，实现FunctionTool工具(调用高德天气API)   
def get_weather_from_gaode(location: str,adcode: str $\mathbf { \sigma } = \mathbf { \sigma }$   
None): """·调用高德地图API查询天气." gaode_api_key $\mathbf { \tau } = \mathbf { \tau }$ "xxxxxx" # 替换成你的高德APl Key base_url $\mathbf { \tau } = \mathbf { \tau }$   
"https://restapi.amap.com/v3/weather/weatherlnfo" $\mathsf { p a r a m s } = \left\{ \begin{array} { r l } \end{array} \right.$ "key": gaode_api_key, "city": adcode if adcode else location, "extensions": "base", 1J response $\mathbf { \tau } = \mathbf { \tau }$ requests.get(base_url, params=params)   
if response.status_code $= = 2 0 0$ ： return response.json() else: return {"error": f"Failed to fetch weather:   
{response.status_code}"} 通过HTTPGET请求调用高德天气API，获取指定 城市的实时天气。   
支持通过城市名或 adcode 查询。

# CASE: 天气调用 (Function Calling)

Step4，主流程函数：run_weather_query def run_weather_query():

""使用 Qwen3 $^ +$ Function 查询天气." $\mathsf { m e s s a g e s } = [$ {"role":"system","content":"你是一个智能助手，   
可以查询天气信息。"}, {"role":"user","content":"北京现在天气怎么样？"}   
] response $\mathbf { \tau } = \mathbf { \tau }$ dashscope.Generation.call( model $= ^ { \mathsf { \Gamma } }$ "qwen-plus-2025-04-28", messages $\ c =$ messages, tools $\ c =$ [weather_tool] tool_choice $\ c =$ "auto",) if response.status_code $\scriptstyle = =$ HTTPStatus.OK: #检查是否需要调用工具 if "tool_calls" in response.output.choices[O].message: tool_call $\mathbf { \sigma } = \mathbf { \sigma }$   
response.output.choices[O].message.tool_calls[0] if tool_call["function"]["name"] ==   
'get_current_weather": #解析参数并调用高德API import json args $\mathbf { \tau } = \mathbf { \tau }$ json.loads(tool_call["function"]["arguments"]) location $\mathbf { \tau } = \mathbf { \tau }$ args.get("location","北京") adcode $\mathbf { \sigma } = \mathbf { \sigma }$ args.get("adcode", None)

# CASE: 天气调用 (Function Calling)

weather_data $\mathbf { \tau } = \mathbf { \tau }$ get_weather_from_gaode(location,adcode) print(f"查询结果: {weather_data}") else: print(response.output.choices[O].message.content) else: print(f"请求失败: {response.code} - {response.message}")

# 整体流程：

# 1.构造对话消息

-系统消息：设定助手身份。  
-用户消息：提出天气查询请求。

2.调用Qwen3大模型

-传入模型名称、对话消息、工具定义。  
- 'tool_choice $= ^ { \mathsf { 1 } }$ "auto"让模型自动决定是否调用工具。

# 3.处理模型返回结果

-如果模型决定调用工具（即‘tool_calls\`存在），解析工具调用参数。

-调用本地\`get_weather_from_gaode\`函数，获取天气数据。打印查询结果。

-如果模型未调用工具，直接输出模型回复内容

CASE：门票助手

# CASE：门票助手

TO DO: 搭建门票助手， 可以对门票业务进行查询

2023年4、5、6月一日门票，二日门票的销量多少？帮我按照周进行统计

2023年7月的不同省份的入园人数统计帮我查看2023年10月1-7日销售渠道订单金额排名

tkt_orders数据表  

<html><body><table><tr><td>字段名</td><td>含义说明</td></tr><tr><td>order_time</td><td>订单日期</td></tr><tr><td>account_id</td><td>预定用户ID</td></tr><tr><td>gov_id</td><td>商品使用人身份证号</td></tr><tr><td>gender</td><td>使用人性别</td></tr><tr><td>age</td><td>年龄</td></tr><tr><td>province</td><td>使用人省份</td></tr><tr><td>SKU</td><td>商品SKU名</td></tr><tr><td>product_serial_no</td><td>商品ID</td></tr><tr><td>eco_main_order_id</td><td>订单ID</td></tr><tr><td>sales_channel</td><td>销售渠道</td></tr><tr><td>status</td><td>商品状态</td></tr><tr><td>order_value</td><td>订单金额</td></tr><tr><td>quantity</td><td>商品数量</td></tr></table></body></html>

# CASE：门票助手

Thinking: 如何使用Function Call, 整体的搭建流程是怎样的？

Step1.系统初始化

选择WebUI模式，用户通过网页输入问题，助手自动完成SQL查询并返回结果，右侧可列出常见问题。

·设置系统prompt，描述门票表结构和常见查询需求·注册SQL查询工具（exc_sql），用于执行数据查询。

# Step3.设置交互模式

Step4.Function Call机制

# Step2.助手实例化

使用Qwen-Agent的\`Assistant类，加载LLM 配置、系统 prompt 和 function_list（只包含exc_sql）。

·用户输入自然语言问题。  
·LLM解析意图并自动生成SQL查询语句。  
exc_sqI工具被自动调用，执行SQL并返回查询结果。  
·结果通过终端或WebUI展示给用户。

# CASE: 门票助手 (system_prompt)

system_prompt $\mathbf { \tau } = \mathbf { \tau }$ ""我是门票助手，以下是关于门票订单表相关的字段，我可能会编写对应的SQL，对数据进行查询--门票订单表

CREATE TABLE tkt_orders (order_time DATETIME, --订单日期account_id INT, --预定用户IDgov_id VARCHAR(18), --商品使用人ID (身份证号)gender VARCHAR(10), --使用人性别age INT, --年龄province VARCHAR(30), --使用人省份SKU VARCHAR(100), -- 商品SKU名product_serial_no VARCHAR(3O)，-- 商品IDeco_main_order_id VARCHAR(2O),-- 订单IDsales_channel VARCHAR(20), --销售渠道status VARCHAR(30), -- 商品状态

Thinking: 是否能找到原始的数据表metadata，是否有常用的术语需要提供， 方便后续撰写SQL

# CASE：门票助手 (exc_sql工具注册)

<html><body><table><tr><td>from qwen_agent.tools.base import BaseTool, register_tool def call(self, params: str, **kwargs) -> str: import json @register_tool('exc_sql') args = json.loads(params) class ExcSQLTool(BaseTool): sql_input = args['sql_input']</td></tr></table></body></html>

Thinking：这个地方是否可以通过用户的需求， 自适应进行调整？

# CASE: 门票助手 (Assistant 初始化与function_list)

def init_agent_service(): ""初始化门票助手服务" $1 1 m \_ { \cdot } \mathrm { c f g } = \left\{ \begin{array} { r l } \end{array} \right.$ 'model': 'qwen-turbo-2025-04-28', 'timeout': 30, 'retry_count': 3, } try: bot $\mathbf { \tau } = \mathbf { \tau }$ Assistant( IIm=llm_cfg, name $\mathrel { \mathop : }$ 门票助手， description $| = |$ 门票查询与订单分析， system_message $\ c =$ system_prompt, function_list $\Finv$ ['exc_sql']，#只传工具名字符串

print("助手初始化成功！") return bot   
except Exception as e: print(f"助手初始化失败:{str(e)}") raise

# CASE: 门票助手 (Web 图形界面）

def app_gui():

"""图形界面模式，提供Web 图形界面"bot $\mathbf { \tau } = \mathbf { \tau }$ init_agent_service()chatbot_config = {prompt.suggestions': [2023年4、5、6月一日门票，二日门票的销量多少？帮  
我按照周进行统计，2023年7月的不同省份的入园人数统计帮我查看2023年10月1-7日销售渠道订单金额排名']  
}  
WebUI(bot,chatbot_config $\ c =$ chatbot_config  
).run()

function call 相关逻辑全部通过 Assistant 的function_1ist机制与工具注册实现exc_sq1 工具负责 SQL 查询，注册后可被 LLM调用。支持终端(app_tui)和 WebUI 两种交互方式.

# CASE：门票助手

2023年4、5、6月一日门票，二日门票的销量多少？帮我按照周进行统计

![](images/5921a98ebe56d8c1cb9f9525beaf11b5666af82889448c651ef698d329f44c0e.jpg)

>Start calling tool "exc_sq.\*".

● Finished tool calling.

以下是2023年4、5、6月一日门票和二日门票的周销量统计：

![](images/17bfc5feaf20b96adc757bdfefaeac182e84df1d8f92a1769fc6a63ddd66a57f.jpg)

√Startcalling tool "exc_sql."..

{"sq_input":"SELECTDATE_FRMAT(order_time,'%Y-%U)ASweek,\nSUM(CASEWHENSKULIKE'UniversalStudios BejingOne-Day% THEN quantity ELSE 0 END) AS one_day_ticket_sales, $\mathsf { \Omega } \backslash \mathsf { n }$ SUM(CASE WHEN SKU LIKE 'USB%' THEN quantity ELSE 0 END) AS two_day_ticket_sales\nFROMtkt_orders\nWHEREorder_timeBETWEEN'2023-04-01'AND'2023-06-30'\GROUPBYweek\nORDERBY week;"}

<html><body><table><tr><td>周数</td><td>一日门票销量</td><td>二日门票销量</td></tr><tr><td>2023-13</td><td>3367</td><td>2732</td></tr><tr><td>2023-14</td><td>19444</td><td>14267</td></tr><tr><td>2023-15</td><td>20123</td><td>14888</td></tr><tr><td>2023-16</td><td>19399</td><td>15007</td></tr><tr><td>2023-17</td><td>19489</td><td>14603</td></tr><tr><td>2023-18</td><td>19933</td><td>15249</td></tr><tr><td>2023-19</td><td>19422</td><td>14783</td></tr><tr><td>2023-20</td><td>19594</td><td>14428</td></tr><tr><td>2023-21</td><td>19163</td><td>14339</td></tr><tr><td>2023-22</td><td>19573</td><td>14297</td></tr></table></body></html>

如果需要更详细的分析或进一步的数据，请告诉我！

√Finished tool calling.   

<html><body><table><tr><td>week</td><td>one_day_ticket_sales</td><td>two_day_ticket_sales</td></tr><tr><td>2023-13</td><td>3367</td><td>2732</td></tr><tr><td>2023-14</td><td>19444</td><td>14267</td></tr><tr><td>2023-15</td><td>20123</td><td>14888</td></tr><tr><td>2023-16</td><td>19399</td><td>15007</td></tr><tr><td>2023-17</td><td>19489</td><td>14603</td></tr><tr><td>2023-18</td><td>19933</td><td>15249</td></tr><tr><td>2023-19</td><td>19422</td><td>14783</td></tr><tr><td>2023-20</td><td>19594</td><td>14428</td></tr><tr><td>2023-21</td><td>19163</td><td>14339</td></tr><tr><td>2023-22</td><td>19573</td><td>14297</td></tr></table></body></html>

# CASE：门票助手

2023年7月的不同省份的入园人数统计

> Start calling tool "exc_sql."..

→Finished tool calling

以下是2023年7月不同省份的入园人数统计：

<html><body><table><tr><td>省份</td><td>入园人数</td></tr><tr><td>北京市</td><td>99893</td></tr><tr><td>江苏省</td><td>47290</td></tr><tr><td>河北省</td><td>46602</td></tr><tr><td>山东省</td><td>43762</td></tr><tr><td>广东省</td><td>42601</td></tr><tr><td>上海市</td><td>40782</td></tr><tr><td>浙江省</td><td>38042</td></tr><tr><td>辽宁省</td><td>24910</td></tr><tr><td>湖北省</td><td>24231</td></tr><tr><td>四川省</td><td>22672</td></tr></table></body></html>

如果需要更详细的分析或进一步的数据，请告诉我！

user

√Start calling tool "exc_sq\*..

{"sqinput":"SELECTprovince,SUMquantity)ASvisitor_count\nFROMtkt_orders\nWHEREorder_timeBTWEEN'2023-07-01'AND 2023-07-31'\nGROUP BY province\nORDER BY visitor_count DESC;"}

√Finished tool calling

<html><body><table><tr><td>province</td><td>visitor_count</td></tr><tr><td>北京市</td><td>99893</td></tr><tr><td>江苏省</td><td>47290</td></tr><tr><td>河北省</td><td>46602</td></tr><tr><td>山东省</td><td>43762</td></tr><tr><td>广东省</td><td>42601</td></tr><tr><td>上海市</td><td>40782</td></tr><tr><td>浙江省</td><td>38042</td></tr><tr><td>辽宁省</td><td>24910</td></tr><tr><td>湖北省</td><td>24231</td></tr><tr><td>四川省</td><td>22672</td></tr></table></body></html>

# CASE：门票助手

帮我查看2023年10月1-7日销售渠道订单金额排名

√ Start calling tool "exc_sq.\*"..

{sqinput":"SELECTsales_cannel,SUM(ordervalue)AStotal_rdervalue\nFROMtkt_orders\nWHEREorder_timeBETWEE202- 10-01'AND '2023-10-07'\nGROUP BY sales_channel \nORDER BY total_order_value DESC;"}

√Finished tool calling.

<html><body><table><tr><td>sales_channel</td><td>total_order_value</td></tr><tr><td>B2B_OTA</td><td>2.0915e+07</td></tr><tr><td>B2C_UBRAPP</td><td>1.03013e+07</td></tr><tr><td>B2B_TTAGIT</td><td>3.51182e+06</td></tr></table></body></html>

以下是2023年10月1日至7日销售渠道的订单金额排名：

<html><body><table><tr><td>销售渠道</td><td>订单金额</td></tr><tr><td>B2B_OTA</td><td>20,915,000</td></tr><tr><td>B2C_UBRAPP</td><td>10,301,300</td></tr><tr><td>B2B_TTAGIT</td><td>3,511,820</td></tr></table></body></html>

如果需要更详细的分析或进一步的数据，请告诉我！

TODO：快来搭建你的业务助手吧！

# 打卡：业务助手

练习使用LLM/Agent $^ +$ Function Calling使用，可以使用Qwen3或Qwen-Agent如果你在本地有MySQL，可以基于自己的数据，进行业务查询

1）某个月份的销量是多少？  
2）相比于上个月，这个月的销量环比增长多少？  
3） 不同省份的销售额是多少？  
4）某个时间段，销售金额Top3的渠道是哪些？

# CASE：门票助手 （可视化图表）

Thinking：如何在exc_sql查询数据之后， 将数据进行可视化图表呈现？

方法1：编写新的函数plot_data，传入Markdown的图表，进行可视化  
方法2：在原有exc_sql函数基础上，增加plot_data的功能，返回结果包括：数据表markdown以及可视化  
的图表png

Thinking: 方法1的问题是什么？

Markdown传参可能更大，另外要绘制的x,y参数也不一定能传递准确  
编写Markdown绘图有一定的难度，也需要先将Markdown转化为df (dataframe格式）然后再进行绘制  
在qwen-agent中，很难保存中间的df，不同用户实例之间的维护成本可能较高  
$\Rightarrow$ 采用方法2

# 可视化图表：实现步骤

在传统实现中，数据查询和可视化通常是分开的两个步骤（工具）：

先执行SQL查询获取数据·再调用可视化工具进行图表绘制

我们的优化是将两者集成到一个工具中，实现：

一次调用，完成查询和可视化自动推断，图表类型和字段映射(x轴、v轴)·结果双输出，同时返回表格和图表

# 可视化图表：实现步骤

# Step1，SQL查询获取数据

#执行SQL查询   
df $\mathbf { \tau } = \mathbf { \tau }$ pd.read_sql(sql_input,engine)   
#生成markdown表格   
md $\mathbf { \tau } = \mathbf { \tau }$ df.head(10).to_markdown(index $\ c =$ False)   
Step2，自动推断图表字段   
#自动推断x/y字段   
x_candidates $\mathbf { \tau } = \mathbf { \tau }$ df.select_dtypes(include $\ c =$ ['object']).columns.tolist()   
if not x_candidates: X_candidates $\mathbf { \tau } = \mathbf { \tau }$ df.columns.tolist()   
$\mathsf { x } = \mathsf { x }$ _candidates[0]   
Y_candidates $\mathbf { \tau } = \mathbf { \tau }$ df.select_dtypes(include $\mathbf { \tau } = \mathbf { \tau }$ ['number']).columns.tolist()   
y_fields $\mathbf { \Psi } = \mathbf { \Psi } \mathbf { \Psi }$ _candidates

字段推断逻辑：

x轴字段：优先选择第一个字符串类型(object）的列，如日期、分类名称等y轴字段：选择所有数值类型的列，支持多系列数据展示

# 可视化图表：实现步骤

# Step3，柱状图绘制

plt.figure(figsize=(8, 5))   
bar_width $= 0 . 3 5$ if len(y_fields) $> 1$ else 0.6   
x_labels $\mathbf { \tau } = \mathbf { \tau }$ df[x].astype(str)   
（204号 $\mathsf { X \_ p o s } = \mathsf { r a n g e } ( \mathsf { l e n } ( \mathsf { d f } ) )$   
for idx, Y_col in enumerate(y_fields): plt.bar([p + idx\*bar_width for p in ×_pos], df[y_col],width=bar_width,label=y_col)

# 绘图逻辑：

创建适当大小的图表根据y轴字段数量调整柱宽支持多系列数据的并列柱状图每个y轴字段绘制一组柱子自动错开位置，避免柱子重叠

# 可视化图表：实现步骤

# Step4， 图表样式设置

plt.xlabel(x)   
plt.ylabel(','.join(y_fields))   
plt.title(f"{' &'.join(y_fields)} by {x}")   
plt.xticks([p $^ +$ bar_width\*(len(y_fields)-1)/2 for p in X_pos],x_labels,rotation=45,ha $= "$ right')   
plt.legend()   
plt.tight_layout()

# 样式设置：

设置x轴、y轴标签  
自动生成图表标题  
x轴标签45度倾斜，避免重叠  
添加图例，区分多系列数据  
调整图表布局，确保所有元素可见

# 可视化图表：实现步骤

# Step5， 图表保存与返回

#自动创建目录

save_dir $\mathbf { \tau } = \mathbf { \tau }$ os.path.join(os.path.dirname(__file__),'image_show')

os.makedirs(save_dir,exist_ok $\ c =$ True)   
#生成唯一文件名   
filename $\mathbf { \tau } = \mathbf { \tau }$ f'bar_{int(time.time()\*1000)}.png'   
save_path $\mathbf { \tau } = \mathbf { \tau }$ os.path.join(save_dir, filename)   
plt.savefig(save_path)   
plt.close()   
img_path $\mathbf { \tau } = \mathbf { \tau }$ os.path.join('image_show', filename)   
img_md $\mathbf { \sigma } = \mathbf { \sigma }$ f'![柱状图]({img_path})'   
return f"{md}\n\n{img_md}"

保存与返回逻辑：

自动创建图片保存目录生成基于时间戳的唯一文件名保存图片到本地生成markdown格式的图片引用返回"表格 $^ +$ 图片"组合结果

# CASE：门票助手 （可视化图表）

# 2023年4、5、6月一日门票，二日门票的销量多少？帮我按照周进行统计

Start calling tool "exc_sq.\*..

■ Finished tool calling.

以下是2023年4、5、6月一日门票和二日门票的周销量统计：

<html><body><table><tr><td>week_number</td><td>一日门票销量</td><td>二日门票销量</td></tr><tr><td>2023-13</td><td>3367</td><td>2732</td></tr><tr><td>2023-14</td><td>19444</td><td>14267</td></tr><tr><td>2023-15</td><td>20123</td><td>14888</td></tr><tr><td>2023-16</td><td>19399</td><td>15007</td></tr><tr><td>2023-17</td><td>19489</td><td>14603</td></tr><tr><td>2023-18</td><td>19933</td><td>15249</td></tr><tr><td>2023-19</td><td>19422</td><td>14783</td></tr><tr><td>2023-20</td><td>19594</td><td>14428</td></tr><tr><td>2023-21</td><td>19163</td><td>14339</td></tr><tr><td>2023-22</td><td>19573</td><td>14297</td></tr></table></body></html>

![](images/caebf5bec680f49bc4d4f3b6d46df207c22c30b81bfcaced0b82f8b4c42e355c.jpg)  
one_day_ticket_sales&two_day_ticket_salesbyweek_number

# CASE：门票助手 （可视化图表）

# 我看到第13周数据有异常，帮我按照天、渠道的维度进行统计，给我他们的表现

》 Start calling tool "exc_sql."...

■Finished tool calling.

以下是2023年第13周（即2023-04-01）一日门票和二日门票按天和销售渠道的销量统计：

<html><body><table><tr><td>order_date</td><td>sales_channel</td><td>一日门票销量</td><td>二日门票销量</td></tr><tr><td>2023-04-01</td><td>B2B_OTA</td><td>2069</td><td>1633</td></tr><tr><td>2023-04-01</td><td>B2B_TTAGIT</td><td>339</td><td>222</td></tr><tr><td>2023-04-01</td><td>B2C_UBRAPP</td><td>959</td><td>877</td></tr></table></body></html>

Thinking: 这里为什么提取的数据不对？

WHERE order_time BETWEEN'2023-04-01' AND'2023-06-30' AND DATE_FORMAT(order_time,'%Y-%U')='2023-13'

![](images/93e34f26ceb76d1d1cd82a58b103ff221be98685655804d667742747c84c6183.jpg)

# CASE：门票助手 (可视化图表）

# 我看到第13周（2023年3月27日-4月2日）数据有异常，帮我按照天、渠道的维度进行统计，给我他们的表现

> Start calling tool "exc_sql."..

■Finished tool calling.

以下是2023年3月27日至4月2日（第13周）一日门票和二日门票按天和销售渠道的销量统计：

<html><body><table><tr><td>order_date</td><td>sales_channel</td><td>一日门票销量</td><td>二日门票销量</td></tr><tr><td>2023-03-27</td><td>B2B_OTA</td><td>1596</td><td>1111</td></tr><tr><td>2023-03-27</td><td>B2B_TTAGIT</td><td>274</td><td>183</td></tr><tr><td>2023-03-27</td><td>B2C_UBRAPP</td><td>694</td><td>499</td></tr><tr><td>2023-03-28</td><td>B2B_OTA</td><td>1537</td><td>991</td></tr><tr><td>2023-03-28</td><td>B2B_TTAGIT</td><td>245</td><td>190</td></tr><tr><td>2023-03-28</td><td>B2C_UBRAPP</td><td>816</td><td>535</td></tr><tr><td>2023-03-29</td><td>B2B_OTA</td><td>1618</td><td>1249</td></tr><tr><td>2023-03-29</td><td>B2B_TTAGIT</td><td>205</td><td>144</td></tr><tr><td>2023-03-29</td><td>B2C_UBRAPP</td><td>663</td><td>493</td></tr><tr><td>2023-03-30</td><td>B2B_OTA</td><td>1486</td><td>868</td></tr></table></body></html>

![](images/c7675887715863bddefbde08f81b81ce856da56e8e9fd556f18023cc1e043005.jpg)

Thinking: 如何将渠道显示出来？

# CASE：门票助手 (可视化图表）

# 我看到第13周（2023年3月27日-4月2日）数据有异常，帮我按照天、渠道的维度进行统计，给我他们的表现

> Start calling tool "exc_sql."..

■Finished tool calling.

以下是2023年3月27日至4月2日（第13周）一日门票和二日门票按天和销售渠道的销量统计：

<html><body><table><tr><td>order_date</td><td>sales_channel</td><td>一日门票销量</td><td>二日门票销量</td></tr><tr><td>2023-03-27</td><td>B2B_OTA</td><td>1596</td><td>1111</td></tr><tr><td>2023-03-27</td><td>B2B_TTAGIT</td><td>274</td><td>183</td></tr><tr><td>2023-03-27</td><td>B2C_UBRAPP</td><td>694</td><td>499</td></tr><tr><td>2023-03-28</td><td>B2B_OTA</td><td>1537</td><td>991</td></tr><tr><td>2023-03-28</td><td>B2B_TTAGIT</td><td>245</td><td>190</td></tr><tr><td>2023-03-28</td><td>B2C_UBRAPP</td><td>816</td><td>535</td></tr><tr><td>2023-03-29</td><td>B2B_OTA</td><td>1618</td><td>1249</td></tr><tr><td>2023-03-29</td><td>B2B_TTAGIT</td><td>205</td><td>144</td></tr><tr><td>2023-03-29</td><td>B2C_UBRAPP</td><td>663</td><td>493</td></tr><tr><td>2023-03-30</td><td>B2B_OTA</td><td>1486</td><td>868</td></tr></table></body></html>

![](images/de50d4ad92ba05e25de30a191e7d3c4d1c6d22997199803c575a153b6d21d5b6.jpg)

Thinking: 如何将渠道显示出来？

# CASE：门票助手 (可视化图表)

Thinking: 如何将渠道显示出来？

采用分组与透视

如果存在 object_columns，则用pd.pivot_table 以 $\textsf { \textbf { x } }$ 轴为index，object_columns 为columns，num_columns 为  
values，自动聚合  
支持多object、多数值列，自动生成多级分组

def generate_chart_png(df_sql, save_path):

Version更新:

assistant_ticket_bot-1:实现了function call调用exc_sqlassistant_ticket_bot-2：添加了基本的绘制图表功能assistant_ticket_bot-3：进一步完善绘制图表功能，支持多类别变量的透视图可视化

# Function Cali的微调

Thinking：Functioncall是否需要微调？

通常大模型具备Function Cali的能力，但有时候针对特定的Function Call理解和提参能力不强 $\Rightarrow$ 可以微调FunctionCall的微调目标，是教会模型下面两件事：

·判断是否需要调用函数（比如"查天气"需要，而"写首诗"不需要）。  
·正确提取参数并生成格式化的调用指令（比如转成JSON）。

# Function Call的微调

Thinking: 微调的步骤是怎样的？

Step1，准备数据

输入：用户问题 （如"北京今天天气？"）。

函数描述：告诉模型有哪些函数可用（比如get_weather(city,date)）。

期望输出:

·需要调用时：生成JSON格式的函数调用(如{"name":"get_weather","arguments":{"city":"北京","date":"今天"}1）。

·不需要时：直接生成回答 (如"你好，今天星期一..."）。

Step2， 模型训练

选一个擅长理解指令的预训练模型，如Qwen。

用上述数据训练模型，让它学会"根据问题和函数描述，决定是否调用函数，并生成正确格式"。

# Function Cali的微调

FunctionCall微调的关键点：

·数据质量：需覆盖各种场景（需要/不需要调用、参数变化等）。函数描述要清晰：模型靠描述理解函数用途。  
·避免误触发：加入足够多“无需调用"的样本，防止模型滥用函数。

# Function Call的微调

# 微调数据集参考：

https://huggingface.co/datasets/NousResearch/herme s-function-calling-v1

训练LLM模型根据自然语言指令执行函数调用并返回结构化输出。数据集涵盖了各种对话场景，要求AI代理能够解释查询并执行适当的单个或多个函数调用。

例如，当被要求"查找下周五从纽约飞往洛杉矶的航班"时，函数调用代理可以解释请求，生成必要的函数调用（例如search_flights），并返回结果。

田 Dataset Viewer $a$ Auto-converted to Parquet </>API Embed 田 Data Studio   
Subset (5) Split (1)   
func_calling_singleturn $\mathbf { \nabla } \cdot \mathbf { \varepsilon }$ 1.89k rows train · 1.89k rows   
Q Search this dataset   
id conversations 一 category   
string ·lengths list ·lengths string · classe   
36 36 3 3 63 values   
85f6c398-69c7- [ {"from": "system"，"value": "You are a function IoT and Home   
4df2-aed1-... calling AI model. You are provided with function... Automation   
89ef3c87-66bd- [ {"from": "system"，"value": "You are a function IoT and Home   
46ee-9297-.. calling AI model. You are provided with function... Automation   
14657d01-d6d1- [ {"from":"system"，"value": "You are a function IoT and Home   
46df-8eb1-... calling AI model. You are provided with function... Automation   
c483f963-8a29- [{"from":"system"，"value": "You are a function IoT and Home   
4ff0-a684-.. calling AI model. You are provided with function.. Automation   
81ad724a-bb74- [ { "from": "system"，"value": "You are a function IoT and Home   
420f-8221-.. calling AI model. You are provided with function... Automation   
7d99abac-f27f- [{"from":"system"，"value": "You are a function IoT and Home < Previous 1 2 3 19 Next >

# Function Cali的微调

# 该数据集由5个数据集组成，分别是：

func-calling-singleturn.json -单轮函数调用  
·func-calling.json-多轮对话函数调用  
·glaive-function-calling-5k.json-Glaive Al 更新和清理后的Glaive函数调用5k数据集  
·json-mode-agentic.json-高级JSON 结构化输出样本  
·json-mode-singleturn.json-单轮 JSON 结构化输出样本

<html><body><table><tr><td>id string·lengths</td><td>conversations list·lengths</td><td></td><td>category string·classes</td><td>subi str:</td></tr><tr><td>36 100%</td><td>3 100%</td><td>IoT and Ho...</td><td>0.8%</td><td>24</td></tr><tr><td>85f6c398-69c7- 4df2-aed1- 29d614a93a26</td><td>[{"from":"system"，"value":"You are a function calling AI model.You are provided with function signatures within <tools> </tools> XML tags.You may call one or more functions to assist with the user query. Don't make assumptions about what values to plug into functions.\n<tools>\n[{'type':</td><td></td><td>IoT and Home Automation</td><td>Secl Mana</td></tr><tr><td></td><td>'function'，'function':{'name': 'get_camera_live_feed'，'description':'Retrieves the live feed from a specified security camera.' 'parameters':{'type':'object'，'properties'： {'camera_id':{'type':'string'，'description': 'Theunique identifier for the camera.'}, 'stream_quality':{'type':'string'，'description': 'The desired quality of the live stream.'，'enum': ['720p'，'1080p'，'4k']}}，'required'： ['camera_id']}}}，{'type':'function'，'function': {'name':'list_all_cameras'，'description':'Lists</td><td></td><td></td><td></td></tr></table></body></html>

# func-calling-singleturn.json 中的某条训练样本

# Thank You Using data to solve problems