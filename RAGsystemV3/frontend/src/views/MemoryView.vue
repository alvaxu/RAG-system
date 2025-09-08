<template>
  <div class="memory-container">
    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 左侧边栏：会话管理 -->
      <div class="sidebar" :style="{ width: sidebarWidth + 'px' }">
        <!-- 页面标题 -->
        <div class="page-header">
          <h1>🧠 记忆管理</h1>
          <p>管理多轮对话记忆，支持智能压缩和检索</p>
        </div>
        
        <!-- 会话管理区域 -->
        <div class="session-management">
          <div class="section-header">
            <h3>💬 会话管理</h3>
            <el-button type="primary" size="small" @click="createNewSession">
              <el-icon><Plus /></el-icon>
              新建会话
            </el-button>
          </div>
          
          <div class="session-list">
            <div 
              v-for="session in sessions" 
              :key="session.session_id"
              class="session-item"
              @click="selectSession(session)"
              :class="{ 'active': selectedSession?.session_id === session.session_id }"
            >
              <div class="session-info">
                <div class="session-id">🔑 {{ session.session_id.substring(0, 8) }}...</div>
                <div class="session-meta">
                  <span>📝 记忆: {{ session.memory_count }}</span>
                  <span>⏰ 更新: {{ session.formatted_updated_at }}</span>
                </div>
              </div>
              <div class="session-actions">
                <el-button size="small" @click.stop="deleteSession(session.session_id)">
                  删除
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 可拖拽分隔条 -->
      <div 
        class="resize-handle" 
        @mousedown="startResize"
        ref="resizeHandle"
      ></div>

      <!-- 右侧记忆区域 -->
      <div class="memory-area" ref="memoryArea">
        <div v-if="!selectedSession" class="no-session">
          <div class="empty-state">
            <el-icon size="48"><ChatDotRound /></el-icon>
            <h3>选择会话</h3>
            <p>请从左侧选择一个会话查看记忆内容</p>
          </div>
        </div>
        
        <div v-else class="memory-management">
          <!-- 会话信息 -->
          <div class="session-detail-section">
            <div class="section-header">
              <h3>📋 会话详情</h3>
              <el-button @click="refreshMemories" :loading="loadingMemories">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
            
            <div class="session-detail">
              <p><strong>会话ID:</strong> {{ selectedSession.session_id }}</p>
              <p><strong>用户ID:</strong> {{ selectedSession.user_id }}</p>
              <p><strong>创建时间:</strong> {{ selectedSession.created_at }}</p>
              <p><strong>记忆数量:</strong> {{ selectedSession.memory_count }}</p>
            </div>
          </div>
          
          <!-- 记忆列表 -->
          <div class="memory-list-section">
            <div class="section-header">
              <h3>📚 记忆列表</h3>
              <div class="list-actions">
                <el-button @click="refreshMemories" :loading="loadingMemories">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
                <el-button type="primary" @click="showAddMemoryDialog = true">
                  <el-icon><Plus /></el-icon>
                  添加记忆
                </el-button>
              </div>
            </div>
            
            <div class="memory-list">
              <div v-if="memories.length === 0" class="no-memories">
                <p>该会话暂无记忆</p>
              </div>
              <div v-else>
                <div 
                  v-for="memory in memories" 
                  :key="memory.chunk_id"
                  class="memory-item"
                >
                  <div class="memory-content">
                    <div class="memory-main-content">
                      <div class="content-label">内容:</div>
                      <div class="markdown-content" v-html="renderMarkdown(memory.content)"></div>
                    </div>
                    <div class="memory-meta">
                      <div class="meta-item">
                        <span class="meta-label">类型:</span>
                        <el-tag :type="getContentTypeTag(memory.content_type)" size="small">
                          {{ memory.content_type }}
                        </el-tag>
                      </div>
                      <div class="meta-item">
                        <span class="meta-label">相关性:</span>
                        <el-progress 
                          :percentage="Math.round(memory.relevance_score * 100)" 
                          :color="getScoreColor(memory.relevance_score)"
                          :show-text="false"
                          :stroke-width="6"
                        />
                        <span class="score-text">{{ memory.relevance_score.toFixed(2) }}</span>
                      </div>
                      <div class="meta-item">
                        <span class="meta-label">重要性:</span>
                        <el-progress 
                          :percentage="Math.round(memory.importance_score * 100)" 
                          :color="getScoreColor(memory.importance_score)"
                          :show-text="false"
                          :stroke-width="6"
                        />
                        <span class="score-text">{{ memory.importance_score.toFixed(2) }}</span>
                      </div>
                      <div class="meta-item">
                        <span class="meta-label">创建时间:</span>
                        <span class="time-text">{{ formatDate(memory.created_at) }}</span>
                      </div>
                    </div>
                  </div>
                  <div class="memory-actions">
                    <el-button size="small" type="danger" @click="deleteMemory(memory.chunk_id)">
                      删除
                    </el-button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加记忆对话框 -->
    <el-dialog v-model="showAddMemoryDialog" title="添加记忆" width="500px">
      <el-form :model="newMemory" label-width="80px">
        <el-form-item label="内容">
          <el-input v-model="newMemory.content" type="textarea" :rows="4" placeholder="请输入记忆内容" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="newMemory.content_type" placeholder="选择内容类型">
            <el-option label="文本" value="text" />
            <el-option label="图片" value="image" />
            <el-option label="表格" value="table" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddMemoryDialog = false">取消</el-button>
        <el-button type="primary" @click="addMemory" :loading="addingMemory">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, ChatDotRound } from '@element-plus/icons-vue'
import axios from 'axios'

// 响应式数据
const sessions = ref([])
const selectedSession = ref(null)
const memories = ref([])
const loadingMemories = ref(false)
const addingMemory = ref(false)
const showAddMemoryDialog = ref(false)
const newMemory = ref({
  content: '',
  content_type: 'text'
})

// 侧边栏宽度和拖拽相关
const sidebarWidth = ref(350)
const isResizing = ref(false)
const resizeHandle = ref(null)
const memoryArea = ref(null)

// 格式化时间
const formatDate = (dateString) => {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString()
}

// 简单的Markdown渲染函数
const renderMarkdown = (content) => {
  if (!content) return ''
  
  return content
    // 处理标题
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    // 处理粗体
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    // 处理斜体
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    // 处理代码块
    .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
    // 处理行内代码
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    // 处理列表
    .replace(/^\* (.*$)/gim, '<li>$1</li>')
    .replace(/^- (.*$)/gim, '<li>$1</li>')
    .replace(/^\d+\. (.*$)/gim, '<li>$1</li>')
    // 处理换行
    .replace(/\n/g, '<br>')
}

// 获取内容类型标签样式
const getContentTypeTag = (contentType) => {
  const typeMap = {
    'text': 'primary',
    'image': 'success',
    'table': 'warning'
  }
  return typeMap[contentType] || 'info'
}

// 获取分数颜色
const getScoreColor = (score) => {
  if (score >= 0.8) return '#67c23a' // 绿色
  if (score >= 0.6) return '#e6a23c' // 橙色
  if (score >= 0.4) return '#f56c6c' // 红色
  return '#909399' // 灰色
}

// 加载会话列表
const loadSessions = async () => {
  try {
    const response = await axios.get('http://localhost:8000/api/v3/memory/sessions')
    sessions.value = response.data.map(session => ({
      ...session,
      formatted_updated_at: formatDate(session.updated_at || session.created_at)
    }))
  } catch (error) {
    console.error('加载会话失败:', error)
    ElMessage.error('加载会话失败')
  }
}

// 选择会话
const selectSession = async (session) => {
  selectedSession.value = session
  await loadMemories()
}

// 加载记忆
const loadMemories = async () => {
  if (!selectedSession.value) return
  
  loadingMemories.value = true
  try {
    const response = await axios.get(`http://localhost:8000/api/v3/memory/sessions/${selectedSession.value.session_id}/memories?max_results=100`)
    memories.value = response.data
  } catch (error) {
    console.error('加载记忆失败:', error)
    ElMessage.error('加载记忆失败')
  } finally {
    loadingMemories.value = false
  }
}

// 刷新记忆
const refreshMemories = async () => {
  await loadMemories()
}

// 创建新会话
const createNewSession = async () => {
  try {
    const response = await axios.post('http://localhost:8000/api/v3/memory/sessions', {
      user_id: 'web_user'
    })
    ElMessage.success('会话创建成功')
    await loadSessions()
    selectSession(response.data)
  } catch (error) {
    console.error('创建会话失败:', error)
    ElMessage.error('创建会话失败')
  }
}

// 删除会话
const deleteSession = async (sessionId) => {
  try {
    await ElMessageBox.confirm('确定要删除这个会话吗？', '确认删除', {
      type: 'warning'
    })
    
    await axios.delete(`http://localhost:8000/api/v3/memory/sessions/${sessionId}`)
    ElMessage.success('会话删除成功')
    
    if (selectedSession.value?.session_id === sessionId) {
      selectedSession.value = null
      memories.value = []
    }
    
    await loadSessions()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除会话失败:', error)
      ElMessage.error('删除会话失败')
    }
  }
}

// 添加记忆
const addMemory = async () => {
  if (!selectedSession.value || !newMemory.value.content.trim()) {
    ElMessage.warning('请填写记忆内容')
    return
  }
  
  addingMemory.value = true
  try {
    await axios.post(`http://localhost:8000/api/v3/memory/sessions/${selectedSession.value.session_id}/memories`, {
      content: newMemory.value.content,
      content_type: newMemory.value.content_type,
      relevance_score: 0.8,
      importance_score: 0.7
    })
    
    ElMessage.success('记忆添加成功')
    showAddMemoryDialog.value = false
    newMemory.value = { content: '', content_type: 'text' }
    await loadMemories()
    await loadSessions() // 更新会话的记忆数量
  } catch (error) {
    console.error('添加记忆失败:', error)
    ElMessage.error('添加记忆失败')
  } finally {
    addingMemory.value = false
  }
}

// 删除记忆
const deleteMemory = async (chunkId) => {
  try {
    await ElMessageBox.confirm('确定要删除这个记忆吗？', '确认删除', {
      type: 'warning'
    })
    
    await axios.delete(`http://localhost:8000/api/v3/memory/memories/${chunkId}`)
    ElMessage.success('记忆删除成功')
    await loadMemories()
    await loadSessions() // 更新会话的记忆数量
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除记忆失败:', error)
      ElMessage.error('删除记忆失败')
    }
  }
}

// 拖拽调整宽度相关函数
const startResize = (e) => {
  isResizing.value = true
  document.addEventListener('mousemove', handleResize)
  document.addEventListener('mouseup', stopResize)
  e.preventDefault()
}

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

const stopResize = () => {
  isResizing.value = false
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
}

// 生命周期
onMounted(() => {
  loadSessions()
})
</script>

<style scoped>
.memory-container {
  display: flex;
  height: 100vh;
  background: #f5f5f5;
  overflow: hidden;
}

.main-content {
  display: flex;
  flex: 1;
  height: 100vh;
  overflow: hidden;
}

/* 左侧边栏 */
.sidebar {
  background: #fff;
  border-right: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 200px;
}

.page-header {
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
  text-align: center;
}

.page-header h1 {
  margin: 0 0 8px 0;
  color: #333;
  font-size: 20px;
  font-weight: 600;
}

.page-header p {
  margin: 0;
  color: #666;
  font-size: 12px;
  line-height: 1.4;
}

.session-management {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.section-header h3 {
  margin: 0;
  color: #333;
  font-size: 16px;
  font-weight: 600;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 20px 20px 20px;
}

.session-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.3s;
  background: #f8f9fa;
}

.session-item:hover {
  border-color: #409eff;
  background: #f0f8ff;
}

.session-item.active {
  border-color: #409eff;
  background: #f0f8ff;
}

.session-info {
  flex: 1;
}

.session-id {
  font-weight: 600;
  margin-bottom: 4px;
  font-family: monospace;
  font-size: 12px;
  color: #333;
}

.session-meta {
  display: flex;
  gap: 12px;
  color: #909399;
  font-size: 11px;
}

.session-actions {
  display: flex;
  gap: 4px;
}

/* 拖拽分隔条 */
.resize-handle {
  width: 4px;
  background: #e0e0e0;
  cursor: col-resize;
  transition: background-color 0.2s;
}

.resize-handle:hover {
  background: #409eff;
}

/* 右侧记忆区域 */
.memory-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #f5f5f5;
}

.no-session {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: #f5f5f5;
}

.empty-state {
  text-align: center;
  color: #7f8c8d;
}

.empty-state .el-icon {
  font-size: 48px;
  margin-bottom: 16px;
  color: #dee2e6;
}

.empty-state h3 {
  margin: 16px 0 8px;
  color: #6c757d;
  font-weight: 600;
}

.empty-state p {
  color: #adb5bd;
  font-size: 14px;
}

.memory-management {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.session-detail-section {
  background: #fff;
  border-bottom: 1px solid #e0e0e0;
  padding: 20px;
}

.session-detail-section .section-header {
  padding: 0 0 16px 0;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 16px;
}

.session-detail {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
}

.session-detail p {
  margin: 8px 0;
  color: #606266;
  font-size: 14px;
}

.memory-list-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #fff;
}

.memory-list-section .section-header {
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.list-actions {
  display: flex;
  gap: 8px;
}

.memory-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.memory-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  margin-bottom: 12px;
  background: #fafafa;
  transition: all 0.3s;
}

.memory-item:hover {
  border-color: #409eff;
  background: #f0f8ff;
}

.memory-content {
  flex: 1;
  margin-right: 12px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.memory-main-content {
  flex: 1;
}

.content-label {
  font-weight: 600;
  color: #333;
  font-size: 14px;
  margin-bottom: 8px;
}

.markdown-content {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 12px;
  font-size: 14px;
  line-height: 1.6;
  color: #333;
  max-height: 200px;
  overflow-y: auto;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3 {
  margin: 8px 0 4px 0;
  color: #2c3e50;
}

.markdown-content h1 {
  font-size: 18px;
  border-bottom: 2px solid #e9ecef;
  padding-bottom: 4px;
}

.markdown-content h2 {
  font-size: 16px;
  border-bottom: 1px solid #e9ecef;
  padding-bottom: 2px;
}

.markdown-content h3 {
  font-size: 14px;
}

.markdown-content strong {
  color: #2c3e50;
  font-weight: 600;
}

.markdown-content em {
  color: #6c757d;
  font-style: italic;
}

.markdown-content code {
  background: #e9ecef;
  padding: 2px 4px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.markdown-content pre {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  padding: 8px;
  overflow-x: auto;
  margin: 8px 0;
}

.markdown-content pre code {
  background: none;
  padding: 0;
}

.markdown-content li {
  margin: 4px 0;
  padding-left: 8px;
}

.memory-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.meta-label {
  font-weight: 600;
  color: #606266;
  font-size: 12px;
  min-width: 60px;
}

.score-text {
  font-size: 12px;
  color: #606266;
  margin-left: 4px;
  min-width: 40px;
}

.time-text {
  font-size: 12px;
  color: #909399;
}

.memory-actions {
  display: flex;
  gap: 4px;
  align-items: center;
}

.no-memories {
  text-align: center;
  padding: 40px;
  color: #7f8c8d;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .main-content {
    flex-direction: column;
  }
  
  .sidebar {
    height: 200px;
    border-right: none;
    border-bottom: 1px solid #e0e0e0;
  }
  
  .resize-handle {
    width: 100%;
    height: 4px;
    cursor: row-resize;
  }
  
  .memory-area {
    flex: 1;
  }
}

/* 滚动条样式 */
.session-list::-webkit-scrollbar,
.memory-list::-webkit-scrollbar {
  width: 6px;
}

.session-list::-webkit-scrollbar-track,
.memory-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.session-list::-webkit-scrollbar-thumb,
.memory-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.session-list::-webkit-scrollbar-thumb:hover,
.memory-list::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
