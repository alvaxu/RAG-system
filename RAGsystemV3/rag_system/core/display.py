"""
RAG前端展示模块

RAG系统的前端展示模块，负责Vue 3.x界面、响应式设计和多模式展示
为RAG系统提供完整的用户界面支持
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class DisplayMode(Enum):
    """展示模式枚举"""
    CHAT = "chat"                      # 聊天模式
    SEARCH = "search"                   # 搜索模式
    ANALYSIS = "analysis"               # 分析模式
    COMPARISON = "comparison"           # 对比模式
    DASHBOARD = "dashboard"             # 仪表板模式


@dataclass
class DisplayConfig:
    """展示配置"""
    mode: DisplayMode                   # 展示模式
    theme: str                          # 主题（light/dark）
    language: str                       # 语言（zh-CN/en-US）
    responsive: bool                    # 是否响应式
    animations: bool                    # 是否启用动画
    accessibility: bool                 # 是否启用无障碍功能


@dataclass
class DisplayData:
    """展示数据"""
    query_text: str                     # 查询文本
    answer_text: str                    # 答案文本
    sources: List[Dict[str, Any]]      # 来源信息
    attribution: Dict[str, Any]        # 溯源信息
    metadata: Dict[str, Any]           # 元数据


class DisplaySelector:
    """展示模式选择器"""
    
    def __init__(self, config_integration):
        """
        初始化展示模式选择器
        
        :param config_integration: RAG配置集成管理器实例
        """
        self.config = config_integration
        self.default_config = self._load_default_config()
        logger.info("展示模式选择器初始化完成")
    
    def _load_default_config(self) -> DisplayConfig:
        """加载默认展示配置"""
        try:
            # 从配置中读取默认设置
            display_config = self.config.get('rag_system.display', {})
            
            return DisplayConfig(
                mode=DisplayMode(display_config.get('default_mode', 'chat')),
                theme=display_config.get('theme', 'light'),
                language=display_config.get('language', 'zh-CN'),
                responsive=display_config.get('responsive', True),
                animations=display_config.get('animations', True),
                accessibility=display_config.get('accessibility', True)
            )
            
        except Exception as e:
            logger.error(f"加载默认展示配置失败: {e}")
            # 返回硬编码默认值
            return DisplayConfig(
                mode=DisplayMode.CHAT,
                theme='light',
                language='zh-CN',
                responsive=True,
                animations=True,
                accessibility=True
            )
    
    def select_display_mode(self, query_type: str, content_type: str, 
                           user_preference: str = None) -> DisplayMode:
        """
        智能选择展示模式
        
        :param query_type: 查询类型
        :param content_type: 内容类型
        :param user_preference: 用户偏好
        :return: 推荐的展示模式
        """
        try:
            # 如果用户有明确偏好，优先使用
            if user_preference:
                try:
                    return DisplayMode(user_preference)
                except ValueError:
                    logger.warning(f"无效的用户偏好展示模式: {user_preference}")
            
            # 基于查询类型和内容类型智能选择
            if query_type == 'comparison':
                return DisplayMode.COMPARISON
            elif query_type == 'analysis':
                return DisplayMode.ANALYSIS
            elif content_type == 'image':
                return DisplayMode.SEARCH
            elif query_type == 'search':
                return DisplayMode.SEARCH
            else:
                return DisplayMode.CHAT
                
        except Exception as e:
            logger.error(f"选择展示模式失败: {e}")
            return self.default_config.mode
    
    def get_display_config(self, mode: DisplayMode = None) -> DisplayConfig:
        """
        获取展示配置
        
        :param mode: 展示模式
        :return: 展示配置
        """
        try:
            if mode is None:
                mode = self.default_config.mode
            
            # 从配置中读取特定模式的配置
            mode_config = self.config.get(f'rag_system.display.modes.{mode.value}', {})
            
            return DisplayConfig(
                mode=mode,
                theme=mode_config.get('theme', self.default_config.theme),
                language=mode_config.get('language', self.default_config.language),
                responsive=mode_config.get('responsive', self.default_config.responsive),
                animations=mode_config.get('animations', self.default_config.animations),
                accessibility=mode_config.get('accessibility', self.default_config.accessibility)
            )
            
        except Exception as e:
            logger.error(f"获取展示配置失败: {e}")
            return self.default_config


class VueComponentGenerator:
    """Vue组件生成器"""
    
    def __init__(self, display_config: DisplayConfig):
        """
        初始化Vue组件生成器
        
        :param display_config: 展示配置
        """
        self.config = display_config
        logger.info("Vue组件生成器初始化完成")
    
    def generate_chat_component(self, display_data: DisplayData) -> str:
        """
        生成聊天模式Vue组件
        
        :param display_data: 展示数据
        :return: Vue组件代码
        """
        try:
            component_code = f"""
<template>
  <div class="rag-chat-container" :class="themeClass">
    <!-- 聊天历史 -->
    <div class="chat-history" ref="chatHistory">
      <div v-for="(message, index) in chatMessages" :key="index" 
           class="message" :class="message.type">
        <div class="message-content">
          <div class="message-text" v-html="message.text"></div>
          <div v-if="message.type === 'answer'" class="message-sources">
            <div class="sources-header">
              <span class="sources-title">来源信息</span>
              <span class="sources-count">({message.sources.length}个来源)</span>
            </div>
            <div class="sources-list">
              <div v-for="source in message.sources" :key="source.chunk_id" 
                   class="source-item">
                <div class="source-header">
                  <span class="source-document">{{ source.document_name }}</span>
                  <span class="source-page">第{{ source.page_number }}页</span>
                  <span class="source-type">{{ source.content_type }}</span>
                </div>
                <div class="source-preview">{{ source.content_preview }}</div>
                <div class="source-meta">
                  <span class="source-score">相关性: {{ source.relevance_score.toFixed(2) }}</span>
                  <span class="source-confidence">置信度: {{ source.confidence_level }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="message-timestamp">{{ formatTimestamp(message.timestamp) }}</div>
      </div>
    </div>
    
    <!-- 输入区域 -->
    <div class="chat-input-area">
      <div class="input-container">
        <textarea 
          v-model="currentQuery" 
          @keydown.enter.prevent="sendQuery"
          placeholder="请输入您的问题..."
          class="query-input"
          :disabled="isProcessing"
        ></textarea>
        <button @click="sendQuery" :disabled="isProcessing || !currentQuery.trim()" 
                class="send-button">
          <span v-if="!isProcessing">发送</span>
          <span v-else class="loading-spinner"></span>
        </button>
      </div>
      <div class="input-options">
        <label class="option-item">
          <input type="checkbox" v-model="showSources" />
          <span>显示来源</span>
        </label>
        <label class="option-item">
          <input type="checkbox" v-model="showAttribution" />
          <span>显示溯源</span>
        </label>
      </div>
    </div>
  </div>
</template>

<script setup>
import {{ ref, computed, nextTick, onMounted }} from 'vue'

// 响应式数据
const currentQuery = ref('')
const chatMessages = ref([])
const isProcessing = ref(false)
const showSources = ref(true)
const showAttribution = ref(true)
const chatHistory = ref(null)

// 计算属性
const themeClass = computed(() => `theme-${props.theme}`)

// Props
const props = defineProps({{
  theme: {{
    type: String,
    default: '{self.config.theme}'
  }},
  language: {{
    type: String,
    default: '{self.config.language}'
  }}
}})

// 方法
const sendQuery = async () => {{
  if (!currentQuery.value.trim() || isProcessing.value) return
  
  const queryText = currentQuery.value.trim()
  currentQuery.value = ''
  
  // 添加用户查询消息
  addMessage('user', queryText)
  
  isProcessing.value = true
  
  try {{
    // 调用RAG API
    const response = await callRAGAPI(queryText)
    
    // 添加AI答案消息
    addMessage('answer', response.answer, response.sources, response.attribution)
    
  }} catch (error) {{
    console.error('查询失败:', error)
    addMessage('error', '抱歉，查询失败，请稍后重试。')
  }} finally {{
    isProcessing.value = false
  }}
}}

const addMessage = (type, text, sources = [], attribution = null) => {{
  const message = {{
    type,
    text,
    sources,
    attribution,
    timestamp: new Date()
  }}
  
  chatMessages.value.push(message)
  
  // 滚动到底部
  nextTick(() => {{
    if (chatHistory.value) {{
      chatHistory.value.scrollTop = chatHistory.value.scrollHeight
    }}
  }})
}}

const formatTimestamp = (timestamp) => {{
  return new Date(timestamp).toLocaleTimeString('zh-CN', {{
    hour: '2-digit',
    minute: '2-digit'
  }})
}}

const callRAGAPI = async (query) => {{
  // 这里应该调用实际的RAG API
  // 暂时返回模拟数据
  return {{
    answer: '这是一个模拟的RAG答案，实际应该调用后端API。',
    sources: [],
    attribution: null
  }}
}}

// 生命周期
onMounted(() => {{
  // 添加欢迎消息
  addMessage('system', '您好！我是RAG智能助手，请问有什么可以帮助您的？')
}})
</script>

<style scoped>
.rag-chat-container {{
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-color);
  color: var(--text-color);
}}

.chat-history {{
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}}

.message {{
  display: flex;
  flex-direction: column;
  max-width: 80%;
}}

.message.user {{
  align-self: flex-end;
}}

.message.answer, .message.system, .message.error {{
  align-self: flex-start;
}}

.message-content {{
  padding: 15px 20px;
  border-radius: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}}

.message.user .message-content {{
  background-color: var(--primary-color);
  color: white;
}}

.message.answer .message-content {{
  background-color: var(--secondary-bg);
  border: 1px solid var(--border-color);
}}

.message.system .message-content {{
  background-color: var(--info-bg);
  color: var(--info-text);
}}

.message.error .message-content {{
  background-color: var(--error-bg);
  color: var(--error-text);
}}

.message-sources {{
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid var(--border-color);
}}

.sources-header {{
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}}

.sources-title {{
  font-weight: 600;
  color: var(--text-color);
}}

.sources-count {{
  font-size: 0.9em;
  color: var(--text-muted);
}}

.sources-list {{
  display: flex;
  flex-direction: column;
  gap: 10px;
}}

.source-item {{
  padding: 10px;
  background-color: var(--bg-light);
  border-radius: 8px;
  border: 1px solid var(--border-light);
}}

.source-header {{
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}}

.source-document {{
  font-weight: 600;
  color: var(--text-color);
}}

.source-page, .source-type {{
  font-size: 0.9em;
  color: var(--text-muted);
}}

.source-preview {{
  font-size: 0.9em;
  color: var(--text-color);
  margin-bottom: 8px;
  line-height: 1.4;
}}

.source-meta {{
  display: flex;
  gap: 15px;
  font-size: 0.8em;
  color: var(--text-muted);
}}

.chat-input-area {{
  padding: 20px;
  border-top: 1px solid var(--border-color);
  background-color: var(--bg-color);
}}

.input-container {{
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}}

.query-input {{
  flex: 1;
  padding: 12px 16px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  resize: none;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.4;
  background-color: var(--input-bg);
  color: var(--text-color);
}}

.query-input:focus {{
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px var(--primary-light);
}}

.send-button {{
  padding: 12px 24px;
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: background-color 0.2s;
}}

.send-button:hover:not(:disabled) {{
  background-color: var(--primary-dark);
}}

.send-button:disabled {{
  background-color: var(--disabled-bg);
  cursor: not-allowed;
}}

.input-options {{
  display: flex;
  gap: 20px;
}}

.option-item {{
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--text-muted);
  cursor: pointer;
}}

.option-item input[type="checkbox"] {{
  margin: 0;
}}

.loading-spinner {{
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top: 2px solid currentColor;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}}

@keyframes spin {{
  0% {{ transform: rotate(0deg); }}
  100% {{ transform: rotate(360deg); }}
}}

/* 响应式设计 */
@media (max-width: 768px) {{
  .message {{
    max-width: 90%;
  }}
  
  .chat-input-area {{
    padding: 15px;
  }}
  
  .input-container {{
    flex-direction: column;
  }}
  
  .send-button {{
    width: 100%;
  }}
}}

/* 主题变量 */
.theme-light {{
  --bg-color: #ffffff;
  --text-color: #333333;
  --text-muted: #666666;
  --primary-color: #1890ff;
  --primary-dark: #096dd9;
  --primary-light: rgba(24, 144, 255, 0.2);
  --secondary-bg: #f8f9fa;
  --border-color: #e8e8e8;
  --border-light: #f0f0f0;
  --bg-light: #fafafa;
  --input-bg: #ffffff;
  --info-bg: #e6f7ff;
  --info-text: #1890ff;
  --error-bg: #fff2f0;
  --error-text: #ff4d4f;
  --disabled-bg: #f5f5f5;
}}

.theme-dark {{
  --bg-color: #1f1f1f;
  --text-color: #ffffff;
  --text-muted: #a0a0a0;
  --primary-color: #1890ff;
  --primary-dark: #096dd9;
  --primary-light: rgba(24, 144, 255, 0.2);
  --secondary-bg: #2a2a2a;
  --border-color: #404040;
  --border-light: #333333;
  --bg-light: #262626;
  --input-bg: #2a2a2a;
  --info-bg: #111b26;
  --info-text: #1890ff;
  --error-bg: #2a1215;
  --error-text: #ff7875;
  --disabled-bg: #404040;
}}
</style>
"""
            
            return component_code
            
        except Exception as e:
            logger.error(f"生成聊天模式Vue组件失败: {e}")
            return "// Vue组件生成失败"
    
    def generate_search_component(self, display_data: DisplayData) -> str:
        """
        生成搜索模式Vue组件
        
        :param display_data: 展示数据
        :return: Vue组件代码
        """
        try:
            component_code = f"""
<template>
  <div class="rag-search-container" :class="themeClass">
    <!-- 搜索头部 -->
    <div class="search-header">
      <h1 class="search-title">RAG智能搜索</h1>
      <div class="search-description">基于向量数据库的智能内容检索</div>
    </div>
    
    <!-- 搜索输入 -->
    <div class="search-input-section">
      <div class="search-input-container">
        <input 
          v-model="searchQuery" 
          @keydown.enter="performSearch"
          placeholder="输入搜索关键词..."
          class="search-input"
          :disabled="isSearching"
        />
        <button @click="performSearch" :disabled="isSearching || !searchQuery.trim()" 
                class="search-button">
          <span v-if="!isSearching">搜索</span>
          <span v-else class="loading-spinner"></span>
        </button>
      </div>
      
      <!-- 搜索选项 -->
      <div class="search-options">
        <div class="option-group">
          <label class="option-label">内容类型:</label>
          <select v-model="selectedContentType" class="option-select">
            <option value="all">全部</option>
            <option value="text">文本</option>
            <option value="image">图片</option>
            <option value="table">表格</option>
          </select>
        </div>
        
        <div class="option-group">
          <label class="option-label">结果数量:</label>
          <select v-model="maxResults" class="option-select">
            <option value="10">10</option>
            <option value="20">20</option>
            <option value="50">50</option>
          </select>
        </div>
        
        <div class="option-group">
          <label class="option-label">相似度阈值:</label>
          <input 
            type="range" 
            v-model="similarityThreshold" 
            min="0" 
            max="1" 
            step="0.1"
            class="option-range"
          />
          <span class="threshold-value">{{ similarityThreshold }}</span>
        </div>
      </div>
    </div>
    
    <!-- 搜索结果 -->
    <div v-if="searchResults.length > 0" class="search-results">
      <div class="results-header">
        <h2>搜索结果 ({{ searchResults.length }})</h2>
        <div class="results-stats">
          <span>搜索耗时: {{ searchTime }}ms</span>
          <span>平均相似度: {{ averageSimilarity.toFixed(2) }}</span>
        </div>
      </div>
      
      <div class="results-list">
        <div v-for="(result, index) in searchResults" :key="result.chunk_id" 
             class="result-item" :class="result.chunk_type">
          <div class="result-header">
            <div class="result-meta">
              <span class="result-rank">#{{ index + 1 }}</span>
              <span class="result-type">{{ getContentTypeLabel(result.chunk_type) }}</span>
              <span class="result-document">{{ result.document_name }}</span>
              <span v-if="result.page_number > 0" class="result-page">
                第{{ result.page_number }}页
              </span>
            </div>
            <div class="result-score">
              <span class="score-label">相似度:</span>
              <span class="score-value" :class="getScoreClass(result.similarity_score)">
                {{ result.similarity_score.toFixed(3) }}
              </span>
            </div>
          </div>
          
          <div class="result-content">
            <div v-if="result.chunk_type === 'image'" class="image-content">
              <img :src="result.image_url" :alt="result.description" class="result-image" />
              <div class="image-description">{{ result.description }}</div>
            </div>
            <div v-else class="text-content">
              {{ result.content }}
            </div>
          </div>
          
          <div class="result-actions">
            <button @click="viewDetails(result)" class="action-button view-button">
              查看详情
            </button>
            <button @click="copyContent(result)" class="action-button copy-button">
              复制内容
            </button>
            <button @click="addToCollection(result)" class="action-button collect-button">
              收藏
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 无结果提示 -->
    <div v-else-if="hasSearched && searchResults.length === 0" class="no-results">
      <div class="no-results-icon">🔍</div>
      <h3>未找到相关结果</h3>
      <p>请尝试调整搜索关键词或降低相似度阈值</p>
    </div>
    
    <!-- 搜索建议 -->
    <div v-if="searchSuggestions.length > 0" class="search-suggestions">
      <h3>搜索建议</h3>
      <div class="suggestions-list">
        <span 
          v-for="suggestion in searchSuggestions" 
          :key="suggestion"
          @click="useSuggestion(suggestion)"
          class="suggestion-item"
        >
          {{ suggestion }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import {{ ref, computed, onMounted }} from 'vue'

// 响应式数据
const searchQuery = ref('')
const selectedContentType = ref('all')
const maxResults = ref(20)
const similarityThreshold = ref(0.5)
const searchResults = ref([])
const isSearching = ref(false)
const hasSearched = ref(false)
const searchTime = ref(0)
const searchSuggestions = ref([])

// Props
const props = defineProps({{
  theme: {{
    type: String,
    default: '{self.config.theme}'
  }},
  language: {{
    type: String,
    default: '{self.config.language}'
  }}
}})

// 计算属性
const themeClass = computed(() => `theme-${props.theme}`)
const averageSimilarity = computed(() => {{
  if (searchResults.value.length === 0) return 0
  const total = searchResults.value.reduce((sum, result) => sum + result.similarity_score, 0)
  return total / searchResults.value.length
}})

// 方法
const performSearch = async () => {{
  if (!searchQuery.value.trim() || isSearching.value) return
  
  isSearching.value = true
  hasSearched.value = true
  const startTime = Date.now()
  
  try {{
    // 调用RAG搜索API
    const response = await callSearchAPI({{
      query: searchQuery.value,
      content_type: selectedContentType.value,
      max_results: parseInt(maxResults.value),
      similarity_threshold: parseFloat(similarityThreshold.value)
    }})
    
    searchResults.value = response.results || []
    searchSuggestions.value = response.suggestions || []
    
  }} catch (error) {{
    console.error('搜索失败:', error)
    searchResults.value = []
    searchSuggestions.value = []
  }} finally {{
    isSearching.value = false
    searchTime.value = Date.now() - startTime
  }}
}}

const getContentTypeLabel = (type) => {{
  const labels = {{
    'text': '文本',
    'image': '图片',
    'table': '表格'
  }}
  return labels[type] || type
}}

const getScoreClass = (score) => {{
  if (score >= 0.8) return 'score-high'
  if (score >= 0.6) return 'score-medium'
  return 'score-low'
}}

const viewDetails = (result) => {{
  // 实现查看详情功能
  console.log('查看详情:', result)
}}

const copyContent = async (result) => {{
  try {{
    const content = result.content || result.description || ''
    await navigator.clipboard.writeText(content)
    // 显示复制成功提示
  }} catch (error) {{
    console.error('复制失败:', error)
  }}
}}

const addToCollection = (result) => {{
  // 实现添加到收藏功能
  console.log('添加到收藏:', result)
}}

const useSuggestion = (suggestion) => {{
  searchQuery.value = suggestion
  performSearch()
}}

const callSearchAPI = async (params) => {{
  // 这里应该调用实际的RAG搜索API
  // 暂时返回模拟数据
  return {{
    results: [
      {{
        chunk_id: 'mock_1',
        chunk_type: 'text',
        document_name: '示例文档.pdf',
        page_number: 1,
        content: '这是一个示例搜索结果，实际应该调用后端API。',
        similarity_score: 0.85,
        description: '示例文本内容'
      }}
    ],
    suggestions: ['相关建议1', '相关建议2']
  }}
}}

// 生命周期
onMounted(() => {{
  // 初始化搜索建议
  searchSuggestions.value = ['热门搜索1', '热门搜索2', '热门搜索3']
}})
</script>

<style scoped>
.rag-search-container {{
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  background-color: var(--bg-color);
  color: var(--text-color);
  min-height: 100vh;
}}

.search-header {{
  text-align: center;
  margin-bottom: 40px;
}}

.search-title {{
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 10px;
  color: var(--primary-color);
}}

.search-description {{
  font-size: 1.1rem;
  color: var(--text-muted);
}}

.search-input-section {{
  margin-bottom: 40px;
}}

.search-input-container {{
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
}}

.search-input {{
  flex: 1;
  padding: 15px 20px;
  border: 2px solid var(--border-color);
  border-radius: 10px;
  font-size: 16px;
  background-color: var(--input-bg);
  color: var(--text-color);
  transition: border-color 0.3s;
}}

.search-input:focus {{
  outline: none;
  border-color: var(--primary-color);
}}

.search-button {{
  padding: 15px 30px;
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.3s;
}}

.search-button:hover:not(:disabled) {{
  background-color: var(--primary-dark);
}}

.search-button:disabled {{
  background-color: var(--disabled-bg);
  cursor: not-allowed;
}}

.search-options {{
  display: flex;
  gap: 30px;
  align-items: center;
  flex-wrap: wrap;
}}

.option-group {{
  display: flex;
  align-items: center;
  gap: 10px;
}}

.option-label {{
  font-weight: 600;
  color: var(--text-color);
}}

.option-select {{
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background-color: var(--input-bg);
  color: var(--text-color);
}}

.option-range {{
  width: 100px;
}}

.threshold-value {{
  min-width: 30px;
  text-align: center;
  font-weight: 600;
  color: var(--primary-color);
}}

.search-results {{
  margin-bottom: 40px;
}}

.results-header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid var(--border-color);
}}

.results-header h2 {{
  margin: 0;
  color: var(--text-color);
}}

.results-stats {{
  display: flex;
  gap: 20px;
  color: var(--text-muted);
  font-size: 0.9rem;
}}

.results-list {{
  display: flex;
  flex-direction: column;
  gap: 20px;
}}

.result-item {{
  padding: 20px;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  background-color: var(--secondary-bg);
  transition: transform 0.2s, box-shadow 0.2s;
}}

.result-item:hover {{
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}}

.result-header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}}

.result-meta {{
  display: flex;
  align-items: center;
  gap: 15px;
}}

.result-rank {{
  font-weight: 700;
  color: var(--primary-color);
  font-size: 1.1rem;
}}

.result-type {{
  padding: 4px 8px;
  background-color: var(--primary-light);
  color: var(--primary-color);
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 600;
}}

.result-document {{
  font-weight: 600;
  color: var(--text-color);
}}

.result-page {{
  color: var(--text-muted);
  font-size: 0.9rem;
}}

.result-score {{
  display: flex;
  align-items: center;
  gap: 8px;
}}

.score-label {{
  color: var(--text-muted);
  font-size: 0.9rem;
}}

.score-value {{
  font-weight: 700;
  font-size: 1.1rem;
}}

.score-high {{ color: #52c41a; }}
.score-medium {{ color: #faad14; }}
.score-low {{ color: #ff4d4f; }}

.result-content {{
  margin-bottom: 20px;
  line-height: 1.6;
}}

.image-content {{
  text-align: center;
}}

.result-image {{
  max-width: 100%;
  max-height: 300px;
  border-radius: 8px;
  margin-bottom: 10px;
}}

.image-description {{
  color: var(--text-muted);
  font-style: italic;
}}

.result-actions {{
  display: flex;
  gap: 10px;
}}

.action-button {{
  padding: 8px 16px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background-color: var(--bg-color);
  color: var(--text-color);
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9rem;
}}

.view-button:hover {{
  background-color: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}}

.copy-button:hover {{
  background-color: var(--success-color);
  color: white;
  border-color: var(--success-color);
}}

.collect-button:hover {{
  background-color: var(--warning-color);
  color: white;
  border-color: var(--warning-color);
}}

.no-results {{
  text-align: center;
  padding: 60px 20px;
  color: var(--text-muted);
}}

.no-results-icon {{
  font-size: 4rem;
  margin-bottom: 20px;
}}

.no-results h3 {{
  margin-bottom: 10px;
  color: var(--text-color);
}}

.search-suggestions {{
  margin-top: 40px;
}}

.search-suggestions h3 {{
  margin-bottom: 15px;
  color: var(--text-color);
}}

.suggestions-list {{
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}}

.suggestion-item {{
  padding: 8px 16px;
  background-color: var(--secondary-bg);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9rem;
}}

.suggestion-item:hover {{
  background-color: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}}

.loading-spinner {{
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top: 2px solid currentColor;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}}

@keyframes spin {{
  0% {{ transform: rotate(0deg); }}
  100% {{ transform: rotate(360deg); }}
}}

/* 响应式设计 */
@media (max-width: 768px) {{
  .rag-search-container {{
    padding: 15px;
  }}
  
  .search-title {{
    font-size: 2rem;
  }}
  
  .search-input-container {{
    flex-direction: column;
  }}
  
  .search-options {{
    flex-direction: column;
    align-items: stretch;
  }}
  
  .results-header {{
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }}
  
  .result-header {{
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }}
  
  .result-actions {{
    flex-wrap: wrap;
  }}
}}

/* 主题变量 */
.theme-light {{
  --bg-color: #ffffff;
  --text-color: #333333;
  --text-muted: #666666;
  --primary-color: #1890ff;
  --primary-dark: #096dd9;
  --primary-light: rgba(24, 144, 255, 0.2);
  --secondary-bg: #f8f9fa;
  --border-color: #e8e8e8;
  --input-bg: #ffffff;
  --success-color: #52c41a;
  --warning-color: #faad14;
  --disabled-bg: #f5f5f5;
}}

.theme-dark {{
  --bg-color: #1f1f1f;
  --text-color: #ffffff;
  --text-muted: #a0a0a0;
  --primary-color: #1890ff;
  --primary-dark: #096dd9;
  --primary-light: rgba(24, 144, 255, 0.2);
  --secondary-bg: #2a2a2a;
  --border-color: #404040;
  --input-bg: #2a2a2a;
  --success-color: #52c41a;
  --warning-color: #faad14;
  --disabled-bg: #404040;
}}
</style>
"""
            
            return component_code
            
        except Exception as e:
            logger.error(f"生成搜索模式Vue组件失败: {e}")
            return "// Vue组件生成失败"
    
    def generate_component_wrapper(self, component_code: str, component_name: str) -> str:
        """
        生成Vue组件包装器
        
        :param component_code: 组件代码
        :param component_name: 组件名称
        :return: 包装后的组件代码
        """
        try:
            wrapper_code = f"""
{component_code}

// 组件导出
export default {{
  name: '{component_name}',
  setup() {{
    // 组件逻辑已在上面定义
  }}
}}
"""
            return wrapper_code
            
        except Exception as e:
            logger.error(f"生成Vue组件包装器失败: {e}")
            return "// Vue组件包装器生成失败"
    
    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态信息"""
        return {
            'status': 'ready',
            'service_type': 'Vue Component Generator',
            'supported_modes': ['chat', 'search', 'analysis', 'comparison', 'dashboard'],
            'supported_themes': ['light', 'dark'],
            'supported_languages': ['zh-CN', 'en-US'],
            'features': [
                'responsive_design',
                'theme_support',
                'accessibility',
                'animations',
                'component_generation'
            ]
        }


class DisplayService:
    """展示服务 - RAG系统的前端展示管理"""
    
    def __init__(self, config_integration):
        """
        初始化展示服务
        
        :param config_integration: RAG配置集成管理器实例
        """
        self.config = config_integration
        self.display_selector = DisplaySelector(config_integration)
        self.vue_generator = None  # 延迟初始化
        logger.info("展示服务初始化完成")
    
    def get_display_mode(self, query_type: str, content_type: str, 
                        user_preference: str = None) -> DisplayMode:
        """
        获取展示模式
        
        :param query_type: 查询类型
        :param content_type: 内容类型
        :param user_preference: 用户偏好
        :return: 展示模式
        """
        try:
            return self.display_selector.select_display_mode(query_type, content_type, user_preference)
        except Exception as e:
            logger.error(f"获取展示模式失败: {e}")
            return DisplayMode.CHAT
    
    def get_display_config(self, mode: DisplayMode = None) -> DisplayConfig:
        """
        获取展示配置
        
        :param mode: 展示模式
        :return: 展示配置
        """
        try:
            return self.display_selector.get_display_config(mode)
        except Exception as e:
            logger.error(f"获取展示配置失败: {e}")
            return self.display_selector.default_config
    
    def generate_vue_component(self, mode: DisplayMode, display_data: DisplayData) -> str:
        """
        生成Vue组件
        
        :param mode: 展示模式
        :param display_data: 展示数据
        :return: Vue组件代码
        """
        try:
            # 延迟初始化Vue组件生成器
            if self.vue_generator is None:
                config = self.get_display_config(mode)
                self.vue_generator = VueComponentGenerator(config)
            
            # 根据模式生成不同的组件
            if mode == DisplayMode.CHAT:
                component_code = self.vue_generator.generate_chat_component(display_data)
            elif mode == DisplayMode.SEARCH:
                component_code = self.vue_generator.generate_search_component(display_data)
            else:
                # 默认使用聊天模式
                component_code = self.vue_generator.generate_chat_component(display_data)
            
            # 生成组件包装器
            component_name = f"RAG{mode.value.capitalize()}Component"
            return self.vue_generator.generate_component_wrapper(component_code, component_name)
            
        except Exception as e:
            logger.error(f"生成Vue组件失败: {e}")
            return "// Vue组件生成失败"
    
    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态信息"""
        return {
            'status': 'ready',
            'service_type': 'RAG Display Service',
            'display_selector': self.display_selector.get_service_status(),
            'vue_generator': self.vue_generator.get_service_status() if self.vue_generator else None,
            'supported_modes': [mode.value for mode in DisplayMode],
            'features': [
                'display_mode_selection',
                'vue_component_generation',
                'responsive_design',
                'theme_support',
                'accessibility'
            ]
        }
