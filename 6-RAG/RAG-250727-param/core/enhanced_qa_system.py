'''
程序说明：
## 1. 增强版QA系统实现
## 2. 集成重排序引擎、源过滤引擎、智能过滤引擎
## 3. 支持多阶段优化流程
## 4. 提供详细的优化统计信息
'''

import os
import time
import logging
from typing import Dict, Any, List, Optional
from langchain_community.vectorstores import FAISS
from langchain_community.llms import Tongyi
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain.schema import Document

# 导入相关模块
from .memory_manager import MemoryManager
from .reranking_engine import RerankingEngine
from .source_filter_engine import SourceFilterEngine
from .smart_filter_engine import SmartFilterEngine

logger = logging.getLogger(__name__)


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


class EnhancedQASystem:
    """
    增强版问答系统类
    """
    
    def __init__(self, vector_store: Optional[FAISS], api_key: str, 
                 memory_manager: MemoryManager = None, config: Dict[str, Any] = None):
        """
        初始化增强版QA系统
        :param vector_store: 向量存储
        :param api_key: API密钥
        :param memory_manager: 记忆管理器
        :param config: 配置字典
        """
        # 基础组件初始化
        self.vector_store = vector_store
        self.api_key = api_key
        self.memory_manager = memory_manager or MemoryManager()
        self.cost_calculator = TongyiCostCalculator()
        self.memory_cleared_flag = False
        
        # 配置初始化
        self.config = config or {}
        
        # 检查向量存储是否有效
        if vector_store is None:
            logger.warning("向量存储为None，问答系统可能无法正常工作")
        else:
            logger.info(f"向量存储加载成功，包含 {len(vector_store.docstore._dict)} 个文档")
        
        # 初始化语言模型
        model_name = self.config.get('model_name', 'qwen-turbo')
        temperature = self.config.get('temperature', 0.5)
        max_tokens = self.config.get('max_tokens', 1500)
        
        self.llm = Tongyi(
            model_name=model_name,
            dashscope_api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # 加载问答链
        self.qa_chain = load_qa_chain(
            self.llm, 
            chain_type="stuff",
            prompt=self._create_enhanced_prompt()
        )
        
        # 初始化优化引擎
        self._initialize_optimization_engines()
        
        logger.info("增强版QA系统初始化完成")
    
    def _initialize_optimization_engines(self):
        """
        初始化优化引擎
        """
        try:
            # 初始化重排序引擎
            vector_config = self.config.get('vector_store', {})
            self.reranking_engine = RerankingEngine(vector_config)
            logger.info("重排序引擎初始化完成")
            
            # 初始化源过滤引擎
            qa_config = self.config.get('qa_system', {})
            self.source_filter_engine = SourceFilterEngine(qa_config)
            logger.info("源过滤引擎初始化完成")
            
            # 初始化智能过滤引擎
            processing_config = self.config.get('processing', {})
            self.smart_filter_engine = SmartFilterEngine(processing_config)
            logger.info("智能过滤引擎初始化完成")
            
        except Exception as e:
            logger.error(f"优化引擎初始化失败: {e}")
            # 如果引擎初始化失败，使用默认配置
            self.reranking_engine = None
            self.source_filter_engine = None
            self.smart_filter_engine = None
    
    def _create_enhanced_prompt(self):
        """
        创建增强的提示词模板
        :return: 自定义提示词模板
        """
        enhanced_prompt_template = f"""你是一个专业的AI助手，专门基于提供的文档内容回答用户问题。

        ## 回答要求
        1. **准确性**：严格基于提供的文档内容回答，不要添加文档中没有的信息
        2. **完整性**：尽可能全面回答用户问题，涵盖相关要点
        3. **逻辑性**：回答要有清晰的逻辑结构，层次分明
        4. **客观性**：保持客观中立的语气，避免主观判断

        ## 回答格式
        请使用Markdown格式组织回答

        ## 特殊情况处理
        - 如果文档中没有相关信息，请明确说明"根据提供的文档内容，没有找到相关信息"
        - 如果问题涉及多个方面，请分点详细说明
        - 如果涉及技术概念，请先解释概念再回答问题

        请确保回答内容准确、有用且易于理解。

        基于以下文档内容回答问题：

        {{context}}

        问题：{{question}}

        回答："""
        
        return PromptTemplate(
            template=enhanced_prompt_template,
            input_variables=["context", "question"]
        )
    
    def answer_question(self, question: str, k: int = None) -> Dict[str, Any]:
        """
        回答问题（增强版）
        :param question: 问题
        :param k: 检索文档数量
        :return: 回答结果
        """
        start_time = time.time()
        
        try:
            # 获取配置参数
            k = k or self.config.get('similarity_top_k', 3)
            
            logger.info(f"开始处理问题: {question}")
            
            # 1. 初始检索
            initial_docs = self._initial_retrieval(question, k)
            logger.info(f"初始检索完成，获得 {len(initial_docs)} 个文档")
            
            # 2. 重排序优化
            reranked_docs = self._apply_reranking(question, initial_docs)
            logger.info(f"重排序完成，保留 {len(reranked_docs)} 个文档")
            
            # 3. 智能过滤
            filtered_docs = self._apply_smart_filtering(question, reranked_docs)
            logger.info(f"智能过滤完成，保留 {len(filtered_docs)} 个文档")
            
            # 4. 生成回答
            answer_result = self._generate_answer(question, filtered_docs)
            
            # 5. 源过滤优化
            final_sources = self._apply_source_filtering(answer_result['answer'], filtered_docs)
            logger.info(f"源过滤完成，保留 {len(final_sources)} 个源")
            
            # 计算处理时间
            processing_time = time.time() - start_time
            
            # 构建结果
            result = {
                'answer': answer_result['answer'],
                'sources': final_sources,
                'cost': answer_result.get('cost', 0.0),
                'processing_time': processing_time,
                'optimization_stats': self._get_optimization_stats(initial_docs, reranked_docs, filtered_docs, final_sources)
            }
            
            logger.info(f"问题处理完成，耗时: {processing_time:.2f}秒")
            return result
            
        except Exception as e:
            logger.error(f"回答问题失败: {e}")
            return {
                'answer': f"抱歉，处理您的问题时出现错误: {str(e)}",
                'sources': [],
                'cost': 0.0,
                'processing_time': time.time() - start_time,
                'error': str(e)
            }
    
    def _initial_retrieval(self, question: str, k: int) -> List[Document]:
        """
        初始检索
        :param question: 问题
        :param k: 检索数量
        :return: 检索到的文档
        """
        if not self.vector_store:
            return []
        
        try:
            # 执行相似度搜索
            docs = self.vector_store.similarity_search(question, k=k)
            return docs
        except Exception as e:
            logger.error(f"初始检索失败: {e}")
            return []
    
    def _apply_reranking(self, question: str, documents: List[Document]) -> List[Document]:
        """
        应用重排序
        :param question: 问题
        :param documents: 文档列表
        :return: 重排序后的文档
        """
        if not self.reranking_engine or not documents:
            return documents
        
        try:
            # 转换为字典格式
            doc_dicts = []
            for doc in documents:
                doc_dict = {
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'score': getattr(doc, 'score', 0.0)
                }
                doc_dicts.append(doc_dict)
            
            # 执行重排序
            reranked_dicts = self.reranking_engine.rerank_results(question, doc_dicts)
            
            # 转换回Document格式
            reranked_docs = []
            for doc_dict in reranked_dicts:
                doc = Document(
                    page_content=doc_dict['content'],
                    metadata=doc_dict['metadata']
                )
                # 保存重排序分数
                doc.rerank_score = doc_dict.get('rerank_score', 0.0)
                reranked_docs.append(doc)
            
            return reranked_docs
            
        except Exception as e:
            logger.error(f"重排序失败: {e}")
            return documents
    
    def _apply_smart_filtering(self, question: str, documents: List[Document]) -> List[Document]:
        """
        应用智能过滤
        :param question: 问题
        :param documents: 文档列表
        :return: 过滤后的文档
        """
        if not self.smart_filter_engine or not documents:
            return documents
        
        try:
            # 转换为字典格式
            doc_dicts = []
            for doc in documents:
                doc_dict = {
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'score': getattr(doc, 'score', 0.0)
                }
                doc_dicts.append(doc_dict)
            
            # 执行智能过滤
            filtered_dicts = self.smart_filter_engine.smart_filter(question, doc_dicts)
            
            # 转换回Document格式
            filtered_docs = []
            for doc_dict in filtered_dicts:
                doc = Document(
                    page_content=doc_dict['content'],
                    metadata=doc_dict['metadata']
                )
                # 保存智能过滤分数
                doc.smart_filter_scores = doc_dict.get('smart_filter_scores', {})
                filtered_docs.append(doc)
            
            return filtered_docs
            
        except Exception as e:
            logger.error(f"智能过滤失败: {e}")
            return documents
    
    def _generate_answer(self, question: str, documents: List[Document]) -> Dict[str, Any]:
        """
        生成回答
        :param question: 问题
        :param documents: 文档列表
        :return: 回答结果
        """
        try:
            if not documents:
                return {
                    'answer': "根据提供的文档内容，没有找到相关信息。",
                    'cost': 0.0
                }
            
            # 准备上下文
            context = "\n\n".join([doc.page_content for doc in documents])
            
            # 生成回答
            response = self.qa_chain.run({
                "context": context,
                "question": question
            })
            
            # 计算成本（简化计算）
            input_tokens = len(context + question) // 4  # 粗略估算
            output_tokens = len(response) // 4
            cost = self.cost_calculator.calculate_cost(input_tokens, output_tokens)
            
            return {
                'answer': response,
                'cost': cost
            }
            
        except Exception as e:
            logger.error(f"生成回答失败: {e}")
            return {
                'answer': f"抱歉，生成回答时出现错误: {str(e)}",
                'cost': 0.0
            }
    
    def _apply_source_filtering(self, llm_answer: str, documents: List[Document]) -> List[Dict[str, Any]]:
        """
        应用源过滤
        :param llm_answer: LLM回答
        :param documents: 文档列表
        :return: 过滤后的源列表
        """
        if not self.source_filter_engine or not documents:
            # 转换为源格式
            sources = []
            for doc in documents:
                source = {
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'score': getattr(doc, 'score', 0.0)
                }
                sources.append(source)
            return sources
        
        try:
            # 转换为源格式
            sources = []
            for doc in documents:
                source = {
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'score': getattr(doc, 'score', 0.0)
                }
                sources.append(source)
            
            # 执行源过滤
            filtered_sources = self.source_filter_engine.filter_sources(llm_answer, sources)
            
            return filtered_sources
            
        except Exception as e:
            logger.error(f"源过滤失败: {e}")
            return sources
    
    def _get_optimization_stats(self, initial_docs: List[Document], 
                               reranked_docs: List[Document], 
                               filtered_docs: List[Document], 
                               final_sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取优化统计信息
        :param initial_docs: 初始文档
        :param reranked_docs: 重排序文档
        :param filtered_docs: 过滤文档
        :param final_sources: 最终源
        :return: 统计信息
        """
        stats = {
            'initial_count': len(initial_docs),
            'reranked_count': len(reranked_docs),
            'filtered_count': len(filtered_docs),
            'final_count': len(final_sources),
            'reranking_reduction': len(initial_docs) - len(reranked_docs),
            'filtering_reduction': len(reranked_docs) - len(filtered_docs),
            'source_filtering_reduction': len(filtered_docs) - len(final_sources),
            'total_reduction': len(initial_docs) - len(final_sources),
            'reranking_engine_stats': self.reranking_engine.get_reranking_stats() if self.reranking_engine else None,
            'smart_filter_engine_stats': self.smart_filter_engine.get_filtering_stats() if self.smart_filter_engine else None,
            'source_filter_engine_stats': self.source_filter_engine.get_filtering_stats() if self.source_filter_engine else None
        }
        
        return stats
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """
        获取优化引擎统计信息
        :return: 统计信息
        """
        stats = {
            'reranking_engine': self.reranking_engine.get_reranking_stats() if self.reranking_engine else None,
            'smart_filter_engine': self.smart_filter_engine.get_filtering_stats() if self.smart_filter_engine else None,
            'source_filter_engine': self.source_filter_engine.get_filtering_stats() if self.source_filter_engine else None
        }
        return stats


def load_enhanced_qa_system(vector_db_path: str, api_key: str = "", 
                           memory_manager: MemoryManager = None, 
                           config: Dict[str, Any] = None) -> EnhancedQASystem:
    """
    加载增强版QA系统
    :param vector_db_path: 向量数据库路径
    :param api_key: API密钥
    :param memory_manager: 记忆管理器
    :param config: 配置字典
    :return: 增强版QA系统实例
    """
    try:
        # 加载向量存储
        vector_store = None
        if os.path.exists(vector_db_path):
            vector_store = FAISS.load_local(vector_db_path)
            logger.info(f"向量存储加载成功: {vector_db_path}")
        else:
            logger.warning(f"向量数据库路径不存在: {vector_db_path}")
        
        # 创建增强版QA系统
        qa_system = EnhancedQASystem(
            vector_store=vector_store,
            api_key=api_key,
            memory_manager=memory_manager,
            config=config
        )
        
        return qa_system
        
    except Exception as e:
        logger.error(f"加载增强版QA系统失败: {e}")
        return None 