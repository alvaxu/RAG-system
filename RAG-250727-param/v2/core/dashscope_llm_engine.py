"""
DashScope LLM引擎 - 基于通义千问的智能答案生成

## 1. 功能特点
- 使用DashScope API访问通义千问模型
- 支持多种模型选择（Qwen-Turbo/Qwen-Plus）
- 智能提示词工程和答案生成
- 可配置的生成参数

## 2. 与其他版本的不同点
- 新增的LLM引擎，替代原有的简单模板答案
- 支持DashScope API密钥管理
- 智能的上下文处理和答案生成
"""

import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import dashscope
from dashscope import Generation

logger = logging.getLogger(__name__)

@dataclass
class LLMConfig:
    """LLM配置"""
    model_name: str = "qwen-turbo"
    temperature: float = 0.7
    max_tokens: int = 2000
    top_p: float = 0.8
    enable_stream: bool = False
    system_prompt: str = "你是一个专业的AI助手，能够基于提供的上下文信息生成准确、相关、完整的答案。"

class DashScopeLLMEngine:
    """DashScope LLM引擎"""
    
    def __init__(self, api_key: str, config: Optional[LLMConfig] = None):
        """
        初始化LLM引擎
        
        :param api_key: DashScope API密钥
        :param config: LLM配置
        """
        self.api_key = api_key
        self.config = config or LLMConfig()
        
        # 设置API密钥
        dashscope.api_key = self.api_key
        
        logger.info(f"DashScope LLM引擎初始化完成，使用模型: {self.config.model_name}")
    
    def generate_answer(self, question: str, context: str, **kwargs) -> str:
        """
        基于上下文生成答案
        
        :param question: 用户问题
        :param context: 上下文信息
        :param kwargs: 其他参数
        :return: 生成的答案
        """
        try:
            # 构建提示词
            prompt = self._build_prompt(question, context)
            
            # 调用生成API
            response = self._call_generation_api(prompt, **kwargs)
            
            if response.status_code == 200:
                answer = response.output.text
                logger.info(f"答案生成成功，长度: {len(answer)} 字符")
                return answer
            else:
                logger.error(f"答案生成失败: {response.message}")
                return self._generate_fallback_answer(question, context)
                
        except Exception as e:
            logger.error(f"答案生成过程中发生错误: {str(e)}")
            return self._generate_fallback_answer(question, context)
    
    def _build_prompt(self, question: str, context: str) -> str:
        """
        构建提示词
        
        :param question: 用户问题
        :param context: 上下文信息
        :return: 完整的提示词
        """
        prompt = f"""系统：{self.config.system_prompt}

上下文信息：
{context}

用户问题：{question}

请基于上述上下文信息，为用户提供准确、相关、完整的答案。如果上下文中没有相关信息，请明确说明。答案应该：
1. 直接回答用户问题
2. 引用相关的上下文信息
3. 保持逻辑清晰和结构完整
4. 使用中文回答

答案："""
        return prompt
    
    def _call_generation_api(self, prompt: str, **kwargs) -> Any:
        """
        调用生成API
        
        :param prompt: 提示词
        :param kwargs: 其他参数
        :return: API响应
        """
        # 合并配置参数和传入参数
        generation_params = {
            'model': self.config.model_name,
            'prompt': prompt,
            'temperature': kwargs.get('temperature', self.config.temperature),
            'max_tokens': kwargs.get('max_tokens', self.config.max_tokens),
            'top_p': kwargs.get('top_p', self.config.top_p),
            'stream': kwargs.get('enable_stream', self.config.enable_stream)
        }
        
        # 移除None值
        generation_params = {k: v for k, v in generation_params.items() if v is not None}
        
        return Generation.call(**generation_params)
    
    def _generate_fallback_answer(self, question: str, context: str) -> str:
        """
        生成备用答案（当API调用失败时）
        
        :param question: 用户问题
        :param context: 上下文信息
        :return: 备用答案
        """
        logger.warning("使用备用答案生成逻辑")
        
        # 简单的关键词匹配和模板答案
        if not context or context.strip() == "":
            return "抱歉，我没有找到相关的上下文信息来回答您的问题。请尝试重新提问或提供更多信息。"
        
        # 基于上下文长度和问题类型生成简单答案
        context_length = len(context)
        if context_length > 1000:
            return f"根据您的问题，我在文档中找到了相关内容。文档信息较为详细（约{context_length}字符），建议您查看详细结果获取完整信息。"
        else:
            return f"根据您的问题，我找到了以下相关内容：{context[:200]}{'...' if len(context) > 200 else ''}"
    
    def batch_generate_answers(self, questions: List[str], contexts: List[str], **kwargs) -> List[str]:
        """
        批量生成答案
        
        :param questions: 问题列表
        :param contexts: 上下文列表
        :param kwargs: 其他参数
        :return: 答案列表
        """
        if len(questions) != len(contexts):
            raise ValueError("问题列表和上下文列表长度必须相同")
        
        answers = []
        for i, (question, context) in enumerate(zip(questions, contexts)):
            try:
                answer = self.generate_answer(question, context, **kwargs)
                answers.append(answer)
                logger.info(f"批量生成进度: {i+1}/{len(questions)}")
            except Exception as e:
                logger.error(f"批量生成第{i+1}个答案时发生错误: {str(e)}")
                answers.append(self._generate_fallback_answer(question, context))
        
        return answers
    
    def analyze_question_intent(self, question: str) -> Dict[str, Any]:
        """
        分析问题意图
        
        :param question: 用户问题
        :return: 意图分析结果
        """
        try:
            analysis_prompt = f"""请分析以下问题的意图和类型：

问题：{question}

请从以下维度分析：
1. 问题类型（事实查询/分析比较/操作指导/其他）
2. 信息需求（具体数据/概念解释/步骤说明/其他）
3. 复杂度（简单/中等/复杂）
4. 领域分类（技术/业务/管理/其他）

分析结果："""
            
            response = self._call_generation_api(analysis_prompt, temperature=0.3)
            
            if response.status_code == 200:
                analysis = response.output.text
                return {
                    'question': question,
                    'analysis': analysis,
                    'status': 'success'
                }
            else:
                return {
                    'question': question,
                    'analysis': '分析失败',
                    'status': 'failed',
                    'error': response.message
                }
                
        except Exception as e:
            logger.error(f"问题意图分析失败: {str(e)}")
            return {
                'question': question,
                'analysis': '分析失败',
                'status': 'error',
                'error': str(e)
            }
    
    def get_engine_status(self) -> Dict[str, Any]:
        """
        获取引擎状态信息
        
        :return: 状态信息字典
        """
        return {
            "engine_type": "DashScope LLM",
            "model_name": self.config.model_name,
            "api_key_configured": bool(self.api_key),
            "config": {
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "top_p": self.config.top_p,
                "enable_stream": self.config.enable_stream,
                "system_prompt_length": len(self.config.system_prompt)
            }
        }
    
    def update_config(self, **kwargs) -> bool:
        """
        更新配置参数
        
        :param kwargs: 要更新的配置参数
        :return: 是否更新成功
        """
        try:
            for key, value in kwargs.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                    logger.info(f"配置参数 {key} 更新为: {value}")
                else:
                    logger.warning(f"未知的配置参数: {key}")
            
            return True
            
        except Exception as e:
            logger.error(f"更新配置失败: {str(e)}")
            return False
