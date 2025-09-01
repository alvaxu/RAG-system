'''
程序说明：

## 1. 重构后的轻量级记忆管理系统
## 2. 专注于指代词解析和上下文连续性
## 3. 不再存储完整的问答对，只保存关键上下文信息
## 4. 简化相关性计算，提高性能
## 5. 符合"记忆作为查询增强器"的设计理念
'''

import os
import json
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)


class ConversationContext:
    """
    简化的对话上下文，专注于指代词解析
    """
    
    def __init__(self, user_id: str):
        self.user_id: str = user_id
        self.current_topic: str = ""           # 当前讨论主题
        self.last_question: str = ""           # 上一个问题
        self.last_entities: List[str] = []     # 上一个问题中的实体
        self.entity_mentions: Dict[str, str] = {}  # 指代词映射 {"它": "中芯国际"}
        self.timestamp: float = 0.0
        self.conversation_history: List[Dict[str, Any]] = []  # 简化的对话历史
    
    def update_context(self, question: str, answer: str):
        """更新对话上下文"""
        self.last_question = question
        self.last_entities = self._extract_entities(question)
        self.current_topic = self._identify_topic(question)
        self.timestamp = time.time()
        
        # 保存简化的对话记录（只保存关键信息）
        conversation_item = {
            'question': question,
            'entities': self.last_entities,
            'topic': self.current_topic,
            'timestamp': self.timestamp
        }
        self.conversation_history.append(conversation_item)
        
        # 只保留最近10条记录，避免内存膨胀
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
    
    def _extract_entities(self, question: str) -> List[str]:
        """提取问题中的关键实体"""
        entities = []
        
        # 提取公司名称
        if '中芯国际' in question:
            entities.append('中芯国际')
        if '公司' in question:
            entities.append('公司')
        
        # 提取技术相关词汇
        tech_keywords = ['技术', '芯片', '制造', '工艺', '设备']
        for keyword in tech_keywords:
            if keyword in question:
                entities.append(keyword)
        
        # 提取财务相关词汇
        finance_keywords = ['营收', '利润', '财务', '业绩', '数据']
        for keyword in finance_keywords:
            if keyword in question:
                entities.append(keyword)
        
        return entities
    
    def _identify_topic(self, question: str) -> str:
        """识别问题主题"""
        if any(word in question for word in ['技术', '芯片', '制造']):
            return '技术'
        elif any(word in question for word in ['财务', '营收', '利润', '业绩']):
            return '财务'
        elif any(word in question for word in ['业务', '市场', '竞争']):
            return '业务'
        elif any(word in question for word in ['图', '表', '数据']):
            return '图表'
        else:
            return '综合'
    
    def resolve_references(self, question: str) -> str:
        """解析指代词，返回增强的查询"""
        resolved_question = question
        
        # 解析"它"、"那个"等指代词
        if "它" in question and self.last_entities:
            resolved_question = question.replace("它", self.last_entities[0])
            logger.info(f"指代词解析: '它' -> '{self.last_entities[0]}'")
        
        if "那个" in question and self.last_question:
            # 从上一个问题中提取关键信息
            key_info = self._extract_key_info(self.last_question)
            if key_info:
                resolved_question = question.replace("那个", key_info)
                logger.info(f"指代词解析: '那个' -> '{key_info}'")
        
        if "刚才说的" in question and self.last_question:
            # 解析"刚才说的"
            key_info = self._extract_key_info(self.last_question)
            if key_info:
                resolved_question = question.replace("刚才说的", key_info)
                logger.info(f"指代词解析: '刚才说的' -> '{key_info}'")
        
        return resolved_question
    
    def _extract_key_info(self, question: str) -> str:
        """从问题中提取关键信息"""
        # 提取实体信息
        entities = self._extract_entities(question)
        if entities:
            return entities[0]
        
        # 提取关键词
        keywords = ['技术', '业务', '财务', '业绩', '数据', '图表']
        for keyword in keywords:
            if keyword in question:
                return keyword
        
        return ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'user_id': self.user_id,
            'current_topic': self.current_topic,
            'last_question': self.last_question,
            'last_entities': self.last_entities,
            'entity_mentions': self.entity_mentions,
            'timestamp': self.timestamp,
            'conversation_history': self.conversation_history
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationContext':
        """从字典创建对话上下文"""
        context = cls(data['user_id'])
        context.current_topic = data.get('current_topic', '')
        context.last_question = data.get('last_question', '')
        context.last_entities = data.get('last_entities', [])
        context.entity_mentions = data.get('entity_mentions', {})
        context.timestamp = data.get('timestamp', 0.0)
        context.conversation_history = data.get('conversation_history', [])
        return context


class UserPreferences:
    """
    用户偏好管理，存储用户关注的重点
    """
    
    def __init__(self, user_id: str):
        self.user_id: str = user_id
        self.interest_areas: List[str] = []      # 用户感兴趣的领域
        self.frequent_queries: List[str] = []    # 用户经常查询的内容
        self.last_updated: float = 0.0
    
    def update_preferences(self, question: str, topic: str):
        """更新用户偏好"""
        # 更新兴趣领域
        if topic not in self.interest_areas:
            self.interest_areas.append(topic)
        
        # 限制兴趣领域数量
        if len(self.interest_areas) > 5:
            self.interest_areas = self.interest_areas[-5:]
        
        # 更新查询频率
        if question not in self.frequent_queries:
            self.frequent_queries.append(question)
        
        # 限制查询记录数量
        if len(self.frequent_queries) > 10:
            self.frequent_queries = self.frequent_queries[-10:]
        
        self.last_updated = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'user_id': self.user_id,
            'interest_areas': self.interest_areas,
            'frequent_queries': self.frequent_queries,
            'last_updated': self.last_updated
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserPreferences':
        """从字典创建用户偏好"""
        preferences = cls(data['user_id'])
        preferences.interest_areas = data.get('interest_areas', [])
        preferences.frequent_queries = data.get('frequent_queries', [])
        preferences.last_updated = data.get('last_updated', 0.0)
        return preferences


class SimplifiedMemoryManager:
    """
    简化的记忆管理器，专注于指代词解析和上下文管理
    """
    
    def __init__(self, memory_dir: str = None):
        """初始化记忆管理器"""
        # 设置记忆目录
        if memory_dir is None:
            memory_dir = "./central/memory_db"
        
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # 记忆文件路径
        self.context_file = self.memory_dir / "conversation_contexts.json"
        self.preferences_file = self.memory_dir / "user_preferences.json"
        
        # 内存存储
        self.conversation_contexts: Dict[str, ConversationContext] = {}  # user_id -> context
        self.user_preferences: Dict[str, UserPreferences] = {}           # user_id -> preferences
        
        # 加载现有数据
        self._load_data()
    
    def _load_data(self):
        """加载记忆数据"""
        try:
            # 加载对话上下文
            if self.context_file.exists():
                with open(self.context_file, 'r', encoding='utf-8') as f:
                    context_data = json.load(f)
                    for user_id, data in context_data.items():
                        self.conversation_contexts[user_id] = ConversationContext.from_dict(data)
                logger.info(f"已加载 {len(self.conversation_contexts)} 个用户的对话上下文")
        except Exception as e:
            logger.warning(f"加载对话上下文失败: {e}")
        
        try:
            # 加载用户偏好
            if self.preferences_file.exists():
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    preferences_data = json.load(f)
                    for user_id, data in preferences_data.items():
                        self.user_preferences[user_id] = UserPreferences.from_dict(data)
                logger.info(f"已加载 {len(self.user_preferences)} 个用户的偏好信息")
        except Exception as e:
            logger.warning(f"加载用户偏好失败: {e}")
    
    def _save_data(self):
        """保存记忆数据"""
        try:
            # 保存对话上下文
            context_data = {}
            for user_id, context in self.conversation_contexts.items():
                context_data[user_id] = context.to_dict()
            
            with open(self.context_file, 'w', encoding='utf-8') as f:
                json.dump(context_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存对话上下文失败: {e}")
        
        try:
            # 保存用户偏好
            preferences_data = {}
            for user_id, preferences in self.user_preferences.items():
                preferences_data[user_id] = preferences.to_dict()
            
            with open(self.preferences_file, 'w', encoding='utf-8') as f:
                json.dump(preferences_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存用户偏好失败: {e}")
    
    def process_query(self, user_id: str, question: str) -> str:
        """
        处理查询：解析指代词，返回增强的查询
        """
        # 确保用户上下文存在
        if user_id not in self.conversation_contexts:
            self.conversation_contexts[user_id] = ConversationContext(user_id)
        
        # 解析指代词
        resolved_question = self.conversation_contexts[user_id].resolve_references(question)
        
        return resolved_question
    
    def update_context(self, user_id: str, question: str, answer: str):
        """
        更新对话上下文
        """
        # 确保用户上下文存在
        if user_id not in self.conversation_contexts:
            self.conversation_contexts[user_id] = ConversationContext(user_id)
        
        # 更新对话上下文
        self.conversation_contexts[user_id].update_context(question, answer)
        
        # 更新用户偏好
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = UserPreferences(user_id)
        
        topic = self.conversation_contexts[user_id].current_topic
        self.user_preferences[user_id].update_preferences(question, topic)
        
        # 保存数据
        self._save_data()
    
    def get_context_summary(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户上下文摘要
        """
        if user_id not in self.conversation_contexts:
            return {
                'has_context': False,
                'current_topic': '',
                'last_question': '',
                'entities': []
            }
        
        context = self.conversation_contexts[user_id]
        return {
            'has_context': True,
            'current_topic': context.current_topic,
            'last_question': context.last_question,
            'entities': context.last_entities,
            'conversation_count': len(context.conversation_history)
        }
    
    def clear_context(self, user_id: str = None):
        """
        清除上下文
        """
        if user_id is None:
            # 清除所有用户的上下文
            self.conversation_contexts.clear()
            self.user_preferences.clear()
        else:
            # 清除指定用户的上下文
            self.conversation_contexts.pop(user_id, None)
            self.user_preferences.pop(user_id, None)
        
        # 保存数据
        self._save_data()
    
    def get_memory_stats(self, user_id: str = None) -> Dict[str, Any]:
        """
        获取记忆统计信息（保持向后兼容）
        """
        if user_id:
            # 获取指定用户的统计
            context_count = len(self.conversation_contexts.get(user_id, ConversationContext(user_id)).conversation_history)
            preferences_count = len(self.user_preferences.get(user_id, UserPreferences(user_id)).interest_areas)
            
            return {
                'user_id': user_id,
                'session_memory_count': context_count,
                'user_memory_count': preferences_count,
                'total_memory_count': context_count + preferences_count
            }
        else:
            # 获取默认用户的统计
            default_user = "default_user"
            default_context_count = len(self.conversation_contexts.get(default_user, ConversationContext(default_user)).conversation_history)
            default_preferences_count = len(self.user_preferences.get(default_user, UserPreferences(default_user)).interest_areas)
            
            return {
                'user_id': default_user,
                'session_memory_count': default_context_count,
                'user_memory_count': default_preferences_count,
                'total_memory_count': default_context_count + default_preferences_count,
                'total_users': len(self.conversation_contexts),
                'total_contexts': sum(len(ctx.conversation_history) for ctx in self.conversation_contexts.values()),
                'total_preferences': sum(len(pref.interest_areas) for pref in self.user_preferences.values())
            }
    
    # 保持向后兼容的方法
    def add_to_session(self, user_id: str, question: str, answer: str, context: Dict[str, Any] = None):
        """向后兼容：添加会话记忆"""
        self.update_context(user_id, question, answer)
    
    def add_to_user_memory(self, memory_item):
        """向后兼容：添加用户记忆"""
        if hasattr(memory_item, 'user_id'):
            self.update_context(memory_item.user_id, memory_item.question, memory_item.answer)
    
    def retrieve_relevant_memory(self, user_id: str, current_question: str, 
                               memory_limit: int = 5, relevance_threshold: float = 0.05) -> List[Any]:
        """向后兼容：检索相关记忆"""
        # 返回空的记忆列表，因为新系统不需要这个功能
        return []
    
    def clear_session_memory(self, user_id: str = None):
        """向后兼容：清除会话记忆"""
        self.clear_context(user_id)
    
    def clear_user_memory(self, user_id: str = None):
        """向后兼容：清除用户记忆"""
        self.clear_context(user_id) 
    
    def clear_all_memories(self):
        """
        清除所有记忆数据（用于系统优雅退出）
        """
        try:
            # 清除所有用户上下文
            total_contexts = len(self.conversation_contexts)
            total_preferences = len(self.user_preferences)
            
            self.conversation_contexts.clear()
            self.user_preferences.clear()
            
            # 保存空数据
            self._save_data()
            
            logger.info(f"记忆管理器清理完成，共清理 {total_contexts} 个用户上下文，{total_preferences} 个用户偏好")
            return {
                'contexts_cleared': total_contexts,
                'preferences_cleared': total_preferences
            }
            
        except Exception as e:
            logger.error(f"清理记忆管理器失败: {e}")
            return {
                'contexts_cleared': 0,
                'preferences_cleared': 0,
                'error': str(e)
            }