# Agent智能体系统的设计与应用

# 今天的学习目标

# Agent智能体系统的设计与应用

AlAgent对比  
·智能体架构设计  
反应式(Reactive)  
深思熟虑 (Deliberative)  
混合式 (Hybrid)CASE：私募基金运作指引问答助手 (反应式)CASE：智能投研助手 (深思熟虑)CASE：投顾AI助手 (混合式)

# Al Agent:

规划（Planning）：将任务分解为较小的、可管理的子目标

通过LLM，能够自主理解、规划、执行复杂任务的系统。给它一个目标，AIAgents就能完成剩下的全部工作

记忆（Memory）：短期记忆，进行上下文学习；长期记忆，-般通过外部载体储存和快速检索来实现

工具使用（Tooluse）：调用外部API，获取额外信息

![](images/0fa20109f65ee0aafc82b152ae8e153466cf98223cc5a707872900300e1453d5.jpg)

# Generative Agents: Interactive Simulacra of Human Behavior

# 从自动化到自主化：

Joon Sung Park Stanford University Stanford,U joonspk@stanford.edu

Joseph C.O'Brien Stanford University Stanford,U jobrien3@stanford.edu

Carrie J. Cai   
GoogleResearch   
Mountain View, CA,USA   
cjcai@google.com   
MeredithRingel Morris   
Google Research   
Seattle,WA,U   
merrie@google.com   
Percy Liang   
Stanford University   
Stanford,U   
pliang@cs.stanford.edu   
Michael S.Bernstein   
Stanford University   
Stanford,U   
msb@cs.stanford.edu

Generative Agents: Interactive Simulacraof Human Behavior， 2023https://arxiv.0rg/pdf/2304.03442v1.pdfGoogle和Stanford学者构造了一个《西部世界》小镇，打造模拟人类行为的AgentGenerativeAgents（生成式智能体），利用生成模型来模拟可信人类行为的Agent，并证明它们能生成可信的个人和突发的群体行为

![](images/813c43a5dd4ea4d03decef65be5a175fbb9fc93fe3fdf8a40c2568b5fee3e78a.jpg)

# Generative Agents

This is a pre-computed replay of a simulation that accompanies the paper entitled "Generative Agents: Interactive Simulacra of Human Behavior." It is for demonstration purposes only.

Current Time:   
Monday, February 13, 2023 at   
6:13:10AM

Play 1 Pause

![](images/6d6a9540b541875a680915dc24f8c61c90555e3039b7d3e6cc5fbdea6e3ad4ec.jpg)

http://reverie.herokuapp.com/arXiv_Demo/#25个Agent居住在Smallville小镇，每个Agent都可以：

与别人和环境交流；  
记住并回忆它们所做的和观察到的事情；反思这些观察结果；  
制定每天的计划

![](images/f00507c6185a3724848db80218f9d5537dac3dbc7de7b5394e3fb6fb6c70a81b.jpg)

# Generative Agents

用自然语言设定每个Agent的角色，包括它们的职业与其他Agent的关系

比如：JohnLin是一名药店店主，他乐于助人。他一直在寻找使客户更容易获得药物的方法。JohnLin的妻子是大学教授MeiLin，它们和学习音乐理论的儿子EddyLin住在一起；JohnLin 非常爱它的家人；JohnLin认识隔壁的老夫妇SamMoore和Jennifer Moore 好几年·...

在沙盒的每个Step，Agent都输出一个自然语句，描述它们当前的动作，比如：IsabellaRodriguez正在写日记、Isabella Rodriguez正在查看邮件等。

![](images/9ccbcd6753c340a2fc36b3e71f440e23bb5798653520cc745177871276203584.jpg)

然后这些自然语言将转化为影响沙盒的具体动作动作以一组表情符号显示在沙盒界面上，这些表情符号提供了动作的抽象表征。

# Agent与环境交互

Smallville小镇有许多公共场景，包括咖啡馆、酒吧、公园、学校、宿舍、房屋和商店。

每个公共场景包括自己的功能和设施，比如房子中有厨房、厨房中有炉子。在Agent的生活空间中有床、桌子、衣柜、架子、浴室、厨房等。

Agent可以在Smallville小镇随意走动，导航前往一座建筑，或者去接近另一个Agent。Agent的移动由GenerativeAgents的架构和沙盒引擎控制（当模型指示Agent移动到某个位置时，它会计算Agent到达目的地的步行路径，然后开始移动）

![](images/6f92a17dfc6357e57bb6d35dc80ad2d71ba815437e6d7a20c1befcbe5d0830cd.jpg)  
Figure 2:TheSmalvillsandbox world,withareaslabeled.Therootnode describes theentire world,childrendescribeareas (e.g.,houses,cafe,stores),andleaf nodesdescribejects (e.g.,table,bookshelf).Agentrememberasubraphflecting the parts of the world they have seen,in the state that they saw them.

在公共环境中，Agent会影响其他人的状态，比如：某Agent睡觉时床是被占用的，当Agent用完早餐冰箱可能是空的

# Agent之间的信息传播

GenerativeAgents具有社交属性，信息可以在Agent之间进行传播

比如Sam和Tom在杂货店中相遇，Sam告诉了Tom他在竞选镇长；

在Sam离开后，Tom和John讨论了Sam 赢得选举的机会;

Sam: Hey Tom, how's it going?

Tom: Good, thanks. What's up?

逐渐地，Sam的竞选成为镇上的热门话题，有人支持他，有人犹豫不决。

Tom: Really? That's great news! Why are you running? Sam: l've been involved in local politics for years now,

Sam: Well, I wanted to talk to you about something. l'm actually running for mayor in the upcoming local election.

John: I heard that Sam Moore is running for mayor in the local election. Do you think he has a good chance of winning?

Tom: l do think he has a good chance. He's been working hard in the community and I think he will get a lot of support. What do you think?

John: l think it's great that he's running. I'm curious to see who else is running and how the election will turn out.

# Agent的关系记忆

随着时间的推移，小镇上的Agent形成了新的关系，并记住了它们与其他Agent的互动。

比如Sam 一开始不认识 Latoya。

在约翰逊公园散步时，Sam碰到了Latoya，互相做了自我介绍，Latoya提到自己正在进行一个摄影项目：

Latoya：我正在这里给一个项目拍摄照片。

在后来他们又相遇了，Sam与Latoya的对话表明了他们还记得这件事

Sam：Latoya，你的项目进展如何？Latoya：进展得好！

# 记忆流:

：是GenerativeAgents的核心模块，全面记录Agent经验的数据库。  
·Agent会从记忆流中检索相关记录，用来规划Agent的动作，并对环境做出适当反应。每次行为都会被记录，从而生成更高级别的行为指令。  
所有的内容都会被记录，并以自然语言进行推理这样Agent能够使用大语言模型 （GPT3.5或GPT4.0）进行推理。

# Generative Agents核心模块

![](images/bf3071388e49de655597064b81c96a6536847f0cf90b96b5002c1ca1e22a66a9.jpg)

1）长期记忆，Agent要做多轮决策，所以要考虑更长的上下文，这些信息会超过GPT模型的token上限。

2）外部工具，使用外部工具可以让GPT调用更多的服务作为输入/输出，增强GPT的能力，这好比人会使用这些外部工具，那么GPT也可以使用

3）短期记忆，基于Attention机制将长期记忆中最相关的部分喂给GPT，生成结果

# Al Agent对比

AIAgent工具定位与对比  

<html><body><table><tr><td>工具</td><td>核心定位</td><td>架构特点 适用场景</td></tr><tr><td></td><td>LangChain开源LLM应用开发框架</td><td>基于ge链t（C式ain）的线性或分支工作流，支快构建RAG、对话系统、工具调用等线性</td></tr><tr><td>LangGraph杂工作流</td><td>LangChain的扩展，专注于复</td><td>基于图（Graph）的循环和条件逻辑，支持 需要循环、动态分支或状态管理的复杂任务 多Agent协作 (如自适应RAG、多Agent系统)</td></tr><tr><td>Agent</td><td>通义干问的AI Agent框架</td><td>基于阿里云大模型，支持多模态交互与工 开源，集成多种工具，MCP调用</td></tr><tr><td>Coze</td><td>字节跳动的无代码AI Bot平台可视化拖拽界面，内置知识库、多模态插</td><td>快速部署社交平台机器人、轻量级工作流</td></tr><tr><td>Dify</td><td>开源LLM应用开发平台</td><td>开发者定制化LLM应用，需深度集成或私有 API优先，支持Prompt工程与灵活编排 化部署</td></tr></table></body></html>

# Agent: 自主智能体的力量

Agent通常被实现为LLM通过工具调用（基于环境反馈）在循环中执行动作的系统。正如Anthropic指出的，Agent可以处理复杂的任务，但其实现很简单。它们通常是LLM根据环境反馈使用工具的循环。因此，清晰全面的设计工具集以及文档对于Agent的成功至关重要。

![](images/8169fb218a5c438259cfde0c249934f1f18167eacb0daccc15476d95ee2f21c2.jpg)

# Agent: 自主智能体的力量

Thinking: 什么时候使用Agent?

Agent适用于那些开放性问题，这些问题很难或无法预测所需的步骤数量，并且无法硬编码固定路径。  
LLM可能会运行多个回合，因此你需要对其决策能力有一定的信任。  
智能体的自主性使其非常适合在受信任的环境中扩展任务。然而，自主性也意味着更高的成本和可能出现的错误累积。  
$\Rightarrow$ 建议在沙盒环境中进行广泛的测试，并设置适当的防护栏。编程Agent可以解决涉及对多个文件进行编辑的任务。  
ComputerUse实现中，Claude通过计算机完成任务。

# 打造Best Practice

AI智能体和工作流是互补的，可以集成在一起以实现最佳效果，尤其是在复杂的现实世界应用中。·增强自动化  
AI智能体可以自主处理特定任务，而工作流则将这些任务协调成一个连贯、高效的过程。  
·可扩展性  
在结构化工作流中结合多个AI智能体，可以使组织高效扩展运营，减少人工工作量，提高生产力。·弹性与适应性  
虽然单个智能体可以应对局部变化，但工作流可以动态调整整体流程，用来与战略目标保持一致。在智能制造系统中：  
·AI智能体可以监控设备性能、预测维护需求并优化生产计划。  
·工作流则负责原材料采购、生产排序、质量保证和物流，确保从原材料到产品交付的无缝过渡。

# 打造Best Practice

选择适合你的系统才是成功的关键：

·在AI领域，成功并不是关于构建复杂的系统，而是构建最适合需求的系统.·从简单的提示开始，只有在简单方案解决步了时，再添加多步智能体系统。在实现智能体时，有三个核心原则：

1.保持智能体设计的简洁性：避免不必要的复杂性，专注于核心功能。  
2.优先考虑透明性：明确展示智能体的规划步骤，让用户清楚了解其决策过程。  
3.打造Function/MCP：打造工具，以及说明文档和测试，确保Agent与外部环境的交互。

框架可以帮助你快速上手，但不要害怕在进入生产阶段时减少抽象层，直接使用基础组件。遵循这些原则，你可以创建出不仅强大而且可靠、可维护且值得用户信赖的智能体系统。

# 智能体分类 (反应式 Reactive)

Thinking: 都有哪些典型的AIAgent?

1、反应式 (Reactive)

反应式架构： 快速决策的"直觉型"智能体

反应式架构是AI智能体设计中最简单直接的模式。在这种架构！析当前情况，确定下一步要采取的行动。然后，在环境中执行处理这些观察结果，重新评估下一步行动，选择另一个行动，

![](images/17fd6499e26c76990fcc67f2a422cd88f45151bc86322762d0fa3292aa8af147.jpg)

# 智能体分类 (反应式 Reactive)

反应式架构 (Reactive Architecture

特点：基于当前环境即时决策，无长期规划，依赖预设规则快速响应。

工作原理:

·感知： 获取环境输入（如传感器数据）。

·决策：LLM或规则系统立即生成响应动作。

·执行：执行动作并观察结果，循环往复直至任务完成。

优势:

·速度快：无复杂推理，适合毫秒级响应的场景 (如机器人避障、高频交易)

·简单可靠：行为由明确规则驱动， 易于设计和验证

# 局限：

·缺乏适应性： 无法处理未预见的场景或需多步规划的任务。

·短视性：仅优化当前动作，可能陷入局部循环（如机器人绕圈）。

![](images/38bdf1f12ec7312e7bafd3c3f71d6150beebc2e1974d2e581cf955bf308cf17b.jpg)

# 智能体分类 (反应式 Reactive)

# 典型应用:

·机器人：扫地机器人避障、 无人机紧急悬停。

·游戏NPC：敌人对玩家攻击的即时反应

·工业控制：传感器超限时触发警报或停机。

适用场景：任务规则明确、响应需实时，且无需长期策略的简单环境。

“条件反射"一一像膝跳反应一样快速直接，但无法应对复杂变化。

![](images/31a18a84ea24a7f939f22c3159da04d480e7fe13783bba535df22b989f758839.jpg)

# CASE: 私募基金运作指引问答助手

# TODO：私募基金运作指引问答助手

采用反应式智能体架构设计，区别于传统的工作流模式，该智能体能够主动思考、自主决策并选择合适的工具来回答用户问题，具备真正的智能体特性。

1.自主决策：智能体能够根据问题类型自主选择使用哪种工具回答问题  
2.透明思考过程：展示清晰的思考过程，使决策链路可追踪  
3.知识边界感知：明确区分知识库内容和模型知识  
4.多工具协作：集成多种工具，包括关键词搜索、类别查询和直接问答  
5.异常处理：妥善处理边界情况和超出知识范围的问题

基于LangChain的Agent框架实现，使用通义千问(Qwen-Turbo)模型作为底层大语言模型通过工具选择、思考链路和自主决策能力，提供高质量的私募基金规则咨询服务。

# CASE: 私募基金运作指引问答助手

# Step1.数据准备

系统基于私募基金运作规则构建了精简的知识库(FUND_RULES_DB)，每条规则包含：

-ID：规则唯一标识

-类别：规则所属类别(如"设立与募集"、"监管规定"等)

-问题：规则对应的常见问题-答案：规则的详细内容

"id": "rule001","category":"设立与募集","question":"私募基金的合格投资者标准是什么？","answer":"合格投资者是指具备相应风险识别能力和风险承担能力，投资于单只私募基金的金额不低于100万元且符合下列条件之一的单位和个人：\n1.净资产不低于1000万元的单位\n2.金融资产不低于300万元或者最近三年个人年均收入不低于50万元的个人"},

# CASE: 私募基金运作指引问答助手

# Step2.工具设计

# 系统实现了三种核心工具：

1.关键词搜索工具：通过关键词匹配检索相关规则，search_rules_by_keywords  
2.类别查询工具：根据规则类别查询相关规则，search_rules_by_category  
3.直接回答工具：基于问题与规则的匹配度直接回答用户问题，answer_question

# CASE: 私募基金运作指引问答助手

# Step3.Agent架构搭建

基于LangChain的Agent框架，构建了完整的反应式智能体系统：

1.自定义提示模板(CustomPromptTemplate)：定义Agent的思考和决策格式  
2.自定义输出解析器(CustomOutputParser)：解析LLM的输出，确定下一步行动  
3.Agent执行器(AgentExecutor):协调智能体与工具的交互

# CASE: 私募基金运作指引问答助手

# Step4. 知识边界处理

专门设计了处理超出知识库范围问题的机制：

1.问题主题识别：识别用户问题涉及的具体主题  
2.明确边界区分：在回答中明确区分知识库内容和模型知识  
3.提供有价值建议：引导用户寻求更权威的信息来源

# CASE: 私募基金运作指引问答助手

# 私募基金的合格投资者标准是什么？

> Entering new AgentExecutor chain...  
Question：私募基金的合格投资者标准是什么？  
Thought：我需要查询私募基金规则中关于合格投资者的标准。Action：关键词搜索  
Action Input:合格投资者 标准

Observation:类别：设立与募集可题：私募基金的合格投资者标准是什么？

答案：合格投资者是指具备相应风险识别能力和风险承担能力，投资于单只私募基金的金额不低于100万元且符合下列条件之一的单位和个人：

1．净资产不低于1000万元的单位

2．金融资产不低于300万元或者最近三年个人年均收入不低于50万元的个人我现在知道答案了。

Final Answer：私募基金的合格投资者是指具备相应风险识别能力和风险承担能力，投资于单只私募基金的金额不低于100万元且符合下列条件之一的单位和个人：

1．净资产不低于1000万元的单位；

2．金融资产不低于300万元或者最近三年个人年均收入不低于50万元的个人。

> Finished chain.

回答：私募基金的合格投资者是指具备相应风险识别能力和风险承担能力，投资于单只私募基金的金额不低于100万元且符合下列条件之一的单位和个人：

1．净资产不低于1000万元的单位；

2．金融资产不低于300万元或者最近三年个人年均收入不低于50万元的个人。

# CASE: 私募基金运作指引问答助手

# 如果我是一个净资产800万元的机构，我能投资私募基金吗？

> Entering new AgentExecutor chain...

Question：如果我是一个净资产800万元的机构，我能投资私募基金吗？Thought：我需要了解关于机构投资者资格的相关规则。  
Action:类别查询  
Action Input: 机构投资者资格Observation:未找到类别为‘机构投资者资格’的规则。  
对不起，在我的知识库中没有关于机构投资者资格的详细信息。一般来说，私募基金对投资者的资质有一定的要求，包括资金实力、投资经验等。净资产达到800万元的机构可能会符合某些私募基金的投资门槛，但具体还需要参考相关的法律法规和私募基金的具体规定。

建议您查阅最新的私募基金相关法律法规或咨询专业的金融顾问以获取准确的信息。

FinalAnswer：根据现有信息无法确定，建议查阅最新法律法规或咨询专业金融顾问。

> Finished chain.   
回答：根据现有信息无法确定，建议查阅最新法律法规或咨询专业金融顾问。

这里Agent自主选择了工具2：根据规则类别查询search_rules_by_category，没有找到知识

# CASE: 私募基金运作指引问答助手

# 如果我是一个净资产800万元的机构，我能投资私募基金吗？

> Entering new AgentExecutor chain.

Thought：我需要确认机构投资者的资格要求，以判断净资产800万元是否满足条件。Action:关键词搜索  
Action Input：机构投资者 私募基金 净资产 资格要求

Observation:类别：设立与募集

问题：私募基金的合格投资者标准是什么？  
答案：合格投资者是指具备相应风险识别能力和风险承担能力，投资于单只私募基金的金额不低于100万元且符  
合下列条件之一的单位和个人：  
1．净资产不低于1000万元的单位  
2．金融资产不低于300万元或者最近三年个人年均收入不低于50万元的个人

类别：设立与募集

问题：私募基金的最低募集规模要求是多少？  
答案：私募证券投资基金的最低募集规模不得低于人民币1000万元。对于私募股权基金、创业投资基金等其他类型的私募基金，监管规定更加灵活，通常需符合基金合同的约定。  
我现在知道答案了。

Final Answer：根据私募基金的合格投资者标准，机构投资者需要净资产不低于1000万元。因此，作为净资产为800万元的机构，您目前不符合投资私募基金的资格要求。请注意，除了净资产要求外，投资于单只私募基金的金额还不得低于100万元。建议您咨询专业法律顾问或等待净资产达到要求后再进行投资。

这里Agent自主选择了工具1:通过关键词搜索相关规则search_rules_by_keywords,找到了知识

> Finished chain.

回答：根据私募基金的合格投资者标准，机构投资者需要净资产不低于1000万元。因此，作为净资产为800万元的机构，您目前不符合投资私募基金的资格要求。请注意，除了净资产要求外，投资于单只私募基金的金额还不得低于100万元。建议您咨询专业法律顾问或等待净资产达到要求后再进行投资。

# CASE: 私募基金运作指引问答助手

# 如果我是一个净资产800万元的机构，我能投资私募基金吗？

> Entering new AgentExecutor chain.

Thought：我需要确认机构投资者的资格要求，以判断净资产800万元是否满足条件。Action:关键词搜索  
Action Input：机构投资者 私募基金 净资产 资格要求

Observation:类别：设立与募集

问题：私募基金的合格投资者标准是什么？  
答案：合格投资者是指具备相应风险识别能力和风险承担能力，投资于单只私募基金的金额不低于100万元且符  
合下列条件之一的单位和个人：  
1．净资产不低于1000万元的单位  
2．金融资产不低于300万元或者最近三年个人年均收入不低于50万元的个人

类别：设立与募集

问题：私募基金的最低募集规模要求是多少？  
答案：私募证券投资基金的最低募集规模不得低于人民币1000万元。对于私募股权基金、创业投资基金等其他类型的私募基金，监管规定更加灵活，通常需符合基金合同的约定。  
我现在知道答案了。

Final Answer：根据私募基金的合格投资者标准，机构投资者需要净资产不低于1000万元。因此，作为净资产为800万元的机构，您目前不符合投资私募基金的资格要求。请注意，除了净资产要求外，投资于单只私募基金的金额还不得低于100万元。建议您咨询专业法律顾问或等待净资产达到要求后再进行投资。

这里Agent自主选择了工具1:通过关键词搜索相关规则search_rules_by_keywords,找到了知识

> Finished chain.

回答：根据私募基金的合格投资者标准，机构投资者需要净资产不低于1000万元。因此，作为净资产为800万元的机构，您目前不符合投资私募基金的资格要求。请注意，除了净资产要求外，投资于单只私募基金的金额还不得低于100万元。建议您咨询专业法律顾问或等待净资产达到要求后再进行投资。

# CASE: 私募基金运作指引问答助手

# 私募基金可以投资哪些资产类别？

> Entering new AgentExecutor chain..  
Thought：用户询问私募基金可以投资的资产类别，我可以通过类别查询来获取相关信息。Action:类别查询  
ActionInput：私募基金可投资资产类别Observation:未找到类别为‘私募基金可投资资产类别'的规则。  
Direct response detected:对不起，在我的知识库中没有关于私募基金可投资资产类别的详细信息。根据我的经验，私募基金通常可以投资于股票、债券、房地产、大宗商品、对冲基金和其他另类资产等。但具体的投资范围可能会受到当地法律法规和基金合同的限制。建议您查阅相关法规或基金合同以获取准确的信息。>rinisnea cnain.  
回答：对不起，在我的知识库中没有关于私募基金可投资资产类别的详细信息。根据我的经验，私募基金通常可以投资于股票、债券、房地产、大宗商品、对冲基金和其他另类资产等。但具体的投资范围可能会受到当地法律法规和基金合同的限制。建议您查阅相关法规或基金合同以获取准确的信息。

# 智能体分类 深思熟虑 Deliberative

深思熟虑智能体 (Deliberative Agent)

特点：基于内部模型进行规划，通过推理选择最优行动方案，具有长期目标导向性。

核心流程：

·感知： 获取环境信息建模: 更新内部世界状态表示推理：生成候选计划并模拟结果·决策：选择最优方案执行

优势:

![](images/74655151a34b95f69af1c4dd146199a050e4289fe2ebcadc11cce3a45e937e8b.jpg)

$v$ 能处理多步复杂任务$v$ 优化长期目标而非即时反馈$v$ 适应动态变化环境

# 智能体分类 深思熟虑 Deliberative

# 典型示例：

路径规划智能体：

·生成多条候选路线>评估安全性/耗时等指标■选择最优路径执行

适用场景： 需战略规划的任务 (如物流调度、投资决策等)

像下棋高手一一每步棋都经过推演，而非凭直觉反应

![](images/0148bcdd9c56a85c4c7ce5aee97fa36f9d284879bef8c2822d293f03639b221f.jpg)

# CASE: 智能投研助手

# TO DO: 智能投研助手

为投资研究场景设计，基于LangGraph实现的深思熟虑型智能体。  
该智能体能够整合市场数据，进行多步骤分析和推理，生成投资观点和研究报告。  
与反应式智能体不同，深思熟虑型智能体通过内部建模、推理和规划，制定最优行动方案，特别适合需要多步骤思考和长期目标优化的任务。

1.内部建模：构建市场模型和行业理解  
2.多方案生成： 基于市场模型创建多个候选投资策略  
3.方案评估：对比分析各方案优劣，考虑多维度因素  
4.长期规划： 优化整体投资回报，而非单点决策  
5.推理透明： 能够解释决策过程和选择理由

# CASE: 智能投研助手 (步骤)

# 具体实现步骤：

Step1，感知阶段  
收集和整理市场数据与信息，包括：  
-市场概况和最新动态  
-关键经济和市场指标  
-近期重要新闻  
-行业趋势分析

# Step2.建模阶段

基于收集的数据构建内部世界模型，分析：

-当前市场状态评估-经济周期判断-主要风险因素-潜在机会领域-市场情绪分析

# CASE: 智能投研助手 (步骤）

# Step3.推理阶段

生成多个候选投资分析方案，每个方案包含：

-投资假设-分析方法-预期结果-置信度-方案优缺点

Step4.决策阶段

评估候选方案并选择最优投资观点，形成：

-投资论点-支持证据-风险评估-投资建议-时间框架

# CASE: 智能投研助手 (步骤）

# Step5.报告阶段

生成完整的投资研究报告，包含：

-报告标题和摘要  
-市场和行业背景  
-核心投资观点  
-详细分析论证  
-风险因素  
-投资建议  
-时间框架和预期回报

![](images/09ab745188091db63521499748443fd4537fa66f32b013c1ca73843d2cae85d8.jpg)

# CASE: 智能投研助手 (状态定义）

class ResearchAgentState(TypedDict): #输入 research topic:str # 研究主题 industry_focus:str #行业焦点 time_horizon:str #时间范围(短期/中期/长期)

#处理状态perception_data:Optional[Dict[str,Any]] # 感知阶段收集的数据world_model: Optional[Dict[str,Any]] # 内部世界模型reasoning_plans:Optional[List[Dict[str,Any]l] # 候选分析方案selected_plan:Optional[Dict[str,Any]] #选中的最优方案

#输出final_report:Optional[str] #最终研究报告

#控制流   
current_phase: Literal["perception", "modeling", "reasoning", "decision", "report"]   
error: Optional[str] #错误信息

# CASE: 智能投研助手 （输出模型）

class PerceptionOutput(BaseModel): """感知阶段输出的市场数据和信息." market_overview: str key_indicators: Dict[str, str] recent_news: List[str] industry_trends: Dict[str, str]   
class ModelingOutput(BaseModel): """建模阶段输出的内部世界模型" market_state: str economic_cycle: str risk_factors: List[str] opportunity_areas: List[str] market_sentiment: str

使用Pydantic模型严格定义各阶段输出，确保结构化数据

class ReasoningPlan(BaseModel): """推理阶段生成的候选分析方案 plan_id: str hypothesis: str analysis_approach: str expected_outcome: str confidence_level: float pros: List[str] cons: List[str]   
class DecisionOutput(BaseModel): ""决策阶段选择的最优投资观点" selected_plan_id: str investment_thesis: str supporting_evidence: List[str] risk_assessment: str recommendation: str timeframe: str

# CASE: 智能投研助手 （工作流实现）

def create_research_agent_workflow() $- >$ StateGraph: #创建状态图 workflow $\mathbf { \tau } = \mathbf { \tau }$ StateGraph(ResearchAgentState)

#添加节点 workflow.add_node("perception", perception) workflow.add_node("modeling",modeling) workflow.add_node("reasoning", reasoning) workflow.add_node("decision", decision) workflow.add_node("report", report_generation)

#设置入口点workflow.set_entry_point("perception")

#设置边和转换条件 workflow.add_edge("perception","modeling") workflow.add_edge("modeling", "reasoning") workflow.add_edge("reasoning","decision")

workflow.add_edge("decision","report") workflow.add_edge("report", END)

#编译工作流 return workflow.compile()

核心工作流通过LangGraph的\`StateGraph\`实现将各阶段连接成一个有向图

# CASE: 智能投研助手 （各阶段处理逻辑）

每个阶段都遵循类似的处理模式：

1.检查前置条件 (上一阶段数据)  
2.准备LLM提示  
3.调用LLM进行推理  
4.解析结果并更新状态  
5.错误处理与恢复机制

例如，推理阶段实现：

def reasoning(state: ResearchAgentState) $- >$ ResearchAgentState: try: #检查前置条件 if not state.get("world_model"): return { \*\*state, "error":"推理阶段缺少世界模型", "current_phase":"modeling" # 回到建模阶段 } #准备提示 prompt $\mathbf { \tau } = \mathbf { \tau }$   
ChatPromptTemplate.from_template(REASONING_PROMPT) #构建输入 input_data $= \{$ "research_topic": state["research_topic"], "industry_focus": state["industry_focus"], "time_horizon": state["time_horizon"],

# CASE: 智能投研助手 （各阶段处理逻辑）

"world_model": json.dumps(state["world_model"],   
ensure_ascii $\ c =$ False,indent $: = 2$ } #调用LLM chain $\mathbf { \tau } = \mathbf { \tau }$ prompt | IIm | JsonOutputParser() result $\mathbf { \tau } = \mathbf { \tau }$ chain.invoke(input_data) #更新状态 return { \*\*state, "reasoning_plans": result, "current_phase": "decision" } except Exception as e: return { \*\*state, "error": f"推理阶段出错:{str(e)}", "current_phase":"reasoning" #保持在当前阶段 }

# CASE: 智能投研助手 （使用方法）

if__name_ $= = "$ _main__"print( $\ " =$ 深思熟虑智能体-智能投研助手 $\vert = = = \ln ^ { 1 1 } )$ （2号#用户输入topic $\mathbf { \tau } = \mathbf { \tau }$ input("请输入研究主题 (例如:新能源汽车行业投资机会)：")industry $\mathbf { \tau } = \mathbf { \tau }$ input("请输入行业焦点(例如:电动汽车制造、电池技术):")horizon $\mathbf { \tau } = \mathbf { \tau }$ input("请输入时间范围 [短期/中期/长期]:")

print("\n智能投研助手开始工作..\n")

#运行智能体 result $\mathbf { \tau } = \mathbf { \tau }$ run_research_agent(topic, industry, horizon)

#处理结果  
if result.get("error"):print(f"\n发生错误: {result['error']}")  
else:print( $\because \vert n = = =$ 最终研究报告 $\Rightarrow ( n ^ { \prime \prime } )$ （24print(result.get("final report"."未生成.报告"))

请输入研究主题(例如：新能源汽车行业投资机会)：新能源汽车行业投资机会请输入行业焦点(例如：电动汽车制造、电池技术)：电动汽车制造 电池技术请输入时间范围[短期/中期/长期]:中期

# CASE: 智能投研助手 (生成报告)

#新能源汽车行业投资研究报告：中端电动汽车市场的中期增长机会

##\*\*报告摘要 \*\*

新能源汽车行业正处于快速发展的阶段，全球政策支持、技术进步以及消费者环保意识的增强共同推动了电动汽车(EV)和电池技术的需求增长。本报告聚焦于中端电动汽车市场及下一代电池技术的投资机会，结合市场数据、行业趋势和风险评估，提出以成本优化和规模化生产为核心的投资策略。我们建议优先投资具备较强成本管理和规模效应的企业，并关注充电基础设施建设带来的协同效应。

## $* * 1$ 市场和行业背景 \*\* ### $* * _ { 1 . 1 }$ 行业现状\*\*

新能源汽车行业目前处于快速增长阶段，市场需求强劲，技术创新活跃。根据最新市场数据：-\*\*全球电动汽车销量同比增长率\*\*：2022年达到 $42 \%$ ，显示出强劲的市场需求。-\*\*锂电池成本\*\*：降至\$107/kWh（2022年），持续下降的成本推动了电动汽车价格竞争力的提升。-\*\*政府补贴\*\*：平均每辆电动车补贴在\$5,000-\$8,000之间，加速了电动车的普及。

### $* * _ { 1 . 2 }$ 行业驱动因素\*\*

\*\*政策支持\*\*：各国政府通过购车补贴、税收优惠和排放法规等措施支持电动车发展。

‘\*技术进步\*\*：固态电池、快充技术和模块化平台的研发显著提升了电动汽车的性能和生产效率·\*\*消费者需求\*\*：环保意识增强和电动车性价比提升推动了市场需求的增长。

# CASE: 智能投研助手 (生成报告)

# ### $* * _ { 1 . 3 }$ 近期动态\*\*

-特斯拉宣布将在墨西哥建立新工厂，专注于生产下一代电动汽车平台。  
·宁德时代与宝马达成战略合作协议，共同开发新一代电池技术。  
-美国能源部预测，到2030年美国电动车充电基础设施投资需求将达到400亿美元。

## $\ast \ast _ { 2 }$ 核心投资观点\*\*

中端电动汽车市场将成为未来3-5年销量增长的核心驱动力。随着生产效率的提升和成本的下降，中端市场将受益于规模经济效应和技术进步。同时，下一代电池技术（如固态电池和快充技术）的突破将进一步推动行业的利润增长。

## $\ast \ast _ { 3 }$ .详细分析论证\*\*### $* * _ { 3 . 1 }$ 中端电动汽车市场的潜力\*\*

-\*\*市场规模\*\*：中端市场具有相对稳定的消费者基础和庞大的潜在需求。随着电动车价格的下降，更多消费者能够负担得起中端车型。  
-\*\*成本优化\*\*：模块化平台的应用显著提高了生产效率，降低了单位制造成本。  
-\*\*政策支持\*\*：政府补贴和税收优惠政策进一步增强了中端电动车的价格竞争力。

### $* * _ { 3 . 2 }$ 下一代电池技术的发展\*\*

-\*\*高能量密度\*\*：当前主流锂离子电池正在向更高能量密度方向发展，而固态电池被认为是下一代技术的关键。  
-\*\*快充技术\*\*：超级快充站的普及将显著改善用户体验，减少充电时间。  
-\*\*原材料回收\*\*：电池回收利用技术的进步有助于缓解锂、钴等关键材料的供应压力。

# CASE: 智能投研助手 (生成报告)

# ### $* * _ { 3 . 3 }$ 充电基础设施建设\*\*

-\*\*全球范围扩展\*\*：为满足快速增长的电动车保有量，全球范围内的充电网络建设正在加速。  
-\*\*新兴市场机会\*\*：新兴市场对充电桩的需求尚未完全释放，提供了巨大的投资机会。  
-\*\*技术升级\*\*：家庭充电桩和超级快充站的普及将进一步提升用户便利性。

## $* * 4$ .风险因素\*\*

尽管新能源汽车行业前景广阔，但仍需关注以下风险因素：

1.\*\*原材料价格波动\*\*：锂、钴等关键电池材料的价格波动可能对成本控制构成压力。  
2.\*\*技术迭代风险\*\*：固态电池等新技术的研发进度可能不及预期，影响现有技术的市场竞争力。  
3.\*\*地缘政治不确定性\*\*：供应链全球化可能导致受国际贸易摩擦或区域性政策变化的影响。  
4.\*\*市场竞争加剧\*\*：随着越来越多的企业进入市场，竞争可能加剧，导致利润率下降。

## $\ast \ast 5$ 投资建议\*\*

### $* * 5 . 1$ 投资目标\*\*  
优先投资于中端电动汽车市场的领先企业，特别是那些能够通过规模经济和技术优势实现成本优化的公司。### $* * 5 . 2$ 投资逻辑\*\*  
-\*\*市场内部模型支持\*\*：新能源汽车行业处于快速增长阶段，中端市场的扩展将受益于生产效率提升和成本下降。-\*\*政策和技术双重驱动\*\*：政策支持和技术进步有助于降低中端电动汽车的成本，增强产品竞争力。  
-\*\*稳定目庞大的市场需求\*\*：中端市场话合大规模资金投入，且备较高的回报潜力.

# CASE: 智能投研助手 (生成报告)

### $* * 5 . 3$ 监控指标\*\*

-\*\*原材料价格\*\*：密切关注锂、钴等关键材料的价格波动。  
-\*\*市场竞争动态\*\*：跟踪主要竞争对手的技术进展和市场份额变化。  
-\*\*政策变化\*\*：评估各国政府对电动车的支持力度是否发生变化。

## $* * 6$ 时间框架和预期回报\*\*### $* * _ { 6 . 1 }$ 时间框架\*\*

-\*\*中期（3-5年）\*\*：重点关注中端电动汽车市场的增长和下一代电池技术的商业化进程。  
### $* * 6 . 2$ 预期回报\*\*-\*\*市场规模扩张\*\*：预计全球中端电动汽车销量将以每年 $30 \% - 4 0 \%$ 的速度增长。  
-\*\*成本下降\*\*：锂电池成本有望进一步下降至\$80/kWh以下，推动电动车价格竞争力提升。  
-\*\*投资回报\*\*：基于市场增长和技术进步，预计投资年化回报率可达 $1 5 \% - 2 0 \%$ 。

## $\ast \ast 7$ 结论\*\*

新能源汽车行业正处于快速发展阶段，中端电动汽车市场和下一代电池技术是未来3-5年的核心投资机会。通过选择具备成本管理和规模效应的企业，并关注充电基础设施建设的协同效应，投资者可以在行业中长期发展中获得可观回报。同时，需密切监控原材料价格波动、技术迭代风险和市场竞争动态，以及时调整投资策略。

# 智能体分类 (混合 Hybrid)

混合智能体架构 (Hybrid Agent Architecture)

特点：结合反应式的"快速本能"和深思熟虑的"战略规划"，实现智能与效率的平衡。

三层设计：

·底层 （反应式）：即时处理紧急任务 (如避障)

·中层 （协调）：管理任务优先级 （可选)

·顶层 （深思熟虑）：进行长期目标规划 (如路径优化)

![](images/e69e798a674c47cf73fe2c13dca0ae0ea00632415afaaed34788c592ca2ea2ae.jpg)

运作机制：

通过仲裁系统 (如监督器) 动态切换模式：

紧急情况 $$ 启用反应式快速响应常规情况 $\mid $ 启动深思熟虑规划

# 智能体分类 (混合 Hybrid)

# 典型示例：

# 自动驾驶车辆：

·突发障碍 $\mid $ 立即刹车 (反应式) 正常行驶 $$ 规划最优路线 (深思熟虑)

# 核心优势：

兼具实时响应能力 (毫秒级) ·保留战略规划优势 （长期目标）

![](images/836b4ebf1028696b6a7063546d0391cf11f8a3142f3c0b777e315e6c59b27f3b.jpg)

# CASE：投顾AI助手

# TODO：投顾AI助手

基于混合智能体架构设计，结合了反应式架构的即时响应能力和深思熟虑架构的长期规划能力，通过协调层动态选择最合适的处理模式，为客户提供智能化、个性化的财富管理咨询服务。

混合智能体采用三层架构设计：

# 1.底层 （反应式层）

# 2.中层 (协调层)

# 3.顶层 (深思熟虑层)

·处理简单直接的查询，如市场状况账户信息等·毫秒级响应速度，提供快速反馈·基于预设规则和简单逻辑作出决策·处理复杂的投资分析和长期财务规划·多步骤、深度思考过程·构建内部模型并生成多个备选方案

：评估任务类型和优先级动态选择处理模式 (反应式或深思熟虑)  
·管理系统资源分配

# CASE: 投顾AI助手 （处理流程）

# Step1.查询评估阶段

协调层首先评估客户查询，确定：

：查询类型：紧急型、信息型或分析型·处理模式：反应式或深思熟虑

评估基于以下因素：

![](images/5d4841d39363eeb996ff6e431af415ac0cc1581b415b3e144b3dafb1f6a81c6d.jpg)

查询的复杂性和时效性所需数据和计算资源·客户期望的响应时间

# CASE: 投顾AI助手 （处理流程）

# Step2A.反应式处理流程

# 针对简单直接的查询：

·市场状况查询 (如"今天上证指数表现如何")·账户信息查询 (如"我的投资组合中科技股占比")·基础概念解释 (如"什么是ETF")

![](images/e392546e7e8d5bbb9852bee9e200e3785cdbb1d8cb1135d8b27dcbf8675ca07e.jpg)

# 处理特点:

·低延迟、高响应速度·直接调用数据和预设回答·简洁明了的输出格式

# CASE: 投顾AI助手 （处理流程）

# Step2B. 深思熟虑处理流程

# 针对复杂分析型查询：

·投资组合调整建议·长期财务规划·风险评估和应对策略

# 处理步骤:

![](images/73c9337de732abe2b8f13334f73c394d45fb1c026ee6b5391e2b483c24073a1e.jpg)

1.数据收集：整合市场数据、客户画像、历史数据等  
2.深度分析： 构建市场模型，分析多种可能情景  
3.生成建议： 形成多个方案并选择最优解

# CASE: 投顾AI助手 （状态管理）

智能体通过WealthAdvisorState维护完整状态：

class WealthAdvisorState(TypedDict): #输入 user_query:str #用户查询 customer_profile: Optional[Dict[str,Any]] # 客户画像 #处理状态 query_type: Optional[Literal["emergency", "informational","analytical"]]   
#查询类型 processing_mode: Optional[Literal["reactive","deliberative"]] # 处理模式 emergency_response: Optional[Dict[str,Any]] # 紧急响应结果 market_data: Optional[Dict[str,Any]] # 市场数据 analysis_results: Optional[Dict[str,Any]] #分析结果   
#输出 final_response: Optional[str] #最终响应 #控制流 current_phase: Literal["assess","reactive",   
"collect_data","analyze","recommend","respond"] error:Optional[str] #错误信息

# CASE: 投顾AI助手 （使用场景-反应式）

# 场景1: 市场信息查询 （反应式处理）

# 今天上证指数的表现如何？

用户查询：今天上证指数的表现如何？选择客户：平衡型投资者

正在处理...

[DEBUG]LLM评估输出:{querytype':'emergency',processngmode':'reactive',reasoning':"用户的查询是关于当天上证指的表，这一个需要实时市场数据的紧急查询。用户期望快速获取最新的市场信息，因此需要立即响应。这种类型的查询适合采用'reactive'处理模式，以便迅速提供准确的市场数据。"}

[DEBUG]分支判断: processing_mode=reactive,query_type $\ c =$ emergency   
[DEBUG]进入节点:reactive_processing   
【处理模式：反应式】-快速响应简单查询

===响应结果 $\scriptstyle = =$

我需要查询今天的上证指数表现。让我查询一下最新的数据根据最新数据，今天上证指数收于3200.12点，上涨了15.67点，涨幅为0.49%。请注意，这是截至今天的市场数据，股市有风险，投资需谨慎。如果您需要更详细的信息，可以关注证券市场的实时报道或者财经新闻。

处理用时：11.34秒

# CASE: 投顾AI助手 （使用场景-深思熟虑）

# 场景2： 投资组合优化 （深思熟虑处理

根据当前市场情况，我应该如何调整投资组合以应对可能的经济衰退？

用户查询：根据当前市场情况，我应该如何调整投资组合以应对可能的经济衰退？选择客户：平衡型投资者

正在处理...

[DEBUG]进入节点:assess_query  
[DEBUG] LLM评估输出:{'query_type':'analytical','processing_mode':'deliberative','reasoning':'用  
户的查询涉及根据当前市场情况调整投资组合以应对经济衰退，这需要深入分析市场趋势、经济指标以及用户的投资目标和风险承受能  
力。因此，这是一个需要深度思考和分析的查询，适合采用deliberative处理模式。"  
[DEBUG]分支判断: processing_mode=deliberative,query_type=analytical  
[DEBUG]进入节点:collect_data  
[DEBUG]进入节点:analyze_data  
[DEBUG]进入节点: generate_recommendations【处理模式：深思熟虑】-深度分析复杂查询

===响应结果 $\scriptstyle = = { \frac { } { } }$

# CASE: 投顾AI助手 （使用场景-深思熟虑）

尊敬的客户，

感谢您选择我们的财富管理服务。根据当前市场环境和您的个人情况，我们为您制定了以下详细的投资建议，帮助您更好地应对可能的经济衰退，同时实现中期财务目标（如退休规划和子女教育金）。以下是具体的内容：

### $* * 1$ 总体投资策略\*\*

在当前经济可能进入衰退的情况下，我们需要采取一种“防御性增长"的策略。这意味着在保护现有资本的同时，继续寻找具备长期潜力的投资机会。我们将通过优化资产配置、降低波动性和定期再平衡来实现这一目标。

由于您是“平衡型"风险承受能力的投资者，新的投资组合将更加注重收益与稳定性的平衡。调整后，您可以更安心地面对市场波动，同时为未来的财务目标打下坚实基础。

一

### $* * 2$ 具体行动步骤\*\*

以下是具体的调整建议，分为四个主要类别：股票、债券、现金和另类投资。

#### $^ { * * } ( 1 )$ 股票部分\*\*

- \*\*调整比例\*\*：从 $40 \%$ 降至 $30 \%$ 。  
-\*\*原因\*\*：股票市场的波动性较高，尤其是在经济衰退期间。减少股票配置可以降低整体风险。

# CASE: 投顾AI助手 （使用场景-深思熟虑）

-\*\*选择方向\*\*:

-优先考虑具有防御属性的行业，例如医疗保健、消费品和可再生能源领域。  
-继续关注ESG投资，但要确保标的具备良好的基本面和较低估值。  
-在科技行业中，选择与人工智能、云计算等高成长领域相关的优质公司，同时避免过度依赖高估值个股。

####\*\*(2)债券部分\*\*

-\*\*调整比例\*\*：从30%提高至 $40 \%$ 。

-\*\*原因\*\*：债券在经济衰退时通常表现更为稳定，能够有效分散风险。

-\*\*选择方向\*\*:

-优先配置高质量的政府债券或投资级公司债券。

-避免对利率敏感的长期债券，更多选择短期或中期债券以降低利率风险。

#### $^ { * * } ( 3 )$ 现金部分\*\*

- \*\*调整比例\*\*：从 $10 \%$ 提高至 $1 5 \%$ 。

-\*\*原因\*\*：增加现金储备可以为您提供更高的流动性和灵活性，以便在市场出现机会时快速行动。

-\*\*用途\*\*:

-作为应急资金，应对短期内可能出现的资金需求。

-在市场下跌时，用于抄底优质资产。

# CASE: 投顾AI助手 （使用场景-深思熟虑）

#### $^ { * * } ( 4 )$ 另类投资部分\*\*\*\*调整比例\*\*：从 $20 \%$ 降至 $1 5 \%$ 。

-\*\*原因\*\*：另类投资虽然具备一定的增长潜力，但在经济衰退期间流动性较低，风险较高。

-\*\*选择方向\*\*:

-关注与科技行业相关的低相关性资产，例如私募股权或基础设施基金。

-确保所选标的具备稳健的现金流和长期增值潜力。

### $\ast \ast _ { 3 }$ 资产配置建议\*\*

以下是调整后的资产配置比例（基于您的150万元投资组合）：

|\*\*资产类别\*\*「\*\*当前比例\*\*|\*\*调整后比例\*\*｜\*\*金额（元）\*\*||股票 |40% |30% |450,000 1|债券 |30% |40% |600,000 一|现金 |10% |15% |225,000 一|另类投资 一 $20 \%$ |15% | 225,000 一

基于深思熟虑模式给用户的回复collect_data $\Rightarrow$ analyze_data $\Rightarrow$ generate_recommendations

# Summary （构建Agent的核心思想）

# 构建Agent的三个核心思想总结

1.不要为所有任务构建Agent

适用场景：Agent适合处理复杂、模糊且高价值的任务，而非所有场景。

判断标准:

·任务复杂性：若决策树可明确规划，直接构建工作流更高效。

·任务价值：高成本（如大量Token消耗）需由高回报任务承担。

·关键能力验证：确保Agent能处理核心子任务（如代码生成、调试）。

·错误成本：高风险的错误需通过限制权限或人工介入来缓解。

案例：代码生成是理想场景，因其复杂性高、价值大且输出易验证（如通过单元测试），

# Summary （构建Agent的核心思想）

# 2.保持简洁

Agent的核心组件：

·环境：Agent的操作系统

工具集：提供行动接口和反馈机制。

·系统提示：定义目标、约束和预期行为。

# 设计原则：

·初期避免过度复杂化，优先迭代核心组件。

·优化 (如成本、延迟) 可在基础行为稳定后进行。

案例：不同功能的Agent可共享相同代码框架，仅调整工具和提示。

# Summary （构建Agent的核心思想）

# 3.像Agent一样思考

理解Agent的局限性：

·Agent仅基于有限上下文（10-20kToken）做决策。  
·需模拟Agent的视角（如仅通过静态截图操作电脑）以发现设计缺陷。  
改进方法：·直接询问模型（如Claude）以验证指令清晰度或工具使用合理性。  
·分析轨迹日志，优化上下文提供方式（如分辨率信息、操作建议）。优先评估：任务是否值得使用Agent。  
简单起步：聚焦环境、工具、提示三大组件。  
换位思考：通过模拟和日志分析优化Agent设计。  
核心目标：在提升Agent能力的同时，平衡成本、风险与用户体验

# Thank You Using data to solve problems