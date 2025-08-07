
# 图4检索修复补丁
# 在 core/enhanced_qa_system.py 的 _initial_retrieval 方法中添加以下代码

import re

def _initial_retrieval(self, question: str, k: int) -> List[Document]:
    """
    改进的初始检索方法 - 支持特定图片编号的精确匹配
    :param question: 问题
    :param k: 检索数量
    :return: 检索到的文档
    """
    if not self.vector_store:
        return []
    
    try:
        # 检查是否包含特定图片编号请求
        figure_pattern = r'图(\d+)'
        figure_matches = re.findall(figure_pattern, question)
        
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
                        caption = doc.metadata.get('img_caption', [])
                        caption_text = ' '.join(caption) if caption else ''
                        
                        # 检查多种匹配模式
                        match_patterns = [
                            f"图{figure_num}",
                            f"图表{figure_num}",
                            f"图片{figure_num}",
                            f"Figure {figure_num}"
                        ]
                        
                        is_match = any(pattern in caption_text for pattern in match_patterns)
                        
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
            
            # 如果找到了特定图片，直接返回
            if all_docs:
                logger.info(f"找到 {len(all_docs)} 个特定图片，直接返回")
                return all_docs[:k]
        
        # 如果没有找到特定图片或没有特定图片请求，进行常规检索
        # ... 原有的检索逻辑 ...
        
    except Exception as e:
        logger.error(f"初始检索失败: {e}")
        return []
