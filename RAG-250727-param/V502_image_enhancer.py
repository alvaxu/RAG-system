"""
程序说明：

## 1. V502图像增强器
- 使用DashScope的Qwen-VL-Plus图像大模型对向量数据库中的图片进行深度内容识别
- 生成分层描述（基础视觉、内容理解、数据趋势、语义特征）
- 提取结构化信息（图表类型、数据点、趋势、关键洞察）
- 将识别结果追加到enhanced_description字段中，保留原有信息
- 仅支持批量处理，不支持单张图片处理
- 默认使用config.json，无需额外指定

## 2. 主要功能
- 智能识别已处理图片，避免重复处理
- 保留原有enhanced_description信息
- 添加大模型生成的分层描述和结构化信息
- 支持批量处理和断点续传
- 统一的配置管理和错误处理
"""

import os
import sys
import json
import time
import logging
import argparse
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import base64
import hashlib

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    import dashscope
    from dashscope import MultiModalConversation
    from langchain_community.vectorstores import FAISS
    from langchain_community.embeddings import DashScopeEmbeddings
except ImportError as e:
    print(f"❌ 缺少必要的依赖包: {e}")
    print("请安装: pip install dashscope langchain-community")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class EnhancementResult:
    """增强结果数据类"""
    total_images: int
    enhanced_images: int
    failed_images: int
    processing_time: float
    enhanced_descriptions: List[Dict[str, Any]]


class V502ImageEnhancer:
    """
    V502图像增强器 - 使用Qwen-VL-Plus模型增强图片描述
    """
    
    def __init__(self):
        """
        初始化图像增强器
        """
        # 使用统一配置管理
        self.settings = self._load_unified_config()
        self.api_key = self._get_api_key()
        if not self.api_key:
            raise ValueError("未找到有效的DashScope API密钥")
        
        self.model = "qwen-vl-plus"
        self.vector_store_path = self.settings.vector_db_dir
        
        # 初始化DashScope
        dashscope.api_key = self.api_key
        
        logger.info("V502图像增强器初始化完成")
    
    def _load_unified_config(self) -> 'Settings':
        """
        使用统一配置管理加载配置
        :return: Settings对象
        """
        try:
            from config.settings import Settings
            settings = Settings.load_from_file("config.json")
            logger.info("✅ 使用统一配置管理加载配置成功")
            return settings
        except ImportError as e:
            logger.warning(f"无法导入统一配置管理模块: {e}，使用简单配置加载")
            return self._load_simple_config()
        except Exception as e:
            logger.warning(f"统一配置管理加载失败: {e}，使用简单配置加载")
            return self._load_simple_config()
    
    def _load_simple_config(self) -> 'SimpleSettings':
        """
        简单配置加载（备用方案）
        :return: 简单配置对象
        """
        class SimpleSettings:
            def __init__(self):
                self.vector_db_dir = './central/vector_db'
                self.dashscope_api_key = ''
        
        try:
            if os.path.exists("config.json"):
                with open("config.json", 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                settings = SimpleSettings()
                
                # 加载API密钥
                api_key = config_data.get('api', {}).get('dashscope_api_key', '')
                if api_key and api_key != '你的DashScope API密钥':
                    settings.dashscope_api_key = api_key
                
                # 加载路径配置
                vector_db_dir = config_data.get('paths', {}).get('vector_db_dir', '')
                if vector_db_dir:
                    settings.vector_db_dir = vector_db_dir
                
                logger.info("✅ 使用简单配置加载成功")
                return settings
            else:
                logger.warning("⚠️ config.json不存在，使用默认配置")
                return SimpleSettings()
        except Exception as e:
            logger.warning(f"简单配置加载失败: {e}，使用默认配置")
            return SimpleSettings()
    
    def _get_api_key(self) -> str:
        """
        获取DashScope API密钥 - 与现有代码保持一致
        :return: API密钥
        """
        # 1. 优先从统一配置加载
        if hasattr(self.settings, 'dashscope_api_key') and self.settings.dashscope_api_key:
            logger.info("✅ 从统一配置加载API密钥成功")
            return self.settings.dashscope_api_key
        
        # 2. 备选环境变量
        api_key = os.getenv('MY_DASHSCOPE_API_KEY', '')
        if api_key and api_key != '你的APIKEY':
            logger.info("✅ 从环境变量加载API密钥成功")
            return api_key
        
        # 3. 最后备用
        logger.error("❌ 未找到有效的DashScope API密钥")
        return ""
    
    def _load_vector_store(self) -> Optional[FAISS]:
        """
        加载向量数据库
        :return: FAISS向量存储对象
        """
        try:
            if not os.path.exists(self.vector_store_path):
                logger.error(f"向量数据库路径不存在: {self.vector_store_path}")
                return None
            
            embeddings = DashScopeEmbeddings(
                dashscope_api_key=self.api_key, 
                model="text-embedding-v1"
            )
            vector_store = FAISS.load_local(
                self.vector_store_path, 
                embeddings, 
                allow_dangerous_deserialization=True
            )
            logger.info(f"✅ 向量数据库加载成功，包含 {len(vector_store.docstore._dict)} 个文档")
            return vector_store
        except Exception as e:
            logger.error(f"❌ 加载向量数据库失败: {e}")
            return None
    
    def _identify_image_documents(self, vector_store: FAISS) -> List[Tuple[str, Dict[str, Any]]]:
        """
        识别向量数据库中的图片文档
        :param vector_store: FAISS向量存储对象
        :return: 图片文档列表，每个元素为(doc_id, doc_info)
        """
        image_docs = []
        
        try:
            for doc_id, doc in vector_store.docstore._dict.items():
                metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
                
                # 检查是否为图片类型
                if metadata.get('chunk_type') == 'image':
                    doc_info = {
                        'doc_id': doc_id,
                        'content': doc.page_content,
                        'metadata': metadata,
                        'image_path': metadata.get('image_path', ''),
                        'document_name': metadata.get('document_name', '未知文档'),
                        'page_number': metadata.get('page_number', 1),
                        'img_caption': metadata.get('img_caption', []),
                        'img_footnote': metadata.get('img_footnote', []),
                        'enhanced_description': metadata.get('enhanced_description', ''),
                        'image_type': metadata.get('image_type', 'general'),
                        'semantic_features': metadata.get('semantic_features', {})
                    }
                    image_docs.append((doc_id, doc_info))
            
            logger.info(f"🔍 识别到 {len(image_docs)} 个图片文档")
            return image_docs
            
        except Exception as e:
            logger.error(f"❌ 识别图片文档失败: {e}")
            return []
    
    def is_image_processed(self, doc_info: Dict[str, Any]) -> bool:
        """
        检查图片是否已经通过V502程序处理过
        :param doc_info: 文档信息
        :return: True表示已处理，False表示未处理
        """
        metadata = doc_info.get('metadata', {})
        enhanced_description = metadata.get('enhanced_description', '')
        
        # 检查V502特有标记（更严格的检查）
        v502_markers = [
            'V502_enhanced',
            '基础视觉描述:',
            '内容理解描述:', 
            '数据趋势描述:',
            '语义特征描述:',
            '数据点:',
            '趋势分析:',
            '关键洞察:'
        ]
        
        # 检查是否有V502特有的标记
        if any(marker in enhanced_description for marker in v502_markers):
            # 临时：如果只包含原有信息，允许重新处理
            if '基础视觉描述:' not in enhanced_description and '内容理解描述:' not in enhanced_description:
                return False
            return True
        
        # 检查时间戳
        if metadata.get('v502_enhancement_timestamp'):
            return True
        
        # 检查V502标记字段
        if metadata.get('v502_enhanced'):
            return True
        
        return False
    
    def filter_unprocessed_images(self, image_docs: List[Tuple[str, Dict[str, Any]]]) -> List[Tuple[str, Dict[str, Any]]]:
        """
        过滤出未处理的图片
        :param image_docs: 所有图片文档列表
        :return: 未处理的图片文档列表
        """
        unprocessed_docs = []
        
        for doc_id, doc_info in image_docs:
            if not self.is_image_processed(doc_info):
                unprocessed_docs.append((doc_id, doc_info))
        
        logger.info(f"📊 总图片数: {len(image_docs)}, 未处理图片数: {len(unprocessed_docs)}")
        return unprocessed_docs
    
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
    
    def _call_qwen_vl_model(self, image_path: str) -> Optional[str]:
        """
        调用Qwen-VL-Plus模型进行图像理解
        :param image_path: 图片路径
        :return: 模型响应
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
                max_tokens=1000,
                temperature=0.1
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
            logger.error(f"调用Qwen-VL模型失败: {e}")
            return None
    
    def _generate_layered_descriptions(self, image_path: str) -> Dict[str, str]:
        """
        生成分层描述
        :param image_path: 图片路径
        :return: 分层描述字典
        """
        try:
            # 调用Qwen-VL-Plus模型
            response = self._call_qwen_vl_model(image_path)
            
            if not response:
                return {}
            
            # 解析响应并生成分层描述
            descriptions = {}
            
            # 提取基础视觉描述（支持多种格式）
            if '基础视觉描述' in response:
                # 处理Markdown格式
                if '**基础视觉描述**' in response:
                    start = response.find('**基础视觉描述**') + len('**基础视觉描述**')
                else:
                    start = response.find('基础视觉描述') + len('基础视觉描述')
                
                # 查找结束位置
                end_markers = ['**内容理解描述**', '内容理解描述', '- 内容理解描述', '\n\n']
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
                
                end_markers = ['**数据趋势描述**', '数据趋势描述', '- 数据趋势描述', '\n\n']
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
                
                end_markers = ['**语义特征描述**', '语义特征描述', '- 语义特征描述', '\n\n']
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
                
                end_markers = ['**图表类型**', '图表类型', '- 图表类型', '\n\n']
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
    
    def _extract_structured_info(self, image_path: str) -> Dict[str, Any]:
        """
        提取结构化信息
        :param image_path: 图片路径
        :return: 结构化信息字典
        """
        try:
            # 调用Qwen-VL-Plus模型
            response = self._call_qwen_vl_model(image_path)
            
            if not response:
                return {}
            
            # 解析响应并提取结构化信息
            structured_info = {}
            
            # 提取图表类型
            if '图表类型' in response:
                if '**图表类型**' in response:
                    start = response.find('**图表类型**') + len('**图表类型**')
                else:
                    start = response.find('图表类型') + len('图表类型')
                
                end_markers = ['**数据点**', '数据点', '- 数据点', '\n\n']
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
                
                end_markers = ['**趋势分析**', '趋势分析', '- 趋势分析', '\n\n']
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
                
                end_markers = ['\n\n', '\n', '']
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
        
        # 1. 保留原有信息（如果存在且不是V502生成的）
        if original_description and 'V502_enhanced' not in original_description:
            description_parts.append(f"原有信息: {original_description}")
        elif original_description:
            # 如果原有描述已经包含V502_enhanced标记，仍然保留原有信息
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
        if "V502_enhanced" not in " | ".join(description_parts):
            description_parts.append("V502_enhanced")
        
        return " | ".join(description_parts)
    
    def enhance_single_image(self, doc_id: str, doc_info: Dict[str, Any], vector_store: FAISS) -> Optional[Dict[str, Any]]:
        """
        增强单个图片，保留原有信息
        :param doc_id: 文档ID
        :param doc_info: 文档信息
        :param vector_store: FAISS向量存储对象
        :return: 增强后的信息
        """
        try:
            image_path = doc_info.get('image_path', '')
            
            if not image_path or not os.path.exists(image_path):
                logger.warning(f"图片文件不存在: {image_path}")
                return None
            
            # 获取原有信息
            original_description = doc_info.get('enhanced_description', '')
            
            # 生成新的分层描述和结构化信息
            layered_descriptions = self._generate_layered_descriptions(image_path)
            structured_info = self._extract_structured_info(image_path)
            
            # 构建新的增强描述，保留原有信息
            new_enhanced_description = self._merge_descriptions(
                original_description, 
                layered_descriptions, 
                structured_info
            )
            
            # 更新元数据
            updated_metadata = doc_info['metadata'].copy()
            updated_metadata['enhanced_description'] = new_enhanced_description
            updated_metadata['v502_layered_descriptions'] = layered_descriptions
            updated_metadata['v502_structured_info'] = structured_info
            updated_metadata['v502_enhancement_timestamp'] = int(time.time())
            updated_metadata['v502_enhanced'] = True
            
            # 更新文档
            doc = vector_store.docstore._dict[doc_id]
            doc.metadata = updated_metadata
            
            return {
                'doc_id': doc_id,
                'image_path': image_path,
                'original_description': original_description,
                'enhanced_description': new_enhanced_description,
                'layered_descriptions': layered_descriptions,
                'structured_info': structured_info,
                'document_name': doc_info.get('document_name', '未知文档')
            }
            
        except Exception as e:
            logger.error(f"增强单个图片失败: {e}")
            return None
    
    def _save_vector_store(self, vector_store: FAISS) -> bool:
        """
        保存向量数据库
        :param vector_store: FAISS向量存储对象
        :return: 是否保存成功
        """
        try:
            vector_store.save_local(self.vector_store_path)
            logger.info("✅ 向量数据库保存成功")
            return True
        except Exception as e:
            logger.error(f"❌ 保存向量数据库失败: {e}")
            return False
    
    def enhance_all_images(self, skip_processed: bool = True, batch_size: int = 10) -> EnhancementResult:
        """
        增强所有图片
        :param skip_processed: 是否跳过已处理的图片
        :param batch_size: 批次大小
        :return: 增强结果
        """
        start_time = time.time()
        
        # 1. 加载向量数据库
        vector_store = self._load_vector_store()
        if not vector_store:
            raise ValueError("无法加载向量数据库")
        
        # 2. 识别图片文档
        all_image_docs = self._identify_image_documents(vector_store)
        
        if not all_image_docs:
            logger.warning("⚠️ 未找到图片文档")
            return EnhancementResult(
                total_images=0,
                enhanced_images=0,
                failed_images=0,
                processing_time=time.time() - start_time,
                enhanced_descriptions=[]
            )
        
        # 3. 过滤未处理图片（如果需要）
        if skip_processed:
            image_docs = self.filter_unprocessed_images(all_image_docs)
            logger.info(f"🔍 跳过已处理图片，剩余 {len(image_docs)} 个图片需要处理")
        else:
            image_docs = all_image_docs
            logger.info(f"🔍 处理所有图片，共 {len(image_docs)} 个图片")
        
        # 4. 批量处理图片
        enhanced_count = 0
        failed_count = 0
        enhanced_descriptions = []
        
        for i in range(0, len(image_docs), batch_size):
            batch = image_docs[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(image_docs) + batch_size - 1) // batch_size
            
            logger.info(f"🔄 处理批次 {batch_num}/{total_batches}，共 {len(batch)} 个图片")
            
            for doc_id, doc_info in batch:
                try:
                    enhanced_info = self.enhance_single_image(doc_id, doc_info, vector_store)
                    if enhanced_info:
                        enhanced_descriptions.append(enhanced_info)
                        enhanced_count += 1
                        logger.info(f"✅ 成功增强图片: {doc_info.get('image_path', 'unknown')}")
                    else:
                        failed_count += 1
                        logger.warning(f"❌ 增强失败: {doc_info.get('image_path', 'unknown')}")
                except Exception as e:
                    failed_count += 1
                    logger.error(f"❌ 处理图片时出错: {e}")
                    continue
            
            # 每批次保存一次
            if enhanced_count > 0:
                self._save_vector_store(vector_store)
        
        # 5. 最终保存
        if enhanced_count > 0:
            self._save_vector_store(vector_store)
        
        processing_time = time.time() - start_time
        
        logger.info(f"🎉 图片增强完成")
        logger.info(f"📊 总图片数: {len(image_docs)}")
        logger.info(f"✅ 成功增强: {enhanced_count}")
        logger.info(f"❌ 处理失败: {failed_count}")
        logger.info(f"⏱️ 处理时间: {processing_time:.2f}秒")
        
        return EnhancementResult(
            total_images=len(image_docs),
            enhanced_images=enhanced_count,
            failed_images=failed_count,
            processing_time=processing_time,
            enhanced_descriptions=enhanced_descriptions
        )

    def query_enhanced_descriptions(self, limit: int = 10, show_details: bool = False) -> List[Dict[str, Any]]:
        """
        查询enhanced_description字段内容
        :param limit: 限制返回的图片数量，默认10个
        :param show_details: 是否显示详细信息，默认False
        :return: 图片描述信息列表
        """
        try:
            # 1. 加载向量数据库
            vector_store = self._load_vector_store()
            if not vector_store:
                logger.error("❌ 无法加载向量数据库")
                return []
            
            # 2. 识别图片文档
            image_docs = self._identify_image_documents(vector_store)
            
            if not image_docs:
                logger.warning("⚠️ 未找到图片文档")
                return []
            
            # 3. 提取enhanced_description信息
            descriptions = []
            for doc_id, doc_info in image_docs[:limit]:
                enhanced_description = doc_info.get('enhanced_description', '')
                metadata = doc_info.get('metadata', {})
                
                description_info = {
                    'doc_id': doc_id,
                    'image_path': doc_info.get('image_path', ''),
                    'document_name': doc_info.get('document_name', '未知文档'),
                    'page_number': doc_info.get('page_number', 1),
                    'enhanced_description': enhanced_description,
                    'description_length': len(enhanced_description),
                    'v502_enhanced': metadata.get('v502_enhanced', False),
                    'v502_enhancement_timestamp': metadata.get('v502_enhancement_timestamp', None)
                }
                
                # 如果需要显示详细信息
                if show_details:
                    description_info.update({
                        'img_caption': doc_info.get('img_caption', []),
                        'img_footnote': doc_info.get('img_footnote', []),
                        'image_type': doc_info.get('image_type', 'general'),
                        'v502_layered_descriptions': metadata.get('v502_layered_descriptions', {}),
                        'v502_structured_info': metadata.get('v502_structured_info', {})
                    })
                
                descriptions.append(description_info)
            
            logger.info(f"🔍 查询到 {len(descriptions)} 个图片的enhanced_description信息")
            return descriptions
            
        except Exception as e:
            logger.error(f"❌ 查询enhanced_description失败: {e}")
            return []
    
    def print_enhanced_descriptions(self, limit: int = 10, show_details: bool = False):
        """
        打印enhanced_description字段内容
        :param limit: 限制显示的图片数量，默认10个
        :param show_details: 是否显示详细信息，默认False
        """
        descriptions = self.query_enhanced_descriptions(limit, show_details)
        
        if not descriptions:
            print("❌ 未找到图片描述信息")
            return
        
        print(f"\n📊 图片enhanced_description查询结果（显示前{len(descriptions)}个）:")
        print("=" * 80)
        
        for i, desc_info in enumerate(descriptions, 1):
            print(f"\n📷 图片 {i}: {desc_info['image_path']}")
            print(f"   文档名称: {desc_info['document_name']}")
            print(f"   页面: {desc_info['page_number']}")
            print(f"   描述长度: {desc_info['description_length']} 字符")
            print(f"   V502增强: {desc_info['v502_enhanced']}")
            
            if desc_info['v502_enhancement_timestamp']:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(desc_info['v502_enhancement_timestamp']))
                print(f"   增强时间: {timestamp}")
            
            # 显示enhanced_description内容
            enhanced_desc = desc_info['enhanced_description']
            if enhanced_desc:
                print(f"   增强描述:")
                # 如果描述太长，分段显示
                if len(enhanced_desc) > 200:
                    print(f"      {enhanced_desc[:200]}...")
                    print(f"      ... (完整内容请查看详细信息)")
                else:
                    print(f"      {enhanced_desc}")
            else:
                print(f"   增强描述: 无")
            
            # 如果需要显示详细信息
            if show_details:
                print(f"   详细信息:")
                if desc_info.get('img_caption'):
                    print(f"     图片标题: {desc_info['img_caption']}")
                if desc_info.get('img_footnote'):
                    print(f"     图片脚注: {desc_info['img_footnote']}")
                if desc_info.get('v502_layered_descriptions'):
                    print(f"     分层描述: {desc_info['v502_layered_descriptions']}")
                if desc_info.get('v502_structured_info'):
                    print(f"     结构化信息: {desc_info['v502_structured_info']}")
            
            print("-" * 60)
        
        print(f"\n📈 统计信息:")
        print(f"   总查询数: {len(descriptions)}")
        print(f"   有V502增强: {sum(1 for d in descriptions if d['v502_enhanced'])}")
        print(f"   无V502增强: {sum(1 for d in descriptions if not d['v502_enhanced'])}")
        print(f"   平均描述长度: {sum(d['description_length'] for d in descriptions) / len(descriptions):.1f} 字符")


def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='V502图像增强器 - 使用Qwen-VL-Plus模型增强图片描述')
    parser.add_argument('--skip_processed', action='store_true', default=True,
                       help='是否跳过已处理的图片（默认：是）')
    parser.add_argument('--batch_size', type=int, default=10,
                       help='批次大小（默认：10）')
    parser.add_argument('--config', type=str, default='config.json',
                       help='配置文件路径（默认：config.json）')
    
    # 新增查询功能参数
    parser.add_argument('--query', action='store_true',
                       help='查询enhanced_description字段内容')
    parser.add_argument('--limit', type=int, default=10,
                       help='查询时限制返回的图片数量（默认：10）')
    parser.add_argument('--show_details', action='store_true',
                       help='查询时是否显示详细信息')
    
    args = parser.parse_args()
    
    try:
        # 初始化增强器
        enhancer = V502ImageEnhancer()
        
        # 如果指定了查询参数，执行查询功能
        if args.query:
            enhancer.print_enhanced_descriptions(limit=args.limit, show_details=args.show_details)
            return
        
        # 否则执行增强功能
        results = enhancer.enhance_all_images(
            skip_processed=args.skip_processed,
            batch_size=args.batch_size
        )
        
        # 输出结果
        print(f"\n🎉 V502图像增强完成！")
        print(f"📊 总图片数: {results.total_images}")
        print(f"✅ 成功增强: {results.enhanced_images}")
        print(f"❌ 处理失败: {results.failed_images}")
        print(f"⏱️ 处理时间: {results.processing_time:.2f}秒")
        
        if results.enhanced_images > 0:
            print(f"📈 成功率: {results.enhanced_images / results.total_images * 100:.1f}%")
        
    except Exception as e:
        logger.error(f"❌ 程序执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
