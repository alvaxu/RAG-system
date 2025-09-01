"""
LLM调用器模块

集成DashScope LLM服务，提供智能问答功能
严格按照35.V3_RAG_LLM调用模块详细设计文档实现
"""

import logging
import time
from typing import Dict, List, Any, Optional
import dashscope
from dashscope import Generation
from dataclasses import dataclass

from .config_integration import ConfigIntegration
from .prompt_manager import PromptManager
from .context_manager import ContextManager, ContextChunk

logger = logging.getLogger(__name__)

@dataclass
class LLMResponse:
    """LLM响应数据结构"""
    answer: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    processing_time: float
    model_name: str
    prompt_template: str
    context_length: int
    success: bool
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class LLMCaller:
    """LLM调用器 - 集成DashScope LLM服务"""
    
    def __init__(self, config_integration: ConfigIntegration):
        """
        初始化RAG LLM调用器
        
        :param config_integration: 配置集成管理器实例
        """
        self.config = config_integration
        
        # 获取RAG LLM配置
        self.rag_config = config_integration.get_rag_config('models.llm', {})
        
        # LLM模型参数
        self.model_name = self.rag_config.get('model_name', 'qwen-turbo')
        self.max_tokens = self.rag_config.get('max_tokens', 2048)
        self.temperature = self.rag_config.get('temperature', 0.7)
        self.system_prompt = self.rag_config.get('system_prompt', '你是一个专业的AI助手，请基于提供的上下文信息回答问题。')
        
        # 初始化LLM客户端
        self.llm_client = None
        self._initialize_llm()
        
        # 初始化提示词管理器和上下文管理器
        self.prompt_manager = PromptManager(config_integration)
        self.context_manager = ContextManager(config_integration)
        
        # Token统计
        self.token_stats = {
            'total_prompts': 0,
            'total_completions': 0,
            'total_tokens': 0,
            'avg_prompt_tokens': 0,
            'avg_completion_tokens': 0,
            'avg_total_tokens': 0
        }
        
        logger.info(f"LLM调用器初始化完成，使用模型: {self.model_name}")
    
    def _initialize_llm(self):
        """初始化LLM客户端"""
        try:
            # 获取API密钥（复用V3的环境变量管理）
            api_key = self.config.get_env_var('DASHSCOPE_API_KEY')
            
            if not api_key or api_key == 'mock_key':
                logger.warning("未找到有效的DashScope API密钥，使用模拟模式")
                self.llm_client = None
                return
            
            # 设置DashScope API密钥
            dashscope.api_key = api_key
            self.llm_client = True  # 标记为可用
            logger.info(f"DashScope LLM客户端初始化成功: {self.model_name}")
                
        except Exception as e:
            logger.error(f"LLM客户端初始化失败: {str(e)}")
            self.llm_client = None
    
    def generate_answer(self, query_text: str, context_chunks: List[ContextChunk], 
                       prompt_template: str = 'rag_qa') -> LLMResponse:
        """
        使用LLM生成答案
        
        Args:
            query_text: 查询文本
            context_chunks: 上下文块列表
            prompt_template: 提示词模板名称
            
        Returns:
            LLMResponse: 包含答案和统计信息的响应对象
        """
        start_time = time.time()
        
        try:
            if not self.llm_client:
                logger.warning("LLM客户端未初始化，返回模拟答案")
                return self._generate_mock_response(query_text, context_chunks, prompt_template)
            
            logger.info("开始生成LLM答案")
            
            # 1. 优化上下文
            optimized_context = self.context_manager.optimize_context(
                context_chunks, query_text
            )
            
            # 2. 生成提示词
            prompt = self.prompt_manager.generate_prompt(
                prompt_template, 
                {'context': optimized_context, 'query': query_text}
            )
            
            # 3. 调用LLM生成答案
            response = self._call_llm(prompt)
            
            # 4. 处理响应结果
            answer = self._process_response(response)
            
            # 5. 统计Token使用量
            prompt_tokens = self._estimate_tokens(prompt)
            completion_tokens = self._estimate_tokens(answer)
            total_tokens = prompt_tokens + completion_tokens
            
            # 6. 更新Token统计
            self._update_token_stats(prompt_tokens, completion_tokens, total_tokens)
            
            processing_time = time.time() - start_time
            
            logger.info("LLM答案生成完成")
            
            return LLMResponse(
                answer=answer,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                processing_time=processing_time,
                model_name=self.model_name,
                prompt_template=prompt_template,
                context_length=len(optimized_context),
                success=True,
                metadata={
                    'context_chunks_count': len(context_chunks),
                    'optimized_context_length': len(optimized_context),
                    'prompt_length': len(prompt)
                }
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"LLM答案生成失败: {str(e)}"
            logger.error(error_msg)
            
            return LLMResponse(
                answer="",
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                processing_time=processing_time,
                model_name=self.model_name,
                prompt_template=prompt_template,
                context_length=0,
                success=False,
                error_message=error_msg
            )
    
    def _call_llm(self, prompt: str) -> str:
        """调用DashScope LLM服务"""
        try:
            logger.info(f"调用DashScope LLM API，模型: {self.model_name}，提示词长度: {len(prompt)}")
            
            # 调用DashScope Generation API
            response = Generation.call(
                model=self.model_name,
                prompt=prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            if response.status_code == 200:
                # 成功响应
                answer = response.output.text
                logger.info(f"DashScope LLM API调用成功，生成长度: {len(answer)} 字符")
                return answer
            else:
                # API调用失败
                error_msg = f"DashScope API调用失败: {response.message}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"调用DashScope LLM API失败: {str(e)}")
            raise
    
    def _process_response(self, response: str) -> str:
        """处理LLM响应，返回答案文本"""
        try:
            # 直接返回响应文本
            return response.strip()
            
        except Exception as e:
            logger.error(f"处理LLM响应失败: {str(e)}")
            return "抱歉，处理响应时出现错误。"
    
    def _estimate_tokens(self, text: str) -> int:
        """
        估算文本的Token数量
        
        :param text: 文本内容
        :return: 估算的Token数量
        """
        try:
            # 简单的Token估算（中文约1.5字符=1Token，英文约4字符=1Token）
            chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
            english_chars = len(text) - chinese_chars
            
            # 估算Token数量
            estimated_tokens = int(chinese_chars / 1.5 + english_chars / 4)
            
            return max(1, estimated_tokens)  # 至少1个Token
            
        except Exception as e:
            logger.error(f"Token估算失败: {e}")
            # 使用简单的字符数估算
            return max(1, len(text) // 4)
    
    def _update_token_stats(self, prompt_tokens: int, completion_tokens: int, total_tokens: int):
        """更新Token统计信息"""
        try:
            self.token_stats['total_prompts'] += prompt_tokens
            self.token_stats['total_completions'] += completion_tokens
            self.token_stats['total_tokens'] += total_tokens
            
            # 计算平均值
            total_calls = self.token_stats.get('total_calls', 0) + 1
            self.token_stats['total_calls'] = total_calls
            
            self.token_stats['avg_prompt_tokens'] = self.token_stats['total_prompts'] / total_calls
            self.token_stats['avg_completion_tokens'] = self.token_stats['total_completions'] / total_calls
            self.token_stats['avg_total_tokens'] = self.token_stats['total_tokens'] / total_calls
            
        except Exception as e:
            logger.error(f"更新Token统计失败: {e}")
    
    def _generate_mock_response(self, query_text: str, context_chunks: List[ContextChunk], 
                               prompt_template: str) -> LLMResponse:
        """生成模拟响应（当LLM服务不可用时）"""
        start_time = time.time()
        
        try:
            # 优化上下文
            optimized_context = self.context_manager.optimize_context(context_chunks, query_text)
            
            # 生成提示词
            prompt = self.prompt_manager.generate_prompt(
                prompt_template, 
                {'context': optimized_context, 'query': query_text}
            )
            
            # 生成模拟答案
            if not optimized_context:
                answer = "抱歉，没有找到相关的上下文信息。"
            else:
                context_preview = optimized_context[:200] + "..." if len(optimized_context) > 200 else optimized_context
                answer = f"基于提供的上下文信息，我来回答您的问题：{query_text}\n\n"
                answer += f"上下文内容：{context_preview}\n\n"
                answer += "这是一个模拟的LLM响应，实际应该调用DashScope的Qwen模型。"
            
            # 统计Token
            prompt_tokens = self._estimate_tokens(prompt)
            completion_tokens = self._estimate_tokens(answer)
            total_tokens = prompt_tokens + completion_tokens
            
            # 更新统计
            self._update_token_stats(prompt_tokens, completion_tokens, total_tokens)
            
            processing_time = time.time() - start_time
            
            return LLMResponse(
                answer=answer,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                processing_time=processing_time,
                model_name=self.model_name,
                prompt_template=prompt_template,
                context_length=len(optimized_context),
                success=True,
                metadata={
                    'mode': 'mock',
                    'context_chunks_count': len(context_chunks),
                    'optimized_context_length': len(optimized_context)
                }
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return LLMResponse(
                answer="生成模拟答案时发生错误",
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                processing_time=processing_time,
                model_name=self.model_name,
                prompt_template=prompt_template,
                context_length=0,
                success=False,
                error_message=str(e)
            )
    
    def get_token_stats(self) -> Dict[str, Any]:
        """获取Token使用统计"""
        return self.token_stats.copy()
    
    def get_prompt_manager(self) -> PromptManager:
        """获取提示词管理器"""
        return self.prompt_manager
    
    def get_context_manager(self) -> ContextManager:
        """获取上下文管理器"""
        return self.context_manager
    
    def update_config(self, **kwargs):
        """更新配置参数"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                logger.info(f"LLM调用器配置更新: {key} = {value}")
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return {
            "model_name": self.model_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "system_prompt": self.system_prompt,
            "token_stats": self.token_stats
        }
    
    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态信息"""
        return {
            'status': 'ready',
            'service_type': 'RAG LLM Caller',
            'model_name': self.model_name,
            'llm_client_available': self.llm_client is not None,
            'token_stats': self.token_stats,
            'prompt_manager_status': self.prompt_manager.get_service_status(),
            'context_manager_status': self.context_manager.get_service_status()
        }
