<template>
  <div class="chat-container">
    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 左侧边栏 -->
      <div class="sidebar">
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

      <!-- 右侧聊天区域 -->
      <div class="chat-area">
        <!-- 聊天消息区域 -->
        <div class="chat-messages" ref="chatMessages">
          <div 
            v-for="(message, index) in messages" 
            :key="index" 
            :class="['message', message.type]"
          >
          <div class="message-content">
            <div class="message-header">
              <span class="message-type">{{ getMessageTypeLabel(message.type) }}</span>
                <span class="message-time">{{ formatTime(message.timestamp) }}</span>
            </div>
              
            <div class="message-body">
              <!-- 用户消息 -->
              <div v-if="message.type === 'user'" class="user-message">
                  <div class="query-type-tag">{{ getQueryTypeLabel(message.queryType) }}</div>
                  <div class="query-content">{{ message.content }}</div>
              </div>

                <!-- 助手消息 -->
              <div v-else-if="message.type === 'assistant'" class="assistant-message">
                <!-- 使用智能问答结果组件 -->
                <SmartQAResult
                  :query-type="message.queryType || 'text'"
                  :display-mode="message.displayMode || 'text-focused'"
                  :llm-answer="message.content"
                  :sources="message.sources || []"
                  :content-analysis="message.contentAnalysis"
                  :confidence="message.confidence || 0.5"
                  @display-mode-change="handleDisplayModeChange"
                />
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

  try {
    const response = await ragAPI.sendQuery({
          query: query,
      query_type: selectedQueryType.value,
          options: {
            return_sources: true,
            return_metadata: true
          }
        })

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

const scrollToBottom = () => {
      nextTick(() => {
        if (chatMessages.value) {
          chatMessages.value.scrollTop = chatMessages.value.scrollHeight
        }
      })
    }

    // 生命周期
    onMounted(() => {
      // 初始化欢迎消息
      const welcomeMessage = {
        type: 'assistant',
        content: '欢迎使用智能问答系统！您可以选择不同的查询类型，系统会根据您的问题类型提供相应的回答。',
        sources: [],
        timestamp: new Date().toISOString()
      }
      messages.value.push(welcomeMessage)
    })

    return {
      selectedQueryType,
      currentQuery,
      isLoading,
      messages,
      chatMessages,
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
      handleDisplayModeChange
    }
  }
}
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f5f5;
  overflow: hidden;
}



.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

/* 左侧边栏 */
.sidebar {
  width: 320px;
  background: #fff;
  border-right: 1px solid #e0e0e0;
  overflow-y: auto;
  flex-shrink: 0;
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
  height: calc(100vh - 60px);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px 20px 5px 20px;
  background: #f5f5f5;
  min-height: 0;
}

.message {
  margin-bottom: 20px;
}

.message-content {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.message-type {
  font-weight: 600;
  color: #333;
}

.message-time {
  font-size: 12px;
  color: #999;
}

.user-message .query-type-tag {
  display: inline-block;
  background: #409eff;
  color: #fff;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  margin-bottom: 8px;
}

.query-content {
  color: #333;
  line-height: 1.6;
}

.assistant-message .answer-content {
  color: #333;
  line-height: 1.6;
  margin-bottom: 16px;
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
}
</style>