'''
程序说明：
## 1. 统一的问答系统模块
## 2. 从V401_fixed_qa_system.py中提取核心功能
## 3. 支持记忆管理和向量存储
## 4. 提供增强的问答功能
'''

import os
import time
from typing import Dict, Any, List, Optional
from langchain_community.vectorstores import FAISS
from langchain_community.llms import Tongyi
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain.schema import Document

# 导入相关模块
from .memory_manager import MemoryManager


class TongyiCostCalculator:
    """
    通义千问成本计算器
    """
    
    def __init__(self):
        """
        初始化成本计算器
        """
        # 通义千问的定价（示例，实际价格请参考官方文档）
        self.input_price_per_1k_tokens = 0.0005  # 输入价格
        self.output_price_per_1k_tokens = 0.001   # 输出价格
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        计算成本
        :param input_tokens: 输入令牌数
        :param output_tokens: 输出令牌数
        :return: 成本（元）
        """
        input_cost = (input_tokens / 1000) * self.input_price_per_1k_tokens
        output_cost = (output_tokens / 1000) * self.output_price_per_1k_tokens
        return input_cost + output_cost


class QASystem:
    """
    统一的问答系统类
    """
    
    def __init__(self, vector_store: Optional[FAISS], api_key: str, memory_manager: MemoryManager = None):
        """
        初始化QA系统
        :param vector_store: 向量存储
        :param api_key: API密钥
        :param memory_manager: 记忆管理器
        """
        self.vector_store = vector_store
        self.api_key = api_key
        self.memory_manager = memory_manager
        self.cost_calculator = TongyiCostCalculator()
        self.memory_cleared_flag = False  # 新增：记忆清除标志
        """
        初始化问答系统
        :param vector_store: FAISS向量存储对象（可能为None）
        :param api_key: DashScope API密钥
        :param memory_manager: 记忆管理器对象
        """
        # 检查向量存储是否有效
        if vector_store is None:
            print("警告: 向量存储为None，问答系统可能无法正常工作")
        else:
            print(f"向量存储加载成功，包含 {len(vector_store.docstore._dict)} 个文档")
            
        self.vector_store = vector_store
        self.api_key = api_key
        self.memory_manager = memory_manager or MemoryManager()
        
        # 初始化语言模型
        self.llm = Tongyi(
            model_name="qwen-turbo", 
            dashscope_api_key=api_key
        )
        
        # 加载问答链，使用自定义提示词
        self.qa_chain = load_qa_chain(
            self.llm, 
            chain_type="stuff",
            prompt=self._create_enhanced_prompt()
        )
        
        # 初始化成本计算器
        self.cost_calculator = TongyiCostCalculator()
    
    def _create_enhanced_prompt(self):
        """
        创建增强的提示词模板，支持记忆上下文
        :return: 自定义提示词模板
        """
        # 根据记忆清除标志调整提示词
        if self.memory_cleared_flag:
            # 记忆清除后的提示词 - 明确告诉LLM忘记历史对话
            enhanced_prompt_template = f"""你是一个专业的AI助手，专门基于提供的文档内容回答用户问题。

            ## 重要提醒
            **用户刚刚清除了所有历史对话记忆，请忘记之前的所有对话内容，只基于当前提供的文档内容回答问题。**

            ## 回答要求
            1. **准确性**：严格基于提供的文档内容回答，不要添加文档中没有的信息
            2. **完整性**：尽可能全面回答用户问题，涵盖相关要点
            3. **逻辑性**：回答要有清晰的逻辑结构，层次分明
            4. **客观性**：保持客观中立的语气，避免主观判断
            5. **专注当前**：只关注当前问题，不要提及任何历史对话

            ## 回答格式
            请使用Markdown格式组织回答

            ## 特殊情况处理
            - 如果文档中没有相关信息，请明确说明"根据提供的文档内容，没有找到相关信息"
            - 如果问题涉及多个方面，请分点详细说明
            - 如果涉及技术概念，请先解释概念再回答问题
            - **重要**：不要引用任何历史对话，只基于当前文档内容回答

            请确保回答内容准确、有用且易于理解。

            基于以下文档内容回答问题：

            {{context}}

            问题：{{question}}

            回答："""
        else:
            # 正常情况下的提示词
            enhanced_prompt_template = f"""你是一个专业的AI助手，专门基于提供的文档内容和对话历史回答用户问题。请遵循以下指导原则：

            ## 回答要求
            1. **准确性**：严格基于提供的文档内容回答，不要添加文档中没有的信息
            2. **完整性**：尽可能全面回答用户问题，涵盖相关要点
            3. **逻辑性**：回答要有清晰的逻辑结构，层次分明
            4. **客观性**：保持客观中立的语气，避免主观判断
            5. **上下文理解**：充分利用对话历史中的相关信息，提供连贯的回答

            ## 回答格式
            请使用Markdown格式组织回答

            ## 特殊情况处理
            - 如果文档中没有相关信息，请明确说明"根据提供的文档内容，没有找到相关信息"
            - 如果问题涉及多个方面，请分点详细说明
            - 如果涉及技术概念，请先解释概念再回答问题
            - 如果有相关历史对话，请适当引用和对比

            请确保回答内容准确、有用且易于理解。

            基于以下文档内容和对话历史回答问题：

            {{context}}

            问题：{{question}}

            回答："""
        
        return PromptTemplate(
            template=enhanced_prompt_template,
            input_variables=["context", "question"]
        )
    
    def answer_question(self, question: str, k: int = 3) -> Dict[str, Any]:
        """
        回答单个问题
        :param question: 用户问题
        :param k: 检索的文档数量
        :return: 回答结果
        """
        if not self.vector_store:
            return {
                'answer': '抱歉，向量存储未加载，无法回答问题。',
                'sources': [],
                'cost': 0.0,
                'error': '向量存储未加载'
            }
        
        try:
            # 检查是否是图片相关的问题
            image_keywords = ['图片', '图像', '照片', '图表', '图', 'image', 'picture', 'photo', 'chart']
            is_image_question = any(keyword in question.lower() for keyword in image_keywords)
            
            if is_image_question:
                # 专门搜索图片类型的文档
                docs = self._search_images(k)
            else:
                # 检索相关文档
                docs = self.vector_store.similarity_search(question, k=k)
            
            if not docs:
                return {
                    'answer': '根据提供的文档内容，没有找到相关信息。',
                    'sources': [],
                    'cost': 0.0
                }
            
            # 构建上下文
            context = "\n\n".join([doc.page_content for doc in docs])
            
            # 生成回答 - 使用老版本的正确方法
            chain_result = self.qa_chain.invoke({
                "input_documents": docs,
                "question": question,
                "context": context
            })
            
            # 提取答案
            result = chain_result.get('output_text', chain_result.get('result', ''))
            
            # 提取源信息
            sources = []
            for doc in docs:
                source_info = {
                    'content': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    'metadata': doc.metadata
                }
                sources.append(source_info)
            
            # 处理图片ID：在AI回答中包含图片ID但不显示给用户
            if any(doc.metadata.get('chunk_type') == 'image' for doc in docs):
                # 为每个图片添加ID标记
                image_sources = [doc for doc in docs if doc.metadata.get('chunk_type') == 'image']
                for image_doc in image_sources:
                    image_id = image_doc.metadata.get('image_id') or image_doc.metadata.get('image_path', '').split('/')[-1].split('.')[0]
                    # 在AI回答中插入图片ID标记（用户看不到）
                    result = result.replace(
                        image_doc.metadata.get('img_caption', [''])[0] if image_doc.metadata.get('img_caption') else '',
                        f"{image_doc.metadata.get('img_caption', [''])[0] if image_doc.metadata.get('img_caption') else ''} [IMAGE_ID:{image_id}]"
                    )
            
            # 计算成本（估算）
            input_tokens = len(context + question) // 4  # 粗略估算
            output_tokens = len(result) // 4
            cost = self.cost_calculator.calculate_cost(input_tokens, output_tokens)
            
            return {
                'answer': result,
                'sources': sources,
                'cost': cost,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens
            }
            
        except Exception as e:
            return {
                'answer': f'回答问题时发生错误: {str(e)}',
                'sources': [],
                'cost': 0.0,
                'error': str(e)
            }
    
    def _search_images(self, k: int = 3) -> List[Document]:
        """
        专门搜索图片类型的文档
        :param k: 检索的文档数量
        :return: 图片文档列表
        """
        try:
            image_docs = []
            
            # 遍历所有文档，筛选图片类型
            for doc_id, doc in self.vector_store.docstore._dict.items():
                if doc.metadata.get('chunk_type') == 'image':
                    image_docs.append(doc)
                    if len(image_docs) >= k:
                        break
            
            return image_docs
            
        except Exception as e:
            print(f"搜索图片文档失败: {e}")
            return []
    
    def answer_with_memory(self, user_id: str, question: str, k: int = 3) -> Dict[str, Any]:
        """
        带记忆的问答功能
        :param user_id: 用户ID
        :param question: 用户问题
        :param k: 检索的文档数量
        :return: 回答结果
        """
        try:
            # 构建记忆上下文
            memory_context = self.memory_manager.build_context(user_id, question, memory_limit=5)
            
            # 获取相关记忆
            relevant_memories = self.memory_manager.retrieve_relevant_memory(user_id, question)
            
            # 生成回答
            result = self.answer_question(question, k)
            
            # 只有在有相关记忆且记忆未被清除时才添加历史对话信息
            # 同时检查记忆是否真的相关（避免完全相同的问题被重复处理）
            if (not self.memory_cleared_flag and
                memory_context.get('memory_context') and 
                memory_context.get('memory_count', 0) > 0 and
                not self._is_exact_duplicate_question(question, memory_context.get('memories', []))):
                enhanced_answer = f"{result['answer']}\n\n## 相关历史对话\n{memory_context['memory_context']}"
                result['answer'] = enhanced_answer
            elif self.memory_cleared_flag:
                # 记忆清除后，确保回答中不包含任何历史对话引用
                # 重新生成回答，使用清除记忆后的提示词
                result = self.answer_question(question, k)
            
            # 只有在记忆未被清除时才保存到记忆
            if not self.memory_cleared_flag:
                self.memory_manager.add_to_session(
                    user_id=user_id,
                    question=question,
                    answer=result['answer'],
                    context={
                        'sources': result.get('sources', []),
                        'cost': result.get('cost', 0.0),
                        'relevant_memories': len(relevant_memories)
                    }
                )
            
            return result
            
        except Exception as e:
            return {
                'answer': f'带记忆的问答过程中发生错误: {str(e)}',
                'sources': [],
                'cost': 0.0,
                'error': str(e)
            }
    
    def _is_exact_duplicate_question(self, current_question: str, memories: List) -> bool:
        """
        检查当前问题是否与历史记忆中的问题完全相同
        :param current_question: 当前问题
        :param memories: 记忆列表
        :return: 是否为完全重复的问题
        """
        if not memories:
            return False
        
        current_question_clean = current_question.strip().lower()
        for memory in memories:
            if hasattr(memory, 'question'):
                memory_question_clean = memory.question.strip().lower()
                if current_question_clean == memory_question_clean:
                    return True
        return False
    
    def calculate_similarity(self, question: str, content: str) -> float:
        """
        计算问题与内容的相关性
        :param question: 问题
        :param content: 内容
        :return: 相似度分数
        """
        try:
            # 简单的Jaccard相似度计算
            def jaccard_similarity(set1, set2):
                intersection = len(set1.intersection(set2))
                union = len(set1.union(set2))
                return intersection / union if union > 0 else 0
            
            # 分词（简单实现）
            question_words = set(question.lower().split())
            content_words = set(content.lower().split())
            
            return jaccard_similarity(question_words, content_words)
            
        except Exception as e:
            print(f"计算相似度时发生错误: {e}")
            return 0.0
    
    def format_timestamp(self, timestamp: float) -> str:
        """
        格式化时间戳
        :param timestamp: 时间戳
        :return: 格式化的时间字符串
        """
        import datetime
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    def append_sources_to_answer(self, answer: str, sources: List[Dict[str, Any]]) -> str:
        """
        将源信息添加到回答中
        :param answer: 原始回答
        :param sources: 源信息列表
        :return: 增强的回答
        """
        if not sources:
            return answer
        
        enhanced_answer = answer + "\n\n## 参考来源\n"
        
        for i, source in enumerate(sources, 1):
            metadata = source.get('metadata', {})
            doc_name = metadata.get('document_name', '未知文档')
            page_number = metadata.get('page_number', '未知页码')
            
            enhanced_answer += f"{i}. **{doc_name}** (第{page_number}页)\n"
            enhanced_answer += f"   {source.get('content', '')[:100]}...\n\n"
        
        return enhanced_answer
    
    def get_memory_stats(self, user_id: str = None) -> Dict[str, Any]:
        """
        获取记忆统计信息
        :param user_id: 用户ID
        :return: 统计信息
        """
        return self.memory_manager.get_memory_stats(user_id)
    
    def set_memory_cleared_flag(self, cleared: bool = True):
        """
        设置记忆清除标志
        :param cleared: 是否已清除记忆
        """
        self.memory_cleared_flag = cleared
        if cleared:
            # 清除记忆时，给LLM明确的"忘记"指令
            self._reset_conversation_context()
    
    def _reset_conversation_context(self):
        """
        重置对话上下文，让LLM忘记之前的对话
        """
        # 重新创建增强提示词，确保LLM不会引用历史对话
        self.enhanced_prompt = self._create_enhanced_prompt()
        
        # 重新初始化问答链，彻底重置LLM上下文
        try:
            from langchain.chains.question_answering import load_qa_chain
            self.qa_chain = load_qa_chain(
                self.llm, 
                chain_type="stuff",
                prompt=self.enhanced_prompt
            )
        except ImportError:
            # 如果导入失败，尝试其他路径
            try:
                from langchain.chains import load_qa_chain
                self.qa_chain = load_qa_chain(
                    self.llm, 
                    chain_type="stuff",
                    prompt=self.enhanced_prompt
                )
            except ImportError:
                # 如果还是失败，使用简单的链
                from langchain.chains import LLMChain
                self.qa_chain = LLMChain(llm=self.llm, prompt=self.enhanced_prompt)
    
    def clear_memory(self, user_id: str = None, memory_type: str = "all"):
        """
        清除记忆
        :param user_id: 用户ID
        :param memory_type: 记忆类型
        """
        if memory_type == "all":
            self.memory_manager.clear_session_memory(user_id)
            self.memory_manager.clear_user_memory(user_id)
        elif memory_type == "session":
            self.memory_manager.clear_session_memory(user_id)
        elif memory_type == "user":
            self.memory_manager.clear_user_memory(user_id)


def load_qa_system(vector_db_path: str, api_key: str = "", memory_manager: MemoryManager = None) -> QASystem:
    """
    加载问答系统
    :param vector_db_path: 向量数据库路径
    :param api_key: API密钥
    :param memory_manager: 记忆管理器实例（可选）
    :return: 问答系统实例
    """
    from langchain_community.embeddings import DashScopeEmbeddings
    from langchain_community.vectorstores import FAISS
    
    # 获取API密钥 - 按照优先级：参数 > 环境变量 > 默认值
    if not api_key:
        api_key = os.getenv('MY_DASHSCOPE_API_KEY', '')
    
    if not api_key or api_key == '你的APIKEY':
        print("错误: 未配置DashScope API密钥")
        return None
    
    try:
        # 加载向量存储
        embeddings = DashScopeEmbeddings(dashscope_api_key=api_key, model="text-embedding-v1")
        vector_store = FAISS.load_local(vector_db_path, embeddings, allow_dangerous_deserialization=True)
        
        # 如果没有提供记忆管理器，则创建一个新的
        if memory_manager is None:
            memory_manager = MemoryManager()
        
        # 创建问答系统
        qa_system = QASystem(vector_store, api_key, memory_manager)
        
        return qa_system
        
    except Exception as e:
        print(f"加载问答系统失败: {e}")
        return None 