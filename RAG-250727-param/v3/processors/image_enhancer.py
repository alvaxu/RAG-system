'''
程序说明：
## 1. ImageEnhancer子模块
- 负责图片增强处理，一次性生成完整的增强信息
- 避免多层处理导致的重复，实现智能去重机制
- 完全符合设计文档规范，位于processors模块下
## 2. 主要功能
- 一次性生成完整的图片增强信息
- 智能去重机制，确保信息质量和一致性
- 通过ModelCaller调用图片增强模型
- 生成分层描述和结构化信息
## 3. 与优化方案的关系
- 实现优化方案要求的一次性增强信息生成
- 避免重复内容，提高处理效率
'''
import os
import time
import logging
import re
from typing import Dict, List, Any
import dashscope

class ImageEnhancer:
    """
    图片增强处理器（优化版）
    一次性生成完整增强信息，避免重复内容
    完全符合设计文档规范，位于processors模块下
    """
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.config = config_manager.get_all_config()
        self.enhancement_model = self.config.get('image_processing.enhancement_model', 'qwen-vl-plus')
        self.enhancement_model_api = self.config.get('image_processing.enhancement_model_api', 'dashscope')
        self.batch_size = self.config.get('api_rate_limiting.enhancement_batch_size', 5)
        self.delay_seconds = self.config.get('api_rate_limiting.enhancement_delay_seconds', 2)
        self.failure_handler = config_manager.get_failure_handler()
        
        # 初始化DashScope API
        self.dashscope_api_key = os.getenv('DASHSCOPE_API_KEY')
        if not self.dashscope_api_key:
            raise ValueError("未设置环境变量 DASHSCOPE_API_KEY")
        dashscope.api_key = self.dashscope_api_key
        
        # 加载处理标记
        self._load_processing_markers()
        
        logging.info("图片增强处理器（优化版）初始化完成")
    
    def _load_processing_markers(self):
        """加载处理标记配置"""
        self.processing_markers = {
            'layered_descriptions': {
                'scene': ['场景', '环境', '背景', '地点', '位置'],
                'objects': ['物体', '物品', '对象', '主体', '主要元素'],
                'actions': ['动作', '行为', '活动', '状态', '过程'],
                'attributes': ['属性', '特征', '性质', '特点', '描述'],
                'relationships': ['关系', '联系', '关联', '组合', '布局'],
                'details': ['细节', '纹理', '颜色', '形状', '大小']
            },
            'structured_info': {
                'technical': ['技术', '参数', '规格', '配置', '设置'],
                'business': ['业务', '商业', '市场', '产品', '服务'],
                'scientific': ['科学', '研究', '实验', '数据', '分析'],
                'artistic': ['艺术', '设计', '创意', '风格', '美学'],
                'documentary': ['文档', '记录', '信息', '内容', '文本']
            }
        }
        
        # 生成标记组合
        self.marker_combinations = self._generate_marker_combinations(self.processing_markers)
    
    def _generate_marker_combinations(self, marker_config: Dict) -> List[str]:
        """生成标记组合"""
        combinations = []
        
        for category, markers in marker_config.items():
            for marker in markers:
                combinations.append(f"{category}:{marker}")
        
        return combinations
    
    def enhance_image_complete(self, image_path: str, mineru_info: Dict) -> Dict[str, Any]:
        """
        一次性生成完整的图片增强信息，避免重复
        
        :param image_path: 图片文件路径
        :param mineru_info: MinerU解析的图片信息
        :return: 完整的增强信息字典
        """
        try:
            logging.info(f"开始增强图片: {os.path.basename(image_path)}")
            
            # 步骤1: 调用视觉模型进行深度分析
            vision_response = self._call_vision_model(image_path)
            
            # 步骤2: 获取基础描述信息
            img_caption = mineru_info.get('img_caption', [])
            img_footnote = mineru_info.get('img_footnote', [])
            
            # 步骤3: 生成完整描述（避免重复）
            complete_description = self._generate_complete_description(
                img_caption, img_footnote, vision_response
            )
            
            # 步骤4: 提取分层描述
            layered_descriptions = self._extract_layered_descriptions(vision_response)
            
            # 步骤5: 提取结构化信息
            structured_info = self._extract_structured_info(vision_response)
            
            # 步骤6: 生成增强摘要
            enhancement_summary = self._generate_enhancement_summary(
                complete_description, layered_descriptions, structured_info
            )
            
            # 整合结果
            enhancement_result = {
                'enhancement_status': 'success',
                'enhancement_timestamp': int(time.time()),
                'enhancement_model': self.enhancement_model,
                'enhanced_description': complete_description,
                'layered_descriptions': layered_descriptions,
                'structured_info': structured_info,
                'enhancement_summary': enhancement_summary,
                'vision_analysis': {
                    'raw_response': vision_response,
                    'analysis_quality': self._assess_analysis_quality(vision_response)
                },
                'processing_metadata': {
                    'enhancement_version': '3.0.0',
                    'processing_pipeline': 'One_Time_Enhancement_Pipeline',
                    'optimization_features': [
                        'one_time_enhancement',
                        'smart_deduplication',
                        'complete_metadata',
                        'layered_analysis'
                    ]
                }
            }
            
            logging.info(f"图片增强完成: {os.path.basename(image_path)}")
            return enhancement_result
            
        except Exception as e:
            error_msg = f"图片增强失败: {str(e)}"
            logging.error(error_msg)
            self.failure_handler.record_failure(image_path, 'image_enhancement', str(e))
            
            # 返回回退描述
            return self._create_fallback_description(
                mineru_info.get('img_caption', []),
                mineru_info.get('img_footnote', []),
                str(e)
            )
    
    def _call_vision_model(self, image_path: str) -> str:
        """
        调用视觉模型进行深度分析 (DashScope qwen-vl-plus)
        """
        try:
            # 构建增强提示词
            enhanced_prompt = self._build_enhanced_prompt()
            
            # 调用DashScope API
            response = dashscope.MultiModalConversation.call(
                model=self.enhancement_model,
                messages=[
                    {
                        'role': 'user',
                        'content': [
                            {'image': image_path},
                            {'text': enhanced_prompt}
                        ]
                    }
                ]
            )
            
            if response.status_code == 200:
                return response.output.choices[0].message.content
            else:
                raise Exception(f"DashScope API调用失败: {response.message}")
                
        except Exception as e:
            logging.error(f"视觉模型调用失败: {e}")
            raise
    
    def _build_enhanced_prompt(self) -> str:
        """构建增强提示词"""
        prompt = """
请对这张图片进行全面的深度分析，包括以下方面：

1. 场景描述：详细描述图片的场景、环境、背景和整体氛围
2. 主体识别：识别图片中的主要物体、人物或元素
3. 动作状态：描述图片中发生的动作、行为或状态
4. 视觉特征：分析颜色、形状、纹理、光线等视觉特征
5. 空间关系：描述物体之间的位置关系、布局和组合
6. 细节观察：注意图片中的细节、标志、文字等
7. 情感表达：分析图片传达的情感、情绪或态度
8. 专业信息：识别可能的技术参数、业务信息或专业内容

请提供详细、准确、结构化的描述，避免重复信息，确保分析的完整性和专业性。
"""
        return prompt.strip()
    
    def _generate_complete_description(self, img_caption: List[str], img_footnote: List[str], vision_response: str) -> str:
        """
        智能生成完整描述（避免重复）
        """
        # 收集所有可用的描述信息
        all_descriptions = []
        
        # 添加MinerU的图片标题
        if img_caption:
            caption_text = ' '.join(img_caption)
            if caption_text.strip():
                all_descriptions.append(f"图片标题: {caption_text}")
        
        # 添加MinerU的图片脚注
        if img_footnote:
            footnote_text = ' '.join(img_footnote)
            if footnote_text.strip():
                all_descriptions.append(f"图片说明: {footnote_text}")
        
        # 添加视觉模型的分析结果
        if vision_response:
            # 应用智能去重
            cleaned_vision_response = self._apply_smart_deduplication(vision_response)
            all_descriptions.append(f"深度分析: {cleaned_vision_response}")
        
        # 合并所有描述
        if all_descriptions:
            complete_description = '\n\n'.join(all_descriptions)
            # 最终去重处理
            return self._apply_smart_deduplication(complete_description)
        else:
            return "图片内容描述"
    
    def _is_duplicate_content(self, content: str, reference: str) -> bool:
        """
        检查内容是否重复
        """
        if not content or not reference:
            return False
        
        # 简化的重复检测：检查关键短语
        content_words = set(content.lower().split())
        reference_words = set(reference.lower().split())
        
        # 计算重叠度
        overlap = len(content_words.intersection(reference_words))
        total_unique = len(content_words.union(reference_words))
        
        if total_unique == 0:
            return False
        
        overlap_ratio = overlap / total_unique
        return overlap_ratio > 0.7  # 70%以上重叠认为重复
    
    def _apply_smart_deduplication(self, text: str) -> str:
        """
        应用智能去重
        """
        if not text:
            return text
        
        # 移除重复行
        lines = text.split('\n')
        unique_lines = []
        seen_lines = set()
        
        for line in lines:
            line_clean = line.strip()
            if line_clean and line_clean not in seen_lines:
                unique_lines.append(line)
                seen_lines.add(line_clean)
        
        # 合并多余的空行
        deduplicated_text = '\n'.join(unique_lines)
        deduplicated_text = re.sub(r'\n{3,}', '\n\n', deduplicated_text)
        
        return deduplicated_text.strip()
    
    def _extract_layered_descriptions(self, vision_response: str) -> Dict[str, str]:
        """
        提取分层描述
        """
        if not vision_response:
            return {}
        
        layered_descriptions = {}
        
        # 根据标记提取分层信息
        for category, markers in self.processing_markers['layered_descriptions'].items():
            category_content = []
            
            for marker in markers:
                # 查找包含标记的内容
                pattern = rf'{marker}[：:]\s*(.*?)(?=\n|$)'
                matches = re.findall(pattern, vision_response)
                
                if matches:
                    category_content.extend(matches)
            
            if category_content:
                # 去重并合并
                unique_content = list(set(category_content))
                layered_descriptions[category] = '；'.join(unique_content)
        
        return layered_descriptions
    
    def _extract_structured_info(self, vision_response: str) -> Dict[str, str]:
        """
        提取结构化信息
        """
        if not vision_response:
            return {}
        
        structured_info = {}
        
        # 根据标记提取结构化信息
        for category, markers in self.processing_markers['structured_info'].items():
            category_content = []
            
            for marker in markers:
                # 查找包含标记的内容
                pattern = rf'{marker}[：:]\s*(.*?)(?=\n|$)'
                matches = re.findall(pattern, vision_response)
                
                if matches:
                    category_content.extend(matches)
            
            if category_content:
                # 去重并合并
                unique_content = list(set(category_content))
                structured_info[category] = '；'.join(unique_content)
        
        return structured_info
    
    def _generate_enhancement_summary(self, complete_description: str, layered_descriptions: Dict, structured_info: Dict) -> str:
        """
        生成增强摘要
        """
        summary_parts = []
        
        # 基础描述摘要
        if complete_description:
            # 取前100个字符作为摘要
            if len(complete_description) > 100:
                summary_parts.append(f"{complete_description[:100]}...")
            else:
                summary_parts.append(complete_description)
        
        # 分层描述摘要
        if layered_descriptions:
            layer_count = len(layered_descriptions)
            summary_parts.append(f"包含{layer_count}个层次的分析")
        
        # 结构化信息摘要
        if structured_info:
            info_count = len(structured_info)
            summary_parts.append(f"提取了{info_count}类结构化信息")
        
        if not summary_parts:
            summary_parts.append("图片增强分析完成")
        
        return "。".join(summary_parts) + "。"
    
    def _assess_analysis_quality(self, vision_response: str) -> Dict[str, Any]:
        """
        评估分析质量
        """
        if not vision_response:
            return {'quality_score': 0, 'quality_level': 'poor', 'issues': ['无分析内容']}
        
        quality_score = 0.0
        issues = []
        
        # 长度评估
        response_length = len(vision_response)
        if response_length > 500:
            quality_score += 0.3
        elif response_length > 200:
            quality_score += 0.2
        elif response_length > 100:
            quality_score += 0.1
        else:
            issues.append("分析内容过短")
        
        # 结构评估
        if '：' in vision_response or ':' in vision_response:
            quality_score += 0.3
        else:
            issues.append("缺乏结构化描述")
        
        # 细节评估
        detail_indicators = ['详细', '具体', '包括', '包含', '涉及']
        if any(indicator in vision_response for indicator in detail_indicators):
            quality_score += 0.2
        else:
            issues.append("描述不够详细")
        
        # 专业度评估
        professional_indicators = ['技术', '参数', '特征', '分析', '评估']
        if any(indicator in vision_response for indicator in professional_indicators):
            quality_score += 0.2
        else:
            issues.append("专业度不足")
        
        # 确定质量级别
        if quality_score >= 0.8:
            quality_level = 'excellent'
        elif quality_score >= 0.6:
            quality_level = 'good'
        elif quality_score >= 0.4:
            quality_level = 'fair'
        else:
            quality_level = 'poor'
        
        return {
            'quality_score': quality_score,
            'quality_level': quality_level,
            'issues': issues,
            'response_length': response_length,
            'has_structure': '：' in vision_response or ':' in vision_response,
            'has_details': any(indicator in vision_response for indicator in detail_indicators),
            'is_professional': any(indicator in vision_response for indicator in professional_indicators)
        }
    
    def _create_fallback_description(self, img_caption: List[str], img_footnote: List[str], error: str = None) -> Dict[str, Any]:
        """
        创建回退描述（当增强失败时）
        """
        # 收集可用的基础信息
        basic_descriptions = []
        
        if img_caption:
            basic_descriptions.extend(img_caption)
        
        if img_footnote:
            basic_descriptions.extend(img_footnote)
        
        # 生成基础描述
        if basic_descriptions:
            basic_description = ' '.join(basic_descriptions)
        else:
            basic_description = "图片内容描述"
        
        # 构建回退结果
        fallback_result = {
            'enhancement_status': 'failed',
            'enhancement_timestamp': int(time.time()),
            'enhancement_model': self.enhancement_model,
            'enhanced_description': basic_description,
            'layered_descriptions': {},
            'structured_info': {},
            'enhancement_summary': f"增强处理失败，使用基础描述: {basic_description}",
            'error': error,
            'fallback_used': True,
            'processing_metadata': {
                'enhancement_version': '3.0.0',
                'processing_pipeline': 'Fallback_Description_Pipeline',
                'optimization_features': ['fallback_handling', 'basic_description']
            }
        }
        
        return fallback_result
    
    def enhance_images_batch(self, images: List[Dict]) -> List[Dict[str, Any]]:
        """
        批量增强图片
        """
        enhanced_images = []
        
        for i, image_info in enumerate(images):
            try:
                # 获取图片路径
                image_path = image_info.get('img_path', '')
                if not image_path:
                    logging.warning(f"图片 {i+1} 缺少路径信息")
                    continue
                
                # 检查图片文件是否存在
                if not os.path.exists(image_path):
                    logging.warning(f"图片文件不存在: {image_path}")
                    continue
                
                # 执行增强
                enhancement_result = self.enhance_image_complete(image_path, image_info)
                enhanced_images.append(enhancement_result)
                
                # API限流控制
                if (i + 1) % self.batch_size == 0 and i < len(images) - 1:
                    logging.info(f"批量处理进度: {i+1}/{len(images)}，等待 {self.delay_seconds} 秒...")
                    time.sleep(self.delay_seconds)
                
            except Exception as e:
                error_msg = f"批量增强图片 {i+1} 失败: {str(e)}"
                logging.error(error_msg)
                self.failure_handler.record_failure(image_info, 'batch_image_enhancement', str(e))
                
                # 创建错误结果
                error_result = self._create_fallback_description(
                    image_info.get('img_caption', []),
                    image_info.get('img_footnote', []),
                    str(e)
                )
                enhanced_images.append(error_result)
        
        logging.info(f"批量图片增强完成: {len(enhanced_images)}/{len(images)} 成功")
        return enhanced_images
    
    def get_enhancement_status(self) -> Dict[str, Any]:
        """获取增强器状态"""
        return {
            'enhancer_type': 'image_enhancer',
            'status': 'ready',
            'enhancement_model': self.enhancement_model,
            'batch_size': self.batch_size,
            'delay_seconds': self.delay_seconds,
            'capabilities': [
                'one_time_enhancement',
                'smart_deduplication',
                'layered_analysis',
                'structured_extraction',
                'batch_processing',
                'fallback_handling'
            ],
            'version': '3.0.0'
        }
    
    def get_processing_markers(self) -> Dict[str, Any]:
        """获取处理标记信息"""
        return {
            'layered_descriptions': self.processing_markers['layered_descriptions'],
            'structured_info': self.processing_markers['structured_info'],
            'marker_combinations': self.marker_combinations,
            'total_markers': len(self.marker_combinations)
        }
