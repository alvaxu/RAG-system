"""
RAG召回引擎模块

RAG系统的召回引擎模块，负责多策略内容检索和智能召回
为RAG系统提供高效、准确的内容检索服务
"""

import logging
import time
from typing import Dict, List, Optional, Any
from .vector_db_integration import VectorDBIntegration

# 集成jieba分词工具
try:
    import jieba
    import jieba.analyse
    JIEBA_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("jieba分词工具加载成功")
except ImportError:
    JIEBA_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("jieba分词工具未安装，将使用基础分词方法")

logger = logging.getLogger(__name__)

class RetrievalEngine:
    """RAG召回引擎 - 多策略内容检索"""
    
    def __init__(self, config_integration, vector_db_integration: VectorDBIntegration):
        """
        初始化召回引擎
        
        :param config_integration: 配置集成管理器实例
        :param vector_db_integration: 向量数据库集成管理器实例
        """
        self.config = config_integration
        self.vector_db = vector_db_integration
        self.retrieval_stats = {
            'total_queries': 0,
            'total_results': 0,
            'average_response_time': 0.0,
            'last_query_time': None,
            'visual_searches': 0,
            'table_searches': 0
        }
        logger.info("召回引擎初始化完成")
    
    def retrieve_texts(self, query: str, max_results: int = 30, relevance_threshold: float = None) -> List[Dict[str, Any]]:
        """
        文本内容召回
        
        :param query: 查询文本
        :param max_results: 最大结果数量
        :param relevance_threshold: 相关性阈值，如果为None则使用配置文件中的值
        :return: 召回结果列表
        """
        start_time = time.time()
        try:
            logger.info(f"开始文本召回，查询: {query[:50]}...，最大结果: {max_results}")
            
            # 获取文本引擎配置
            text_config = self.config.get('rag_system.engines.text_engine', {})
            if relevance_threshold is None:
                similarity_threshold = text_config.get('similarity_threshold', 0.7)
            else:
                similarity_threshold = relevance_threshold
            
            logger.info(f"文本召回配置: 相似度阈值={similarity_threshold}")
            
            # 第一层：文本向量搜索
            logger.info("开始第一层：文本向量搜索")
            vector_results = self._text_vector_search(query, max_results, similarity_threshold)
            logger.info(f"第一层向量搜索完成，返回 {len(vector_results)} 个结果")
            
            # 第二层：文本关键词搜索
            logger.info("开始第二层：文本关键词搜索")
            keyword_results = self._text_keyword_search(query, max_results // 2, similarity_threshold)
            logger.info(f"第二层关键词搜索完成，返回 {len(keyword_results)} 个结果")
            
            # 第三层：文本扩展搜索
            logger.info("开始第三层：文本扩展搜索")
            expansion_results = self._text_expansion_search(query, max_results // 3, similarity_threshold)
            logger.info(f"第三层扩展搜索完成，返回 {len(expansion_results)} 个结果")
            
            # 合并和去重
            logger.info("开始合并和去重处理")
            all_results = self._deduplicate_and_sort(
                vector_results + keyword_results + expansion_results,
                max_results
            )
            
            # 更新统计信息
            self._update_stats(len(all_results), time.time() - start_time)
            
            logger.info(f"文本召回完成，查询: {query[:50]}...，最终结果: {len(all_results)}")
            return all_results
            
        except Exception as e:
            logger.error(f"文本召回失败: {e}")
            return []
    
    def retrieve_images(self, query: str, max_results: int = 20, relevance_threshold: float = None) -> List[Dict[str, Any]]:
        """
        图片内容召回
        
        :param query: 查询文本
        :param max_results: 最大结果数量
        :param relevance_threshold: 相关性阈值，如果为None则使用配置文件中的值
        :return: 召回结果列表
        """
        start_time = time.time()
        try:
            logger.info(f"开始图片召回，查询: {query[:50]}...，最大结果: {max_results}")
            
            # 获取图片引擎配置
            image_config = self.config.get('rag_system.engines.image_engine', {})
            if relevance_threshold is None:
                similarity_threshold = image_config.get('similarity_threshold', 0.3)
            else:
                similarity_threshold = relevance_threshold
            
            logger.info(f"图片召回配置: 相似度阈值={similarity_threshold}")
            
            # 第一层：图片语义搜索
            logger.info("开始第一层：图片语义搜索")
            semantic_results = self._image_semantic_search(query, max_results, similarity_threshold)
            logger.info(f"第一层语义搜索完成，返回 {len(semantic_results)} 个结果")
            
            # 第二层：图片视觉搜索
            logger.info("开始第二层：图片视觉搜索")
            visual_results = self._image_visual_search(query, max_results // 2, similarity_threshold)
            logger.info(f"第二层视觉搜索完成，返回 {len(visual_results)} 个结果")
            
            # 第三层：图片关键词搜索
            logger.info("开始第三层：图片关键词搜索")
            keyword_results = self._image_keyword_search(query, max_results // 3, similarity_threshold)
            logger.info(f"第三层关键词搜索完成，返回 {len(keyword_results)} 个结果")
            
            # 第四层：图片扩展搜索
            logger.info("开始第四层：图片扩展搜索")
            expansion_results = self._image_expansion_search(query, max_results // 4, similarity_threshold)
            logger.info(f"第四层扩展搜索完成，返回 {len(expansion_results)} 个结果")
            
            # 合并和去重
            logger.info("开始合并和去重处理")
            all_results = self._deduplicate_and_sort(
                semantic_results + visual_results + keyword_results + expansion_results,
                max_results
            )
            
            # 更新统计信息
            self._update_stats(len(all_results), time.time() - start_time)
            
            logger.info(f"图片召回完成，查询: {query[:50]}...，最终结果: {len(all_results)}")
            return all_results
            
        except Exception as e:
            logger.error(f"图片召回失败: {e}")
            return []
    
    def retrieve_tables(self, query: str, max_results: int = 15, relevance_threshold: float = None) -> List[Dict[str, Any]]:
        """
        表格内容召回
        
        :param query: 查询文本
        :param max_results: 最大结果数量
        :param relevance_threshold: 相关性阈值，如果为None则使用配置文件中的值
        :return: 召回结果列表
        """
        start_time = time.time()
        try:
            logger.info(f"开始表格召回，查询: {query[:50]}...，最大结果: {max_results}")
            
            # 获取表格引擎配置
            table_config = self.config.get('rag_system.engines.table_engine', {})
            if relevance_threshold is None:
                similarity_threshold = table_config.get('similarity_threshold', 0.65)
            else:
                similarity_threshold = relevance_threshold
            
            logger.info(f"表格召回配置: 相似度阈值={similarity_threshold}")
            
            # 第一层：表格结构搜索
            logger.info("开始第一层：表格结构搜索")
            structure_results = self._table_structure_search(query, max_results, similarity_threshold)
            logger.info(f"第一层结构搜索完成，返回 {len(structure_results)} 个结果")
            
            # 第二层：表格语义搜索
            logger.info("开始第二层：表格语义搜索")
            semantic_results = self._table_semantic_search(query, max_results // 2, similarity_threshold)
            logger.info(f"第二层语义搜索完成，返回 {len(semantic_results)} 个结果")
            
            # 第三层：表格关键词搜索
            logger.info("开始第三层：表格关键词搜索")
            keyword_results = self._table_keyword_search(query, max_results // 3, similarity_threshold)
            logger.info(f"第三层关键词搜索完成，返回 {len(keyword_results)} 个结果")
            
            # 第四层：表格扩展搜索
            logger.info("开始第四层：表格扩展搜索")
            expansion_results = self._table_expansion_search(query, max_results // 4, similarity_threshold)
            logger.info(f"第四层扩展搜索完成，返回 {len(expansion_results)} 个结果")
            
            # 合并和去重
            logger.info("开始合并和去重处理")
            all_results = self._deduplicate_and_sort(
                structure_results + semantic_results + keyword_results + expansion_results,
                max_results
            )
            
            # 更新统计信息
            self._update_stats(len(all_results), time.time() - start_time)
            self.retrieval_stats['table_searches'] += 1
            
            logger.info(f"表格召回完成，查询: {query[:50]}...，最终结果: {len(all_results)}")
            return all_results
            
        except Exception as e:
            logger.error(f"表格召回失败: {e}")
            return []
    
    def retrieve_hybrid(self, query: str, max_results: int = 25) -> List[Dict[str, Any]]:
        """
        混合内容召回 - 增强版
        
        :param query: 查询文本
        :param max_results: 最大结果数量
        :return: 召回结果列表
        """
        start_time = time.time()
        try:
            logger.info(f"开始混合召回，查询: {query[:50]}...，最大结果: {max_results}")
            
            # 获取混合引擎配置
            hybrid_config = self.config.get('rag_system.engines.hybrid_engine', {})
            weights = hybrid_config.get('weights', {'image': 0.3, 'text': 0.4, 'table': 0.3})
            cross_type_boost = hybrid_config.get('cross_type_boost', 0.2)
            
            logger.info(f"混合召回配置: 权重={weights}, 跨类型提升={cross_type_boost}")
            
            # 分别召回各类型内容
            logger.info("开始各类型内容召回")
            text_results = self.retrieve_texts(query, int(max_results * weights['text']))
            image_results = self.retrieve_images(query, int(max_results * weights['image']))
            table_results = self.retrieve_tables(query, int(max_results * weights['table']))
            
            logger.info(f"各类型召回结果: 文本={len(text_results)}, 图片={len(image_results)}, 表格={len(table_results)}")
            
            # 计算跨类型相关性
            logger.info("开始计算跨类型相关性")
            enhanced_results = self._enhance_cross_type_relevance(
                text_results, image_results, table_results, query, cross_type_boost
            )
            logger.info(f"跨类型相关性增强完成，结果数: {len(enhanced_results)}")
            
            # 智能融合搜索结果
            logger.info("开始智能融合搜索结果")
            fused_results = self._fuse_hybrid_results(
                enhanced_results, query, max_results
            )
            logger.info(f"智能融合完成，结果数: {len(fused_results)}")
            
            # 去重和排序
            logger.info("开始去重和排序")
            final_results = self._deduplicate_and_sort(fused_results, max_results)
            
            # 更新统计信息
            self._update_stats(len(final_results), time.time() - start_time)
            
            logger.info(f"混合召回完成，查询: {query[:50]}...，最终结果: {len(final_results)}")
            return final_results
            
        except Exception as e:
            logger.error(f"混合召回失败: {e}")
            return []
    
    def smart_retrieve(self, query: str, query_type: str = None, 
                      content_type: str = None, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        智能召回 - 根据查询类型和内容类型自动选择召回策略
        
        :param query: 查询文本
        :param query_type: 查询类型
        :param content_type: 内容类型
        :param max_results: 最大结果数量
        :return: 召回结果列表
        """
        try:
            # 自动检测查询类型
            if query_type is None:
                query_type = self._detect_query_type(query)
            
            # 自动检测内容类型
            if content_type is None:
                content_type = self._detect_content_type(query)
            
            # 根据类型选择召回策略
            if content_type == 'image':
                return self.retrieve_images(query, max_results)
            elif content_type == 'table':
                return self.retrieve_tables(query, max_results)
            elif content_type == 'text':
                return self.retrieve_texts(query, max_results)
            else:
                # 默认使用混合召回
                return self.retrieve_hybrid(query, max_results)
                
        except Exception as e:
            logger.error(f"智能召回失败: {e}")
            return []
    
    # 文本召回策略实现
    def _text_vector_search(self, query: str, max_results: int, threshold: float) -> List[Dict[str, Any]]:
        """文本向量搜索"""
        try:
            results = self.vector_db.search_texts(query, max_results, threshold)
            for result in results:
                result['strategy'] = 'vector_similarity'
                result['layer'] = 1
            return results
        except Exception as e:
            logger.error(f"文本向量搜索失败: {e}")
            return []
    
    def _text_keyword_search(self, query: str, max_results: int, threshold: float) -> List[Dict[str, Any]]:
        """文本关键词搜索"""
        try:
            # 提取关键词
            keywords = self._extract_text_keywords(query)
            if not keywords:
                return []
            
            # 使用关键词进行搜索
            results = []
            for keyword in keywords[:3]:  # 限制关键词数量
                keyword_results = self.vector_db.search_texts(keyword, max_results // 3, threshold)
                for result in keyword_results:
                    result['strategy'] = 'keyword_matching'
                    result['layer'] = 2
                    result['keyword'] = keyword
                results.extend(keyword_results)
            
            return results
        except Exception as e:
            logger.error(f"文本关键词搜索失败: {e}")
            return []
    
    def _text_expansion_search(self, query: str, max_results: int, threshold: float) -> List[Dict[str, Any]]:
        """文本扩展搜索"""
        try:
            # 生成扩展查询
            expanded_queries = self._generate_expanded_queries(query)
            if not expanded_queries:
                return []
            
            # 使用扩展查询进行搜索
            results = []
            for expanded_query in expanded_queries[:2]:  # 限制扩展查询数量
                expanded_results = self.vector_db.search_texts(expanded_query, max_results // 2, threshold)
                for result in expanded_results:
                    result['strategy'] = 'query_expansion'
                    result['layer'] = 3
                    result['expanded_query'] = expanded_query
                results.extend(expanded_results)
            
            return results
        except Exception as e:
            logger.error(f"文本扩展搜索失败: {e}")
            return []
    
    # 图片召回策略实现

    def _image_semantic_search(self, query: str, max_results: int, threshold: float) -> List[Dict[str, Any]]:
        """图片语义搜索"""
        try:
            results = self.vector_db.search_images(query, max_results, threshold)
            for result in results:
                result['strategy'] = 'semantic_similarity'
                result['layer'] = 1
            return results
        except Exception as e:
            logger.error(f"图片语义搜索失败: {e}")
            return []
    
    def _image_visual_search(self, query: str, max_results: int, threshold: float) -> List[Dict[str, Any]]:
        """
        图片视觉搜索 - 使用multimodal-embedding-one-peace-v1模型在visual_embedding向量空间中搜索
        
        :param query: 查询文本
        :param max_results: 最大结果数量
        :param threshold: 相似度阈值
        :return: 搜索结果列表
        """
        try:
            logger.info(f"开始图片视觉搜索，查询: {query[:50]}...，最大结果: {max_results}，阈值: {threshold}")
            
            # 1. 使用配置中的图片embedding模型将查询文本向量化
            image_embedding_model = self.config.get('vectorization.image_embedding_model', 'multimodal-embedding-one-peace-v1')
            logger.info(f"使用{image_embedding_model}模型向量化查询文本")
            try:
                # 直接使用DashScope的MultiModalEmbedding API，而不是LangChain包装
                import dashscope
                from dashscope import MultiModalEmbedding
                
                # 设置API密钥
                api_key = self.vector_db.vector_store_manager.config_manager.get_environment_manager().get_required_var('DASHSCOPE_API_KEY')
                dashscope.api_key = api_key
                
                # 构建正确的输入格式：纯文本输入
                input_data = [{'text': query}]
                
                # 调用多模态embedding模型
                result = MultiModalEmbedding.call(
                    model=image_embedding_model,
                    input=input_data,
                    auto_truncation=True
                )
                
                if result.status_code == 200:
                    query_vector = result.output["embedding"]
                    logger.info(f"多模态模型向量化完成，向量维度: {len(query_vector)}")
                else:
                    raise Exception(f"多模态模型调用失败: {result.message}")
                    
            except Exception as e:
                logger.error(f"多模态模型向量化失败: {e}")
                raise Exception(f"无法使用多模态模型向量化查询: {e}")
            
            # 2. 在visual_embedding向量空间中搜索
            logger.info("在visual_embedding向量空间中搜索")
            results = self.vector_db.vector_store_manager.similarity_search_by_vector(
                query_vector=query_vector,
                k=max_results
            )
            logger.info(f"向量搜索返回 {len(results)} 个原始结果")
            
            # 3. 过滤结果：只保留visual_embedding类型且相似度达到阈值的图片
            filtered_results = []
            for result in results:
                try:
                    # 检查是否为图片类型且为visual_embedding
                    if (hasattr(result, 'metadata') and 
                        result.metadata.get('chunk_type') == 'image' and
                        result.metadata.get('vector_type') == 'visual_embedding'):
                        
                        # 获取相似度分数
                        similarity_score = result.metadata.get('similarity_score', 0.0)
                        
                        # 检查是否达到阈值
                        if similarity_score >= threshold:
                            formatted_result = {
                                'chunk_id': result.metadata.get('chunk_id', ''),
                                'content': result.page_content if hasattr(result, 'page_content') else '',
                                'content_type': 'image',
                                'similarity_score': similarity_score,
                                'strategy': 'visual_similarity',
                                'layer': 2,  # 第二层搜索
                                'metadata': result.metadata
                            }
                            filtered_results.append(formatted_result)
                            
                except Exception as e:
                    logger.warning(f"处理搜索结果时出错: {e}")
                    continue
            
            # 4. 按相似度排序并限制结果数量
            filtered_results.sort(key=lambda x: x['similarity_score'], reverse=True)
            final_results = filtered_results[:max_results]
            
            # 5. 更新统计信息
            self.retrieval_stats['visual_searches'] += 1
            self.retrieval_stats['total_results'] += len(final_results)
            
            logger.info(f"图片视觉搜索完成，找到 {len(final_results)} 个结果，最高相似度: {final_results[0]['similarity_score'] if final_results else 0.0}")
            return final_results
            
        except Exception as e:
            logger.error(f"图片视觉搜索失败: {e}")
            # 回退到语义搜索
            logger.info("回退到语义搜索")
            return self._image_semantic_search(query, max_results, threshold)

    def _image_keyword_search(self, query: str, max_results: int, threshold: float) -> List[Dict[str, Any]]:
        """图片关键词搜索"""
        try:
            # 提取图片相关关键词
            keywords = self._extract_image_keywords(query)
            if not keywords:
                return []
            
            # 使用关键词进行搜索
            results = []
            for keyword in keywords[:3]:
                keyword_results = self.vector_db.search_images(keyword, max_results // 3, threshold)
                for result in keyword_results:
                    result['strategy'] = 'keyword_matching'
                    result['layer'] = 3
                    result['keyword'] = keyword
                results.extend(keyword_results)
            
            return results
        except Exception as e:
            logger.error(f"图片关键词搜索失败: {e}")
            return []
    
    def _image_expansion_search(self, query: str, max_results: int, threshold: float) -> List[Dict[str, Any]]:
        """图片扩展搜索"""
        try:
            # 生成图片相关扩展查询
            expanded_queries = self._generate_image_expanded_queries(query)
            if not expanded_queries:
                return []
            
            # 使用扩展查询进行搜索
            results = []
            for expanded_query in expanded_queries[:2]:
                expanded_results = self.vector_db.search_images(expanded_query, max_results // 2, threshold)
                for result in expanded_results:
                    result['strategy'] = 'query_expansion'
                    result['layer'] = 4
                    result['expanded_query'] = expanded_query
                results.extend(expanded_results)
            
            return results
        except Exception as e:
            logger.error(f"图片扩展搜索失败: {e}")
            return []
    
    # 表格召回策略实现
    def _table_structure_search(self, query: str, max_results: int, threshold: float) -> List[Dict[str, Any]]:
        """表格结构搜索"""
        try:
            results = self.vector_db.search_tables(query, max_results, threshold)
            for result in results:
                result['strategy'] = 'structure_similarity'
                result['layer'] = 1
            return results
        except Exception as e:
            logger.error(f"表格结构搜索失败: {e}")
            return []
    
    def _table_semantic_search(self, query: str, max_results: int, threshold: float) -> List[Dict[str, Any]]:
        """表格语义搜索"""
        try:
            # 使用语义搜索
            results = self.vector_db.search_tables(query, max_results, threshold)
            for result in results:
                result['strategy'] = 'semantic_similarity'
                result['layer'] = 2
            return results
        except Exception as e:
            logger.error(f"表格语义搜索失败: {e}")
            return []
    
    def _table_keyword_search(self, query: str, max_results: int, threshold: float) -> List[Dict[str, Any]]:
        """表格关键词搜索"""
        try:
            # 提取表格相关关键词
            keywords = self._extract_table_keywords(query)
            if not keywords:
                return []
            
            # 使用关键词进行搜索
            results = []
            for keyword in keywords[:3]:
                keyword_results = self.vector_db.search_tables(keyword, max_results // 3, threshold)
                for result in keyword_results:
                    result['strategy'] = 'keyword_matching'
                    result['layer'] = 3
                    result['keyword'] = keyword
                results.extend(keyword_results)
            
            return results
        except Exception as e:
            logger.error(f"表格关键词搜索失败: {e}")
            return []
    
    def _table_expansion_search(self, query: str, max_results: int, threshold: float) -> List[Dict[str, Any]]:
        """表格扩展搜索"""
        try:
            # 生成表格相关扩展查询
            expanded_queries = self._generate_table_expanded_queries(query)
            if not expanded_queries:
                return []
            
            # 使用扩展查询进行搜索
            results = []
            for expanded_query in expanded_queries[:2]:
                expanded_results = self.vector_db.search_tables(expanded_query, max_results // 2, threshold)
                for result in expanded_results:
                    result['strategy'] = 'query_expansion'
                    result['layer'] = 4
                    result['expanded_query'] = expanded_query
                results.extend(expanded_results)
            
            return results
        except Exception as e:
            logger.error(f"表格扩展搜索失败: {e}")
            return []
    
    # 辅助方法
    def _deduplicate_and_sort(self, results: List[Dict[str, Any]], max_results: int) -> List[Dict[str, Any]]:
        """去重和排序"""
        try:
            # 基于chunk_id去重
            seen_ids = set()
            unique_results = []
            
            for result in results:
                chunk_id = result.get('chunk_id', '')
                if chunk_id and chunk_id not in seen_ids:
                    seen_ids.add(chunk_id)
                    unique_results.append(result)
                elif not chunk_id:
                    # 如果没有chunk_id，基于内容去重
                    content = result.get('content', '')
                    if content not in seen_ids:
                        seen_ids.add(content)
                        unique_results.append(result)
            
            # 按相似度排序
            unique_results.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
            
            # 返回前max_results个结果
            return unique_results[:max_results]
            
        except Exception as e:
            logger.error(f"去重和排序失败: {e}")
            return results[:max_results]
    
    def _extract_text_keywords(self, query: str) -> List[str]:
        """提取文本关键词"""
        try:
            # 简单的关键词提取（实际应该使用jieba等分词工具）
            words = query.split()
            # 过滤短词和常见词
            keywords = [word for word in words if len(word) > 1 and word not in ['的', '是', '在', '有', '和']]
            return keywords[:5]  # 限制关键词数量
        except Exception as e:
            logger.error(f"提取文本关键词失败: {e}")
            return []
    
    def _extract_image_keywords(self, query: str) -> List[str]:
        """提取图片关键词"""
        try:
            # 图片相关关键词提取
            image_keywords = ['图片', '图像', '照片', '图', '画', '照片', '截图']
            words = query.split()
            keywords = [word for word in words if word in image_keywords or len(word) > 1]
            return keywords[:5]
        except Exception as e:
            logger.error(f"提取图片关键词失败: {e}")
            return []
    
    def _extract_table_keywords(self, query: str) -> List[str]:
        """提取表格关键词"""
        try:
            # 表格相关关键词提取
            table_keywords = ['表格', '表', '数据', '统计', '数字', '列', '行']
            words = query.split()
            keywords = [word for word in words if word in table_keywords or len(word) > 1]
            return keywords[:5]
        except Exception as e:
            logger.error(f"提取表格关键词失败: {e}")
            return []
    
    def _generate_expanded_queries(self, query: str) -> List[str]:
        """生成扩展查询"""
        try:
            # 简单的查询扩展（实际应该使用同义词词典或LLM）
            expanded = []
            # 添加同义词
            synonyms = {
                '分析': ['分析', '研究', '探讨', '讨论'],
                '比较': ['比较', '对比', '对照', '对比分析'],
                '总结': ['总结', '概括', '归纳', '汇总']
            }
            
            for word, syns in synonyms.items():
                if word in query:
                    for syn in syns:
                        if syn != word:
                            expanded.append(query.replace(word, syn))
            
            return expanded[:3]  # 限制扩展查询数量
        except Exception as e:
            logger.error(f"生成扩展查询失败: {e}")
            return []
    
    def _generate_image_expanded_queries(self, query: str) -> List[str]:
        """生成图片扩展查询"""
        try:
            # 图片相关扩展查询
            expanded = []
            if '图片' in query:
                expanded.append(query.replace('图片', '图像'))
                expanded.append(query.replace('图片', '照片'))
            elif '图像' in query:
                expanded.append(query.replace('图像', '图片'))
            elif '照片' in query:
                expanded.append(query.replace('照片', '图片'))
            
            return expanded[:3]
        except Exception as e:
            logger.error(f"生成图片扩展查询失败: {e}")
            return []
    
    def _generate_table_expanded_queries(self, query: str) -> List[str]:
        """生成表格扩展查询"""
        try:
            # 表格相关扩展查询
            expanded = []
            if '表格' in query:
                expanded.append(query.replace('表格', '表'))
                expanded.append(query.replace('表格', '数据'))
            elif '表' in query:
                expanded.append(query.replace('表', '表格'))
            
            return expanded[:3]
        except Exception as e:
            logger.error(f"生成表格扩展查询失败: {e}")
            return []
    
    def _detect_query_type(self, query: str) -> str:
        """检测查询类型"""
        try:
            query_lower = query.lower()
            if any(word in query_lower for word in ['比较', '对比', '对照']):
                return 'comparison'
            elif any(word in query_lower for word in ['分析', '研究', '探讨']):
                return 'analysis'
            elif any(word in query_lower for word in ['搜索', '查找', '找']):
                return 'search'
            else:
                return 'general'
        except Exception as e:
            logger.error(f"检测查询类型失败: {e}")
            return 'general'
    
    def _detect_content_type(self, query: str) -> str:
        """检测内容类型"""
        try:
            query_lower = query.lower()
            if any(word in query_lower for word in ['图片', '图像', '照片', '图']):
                return 'image'
            elif any(word in query_lower for word in ['表格', '表', '数据', '统计']):
                return 'table'
            else:
                return 'text'
        except Exception as e:
            logger.error(f"检测内容类型失败: {e}")
            return 'text'
    
    def _update_stats(self, result_count: int, response_time: float):
        """更新统计信息"""
        try:
            self.retrieval_stats['total_queries'] += 1
            self.retrieval_stats['total_results'] += result_count
            self.retrieval_stats['last_query_time'] = time.time()
            
            # 计算平均响应时间
            current_avg = self.retrieval_stats['average_response_time']
            total_queries = self.retrieval_stats['total_queries']
            self.retrieval_stats['average_response_time'] = (
                (current_avg * (total_queries - 1) + response_time) / total_queries
            )
        except Exception as e:
            logger.error(f"更新统计信息失败: {e}")
    
    # 核心算法实现 - 根据改造计划要求
    def _calculate_text_relevance(self, query: str, content: str) -> float:
        """
        计算文本相关性分数 - 核心算法1
        
        :param query: 查询文本
        :param content: 内容文本
        :return: 相关性分数 (0.0-1.0)
        """
        try:
            if not query or not content:
                return 0.0
            
            # 1. 快速文本相似度（权重：0.4）
            fast_similarity = self._calculate_fast_text_similarity(query, content)
            
            # 2. 向量相似度（权重：0.6）
            vector_similarity = self._calculate_vector_similarity(query, content)
            
            # 加权计算最终相关性分数
            relevance_score = (fast_similarity * 0.4) + (vector_similarity * 0.6)
            
            # 确保分数在0.0-1.0范围内
            return max(0.0, min(1.0, relevance_score))
            
        except Exception as e:
            logger.error(f"计算文本相关性失败: {e}")
            return 0.0
    
    def _calculate_fast_text_similarity(self, query: str, content: str) -> float:
        """
        计算快速文本相似度 - 核心算法2
        
        :param query: 查询文本
        :param content: 内容文本
        :return: 相似度分数 (0.0-1.0)
        """
        try:
            if not query or not content:
                return 0.0
            
            # 使用jieba分词工具（如果可用）
            if JIEBA_AVAILABLE:
                query_words = set(jieba.lcut(query))
                content_words = set(jieba.lcut(content))
            else:
                # 备选方案：基础分词
                query_words = set(query.lower().split())
                content_words = set(content.lower().split())
            
            if not query_words or not content_words:
                return 0.0
            
            # 计算Jaccard相似度
            intersection = len(query_words.intersection(content_words))
            union = len(query_words.union(content_words))
            
            if union == 0:
                return 0.0
            
            jaccard_similarity = intersection / union
            
            # 计算词频相似度
            query_freq = {}
            content_freq = {}
            
            for word in query_words:
                query_freq[word] = query.count(word)
            
            for word in content_words:
                content_freq[word] = content.count(word)
            
            # 计算余弦相似度
            common_words = query_words.intersection(content_words)
            if not common_words:
                return jaccard_similarity
            
            numerator = sum(query_freq[word] * content_freq[word] for word in common_words)
            query_norm = sum(query_freq[word] ** 2 for word in query_words) ** 0.5
            content_norm = sum(content_freq[word] ** 2 for word in content_words) ** 0.5
            
            if query_norm == 0 or content_norm == 0:
                return jaccard_similarity
            
            cosine_similarity = numerator / (query_norm * content_norm)
            
            # 综合相似度（Jaccard + 余弦）
            combined_similarity = (jaccard_similarity + cosine_similarity) / 2
            
            return max(0.0, min(1.0, combined_similarity))
            
        except Exception as e:
            logger.error(f"计算快速文本相似度失败: {e}")
            return 0.0
    
    def _calculate_vector_similarity(self, query: str, content: str) -> float:
        """
        计算向量相似度 - 核心算法3
        
        :param query: 查询文本
        :param content: 内容文本
        :return: 相似度分数 (0.0-1.0)
        """
        try:
            if not query or not content:
                return 0.0
            
            # 使用向量数据库计算相似度
            if hasattr(self.vector_db, 'calculate_similarity'):
                # 如果向量数据库支持直接相似度计算
                return self.vector_db.calculate_similarity(query, content)
            
            # 备选方案：基于TF-IDF的相似度计算
            return self._calculate_tfidf_similarity(query, content)
            
        except Exception as e:
            logger.error(f"计算向量相似度失败: {e}")
            return 0.0
    
    def _calculate_tfidf_similarity(self, query: str, content: str) -> float:
        """
        基于TF-IDF的相似度计算（备选方案）
        
        :param query: 查询文本
        :param content: 内容文本
        :return: 相似度分数 (0.0-1.0)
        """
        try:
            # 使用jieba分词工具（如果可用）
            if JIEBA_AVAILABLE:
                query_words = jieba.lcut(query)
                content_words = jieba.lcut(content)
            else:
                # 备选方案：基础分词
                query_words = query.lower().split()
                content_words = content.lower().split()
            
            if not query_words or not content_words:
                return 0.0
            
            # 计算词频
            query_tf = {}
            content_tf = {}
            
            for word in query_words:
                query_tf[word] = query_tf.get(word, 0) + 1
            
            for word in content_words:
                content_tf[word] = content_tf.get(word, 0) + 1
            
            # 计算TF-IDF向量
            all_words = set(query_words + content_words)
            query_vector = []
            content_vector = []
            
            for word in all_words:
                query_vector.append(query_tf.get(word, 0))
                content_vector.append(content_tf.get(word, 0))
            
            # 计算余弦相似度
            numerator = sum(a * b for a, b in zip(query_vector, content_vector))
            query_norm = sum(a ** 2 for a in query_vector) ** 0.5
            content_norm = sum(b ** 2 for b in content_vector) ** 0.5
            
            if query_norm == 0 or content_norm == 0:
                return 0.0
            
            cosine_similarity = numerator / (query_norm * content_norm)
            
            return max(0.0, min(1.0, cosine_similarity))
            
        except Exception as e:
            logger.error(f"计算TF-IDF相似度失败: {e}")
            return 0.0

    def _calculate_content_similarity(self, query_features: Dict[str, Any], image_features: Dict[str, Any]) -> float:
        """
        计算内容相似度
        
        :param query_features: 查询特征
        :param image_features: 图像特征
        :return: 内容相似度分数 (0.0-1.0)
        """
        try:
            similarity_score = 0.0
            total_weight = 0.0
            
            # 1. 关键词匹配（权重：0.5）
            if 'keywords' in query_features and 'keywords' in image_features:
                keyword_similarity = self._calculate_keyword_similarity(
                    query_features['keywords'], 
                    image_features.get('keywords', [])
                )
                similarity_score += keyword_similarity * 0.5
                total_weight += 0.5
            
            # 2. 内容类型匹配（权重：0.3）
            if 'content_types' in query_features and 'content_types' in image_features:
                content_type_similarity = self._calculate_content_type_similarity(
                    query_features['content_types'],
                    image_features['content_types']
                )
                similarity_score += content_type_similarity * 0.3
                total_weight += 0.3
            
            # 3. 视觉概念匹配（权重：0.2）
            if 'visual_concepts' in query_features and 'visual_concepts' in image_features:
                visual_concept_similarity = self._calculate_visual_concept_similarity(
                    query_features['visual_concepts'],
                    image_features['visual_concepts']
                )
                similarity_score += visual_concept_similarity * 0.2
                total_weight += 0.2
            
            # 计算加权平均
            if total_weight > 0:
                return similarity_score / total_weight
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"计算内容相似度失败: {e}")
            return 0.0
    
    def _calculate_style_similarity(self, query_features: Dict[str, Any], image_features: Dict[str, Any]) -> float:
        """
        计算风格相似度
        
        :param query_features: 查询特征
        :param image_features: 图像特征
        :return: 风格相似度分数 (0.0-1.0)
        """
        try:
            similarity_score = 0.0
            total_weight = 0.0
            
            # 1. 艺术风格匹配（权重：0.6）
            if 'style_attributes' in query_features and 'style_attributes' in image_features:
                art_style_similarity = self._calculate_art_style_similarity(
                    query_features['style_attributes'],
                    image_features['style_attributes']
                )
                similarity_score += art_style_similarity * 0.6
                total_weight += 0.6
            
            # 2. 摄影风格匹配（权重：0.4）
            if 'style_attributes' in query_features and 'style_attributes' in image_features:
                photo_style_similarity = self._calculate_photo_style_similarity(
                    query_features['style_attributes'],
                    image_features['style_attributes']
                )
                similarity_score += photo_style_similarity * 0.4
                total_weight += 0.4
            
            # 计算加权平均
            if total_weight > 0:
                return similarity_score / total_weight
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"计算风格相似度失败: {e}")
            return 0.0
    
    def _calculate_semantic_similarity(self, query_features: Dict[str, Any], image_features: Dict[str, Any]) -> float:
        """
        计算语义相似度
        
        :param query_features: 查询特征
        :param image_features: 图像特征
        :return: 语义相似度分数 (0.0-1.0)
        """
        try:
            # 使用特征向量计算余弦相似度
            if 'feature_vector' in query_features and 'feature_vector' in image_features:
                query_vector = query_features['feature_vector']
                image_vector = image_features['feature_vector']
                
                if len(query_vector) == len(image_vector) and len(query_vector) > 0:
                    return self._cosine_similarity(query_vector, image_vector)
            
            # 备选方案：基于关键词的语义相似度
            if 'keywords' in query_features and 'keywords' in image_features:
                return self._calculate_keyword_similarity(
                    query_features['keywords'],
                    image_features['keywords']
                )
            
            return 0.0
            
        except Exception as e:
            logger.error(f"计算语义相似度失败: {e}")
            return 0.0
    
    def _calculate_keyword_similarity(self, query_keywords: List[Dict], image_keywords: List[Dict]) -> float:
        """
        计算关键词相似度
        
        :param query_keywords: 查询关键词列表
        :param image_keywords: 图像关键词列表
        :return: 关键词相似度分数 (0.0-1.0)
        """
        try:
            if not query_keywords or not image_keywords:
                return 0.0
            
            # 提取关键词文本
            query_words = set(kw['word'] for kw in query_keywords)
            image_words = set(kw['word'] for kw in image_keywords)
            
            if not query_words or not image_words:
                return 0.0
            
            # 计算Jaccard相似度
            intersection = len(query_words.intersection(image_words))
            union = len(query_words.union(image_words))
            
            if union == 0:
                return 0.0
            
            return intersection / union
            
        except Exception as e:
            logger.error(f"计算关键词相似度失败: {e}")
            return 0.0
    
    def _calculate_content_type_similarity(self, query_types: List[Dict], image_types: List[Dict]) -> float:
        """
        计算内容类型相似度
        
        :param query_types: 查询内容类型列表
        :param image_types: 图像内容类型列表
        :return: 内容类型相似度分数 (0.0-1.0)
        """
        try:
            if not query_types or not image_types:
                return 0.0
            
            # 提取类型名称
            query_type_names = set(ct.get('name', '') for ct in query_types)
            image_type_names = set(ct.get('name', '') for ct in image_types)
            
            if not query_type_names or not image_type_names:
                return 0.0
            
            # 计算Jaccard相似度
            intersection = len(query_type_names.intersection(image_type_names))
            union = len(query_type_names.union(image_type_names))
            
            if union == 0:
                return 0.0
            
            return intersection / union
            
        except Exception as e:
            logger.error(f"计算内容类型相似度失败: {e}")
            return 0.0
    
    def _calculate_visual_concept_similarity(self, query_concepts: List[Dict], image_concepts: List[Dict]) -> float:
        """
        计算视觉概念相似度
        
        :param query_concepts: 查询视觉概念列表
        :param image_concepts: 图像视觉概念列表
        :return: 视觉概念相似度分数 (0.0-1.0)
        """
        try:
            if not query_concepts or not image_concepts:
                return 0.0
            
            # 按类型分组计算相似度
            concept_types = ['color', 'shape', 'texture']
            type_similarities = []
            
            for concept_type in concept_types:
                query_type_concepts = [c for c in query_concepts if c.get('type') == concept_type]
                image_type_concepts = [c for c in image_concepts if c.get('type') == concept_type]
                
                if query_type_concepts and image_type_concepts:
                    # 计算该类型的相似度
                    type_similarity = self._calculate_concept_type_similarity(
                        query_type_concepts, image_type_concepts
                    )
                    type_similarities.append(type_similarity)
            
            # 计算平均相似度
            if type_similarities:
                return sum(type_similarities) / len(type_similarities)
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"计算视觉概念相似度失败: {e}")
            return 0.0
    
    def _calculate_concept_type_similarity(self, query_concepts: List[Dict], image_concepts: List[Dict]) -> float:
        """
        计算特定类型概念的相似度
        
        :param query_concepts: 查询概念列表
        :param image_concepts: 图像概念列表
        :return: 概念相似度分数 (0.0-1.0)
        """
        try:
            if not query_concepts or not image_concepts:
                return 0.0
            
            # 提取概念名称
            query_names = set(c.get('name', '') for c in query_concepts)
            image_names = set(c.get('name', '') for c in image_concepts)
            
            if not query_names or not image_names:
                return 0.0
            
            # 计算Jaccard相似度
            intersection = len(query_names.intersection(image_names))
            union = len(query_names.union(image_names))
            
            if union == 0:
                return 0.0
            
            return intersection / union
            
        except Exception as e:
            logger.error(f"计算概念类型相似度失败: {e}")
            return 0.0
    
    def _calculate_art_style_similarity(self, query_styles: List[Dict], image_styles: List[Dict]) -> float:
        """
        计算艺术风格相似度
        
        :param query_styles: 查询风格列表
        :param image_styles: 图像风格列表
        :return: 艺术风格相似度分数 (0.0-1.0)
        """
        try:
            # 筛选艺术风格
            query_art_styles = [s for s in query_styles if s.get('type') == 'art_style']
            image_art_styles = [s for s in image_styles if s.get('type') == 'art_style']
            
            if not query_art_styles or not image_art_styles:
                return 0.0
            
            # 提取风格名称
            query_names = set(s.get('name', '') for s in query_art_styles)
            image_names = set(s.get('name', '') for s in image_art_styles)
            
            # 计算Jaccard相似度
            intersection = len(query_names.intersection(image_names))
            union = len(query_names.union(image_names))
            
            if union == 0:
                return 0.0
            
            return intersection / union
            
        except Exception as e:
            logger.error(f"计算艺术风格相似度失败: {e}")
            return 0.0
    
    def _calculate_photo_style_similarity(self, query_styles: List[Dict], image_styles: List[Dict]) -> float:
        """
        计算摄影风格相似度
        
        :param query_styles: 查询风格列表
        :param image_styles: 图像风格列表
        :return: 摄影风格相似度分数 (0.0-1.0)
        """
        try:
            # 筛选摄影风格
            query_photo_styles = [s for s in query_styles if s.get('type') == 'photo_style']
            image_photo_styles = [s for s in image_styles if s.get('type') == 'photo_style']
            
            if not query_photo_styles or not image_photo_styles:
                return 0.0
            
            # 提取风格名称
            query_names = set(s.get('name', '') for s in query_photo_styles)
            image_names = set(s.get('name', '') for s in image_photo_styles)
            
            # 计算Jaccard相似度
            intersection = len(query_names.intersection(image_names))
            union = len(query_names.union(image_names))
            
            if union == 0:
                return 0.0
            
            return intersection / union
            
        except Exception as e:
            logger.error(f"计算摄影风格相似度失败: {e}")
            return 0.0
    
    def _cosine_similarity(self, vector1: List[float], vector2: List[float]) -> float:
        """
        计算两个向量的余弦相似度
        
        :param vector1: 向量1
        :param vector2: 向量2
        :return: 余弦相似度分数 (-1.0-1.0)
        """
        try:
            if len(vector1) != len(vector2):
                return 0.0
            
            # 计算点积
            dot_product = sum(a * b for a, b in zip(vector1, vector2))
            
            # 计算向量模长
            norm1 = sum(a * a for a in vector1) ** 0.5
            norm2 = sum(b * b for b in vector2) ** 0.5
            
            # 避免除零错误
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # 计算余弦相似度
            cosine_sim = dot_product / (norm1 * norm2)
            
            # 将余弦相似度从[-1,1]映射到[0,1]
            return (cosine_sim + 1) / 2
            
        except Exception as e:
            logger.error(f"计算余弦相似度失败: {e}")
            return 0.0
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """获取召回统计信息"""
        return self.retrieval_stats.copy()
    
    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态信息"""
        return {
            'status': 'ready',
            'service_type': 'RAG Retrieval Engine',
            'retrieval_stats': self.retrieval_stats,
            'features': [
                'text_retrieval',
                'image_retrieval',
                'table_retrieval',
                'hybrid_retrieval',
                'smart_retrieval',
                'multi_layer_strategy'
            ],
            'strategies': {
                'text': ['vector_similarity', 'keyword_matching', 'query_expansion'],
                'image': ['semantic_similarity', 'visual_similarity', 'keyword_matching', 'query_expansion'],
                'table': ['structure_similarity', 'semantic_similarity', 'keyword_matching', 'query_expansion']
            }
        }

    def _enhance_cross_type_relevance(self, text_results: List[Dict], 
                                    image_results: List[Dict], 
                                    table_results: List[Dict], 
                                    query: str, 
                                    cross_type_boost: float) -> List[Dict]:
        """
        增强跨类型内容相关性
        
        :param text_results: 文本搜索结果
        :param image_results: 图片搜索结果
        :param table_results: 表格搜索结果
        :param query: 查询文本
        :param cross_type_boost: 跨类型提升系数
        :return: 增强后的结果列表
        """
        try:
            enhanced_results = []
            
            # 1. 处理文本结果
            for result in text_results:
                if result is None:
                    continue
                enhanced_result = result.copy()
                enhanced_result['cross_type_score'] = self._calculate_cross_type_relevance(
                    result, image_results + table_results, query
                )
                enhanced_result['final_score'] = result.get('similarity_score', 0.0) + \
                                               enhanced_result['cross_type_score'] * cross_type_boost
                enhanced_results.append(enhanced_result)
            
            # 2. 处理图片结果
            for result in image_results:
                if result is None:
                    continue
                enhanced_result = result.copy()
                enhanced_result['cross_type_score'] = self._calculate_cross_type_relevance(
                    result, text_results + table_results, query
                )
                enhanced_result['final_score'] = result.get('similarity_score', 0.0) + \
                                               enhanced_result['cross_type_score'] * cross_type_boost
                enhanced_results.append(enhanced_result)
            
            # 3. 处理表格结果
            for result in table_results:
                if result is None:
                    continue
                enhanced_result = result.copy()
                enhanced_result['cross_type_score'] = self._calculate_cross_type_relevance(
                    result, text_results + image_results, query
                )
                enhanced_result['final_score'] = result.get('similarity_score', 0.0) + \
                                               enhanced_result['cross_type_score'] * cross_type_boost
                enhanced_results.append(enhanced_result)
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"增强跨类型相关性失败: {e}")
            return text_results + image_results + table_results
    
    def _calculate_cross_type_relevance(self, current_result: Dict, 
                                      other_results: List[Dict], 
                                      query: str) -> float:
        """
        计算跨类型内容相关性分数
        
        :param current_result: 当前结果
        :param other_results: 其他类型结果列表
        :param query: 查询文本
        :return: 跨类型相关性分数
        """
        try:
            if not other_results:
                return 0.0
            
            cross_type_scores = []
            current_content = current_result.get('content', '')
            current_metadata = current_result.get('metadata', {})
            
            for other_result in other_results:

                other_content = other_result.get('content', '')
                other_metadata = other_result.get('metadata', {})
                
                # 计算内容相似度
                content_similarity = self._calculate_cross_content_similarity(
                    current_content, other_content, current_metadata, other_metadata
                )
                
                # 计算查询相关性
                query_relevance = self._calculate_query_relevance_for_cross_type(
                    query, current_result, other_result
                )
                
                # 综合分数
                cross_score = (content_similarity * 0.6) + (query_relevance * 0.4)
                cross_type_scores.append(cross_score)
            
            # 返回最高分数
            return max(cross_type_scores) if cross_type_scores else 0.0
            
        except Exception as e:
            logger.error(f"计算跨类型相关性失败: {e}")
            return 0.0
    
    def _calculate_cross_content_similarity(self, content1: str, content2: str, 
                                          metadata1: Dict, metadata2: Dict) -> float:
        """
        计算跨类型内容相似度
        
        :param content1: 内容1
        :param content2: 内容2
        :param metadata1: 元数据1
        :param metadata2: 元数据2
        :return: 相似度分数
        """
        try:
            # 1. 文本内容相似度
            text_similarity = self._calculate_text_similarity(content1, content2)
            
            # 2. 元数据相似度
            metadata_similarity = self._calculate_metadata_similarity(metadata1, metadata2)
            
            # 3. 关键词相似度
            keywords1 = self._extract_keywords_from_content(content1)
            keywords2 = self._extract_keywords_from_content(content2)
            keyword_similarity = self._calculate_keyword_set_similarity(keywords1, keywords2)
            
            # 加权计算
            final_similarity = (
                text_similarity * 0.4 +
                metadata_similarity * 0.3 +
                keyword_similarity * 0.3
            )
            
            return final_similarity
            
        except Exception as e:
            logger.error(f"计算跨内容相似度失败: {e}")
            return 0.0
    
    def _calculate_metadata_similarity(self, metadata1: Dict, metadata2: Dict) -> float:
        """
        计算元数据相似度
        
        :param metadata1: 元数据1
        :param metadata2: 元数据2
        :return: 相似度分数
        """
        try:
            if not metadata1 or not metadata2:
                return 0.0
            
            # 提取可比较的字段
            comparable_fields = ['title', 'description', 'keywords', 'tags', 'category']
            similarities = []
            
            for field in comparable_fields:
                value1 = metadata1.get(field, '')
                value2 = metadata2.get(field, '')
                
                if value1 and value2:
                    if isinstance(value1, str) and isinstance(value2, str):
                        field_similarity = self._calculate_text_similarity(value1, value2)
                        similarities.append(field_similarity)
                    elif isinstance(value1, list) and isinstance(value2, list):
                        field_similarity = self._calculate_list_similarity(value1, value2)
                        similarities.append(field_similarity)
            
            # 返回平均相似度
            return sum(similarities) / len(similarities) if similarities else 0.0
            
        except Exception as e:
            logger.error(f"计算元数据相似度失败: {e}")
            return 0.0
    
    def _calculate_list_similarity(self, list1: List, list2: List) -> float:
        """
        计算列表相似度
        
        :param list1: 列表1
        :param list2: 列表2
        :return: 相似度分数
        """
        try:
            if not list1 or not list2:
                return 0.0
            
            # 转换为集合计算Jaccard相似度
            set1 = set(str(item) for item in list1)
            set2 = set(str(item) for item in list2)
            
            intersection = len(set1.intersection(set2))
            union = len(set1.union(set2))
            
            if union == 0:
                return 0.0
            
            return intersection / union
            
        except Exception as e:
            logger.error(f"计算列表相似度失败: {e}")
            return 0.0
    
    def _extract_keywords_from_content(self, content: str) -> List[str]:
        """
        从内容中提取关键词
        
        :param content: 内容文本
        :return: 关键词列表
        """
        try:
            if JIEBA_AVAILABLE:
                # 使用jieba提取关键词
                keywords = jieba.analyse.extract_tags(content, topK=20)
                return keywords
            else:
                # 基础分词
                words = content.split()
                # 过滤短词和常见词
                stop_words = {'的', '是', '在', '有', '和', '与', '或', '但', '而', '了', '着', '过'}
                keywords = [word for word in words if len(word) > 1 and word not in stop_words]
                return keywords[:20]
                
        except Exception as e:
            logger.error(f"提取关键词失败: {e}")
            return []
    
    def _calculate_keyword_set_similarity(self, keywords1: List[str], keywords2: List[str]) -> float:
        """
        计算关键词集合相似度
        
        :param keywords1: 关键词集合1
        :param keywords2: 关键词集合2
        :return: 相似度分数
        """
        try:
            if not keywords1 or not keywords2:
                return 0.0
            
            # 转换为集合
            set1 = set(keywords1)
            set2 = set(keywords2)
            
            # 计算Jaccard相似度
            intersection = len(set1.intersection(set2))
            union = len(set1.union(set2))
            
            if union == 0:
                return 0.0
            
            return intersection / union
            
        except Exception as e:
            logger.error(f"计算关键词集合相似度失败: {e}")
            return 0.0
    
    def _calculate_query_relevance_for_cross_type(self, query: str, 
                                                result1: Dict, 
                                                result2: Dict) -> float:
        """
        计算查询与跨类型结果的相关性
        
        :param query: 查询文本
        :param result1: 结果1
        :param result2: 结果2
        :return: 相关性分数
        """
        try:
            # 计算查询与两个结果的相关性
            relevance1 = self._calculate_query_relevance(query, result1)
            relevance2 = self._calculate_query_relevance(query, result2)
            
            # 返回平均相关性
            return (relevance1 + relevance2) / 2
            
        except Exception as e:
            logger.error(f"计算跨类型查询相关性失败: {e}")
            return 0.0
    
    def _calculate_query_relevance(self, query: str, result: Dict) -> float:
        """
        计算查询与结果的相关性
        
        :param query: 查询文本
        :param result: 结果
        :return: 相关性分数
        """
        try:
            content = result.get('content', '')
            if not content:
                return 0.0
            
            # 使用文本相似度计算
            return self._calculate_text_similarity(query, content)
            
        except Exception as e:
            logger.error(f"计算查询相关性失败: {e}")
            return 0.0
    
    def _fuse_hybrid_results(self, enhanced_results: List[Dict], 
                            query: str, 
                            max_results: int) -> List[Dict]:
        """
        智能融合混合搜索结果
        
        :param enhanced_results: 增强后的结果列表
        :param query: 查询文本
        :param max_results: 最大结果数量
        :return: 融合后的结果列表
        """
        try:
            if not enhanced_results:
                return []
            
            # 1. 按最终分数排序
            sorted_results = sorted(enhanced_results, 
                                  key=lambda x: x.get('final_score', 0.0), 
                                  reverse=True)
            
            # 2. 应用多样性策略
            diverse_results = self._apply_diversity_strategy(sorted_results, max_results)
            
            # 3. 应用内容类型平衡策略
            balanced_results = self._apply_content_type_balance(diverse_results, max_results)
            
            return balanced_results
            
        except Exception as e:
            logger.error(f"融合混合搜索结果失败: {e}")
            return enhanced_results[:max_results]
    
    def _apply_diversity_strategy(self, results: List[Dict], max_results: int) -> List[Dict]:
        """
        应用多样性策略
        
        :param results: 结果列表
        :param max_results: 最大结果数量
        :return: 多样性结果列表
        """
        try:
            if len(results) <= max_results:
                return results
            
            diverse_results = []
            seen_content_types = set()
            seen_keywords = set()
            
            for result in results:
                if len(diverse_results) >= max_results:
                    break
                
                content_type = result.get('content_type', 'unknown')
                content = result.get('content', '')
                
                # 检查内容类型多样性
                if content_type not in seen_content_types:
                    diverse_results.append(result)
                    seen_content_types.add(content_type)
                    continue
                
                # 检查关键词多样性
                keywords = self._extract_keywords_from_content(content)
                new_keywords = [kw for kw in keywords if kw not in seen_keywords]
                
                if new_keywords:
                    diverse_results.append(result)
                    seen_keywords.update(new_keywords)
                    continue
                
                # 如果都没有新的多样性，检查分数
                if len(diverse_results) < max_results * 0.8:  # 保留20%给高分结果
                    diverse_results.append(result)
            
            return diverse_results
            
        except Exception as e:
            logger.error(f"应用多样性策略失败: {e}")
            return results[:max_results]
    
    def _apply_content_type_balance(self, results: List[Dict], max_results: int) -> List[Dict]:
        """
        应用内容类型平衡策略
        
        :param results: 结果列表
        :param max_results: 最大结果数量
        :return: 平衡后的结果列表
        """
        try:
            if len(results) <= max_results:
                return results
            
            # 统计各类型数量
            type_counts = {}
            for result in results:
                content_type = result.get('content_type', 'unknown')
                type_counts[content_type] = type_counts.get(content_type, 0) + 1
            
            # 计算理想分布
            total_results = len(results)
            ideal_distribution = {
                'text': int(max_results * 0.4),
                'image': int(max_results * 0.3),
                'table': int(max_results * 0.3)
            }
            
            # 重新平衡结果
            balanced_results = []
            type_used = {k: 0 for k in ideal_distribution.keys()}
            
            for result in results:
                if len(balanced_results) >= max_results:
                    break
                
                content_type = result.get('content_type', 'unknown')
                if content_type in ideal_distribution:
                    if type_used[content_type] < ideal_distribution[content_type]:
                        balanced_results.append(result)
                        type_used[content_type] += 1
                        continue
                
                # 如果某个类型已满，检查其他类型
                for other_type, limit in ideal_distribution.items():
                    if type_used[other_type] < limit:
                        balanced_results.append(result)
                        type_used[other_type] += 1
                        break
            
            return balanced_results
            
        except Exception as e:
            logger.error(f"应用内容类型平衡策略失败: {e}")
            return results[:max_results]
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的相似度
        
        :param text1: 文本1
        :param text2: 文本2
        :return: 相似度分数 (0.0-1.0)
        """
        try:
            if not text1 or not text2:
                return 0.0
            
            # 使用jieba分词工具（如果可用）
            if JIEBA_AVAILABLE:
                words1 = set(jieba.lcut(text1))
                words2 = set(jieba.lcut(text2))
            else:
                # 备选方案：基础分词
                words1 = set(text1.lower().split())
                words2 = set(text2.lower().split())
            
            if not words1 or not words2:
                return 0.0
            
            # 计算Jaccard相似度
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            
            if union == 0:
                return 0.0
            
            jaccard_similarity = intersection / union
            
            # 计算词频相似度
            freq1 = {}
            freq2 = {}
            
            for word in words1:
                freq1[word] = text1.count(word)
            
            for word in words2:
                freq2[word] = text2.count(word)
            
            # 计算余弦相似度
            common_words = words1.intersection(words2)
            if not common_words:
                return jaccard_similarity
            
            numerator = sum(freq1[word] * freq2[word] for word in common_words)
            norm1 = sum(freq1[word] ** 2 for word in words1) ** 0.5
            norm2 = sum(freq2[word] ** 2 for word in words2) ** 0.5
            
            if norm1 == 0 or norm2 == 0:
                return jaccard_similarity
            
            cosine_similarity = numerator / (norm1 * norm2)
            
            # 综合相似度（Jaccard + 余弦）
            combined_similarity = (jaccard_similarity + cosine_similarity) / 2
            
            return max(0.0, min(1.0, combined_similarity))
            
        except Exception as e:
            logger.error(f"计算文本相似度失败: {e}")
            return 0.0
    
    def retrieve_batch(self, queries: List[str], max_results: int = 25) -> List[List[Dict[str, Any]]]:
        """
        批量召回 - 性能优化版本
        
        :param queries: 查询列表
        :param max_results: 每个查询的最大结果数量
        :return: 每个查询的召回结果列表
        """
        start_time = time.time()
        try:
            if not queries:
                return []
            
            # 获取批处理配置
            batch_config = self.config.get('rag_system.performance.batch_processing', {})
            batch_size = batch_config.get('batch_size', 10)
            use_parallel = batch_config.get('use_parallel', True)
            max_workers = batch_config.get('max_workers', 4)
            
            # 分批处理
            if len(queries) <= batch_size:
                # 小批量直接处理
                results = self._process_batch_direct(queries, max_results)
            else:
                # 大批量分批处理
                results = self._process_batch_in_chunks(queries, max_results, batch_size, use_parallel, max_workers)
            
            # 更新统计信息
            total_results = sum(len(r) for r in results)
            self._update_stats(total_results, time.time() - start_time)
            
            logger.info(f"批量召回完成，查询数量: {len(queries)}，总结果数: {total_results}")
            return results
            
        except Exception as e:
            logger.error(f"批量召回失败: {e}")
            return [[] for _ in queries]
    
    def _process_batch_direct(self, queries: List[str], max_results: int) -> List[List[Dict[str, Any]]]:
        """
        直接处理小批量查询
        
        :param queries: 查询列表
        :param max_results: 最大结果数量
        :return: 结果列表
        """
        try:
            results = []
            for query in queries:
                # 使用混合召回
                query_results = self.retrieve_hybrid(query, max_results)
                results.append(query_results)
            return results
            
        except Exception as e:
            logger.error(f"直接批处理失败: {e}")
            return [[] for _ in queries]
    
    def _process_batch_in_chunks(self, queries: List[str], max_results: int, 
                                batch_size: int, use_parallel: bool, 
                                max_workers: int) -> List[List[Dict[str, Any]]]:
        """
        分批处理大量查询
        
        :param queries: 查询列表
        :param max_results: 最大结果数量
        :param batch_size: 批次大小
        :param use_parallel: 是否使用并行处理
        :param max_workers: 最大工作线程数
        :return: 结果列表
        """
        try:
            results = []
            
            if use_parallel and len(queries) > batch_size:
                # 并行处理
                import concurrent.futures
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # 提交所有任务
                    future_to_query = {
                        executor.submit(self.retrieve_hybrid, query, max_results): i 
                        for i, query in enumerate(queries)
                    }
                    
                    # 收集结果
                    temp_results = [None] * len(queries)
                    for future in concurrent.futures.as_completed(future_to_query):
                        query_index = future_to_query[future]
                        try:
                            temp_results[query_index] = future.result()
                        except Exception as e:
                            logger.error(f"并行处理查询 {query_index} 失败: {e}")
                            temp_results[query_index] = []
                    
                    results = temp_results
            else:
                # 串行处理
                for i in range(0, len(queries), batch_size):
                    batch_queries = queries[i:i + batch_size]
                    batch_results = self._process_batch_direct(batch_queries, max_results)
                    results.extend(batch_results)
            
            return results
            
        except Exception as e:
            logger.error(f"分批处理失败: {e}")
            return [[] for _ in queries]
    
    def retrieve_with_cache(self, query: str, max_results: int = 25, 
                           use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        带缓存的召回 - 性能优化版本
        
        :param query: 查询文本
        :param max_results: 最大结果数量
        :param use_cache: 是否使用缓存
        :return: 召回结果列表
        """
        start_time = time.time()
        try:
            if not use_cache:
                return self.retrieve_hybrid(query, max_results)
            
            # 获取缓存配置
            cache_config = self.config.get('rag_system.performance.caching', {})
            cache_ttl = cache_config.get('cache_ttl', 3600)  # 1小时
            max_cache_size = cache_config.get('max_cache_size', 1000)
            
            # 生成缓存键
            cache_key = self._generate_cache_key(query, max_results)
            
            # 检查缓存
            cached_result = self._get_cached_result(cache_key)
            if cached_result is not None:
                logger.info(f"缓存命中: {query}")
                return cached_result
            
            # 执行召回
            results = self.retrieve_hybrid(query, max_results)
            
            # 缓存结果
            self._cache_result(cache_key, results, cache_ttl, max_cache_size)
            
            # 更新统计信息
            self._update_stats(len(results), time.time() - start_time)
            
            return results
            
        except Exception as e:
            logger.error(f"缓存召回失败: {e}")
            return self.retrieve_hybrid(query, max_results)
    
    def _generate_cache_key(self, query: str, max_results: int) -> str:
        """
        生成缓存键
        
        :param query: 查询文本
        :param max_results: 最大结果数量
        :return: 缓存键
        """
        try:
            import hashlib
            # 生成查询的哈希值
            query_hash = hashlib.md5(query.encode('utf-8')).hexdigest()
            return f"retrieval_{query_hash}_{max_results}"
        except Exception as e:
            logger.error(f"生成缓存键失败: {e}")
            return f"retrieval_{query}_{max_results}"
    
    def _get_cached_result(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """
        获取缓存结果
        
        :param cache_key: 缓存键
        :return: 缓存的结果或None
        """
        try:
            if not hasattr(self, '_cache'):
                self._cache = {}
            
            if cache_key in self._cache:
                cache_entry = self._cache[cache_key]
                # 检查是否过期
                if time.time() < cache_entry['expires_at']:
                    return cache_entry['data']
                else:
                    # 删除过期缓存
                    del self._cache[cache_key]
            
            return None
            
        except Exception as e:
            logger.error(f"获取缓存结果失败: {e}")
            return None
    
    def _cache_result(self, cache_key: str, data: List[Dict[str, Any]], 
                     ttl: int, max_size: int):
        """
        缓存结果
        
        :param cache_key: 缓存键
        :param data: 要缓存的数据
        :param ttl: 生存时间（秒）
        :param max_size: 最大缓存大小
        """
        try:
            if not hasattr(self, '_cache'):
                self._cache = {}
            
            # 检查缓存大小
            if len(self._cache) >= max_size:
                # 清理最旧的缓存
                self._cleanup_cache()
            
            # 添加新缓存
            self._cache[cache_key] = {
                'data': data,
                'expires_at': time.time() + ttl,
                'created_at': time.time()
            }
            
        except Exception as e:
            logger.error(f"缓存结果失败: {e}")
    
    def _cleanup_cache(self):
        """清理过期和旧的缓存"""
        try:
            if not hasattr(self, '_cache'):
                return
            
            current_time = time.time()
            
            # 删除过期缓存
            expired_keys = [
                key for key, entry in self._cache.items()
                if current_time >= entry['expires_at']
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            # 如果仍然超过最大大小，删除最旧的缓存
            if len(self._cache) > 1000:  # 硬限制
                sorted_cache = sorted(
                    self._cache.items(),
                    key=lambda x: x[1]['created_at']
                )
                
                # 删除最旧的20%
                to_delete = int(len(sorted_cache) * 0.2)
                for key, _ in sorted_cache[:to_delete]:
                    del self._cache[key]
                    
        except Exception as e:
            logger.error(f"清理缓存失败: {e}")
    
    def warm_up_cache(self, common_queries: List[str], max_results: int = 25):
        """
        预热缓存
        
        :param common_queries: 常见查询列表
        :param max_results: 最大结果数量
        """
        try:
            logger.info(f"开始预热缓存，查询数量: {len(common_queries)}")
            
            # 批量预热
            warm_up_results = self.retrieve_batch(common_queries, max_results)
            
            # 统计预热结果
            total_results = sum(len(r) for r in warm_up_results)
            logger.info(f"缓存预热完成，总结果数: {total_results}")
            
        except Exception as e:
            logger.error(f"缓存预热失败: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计信息
        
        :return: 性能统计字典
        """
        try:
            stats = {
                'retrieval_stats': self.retrieval_stats.copy(),
                'cache_stats': self._get_cache_stats(),
                'performance_metrics': self._get_performance_metrics()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取性能统计失败: {e}")
            return {}
    
    def _get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            if not hasattr(self, '_cache'):
                return {'cache_size': 0, 'hit_rate': 0.0}
            
            cache_size = len(self._cache)
            # 这里可以添加更详细的缓存统计
            return {
                'cache_size': cache_size,
                'hit_rate': 0.0  # 可以扩展为实际的命中率统计
            }
            
        except Exception as e:
            logger.error(f"获取缓存统计失败: {e}")
            return {'cache_size': 0, 'hit_rate': 0.0}
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        try:
            # 这里可以添加更多性能指标
            return {
                'average_response_time': self.retrieval_stats.get('average_response_time', 0.0),
                'total_queries': self.retrieval_stats.get('total_queries', 0),
                'total_results': self.retrieval_stats.get('total_results', 0)
            }
            
        except Exception as e:
            logger.error(f"获取性能指标失败: {e}")
            return {}
