"""
RAG向量数据库集成模块

RAG系统的向量数据库集成模块，负责与V3向量数据库的交互
为RAG系统提供统一的向量存储访问接口
"""

import logging
from typing import Dict, List, Optional, Any
from db_system.core.vector_store_manager import LangChainVectorStoreManager
from db_system.core.metadata_manager import MetadataManager

logger = logging.getLogger(__name__)


class VectorDBIntegration:
    """向量数据库集成管理器"""
    
    def __init__(self, config_integration):
        """
        初始化RAG向量数据库集成管理器
        
        :param config_integration: RAG配置集成管理器实例
        """
        self.config = config_integration
        self.vector_store_manager = LangChainVectorStoreManager(self.config.config_manager)
        self.metadata_manager = MetadataManager(self.config.config_manager)
        logger.info("RAG向量数据库集成管理器初始化完成")
    
    def search_texts(self, query: str, k: int = 10, 
                    similarity_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        搜索文本内容
        
        :param query: 查询文本
        :param k: 返回结果数量
        :param similarity_threshold: 相似度阈值
        :return: 搜索结果列表
        """
        try:
            logger.info(f"开始文本搜索，查询: {query[:50]}...，请求数量: {k}，阈值: {similarity_threshold}")
            
            # 使用filter_dict指定chunk_type为text
            results = self.vector_store_manager.similarity_search(
                query=query, 
                k=k, 
                filter_dict={'chunk_type': 'text'}
            )
            
            logger.info(f"向量搜索返回 {len(results)} 个原始结果")
            
            # 过滤相似度低于阈值的结果
            filtered_results = []
            for result in results:
                if hasattr(result, 'metadata') and 'similarity_score' in result.metadata:
                    if result.metadata['similarity_score'] >= similarity_threshold:
                        filtered_results.append(self._format_search_result(result))
                else:
                    # 如果没有相似度信息，默认包含
                    filtered_results.append(self._format_search_result(result))
            
            logger.info(f"文本搜索完成，查询: {query[:50]}...，过滤后结果: {len(filtered_results)}")
            return filtered_results
            
        except Exception as e:
            logger.error(f"文本检索失败: {e}")
            return []
    
    def search_images(self, query: str, k: int = 10, 
                     similarity_threshold: float = 0.3) -> List[Dict[str, Any]]:
        """
        搜索图片内容
        
        :param query: 查询文本
        :param k: 返回结果数量
        :param similarity_threshold: 相似度阈值
        :return: 搜索结果列表
        """
        try:
            logger.info(f"开始图片搜索，查询: {query[:50]}...，请求数量: {k}，阈值: {similarity_threshold}")
            
            # 使用filter_dict指定chunk_type为image，增加fetch_k确保有足够的候选结果
            results = self.vector_store_manager.similarity_search(
                query=query, 
                k=k, 
                filter_dict={'chunk_type': 'image'},
                fetch_k=k * 10  # 增加fetch_k，确保有足够的候选结果进行过滤
            )
            
            logger.info(f"向量搜索返回 {len(results)} 个原始结果")
            
            # 过滤相似度低于阈值的结果
            filtered_results = []
            for result in results:
                if hasattr(result, 'metadata') and 'similarity_score' in result.metadata:
                    if result.metadata['similarity_score'] >= similarity_threshold:
                        filtered_results.append(self._format_search_result(result))
                else:
                    # 如果没有相似度信息，默认包含
                    filtered_results.append(self._format_search_result(result))
            
            logger.info(f"图片搜索完成，查询: {query[:50]}...，过滤后结果: {len(filtered_results)}")
            return filtered_results
            
        except Exception as e:
            logger.error(f"图片检索失败: {e}")
            return []


    def search_tables(self, query: str, k: int = 10, 
                     similarity_threshold: float = 0.65) -> List[Dict[str, Any]]:
        """
        搜索表格内容
        
        :param query: 查询文本
        :param k: 返回结果数量
        :param similarity_threshold: 相似度阈值
        :return: 搜索结果列表
        """
        try:
            logger.info(f"开始表格搜索，查询: {query[:50]}...，请求数量: {k}，阈值: {similarity_threshold}")
            
            # 使用filter_dict指定chunk_type为table
            results = self.vector_store_manager.similarity_search(
                query=query, 
                k=k, 
                filter_dict={'chunk_type': 'table'}
            )
            
            logger.info(f"向量搜索返回 {len(results)} 个原始结果")
            
            # 过滤相似度低于阈值的结果
            filtered_results = []
            for result in results:
                if hasattr(result, 'metadata') and 'similarity_score' in result.metadata:
                    if result.metadata['similarity_score'] >= similarity_threshold:
                        filtered_results.append(self._format_search_result(result))
                else:
                    # 如果没有相似度信息，默认包含
                    filtered_results.append(self._format_search_result(result))
            
            logger.info(f"表格搜索完成，查询: {query[:50]}...，过滤后结果: {len(filtered_results)}")
            return filtered_results
            
        except Exception as e:
            logger.error(f"表格检索失败: {e}")
            return []
    
    def search_by_vector(self, query_vector: List[float], k: int = 10, 
                        content_type: str = None) -> List[Dict[str, Any]]:
        """
        基于向量进行搜索
        
        :param query_vector: 查询向量
        :param k: 返回结果数量
        :param content_type: 内容类型过滤
        :return: 搜索结果列表
        """
        try:
            # 使用向量搜索
            results = self.vector_store_manager.similarity_search_by_vector(
                query_vector=query_vector, 
                k=k
            )
            
            # 如果指定了内容类型，进行过滤
            if content_type:
                filtered_results = []
                for result in results:
                    if (hasattr(result, 'metadata') and 
                        'chunk_type' in result.metadata and 
                        result.metadata['chunk_type'] == content_type):
                        filtered_results.append(self._format_search_result(result))
                results = filtered_results
            
            logger.info(f"向量搜索完成，内容类型: {content_type}，返回结果: {len(results)}")
            return [self._format_search_result(result) for result in results]
            
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return []
    
    def hybrid_search(self, query: str, k: int = 15, 
                     weights: Dict[str, float] = None) -> List[Dict[str, Any]]:
        """
        混合搜索（文本+图片+表格）
        
        :param query: 查询文本
        :param k: 返回结果数量
        :param weights: 各类型权重
        :return: 搜索结果列表
        """
        try:
            logger.info(f"开始混合搜索，查询: {query[:50]}...，请求数量: {k}")
            
            if weights is None:
                weights = {'text': 0.4, 'image': 0.3, 'table': 0.3}
            
            logger.info(f"搜索权重: 文本={weights['text']}, 图片={weights['image']}, 表格={weights['table']}")
            
            # 分别搜索各类型内容
            text_results = self.search_texts(query, k=int(k * weights['text']))
            image_results = self.search_images(query, k=int(k * weights['image']))
            table_results = self.search_tables(query, k=int(k * weights['table']))
            
            logger.info(f"各类型搜索结果: 文本={len(text_results)}, 图片={len(image_results)}, 表格={len(table_results)}")
            
            # 合并结果并按相似度排序
            all_results = text_results + image_results + table_results
            all_results.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
            
            # 返回前k个结果
            final_results = all_results[:k]
            
            logger.info(f"混合搜索完成，查询: {query[:50]}...，最终结果: {len(final_results)}")
            return final_results
            
        except Exception as e:
            logger.error(f"混合搜索失败: {e}")
            return []
    
    def _format_search_result(self, result) -> Dict[str, Any]:
        """
        格式化搜索结果
        
        :param result: 原始搜索结果
        :return: 格式化后的结果
        """
        try:
            # 提取基本信息
            # 对于图片，优先使用enhanced_description作为内容
            # 对于文本，优先使用metadata中的text字段作为内容
            # 对于表格，优先使用metadata中的table_content字段作为内容
            content = getattr(result, 'page_content', '')
            if hasattr(result, 'metadata') and result.metadata:
                chunk_type = result.metadata.get('chunk_type', '')
                if chunk_type == 'image' and 'enhanced_description' in result.metadata:
                    content = result.metadata['enhanced_description']
                elif chunk_type == 'text' and 'text' in result.metadata:
                    content = result.metadata['text']
                elif chunk_type == 'table' and 'table_content' in result.metadata:
                    content = result.metadata['table_content']
            
            formatted_result = {
                'chunk_id': getattr(result, 'id', ''),
                'content': content,
                'similarity_score': 0.0,
                'relevance_score': 0.0,  # 添加relevance_score字段
                'chunk_type': 'unknown',
                'document_name': '',
                'page_number': 0,
                'description': '',
                'image_url': '',
                'table_data': None
            }
            
            # 提取元数据
            if hasattr(result, 'metadata') and result.metadata:
                metadata = result.metadata
                
                # 相似度分数
                if 'similarity_score' in metadata:
                    formatted_result['similarity_score'] = float(metadata['similarity_score'])
                    formatted_result['relevance_score'] = float(metadata['similarity_score'])  # 同时设置relevance_score
                elif 'score' in metadata:
                    formatted_result['similarity_score'] = float(metadata['score'])
                    formatted_result['relevance_score'] = float(metadata['score'])  # 同时设置relevance_score
                
                # 内容类型
                if 'chunk_type' in metadata:
                    formatted_result['chunk_type'] = metadata['chunk_type']
                
                # 文档信息
                if 'document_name' in metadata:
                    formatted_result['document_name'] = metadata['document_name']
                if 'page_number' in metadata:
                    formatted_result['page_number'] = int(metadata['page_number'])
                
                # 图片描述
                if 'enhanced_description' in metadata:
                    formatted_result['description'] = metadata['enhanced_description']
                elif 'description' in metadata:
                    formatted_result['description'] = metadata['description']
                
                # 图片URL
                if 'image_path' in metadata:
                    formatted_result['image_url'] = metadata['image_path']
                
                # 表格数据
                if 'table_data' in metadata:
                    formatted_result['table_data'] = metadata['table_data']
            
            return formatted_result
            
        except Exception as e:
            logger.error(f"格式化搜索结果失败: {e}")
            return {
                'chunk_id': '',
                'content': str(result),
                'similarity_score': 0.0,
                'chunk_type': 'unknown',
                'document_name': '',
                'page_number': 0,
                'description': '',
                'image_url': '',
                'table_data': None
            }
    
    def get_vector_db_status(self) -> Dict[str, Any]:
        """获取向量数据库状态"""
        try:
            return {
                'status': 'connected',
                'vector_store_type': 'LangChain FAISS',
                'metadata_manager_type': 'SQLite',
                'features': [
                    'text_search',
                    'image_search', 
                    'table_search',
                    'vector_search',
                    'hybrid_search'
                ],
                'search_methods': [
                    'similarity_search',
                    'similarity_search_by_vector'
                ]
            }
        except Exception as e:
            logger.error(f"获取向量数据库状态失败: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态信息"""
        return {
            'status': 'ready',
            'service_type': 'RAG Vector Database Integration',
            'vector_db_status': self.get_vector_db_status(),
            'features': [
                'text_retrieval',
                'image_retrieval',
                'table_retrieval',
                'vector_retrieval',
                'hybrid_retrieval',
                'result_formatting'
            ]
        }
