<template>
  <div class="chat-container">
    <!-- 聊天头部 -->
    <div class="chat-header">
      <div class="header-content">
        <div class="header-left">
          <el-icon class="header-icon"><ChatDotRound /></el-icon>
          <h1>智能问答</h1>
        </div>
        <div class="header-right">
          <el-button-group>
            <el-button 
              :type="selectedQueryType === 'smart' ? 'primary' : ''"
              @click="selectQueryType('smart')"
              size="small"
            >
              <el-icon><MagicStick /></el-icon>
              智能查询
            </el-button>
            <el-button 
              :type="selectedQueryType === 'text' ? 'primary' : ''"
              @click="selectQueryType('text')"
              size="small"
            >
              <el-icon><Document /></el-icon>
              文本查询
            </el-button>
            <el-button 
              :type="selectedQueryType === 'image' ? 'primary' : ''"
              @click="selectQueryType('image')"
              size="small"
            >
              <el-icon><Picture /></el-icon>
              图片查询
            </el-button>
            <el-button 
              :type="selectedQueryType === 'table' ? 'primary' : ''"
              @click="selectQueryType('table')"
              size="small"
            >
              <el-icon><Grid /></el-icon>
              表格查询
            </el-button>
            <el-button 
              :type="selectedQueryType === 'hybrid' ? 'primary' : ''"
              @click="selectQueryType('hybrid')"
              size="small"
            >
              <el-icon><Connection /></el-icon>
              混合查询
            </el-button>
          </el-button-group>
          <el-button @click="clearHistory" size="small" plain>
            <el-icon><Delete /></el-icon>
            清空历史
          </el-button>
        </div>
      </div>
    </div>

    <!-- 聊天内容区域 -->
    <div class="chat-content" ref="chatContent">
      <div class="chat-messages">
        <!-- 欢迎消息 -->
        <div v-if="messages.length === 0" class="welcome-message">
          <div class="welcome-content">
            <el-icon class="welcome-icon"><ChatDotRound /></el-icon>
            <h2>欢迎使用RAG智能问答系统</h2>
            <p>我是您的AI助手，可以帮您查询文档、回答问题。请选择查询类型并输入您的问题。</p>
            <div class="query-type-info">
              <el-tag 
                v-for="(config, type) in queryTypeConfigs" 
                :key="type"
                :type="selectedQueryType === type ? 'primary' : ''"
                class="type-tag"
              >
                <el-icon><component :is="config.icon" /></el-icon>
                {{ config.label }}
              </el-tag>
            </div>
          </div>
        </div>

        <!-- 消息列表 -->
        <div 
          v-for="message in messages" 
          :key="message.id"
          class="message-item"
          :class="[`message-${message.type}`, { 'message-loading': message.loading }]"
        >
          <div class="message-avatar">
            <el-icon v-if="message.type === 'user'"><User /></el-icon>
            <el-icon v-else-if="message.type === 'assistant'"><Robot /></el-icon>
            <el-icon v-else><InfoFilled /></el-icon>
          </div>
          <div class="message-content">
            <div class="message-header">
              <span class="message-type">{{ getMessageTypeLabel(message.type) }}</span>
              <span class="message-time">{{ formatTimestamp(message.timestamp) }}</span>
            </div>
            <div class="message-body">
              <!-- 用户消息 -->
              <div v-if="message.type === 'user'" class="user-message">
                <div class="query-type-badge">
                  <el-icon><component :is="queryTypeConfigs[message.queryType]?.icon" /></el-icon>
                  {{ queryTypeConfigs[message.queryType]?.label }}
                </div>
                <div class="query-text">{{ message.content }}</div>
              </div>

              <!-- AI回答 -->
              <div v-else-if="message.type === 'assistant'" class="assistant-message">
                <div class="answer-content" v-html="message.content"></div>
                
                <!-- 来源信息 -->
                <div v-if="message.sources && message.sources.length > 0" class="sources-section">
                  <div class="sources-header">
                    <el-icon><Link /></el-icon>
                    <span>来源信息 ({{ message.sources.length }}个)</span>
                  </div>
                  <div class="sources-list">
                    <div 
                      v-for="(source, index) in message.sources" 
                      :key="index"
                      class="source-item"
                    >
                      <div class="source-header">
                        <div class="source-meta">
                          <el-tag size="small" :type="getSourceTypeTag(source.content_type)">
                            {{ getContentTypeLabel(source.content_type) }}
                          </el-tag>
                          <span class="source-document">{{ source.document_name }}</span>
                          <span v-if="source.page_number > 0" class="source-page">
                            第{{ source.page_number }}页
                          </span>
                        </div>
                        <div class="source-score">
                          <el-tag 
                            size="small" 
                            :type="getScoreTagType(source.relevance_score)"
                          >
                            相关性: {{ formatSimilarityScore(source.relevance_score) }}
                          </el-tag>
                        </div>
                      </div>
                      <div class="source-preview">{{ truncateText(source.content_preview, 200) }}</div>
                    </div>
                  </div>
                </div>

                <!-- 溯源信息 -->
                <div v-if="message.attribution" class="attribution-section">
                  <div class="attribution-header">
                    <el-icon><Shield /></el-icon>
                    <span>溯源信息</span>
                  </div>
                  <div class="attribution-content">
                    <div class="attribution-summary">{{ message.attribution.attribution_summary }}</div>
                    <div class="attribution-confidence">
                      <span>整体置信度: </span>
                      <el-tag 
                        :type="getConfidenceTagType(message.attribution.overall_confidence)"
                        size="small"
                      >
                        {{ (message.attribution.overall_confidence * 100).toFixed(1) }}%
                      </el-tag>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 系统消息 -->
              <div v-else-if="message.type === 'system'" class="system-message">
                <el-icon><InfoFilled /></el-icon>
                <span>{{ message.content }}</span>
              </div>

              <!-- 错误消息 -->
              <div v-else-if="message.type === 'error'" class="error-message">
                <el-icon><CircleCloseFilled /></el-icon>
                <span>{{ message.content }}</span>
              </div>

              <!-- 加载状态 -->
              <div v-if="message.loading" class="loading-indicator">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span>正在思考中...</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="chat-input">
      <div class="input-container">
        <div class="input-wrapper">
          <el-input
            v-model="currentQuery"
            type="textarea"
            :rows="3"
            placeholder="请输入您的问题..."
            :disabled="isLoading"
            @keydown.ctrl.enter="sendQuery"
            class="query-input"
          />
          <div class="input-actions">
            <div class="input-options">
              <el-checkbox v-model="showSources">显示来源</el-checkbox>
              <el-checkbox v-model="showAttribution">显示溯源</el-checkbox>
            </div>
            <el-button 
              type="primary" 
              @click="sendQuery"
              :loading="isLoading"
              :disabled="!currentQuery.trim()"
              class="send-button"
            >
              <el-icon><Promotion /></el-icon>
              发送
            </el-button>
          </div>
        </div>
        <div class="input-tips">
          <span>按 Ctrl+Enter 发送消息</span>
          <span>当前查询类型: {{ queryTypeConfigs[selectedQueryType]?.label }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import ragAPI from '@/services/api.js'
import { 
  QUERY_TYPES, 
  QUERY_TYPE_CONFIG, 
  MESSAGE_TYPES,
  STORAGE_KEYS 
} from '@/utils/constants.js'
import { 
  formatTimestamp, 
  formatSimilarityScore, 
  truncateText,
  getContentTypeLabel,
  generateId,
  validateQuery 
} from '@/utils/helpers.js'

// 响应式数据
const currentQuery = ref('')
const messages = ref([])
const isLoading = ref(false)
const selectedQueryType = ref(QUERY_TYPES.SMART)
const showSources = ref(true)
const showAttribution = ref(true)
const chatContent = ref(null)

// 计算属性
const queryTypeConfigs = computed(() => QUERY_TYPE_CONFIG)

// 方法
const selectQueryType = (type) => {
  selectedQueryType.value = type
  ElMessage.success(`已切换到${QUERY_TYPE_CONFIG[type].label}`)
}

const sendQuery = async () => {
  const query = currentQuery.value.trim()
  
  // 验证查询
  const validation = validateQuery(query)
  if (!validation.valid) {
    ElMessage.warning(validation.message)
    return
  }

  // 添加用户消息
  const userMessage = {
    id: generateId('msg'),
    type: MESSAGE_TYPES.USER,
    content: query,
    queryType: selectedQueryType.value,
    timestamp: Date.now()
  }
  messages.value.push(userMessage)

  // 添加加载消息
  const loadingMessage = {
    id: generateId('msg'),
    type: MESSAGE_TYPES.ASSISTANT,
    content: '',
    loading: true,
    timestamp: Date.now()
  }
  messages.value.push(loadingMessage)

  // 清空输入框
  currentQuery.value = ''
  isLoading.value = true

  // 滚动到底部
  await nextTick()
  scrollToBottom()

  try {
    // 发送查询请求
    const response = await ragAPI.sendQuery({
      query,
      query_type: selectedQueryType.value,
      max_results: 10,
      similarity_threshold: 0.5
    })

    // 移除加载消息
    const loadingIndex = messages.value.findIndex(msg => msg.id === loadingMessage.id)
    if (loadingIndex !== -1) {
      messages.value.splice(loadingIndex, 1)
    }

    // 添加AI回答
    const assistantMessage = {
      id: generateId('msg'),
      type: MESSAGE_TYPES.ASSISTANT,
      content: response.answer || '抱歉，我无法回答这个问题。',
      sources: showSources.value ? (response.sources || []) : [],
      attribution: showAttribution.value ? response.attribution : null,
      timestamp: Date.now()
    }
    messages.value.push(assistantMessage)

    // 保存到本地存储
    saveChatHistory()

  } catch (error) {
    console.error('查询失败:', error)
    
    // 移除加载消息
    const loadingIndex = messages.value.findIndex(msg => msg.id === loadingMessage.id)
    if (loadingIndex !== -1) {
      messages.value.splice(loadingIndex, 1)
    }

    // 添加错误消息
    const errorMessage = {
      id: generateId('msg'),
      type: MESSAGE_TYPES.ERROR,
      content: '查询失败，请稍后重试。',
      timestamp: Date.now()
    }
    messages.value.push(errorMessage)
  } finally {
    isLoading.value = false
    await nextTick()
    scrollToBottom()
  }
}

const clearHistory = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空所有聊天记录吗？此操作不可恢复。',
      '确认清空',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    messages.value = []
    localStorage.removeItem(STORAGE_KEYS.CHAT_HISTORY)
    ElMessage.success('聊天记录已清空')
  } catch {
    // 用户取消
  }
}

const scrollToBottom = () => {
  if (chatContent.value) {
    chatContent.value.scrollTop = chatContent.value.scrollHeight
  }
}

const saveChatHistory = () => {
  try {
    const history = messages.value.map(msg => ({
      ...msg,
      // 不保存loading状态
      loading: false
    }))
    localStorage.setItem(STORAGE_KEYS.CHAT_HISTORY, JSON.stringify(history))
  } catch (error) {
    console.error('保存聊天历史失败:', error)
  }
}

const loadChatHistory = () => {
  try {
    const history = localStorage.getItem(STORAGE_KEYS.CHAT_HISTORY)
    if (history) {
      messages.value = JSON.parse(history)
    }
  } catch (error) {
    console.error('加载聊天历史失败:', error)
  }
}

// 工具函数
const getMessageTypeLabel = (type) => {
  const labels = {
    [MESSAGE_TYPES.USER]: '用户',
    [MESSAGE_TYPES.ASSISTANT]: 'AI助手',
    [MESSAGE_TYPES.SYSTEM]: '系统',
    [MESSAGE_TYPES.ERROR]: '错误'
  }
  return labels[type] || type
}

const getSourceTypeTag = (type) => {
  const tagMap = {
    'text': '',
    'image': 'success',
    'table': 'warning',
    'document': 'info'
  }
  return tagMap[type] || ''
}

const getScoreTagType = (score) => {
  if (score >= 0.8) return 'success'
  if (score >= 0.6) return 'warning'
  if (score >= 0.4) return 'danger'
  return 'info'
}

const getConfidenceTagType = (confidence) => {
  if (confidence >= 0.8) return 'success'
  if (confidence >= 0.6) return 'warning'
  if (confidence >= 0.4) return 'danger'
  return 'info'
}

// 生命周期
onMounted(() => {
  loadChatHistory()
})
</script>

<style scoped>
.chat-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--el-bg-color-page);
}

/* 聊天头部 */
.chat-header {
  background: white;
  border-bottom: 1px solid var(--el-border-color);
  padding: 16px 20px;
  flex-shrink: 0;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon {
  font-size: 24px;
  color: var(--el-color-primary);
}

.header-left h1 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* 聊天内容区域 */
.chat-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.chat-messages {
  max-width: 1000px;
  margin: 0 auto;
}

/* 欢迎消息 */
.welcome-message {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  min-height: 400px;
}

.welcome-content {
  text-align: center;
  padding: 40px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  max-width: 500px;
}

.welcome-icon {
  font-size: 4rem;
  color: var(--el-color-primary);
  margin-bottom: 20px;
}

.welcome-content h2 {
  margin: 0 0 16px 0;
  color: var(--el-text-color-primary);
}

.welcome-content p {
  color: var(--el-text-color-regular);
  line-height: 1.6;
  margin-bottom: 24px;
}

.query-type-info {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.type-tag {
  margin: 0;
}

/* 消息项 */
.message-item {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  padding: 16px;
  border-radius: 12px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.message-user {
  flex-direction: row-reverse;
}

.message-user .message-content {
  text-align: right;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--el-color-primary);
  color: white;
  flex-shrink: 0;
}

.message-user .message-avatar {
  background: var(--el-color-success);
}

.message-content {
  flex: 1;
  min-width: 0;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.message-type {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.message-time {
  font-size: 0.8rem;
  color: var(--el-text-color-placeholder);
}

.message-body {
  line-height: 1.6;
}

/* 用户消息 */
.user-message {
  text-align: right;
}

.query-type-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  margin-bottom: 8px;
}

.query-text {
  background: var(--el-color-primary);
  color: white;
  padding: 12px 16px;
  border-radius: 12px;
  display: inline-block;
  max-width: 100%;
  word-wrap: break-word;
}

/* AI回答 */
.assistant-message {
  text-align: left;
}

.answer-content {
  margin-bottom: 16px;
  line-height: 1.6;
  color: var(--el-text-color-primary);
}

/* 来源信息 */
.sources-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.sources-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.sources-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.source-item {
  padding: 12px;
  background: var(--el-bg-color-page);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
}

.source-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.source-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.source-document {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.source-page {
  color: var(--el-text-color-placeholder);
  font-size: 0.9rem;
}

.source-preview {
  color: var(--el-text-color-regular);
  font-size: 0.9rem;
  line-height: 1.4;
}

/* 溯源信息 */
.attribution-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.attribution-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.attribution-content {
  background: var(--el-bg-color-page);
  padding: 12px;
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
}

.attribution-summary {
  margin-bottom: 8px;
  color: var(--el-text-color-regular);
  line-height: 1.4;
}

.attribution-confidence {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--el-text-color-regular);
}

/* 系统消息 */
.system-message {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--el-text-color-info);
  font-style: italic;
}

/* 错误消息 */
.error-message {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--el-color-danger);
}

/* 加载状态 */
.loading-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--el-text-color-placeholder);
}

/* 输入区域 */
.chat-input {
  background: white;
  border-top: 1px solid var(--el-border-color);
  padding: 20px;
  flex-shrink: 0;
}

.input-container {
  max-width: 1000px;
  margin: 0 auto;
}

.input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.query-input {
  width: 100%;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.input-options {
  display: flex;
  gap: 16px;
}

.send-button {
  padding: 12px 24px;
}

.input-tips {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 0.8rem;
  color: var(--el-text-color-placeholder);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chat-header {
    padding: 12px 16px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .header-right {
    justify-content: center;
  }
  
  .chat-content {
    padding: 16px;
  }
  
  .chat-input {
    padding: 16px;
  }
  
  .input-actions {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .input-options {
    justify-content: center;
  }
  
  .input-tips {
    flex-direction: column;
    gap: 4px;
    text-align: center;
  }
}
</style>
