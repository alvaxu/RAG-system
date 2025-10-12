<template>
  <div class="chat-container">
    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 左侧边栏 -->
      <div class="sidebar" :style="{ width: sidebarWidth + 'px' }">
        <!-- 欢迎消息 -->
        <div class="welcome-message">
          <p>欢迎使用智能问答系统！您可以选择不同的查询类型，系统会根据您的问题类型提供相应的回答。</p>
        </div>
        
        <!-- 查询类型选择 -->
        <div class="query-type-selector">
          <h3>查询类型</h3>
          <el-radio-group v-model="selectedQueryType" @change="handleQueryTypeChange">
            <el-radio-button label="text">文本查询</el-radio-button>
            <el-radio-button label="image">图片查询</el-radio-button>
            <el-radio-button label="table">表格查询</el-radio-button>
            <el-radio-button label="smart">智能查询</el-radio-button>
            <el-radio-button label="hybrid">混合查询</el-radio-button>
          </el-radio-group>
        </div>

        <!-- 预设问题区域 -->
        <div class="preset-questions-section">
          <PresetQuestions 
            :query-type="selectedQueryType" 
            @question-selected="handlePresetQuestionSelected" 
          />
        </div>
      </div>

      <!-- 可拖拽分隔条 -->
      <div 
        class="resize-handle" 
        @mousedown="startResize"
        ref="resizeHandle"
      ></div>

      <!-- 右侧聊天区域 -->
      <div class="chat-area" ref="chatArea">
        <!-- 聊天消息区域 -->
        <div class="chat-messages" ref="chatMessages">
          <div 
            v-for="(message, index) in messages" 
            :key="index" 
            :class="['message', message.type]"
          >
            <!-- 用户消息 - 靠右显示 -->
            <div v-if="message.type === 'user'" class="user-message-container">
              <div class="user-message-bubble">
                <div class="message-header">
                  <div class="header-left">
                    <span class="message-type">{{ getMessageTypeLabel(message.type) }}</span>
                    <span class="query-type-tag">{{ getQueryTypeLabel(message.queryType) }}</span>
                  </div>
                  <span class="message-time">{{ formatTime(message.timestamp) }}</span>
                </div>
                <div class="query-content">{{ message.content }}</div>
              </div>
            </div>

            <!-- 助手消息 - 靠左显示 -->
            <div v-else-if="message.type === 'assistant'" class="assistant-message-container">
              <div class="assistant-message-bubble">
                <div class="message-header">
                  <span class="message-type">{{ getMessageTypeLabel(message.type) }}</span>
                  <span class="message-time">{{ formatTime(message.timestamp) }}</span>
                  <!-- 展开/收起按钮 -->
                  <div class="details-toggle">
                    <el-button 
                      @click="toggleMessageDetails(index)" 
                      :type="message.showDetails ? 'info' : 'primary'" 
                      plain
                      size="small"
                      class="toggle-button"
                    >
                      <el-icon>
                        <component :is="message.showDetails ? 'Hide' : 'View'" />
                      </el-icon>
                      {{ message.showDetails ? '收起详情' : '相关来源详情' }}
                    </el-button>
                  </div>
                </div>
                <div class="message-body">
                  <!-- 使用智能问答结果组件 -->
                  <SmartQAResult
                    :query-type="message.queryType || 'text'"
                    :llm-answer="message.content"
                    :sources="message.sources || []"
                    :show-details="message.showDetails || false"
                    :is-thinking="message.isThinking || false"
                    @toggle-details="toggleMessageDetails(index)"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="chat-input">
          <div class="input-container">
              <el-input
                v-model="currentQuery"
                type="textarea"
                :rows="3"
                placeholder="请输入您的问题..."
                  @keydown.enter.ctrl="sendQuery"
                :disabled="isLoading"
              />
              <div class="input-actions">
                  <el-button @click="clearAllMessages" type="danger" plain>清空历史</el-button>
                  <div class="right-actions">
                    <el-button @click="clearChat">清空输入</el-button>
                <el-button 
                  type="primary" 
                  @click="sendQuery"
                  :loading="isLoading"
                  :disabled="!currentQuery.trim()"
                >
                  发送
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import ragAPI from '@/services/api'
import PresetQuestions from '@/components/PresetQuestions.vue'
import SmartQAResult from '@/components/SmartQAResult.vue'

export default {
  name: 'Chat',
  components: {
    PresetQuestions,
    SmartQAResult
  },
  setup() {
// 响应式数据
    const selectedQueryType = ref('text')
const currentQuery = ref('')
    const isLoading = ref(false)
const messages = ref([])
    const chatMessages = ref(null)
    const sidebarWidth = ref(320) // 左侧边栏宽度
    const isResizing = ref(false)
    const resizeHandle = ref(null)
    const chatArea = ref(null)
    const sessionId = ref(null) // 添加会话ID管理

    // 查询类型标签映射
    const queryTypeLabels = {
      text: '文本查询',
      image: '图片查询',
      table: '表格查询',
      smart: '智能查询',
      hybrid: '混合查询'
    }

    // 消息类型标签映射
    const messageTypeLabels = {
      user: '用户',
      assistant: '助手'
    }

    // 方法
    const getQueryTypeLabel = (type) => {
      return queryTypeLabels[type] || type
    }

    const getMessageTypeLabel = (type) => {
      return messageTypeLabels[type] || type
    }

    const getChunkTypeLabel = (type) => {
      const chunkTypeLabels = {
        text: '文本',
        image: '图片',
        table: '表格',
        description: '描述',
        visual: '视觉'
      }
      return chunkTypeLabels[type] || type
    }

    const formatTime = (timestamp) => {
      if (!timestamp) return ''
      const date = new Date(timestamp)
      return date.toLocaleTimeString()
    }

    const truncateText = (text, maxLength) => {
      if (!text) return ''
      if (text.length <= maxLength) return text
      return text.substring(0, maxLength) + '...'
    }

    const handleQueryTypeChange = (newType) => {
      console.log('查询类型变更:', newType)
    }

    const handlePresetQuestionSelected = (question) => {
      currentQuery.value = question
      // 滚动到输入区域
      nextTick(() => {
        const inputArea = document.querySelector('.chat-input')
        if (inputArea) {
          inputArea.scrollIntoView({ behavior: 'smooth', block: 'center' })
        }
      })
    }

    const sendQuery = async () => {
      if (!currentQuery.value.trim() || isLoading.value) return

      const userMessage = {
        type: 'user',
        content: currentQuery.value,
        queryType: selectedQueryType.value,
        timestamp: new Date().toISOString()
      }

      messages.value.push(userMessage)
      const query = currentQuery.value
      currentQuery.value = ''
      isLoading.value = true

      // 添加思考状态的消息
      const thinkingMessage = {
        type: 'assistant',
        content: '',
        sources: [],
        queryType: selectedQueryType.value,
        isThinking: true,
        timestamp: new Date().toISOString()
      }
      messages.value.push(thinkingMessage)
      scrollToBottom()

      try {
        const response = await ragAPI.sendQuery({
          query: query,
          query_type: selectedQueryType.value,
          session_id: sessionId.value, // 传递会话ID
          user_id: 'web_user', // 添加用户ID
          include_sources: true,
          return_sources: true,
          return_metadata: true
        })

        // 更新会话ID（如果响应中包含）
        if (response.session_id) {
          sessionId.value = response.session_id
        }

        // 移除思考状态的消息
        messages.value.pop()

        const assistantMessage = {
          type: 'assistant',
          content: response.answer,
          sources: response.sources || [],
          queryType: response.query_type,
          displayMode: response.display_mode,
          contentAnalysis: response.content_analysis,
          confidence: response.confidence,
          timestamp: new Date().toISOString()
        }

        messages.value.push(assistantMessage)
        scrollToBottom()

  } catch (error) {
    console.error('查询失败:', error)
    ElMessage.error('查询失败，请稍后重试')
    
    // 移除思考状态的消息
    messages.value.pop()
    
    const errorMessage = {
      type: 'assistant',
      content: '抱歉，查询过程中出现错误，请稍后重试。',
      sources: [],
      timestamp: new Date().toISOString()
    }
    messages.value.push(errorMessage)
  } finally {
    isLoading.value = false
  }
    }

    const clearChat = () => {
      // 只清空提问区，保留聊天历史
      currentQuery.value = ''
    }

    const clearAllMessages = () => {
      // 清空所有聊天历史
    messages.value = []
      currentQuery.value = ''
}

    const handleDisplayModeChange = (newMode) => {
      console.log('展示模式变更:', newMode)
      // 这里可以添加展示模式变更的逻辑
      // 比如更新当前消息的展示模式
    }

    // 切换消息详情显示状态
    const toggleMessageDetails = (messageIndex) => {
      if (messages.value[messageIndex]) {
        messages.value[messageIndex].showDetails = !messages.value[messageIndex].showDetails
      }
    }

const scrollToBottom = () => {
      nextTick(() => {
        if (chatMessages.value) {
          chatMessages.value.scrollTop = chatMessages.value.scrollHeight
        }
      })
    }

    // 开始调整宽度
    const startResize = (e) => {
      isResizing.value = true
      document.addEventListener('mousemove', handleResize)
      document.addEventListener('mouseup', stopResize)
      e.preventDefault()
    }

    // 处理调整宽度
    const handleResize = (e) => {
      if (!isResizing.value) return
      
      const containerWidth = document.querySelector('.main-content').offsetWidth
      const newWidth = e.clientX
      
      // 限制最小和最大宽度
      const minWidth = 200
      const maxWidth = containerWidth * 0.7
      
      if (newWidth >= minWidth && newWidth <= maxWidth) {
        sidebarWidth.value = newWidth
      }
    }

    // 停止调整宽度
    const stopResize = () => {
      isResizing.value = false
      document.removeEventListener('mousemove', handleResize)
      document.removeEventListener('mouseup', stopResize)
    }

    // 生命周期
    onMounted(() => {
      // 不再自动添加欢迎消息，因为已经移到了左侧边栏
    })

    return {
      selectedQueryType,
      currentQuery,
      isLoading,
      messages,
      chatMessages,
      sidebarWidth,
      isResizing,
      resizeHandle,
      chatArea,
      getQueryTypeLabel,
      getMessageTypeLabel,
      getChunkTypeLabel,
      formatTime,
      truncateText,
      handleQueryTypeChange,
      handlePresetQuestionSelected,
      sendQuery,
      clearChat,
      clearAllMessages,
      handleDisplayModeChange,
      toggleMessageDetails,
      startResize
    }
  }
}
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 50px - 60px); /* 减去顶部导航栏和底部信息栏的高度 */
  background: #f5f5f5;
  overflow: hidden;
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}



.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
  min-height: 0;
  box-sizing: border-box;
}

/* 左侧边栏 */
.sidebar {
  background: #fff;
  border-right: 1px solid #e0e0e0;
  overflow-y: auto;
  flex-shrink: 0;
  min-width: 200px;
  max-width: 70%;
}

/* 可拖拽分隔条 */
.resize-handle {
  width: 4px;
  background: #e0e0e0;
  cursor: col-resize;
  flex-shrink: 0;
  position: relative;
  transition: background-color 0.2s ease;
}

.resize-handle:hover {
  background: #409eff;
}

.resize-handle:active {
  background: #337ecc;
}

.welcome-message {
  padding: 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
}

.welcome-message p {
  margin: 0;
  color: #666;
  font-size: 14px;
  line-height: 1.5;
  text-align: center;
}

.sidebar h3 {
  margin: 0 0 12px 0;
  color: #333;
  font-size: 16px;
  font-weight: 600;
  padding: 0 20px;
}

.query-type-selector {
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.query-type-selector h3 {
  padding: 0;
  margin-bottom: 16px;
}

.preset-questions-section {
  padding: 20px;
}

.preset-questions-section h3 {
  padding: 0;
  margin-bottom: 16px;
}

.test-questions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.question-item {
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
  line-height: 1.4;
}

.question-item:hover {
  border-color: #409eff;
  background: #f0f8ff;
}

/* 右侧聊天区域 */
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px 20px 120px 20px; /* 增加底部间距，避免被输入区域遮挡 */
  background: #f5f5f5;
  min-height: 0;
}

.message {
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
}

/* 用户消息容器 - 靠右显示 */
.user-message-container {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 20px;
}

.user-message-bubble {
  background: #409eff;
  color: #fff;
  border-radius: 12px 12px 4px 12px;
  padding: 12px 16px;
  max-width: 70%;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
  position: relative;
}

.user-message-bubble .message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  flex-wrap: wrap;
  gap: 8px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-message-bubble .message-type {
  font-weight: 600;
  color: #fff;
  font-size: 14px;
}

.user-message-bubble .message-time {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.8);
}

.user-message-bubble .query-type-tag {
  display: inline-block;
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
  white-space: nowrap;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.user-message-bubble .query-content {
  color: #fff;
  line-height: 1.5;
  font-size: 14px;
}

/* 助手消息容器 - 靠左显示 */
.assistant-message-container {
  display: flex;
  justify-content: flex-start;
  margin-bottom: 20px;
}

.assistant-message-bubble {
  background: #fff;
  border-radius: 12px 12px 12px 4px;
  padding: 16px;
  max-width: 85%;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid #e0e0e0;
  position: relative;
}

.assistant-message-bubble .message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
  flex-wrap: wrap;
  gap: 8px;
}

.details-toggle {
  display: flex;
  align-items: center;
}

.toggle-button {
  border-radius: 16px;
  padding: 4px 12px;
  font-size: 12px;
  height: 28px;
}

.assistant-message-bubble .message-type {
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.assistant-message-bubble .message-time {
  font-size: 12px;
  color: #999;
}

.assistant-message-bubble .message-body {
  color: #333;
  line-height: 1.6;
}

/* 来源信息样式 */
.sources-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.sources-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.sources-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.source-item {
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.source-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  flex-wrap: wrap;
}

.source-page {
  color: #666;
  font-size: 12px;
}

.source-score {
  color: #409eff;
  font-size: 12px;
  font-weight: 500;
}

.source-preview {
  color: #666;
  font-size: 12px;
  line-height: 1.4;
}

.chat-input {
  background: #fff;
  padding: 16px 20px;
  border-top: 1px solid #e0e0e0;
  flex-shrink: 0;
  margin-top: auto;
}

.input-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.right-actions {
  display: flex;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .main-content {
    flex-direction: column;
  }
  
  .sidebar {
    width: 100%;
    height: auto;
    max-height: 300px;
    border-right: none;
    border-bottom: 1px solid #e0e0e0;
  }
  
  .query-type-selector,
  .preset-questions-section {
    padding: 16px;
  }
  
  .chat-messages {
    padding: 16px 16px 5px 16px;
  }
  
  .chat-input {
    padding: 16px;
  }
  
  .input-container {
    max-width: 100%;
  }
  
  .source-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  /* 移动端消息样式调整 */
  .user-message-bubble {
    max-width: 85%;
    padding: 10px 14px;
  }
  
  .assistant-message-bubble {
    max-width: 95%;
    padding: 14px;
  }
  
  .user-message-bubble .message-header,
  .assistant-message-bubble .message-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .user-message-bubble .message-time,
  .assistant-message-bubble .message-time {
    font-size: 10px;
  }
}
</style>