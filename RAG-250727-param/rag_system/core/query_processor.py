"""
查询处理器

RAG系统的核心控制器，负责查询类型识别、流程编排、结果整合等
"""

import logging
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """查询类型枚举"""
    TEXT = "text"
    IMAGE = "image"
    TABLE = "table"
    SMART = "smart"
    HYBRID = "hybrid"


class QueryRequest:
    """查询请求数据类"""
    
    def __init__(self, query_text: str, query_type: QueryType = QueryType.SMART):
        self.query_text = query_text
        self.query_type = query_type
        self.max_results = 10
        self.enable_streaming = True


class QueryResult:
    """查询结果数据类"""
    
    def __init__(self):
        self.query_id = None
        self.status = "pending"
        self.answer = None
        self.sources = []
        self.error_message = None


class QueryProcessor:
    """查询处理器 - RAG系统的核心控制器"""
    
    def __init__(self):
        self.retrieval_engine = None
        self.reranking_service = None
        self.llm_caller = None
        logger.info("查询处理器初始化完成")
    
    def process_query(self, request: QueryRequest) -> QueryResult:
        """处理用户查询请求"""
        try:
            logger.info(f"开始处理查询: {request.query_text[:50]}...")
            
            result = QueryResult()
            result.query_id = self._generate_query_id()
            result.status = "processing"
            
            # 1. 召回检索
            retrieval_results = self._perform_retrieval(request)
            
            # 2. 重排序
            reranked_results = self._perform_reranking(request, retrieval_results)
            
            # 3. LLM生成答案
            answer = self._generate_answer(request, reranked_results)
            result.answer = answer
            
            result.status = "completed"
            return result
            
        except Exception as e:
            logger.error(f"查询处理失败: {str(e)}")
            result = QueryResult()
            result.status = "failed"
            result.error_message = str(e)
            return result
    
    def _perform_retrieval(self, request: QueryRequest) -> List[Dict]:
        """执行召回检索"""
        if not self.retrieval_engine:
            logger.warning("召回引擎未初始化")
            return []
        
        try:
            results = self.retrieval_engine.retrieve(
                request.query_text, 
                max_results=request.max_results
            )
            logger.info(f"召回检索完成，获得 {len(results)} 个结果")
            return results
        except Exception as e:
            logger.error(f"召回检索失败: {str(e)}")
            raise
    
    def _perform_reranking(self, request: QueryRequest, candidates: List[Dict]) -> List[Dict]:
        """执行重排序"""
        if not self.reranking_service:
            return candidates
        
        try:
            reranked_results = self.reranking_service.rerank(
                request.query_text, candidates
            )
            return reranked_results
        except Exception as e:
            logger.error(f"重排序失败: {str(e)}")
            return candidates
    
    def _generate_answer(self, request: QueryRequest, context_results: List[Dict]) -> Dict:
        """使用LLM生成答案"""
        if not self.llm_caller:
            return {"content": "LLM服务暂不可用"}
        
        try:
            context = self._build_context(context_results)
            answer = self.llm_caller.generate_answer(
                request.query_text, context
            )
            return answer
        except Exception as e:
            logger.error(f"LLM答案生成失败: {str(e)}")
            raise
    
    def _build_context(self, results: List[Dict]) -> str:
        """构建LLM上下文"""
        if not results:
            return ""
        
        context_parts = []
        for i, result in enumerate(results[:5]):
            if result.get("content"):
                context_parts.append(f"内容{i+1}: {result['content']}")
        
        return "\n\n".join(context_parts)
    
    def _generate_query_id(self) -> str:
        """生成查询ID"""
        import time
        import uuid
        timestamp = int(time.time())
        unique_id = str(uuid.uuid4())[:8]
        return f"qry_{timestamp}_{unique_id}"
    
    def set_retrieval_engine(self, engine):
        """设置召回引擎"""
        self.retrieval_engine = engine
    
    def set_reranking_service(self, service):
        """设置重排序服务"""
        self.reranking_service = service
    
    def set_llm_caller(self, caller):
        """设置LLM调用器"""
        self.llm_caller = caller
