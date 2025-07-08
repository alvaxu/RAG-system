"""
问答处理模块
"""
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_community.llms import Tongyi
from langchain.prompts import ChatPromptTemplate
from typing import List, Dict, Tuple
from config import LLM_MODEL, DASHSCOPE_API_KEY

class QAChat:
    """
    功能：处理用户问题，生成回答
    """
    def __init__(self, vector_store, model_name: str = LLM_MODEL):
        self.llm = Tongyi(
            model_name=model_name,
            temperature=0.7,
            dashscope_api_key=DASHSCOPE_API_KEY
        )
        self.vector_store = vector_store
        
        # 创建提示模板
        prompt = ChatPromptTemplate.from_template("""
        基于以下上下文回答问题。如果无法从上下文中得到答案，请说明。

        上下文：
        {context}

        问题：{input}

        回答：""")
        
        # 创建文档链
        self.document_chain = create_stuff_documents_chain(
            llm=self.llm,
            prompt=prompt
        )
        
        # 创建检索链
        self.retrieval_chain = create_retrieval_chain(
            self.vector_store.vector_store.as_retriever(),
            self.document_chain
        )

    def generate_answer(self, question: str) -> Tuple[str, List[Dict]]:
        """
        生成回答
        """
        # 使用检索链生成回答
        result = self.retrieval_chain.invoke({"input": question})


        print(f"result={result}")
        """result={
'input': '工作不负责任会得到什么处罚', 
'context': [
	Document(
				id='ecb88c8b-1d37-4eba-9c48-b686bf1a394a', 
				metadata={'page': 5, 'source': '浦发上海浦东发展银行西安分行个金客户经理考核办法.pdf'},
				page_content='百度文库  - 好好学习，天天向上  \n-5 第五章  工作质量考核标准  \n第九条   工作质量考核实行扣分制。工作质量指个金客户经理在\n从事所有个人业务时出现投诉、差错及风险。该项考核最多扣 50分，\n如发生重大差错事故，按分行有关制度处									理。  \n（一）服务质量考核：   \n1、工作责任心不强，缺乏配合协作精神；扣 5分 \n2、客户服务效率低，态度生硬或不及时为客户提供维护服务，\n有客户投诉的 ,每投诉一次扣 2分 \n3、不服从支行工作安排，不认真参加分（支）行宣传活动									的，\n每次扣 2分； \n4、未能及时参加分行（支行）组织的各种业务培训、考试和专\n题活动的每次扣 2分； \n5、未按规定要求进行贷前调查、贷后检查工作的，每笔扣 5分； \n6、未建立信贷台帐资料及档案的每笔扣 5分； \n7、在工作中有不								廉洁自律情况的每发现一次扣 50分。 \n（二）个人资产质量考核：  \n当季考核收息率 97%以上为合格，每降 1个百分点扣 2分；不\n良资产零为合格，每超一个个百分点扣 1分。 \nA.发生跨月逾期，单笔不超过 10万元，当季收回者，扣 1分。 									\nB.发生跨月逾期， 2笔以上累计金额不超过 20万元，当季收回\n者，扣 2分；累计超过 20万元以上的，扣 4分。'), Document(
				id='38252ee4-0e2d-4c50-9f2f-84167620e276', 
				metadata={'page': 8, 'source': '浦发上海浦东发展银行西安分行个金客户经理考核办法.pdf'}, 
				page_content='百度文库  - 好好学习，天天向上  \n-8 第十五条   各项考核分值总计达到某一档行员级别考核分值标\n准，个金客户经理即可在下一季度享受该级行员的薪资标准。下一季\n度考核时，按照已享受行员级别考核折算比值进行考核，以次类推。  \n第十六条   对已聘为各级客户经理的人员，当工作业绩考核达不\n到相应技术职务要求下限时，下一年技术职务相应下调 。 \n第十七条   为保护个人业务客户经理创业的积极性，暂定其收入\n构成中基础薪点不低于 40%。 \n第八章  管理与奖惩  \n第十八条   个金客户经理管理机构为分行客户经理管理委员会。\n管理委员会组成人员：行长或主管业务副行长，个人业务部、人力资\n源部、风险管理部负责人。  \n第十九条   客户经理申报的各种信息必须真实。分行个人业务部\n需对其工作业绩数据进行核实，并对其真实性负责；分行人事部门需\n对其学历、工作阅历等基本信息进行核实，并对其真实性负责。  \n第二十条   对因工作不负责任使资产质量产生严重风险或造成损\n失的给予降级直至开 除处分，构成渎职罪的提请司法部门追究刑事责\n任。'),


	Document(	
				id='3ee4608e-f153-4227-8410-6d0117d1f5e7', 
				metadata={'page': 9, 'source': '浦发上海浦东发展银行西安分行个金客户经理考核办法.pdf'}, 
				page_content='百度文库  - 好好学习，天天向上  \n-9 第九章  附    则 \n第二十一条   本办法自发布之日起执行。  \n第二十二条   本办法由上海浦东发展银行西安分行行负责解释和\n修改。'), 
	Document(
				id='300472b0-adb6-496f-b0a7-6932ec0d193d', 
				metadata={'page': 6, 'source': '浦发上海浦东发展银行西安分行个金客户经理考核办法.pdf'}, 
				page_content='百度文库  - 好好学习，天天向上  \n-6 C.发生逾期超过 3个月，无论金额大小和笔数，扣 10分。 \n第六章  聘任考核程序  \n第十条   凡达到本办法第三章规定的该技术职务所要求的行内职\n工，都可向分行人力资源部申报个金客户经理评聘。  \n第									十一条   每年一月份为客户经理评聘的申报时间，由分行人力\n资源部、个人业务部每年二月份组织统一的资格考试。考试合格者由\n分行颁发个金客户经理资格证书，其有效期为一年。  \n第十二条   客户经理聘任实行开放式、浮动制，即：本人									申报  —\n— 所在部门推荐  —— 分行考核  —— 行长聘任  —— 每年考评\n调整浮动。   \n第十三条   特别聘任：  \n（一）经分行同意录用从其他单位调入的个金客户经理，由用人\n单位按 D类人员进行考核， 薪资待遇按其业绩享受行内正式行									员工同\n等待遇。待正式转正后按第十一条规定申报技术职务。  \n（二）对为我行业务创新、工作业绩等方面做出重大贡献的市场\n人员经支行推荐、分行行长 批准可越级聘任。  \n第十四条   对于创利业绩较高，而暂未入围技术职务系列，或所									\n评聘技术职务较低的市场人员，各级领导要加大培养力度，使其尽快')], 
'answer': '根据上下文，因工作不负责任使资产质量产生严重风险或造成损失的，会给予**降级直至开除处分**。如果行为构成渎职罪，还将提请司法部门追究刑事责任。'}

        
"""

        
        # 获取回答和来源
        answer = result["answer"]
        sources = [doc.metadata for doc in result["context"]]
        
        return answer, sources 