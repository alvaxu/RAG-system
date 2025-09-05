"""
RAG向量数据库集成模块

RAG系统的向量数据库集成模块，负责与V3向量数据库的交互
为RAG系统提供统一的向量存储访问接口
"""

import logging
import re
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
                # 图片展示字段
                'image_path': '',
                'caption': '',
                'image_title': '',
                # 表格展示字段
                'table_html': '',
                'table_title': '',
                'table_headers': [],
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
                
                # 图片相关字段
                if chunk_type == 'image':
                    if 'enhanced_description' in metadata:
                        formatted_result['description'] = metadata['enhanced_description']
                        formatted_result['caption'] = metadata['enhanced_description']
                    elif 'description' in metadata:
                        formatted_result['description'] = metadata['description']
                        formatted_result['caption'] = metadata['description']
                    
                    if 'image_path' in metadata:
                        formatted_result['image_path'] = metadata['image_path']
                        formatted_result['image_url'] = metadata['image_path']
                    elif 'image_url' in metadata:
                        formatted_result['image_path'] = metadata['image_url']
                        formatted_result['image_url'] = metadata['image_url']
                    
                    if 'image_title' in metadata:
                        formatted_result['image_title'] = metadata['image_title']
                    elif 'title' in metadata:
                        formatted_result['image_title'] = metadata['title']
                
                # 表格相关字段
                elif chunk_type == 'table':
                    logger.info(f"🔍 处理表格结果: chunk_id={formatted_result.get('chunk_id')}")
                    
                    # 获取原始HTML
                    if 'table_body' in metadata:
                        table_html = metadata['table_body']
                        logger.info(f"  📄 使用table_body，长度: {len(table_html)}")
                    elif 'table_html' in metadata:
                        table_html = metadata['table_html']
                        logger.info(f"  📄 使用table_html，长度: {len(table_html)}")
                    elif 'table_content' in metadata:
                        # 如果没有HTML，尝试从table_content生成简单的HTML
                        table_html = self._generate_table_html(metadata['table_content'])
                        logger.info(f"  📄 从table_content生成HTML，长度: {len(table_html)}")
                    else:
                        table_html = ""
                        logger.warning(f"  ⚠️ 没有找到表格HTML数据")
                    
                    # ✅ 验证和修复HTML
                    fixed_html = self._validate_and_fix_table_html(table_html, metadata)
                    formatted_result['table_html'] = fixed_html
                    logger.info(f"  🔧 HTML修复后长度: {len(fixed_html)}")
                    
                    if 'table_title' in metadata:
                        formatted_result['table_title'] = metadata['table_title']
                        logger.info(f"  📝 表格标题: {metadata['table_title']}")
                    elif 'title' in metadata:
                        formatted_result['table_title'] = metadata['title']
                        logger.info(f"  📝 表格标题(从title): {metadata['title']}")
                    
                    # 直接使用metadata中的表头
                    table_headers = metadata.get('table_headers', [])
                    formatted_result['table_headers'] = table_headers
                    logger.info(f"  📋 表格标题行: {table_headers}")
                    
                    if 'table_data' in metadata:
                        formatted_result['table_data'] = metadata['table_data']
                        logger.info(f"  📊 表格数据: {len(metadata['table_data']) if isinstance(metadata['table_data'], list) else 'N/A'}")
                    
                    # 检查子表信息
                    is_subtable = metadata.get('is_subtable', False)
                    if is_subtable:
                        parent_id = metadata.get('parent_table_id', '')
                        subtable_index = metadata.get('subtable_index', '')
                        logger.info(f"  🔗 子表信息: parent_id={parent_id}, subtable_index={subtable_index}")
                    else:
                        logger.info(f"  📋 主表")
            
            # 保存原始metadata到格式化结果中
            if hasattr(result, 'metadata') and result.metadata:
                formatted_result['metadata'] = result.metadata
                logger.info(f"  💾 保存metadata，包含字段: {list(result.metadata.keys())}")
            else:
                formatted_result['metadata'] = {}
                logger.info(f"  ⚠️ 没有metadata数据")
            
            return formatted_result
            
        except Exception as e:
            logger.error(f"格式化搜索结果失败: {e}")
            return {
                'chunk_id': '',
                'content': str(result),
                'similarity_score': 0.0,
                'relevance_score': 0.0,
                'chunk_type': 'unknown',
                'document_name': '',
                'page_number': 0,
                'description': '',
                'image_url': '',
                'table_data': None,
                'image_path': '',
                'caption': '',
                'image_title': '',
                'table_html': '',
                'table_title': '',
                'table_headers': []
            }
    
    def _generate_table_html(self, table_content: str) -> str:
        """
        从表格内容生成简单的HTML表格
        
        :param table_content: 表格内容文本
        :return: HTML表格字符串
        """
        try:
            if not table_content:
                return ''
            
            # 简单的表格内容解析
            lines = table_content.strip().split('\n')
            if len(lines) < 2:
                return f'<div class="table-content">{table_content}</div>'
            
            # 假设第一行是表头
            headers = lines[0].split('\t') if '\t' in lines[0] else lines[0].split('|')
            headers = [h.strip() for h in headers if h.strip()]
            
            html = '<table class="result-table">\n'
            html += '  <thead>\n    <tr>\n'
            for header in headers:
                html += f'      <th>{header}</th>\n'
            html += '    </tr>\n  </thead>\n'
            
            # 处理数据行
            html += '  <tbody>\n'
            for line in lines[1:]:
                if line.strip():
                    cells = line.split('\t') if '\t' in line else line.split('|')
                    cells = [c.strip() for c in cells if c.strip()]
                    if cells:
                        html += '    <tr>\n'
                        for cell in cells:
                            html += f'      <td>{cell}</td>\n'
                        html += '    </tr>\n'
            html += '  </tbody>\n'
            html += '</table>'
            
            return html
            
        except Exception as e:
            logger.error(f"生成表格HTML失败: {e}")
            return f'<div class="table-content">{table_content}</div>'
    
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
                'result_formatting',
                'table_merge'
            ]
        }
    
    # ==================== 表格子表合并功能 ====================
    
    def _merge_subtables_for_display(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        为前端展示合并子表HTML
        
        :param results: 重排序后的结果列表
        :return: 合并后的结果列表
        """
        try:
            logger.info(f"🔍 开始子表合并，输入结果数量: {len(results)}")
            
            # 1. 按 parent_table_id 分组子表
            subtable_groups = self._identify_subtable_groups(results)
            logger.info(f"🔍 识别到 {len(subtable_groups)} 个子表组: {list(subtable_groups.keys())}")
            
            # 2. 合并每个子表组
            merged_results = []
            processed_subtables = set()
            non_subtable_count = 0
            
            for i, result in enumerate(results):
                chunk_id = result.get('chunk_id', '')
                chunk_type = result.get('chunk_type', 'unknown')
                metadata = result.get('metadata', {})
                is_subtable = metadata.get('is_subtable', False)
                
                # 如果这个结果已经被合并过，跳过
                if chunk_id in processed_subtables:
                    continue
                
                # 检查是否是子表：如果存在parent_table_id字段，就认为是子表
                parent_id = metadata.get('parent_table_id', '')
                if parent_id:
                    logger.info(f"🔗 处理子表: chunk_id={chunk_id}, parent_id={parent_id}")
                    if parent_id in subtable_groups:
                        # 合并这个子表组
                        logger.info(f"🔄 开始合并子表组 {parent_id}，包含 {len(subtable_groups[parent_id])} 个子表")
                        merged_result = self._merge_subtable_group(subtable_groups[parent_id])
                        if merged_result:
                            logger.info(f"✅ 子表组合并成功")
                            merged_results.append(merged_result)
                            # 标记所有子表为已处理
                            for subtable in subtable_groups[parent_id]:
                                processed_subtables.add(subtable.get('chunk_id', ''))
                        else:
                            logger.warning(f"❌ 子表组合并失败")
                    else:
                        logger.warning(f"⚠️ 子表但找不到对应的组")
                else:
                    # 非子表直接添加
                    non_subtable_count += 1
                    merged_results.append(result)
            
            # 如果有非子表，只记录总数
            if non_subtable_count > 0:
                logger.info(f"➕ 处理了 {non_subtable_count} 个非子表")

            logger.info(f"✅ 子表合并完成，原始结果: {len(results)}，合并后结果: {len(merged_results)}")
            return merged_results

        except Exception as e:
            logger.error(f"❌ 子表合并失败: {e}")
            return results  # 失败时返回原始结果
    
    def _identify_subtable_groups(self, results: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        识别子表组，按parent_table_id分组
        
        :param results: 重排序结果列表
        :return: 子表组字典 {parent_table_id: [subtable_list]}
        """
        subtable_groups = {}
        
        logger.info(f"🔍 开始识别子表组，输入结果数量: {len(results)}")
        
        for i, result in enumerate(results):
            metadata = result.get('metadata', {})
            chunk_id = result.get('chunk_id', '')
            chunk_type = result.get('chunk_type', 'unknown')
            
            logger.info(f"🔍 检查结果 {i+1}: chunk_id={chunk_id}, chunk_type={chunk_type}")
            logger.info(f"🔍  metadata keys: {list(metadata.keys())}")
            logger.info(f"🔍  is_subtable: {metadata.get('is_subtable', 'NOT_FOUND')}")
            logger.info(f"🔍  parent_table_id: {metadata.get('parent_table_id', 'NOT_FOUND')}")
            logger.info(f"🔍  subtable_index: {metadata.get('subtable_index', 'NOT_FOUND')}")
            
            # 检查是否是子表：如果存在parent_table_id字段，就认为是子表
            parent_id = metadata.get('parent_table_id', '')
            if parent_id:
                if parent_id not in subtable_groups:
                    subtable_groups[parent_id] = []
                subtable_groups[parent_id].append(result)
                logger.info(f"🔍 识别到子表: parent_id={parent_id}, chunk_id={chunk_id}")
            else:
                logger.info(f"🔍 非子表: chunk_id={chunk_id}")
        
        logger.info(f"识别到 {len(subtable_groups)} 个子表组")
        return subtable_groups
    
    def _merge_subtable_group(self, subtables: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        合并一个子表组
        
        :param subtables: 子表列表
        :return: 合并后的结果，失败时返回None
        """
        try:
            if not subtables:
                return None
            
            # 按 subtable_index 排序
            subtables.sort(key=lambda x: x.get('metadata', {}).get('subtable_index', 0))
            
            # 提取所有子表的HTML内容
            subtable_htmls = []
            for subtable in subtables:
                html_content = subtable.get('metadata', {}).get('table_body', '')
                if html_content:
                    subtable_htmls.append(html_content)
            
            if not subtable_htmls:
                return None
            
            # 合并HTML（简单拼接，因为子表之间无重复）
            merged_html = self._merge_table_htmls(subtable_htmls)
            
            # 使用第一个子表的metadata，但更新HTML内容
            merged_result = dict(subtables[0])  # 复制第一个子表的所有字段
            
            # 更新关键字段
            merged_result['metadata']['table_body'] = merged_html
            merged_result['metadata']['table_html'] = merged_html
            merged_result['metadata']['is_subtable'] = False  # 标记为合并后的主表
            
            # 更新表格统计信息
            merged_result['metadata']['table_rows'] = self._count_table_rows(merged_html)
            merged_result['metadata']['table_summary'] = self._generate_merged_table_summary(merged_html)
            
            logger.info(f"成功合并子表组，包含 {len(subtables)} 个子表")
            return merged_result
            
        except Exception as e:
            logger.error(f"合并子表组失败: {e}")
            return None
    
    def _merge_table_htmls(self, html_list: List[str]) -> str:
        """
        合并多个表格HTML
        
        :param html_list: HTML列表
        :return: 合并后的HTML
        """
        try:
            if not html_list:
                return ""
            
            # 直接合并所有表格的内容
            all_rows = []
            for html in html_list:
                # 提取所有<tr>标签内容
                tr_matches = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)
                for tr_content in tr_matches:
                    all_rows.append(f"<tr>{tr_content}</tr>")
            
            # 合并HTML（不添加表头，直接合并内容）
            merged_html = f"<table><tbody>{''.join(all_rows)}</tbody></table>"
            
            return merged_html
            
        except Exception as e:
            logger.error(f"HTML合并失败: {e}")
            return html_list[0] if html_list else ""
    
    def _count_table_rows(self, html: str) -> int:
        """
        统计表格行数
        
        :param html: 表格HTML
        :return: 行数
        """
        try:
            # 统计<tr>标签数量
            tr_matches = re.findall(r'<tr[^>]*>', html, re.IGNORECASE)
            return len(tr_matches)
        except Exception as e:
            logger.warning(f"统计表格行数失败: {e}")
            return 0
    
    def _generate_merged_table_summary(self, html: str) -> str:
        """
        生成合并后的表格摘要
        
        :param html: 表格HTML
        :return: 表格摘要
        """
        try:
            rows = self._count_table_rows(html)
            
            # 提取列数
            first_row_match = re.search(r'<tr[^>]*>(.*?)</tr>', html, re.IGNORECASE | re.DOTALL)
            if first_row_match:
                first_row_html = first_row_match.group(1)
                columns = len(re.findall(r'<t[dh][^>]*>', first_row_html, re.IGNORECASE))
            else:
                columns = 0
            
            if rows == 0:
                return "空表格"
            
            return f"合并表格包含 {rows} 行 {columns} 列数据"
            
        except Exception as e:
            logger.warning(f"生成合并表格摘要失败: {e}")
            return "合并表格"
    
    
    # ==================== HTML修复功能 ====================
    
    def _validate_and_fix_table_html(self, table_html: str, metadata: Dict[str, Any]) -> str:
        """
        验证和修复表格HTML
        
        :param table_html: 表格HTML
        :param metadata: 元数据
        :return: 修复后的HTML
        """
        try:
            # 检查HTML是否为空
            if not table_html or table_html.strip() == "":
                # 从table_content生成HTML
                table_content = metadata.get('table_content', '')
                if table_content:
                    return self._generate_table_html_from_content(table_content, metadata)
                else:
                    return self._generate_empty_table_html(metadata)
            
            # 保持原始HTML结构，不添加<thead>标签
            # 原始数据使用<table><tr><td>...</td></tr></table>结构
            # 数据库中的表格已经有<tbody>标签，表头是第一行的<td>内容
            
            return table_html
            
        except Exception as e:
            logger.warning(f"表格HTML验证失败: {e}")
            return table_html
    
    def _generate_table_html_from_content(self, table_content: str, metadata: Dict[str, Any]) -> str:
        """
        从table_content生成HTML表格
        
        :param table_content: 表格纯文本内容
        :param metadata: 元数据
        :return: 生成的HTML表格
        """
        try:
            headers = metadata.get('table_headers', [])
            if not headers:
                # 如果没有表头信息，生成简单表格
                return f"<table><tbody><tr><td>{table_content}</td></tr></tbody></table>"
            
            # 生成完整表格
            header_html = self._generate_header_html(headers)
            data_html = f"<tbody><tr><td>{table_content}</td></tr></tbody>"
            
            return f"<table>{header_html}{data_html}</table>"
            
        except Exception as e:
            logger.warning(f"从内容生成表格HTML失败: {e}")
            return f"<table><tbody><tr><td>{table_content}</td></tr></tbody></table>"
    
    def _generate_empty_table_html(self, metadata: Dict[str, Any]) -> str:
        """
        生成空表格HTML（只有表头）
        
        :param metadata: 元数据
        :return: 空表格HTML
        """
        try:
            headers = metadata.get('table_headers', [])
            if headers:
                header_html = self._generate_header_html(headers)
                return f"<table>{header_html}<tbody></tbody></table>"
            else:
                return "<table><tbody></tbody></table>"
                
        except Exception as e:
            logger.warning(f"生成空表格HTML失败: {e}")
            return "<table><tbody></tbody></table>"
    
    def _generate_header_html(self, headers: List[str]) -> str:
        """
        生成表头HTML
        
        :param headers: 表头列表
        :return: 表头HTML字符串
        """
        if not headers:
            return ""
        
        header_cells = []
        for header in headers:
            header_cells.append(f"<th>{header}</th>")
        
        return f"<thead><tr>{''.join(header_cells)}</tr></thead>"
    
    
    
    
    
    
    
    
    
    def format_search_results_with_merge(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        合并子表（结果已经是格式化后的）
        
        :param results: 已格式化的搜索结果列表
        :return: 合并后的结果列表
        """
        try:
            # 直接合并子表（结果已经是格式化的）
            if self.config.get('rag_system.table_merge.enabled', True):
                merged_results = self._merge_subtables_for_display(results)
                logger.info(f"子表合并完成，原始结果: {len(results)}，合并后结果: {len(merged_results)}")
                return merged_results
            else:
                return results
                
        except Exception as e:
            logger.error(f"子表合并失败: {e}")
            return results
