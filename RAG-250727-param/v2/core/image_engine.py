'''
程序说明：
## 1. 图片引擎 - 专门处理图片查询
## 2. 支持图片标题、描述、关键词匹配
## 3. 智能图片选择和排序
## 4. 向后兼容现有图片查询功能
'''

import logging
import time
from typing import Dict, Any, List, Optional, Union
from .base_engine import BaseEngine, QueryType, QueryResult, EngineConfig, EngineStatus


logger = logging.getLogger(__name__)


class ImageEngineConfig(EngineConfig):
    """图片引擎专用配置"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "image_engine"
        self.max_results = 20  # 图片查询可以返回更多结果
        self.image_similarity_threshold = 0.6  # 图片相似度阈值
        self.keyword_weight = 0.4  # 关键词权重
        self.caption_weight = 0.3  # 标题权重
        self.description_weight = 0.3  # 描述权重
        self.enable_fuzzy_match = True  # 启用模糊匹配
        self.enable_semantic_search = True  # 启用语义搜索


class ImageEngine(BaseEngine):
    """
    图片引擎
    
    专门处理图片查询，支持多种匹配策略
    """
    
    def __init__(self, config: ImageEngineConfig, vector_store=None, document_loader=None, skip_initial_load=False):
        """
        初始化图片引擎
        
        :param config: 图片引擎配置
        :param vector_store: 向量数据库
        :param document_loader: 统一文档加载器
        :param skip_initial_load: 是否跳过初始加载
        """
        super().__init__(config)
        self.vector_store = vector_store
        self.document_loader = document_loader
        self.image_docs = {}  # 缓存的图片文档
        self._docs_loaded = False
        
        # 在设置完vector_store后调用_initialize
        self._initialize()
        
        # 根据参数决定是否加载文档
        if not skip_initial_load:
            if document_loader:
                self._load_from_document_loader()
            else:
                self._load_image_documents()
    
    def _setup_components(self):
        """设置图片引擎组件"""
        if not self.vector_store:
            raise ValueError("向量数据库未提供")
        
        # 初始化图片文档缓存
        self._load_image_documents()
        
        # 设置图片处理组件
        self._setup_image_processors()
    
    def _setup_image_processors(self):
        """设置图片处理器"""
        # 这里可以添加图片预处理、特征提取等组件
        pass
    
    def _validate_config(self):
        """验证图片引擎配置"""
        # 支持两种配置类型：ImageEngineConfig 和 ImageEngineConfigV2
        from ..config.v2_config import ImageEngineConfigV2
        
        if not isinstance(self.config, (ImageEngineConfig, ImageEngineConfigV2)):
            raise ValueError("配置必须是ImageEngineConfig或ImageEngineConfigV2类型")
        
        # 获取相似度阈值，支持两种配置类型
        threshold = getattr(self.config, 'image_similarity_threshold', 0.6)
        if threshold < 0 or threshold > 1:
            raise ValueError("图片相似度阈值必须在0-1之间")
    
    def _load_from_document_loader(self):
        """从统一文档加载器获取图片文档"""
        if self.document_loader:
            try:
                self.image_docs = self.document_loader.get_documents_by_type('image')
                self._docs_loaded = True
                self.logger.info(f"从统一加载器获取图片文档: {len(self.image_docs)} 个")
            except Exception as e:
                self.logger.error(f"从统一加载器获取图片文档失败: {e}")
                # 降级到传统加载方式
                self._load_image_documents()
        else:
            self.logger.warning("文档加载器未提供，使用传统加载方式")
            self._load_image_documents()
    
    def clear_cache(self):
        """清理图片引擎缓存"""
        try:
            total_docs = len(self.image_docs)
            self.image_docs = {}
            self._docs_loaded = False
            
            self.logger.info(f"图片引擎缓存清理完成，共清理 {total_docs} 个文档")
            return total_docs
            
        except Exception as e:
            self.logger.error(f"清理图片引擎缓存失败: {e}")
            return 0
    
    def _ensure_docs_loaded(self):
        """确保文档已加载（延迟加载）"""
        if not self._docs_loaded:
            if self.document_loader:
                self._load_from_document_loader()
            else:
                self._load_image_documents()
                self._docs_loaded = True
    
    def _load_image_documents(self):
        """加载图片文档到缓存"""
        if not self.vector_store or not hasattr(self.vector_store, 'docstore'):
            self.logger.warning("❌ 向量数据库未提供或没有docstore属性")
            return
        
        try:
            self.logger.info(f"📚 开始加载图片文档...")
            self.logger.info(f"向量数据库文档总数: {len(self.vector_store.docstore._dict)}")
            
            # 统计所有文档的类型
            doc_types = {}
            for doc_id, doc in self.vector_store.docstore._dict.items():
                chunk_type = doc.metadata.get('chunk_type', '')
                if chunk_type not in doc_types:
                    doc_types[chunk_type] = 0
                doc_types[chunk_type] += 1
            
            self.logger.info(f"📊 文档类型统计: {doc_types}")
            
            # 从向量数据库加载所有图片文档
            for doc_id, doc in self.vector_store.docstore._dict.items():
                # 检查多种可能的图片标识
                chunk_type = doc.metadata.get('chunk_type', '')
                content_type = doc.metadata.get('content_type', '')
                doc_type = doc.metadata.get('doc_type', '')
                
                # 判断是否为图片文档 - 简化判断逻辑
                is_image = chunk_type == 'image'
                
                if is_image:
                    self.image_docs[doc_id] = doc
                    self.logger.debug(f"✅ 加载图片文档: {doc_id}")
                    self.logger.debug(f"  元数据字段: {list(doc.metadata.keys())}")
            
            self.logger.info(f"🎯 成功加载 {len(self.image_docs)} 个图片文档")
            
            # 如果没有找到图片文档，尝试其他方法
            if not self.image_docs:
                self.logger.warning("⚠️ 未找到图片文档，尝试搜索所有文档...")
                self._search_all_documents_for_images()
                
        except Exception as e:
            self.logger.error(f"❌ 加载图片文档失败: {e}")
            import traceback
            traceback.print_exc()
            self.image_docs = {}
    
    def _search_all_documents_for_images(self):
        """搜索所有文档中的图片内容"""
        try:
            for doc_id, doc in self.vector_store.docstore._dict.items():
                # 检查文档内容是否包含图片相关信息
                content = doc.metadata.get('content', '')
                if isinstance(content, str) and any(keyword in content.lower() for keyword in ['图', '图片', 'chart', 'figure']):
                    self.image_docs[doc_id] = doc
                    self.logger.debug(f"通过内容识别图片文档: {doc_id}")
        except Exception as e:
            self.logger.error(f"搜索图片文档失败: {e}")
    
    def process_query(self, query: str, **kwargs) -> QueryResult:
        """
        处理图片查询
        
        :param query: 查询文本
        :param kwargs: 额外参数
        :return: 查询结果
        """
        if not self.is_enabled():
            return QueryResult(
                success=False,
                query=query,
                query_type=QueryType.IMAGE,
                results=[],
                total_count=0,
                processing_time=0.0,
                engine_name=self.name,
                metadata={},
                error_message="图片引擎未启用"
            )
        
        # 确保文档已加载
        self._ensure_docs_loaded()
        
        start_time = time.time()
        
        try:
            # 分析查询意图
            intent = self._analyze_image_intent(query)
            
            # 执行图片搜索
            results = self._search_images(query, intent, **kwargs)
            
            # 智能排序
            sorted_results = self._rank_image_results(results, query, intent)
            
            processing_time = time.time() - start_time
            
            return QueryResult(
                success=True,
                query=query,
                query_type=QueryType.IMAGE,
                results=sorted_results,
                total_count=len(sorted_results),
                processing_time=processing_time,
                engine_name=self.name,
                metadata={'intent': intent, 'total_images': len(self.image_docs)}
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"图片查询失败: {e}")
            
            return QueryResult(
                success=False,
                query=query,
                query_type=QueryType.IMAGE,
                results=[],
                total_count=0,
                processing_time=processing_time,
                engine_name=self.name,
                metadata={},
                error_message=str(e)
            )
    
    def _analyze_image_intent(self, query: str) -> Dict[str, Any]:
        """
        分析图片查询意图
        
        :param query: 查询文本
        :return: 意图分析结果
        """
        intent = {
            'type': 'general',  # general, specific, very_specific
            'keywords': [],
            'figure_numbers': [],
            'content_types': [],
            'confidence': 0.0,
            'requested_count': None,  # 新增：用户请求的数量
            'show_all': False  # 新增：是否显示所有
        }
        
        # 检测"所有"、"全部"等关键词
        all_keywords = ['所有', '全部', '每一个', '每张', '每幅', '每张图', '每幅图']
        if any(keyword in query for keyword in all_keywords):
            intent['show_all'] = True
            self.logger.debug(f"检测到'显示所有'要求: {query}")
        
        # 检测数量要求（如"两张"、"3个"、"5幅"）
        import re
        count_matches = re.findall(r'(\d+)张|(\d+)个|(\d+)幅|(\d+)张图|(\d+)个图|(\d+)幅图', query)
        if count_matches:
            for match in count_matches:
                if any(match):
                    intent['requested_count'] = int([x for x in match if x][0])
                    self.logger.debug(f"检测到数量要求: {intent['requested_count']}")
                    break
        
        # 提取关键词
        keywords = self._extract_keywords(query)
        intent['keywords'] = keywords
        
        # 检测图表编号
        figure_matches = re.findall(r'图(\d+)', query)
        if figure_matches:
            intent['figure_numbers'] = [int(x) for x in figure_matches]
            intent['type'] = 'very_specific'
            intent['confidence'] = 0.9
        
        # 检测内容类型
        content_keywords = {
            '营收': 'financial',
            '利润': 'financial', 
            '季度': 'temporal',
            '年度': 'temporal',
            '增长': 'trend',
            '下降': 'trend',
            '对比': 'comparison',
            '分析': 'analysis'
        }
        
        for keyword, content_type in content_keywords.items():
            if keyword in query:
                intent['content_types'].append(content_type)
        
        # 根据关键词数量判断具体程度
        if len(keywords) >= 3:
            intent['type'] = 'specific'
            intent['confidence'] = 0.7
        elif len(keywords) >= 1:
            intent['type'] = 'general'
            intent['confidence'] = 0.5
        
        self.logger.debug(f"查询意图分析结果: {intent}")
        return intent
    
    def _extract_keywords(self, query: str) -> List[str]:
        """提取查询关键词"""
        # 简单的关键词提取，可以后续优化
        stop_words = {'的', '是', '在', '有', '和', '与', '或', '但', '而', '了', '吗', '呢', '啊'}
        
        # 移除标点符号
        import re
        clean_query = re.sub(r'[^\w\s]', '', query)
        
        # 分词并过滤停用词
        words = clean_query.split()
        keywords = [word for word in words if word not in stop_words and len(word) > 1]
        
        return keywords
    
    def _search_images(self, query: str, intent: Dict[str, Any], **kwargs) -> List[Any]:
        """
        智能图片搜索 - 支持图号过滤和内容精确匹配
        
        :param query: 查询文本
        :param intent: 查询意图
        :param kwargs: 其他参数
        :return: 匹配的图片列表
        """
        results = []
        self.logger.info(f"🔍 开始智能图片搜索")
        self.logger.info(f"查询: {query}")
        self.logger.info(f"意图: {intent}")
        self.logger.info(f"可用图片文档数量: {len(self.image_docs)}")
        
        # 显示前几个图片文档的元数据，帮助调试
        if self.image_docs:
            self.logger.info("📸 前3个图片文档的元数据:")
            for i, (doc_id, doc) in enumerate(list(self.image_docs.items())[:3]):
                self.logger.info(f"图片 {i+1}:")
                self.logger.info(f"  - 文档ID: {doc_id}")
                self.logger.info(f"  - chunk_type: {doc.metadata.get('chunk_type', 'N/A')}")
                self.logger.info(f"  - img_caption: {doc.metadata.get('img_caption', 'N/A')}")
                self.logger.info(f"  - image_title: {doc.metadata.get('image_title', 'N/A')}")
                self.logger.info(f"  - enhanced_description: {doc.metadata.get('enhanced_description', 'N/A')[:50] if doc.metadata.get('enhanced_description') else 'N/A'}...")

        # 第一步：图号过滤（如果用户提到了图号）
        if intent['figure_numbers']:
            self.logger.info(f"🎯 检测到图号查询，图号: {intent['figure_numbers']}")
            filtered_by_number = self._filter_by_figure_number(intent['figure_numbers'])
            
            if filtered_by_number:
                self.logger.info(f"✅ 图号过滤后剩余图片数量: {len(filtered_by_number)}")
                # 在过滤后的图片中进行内容精确匹配
                results = self._content_precise_match(query, filtered_by_number, intent)
                self.logger.info(f"✅ 内容精确匹配后结果数量: {len(results)}")
                # 图号查询返回所有匹配的结果，不限制数量
                return results
            else:
                self.logger.warning(f"❌ 未找到图号 {intent['figure_numbers']} 对应的图片")
                return []
        
        # 第二步：一般内容搜索（用户没有提到图号）
        self.logger.info("🔍 执行一般内容搜索")
        results = self._general_content_search(query, intent)
        self.logger.info(f"✅ 一般内容搜索结果数量: {len(results)}")
        if results:
            self.logger.info(f"📸 前3个结果预览:")
            for i, result in enumerate(results[:3]):
                self.logger.info(f"  结果 {i+1}: {result.get('caption', 'N/A')} (分数: {result.get('score', 0):.3f})")
        else:
            self.logger.warning("⚠️ 没有找到匹配的图片，可能的原因:")
            self.logger.warning("   - 相似度阈值过高")
            self.logger.warning("   - 关键词匹配失败")
            self.logger.warning("   - 图片元数据不完整")
        
        # 根据查询类型调整结果数量
        max_results = self._adjust_result_count(intent)
        self.logger.info(f"📊 调整后的最大结果数量: {max_results}")
        final_results = results[:max_results]
        self.logger.info(f"🎯 最终返回结果数量: {len(final_results)}")
        return final_results

    def _filter_by_figure_number(self, figure_numbers: List[int]) -> List[Any]:
        """
        根据图号进行第一层过滤
        
        :param figure_numbers: 图号列表
        :return: 过滤后的图片列表
        """
        filtered_images = []
        self.logger.info(f"🔍 开始图号过滤，查找图号: {figure_numbers}")
        
        for doc_id, doc in self.image_docs.items():
            # 获取图片标题和描述
            caption = doc.metadata.get('img_caption', '')
            title = doc.metadata.get('image_title', '')
            
            self.logger.debug(f"检查文档 {doc_id}:")
            self.logger.debug(f"  - caption: {caption}")
            self.logger.debug(f"  - title: {title}")
            
            # 检查图片标题或描述中是否包含指定的图号
            for fig_num in figure_numbers:
                caption_match = f'图{fig_num}' in str(caption)
                title_match = f'图{fig_num}' in str(title)
                
                if caption_match or title_match:
                    self.logger.info(f"✅ 找到匹配的图号 {fig_num} 在文档 {doc_id}")
                    self.logger.info(f"  - caption匹配: {caption_match}")
                    self.logger.info(f"  - title匹配: {title_match}")
                    filtered_images.append(doc)
                    break
        
        self.logger.info(f"🎯 图号过滤结果: 找到 {len(filtered_images)} 张图片")
        return filtered_images

    def _content_precise_match(self, query: str, filtered_images: List[Any], intent: Dict[str, Any]) -> List[Any]:
        """
        在过滤后的图片中进行内容精确匹配
        
        :param query: 查询文本
        :param filtered_images: 过滤后的图片列表
        :param intent: 查询意图
        :return: 精确匹配的图片列表
        """
        if not filtered_images:
            return []
        
        # 提取内容关键词（排除图号部分）
        content_query = self._extract_content_query(query)
        content_keywords = self._extract_keywords(content_query)
        
        self.logger.debug(f"内容查询: {content_query}, 关键词: {content_keywords}")
        
        # 计算每张图片的内容匹配分数
        scored_images = []
        for doc in filtered_images:
            score = self._calculate_content_similarity(query, doc, content_keywords)
            # 对于图号查询，即使分数为0也要返回，因为图号已经匹配了
            if intent.get('figure_numbers'):
                # 图号查询：确保最低分数，让所有匹配的图片都能返回
                score = max(score, 0.1)  # 设置最低分数为0.1
            
            scored_images.append((doc, score))
            self.logger.debug(f"图片 {doc.metadata.get('doc_id', 'unknown')} 分数: {score}")
        
        # 按分数排序
        scored_images.sort(key=lambda x: x[1], reverse=True)
        
        # 构建结果
        results = []
        for doc, score in scored_images:
            # 对于图号查询，返回所有匹配的图片
            if intent.get('figure_numbers') or score > 0:
                # 构建content字段，优先级：增强描述 > 图片标题 > 图片ID
                enhanced_desc = doc.metadata.get('enhanced_description', '')
                caption = doc.metadata.get('img_caption', '')
                content = enhanced_desc or caption or f"图片ID: {doc.metadata.get('doc_id', 'unknown')}"
                
                results.append({
                    'doc_id': doc.metadata.get('doc_id', 'unknown'),
                    'image_path': doc.metadata.get('image_path', ''),
                    'enhanced_description': enhanced_desc,
                    'caption': caption,
                    'title': doc.metadata.get('image_title', ''),
                    'content': content,
                    'score': score,
                    'match_type': 'content_precise_match',
                    'document_name': doc.metadata.get('document_name', '未知文档'),
                    'page_number': doc.metadata.get('page_number', 'N/A')
                })
        
        self.logger.info(f"内容精确匹配结果: {len(results)} 张图片")
        return results

    def _extract_content_query(self, query: str) -> str:
        """
        提取内容查询部分，排除图号
        
        :param query: 原始查询
        :return: 内容查询部分
        """
        import re
        # 移除"图X："部分，保留后面的内容
        content_query = re.sub(r'图\d+[：:]\s*', '', query)
        return content_query.strip()

    def _calculate_content_similarity(self, query: str, doc: Any, content_keywords: List[str]) -> float:
        """
        计算内容相似度分数
        
        :param query: 查询文本
        :param doc: 文档对象
        :param content_keywords: 内容关键词
        :return: 相似度分数 (0-1)
        """
        score = 0.0
        
        # 获取图片元数据
        caption = doc.metadata.get('img_caption', '')
        title = doc.metadata.get('image_title', '')
        description = doc.metadata.get('enhanced_description', '')
        
        self.logger.debug(f"计算相似度 - caption: {caption}, title: {title}, description: {description[:50] if description else 'N/A'}")
        
        # 标题匹配分数（权重最高）
        if title and title != 'N/A' and title != '无标题':
            title_score = self._calculate_text_similarity(query, title)
            score += title_score * 0.5  # 标题权重50%
            self.logger.debug(f"标题匹配分数: {title_score} * 0.5 = {title_score * 0.5}")
        
        # 描述匹配分数
        if description:
            desc_score = self._calculate_text_similarity(query, description)
            score += desc_score * 0.3  # 描述权重30%
            self.logger.debug(f"描述匹配分数: {desc_score} * 0.3 = {desc_score * 0.3}")
        
        # 标题匹配分数
        if caption:
            caption_score = self._calculate_text_similarity(query, caption)
            score += caption_score * 0.2  # 标题权重20%
            self.logger.debug(f"标题匹配分数: {caption_score} * 0.2 = {caption_score * 0.2}")
        
        # 关键词匹配加分
        if content_keywords:
            keyword_score = self._calculate_keyword_match(doc, content_keywords)
            score += keyword_score * 0.1  # 关键词权重10%
            self.logger.debug(f"关键词匹配分数: {keyword_score} * 0.1 = {keyword_score * 0.1}")
        
        final_score = min(score, 1.0)
        self.logger.debug(f"最终相似度分数: {final_score}")
        return final_score

    def _general_content_search(self, query: str, intent: Dict[str, Any]) -> List[Any]:
        """
        一般内容搜索（用户没有提到图号）
        
        :param query: 查询文本
        :param intent: 查询意图
        :return: 搜索结果列表
        """
        results = []
        
        # 关键词匹配
        if intent['keywords']:
            for doc_id, doc in self.image_docs.items():
                try:
                    score = self._calculate_image_score(doc, query, intent)
                    # 降低阈值，确保更多图片能被匹配到
                    if score >= 0.05:  # 使用更低的阈值
                        # 构建content字段
                        enhanced_desc = doc.metadata.get('enhanced_description', '')
                        caption = doc.metadata.get('img_caption', '')
                        content = enhanced_desc or caption or f"图片ID: {doc_id}"
                        
                        results.append({
                            'doc_id': doc_id,
                            'image_path': doc.metadata.get('image_path', ''),
                            'enhanced_description': enhanced_desc,
                            'caption': caption,
                            'title': doc.metadata.get('image_title', ''),
                            'content': content,
                            'score': score,
                            'match_type': 'keyword_match',
                            'document_name': doc.metadata.get('document_name', '未知文档'),
                            'page_number': doc.metadata.get('page_number', 'N/A')
                        })
                        
                        self.logger.debug(f"图片 {doc_id} 匹配成功，分数: {score}, 标题: {caption}")
                except Exception as e:
                    self.logger.warning(f"计算图片分数失败 {doc_id}: {e}")
                    continue
        
        # 如果没有找到结果，尝试模糊匹配
        if not results and self.config.enable_fuzzy_match:
            fuzzy_results = self._fuzzy_image_search(query, intent)
            # 补充字段
            for item in fuzzy_results:
                doc = item.get('doc')
                if doc:
                    enhanced_desc = doc.metadata.get('enhanced_description', '')
                    caption = doc.metadata.get('img_caption', '')
                    content = enhanced_desc or caption or f"图片ID: {item.get('doc_id', 'unknown')}"
                    
                    item['image_path'] = doc.metadata.get('image_path', '')
                    item['enhanced_description'] = enhanced_desc
                    item['caption'] = caption
                    item['title'] = doc.metadata.get('image_title', '')
                    item['content'] = content
                    item['document_name'] = doc.metadata.get('document_name', '未知文档')
                    item['page_number'] = doc.metadata.get('page_number', 'N/A')
            results = fuzzy_results
        
        return results

    def _adjust_result_count(self, intent: Dict[str, Any]) -> int:
        """
        根据查询意图调整结果数量
        
        :param intent: 查询意图
        :return: 结果数量
        """
        # 如果用户要求显示所有，返回一个很大的数字
        if intent.get('show_all'):
            self.logger.info("用户要求显示所有图片，返回最大数量")
            return 999  # 或者使用 len(self.image_docs) 获取实际图片总数
        
        # 如果用户明确要求了数量，优先使用用户的要求
        if intent.get('requested_count'):
            self.logger.info(f"用户要求显示 {intent['requested_count']} 张图片")
            return intent['requested_count']
        
        # 否则使用默认逻辑
        if intent['type'] == 'very_specific':
            return 10  # 非常具体的查询（包含图号），返回最多10个结果，确保能看到所有图号
        elif intent['type'] == 'specific':
            return 5  # 具体查询，返回5个结果
        else:
            return 3  # 一般查询，返回3个结果
    
    def _calculate_image_score(self, doc: Any, query: str, intent: Dict[str, Any]) -> float:
        """
        计算图片匹配分数
        
        :param doc: 文档对象
        :param query: 查询文本
        :param intent: 查询意图
        :return: 匹配分数 (0-1)
        """
        score = 0.0
        
        # 获取图片元数据，确保类型安全
        caption = doc.metadata.get('img_caption', '')
        title = doc.metadata.get('image_title', '')
        description = doc.metadata.get('enhanced_description', '')
        content = doc.metadata.get('content', '')
        
        # 标题匹配分数
        if title and title != '无标题':
            title_score = self._calculate_text_similarity(query, title)
            score += title_score * self.config.caption_weight
        
        # 标题匹配分数
        if caption:
            caption_score = self._calculate_text_similarity(query, caption)
            score += caption_score * self.config.caption_weight
        
        # 描述匹配分数
        if description:
            desc_score = self._calculate_text_similarity(query, description)
            score += desc_score * self.config.description_weight
        
        # 内容匹配分数
        if content:
            content_score = self._calculate_text_similarity(query, content)
            score += content_score * self.config.description_weight
        
        # 关键词匹配分数
        if intent['keywords']:
            keyword_score = self._calculate_keyword_match(doc, intent['keywords'])
            score += keyword_score * self.config.keyword_weight
        
        return min(score, 1.0)
    
    def _calculate_text_similarity(self, query: str, text: str) -> float:
        """计算文本相似度"""
        if not text or not query:
            return 0.0
        
        # 确保text是字符串类型
        if isinstance(text, list):
            text = ' '.join([str(item) for item in text])
        elif not isinstance(text, str):
            text = str(text)
        
        self.logger.debug(f"计算文本相似度 - query: '{query}', text: '{text}'")
        
        # 改进的相似度计算：结合词汇重叠和语义匹配
        query_words = set(query.lower().split())
        text_words = set(text.lower().split())
        
        if not query_words or not text_words:
            self.logger.debug(f"词汇为空 - query_words: {query_words}, text_words: {text_words}")
            return 0.0
        
        # 1. 词汇重叠分数
        intersection = query_words.intersection(text_words)
        union = query_words.union(text_words)
        
        if union:
            overlap_similarity = len(intersection) / len(union)
        else:
            overlap_similarity = 0.0
        
        # 2. 关键词密度分数
        matched_keywords = 0
        for keyword in query_words:
            if keyword in text.lower():
                matched_keywords += 1
        
        keyword_density = matched_keywords / len(query_words) if query_words else 0.0
        
        # 3. 长度匹配分数（短查询匹配长文本时给予加分）
        length_ratio = min(len(query) / max(len(text), 1), 1.0)
        length_score = 1.0 - abs(0.5 - length_ratio) * 0.5  # 0.5时最高分
        
        # 4. 综合分数
        final_similarity = (
            overlap_similarity * 0.4 +      # 词汇重叠权重40%
            keyword_density * 0.4 +         # 关键词密度权重40%
            length_score * 0.2              # 长度匹配权重20%
        )
        
        # 确保分数在合理范围内，避免过低
        final_similarity = max(final_similarity, 0.1)  # 最低分数0.1
        
        self.logger.debug(f"相似度计算 - 重叠: {overlap_similarity:.3f}, 密度: {keyword_density:.3f}, 长度: {length_score:.3f}, 最终: {final_similarity:.3f}")
        return final_similarity
    
    def _calculate_keyword_match(self, doc: Any, keywords: List[str]) -> float:
        """计算关键词匹配分数"""
        if not keywords:
            return 0.0
        
        # 获取所有文本字段，确保类型安全
        text_fields = []
        
        # 安全获取元数据字段
        caption = doc.metadata.get('img_caption', '')
        if isinstance(caption, list):
            caption = ' '.join([str(item) for item in caption])
        elif not isinstance(caption, str):
            caption = str(caption) if caption else ''
        text_fields.append(caption)
        
        title = doc.metadata.get('image_title', '')
        if isinstance(title, list):
            title = ' '.join([str(item) for item in title])
        elif not isinstance(title, str):
            title = str(title) if title else ''
        text_fields.append(title)
        
        description = doc.metadata.get('enhanced_description', '')
        if isinstance(description, list):
            description = ' '.join([str(item) for item in description])
        elif not isinstance(description, str):
            description = str(description) if description else ''
        text_fields.append(description)
        
        # 添加其他可能的文本字段
        content = doc.metadata.get('content', '')
        if isinstance(content, list):
            content = ' '.join([str(item) for item in content])
        elif not isinstance(content, str):
            content = str(content) if content else ''
        text_fields.append(content)
        
        total_score = 0.0
        for keyword in keywords:
            for field in text_fields:
                if field and keyword in field:
                    total_score += 1.0
                    break
        
        return min(total_score / len(keywords), 1.0)
    
    def _fuzzy_image_search(self, query: str, intent: Dict[str, Any]) -> List[Any]:
        """模糊图片搜索"""
        results = []
        
        # 使用向量相似度搜索
        if hasattr(self.vector_store, 'similarity_search'):
            try:
                # 搜索相似文档
                similar_docs = self.vector_store.similarity_search(
                    query, 
                    k=min(10, self.config.max_results)
                )
                
                # 过滤出图片文档
                for doc in similar_docs:
                    if doc.metadata.get('chunk_type') == 'image':
                        results.append({
                            'doc_id': doc.metadata.get('doc_id', 'unknown'),
                            'doc': doc,
                            'score': 0.5,  # 模糊匹配的默认分数
                            'match_type': 'fuzzy_search'
                        })
            except Exception as e:
                self.logger.warning(f"模糊搜索失败: {e}")
        
        return results
    
    def _rank_image_results(self, results: List[Any], query: str, intent: Dict[str, Any]) -> List[Any]:
        """
        对图片结果进行智能排序
        
        :param results: 搜索结果
        :param query: 查询文本
        :param intent: 查询意图
        :return: 排序后的结果
        """
        if not results:
            return []
        
        # 按分数排序
        sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)
        
        # 限制结果数量
        return sorted_results[:self.config.max_results]
    
    def get_image_by_id(self, image_id: str) -> Optional[Any]:
        """根据ID获取图片"""
        return self.image_docs.get(image_id)
    
    def get_all_images(self) -> List[Any]:
        """获取所有图片"""
        return list(self.image_docs.values())
    
    def refresh_image_cache(self):
        """刷新图片缓存"""
        self._load_image_documents()
        self.logger.info("图片缓存已刷新")
    
    def get_image_statistics(self) -> Dict[str, Any]:
        """获取图片统计信息"""
        return {
            'total_images': len(self.image_docs),
            'with_caption': len([d for d in self.image_docs.values() 
                               if d.metadata.get('img_caption')]),
            'with_title': len([d for d in self.image_docs.values() 
                             if d.metadata.get('image_title') and d.metadata.get('image_title') != '无标题']),
            'with_description': len([d for d in self.image_docs.values() 
                                   if d.metadata.get('enhanced_description')])
        }
