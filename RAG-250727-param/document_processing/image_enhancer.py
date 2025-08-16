"""
程序说明：

## 1. 图像增强器
- 使用DashScope的Qwen-VL-Plus图像大模型对图片进行深度内容识别
- 生成分层描述（基础视觉、内容理解、数据趋势、语义特征）
- 提取结构化信息（图表类型、数据点、趋势、关键洞察）
- 将识别结果合并到enhanced_description字段中，保留原有信息
- 支持批量处理和进度提示
- 统一的配置管理和错误处理

## 2. 主要功能
- 智能调用视觉大模型进行图像理解
- 生成分层描述和结构化信息
- 保留原有enhanced_description信息
- 支持进度提示和错误回退
- 统一的配置管理和错误处理
"""

import os
import sys
import json
import time
import logging
import base64
from typing import List, Dict, Any, Optional
from pathlib import Path

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    import dashscope
    from dashscope import MultiModalConversation
except ImportError as e:
    print(f"❌ 缺少必要的依赖包: {e}")
    print("请安装: pip install dashscope")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ImageEnhancer:
    """
    图像增强器 - 使用视觉大模型增强图片描述
    """
    
    def __init__(self, api_key: str, config: Dict[str, Any]):
        """
        初始化图像增强器
        :param api_key: DashScope API密钥
        :param config: 配置字典
        """
        self.api_key = api_key
        self.config = config  # 保存配置对象
        self.model = config.get('enhancement_model', 'qwen-vl-plus')
        self.max_tokens = config.get('enhancement_max_tokens', 1000)
        self.temperature = config.get('enhancement_temperature', 0.1)
        self.batch_size = config.get('enhancement_batch_size', 5)
        self.enable_logging = config.get('enable_progress_logging', True)
        
        # 从配置中获取深度处理标记，如果没有则使用默认值
        self.depth_processing_markers = config.get('depth_processing_markers', [
            '**内容理解描述**', '内容理解描述', '- 内容理解描述',
            '**数据趋势描述**', '数据趋势描述', '- 数据趋势描述',
            '**语义特征描述**', '语义特征描述', '- 语义特征描述',
            '**图表类型**', '图表类型', '- 图表类型',
            '**数据点**', '数据点', '- 数据点',
            '**趋势分析**', '趋势分析', '- 趋势分析',
            '**关键洞察**', '关键洞察', '- 关键洞察',
            '\n\n', '\n', ''
        ])
        
        # 初始化DashScope
        dashscope.api_key = self.api_key
        
        logger.info("图像增强器初始化完成")
    
    def vectorize_enhanced_description(self, enhanced_description: str) -> List[float]:
        """
        将enhanced_description使用配置的text-embedding模型进行向量化
        :param enhanced_description: 增强后的图片描述
        :return: 文本向量
        """
        try:
            # 注意：这个方法现在需要外部传入embeddings实例
            # 因为ImageEnhancer类本身没有embeddings实例
            # 实际的向量化将在调用方进行
            logger.info("文本向量化将在调用方进行，使用vector_generator的embeddings")
            return None
                
        except Exception as e:
            logger.error(f"文本向量化异常: {e}")
            return None

    def enhance_image_description(self, image_path: str, original_description: str) -> Dict[str, Any]:
        """
        增强图像描述
        :param image_path: 图片路径
        :param original_description: 原始描述
        :return: 增强后的信息字典
        """
        if self.enable_logging:
            print(f"🔄 正在增强图片: {os.path.basename(image_path)}")
        
        try:
            # 调用视觉模型
            response = self._call_vision_model(image_path)
            if not response:
                if self.enable_logging:
                    print(f"⚠️ 模型调用失败，使用原始描述: {os.path.basename(image_path)}")
                return {'enhanced_description': original_description}
            
            # 生成分层描述
            layered_descriptions = self._generate_layered_descriptions(response)
            
            # 提取结构化信息
            structured_info = self._extract_structured_info(response)
            
            # 合并描述
            enhanced_description = self._merge_descriptions(
                original_description, layered_descriptions, structured_info
            )
            
            if self.enable_logging:
                print(f"✅ 图片增强完成: {os.path.basename(image_path)}")
            
            return {
                'enhanced_description': enhanced_description,
                'layered_descriptions': layered_descriptions,
                'structured_info': structured_info,
                'enhancement_timestamp': int(time.time()),
                'enhancement_enabled': True
            }
            
        except Exception as e:
            logger.error(f"图像增强失败: {e}")
            if self.enable_logging:
                print(f"⚠️ 图片增强失败，使用原始描述: {os.path.basename(image_path)}")
            return {'enhanced_description': original_description}
    
    def _encode_image_to_base64(self, image_path: str) -> str:
        """
        将图片编码为base64字符串
        :param image_path: 图片路径
        :return: base64编码的图片数据
        """
        try:
            with open(image_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
            return encoded_image
        except Exception as e:
            logger.error(f"编码图片文件失败: {e}")
            raise
    
    def _call_vision_model(self, image_path: str) -> Optional[str]:
        """
        调用视觉大模型进行图像理解
        :param image_path: 图片路径
        :return: 模型响应文本
        """
        try:
            # 编码图片
            base64_image = self._encode_image_to_base64(image_path)
            # 添加data URL前缀
            image_data_url = f"data:image/jpeg;base64,{base64_image}"
            
            # 构建提示词
            prompt = """请详细分析这张图片的内容，包括：

1. 基础视觉描述：颜色、布局、主要对象、场景等
2. 内容理解描述：图片展示的场景、活动、关系等
3. 数据趋势描述：如果是图表，请识别图表类型、数据趋势、关键数值等
4. 语义特征描述：图片的主题、情感、上下文等

请按照以下格式回答：
- 基础视觉描述：[描述]
- 内容理解描述：[描述]
- 数据趋势描述：[描述]
- 语义特征描述：[描述]
- 图表类型：[类型]
- 数据点：[关键数据]
- 趋势分析：[趋势]
- 关键洞察：[洞察]"""
            
            # 调用多模态对话模型
            messages = [
                {
                    'role': 'user',
                    'content': [
                        {'text': prompt},
                        {'image': image_data_url}
                    ]
                }
            ]
            
            # 调用模型
            response = MultiModalConversation.call(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            if hasattr(response, 'status_code') and response.status_code == 200:
                if hasattr(response, 'output') and hasattr(response.output, 'choices'):
                    # 处理choices格式
                    choices = response.output.choices
                    if choices and len(choices) > 0:
                        choice = choices[0]
                        if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                            content = choice.message.content
                            if isinstance(content, list) and len(content) > 0:
                                # 如果是列表格式，取第一个text内容
                                for item in content:
                                    if isinstance(item, dict) and 'text' in item:
                                        return item['text']
                            elif isinstance(content, str):
                                return content
                        elif hasattr(choice, 'message') and hasattr(choice.message, 'text'):
                            return choice.message.text
                elif hasattr(response, 'output') and hasattr(response.output, 'text'):
                    return response.output.text
                else:
                    logger.error(f"响应格式不正确: {response}")
                    return None
            elif hasattr(response, 'status_code'):
                logger.error(f"模型调用失败: {response.status_code} - {getattr(response, 'message', '未知错误')}")
                return None
            else:
                logger.error(f"响应格式不正确: {response}")
                return None
                
        except Exception as e:
            logger.error(f"调用视觉模型失败: {e}")
            return None
    
    def _generate_layered_descriptions(self, response: str) -> Dict[str, str]:
        """
        生成分层描述
        :param response: 模型响应文本
        :return: 分层描述字典
        """
        try:
            descriptions = {}
            
            # 提取基础视觉描述（支持多种格式）
            if '基础视觉描述' in response:
                # 处理Markdown格式
                if '**基础视觉描述**' in response:
                    start = response.find('**基础视觉描述**') + len('**基础视觉描述**')
                else:
                    start = response.find('基础视觉描述') + len('基础视觉描述')
                
                # 查找结束位置
                end_markers = [marker for marker in self.depth_processing_markers if '内容理解描述' in marker]
                end = len(response)
                for marker in end_markers:
                    pos = response.find(marker, start)
                    if pos != -1 and pos < end:
                        end = pos
                
                descriptions['基础视觉描述'] = response[start:end].strip().strip('：').strip()
            
            # 提取内容理解描述
            if '内容理解描述' in response:
                if '**内容理解描述**' in response:
                    start = response.find('**内容理解描述**') + len('**内容理解描述**')
                else:
                    start = response.find('内容理解描述') + len('内容理解描述')
                
                end_markers = [marker for marker in self.depth_processing_markers if '数据趋势描述' in marker]
                end = len(response)
                for marker in end_markers:
                    pos = response.find(marker, start)
                    if pos != -1 and pos < end:
                        end = pos
                
                descriptions['内容理解描述'] = response[start:end].strip().strip('：').strip()
            
            # 提取数据趋势描述
            if '数据趋势描述' in response:
                if '**数据趋势描述**' in response:
                    start = response.find('**数据趋势描述**') + len('**数据趋势描述**')
                else:
                    start = response.find('数据趋势描述') + len('数据趋势描述')
                
                end_markers = [marker for marker in self.depth_processing_markers if '语义特征描述' in marker]
                end = len(response)
                for marker in end_markers:
                    pos = response.find(marker, start)
                    if pos != -1 and pos < end:
                        end = pos
                
                descriptions['数据趋势描述'] = response[start:end].strip().strip('：').strip()
            
            # 提取语义特征描述
            if '语义特征描述' in response:
                if '**语义特征描述**' in response:
                    start = response.find('**语义特征描述**') + len('**语义特征描述**')
                else:
                    start = response.find('语义特征描述') + len('语义特征描述')
                
                end_markers = [marker for marker in self.depth_processing_markers if '图表类型' in marker]
                end = len(response)
                for marker in end_markers:
                    pos = response.find(marker, start)
                    if pos != -1 and pos < end:
                        end = pos
                
                descriptions['语义特征描述'] = response[start:end].strip().strip('：').strip()
            
            return descriptions
            
        except Exception as e:
            logger.error(f"生成分层描述失败: {e}")
            return {}
    
    def _extract_structured_info(self, response: str) -> Dict[str, Any]:
        """
        提取结构化信息
        :param response: 模型响应文本
        :return: 结构化信息字典
        """
        try:
            structured_info = {}
            
            # 提取图表类型
            if '图表类型' in response:
                if '**图表类型**' in response:
                    start = response.find('**图表类型**') + len('**图表类型**')
                else:
                    start = response.find('图表类型') + len('图表类型')
                
                end_markers = [marker for marker in self.depth_processing_markers if '数据点' in marker]
                end = len(response)
                for marker in end_markers:
                    pos = response.find(marker, start)
                    if pos != -1 and pos < end:
                        end = pos
                
                structured_info['chart_type'] = response[start:end].strip().strip('：').strip()
            
            # 提取数据点
            if '数据点' in response:
                if '**数据点**' in response:
                    start = response.find('**数据点**') + len('**数据点**')
                else:
                    start = response.find('数据点') + len('数据点')
                
                end_markers = [marker for marker in self.depth_processing_markers if '趋势分析' in marker]
                end = len(response)
                for marker in end_markers:
                    pos = response.find(marker, start)
                    if pos != -1 and pos < end:
                        end = pos
                
                data_points_str = response[start:end].strip().strip('：').strip()
                structured_info['data_points'] = [point.strip() for point in data_points_str.split(',') if point.strip()]
            
            # 提取趋势分析
            if '趋势分析' in response:
                if '**趋势分析**' in response:
                    start = response.find('**趋势分析**') + len('**趋势分析**')
                else:
                    start = response.find('趋势分析') + len('趋势分析')
                
                end_markers = ['**关键洞察**', '关键洞察', '- 关键洞察', '\n\n']
                end = len(response)
                for marker in end_markers:
                    pos = response.find(marker, start)
                    if pos != -1 and pos < end:
                        end = pos
                
                structured_info['trends'] = response[start:end].strip().strip('：').strip()
            
            # 提取关键洞察
            if '关键洞察' in response:
                if '**关键洞察**' in response:
                    start = response.find('**关键洞察**') + len('**关键洞察**')
                else:
                    start = response.find('关键洞察') + len('关键洞察')
                
                end_markers = [marker for marker in self.depth_processing_markers if marker in ['\n\n', '\n', '']]
                end = len(response)
                for marker in end_markers:
                    pos = response.find(marker, start)
                    if pos != -1 and pos < end:
                        end = pos
                
                structured_info['key_insights'] = response[start:end].strip().strip('：').strip()
            
            return structured_info
            
        except Exception as e:
            logger.error(f"提取结构化信息失败: {e}")
            return {}
    
    def _merge_descriptions(self, original_description: str, layered_descriptions: Dict[str, str], structured_info: Dict[str, Any]) -> str:
        """
        智能合并原有描述和新生成的描述
        :param original_description: 原有描述
        :param layered_descriptions: 分层描述
        :param structured_info: 结构化信息
        :return: 合并后的描述
        """
        description_parts = []
        
        # 1. 保留原有信息（如果存在且不是增强生成的）
        if original_description and 'enhancement_enabled' not in original_description:
            description_parts.append(f"原有信息: {original_description}")
        elif original_description:
            # 如果原有描述已经包含增强标记，仍然保留原有信息
            description_parts.append(f"原有信息: {original_description}")
        
        # 2. 添加分层描述
        for layer, desc in layered_descriptions.items():
            if desc:
                description_parts.append(f"{layer}: {desc}")
        
        # 3. 添加结构化信息
        for key, value in structured_info.items():
            if value:
                if isinstance(value, list):
                    value_str = ', '.join(map(str, value))
                else:
                    value_str = str(value)
                description_parts.append(f"{key}: {value_str}")
        
        # 4. 添加处理标记（如果还没有的话）
        if "enhancement_enabled" not in " | ".join(description_parts):
            description_parts.append("enhancement_enabled")
        
        return " | ".join(description_parts)
    
    def enhance_batch_images(self, image_batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量增强图片
        :param image_batch: 图片批次列表
        :return: 增强后的图片信息列表
        """
        total = len(image_batch)
        if self.enable_logging:
            print(f"🔄 开始批量增强 {total} 张图片...")
        
        results = []
        for i, image_info in enumerate(image_batch, 1):
            if self.enable_logging:
                print(f"📷 处理进度: {i}/{total} - {os.path.basename(image_info['image_path'])}")
            
            enhanced_info = self.enhance_image_description(
                image_info['image_path'], 
                image_info['enhanced_description']
            )
            results.append(enhanced_info)
        
        if self.enable_logging:
            print(f"✅ 批量增强完成，共处理 {total} 张图片")
        return results
