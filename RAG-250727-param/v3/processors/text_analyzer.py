'''
程序说明：
## 1. TextAnalyzer子模块
- 负责文本结构分析，包括段落、句子、关键词等
- 完全符合设计文档规范，位于processors模块下
- 为TextProcessor提供文本分析服务
## 2. 主要功能
- 分析文本结构（段落、句子、关键词）
- 识别文本类型和特征
- 检测文本的规律性和语义特征
- 为后续处理提供结构信息
## 3. 与优化方案的关系
- 实现优化方案要求的模块化设计
- 支持大文本的智能分块处理
- 完全符合设计文档的TEXT_METADATA_SCHEMA规范
'''
import re
import logging
from typing import Dict, List, Any
import time

class TextAnalyzer:
    """
    文本分析器
    负责文本结构分析，包括段落、句子、关键词等
    完全符合设计文档规范，位于processors模块下
    """
    
    def __init__(self):
        logging.info("文本分析器初始化完成")
    
    def analyze(self, text_data: Dict) -> Dict[str, Any]:
        """
        分析文本结构，包括段落、句子、关键词等
        
        :param text_data: 文本数据，包含text_content等字段
        :return: 分析结果字典
        """
        try:
            text_content = text_data.get('text_content', '')
            if not text_content:
                return self._create_empty_analysis_result()
            
            # 步骤1: 基础结构分析
            structure_info = self._analyze_text_structure(text_content)
            
            # 步骤2: 特征分析
            features_info = self._analyze_text_features(text_content, structure_info)
            
            # 步骤3: 语义分析
            semantic_info = self._analyze_semantic_features(text_content, structure_info)
            
            # 步骤4: 智能检测
            detection_info = self._detect_text_patterns(text_content, structure_info)
            
            # 整合分析结果
            analysis_result = {
                'analysis_status': 'success',
                'analysis_timestamp': int(time.time()),
                'structure': structure_info,
                'features': features_info,
                'semantic': semantic_info,
                'detection': detection_info,
                'summary': self._generate_analysis_summary(structure_info, features_info, semantic_info)
            }
            
            logging.info(f"文本分析完成: {structure_info.get('paragraphs', 0)}段落, {structure_info.get('sentences', 0)}句子")
            return analysis_result
            
        except Exception as e:
            error_msg = f"文本分析失败: {str(e)}"
            logging.error(error_msg)
            return self._create_error_analysis_result(error_msg)
    
    def _analyze_text_structure(self, text_content: str) -> Dict[str, Any]:
        """
        分析段落、句子、单词、字符数量等
        """
        if not text_content:
            return {'paragraphs': 0, 'sentences': 0, 'words': 0, 'characters': 0}
        
        # 字符统计
        total_chars = len(text_content)
        non_space_chars = len([c for c in text_content if not c.isspace()])
        
        # 段落统计
        paragraphs = [p.strip() for p in text_content.split('\n\n') if p.strip()]
        paragraph_count = len(paragraphs)
        
        # 句子统计
        sentences = self._split_into_sentences(text_content)
        sentence_count = len(sentences)
        
        # 单词统计
        words = self._split_into_words(text_content)
        word_count = len(words)
        unique_words = len(set(words))
        
        # 行统计
        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
        line_count = len(lines)
        
        # 计算平均长度
        avg_paragraph_length = sum(len(p) for p in paragraphs) / paragraph_count if paragraph_count > 0 else 0
        avg_sentence_length = sum(len(s) for s in sentences) / sentence_count if sentence_count > 0 else 0
        avg_word_length = sum(len(w) for w in words) / word_count if word_count > 0 else 0
        
        return {
            'paragraphs': paragraph_count,
            'sentences': sentence_count,
            'words': word_count,
            'unique_words': unique_words,
            'characters': total_chars,
            'non_space_chars': non_space_chars,
            'lines': line_count,
            'avg_paragraph_length': avg_paragraph_length,
            'avg_sentence_length': avg_sentence_length,
            'avg_word_length': avg_word_length,
            'word_diversity': unique_words / word_count if word_count > 0 else 0
        }
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        智能分割句子
        """
        if not text:
            return []
        
        # 使用多种句子结束符
        sentence_endings = r'[.!?。！？]+'
        sentences = re.split(sentence_endings, text)
        
        # 清理和过滤
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 5:  # 过滤太短的句子
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences
    
    def _split_into_words(self, text: str) -> List[str]:
        """
        智能分割单词
        """
        if not text:
            return []
        
        # 移除标点符号，分割单词
        words = re.findall(r'\b[a-zA-Z\u4e00-\u9fff]+\b', text)
        
        # 过滤太短的单词
        filtered_words = [word for word in words if len(word) > 1]
        
        return filtered_words
    
    def _analyze_text_features(self, text_content: str, structure_info: Dict) -> Dict[str, Any]:
        """
        确定文本类型、结构化程度、语言等
        """
        if not text_content:
            return {}
        
        # 1. 文本类型判断
        text_type = self._determine_text_type(text_content, structure_info)
        
        # 2. 结构化程度分析
        structure_level = self._analyze_structure_level(text_content, structure_info)
        
        # 3. 语言检测
        language_info = self._detect_language(text_content)
        
        # 4. 数字和特殊字符分析
        special_chars_info = self._analyze_special_characters(text_content)
        
        # 5. 复杂度评分
        complexity_score = self._calculate_text_complexity(structure_info, special_chars_info)
        
        return {
            'text_type': text_type,
            'is_structured': structure_level['is_structured'],
            'structure_level': structure_level['level'],
            'language': language_info['primary_language'],
            'language_confidence': language_info['confidence'],
            'has_numbers': special_chars_info['has_numbers'],
            'has_special_chars': special_chars_info['has_special_chars'],
            'complexity_score': complexity_score,
            'readability_score': self._calculate_readability_score(structure_info)
        }
    
    def _determine_text_type(self, text_content: str, structure_info: Dict) -> str:
        """确定文本类型"""
        paragraphs = structure_info.get('paragraphs', 0)
        sentences = structure_info.get('sentences', 0)
        words = structure_info.get('words', 0)
        
        # 检查是否为标题
        if paragraphs <= 1 and sentences <= 2 and words <= 20:
            return 'title'
        
        # 检查是否为摘要
        if paragraphs <= 3 and sentences <= 10 and words <= 100:
            return 'summary'
        
        # 检查是否为列表
        if self._is_list_text(text_content):
            return 'list'
        
        # 检查是否为表格描述
        if self._is_table_description(text_content):
            return 'table_description'
        
        # 检查是否为正文
        if paragraphs > 5 and sentences > 20:
            return 'body_text'
        
        # 检查是否为段落
        if paragraphs > 1 and sentences > 5:
            return 'paragraphs'
        
        return 'general'
    
    def _is_list_text(self, text: str) -> bool:
        """检查是否为列表文本"""
        lines = text.split('\n')
        list_indicators = 0
        
        for line in lines:
            line = line.strip()
            if re.match(r'^[\d\-•\*]\s+', line):
                list_indicators += 1
            elif re.match(r'^[一二三四五六七八九十]+[、.]', line):
                list_indicators += 1
        
        return list_indicators > len(lines) * 0.3
    
    def _is_table_description(self, text: str) -> bool:
        """检查是否为表格描述"""
        table_keywords = ['表格', '表', '数据', '统计', '指标', '参数', '属性']
        return any(keyword in text for keyword in table_keywords)
    
    def _analyze_structure_level(self, text_content: str, structure_info: Dict) -> Dict[str, Any]:
        """分析文本的结构化程度"""
        paragraphs = structure_info.get('paragraphs', 0)
        sentences = structure_info.get('sentences', 0)
        avg_paragraph_length = structure_info.get('avg_paragraph_length', 0)
        
        # 结构化指标
        structure_score = 0
        
        # 段落数量评分
        if paragraphs >= 5:
            structure_score += 0.3
        elif paragraphs >= 3:
            structure_score += 0.2
        elif paragraphs >= 1:
            structure_score += 0.1
        
        # 句子数量评分
        if sentences >= 20:
            structure_score += 0.3
        elif sentences >= 10:
            structure_score += 0.2
        elif sentences >= 5:
            structure_score += 0.1
        
        # 段落长度一致性评分
        if avg_paragraph_length > 100 and avg_paragraph_length < 500:
            structure_score += 0.2
        
        # 检查是否有标题结构
        if self._has_title_structure(text_content):
            structure_score += 0.2
        
        # 确定结构化级别
        if structure_score >= 0.8:
            level = 'high'
            is_structured = True
        elif structure_score >= 0.5:
            level = 'medium'
            is_structured = True
        else:
            level = 'low'
            is_structured = False
        
        return {
            'level': level,
            'is_structured': is_structured,
            'structure_score': structure_score,
            'indicators': {
                'paragraphs': paragraphs,
                'sentences': sentences,
                'avg_paragraph_length': avg_paragraph_length,
                'has_title_structure': self._has_title_structure(text_content)
            }
        }
    
    def _has_title_structure(self, text: str) -> bool:
        """检查是否有标题结构"""
        lines = text.split('\n')
        title_indicators = 0
        
        for line in lines:
            line = line.strip()
            # 检查是否为标题行
            if (len(line) < 50 and 
                (line.isupper() or 
                 re.match(r'^[一二三四五六七八九十]+[、.]', line) or
                 re.match(r'^\d+[、.]', line))):
                title_indicators += 1
        
        return title_indicators > 0
    
    def _detect_language(self, text: str) -> Dict[str, Any]:
        """检测文本语言"""
        # 简化的语言检测
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        total_chars = len(text)
        
        if total_chars == 0:
            return {'primary_language': 'unknown', 'confidence': 0.0}
        
        chinese_ratio = chinese_chars / total_chars
        english_ratio = english_chars / total_chars
        
        if chinese_ratio > 0.5:
            primary_language = 'chinese'
            confidence = chinese_ratio
        elif english_ratio > 0.5:
            primary_language = 'english'
            confidence = english_ratio
        elif chinese_ratio > 0.3 and english_ratio > 0.3:
            primary_language = 'mixed'
            confidence = max(chinese_ratio, english_ratio)
        else:
            primary_language = 'unknown'
            confidence = 0.0
        
        return {
            'primary_language': primary_language,
            'confidence': confidence,
            'chinese_ratio': chinese_ratio,
            'english_ratio': english_ratio,
            'chinese_chars': chinese_chars,
            'english_chars': english_chars
        }
    
    def _analyze_special_characters(self, text: str) -> Dict[str, Any]:
        """分析特殊字符"""
        # 数字检测
        numbers = re.findall(r'\d+', text)
        has_numbers = len(numbers) > 0
        number_count = len(numbers)
        
        # 特殊字符检测
        special_chars = re.findall(r'[^\w\s\u4e00-\u9fff]', text)
        has_special_chars = len(special_chars) > 0
        special_char_count = len(special_chars)
        
        # 标点符号检测
        punctuation = re.findall(r'[，。！？；：""''（）【】]', text)
        punctuation_count = len(punctuation)
        
        # 数学符号检测
        math_symbols = re.findall(r'[+\-*/=<>≤≥≠≈±∞∑∏∫∂√]', text)
        math_symbol_count = len(math_symbols)
        
        return {
            'has_numbers': has_numbers,
            'number_count': number_count,
            'has_special_chars': has_special_chars,
            'special_char_count': special_char_count,
            'punctuation_count': punctuation_count,
            'math_symbol_count': math_symbol_count,
            'special_char_ratio': special_char_count / len(text) if text else 0
        }
    
    def _calculate_text_complexity(self, structure_info: Dict, special_chars_info: Dict) -> float:
        """计算文本复杂度评分"""
        score = 0.0
        
        # 结构复杂度
        paragraphs = structure_info.get('paragraphs', 0)
        sentences = structure_info.get('sentences', 0)
        words = structure_info.get('words', 0)
        
        if paragraphs > 10:
            score += 0.2
        elif paragraphs > 5:
            score += 0.1
        
        if sentences > 50:
            score += 0.2
        elif sentences > 20:
            score += 0.1
        
        if words > 500:
            score += 0.2
        elif words > 200:
            score += 0.1
        
        # 词汇复杂度
        word_diversity = structure_info.get('word_diversity', 0)
        if word_diversity > 0.8:
            score += 0.2
        elif word_diversity > 0.6:
            score += 0.1
        
        # 特殊字符复杂度
        special_char_ratio = special_chars_info.get('special_char_ratio', 0)
        if special_char_ratio > 0.1:
            score += 0.2
        elif special_char_ratio > 0.05:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_readability_score(self, structure_info: Dict) -> float:
        """计算可读性评分"""
        avg_sentence_length = structure_info.get('avg_sentence_length', 0)
        avg_word_length = structure_info.get('avg_word_length', 0)
        
        # 基于句子长度的可读性
        if avg_sentence_length < 20:
            sentence_score = 0.8
        elif avg_sentence_length < 30:
            sentence_score = 0.6
        elif avg_sentence_length < 40:
            sentence_score = 0.4
        else:
            sentence_score = 0.2
        
        # 基于单词长度的可读性
        if avg_word_length < 5:
            word_score = 0.8
        elif avg_word_length < 7:
            word_score = 0.6
        elif avg_word_length < 9:
            word_score = 0.4
        else:
            word_score = 0.2
        
        # 综合评分
        readability_score = (sentence_score + word_score) / 2
        
        return readability_score
    
    def _analyze_semantic_features(self, text_content: str, structure_info: Dict) -> Dict[str, Any]:
        """
        提取关键主题、短语、情感、正式程度等
        """
        if not text_content:
            return {}
        
        # 1. 关键主题提取
        key_topics = self._extract_key_topics(text_content)
        
        # 2. 关键短语提取
        key_phrases = self._extract_key_phrases(text_content)
        
        # 3. 情感分析
        sentiment_info = self._analyze_sentiment(text_content)
        
        # 4. 正式程度分析
        formality_level = self._analyze_formality(text_content)
        
        # 5. 专业术语检测
        technical_terms = self._detect_technical_terms(text_content)
        
        return {
            'key_topics': key_topics,
            'key_phrases': key_phrases,
            'sentiment': sentiment_info['sentiment'],
            'sentiment_score': sentiment_info['score'],
            'formality': formality_level['level'],
            'formality_score': formality_level['score'],
            'technical_terms': technical_terms,
            'semantic_complexity': self._calculate_semantic_complexity(key_topics, technical_terms)
        }
    
    def _extract_key_topics(self, text: str) -> List[str]:
        """提取关键主题"""
        # 简化的主题提取：基于高频词汇
        words = self._split_into_words(text)
        if not words:
            return []
        
        # 过滤停用词
        stop_words = {'的', '是', '在', '有', '和', '与', '或', '但', '而', '如果', '因为', '所以', '这个', '那个', '这些', '那些'}
        filtered_words = [word for word in words if word not in stop_words and len(word) > 1]
        
        # 统计词频
        from collections import Counter
        word_counts = Counter(filtered_words)
        
        # 返回前5个高频词作为主题
        topics = [word for word, count in word_counts.most_common(5)]
        
        return topics
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """提取关键短语"""
        # 简化的短语提取：基于常见模式
        phrases = []
        
        # 提取"的"字短语
        de_phrases = re.findall(r'[\u4e00-\u9fff]+的[\u4e00-\u9fff]+', text)
        phrases.extend(de_phrases[:3])
        
        # 提取数字+单位短语
        number_phrases = re.findall(r'\d+[年月日时分秒个件条张]', text)
        phrases.extend(number_phrases[:3])
        
        # 提取英文短语
        english_phrases = re.findall(r'\b[a-zA-Z]+\s+[a-zA-Z]+\b', text)
        phrases.extend(english_phrases[:3])
        
        return phrases[:5]  # 最多返回5个短语
    
    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """分析情感倾向"""
        # 简化的情感分析
        positive_words = ['好', '优秀', '成功', '积极', '正面', '满意', '高兴', '喜欢', '支持', '推荐']
        negative_words = ['差', '失败', '消极', '负面', '不满', '失望', '讨厌', '反对', '批评', '问题']
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            sentiment = 'positive'
            score = positive_count / (positive_count + negative_count) if (positive_count + negative_count) > 0 else 0.5
        elif negative_count > positive_count:
            sentiment = 'negative'
            score = negative_count / (positive_count + negative_count) if (positive_count + negative_count) > 0 else 0.5
        else:
            sentiment = 'neutral'
            score = 0.5
        
        return {
            'sentiment': sentiment,
            'score': score,
            'positive_count': positive_count,
            'negative_count': negative_count
        }
    
    def _analyze_formality(self, text: str) -> Dict[str, Any]:
        """分析正式程度"""
        # 正式词汇
        formal_words = ['因此', '然而', '此外', '综上所述', '根据', '依据', '规定', '要求', '必须', '应当']
        # 非正式词汇
        informal_words = ['哈哈', '呵呵', '嗯', '啊', '哦', '哎', '哇', '太棒了', '好棒', '厉害']
        
        formal_count = sum(1 for word in formal_words if word in text)
        informal_count = sum(1 for word in informal_words if word in text)
        
        # 计算正式程度
        total_words = len(self._split_into_words(text))
        if total_words == 0:
            formality_score = 0.5
        else:
            formality_score = formal_count / (formal_count + informal_count + 1)
        
        # 确定正式级别
        if formality_score > 0.7:
            level = 'formal'
        elif formality_score > 0.4:
            level = 'neutral'
        else:
            level = 'informal'
        
        return {
            'level': level,
            'score': formality_score,
            'formal_count': formal_count,
            'informal_count': informal_count
        }
    
    def _detect_technical_terms(self, text: str) -> List[str]:
        """检测专业术语"""
        # 简化的专业术语检测
        technical_patterns = [
            r'\b[A-Z]{2,}\b',  # 大写缩写
            r'\d+[%％]',       # 百分比
            r'\d+[°度]',       # 角度
            r'[\u4e00-\u9fff]+[系统|技术|方法|理论|模型|算法|协议|标准|规范]',  # 中文专业术语
        ]
        
        technical_terms = []
        for pattern in technical_patterns:
            matches = re.findall(pattern, text)
            technical_terms.extend(matches)
        
        # 去重并限制数量
        unique_terms = list(set(technical_terms))
        return unique_terms[:10]  # 最多返回10个术语
    
    def _calculate_semantic_complexity(self, key_topics: List[str], technical_terms: List[str]) -> float:
        """计算语义复杂度"""
        score = 0.0
        
        # 主题复杂度
        if len(key_topics) > 5:
            score += 0.3
        elif len(key_topics) > 3:
            score += 0.2
        elif len(key_topics) > 1:
            score += 0.1
        
        # 专业术语复杂度
        if len(technical_terms) > 5:
            score += 0.4
        elif len(technical_terms) > 3:
            score += 0.3
        elif len(technical_terms) > 1:
            score += 0.2
        
        # 词汇多样性
        if len(set(key_topics + technical_terms)) > 10:
            score += 0.3
        elif len(set(key_topics + technical_terms)) > 5:
            score += 0.2
        
        return min(score, 1.0)
    
    def _detect_text_patterns(self, text_content: str, structure_info: Dict) -> Dict[str, Any]:
        """
        检测文本的模式和规律
        """
        if not text_content:
            return {}
        
        # 检测重复模式
        repetition_patterns = self._detect_repetition_patterns(text_content)
        
        # 检测格式化模式
        formatting_patterns = self._detect_formatting_patterns(text_content)
        
        # 检测结构模式
        structure_patterns = self._detect_structure_patterns(text_content, structure_info)
        
        return {
            'repetition_patterns': repetition_patterns,
            'formatting_patterns': formatting_patterns,
            'structure_patterns': structure_patterns,
            'pattern_summary': self._generate_pattern_summary(repetition_patterns, formatting_patterns, structure_patterns)
        }
    
    def _detect_repetition_patterns(self, text: str) -> Dict[str, Any]:
        """检测重复模式"""
        # 检测重复句子
        sentences = self._split_into_sentences(text)
        sentence_hashes = [hash(sentence) for sentence in sentences]
        
        from collections import Counter
        hash_counts = Counter(sentence_hashes)
        duplicate_sentences = {h: c for h, c in hash_counts.items() if c > 1}
        
        # 检测重复短语
        words = self._split_into_words(text)
        word_counts = Counter(words)
        frequent_words = {word: count for word, count in word_counts.items() if count > 3}
        
        return {
            'has_duplicates': len(duplicate_sentences) > 0,
            'duplicate_sentences': len(duplicate_sentences),
            'frequent_words': len(frequent_words),
            'repetition_score': len(duplicate_sentences) / len(sentences) if sentences else 0
        }
    
    def _detect_formatting_patterns(self, text: str) -> Dict[str, Any]:
        """检测格式化模式"""
        patterns = {}
        
        # 检测标题模式
        title_patterns = re.findall(r'^[一二三四五六七八九十]+[、.].*$', text, re.MULTILINE)
        patterns['title_patterns'] = len(title_patterns)
        
        # 检测列表模式
        list_patterns = re.findall(r'^[\d\-•\*]\s+.*$', text, re.MULTILINE)
        patterns['list_patterns'] = len(list_patterns)
        
        # 检测引用模式
        quote_patterns = re.findall(r'[""''].*[""'']', text)
        patterns['quote_patterns'] = len(quote_patterns)
        
        # 检测代码模式
        code_patterns = re.findall(r'`.*?`', text)
        patterns['code_patterns'] = len(code_patterns)
        
        return patterns
    
    def _detect_structure_patterns(self, text: str, structure_info: Dict) -> Dict[str, Any]:
        """检测结构模式"""
        patterns = {}
        
        # 段落长度模式
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        if paragraphs:
            paragraph_lengths = [len(p) for p in paragraphs]
            patterns['paragraph_length_variation'] = max(paragraph_lengths) - min(paragraph_lengths)
            patterns['paragraph_length_consistency'] = len(set(paragraph_lengths)) <= 2
        
        # 句子长度模式
        sentences = self._split_into_sentences(text)
        if sentences:
            sentence_lengths = [len(s) for s in sentences]
            patterns['sentence_length_variation'] = max(sentence_lengths) - min(sentence_lengths)
            patterns['sentence_length_consistency'] = len(set(sentence_lengths)) <= 3
        
        return patterns
    
    def _generate_pattern_summary(self, repetition_patterns: Dict, formatting_patterns: Dict, structure_patterns: Dict) -> str:
        """生成模式总结"""
        summary_parts = []
        
        if repetition_patterns.get('has_duplicates'):
            summary_parts.append("包含重复内容")
        
        if formatting_patterns.get('title_patterns', 0) > 0:
            summary_parts.append("包含标题结构")
        
        if formatting_patterns.get('list_patterns', 0) > 0:
            summary_parts.append("包含列表格式")
        
        if structure_patterns.get('paragraph_length_consistency'):
            summary_parts.append("段落长度一致")
        
        if not summary_parts:
            summary_parts.append("无特殊模式")
        
        return "，".join(summary_parts)
    
    def _generate_analysis_summary(self, structure_info: Dict, features_info: Dict, semantic_info: Dict) -> str:
        """生成分析总结"""
        paragraphs = structure_info.get('paragraphs', 0)
        sentences = structure_info.get('sentences', 0)
        words = structure_info.get('words', 0)
        text_type = features_info.get('text_type', 'unknown')
        complexity = features_info.get('complexity_score', 0)
        
        summary = f"{paragraphs}段落，{sentences}句子，{words}单词的{text_type}"
        
        if complexity > 0.7:
            summary += "，复杂度较高"
        elif complexity > 0.4:
            summary += "，复杂度中等"
        else:
            summary += "，复杂度较低"
        
        # 添加语义信息
        sentiment = semantic_info.get('sentiment', 'neutral')
        if sentiment != 'neutral':
            summary += f"，情感倾向{sentiment}"
        
        formality = semantic_info.get('formality', 'neutral')
        if formality != 'neutral':
            summary += f"，{formality}风格"
        
        return summary
    
    def _create_empty_analysis_result(self) -> Dict[str, Any]:
        """创建空文本的分析结果"""
        return {
            'analysis_status': 'success',
            'analysis_timestamp': int(time.time()),
            'structure': {'paragraphs': 0, 'sentences': 0, 'words': 0, 'characters': 0},
            'features': {'text_type': 'empty', 'complexity_score': 0.0},
            'semantic': {'sentiment': 'neutral', 'formality': 'neutral'},
            'detection': {'repetition_patterns': {}, 'formatting_patterns': {}, 'structure_patterns': {}},
            'summary': '空文本'
        }
    
    def _create_error_analysis_result(self, error_message: str) -> Dict[str, Any]:
        """创建错误分析结果"""
        return {
            'analysis_status': 'failed',
            'analysis_timestamp': int(time.time()),
            'error_message': error_message,
            'structure': {'paragraphs': 0, 'sentences': 0, 'words': 0, 'characters': 0},
            'features': {'text_type': 'error', 'complexity_score': 0.0},
            'semantic': {'sentiment': 'neutral', 'formality': 'neutral'},
            'detection': {'repetition_patterns': {}, 'formatting_patterns': {}, 'structure_patterns': {}},
            'summary': f'分析失败: {error_message}'
        }
    
    def get_analysis_status(self) -> Dict[str, Any]:
        """获取分析器状态"""
        return {
            'analyzer_type': 'text_analyzer',
            'status': 'ready',
            'capabilities': [
                'structure_analysis',
                'feature_analysis',
                'semantic_analysis',
                'pattern_detection',
                'complexity_assessment'
            ],
            'version': '3.0.0'
        }
