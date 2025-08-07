'''
程序说明：

## 1. 修复图号匹配的精确性问题
## 2. 避免图1匹配图11、图12等不相关图片
## 3. 使用更精确的正则表达式匹配
'''

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_figure_matching():
    """
    测试图号匹配逻辑
    """
    # 测试数据
    test_captions = [
        "图1：公司单季度营业收入及增速情况",
        "图1：中芯国际全球部署示意图", 
        "图11：中芯国际股权架构图(截止至2024年年末）",
        "图12：芯片制造9大步骤",
        "图9：公司销/管/研三费费率情况(%) 图10：公司三费费用增长情况",
        "图4：公司25Q1下游应用领域结构情况"
    ]
    
    # 测试查询
    test_queries = ["图1", "图4", "图11"]
    
    logger.info("=== 测试当前匹配逻辑（有问题的版本）===")
    for query in test_queries:
        logger.info(f"\n查询: {query}")
        matches = []
        
        for caption in test_captions:
            # 当前有问题的匹配逻辑
            match_patterns = [
                f"图{query.replace('图', '')}",
                f"图表{query.replace('图', '')}",
                f"图片{query.replace('图', '')}",
                f"Figure {query.replace('图', '')}"
            ]
            
            is_match = any(pattern in caption for pattern in match_patterns)
            if is_match:
                matches.append(caption)
                logger.info(f"  ✅ 匹配: {caption}")
        
        logger.info(f"  总共匹配到 {len(matches)} 个")
    
    logger.info("\n=== 测试修复后的匹配逻辑 ===")
    for query in test_queries:
        logger.info(f"\n查询: {query}")
        matches = []
        
        for caption in test_captions:
            # 修复后的精确匹配逻辑
            figure_num = query.replace('图', '')
            
            # 使用正则表达式进行精确匹配
            # 匹配模式：图+数字+冒号或空格，确保不会匹配到更大的数字
            exact_patterns = [
                rf"图{figure_num}[：:]\s*",  # 图1：或图1:
                rf"图{figure_num}\s+",       # 图1 后面跟空格
                rf"图{figure_num}$",         # 图1 在字符串末尾
                rf"图{figure_num}[）\)]",    # 图1）或图1)
            ]
            
            is_match = any(re.search(pattern, caption) for pattern in exact_patterns)
            if is_match:
                matches.append(caption)
                logger.info(f"  ✅ 精确匹配: {caption}")
        
        logger.info(f"  总共精确匹配到 {len(matches)} 个")

def create_fixed_code():
    """
    生成修复后的代码
    """
    logger.info("\n=== 修复后的代码片段 ===")
    
    fixed_code = '''
# 修复后的图号匹配逻辑
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
        figure_pattern = r'图(\\d+)'
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

                        # 使用精确的正则表达式匹配
                        exact_patterns = [
                            rf"图{figure_num}[：:]\\s*",  # 图1：或图1:
                            rf"图{figure_num}\\s+",       # 图1 后面跟空格
                            rf"图{figure_num}$",          # 图1 在字符串末尾
                            rf"图{figure_num}[）\\)]",    # 图1）或图1)
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

            # 如果找到了特定图片，直接返回
            if all_docs:
                logger.info(f"找到 {len(all_docs)} 个特定图片，直接返回")
                return all_docs[:k]

        # 如果没有找到特定图片或没有特定图片请求，进行常规检索
        # ... 原有的检索逻辑 ...

    except Exception as e:
        logger.error(f"初始检索失败: {e}")
        return []
'''
    
    print(fixed_code)
    logger.info("修复要点：")
    logger.info("1. 使用正则表达式进行精确匹配，而不是简单的字符串包含")
    logger.info("2. 匹配模式包括：图号+冒号、图号+空格、图号+结尾、图号+右括号")
    logger.info("3. 这样可以避免图1匹配到图11、图12等")

if __name__ == "__main__":
    test_figure_matching()
    create_fixed_code()
