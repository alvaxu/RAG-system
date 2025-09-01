'''
程序说明：
## 1. 智能后处理引擎，基于LLM答案对结果进行最终过滤
## 2. 支持图片、文本、表格的统一过滤策略
## 3. 基于关键词匹配和相关性计算进行智能筛选
## 4. 可配置的过滤参数和阈值
'''

import logging
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class FilteringResult:
    """过滤结果数据类"""
    filtered_images: List[Any]
    filtered_texts: List[Any]
    filtered_tables: List[Any]
    filtering_metrics: Dict[str, Any]


class IntelligentPostProcessingEngine:
    """智能后处理引擎"""
    
    def __init__(self, config):
        """
        初始化智能后处理引擎
        
        :param config: 智能后处理配置
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.logger.info("智能后处理引擎初始化完成")
    
    def process(self, llm_answer: str, all_results: Dict[str, List[Any]]) -> FilteringResult:
        """
        基于LLM答案进行智能后处理
        
        :param llm_answer: LLM生成的答案
        :param all_results: 包含所有类型结果的字典
        :return: 过滤后的结果
        """
        try:
            self.logger.info(f"开始智能后处理，LLM答案长度: {len(llm_answer)}")
            
            # 从LLM答案中提取关键词
            keywords = self._extract_keywords_from_llm(llm_answer)
            self.logger.info(f"从LLM答案提取关键词: {keywords}")
            
            # 过滤各类型结果
            filtered_results = FilteringResult(
                filtered_images=[],
                filtered_texts=[],
                filtered_tables=[],
                filtering_metrics={}
            )
            
            # 过滤图片结果
            if self.config.enable_image_filtering and 'image' in all_results:
                filtered_results.filtered_images = self._filter_images(
                    all_results['image'], keywords
                )
            
            # 过滤文本结果
            if self.config.enable_text_filtering and 'text' in all_results:
                filtered_results.filtered_texts = self._filter_texts(
                    all_results['text'], keywords
                )
            
            # 过滤表格结果
            if self.config.enable_table_filtering and 'table' in all_results:
                filtered_results.filtered_tables = self._filter_tables(
                    all_results['table'], keywords
                )
            
            # 收集过滤指标
            filtered_results.filtering_metrics = {
                'input_images': len(all_results.get('image', [])),
                'output_images': len(filtered_results.filtered_images),
                'input_texts': len(all_results.get('text', [])),
                'output_texts': len(filtered_results.filtered_texts),
                'input_tables': len(all_results.get('table', [])),
                'output_tables': len(filtered_results.filtered_tables),
                'extracted_keywords': keywords
            }
            
            self.logger.info(f"智能后处理完成，过滤指标: {filtered_results.filtering_metrics}")
            return filtered_results
            
        except Exception as e:
            self.logger.error(f"智能后处理过程中发生错误: {str(e)}")
            # 返回原始结果
            return FilteringResult(
                filtered_images=all_results.get('image', []),
                filtered_texts=all_results.get('text', []),
                filtered_tables=all_results.get('table', []),
                filtering_metrics={'error': str(e)}
            )
    
    def _extract_keywords_from_llm(self, llm_answer: str) -> List[str]:
        """
        从LLM答案中提取关键词
        
        :param llm_answer: LLM生成的答案
        :return: 关键词列表
        """
        keywords = []
        
        try:
            # 提取图片标题
            title_matches = re.findall(r'图\d+[：:]\s*([^，。\n]+)', llm_answer)
            keywords.extend(title_matches)
            
            # 提取公司名称
            company_keywords = ['中芯国际', 'SMIC', '公司', '企业', '集团']
            for keyword in company_keywords:
                if keyword in llm_answer:
                    keywords.append(keyword)
            
            # 提取图表类型
            chart_keywords = ['柱状图', '折线图', '饼图', '复合图表', '图表', '数据图']
            for keyword in chart_keywords:
                if keyword in llm_answer:
                    keywords.append(keyword)
            
            # 提取时间范围
            time_matches = re.findall(r'\d{4}年[到至]\d{4}年', llm_answer)
            keywords.extend(time_matches)
            
            # 提取财务指标
            finance_keywords = ['净利润', '营收', '收入', '利润', '财务', '业绩', '增长']
            for keyword in finance_keywords:
                if keyword in llm_answer:
                    keywords.append(keyword)
            
            # 去重
            keywords = list(set(keywords))
            
            self.logger.debug(f"从LLM答案提取关键词: {keywords}")
            return keywords
            
        except Exception as e:
            self.logger.error(f"关键词提取失败: {str(e)}")
            return []
    
    def _filter_images(self, images: List[Any], keywords: List[str]) -> List[Any]:
        """
        过滤图片结果
        
        :param images: 图片结果列表
        :param keywords: 关键词列表
        :return: 过滤后的图片列表
        """
        if not images or not keywords:
            return images
        
        try:
            # 计算每张图片的相关性分数
            scored_images = []
            for img in images:
                relevance_score = self._calculate_image_relevance(img, keywords)
                scored_images.append((img, relevance_score))
            
            # 按相关性排序
            scored_images.sort(key=lambda x: x[1], reverse=True)
            
            # 只保留最相关的图片
            max_images = min(self.config.max_images_to_keep, len(scored_images))
            filtered_images = [img for img, score in scored_images[:max_images]]
            
            self.logger.info(f"图片过滤：从 {len(images)} 张过滤到 {len(filtered_images)} 张")
            return filtered_images
            
        except Exception as e:
            self.logger.error(f"图片过滤失败: {str(e)}")
            return images
    
    def _filter_texts(self, texts: List[Any], keywords: List[str]) -> List[Any]:
        """
        过滤文本结果
        
        :param texts: 文本结果列表
        :param keywords: 关键词列表
        :return: 过滤后的文本列表
        """
        if not texts or not keywords:
            return texts
        
        try:
            # 计算每个文本的相关性分数
            scored_texts = []
            for text in texts:
                relevance_score = self._calculate_text_relevance(text, keywords)
                scored_texts.append((text, relevance_score))
            
            # 按相关性排序
            scored_texts.sort(key=lambda x: x[1], reverse=True)
            
            # 只保留最相关的文本
            max_texts = min(self.config.max_texts_to_keep, len(scored_texts))
            filtered_texts = [text for text, score in scored_texts[:max_texts]]
            
            self.logger.info(f"文本过滤：从 {len(texts)} 个过滤到 {len(filtered_texts)} 个")
            return filtered_texts
            
        except Exception as e:
            self.logger.error(f"文本过滤失败: {str(e)}")
            return texts
    
    def _filter_tables(self, tables: List[Any], keywords: List[str]) -> List[Any]:
        """
        过滤表格结果
        
        :param tables: 表格结果列表
        :param keywords: 关键词列表
        :return: 过滤后的表格列表
        """
        if not tables or not keywords:
            return tables
        
        try:
            # 计算每个表格的相关性分数
            scored_tables = []
            for table in tables:
                relevance_score = self._calculate_table_relevance(table, keywords)
                scored_tables.append((table, relevance_score))
            
            # 按相关性排序
            scored_tables.sort(key=lambda x: x[1], reverse=True)
            
            # 只保留最相关的表格
            max_tables = min(self.config.max_tables_to_keep, len(scored_tables))
            filtered_tables = [table for table, score in scored_tables[:max_tables]]
            
            self.logger.info(f"表格过滤：从 {len(tables)} 个过滤到 {len(filtered_tables)} 个")
            return filtered_tables
            
        except Exception as e:
            self.logger.error(f"表格过滤失败: {str(e)}")
            return tables
    
    def _calculate_image_relevance(self, image: Any, keywords: List[str]) -> float:
        """
        计算图片与关键词的相关性分数
        
        :param image: 图片对象
        :param keywords: 关键词列表
        :return: 相关性分数
        """
        score = 0.0
        
        try:
            caption = image.get('caption', '')
            enhanced_desc = image.get('enhanced_description', '')
            title = image.get('title', '')
            
            # 计算关键词匹配分数
            for keyword in keywords:
                keyword_lower = keyword.lower()
                
                # 标题匹配权重最高
                if keyword_lower in str(title).lower():
                    score += 0.8
                
                # 说明文字匹配
                if keyword_lower in str(caption).lower():
                    score += 0.5
                
                # 增强描述匹配
                if keyword_lower in str(enhanced_desc).lower():
                    score += 0.3
            
            return score
            
        except Exception as e:
            self.logger.error(f"计算图片相关性分数失败: {str(e)}")
            return 0.0
    
    def _calculate_text_relevance(self, text: Any, keywords: List[str]) -> float:
        """
        计算文本与关键词的相关性分数
        
        :param text: 文本对象
        :param keywords: 关键词列表
        :return: 相关性分数
        """
        score = 0.0
        
        try:
            content = text.get('content', '')
            title = text.get('title', '')
            
            # 计算关键词匹配分数
            for keyword in keywords:
                keyword_lower = keyword.lower()
                
                # 标题匹配权重最高
                if keyword_lower in str(title).lower():
                    score += 0.7
                
                # 内容匹配
                if keyword_lower in str(content).lower():
                    score += 0.4
            
            return score
            
        except Exception as e:
            self.logger.error(f"计算文本相关性分数失败: {str(e)}")
            return 0.0
    
    def _calculate_table_relevance(self, table: Any, keywords: List[str]) -> float:
        """
        计算表格与关键词的相关性分数
        
        :param table: 表格对象
        :param keywords: 关键词列表
        :return: 相关性分数
        """
        score = 0.0
        
        try:
            title = table.get('title', '')
            content = table.get('content', '')
            headers = table.get('headers', [])
            
            # 计算关键词匹配分数
            for keyword in keywords:
                keyword_lower = keyword.lower()
                
                # 标题匹配权重最高
                if keyword_lower in str(title).lower():
                    score += 0.8
                
                # 表头匹配
                for header in headers:
                    if keyword_lower in str(header).lower():
                        score += 0.6
                
                # 内容匹配
                if keyword_lower in str(content).lower():
                    score += 0.4
            
            return score
            
        except Exception as e:
            self.logger.error(f"计算表格相关性分数失败: {str(e)}")
            return 0.0
