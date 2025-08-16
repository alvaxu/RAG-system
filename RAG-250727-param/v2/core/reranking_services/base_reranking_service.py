'''
程序说明：
## 1. Reranking服务基础接口
## 2. 定义所有Reranking服务必须实现的方法
## 3. 确保接口的一致性和可扩展性
## 4. 支持类型特化的优化策略
'''

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import time

logger = logging.getLogger(__name__)


class BaseRerankingService(ABC):
    """
    Reranking服务基础接口
    
    所有类型特化的Reranking服务都必须继承此类并实现抽象方法
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化Reranking服务
        
        :param config: 服务配置字典
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"初始化 {self.get_service_name()} 服务")
    
    @abstractmethod
    def rerank(self, query: str, candidates: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """
        执行重排序
        
        :param query: 查询文本
        :param candidates: 候选文档列表
        :param kwargs: 其他参数
        :return: 重排序后的文档列表
        """
        pass
    
    @abstractmethod
    def get_service_name(self) -> str:
        """
        获取服务名称
        
        :return: 服务名称字符串
        """
        pass
    
    @abstractmethod
    def get_supported_types(self) -> List[str]:
        """
        获取支持的内容类型
        
        :return: 支持的内容类型列表
        """
        pass
    
    def validate_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        验证候选文档的有效性，返回有效的文档列表
        
        :param candidates: 候选文档列表
        :return: 有效的候选文档列表
        """
        if not candidates:
            self.logger.warning("候选文档列表为空")
            return []
        
        valid_candidates = []
        # 检查必要的字段
        required_fields = ['content', 'metadata']
        for i, candidate in enumerate(candidates):
            if not isinstance(candidate, dict):
                self.logger.warning(f"候选文档 {i} 不是字典格式，跳过")
                continue
            
            # 检查必要字段
            missing_fields = [field for field in required_fields if field not in candidate]
            if missing_fields:
                self.logger.warning(f"候选文档 {i} 缺少必要字段: {missing_fields}，跳过")
                continue
            
            # 检查内容是否为空
            if not candidate.get('content', '').strip():
                self.logger.warning(f"候选文档 {i} 内容为空，跳过")
                continue
            
            valid_candidates.append(candidate)
        
        self.logger.info(f"验证完成：从 {len(candidates)} 个候选文档中筛选出 {len(valid_candidates)} 个有效文档")
        return valid_candidates
    
    def preprocess_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        预处理候选文档
        
        :param candidates: 候选文档列表
        :return: 预处理后的候选文档列表
        """
        if not candidates:
            self.logger.warning("没有候选文档需要预处理")
            return []
        
        # 添加处理标记
        for candidate in candidates:
            candidate['reranking_service'] = self.get_service_name()
            candidate['preprocessed'] = True
            candidate['preprocess_timestamp'] = time.time()
        
        self.logger.info(f"预处理完成：为 {len(candidates)} 个候选文档添加了处理标记")
        return candidates
    
    def postprocess_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        后处理重排序结果
        
        :param results: 重排序后的结果列表
        :return: 后处理后的结果列表
        """
        # 标记重排序完成
        for result in results:
            result['reranking_completed'] = True
            result['reranking_score'] = result.get('reranking_score', 0.0)
        
        # 按重排序分数排序
        results.sort(key=lambda x: x.get('reranking_score', 0.0), reverse=True)
        
        return results
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        安全地获取配置值
        
        :param key: 配置键
        :param default: 默认值
        :return: 配置值
        """
        return self.config.get(key, default)
    
    def log_reranking_stats(self, input_count: int, output_count: int, processing_time: float):
        """
        记录重排序统计信息
        
        :param input_count: 输入文档数量
        :param output_count: 输出文档数量
        :param processing_time: 处理时间
        """
        self.logger.info(
            f"重排序完成 - 输入: {input_count}, 输出: {output_count}, "
            f"耗时: {processing_time:.3f}秒"
        )
