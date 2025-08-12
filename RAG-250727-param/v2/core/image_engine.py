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
    
    def __init__(self, config: ImageEngineConfig, vector_store=None):
        """
        初始化图片引擎
        
        :param config: 图片引擎配置
        :param vector_store: 向量数据库
        """
        super().__init__(config)
        self.vector_store = vector_store
        self.image_docs = {}  # 缓存的图片文档
        
        # 在设置完vector_store后调用_initialize
        self._initialize()
        
        # 加载图片文档
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
    
    def _load_image_documents(self):
        """加载图片文档到缓存"""
        if not self.vector_store or not hasattr(self.vector_store, 'docstore'):
            self.logger.warning("向量数据库未提供或没有docstore属性")
            return
        
        try:
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
                    self.logger.debug(f"加载图片文档: {doc_id}, 元数据: {list(doc.metadata.keys())}")
            
            self.logger.info(f"成功加载 {len(self.image_docs)} 个图片文档")
            
            # 如果没有找到图片文档，尝试其他方法
            if not self.image_docs:
                self.logger.warning("未找到图片文档，尝试搜索所有文档...")
                self._search_all_documents_for_images()
                
        except Exception as e:
            self.logger.error(f"加载图片文档失败: {e}")
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
            'confidence': 0.0
        }
        
        # 提取关键词
        keywords = self._extract_keywords(query)
        intent['keywords'] = keywords
        
        # 检测图表编号
        import re
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
        搜索图片
        :param query: 查询文本
        :param intent: 查询意图
        :return: 匹配的图片列表
        """
        results = []
        self.logger.debug(f"搜索图片，查询: {query}, 意图: {intent}")
        self.logger.debug(f"可用图片文档数量: {len(self.image_docs)}")

        # 图号精确匹配
        if intent['figure_numbers']:
            for doc_id, doc in self.image_docs.items():
                caption = doc.metadata.get('img_caption', '')
                title = doc.metadata.get('image_title', '')
                caption_text = str(caption) if caption else ''
                title_text = str(title) if title else ''
                if any(f'图{num}' in caption_text or f'图{num}' in title_text for num in intent['figure_numbers']):
                    results.append({
                        'doc_id': doc_id,
                        'image_path': doc.metadata.get('image_path', ''),
                        'enhanced_description': doc.metadata.get('enhanced_description', ''),
                        'caption': caption,
                        'title': title,
                        'score': 1.0,
                        'match_type': 'exact_figure'
                    })

        # 关键词匹配
        if intent['keywords']:
            for doc_id, doc in self.image_docs.items():
                try:
                    score = self._calculate_image_score(doc, query, intent)
                    if score >= self.config.image_similarity_threshold:
                        results.append({
                            'doc_id': doc_id,
                            'image_path': doc.metadata.get('image_path', ''),
                            'enhanced_description': doc.metadata.get('enhanced_description', ''),
                            'caption': doc.metadata.get('img_caption', ''),
                            'title': doc.metadata.get('image_title', ''),
                            'score': score,
                            'match_type': 'keyword_match'
                        })
                except Exception as e:
                    self.logger.warning(f"计算图片分数失败 {doc_id}: {e}")
                    continue

        # 如果没有找到结果，尝试模糊匹配
        if not results and self.config.enable_fuzzy_match:
            fuzzy_results = self._fuzzy_image_search(query, intent)
            # 补充image_path和enhanced_description
            for item in fuzzy_results:
                doc = item.get('doc')
                item['image_path'] = doc.metadata.get('image_path', '') if doc else ''
                item['enhanced_description'] = doc.metadata.get('enhanced_description', '') if doc else ''
                item['caption'] = doc.metadata.get('img_caption', '') if doc else ''
                item['title'] = doc.metadata.get('image_title', '') if doc else ''
            results = fuzzy_results

        self.logger.debug(f"搜索结果数量: {len(results)}")
        return results
    
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
        
        # 简单的词汇重叠计算
        query_words = set(query.lower().split())
        text_words = set(text.lower().split())
        
        if not query_words or not text_words:
            return 0.0
        
        intersection = query_words.intersection(text_words)
        union = query_words.union(text_words)
        
        if union:
            return len(intersection) / len(union)
        return 0.0
    
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
