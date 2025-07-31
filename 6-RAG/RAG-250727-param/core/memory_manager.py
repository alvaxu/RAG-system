'''
程序说明：
## 1. 统一的记忆管理模块
## 2. 从V307_memory_manager.py中提取核心功能
## 3. 支持会话记忆和用户记忆
## 4. 提供记忆存储、检索和管理功能
'''

import os
import json
import time
import pickle
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)


class MemoryItem:
    """
    记忆项数据结构
    """
    
    def __init__(self, user_id: str, question: str, answer: str, context: Dict[str, Any] = None):
        """
        初始化记忆项
        :param user_id: 用户ID
        :param question: 用户问题
        :param answer: 系统回答
        :param context: 上下文信息
        """
        self.user_id = user_id
        self.question = question
        self.answer = answer
        self.context = context or {}
        self.timestamp = time.time()
        self.created_at = datetime.now().isoformat()
        self.memory_id = self._generate_memory_id()
    
    def _generate_memory_id(self) -> str:
        """
        生成记忆项的唯一ID
        :return: 记忆项ID
        """
        content = f"{self.user_id}_{self.question}_{self.timestamp}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        :return: 字典格式的记忆项
        """
        return {
            'memory_id': self.memory_id,
            'user_id': self.user_id,
            'question': self.question,
            'answer': self.answer,
            'context': self.context,
            'timestamp': self.timestamp,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryItem':
        """
        从字典创建记忆项
        :param data: 字典数据
        :return: 记忆项对象
        """
        memory_item = cls(
            user_id=data['user_id'],
            question=data['question'],
            answer=data['answer'],
            context=data.get('context', {})
        )
        memory_item.memory_id = data['memory_id']
        memory_item.timestamp = data['timestamp']
        memory_item.created_at = data['created_at']
        return memory_item


class MemoryManager:
    """
    记忆管理器类，负责记忆的存储、检索和管理
    """
    
    def __init__(self, memory_dir: str = None):
        """
        初始化记忆管理器
        :param memory_dir: 记忆数据存储目录
        """
        # 如果没有提供memory_dir，则使用统一配置管理
        if memory_dir is None:
            try:
                # 优先使用统一配置管理
                from config.settings import Settings
                config = Settings.load_from_file('config.json')
                memory_dir = config.memory_db_dir
                logger.info(f"从配置文件加载记忆目录: {memory_dir}")
            except Exception as e:
                # 如果统一配置不可用，尝试ConfigManager
                try:
                    from config import ConfigManager
                    config_manager = ConfigManager()
                    memory_dir = config_manager.settings.memory_db_dir
                    logger.info(f"从ConfigManager加载记忆目录: {memory_dir}")
                except Exception:
                    # 最后的备选方案
                    memory_dir = "./memory_db"
                    logger.warning(f"使用默认记忆目录: {memory_dir}")
        
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # 记忆文件路径
        self.session_memory_file = self.memory_dir / "session_memory.json"
        self.user_memory_file = self.memory_dir / "user_memory.json"
        
        # 初始化记忆存储
        self.session_memory = {}  # 会话记忆 {user_id: [MemoryItem]}
        self.user_memory = {}     # 用户记忆 {user_id: [MemoryItem]}
        
        # 加载现有记忆
        self._load_memories()
    
    def _load_memories(self):
        """
        加载记忆数据
        """
        # 加载会话记忆
        if self.session_memory_file.exists():
            try:
                with open(self.session_memory_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                    for user_id, items in session_data.items():
                        self.session_memory[user_id] = [MemoryItem.from_dict(item) for item in items]
            except Exception as e:
                print(f"加载会话记忆失败: {e}")
        
        # 加载用户记忆
        if self.user_memory_file.exists():
            try:
                with open(self.user_memory_file, 'r', encoding='utf-8') as f:
                    user_data = json.load(f)
                    for user_id, items in user_data.items():
                        self.user_memory[user_id] = [MemoryItem.from_dict(item) for item in items]
            except Exception as e:
                print(f"加载用户记忆失败: {e}")
    
    def _save_session_memory(self):
        """
        保存会话记忆
        """
        try:
            session_data = {}
            for user_id, items in self.session_memory.items():
                session_data[user_id] = [item.to_dict() for item in items]
            
            with open(self.session_memory_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存会话记忆失败: {e}")
    
    def _save_user_memory(self):
        """
        保存用户记忆
        """
        try:
            user_data = {}
            for user_id, items in self.user_memory.items():
                user_data[user_id] = [item.to_dict() for item in items]
            
            with open(self.user_memory_file, 'w', encoding='utf-8') as f:
                json.dump(user_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存用户记忆失败: {e}")
    
    def add_to_session(self, user_id: str, question: str, answer: str, context: Dict[str, Any] = None):
        """
        添加会话记忆
        :param user_id: 用户ID
        :param question: 用户问题
        :param answer: 系统回答
        :param context: 上下文信息
        """
        memory_item = MemoryItem(user_id, question, answer, context)
        
        if user_id not in self.session_memory:
            self.session_memory[user_id] = []
        
        self.session_memory[user_id].append(memory_item)
        
        # 限制会话记忆数量（保留最近50条）
        if len(self.session_memory[user_id]) > 50:
            self.session_memory[user_id] = self.session_memory[user_id][-50:]
        
        self._save_session_memory()
    
    def add_to_user_memory(self, memory_item: MemoryItem):
        """
        添加用户记忆
        :param memory_item: 记忆项
        """
        user_id = memory_item.user_id
        
        if user_id not in self.user_memory:
            self.user_memory[user_id] = []
        
        self.user_memory[user_id].append(memory_item)
        
        # 限制用户记忆数量（保留最近100条）
        if len(self.user_memory[user_id]) > 100:
            self.user_memory[user_id] = self.user_memory[user_id][-100:]
        
        self._save_user_memory()
    
    def retrieve_relevant_memory(self, user_id: str, current_question: str, 
                               memory_limit: int = 5, relevance_threshold: float = 0.1) -> List[MemoryItem]:
        """
        检索相关记忆
        :param user_id: 用户ID
        :param current_question: 当前问题
        :param memory_limit: 记忆数量限制
        :param relevance_threshold: 相关性阈值
        :return: 相关记忆列表
        """
        relevant_memories = []
        
        # 合并会话记忆和用户记忆
        all_memories = []
        if user_id in self.session_memory:
            all_memories.extend(self.session_memory[user_id])
        if user_id in self.user_memory:
            all_memories.extend(self.user_memory[user_id])
        
        # 计算相关性并排序
        for memory in all_memories:
            relevance = self._calculate_relevance(current_question, memory.question)
            if relevance >= relevance_threshold:
                memory.relevance_score = relevance
                relevant_memories.append(memory)
        
        # 按相关性排序并返回限制数量
        relevant_memories.sort(key=lambda x: x.relevance_score, reverse=True)
        return relevant_memories[:memory_limit]
    
    def _calculate_relevance(self, question1: str, question2: str) -> float:
        """
        计算两个问题的相关性
        :param question1: 问题1
        :param question2: 问题2
        :return: 相关性分数
        """
        try:
            # 改进的相关性计算，适合中文对话
            def calculate_chinese_relevance(q1: str, q2: str) -> float:
                import re
                
                # 1. 检查指代词（优先级最高）
                pronouns = ['这', '那', '那个', '这个', '它', '其']
                if any(pronoun in q2 for pronoun in pronouns):
                    # 如果当前问题包含指代词，提高相关性
                    return 0.9
                
                # 2. 检查年份相关性（包括相邻年份）
                years1 = set(re.findall(r'20\d{2}', q1))
                years2 = set(re.findall(r'20\d{2}', q2))
                if years1 and years2:
                    if years1.intersection(years2):
                        return 0.8  # 相同年份
                    else:
                        # 检查是否为相邻年份（如2024 vs 2025）
                        years1_list = sorted(list(years1))
                        years2_list = sorted(list(years2))
                        if len(years1_list) > 0 and len(years2_list) > 0:
                            if abs(int(years1_list[0]) - int(years2_list[0])) <= 1:
                                return 0.7  # 相邻年份
                
                # 3. 检查是否包含相同的公司名称
                companies1 = set(re.findall(r'中芯国际|公司', q1))
                companies2 = set(re.findall(r'中芯国际|公司', q2))
                if companies1 and companies2 and companies1.intersection(companies2):
                    return 0.6
                
                # 4. 检查是否包含相同的图表相关词汇
                chart_words1 = set(re.findall(r'图|走势|表现|营收|净利润', q1))
                chart_words2 = set(re.findall(r'图|走势|表现|营收|净利润', q2))
                if chart_words1 and chart_words2 and chart_words1.intersection(chart_words2):
                    return 0.5
                
                # 5. 检查是否包含相同的关键词
                keywords1 = set(re.findall(r'营业收入|净利润|营收|利润|财务|数据', q1))
                keywords2 = set(re.findall(r'营业收入|净利润|营收|利润|财务|数据', q2))
                if keywords1 and keywords2 and keywords1.intersection(keywords2):
                    return 0.4
                
                # 6. 简单的Jaccard相似度作为后备
                def jaccard_similarity(set1, set2):
                    intersection = len(set1.intersection(set2))
                    union = len(set1.union(set2))
                    return intersection / union if union > 0 else 0
                
                words1 = set(q1.lower().split())
                words2 = set(q2.lower().split())
                return jaccard_similarity(words1, words2) * 0.2
            
            return calculate_chinese_relevance(question1, question2)
            
        except Exception as e:
            print(f"计算相关性时发生错误: {e}")
            return 0.0
    
    def build_context(self, user_id: str, question: str, memory_limit: int = 5) -> Dict[str, Any]:
        """
        构建记忆上下文
        :param user_id: 用户ID
        :param question: 当前问题
        :param memory_limit: 记忆数量限制
        :return: 上下文信息
        """
        relevant_memories = self.retrieve_relevant_memory(user_id, question, memory_limit)
        
        if not relevant_memories:
            return {
                'memory_context': '',
                'memory_count': 0,
                'has_memory': False
            }
        
        # 构建记忆上下文
        memory_context = self._build_memory_context(relevant_memories)
        
        return {
            'memory_context': memory_context,
            'memory_count': len(relevant_memories),
            'has_memory': True,
            'memories': relevant_memories
        }
    
    def _build_memory_context(self, memories: List[MemoryItem]) -> str:
        """
        构建记忆上下文字符串
        :param memories: 记忆列表
        :return: 上下文字符串
        """
        if not memories:
            return ""
        
        context_lines = []
        for i, memory in enumerate(memories, 1):
            context_lines.append(f"{i}. 问题: {memory.question}")
            context_lines.append(f"   回答: {memory.answer}")
            context_lines.append("")
        
        return "\n".join(context_lines)
    
    def clear_session_memory(self, user_id: str = None):
        """
        清除会话记忆
        :param user_id: 用户ID，如果为None则清除所有用户的会话记忆
        """
        if user_id is None:
            self.session_memory.clear()
        else:
            self.session_memory.pop(user_id, None)
        
        self._save_session_memory()
    
    def clear_user_memory(self, user_id: str = None):
        """
        清除用户记忆
        :param user_id: 用户ID，如果为None则清除所有用户的记忆
        """
        if user_id is None:
            self.user_memory.clear()
        else:
            self.user_memory.pop(user_id, None)
        
        self._save_user_memory()
    
    def get_memory_stats(self, user_id: str = None) -> Dict[str, Any]:
        """
        获取记忆统计信息
        :param user_id: 用户ID
        :return: 统计信息
        """
        if user_id:
            session_count = len(self.session_memory.get(user_id, []))
            user_count = len(self.user_memory.get(user_id, []))
            return {
                'user_id': user_id,
                'session_memory_count': session_count,
                'user_memory_count': user_count,
                'total_memory_count': session_count + user_count
            }
        else:
            total_session = sum(len(items) for items in self.session_memory.values())
            total_user = sum(len(items) for items in self.user_memory.values())
            return {
                'total_users': len(set(list(self.session_memory.keys()) + list(self.user_memory.keys()))),
                'total_session_memory': total_session,
                'total_user_memory': total_user,
                'total_memory': total_session + total_user
            } 