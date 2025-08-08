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
import re
from typing import Dict, Any, List, Optional, Tuple
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
        qa_config = self.config.get('qa_system', {})
        model_name = qa_config.get('model_name', 'qwen-turbo')
        temperature = qa_config.get('temperature', 0.5)
        max_tokens = qa_config.get('max_tokens', 1500)
        
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

            ## 图片显示指导
            **重要**：如果回答中涉及图片或图表，请专注于描述图表的内容和含义：
            - 详细解释图表展示的数据和趋势
            - 说明图表与用户问题的关联性
            - 用自然的语言描述图表的作用和意义
            - **不要**在回答中使用图片标记格式（如 ![图片](路径)）
            - **不要**引用具体的图片文件路径
            - 系统会自动根据您的回答内容智能显示相关图片
            - 如果用户明确要求显示特定图片，请描述图片内容但不要使用路径引用

            ## 回答格式
            请使用Markdown格式组织回答

            ## 特殊情况处理
            - 如果文档中没有相关信息，请明确说明"根据提供的文档内容，没有找到相关信息"
            - 如果问题涉及多个方面，请分点详细说明
            - 如果涉及技术概念，请先解释概念再回答问题
            - **重要**：不要引用任何历史对话，只基于当前文档内容回答
            - 如果用户询问图片相关内容，请智能判断哪些图片需要显示

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

            ## 图片显示指导
            **重要**：如果回答中涉及图片或图表，请专注于描述图表的内容和含义：
            - 详细解释图表展示的数据和趋势
            - 说明图表与用户问题的关联性
            - 用自然的语言描述图表的作用和意义
            - **不要**在回答中使用图片标记格式（如 ![图片](路径)）
            - **不要**引用具体的图片文件路径
            - 系统会自动根据您的回答内容智能显示相关图片
            - 如果用户明确要求显示特定图片，请描述图片内容但不要使用路径引用

            ## 回答格式
            请使用Markdown格式组织回答

            ## 特殊情况处理
            - 如果文档中没有相关信息，请明确说明"根据提供的文档内容，没有找到相关信息"
            - 如果问题涉及多个方面，请分点详细说明
            - 如果涉及技术概念，请先解释概念再回答问题
            - 如果有相关历史对话，请适当引用和对比
            - 如果用户询问图片相关内容，请智能判断哪些图片需要显示

            请确保回答内容准确、有用且易于理解。

            基于以下文档内容和对话历史回答问题：

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
            vector_config = self.config.get('vector_store', {})
            k = k or vector_config.get('similarity_top_k', 3)
            
            logger.info(f"开始处理问题: {question[:50]}")
            
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
            
            # 6. 答案验证和智能过滤
            validated_answer, filtered_sources = self._validate_answer_and_filter_sources(answer_result['answer'], final_sources)
            
            # 计算处理时间
            processing_time = time.time() - start_time
            
            # 构建结果
            result = {
                'answer': validated_answer,
                'sources': filtered_sources,
                'cost': answer_result.get('cost', 0.0),
                'processing_time': processing_time,
                'optimization_stats': self._get_optimization_stats(initial_docs, reranked_docs, filtered_docs, filtered_sources)
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
    
    def answer_with_memory(self, user_id: str, question: str, k: int = None) -> Dict[str, Any]:
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
            
            # 检查是否有相关记忆且记忆未被清除
            has_relevant_memory = (not self.memory_cleared_flag and
                                 memory_context.get('memory_context') and 
                                 memory_context.get('memory_count', 0) > 0 and
                                 not self._is_exact_duplicate_question(question, memory_context.get('memories', [])))
            
            if has_relevant_memory:
                # 有相关记忆时，将记忆上下文整合到问题中
                enhanced_question = f"""问题：{question}

## 相关历史对话
{memory_context['memory_context']}

## 智能上下文理解指导
你是一个具有强大上下文理解能力的AI助手。请遵循以下原则：

### 指代词理解策略
1. **时间指代**：
   - "那2025年的呢" → 基于前面提到的某一年的相关信息
   - "去年"、"今年" → 基于对话时间上下文

2. **对象指代**：
   - "这个图"、"那个表" → 基于前面提到的具体内容
   - "它"、"其" → 基于前面提到的实体或概念

3. **概念指代**：
   - "这个数据"、"那个指标" → 基于前面提到的具体数据
   - "这种情况"、"那个问题" → 基于前面提到的具体情境

### 回答要求
1. 首先分析历史对话中的相关信息
2. 准确理解指代词的具体指向
3. 基于文档内容和历史对话提供准确回答
4. 保持对话的连贯性和自然性
5. 如果无法确定指代内容，请明确说明

请基于以上历史对话和文档内容，准确理解用户的指代词，并提供连贯、准确的回答。"""
                
                # 使用增强的问题进行回答
                result = self.answer_question(enhanced_question, k)
            else:
                # 没有相关记忆或记忆被清除时，正常回答
                result = self.answer_question(question, k)
            
            # 只有在记忆未被清除时才保存到记忆
            if not self.memory_cleared_flag:
                # 转换sources为可序列化的格式
                serializable_sources = []
                for source in result.get('sources', []):
                    # 确保content是字符串
                    content = source.get('content', '')
                    if not isinstance(content, str):
                        content = str(content)
                    
                    # 确保metadata是可序列化的
                    metadata = source.get('metadata', {})
                    if isinstance(metadata, dict):
                        # 过滤掉不可序列化的值
                        clean_metadata = {}
                        for key, value in metadata.items():
                            try:
                                # 测试是否可序列化
                                import json
                                json.dumps(value)
                                clean_metadata[key] = value
                            except (TypeError, ValueError):
                                # 如果不可序列化，转换为字符串
                                clean_metadata[key] = str(value)
                    else:
                        clean_metadata = str(metadata)
                    
                    serializable_source = {
                        'content': content,
                        'metadata': clean_metadata,
                        'score': float(source.get('score', 0.0))
                    }
                    serializable_sources.append(serializable_source)
                
                try:
                    self.memory_manager.add_to_session(
                        user_id=user_id,
                        question=question,
                        answer=result['answer'],
                        context={
                            'sources': serializable_sources,
                            'cost': result.get('cost', 0.0),
                            'relevant_memories': len(relevant_memories)
                        }
                    )
                except Exception as e:
                    logger.error(f"保存会话记忆失败: {e}")
                    # 如果保存失败，尝试简化版本
                    try:
                        self.memory_manager.add_to_session(
                            user_id=user_id,
                            question=question,
                            answer=result['answer'],
                            context={
                                'cost': result.get('cost', 0.0),
                                'relevant_memories': len(relevant_memories)
                            }
                        )
                    except Exception as e2:
                        logger.error(f"简化版记忆保存也失败: {e2}")
            
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
            logger.error(f"搜索图片文档失败: {e}")
            return []
    
    def _initial_retrieval(self, question: str, k: int) -> List[Document]:
        """
        改进的初始检索方法 - 确保文档来源平衡，并支持图片文档强制检索
        :param question: 问题
        :param k: 检索数量
        :return: 检索到的文档
        """
        if not self.vector_store:
            return []
        
        try:
            # 检查是否包含图片请求
            image_request_keywords = ['图', '图表', '图片', 'figure', '显示图', '看看图']
            has_image_request = any(keyword in question for keyword in image_request_keywords)
            
            # 提取用户的原始问题（去除记忆上下文）
            original_question = self._extract_original_question(question)
            
            # 检查是否要求显示特定图片编号或完整标题（只从原始问题中提取）
            figure_pattern = r'图(\d+)'
            figure_matches = re.findall(figure_pattern, original_question)
            
            all_docs = []
            
            # 如果有特定图片请求，优先处理
            if figure_matches:
                logger.info(f"检测到特定图片请求: {figure_matches}")
                
                # 直接遍历所有图片文档，查找匹配的图片
                for figure_num in figure_matches:
                    logger.info(f"查找图{figure_num}")
                    found_figure = False
                    
                    for doc_id, doc in self.vector_store.docstore._dict.items():
                        if doc.metadata.get('chunk_type') == 'image':
                            caption = doc.metadata.get('img_caption', [''])
                            caption_text = ' '.join(caption) if caption else ''
                            
                            # 使用精确的正则表达式匹配
                            exact_patterns = [
                                rf"图{figure_num}[：:]\s*",  # 图1：或图1:
                                rf"图{figure_num}\s+",       # 图1 后面跟空格
                                rf"图{figure_num}$",         # 图1 在字符串末尾
                                rf"图{figure_num}[）\)]",    # 图1）或图1)
                            ]
                            
                            is_match = any(re.search(pattern, caption_text) for pattern in exact_patterns)
                            
                            if is_match:
                                # 检查是否已经添加过这个图片
                                current_image_id = doc.metadata.get('image_id')
                                already_added = any(
                                    existing_doc.metadata.get('image_id') == current_image_id 
                                    for existing_doc in all_docs
                                )
                                
                                if not already_added:
                                    all_docs.append(doc)
                                    logger.info(f"找到并添加图{figure_num}: {caption_text}")
                                    found_figure = True
                    
                    if not found_figure:
                        logger.warning(f"未找到图{figure_num}")
                
                # 如果找到了特定图片，进行智能选择
                if all_docs:
                    logger.info(f"找到 {len(all_docs)} 个特定图片")
                    
                    # 如果找到多个图片且用户输入了完整标题，选择最匹配的一个
                    if len(all_docs) > 1 and ('：' in original_question or ':' in original_question):
                        best_doc = max(all_docs, key=lambda doc: 
                            self._calculate_overlap_score(original_question, doc.metadata.get('img_caption', [])))
                        logger.info(f"用户输入了完整标题，选择最匹配的图片: {best_doc.metadata.get('img_caption', [''])}")
                        return [best_doc]
                    else:
                        # 否则返回所有匹配的图片
                        logger.info("返回所有匹配的图片")
                        return all_docs[:k]
            
            # 如果没有找到特定图片或没有特定图片请求，进行常规检索
            # 第一步：获取所有文档的文档名称
            doc_names = set()
            for doc in self.vector_store.docstore._dict.values():
                doc_name = doc.metadata.get('document_name', '未知文档')
                doc_names.add(doc_name)
            
            # 第二步：为每个文档分配检索配额
            total_docs = len(doc_names)
            base_k_per_doc = max(1, k // total_docs)  # 每个文档至少检索1个
            remaining_k = k - (base_k_per_doc * total_docs)
            
            # 第三步：分别从每个文档检索
            doc_results = {}
            
            for doc_name in doc_names:
                try:
                    # 为每个文档检索指定数量的文档
                    docs = self.vector_store.similarity_search(
                        question, 
                        k=base_k_per_doc,
                        filter={"document_name": doc_name}
                    )
                    doc_results[doc_name] = len(docs)
                    all_docs.extend(docs)
                except Exception as e:
                    logger.warning(f"文档 {doc_name} 检索失败: {e}")
                    doc_results[doc_name] = 0
            
            # 第四步：如果有图片请求，强制检索图片文档
            if has_image_request and not figure_matches:
                try:
                    logger.info("进行通用图片检索")
                    image_docs = self.vector_store.similarity_search(
                        question,
                        k=min(3, k),  # 最多检索3个图片文档
                        filter={"chunk_type": "image"}
                    )
                    
                    # 过滤掉已经选中的图片文档
                    selected_doc_contents = {doc.page_content for doc in all_docs}
                    additional_image_docs = []
                    
                    for doc in image_docs:
                        if doc.page_content not in selected_doc_contents:
                            additional_image_docs.append(doc)
                            selected_doc_contents.add(doc.page_content)
                    
                    all_docs.extend(additional_image_docs)
                    logger.info(f"通用图片检索: 新增 {len(additional_image_docs)} 个图片文档")
                    
                except Exception as e:
                    logger.warning(f"图片文档强制检索失败: {e}")
            
            # 第五步：如果还有剩余配额，按相似度补充
            if remaining_k > 0 and len(all_docs) < k:
                try:
                    # 获取所有文档，按相似度排序
                    all_available_docs = self.vector_store.similarity_search(question, k=k*2)
                    
                    # 过滤掉已经选中的文档
                    selected_doc_contents = {doc.page_content for doc in all_docs}
                    additional_docs = []
                    
                    for doc in all_available_docs:
                        if doc.page_content not in selected_doc_contents and len(additional_docs) < remaining_k:
                            additional_docs.append(doc)
                            selected_doc_contents.add(doc.page_content)
                    
                    all_docs.extend(additional_docs)
                    logger.info(f"补充检索: 新增 {len(additional_docs)} 个文档")
                    
                except Exception as e:
                    logger.warning(f"补充检索失败: {e}")
            
            # 第六步：统计最终结果
            final_doc_sources = {}
            for doc in all_docs[:k]:
                doc_name = doc.metadata.get('document_name', '未知文档')
                final_doc_sources[doc_name] = final_doc_sources.get(doc_name, 0) + 1
            
            logger.info(f"最终检索结果分布: {final_doc_sources}")
            logger.info(f"总计检索到: {len(all_docs[:k])} 个文档")
            
            return all_docs[:k]
            
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
                # 保存重排序分数到metadata中
                doc.metadata['rerank_score'] = doc_dict.get('rerank_score', 0.0)
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
                # 保存智能过滤分数到metadata中
                doc.metadata['smart_filter_scores'] = doc_dict.get('smart_filter_scores', {})
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
            
            # 准备上下文 - 对于图片文档，使用enhanced_description作为内容
            context_parts = []
            for doc in documents:
                if doc.metadata.get('chunk_type') == 'image':
                    # 对于图片文档，使用enhanced_description
                    enhanced_desc = doc.metadata.get('enhanced_description', '')
                    img_caption = doc.metadata.get('img_caption', [''])
                    caption_text = ' '.join(img_caption) if img_caption else ''
                    
                    if enhanced_desc:
                        content = f"图片标题: {caption_text}\n图片描述: {enhanced_desc}"
                    else:
                        content = f"图片标题: {caption_text}"
                else:
                    # 对于文字文档，使用page_content
                    content = doc.page_content
                
                context_parts.append(content)
            
            context = "\n\n".join(context_parts)
            
            # 调试信息：打印上下文内容
            logger.info(f"LLM接收到的上下文长度: {len(context)}")
            logger.info(f"上下文内容预览: {context[:500]}...")
            
            # 生成回答
            try:
                response = self.qa_chain.invoke({
                    "input_documents": documents,
                    "question": question
                })
                
                # 确保response是字符串
                if isinstance(response, dict):
                    # 如果是字典，提取output_text或result
                    if 'output_text' in response:
                        response = response['output_text']
                    elif 'result' in response:
                        response = response['result']
                    elif 'answer' in response:
                        response = response['answer']
                    else:
                        # 如果是包含input_documents的调试信息，提取关键信息
                        if 'input_documents' in response:
                            logger.warning("LLM返回了调试信息，尝试提取回答")
                            # 尝试从文档内容中提取有用信息
                            docs_content = []
                            for doc in response.get('input_documents', []):
                                if hasattr(doc, 'page_content'):
                                    docs_content.append(doc.page_content)
                            if docs_content:
                                response = f"基于以下文档内容回答问题：\n\n{chr(10).join(docs_content[:3])}\n\n问题：{question}\n\n回答：根据提供的文档内容，没有找到相关信息。"
                            else:
                                response = "根据提供的文档内容，没有找到相关信息。"
                        else:
                            response = str(response)
                elif hasattr(response, 'content'):
                    response = response.content
                elif hasattr(response, 'text'):
                    response = response.text
                elif hasattr(response, 'result'):
                    response = response.result
                elif hasattr(response, 'output_text'):
                    response = response.output_text
                elif hasattr(response, 'output'):
                    response = response.output
                elif not isinstance(response, str):
                    response = str(response)
                    
                # 如果response太短，可能是错误
                if len(response.strip()) < 10:
                    logger.warning(f"LLM回答过短: '{response}'")
                    context = "\n\n".join([doc.page_content for doc in documents])
                    response = f"基于以下文档内容回答问题：\n\n{context}\n\n问题：{question}\n\n回答：根据提供的文档内容，没有找到相关信息。"
                    
            except Exception as e:
                logger.error(f"问答链调用失败: {e}")
                # 使用简单的字符串拼接作为备选方案
                context = "\n\n".join([doc.page_content for doc in documents])
                response = f"基于以下文档内容回答问题：\n\n{context}\n\n问题：{question}\n\n回答：根据提供的文档内容，没有找到相关信息。"
            
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
    
    def _extract_original_question(self, question: str) -> str:
        """
        从增强问题中提取用户的原始问题
        :param question: 可能包含记忆上下文的增强问题
        :return: 用户的原始问题
        """
        # 如果问题以"问题："开头，说明包含了记忆上下文
        if question.startswith("问题："):
            # 提取"问题："后面的内容，直到遇到"##"或文件末尾
            lines = question.split('\n')
            for line in lines:
                if line.startswith("问题："):
                    return line.replace("问题：", "").strip()
        
        # 如果没有"问题："前缀，直接返回原问题
        return question
    
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
            logger.error(f"计算相似度时发生错误: {e}")
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

    def _validate_answer_and_filter_sources(self, answer: str, sources: List[Any]) -> Tuple[str, List[Any]]:
        """
        验证答案并智能过滤源文档
        :param answer: LLM的回答
        :param sources: 检索到的源文档
        :return: (验证后的答案, 过滤后的源文档)
        """
        # 检查是否明确表示没有找到相关内容
        no_found_keywords = [
            '没有找到', '未找到', '不存在', '没有直接提到', '没有展示',
            '没有相关信息', '没有相关图片', '没有相关数据', '没有相关图表',
            '没有提及', '没有涉及', '没有包含', '没有显示', '没有提供',
            '并未提供', '并未提及', '并未展示', '并未包含', '没有提到',
            '没有提到或展示', '没有提到或', '没有展示或', '没有涉及或'
        ]
        
        answer_lower = answer.lower()
        is_no_found = any(keyword in answer_lower for keyword in no_found_keywords)
        
        if is_no_found:
            logger.info("检测到'没有找到'的回答，将过滤掉所有源文档")
            # 如果明确说没有找到，则不返回任何源文档
            return answer, []
        else:
            # 如果找到了相关内容，返回所有源文档
            return answer, sources

    def _calculate_overlap_score(self, user_input: str, caption_list: List[str]) -> int:
        """
        计算用户输入与图片标题的词汇重叠度
        :param user_input: 用户输入的问题
        :param caption_list: 图片标题列表
        :return: 重叠词汇数量
        """
        caption_text = ' '.join(caption_list)
        
        # 提取用户输入中的中文词汇和数字
        import re
        user_words = set(re.findall(r'[\u4e00-\u9fff]+|\d+[Q\d]*', user_input))
        
        # 计算重叠的词汇数量
        overlap_count = sum(1 for word in user_words if word in caption_text)
        
        return overlap_count

    def _process_question_with_validation(self, question: str, user_id: str = None) -> Dict[str, Any]:
        """
        处理问题并验证答案
        :param question: 用户问题
        :param user_id: 用户ID
        :return: 处理结果
        """
        # 获取原始处理结果
        result = self._process_question(question, user_id)
        
        # 验证答案并过滤源文档
        answer = result.get('answer', '')
        sources = result.get('sources', [])
        
        validated_answer, filtered_sources = self._validate_answer_and_filter_sources(answer, sources)
        
        # 更新结果
        result['answer'] = validated_answer
        result['sources'] = filtered_sources
        
        return result


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
    from langchain_community.embeddings import DashScopeEmbeddings
    
    # 获取API密钥 - 按照优先级：参数 > 环境变量 > 默认值
    if not api_key:
        api_key = os.getenv('MY_DASHSCOPE_API_KEY', '')
    
    # 如果仍然没有API密钥，尝试从config.json加载
    if not api_key or api_key == '你的APIKEY':
        try:
            if os.path.exists("config.json"):
                with open("config.json", 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                api_key = config_data.get('api', {}).get('dashscope_api_key', '')
                if api_key:
                    logger.info("从config.json加载API密钥成功")
        except Exception as e:
            logger.warning(f"从config.json加载API密钥失败: {e}")
    
    if not api_key or api_key == '你的APIKEY':
        logger.error("错误: 未配置DashScope API密钥")
        return None
    
    # 如果没有提供配置，从Settings类加载
    if config is None:
        try:
            from config.settings import Settings
            settings = Settings.load_from_file("config.json")
            config = settings.to_dict()
            logger.info("从配置文件加载配置成功")
        except Exception as e:
            logger.warning(f"加载配置文件失败: {e}，使用默认配置")
            config = {}
    
    try:
        # 加载向量存储
        vector_store = None
        if os.path.exists(vector_db_path):
            embeddings = DashScopeEmbeddings(dashscope_api_key=api_key, model="text-embedding-v1")
            vector_store = FAISS.load_local(vector_db_path, embeddings, allow_dangerous_deserialization=True)
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