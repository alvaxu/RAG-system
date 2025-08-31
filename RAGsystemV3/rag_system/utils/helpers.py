"""
工具函数模块

提供RAG系统开发中需要的通用工具函数
"""

import logging
import hashlib
import time
from typing import List, Dict, Any, Optional
import re

logger = logging.getLogger(__name__)


def generate_id(prefix: str = "item") -> str:
    """
    生成唯一ID
    
    Args:
        prefix: ID前缀
        
    Returns:
        str: 生成的唯一ID
    """
    timestamp = int(time.time() * 1000)
    random_suffix = hashlib.md5(f"{timestamp}".encode()).hexdigest()[:8]
    return f"{prefix}_{timestamp}_{random_suffix}"


def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    安全获取字典值
    
    Args:
        data: 数据字典
        key: 键名
        default: 默认值
        
    Returns:
        Any: 获取的值或默认值
    """
    try:
        return data.get(key, default)
    except (KeyError, TypeError, AttributeError):
        return default


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """
    截断文本
    
    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 截断后缀
        
    Returns:
        str: 截断后的文本
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def extract_keywords(text: str, max_keywords: int = 20) -> List[str]:
    """
    提取文本关键词
    
    Args:
        text: 输入文本
        max_keywords: 最大关键词数量
        
    Returns:
        List[str]: 关键词列表
    """
    if not text:
        return []
    
    try:
        # 简单的关键词提取（基于词频）
        words = re.findall(r'\w+', text.lower())
        
        # 过滤停用词
        stop_words = {
            '的', '是', '在', '有', '和', '与', '或', '但', '而', '如果', '那么', 
            '因为', '所以', '这个', '那个', '这些', '那些', '什么', '怎么', '为什么'
        }
        
        # 过滤短词和停用词
        filtered_words = [
            word for word in words 
            if len(word) > 1 and word not in stop_words
        ]
        
        # 统计词频
        word_freq = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # 按频率排序并返回前N个
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, freq in sorted_words[:max_keywords]]
        
        return keywords
        
    except Exception as e:
        logger.error(f"关键词提取失败: {str(e)}")
        return []


def calculate_similarity(text1: str, text2: str) -> float:
    """
    计算两个文本的相似度（基于关键词重叠）
    
    Args:
        text1: 文本1
        text2: 文本2
        
    Returns:
        float: 相似度分数 (0-1)
    """
    try:
        if not text1 or not text2:
            return 0.0
        
        # 提取关键词
        keywords1 = set(extract_keywords(text1))
        keywords2 = set(extract_keywords(text2))
        
        if not keywords1 or not keywords2:
            return 0.0
        
        # 计算Jaccard相似度
        intersection = len(keywords1.intersection(keywords2))
        union = len(keywords1.union(keywords2))
        
        similarity = intersection / union if union > 0 else 0.0
        return similarity
        
    except Exception as e:
        logger.error(f"相似度计算失败: {str(e)}")
        return 0.0


def validate_config(config: Dict[str, Any], required_keys: List[str]) -> bool:
    """
    验证配置字典
    
    Args:
        config: 配置字典
        required_keys: 必需的键列表
        
    Returns:
        bool: 验证是否通过
    """
    try:
        if not isinstance(config, dict):
            logger.error("配置必须是字典类型")
            return False
        
        for key in required_keys:
            if key not in config:
                logger.error(f"缺少必需的配置项: {key}")
                return False
            
            if config[key] is None:
                logger.error(f"配置项不能为空: {key}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"配置验证失败: {str(e)}")
        return False


def format_timestamp(timestamp: float) -> str:
    """
    格式化时间戳
    
    Args:
        timestamp: Unix时间戳
        
    Returns:
        str: 格式化的时间字符串
    """
    try:
        import datetime
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        logger.error(f"时间格式化失败: {str(e)}")
        return str(timestamp)


def sanitize_filename(filename: str) -> str:
    """
    清理文件名
    
    Args:
        filename: 原始文件名
        
    Returns:
        str: 清理后的文件名
    """
    try:
        # 移除或替换非法字符
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # 限制长度
        if len(sanitized) > 255:
            name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
            sanitized = name[:255-len(ext)-1] + ('.' + ext if ext else '')
        
        return sanitized
        
    except Exception as e:
        logger.error(f"文件名清理失败: {str(e)}")
        return "unknown_file"


def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    合并两个字典
    
    Args:
        dict1: 字典1
        dict2: 字典2
        
    Returns:
        Dict[str, Any]: 合并后的字典
    """
    try:
        merged = dict1.copy()
        
        for key, value in dict2.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                # 递归合并嵌套字典
                merged[key] = merge_dicts(merged[key], value)
            else:
                # 直接覆盖
                merged[key] = value
        
        return merged
        
    except Exception as e:
        logger.error(f"字典合并失败: {str(e)}")
        return dict1.copy()


def chunk_list(data: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    将列表分块
    
    Args:
        data: 原始列表
        chunk_size: 块大小
        
    Returns:
        List[List[Any]]: 分块后的列表
    """
    try:
        if chunk_size <= 0:
            return [data]
        
        return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
        
    except Exception as e:
        logger.error(f"列表分块失败: {str(e)}")
        return [data]


def retry_on_failure(func, max_retries: int = 3, delay: float = 1.0):
    """
    失败重试装饰器
    
    Args:
        func: 要执行的函数
        max_retries: 最大重试次数
        delay: 重试延迟（秒）
    """
    def wrapper(*args, **kwargs):
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    logger.warning(f"函数执行失败，第{attempt + 1}次重试: {str(e)}")
                    time.sleep(delay)
                else:
                    logger.error(f"函数执行失败，已达到最大重试次数: {str(e)}")
        
        raise last_exception
    
    return wrapper
