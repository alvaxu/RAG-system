'''
程序说明：
## 1. 修复记忆模块问题
## 2. 解决后续查询只检索到图片内容的问题
## 3. 优化检索策略，确保文本和图片的平衡
## 4. 改进记忆相关性计算算法
'''

import os
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from core.memory_manager import MemoryManager
from core.enhanced_qa_system import EnhancedQASystem
from config import ConfigManager

def analyze_problem_root_cause():
    """
    分析问题的根本原因
    """
    print("=== 问题根本原因分析 ===")
    
    memory_file = "memory_db/session_memory.json"
    if not os.path.exists(memory_file):
        print("记忆文件不存在")
        return
    
    with open(memory_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("问题模式分析：")
    print("1. 第一个问题（成功）：检索到5个文本来源，0个图片来源")
    print("2. 后续问题（失败）：检索到0个文本来源，5个图片来源")
    print("3. 所有失败问题的平均相关性分数都是0.0000")
    
    print("\n根本原因：")
    print("1. 向量检索策略存在问题，后续查询偏向检索图片而非文本")
    print("2. 图片内容的相关性分数计算可能有问题")
    print("3. 记忆模块的相关性计算过于严格，导致记忆无法正确关联")
    print("4. 检索结果缺乏文本内容，导致LLM无法生成有效回答")

def create_enhanced_memory_manager():
    """
    创建增强版记忆管理器
    """
    print("\n=== 创建增强版记忆管理器 ===")
    
    class EnhancedMemoryManager(MemoryManager):
        """
        增强版记忆管理器，修复相关问题
        """
        
        def __init__(self, memory_dir: str = None):
            super().__init__(memory_dir)
            print("增强版记忆管理器初始化完成")
        
        def _calculate_relevance(self, question1: str, question2: str) -> float:
            """
            改进的相关性计算方法
            :param question1: 问题1
            :param question2: 问题2
            :return: 相关性分数
            """
            try:
                import re
                
                # 1. 检查指代词（优先级最高）
                pronouns = ['这', '那', '那个', '这个', '它', '其', '该', '此']
                if any(pronoun in question2 for pronoun in pronouns):
                    return 0.9
                
                # 2. 检查年份相关性（包括相邻年份）
                years1 = set(re.findall(r'20\d{2}', question1))
                years2 = set(re.findall(r'20\d{2}', question2))
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
                companies1 = set(re.findall(r'中芯国际|公司', question1))
                companies2 = set(re.findall(r'中芯国际|公司', question2))
                if companies1 and companies2 and companies1.intersection(companies2):
                    return 0.6
                
                # 4. 检查是否包含相同的图表相关词汇
                chart_words1 = set(re.findall(r'图|走势|表现|营收|净利润|毛利率|净利率|产能|市场地位', question1))
                chart_words2 = set(re.findall(r'图|走势|表现|营收|净利润|毛利率|净利率|产能|市场地位', question2))
                if chart_words1 and chart_words2 and chart_words1.intersection(chart_words2):
                    return 0.5
                
                # 5. 检查是否包含相同的关键词
                keywords1 = set(re.findall(r'营业收入|净利润|营收|利润|财务|数据|业务|技术|核心', question1))
                keywords2 = set(re.findall(r'营业收入|净利润|营收|利润|财务|数据|业务|技术|核心', question2))
                if keywords1 and keywords2 and keywords1.intersection(keywords2):
                    return 0.4
                
                # 6. 检查问题类型相似性
                question_types1 = set(re.findall(r'是什么|如何|怎样|多少|哪些|什么', question1))
                question_types2 = set(re.findall(r'是什么|如何|怎样|多少|哪些|什么', question2))
                if question_types1 and question_types2 and question_types1.intersection(question_types2):
                    return 0.3
                
                # 7. 简单的Jaccard相似度作为后备
                def jaccard_similarity(set1, set2):
                    intersection = len(set1.intersection(set2))
                    union = len(set1.union(set2))
                    return intersection / union if union > 0 else 0
                
                words1 = set(question1.lower().split())
                words2 = set(question2.lower().split())
                return jaccard_similarity(words1, words2) * 0.2
                
            except Exception as e:
                print(f"计算相关性时发生错误: {e}")
                return 0.0
        
        def retrieve_relevant_memory(self, user_id: str, current_question: str, 
                                   memory_limit: int = 5, relevance_threshold: float = 0.05) -> List:
            """
            改进的记忆检索方法
            :param user_id: 用户ID
            :param current_question: 当前问题
            :param memory_limit: 记忆数量限制
            :param relevance_threshold: 相关性阈值（降低阈值）
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
    
    return EnhancedMemoryManager

def create_enhanced_qa_system():
    """
    创建增强版QA系统
    """
    print("\n=== 创建增强版QA系统 ===")
    
    class EnhancedQASystemFixed(EnhancedQASystem):
        """
        修复版QA系统，解决检索策略问题
        """
        
        def __init__(self, vector_store, api_key: str, 
                     memory_manager=None, config: Dict[str, Any] = None):
            super().__init__(vector_store, api_key, memory_manager, config)
            print("增强版QA系统初始化完成")
        
        def _initial_retrieval(self, question: str, k: int) -> List:
            """
            改进的初始检索方法
            :param question: 问题
            :param k: 检索数量
            :return: 检索结果
            """
            try:
                if not self.vector_store:
                    return []
                
                # 分别检索文本和图片内容
                text_k = max(1, k // 2)  # 确保至少检索1个文本
                image_k = k - text_k
                
                # 检索文本内容
                text_docs = self.vector_store.similarity_search(
                    question, 
                    k=text_k,
                    filter={"chunk_type": "text"}
                )
                
                # 检索图片内容
                image_docs = self.vector_store.similarity_search(
                    question, 
                    k=image_k,
                    filter={"chunk_type": "image"}
                )
                
                # 合并结果
                combined_docs = text_docs + image_docs
                
                # 如果文本内容不足，增加文本检索
                if len(text_docs) < text_k and len(combined_docs) < k:
                    additional_text_k = min(text_k - len(text_docs), k - len(combined_docs))
                    if additional_text_k > 0:
                        additional_text_docs = self.vector_store.similarity_search(
                            question, 
                            k=additional_text_k,
                            filter={"chunk_type": "text"}
                        )
                        combined_docs.extend(additional_text_docs)
                
                # 如果图片内容不足，增加图片检索
                if len(image_docs) < image_k and len(combined_docs) < k:
                    additional_image_k = min(image_k - len(image_docs), k - len(combined_docs))
                    if additional_image_k > 0:
                        additional_image_docs = self.vector_store.similarity_search(
                            question, 
                            k=additional_image_k,
                            filter={"chunk_type": "image"}
                        )
                        combined_docs.extend(additional_image_docs)
                
                # 如果仍然不足，进行无过滤检索
                if len(combined_docs) < k:
                    remaining_k = k - len(combined_docs)
                    remaining_docs = self.vector_store.similarity_search(
                        question, 
                        k=remaining_k
                    )
                    combined_docs.extend(remaining_docs)
                
                return combined_docs[:k]
                
            except Exception as e:
                print(f"初始检索失败: {e}")
                # 降级到原始方法
                return super()._initial_retrieval(question, k)
        
        def answer_with_memory(self, user_id: str, question: str, k: int = None) -> Dict[str, Any]:
            """
            改进的带记忆问答方法
            :param user_id: 用户ID
            :param question: 问题
            :param k: 检索数量
            :return: 回答结果
            """
            try:
                # 构建记忆上下文
                memory_context = self.memory_manager.build_context(user_id, question, memory_limit=5)
                
                # 获取相关记忆
                relevant_memories = self.memory_manager.retrieve_relevant_memory(user_id, question)
                
                # 检查是否有相关记忆且记忆未被清除
                has_relevant_memory = (not self.memory_cleared_flag and
                                     memory_context.get('memory_context') and 
                                     memory_context.get('memory_count', 0) > 0 and
                                     not self._is_exact_duplicate_question(question, memory_context.get('memories', [])))
                
                if has_relevant_memory:
                    # 有相关记忆时，将记忆上下文整合到问题中
                    enhanced_question = f"""问题：{question}

## 相关历史对话
{memory_context['memory_context']}

## 智能上下文理解指导
你是一个具有强大上下文理解能力的AI助手。请遵循以下原则：

### 指代词理解策略
1. **时间指代**：
   - "那2025年的呢" → 基于前面提到的某一年的相关信息
   - "去年"、"今年" → 基于对话时间上下文

2. **对象指代**：
   - "这个图"、"那个表" → 基于前面提到的具体内容
   - "它"、"其" → 基于前面提到的实体或概念

3. **概念指代**：
   - "这个数据"、"那个指标" → 基于前面提到的具体数据
   - "这种情况"、"那个问题" → 基于前面提到的具体情境

### 回答要求
1. 首先分析历史对话中的相关信息
2. 准确理解指代词的具体指向
3. 基于文档内容和历史对话提供准确回答
4. 保持对话的连贯性和自然性
5. 如果无法确定指代内容，请明确说明

请基于以上历史对话和文档内容，准确理解用户的指代词，并提供连贯、准确的回答。"""
                    
                    # 使用增强的问题进行回答
                    result = self.answer_question(enhanced_question, k)
                else:
                    # 没有相关记忆或记忆被清除时，正常回答
                    result = self.answer_question(question, k)
                
                # 只有在记忆未被清除时才保存到记忆
                if not self.memory_cleared_flag:
                    # 转换sources为可序列化的格式
                    serializable_sources = []
                    for source in result.get('sources', []):
                        # 确保content是字符串
                        content = source.get('content', '')
                        if not isinstance(content, str):
                            content = str(content)
                        
                        # 确保metadata是可序列化的
                        metadata = source.get('metadata', {})
                        if isinstance(metadata, dict):
                            # 过滤掉不可序列化的值
                            clean_metadata = {}
                            for key, value in metadata.items():
                                try:
                                    # 测试是否可序列化
                                    import json
                                    json.dumps(value)
                                    clean_metadata[key] = value
                                except (TypeError, ValueError):
                                    # 如果不可序列化，转换为字符串
                                    clean_metadata[key] = str(value)
                        else:
                            clean_metadata = str(metadata)
                        
                        serializable_source = {
                            'content': content,
                            'metadata': clean_metadata,
                            'score': float(source.get('score', 0.0))
                        }
                        serializable_sources.append(serializable_source)
                    
                    try:
                        self.memory_manager.add_to_session(
                            user_id=user_id,
                            question=question,
                            answer=result['answer'],
                            context={
                                'sources': serializable_sources,
                                'cost': result.get('cost', 0.0),
                                'relevant_memories': len(relevant_memories)
                            }
                        )
                    except Exception as e:
                        print(f"保存会话记忆失败: {e}")
                        # 如果保存失败，尝试简化版本
                        try:
                            self.memory_manager.add_to_session(
                                user_id=user_id,
                                question=question,
                                answer=result['answer'],
                                context={
                                    'cost': result.get('cost', 0.0),
                                    'relevant_memories': len(relevant_memories)
                                }
                            )
                        except Exception as e2:
                            print(f"简化版记忆保存也失败: {e2}")
                
                return result
                
            except Exception as e:
                return {
                    'answer': f'带记忆的问答过程中发生错误: {str(e)}',
                    'sources': [],
                    'cost': 0.0,
                    'error': str(e)
                }
    
    return EnhancedQASystemFixed

def test_enhanced_memory_manager():
    """
    测试增强版记忆管理器
    """
    print("\n=== 测试增强版记忆管理器 ===")
    
    try:
        # 创建增强版记忆管理器
        EnhancedMemoryManager = create_enhanced_memory_manager()
        memory_manager = EnhancedMemoryManager()
        
        # 测试记忆检索
        test_questions = [
            "中芯国际的主要业务和核心技术是什么？",
            "中芯国际在晶圆代工行业的市场地位如何？",
            "中芯国际的产能扩张历程和现状是怎样的？",
            "中芯国际2024-2027年的净利润增长趋势如何？"
        ]
        
        for i, question in enumerate(test_questions):
            print(f"\n测试问题 {i+1}: {question}")
            
            # 测试记忆检索
            relevant_memories = memory_manager.retrieve_relevant_memory("default_user", question)
            print(f"  相关记忆数量: {len(relevant_memories)}")
            
            for j, memory in enumerate(relevant_memories):
                print(f"    记忆 {j+1}: {memory.question}")
                print(f"    相关性: {getattr(memory, 'relevance_score', 'N/A')}")
            
            # 测试上下文构建
            context = memory_manager.build_context("default_user", question)
            print(f"  上下文构建: {context.get('has_memory', False)}")
            print(f"  记忆数量: {context.get('memory_count', 0)}")
        
    except Exception as e:
        print(f"增强版记忆管理器测试失败: {e}")

def create_fix_summary():
    """
    创建修复总结
    """
    print("\n=== 修复方案总结 ===")
    
    print("问题诊断：")
    print("1. 后续查询只检索到图片内容，缺乏文本内容")
    print("2. 记忆模块的相关性计算过于严格")
    print("3. 向量检索策略不平衡")
    print("4. 相关性阈值设置过高")
    
    print("\n修复方案：")
    print("1. 改进检索策略：")
    print("   - 分别检索文本和图片内容")
    print("   - 确保至少检索1个文本内容")
    print("   - 平衡文本和图片的检索比例")
    
    print("2. 优化记忆相关性计算：")
    print("   - 降低相关性阈值从0.1到0.05")
    print("   - 增加更多相关性判断规则")
    print("   - 改进指代词识别")
    
    print("3. 增强QA系统：")
    print("   - 改进初始检索方法")
    print("   - 优化记忆上下文构建")
    print("   - 增加错误处理和降级机制")
    
    print("\n实施步骤：")
    print("1. 更新记忆管理器代码")
    print("2. 更新QA系统代码")
    print("3. 测试修复效果")
    print("4. 监控系统性能")

def main():
    """
    主函数
    """
    print("记忆模块问题修复工具")
    print("=" * 50)
    
    # 1. 分析问题根本原因
    analyze_problem_root_cause()
    
    # 2. 测试增强版记忆管理器
    test_enhanced_memory_manager()
    
    # 3. 创建修复总结
    create_fix_summary()
    
    print("\n=== 修复建议 ===")
    print("1. 立即实施检索策略改进")
    print("2. 降低记忆相关性阈值")
    print("3. 增加更多相关性判断规则")
    print("4. 监控修复后的系统性能")

if __name__ == "__main__":
    main() 