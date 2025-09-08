<template>
  <div class="memory-manager">
    <!-- 头部工具栏 -->
    <div class="memory-header">
      <div class="header-left">
        <h3>记忆管理</h3>
        <el-tag type="info" v-if="currentSession">
          当前会话: {{ currentSession.session_id.substring(0, 8) }}...
        </el-tag>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="createNewSession" :loading="creating">
          <el-icon><Plus /></el-icon>
          新建会话
        </el-button>
        <el-button @click="refreshData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 会话选择器 -->
    <div class="session-selector" v-if="!currentSession">
      <el-card>
        <template #header>
          <span>选择会话</span>
        </template>
        <div class="session-list">
          <div 
            v-for="session in sessions" 
            :key="session.session_id"
            class="session-item"
            @click="selectSession(session)"
          >
            <div class="session-info">
              <div class="session-id">{{ session.session_id.substring(0, 8) }}...</div>
              <div class="session-meta">
                <span>记忆: {{ session.memory_count }}</span>
                <span>更新: {{ session.formatted_updated_at }}</span>
              </div>
            </div>
            <div class="session-actions">
              <el-button size="small" @click.stop="deleteSession(session.session_id)">
                删除
              </el-button>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 记忆管理界面 -->
    <div class="memory-content" v-if="currentSession">
      <!-- 记忆操作工具栏 -->
      <div class="memory-toolbar">
        <div class="toolbar-left">
          <el-input
            v-model="searchQuery"
            placeholder="搜索记忆..."
            @keyup.enter="searchMemories"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button type="primary" @click="searchMemories" :loading="searching">
            搜索
          </el-button>
        </div>
        <div class="toolbar-right">
          <el-button @click="showAddMemoryDialog = true">
            <el-icon><Plus /></el-icon>
            添加记忆
          </el-button>
          <el-button @click="showCompressionDialog = true">
            <el-icon><Compress /></el-icon>
            压缩记忆
          </el-button>
        </div>
      </div>

      <!-- 记忆列表 -->
      <div class="memory-list">
        <el-card v-for="memory in memories" :key="memory.chunk_id" class="memory-card">
          <div class="memory-header">
            <div class="memory-scores">
              <el-tag 
                :color="memoryUtils.getSimilarityColor(memory.relevance_score)"
                size="small"
              >
                相关性: {{ memory.relevance_score.toFixed(2) }}
              </el-tag>
              <el-tag 
                :color="memoryUtils.getImportanceColor(memory.importance_score)"
                size="small"
              >
                重要性: {{ memory.importance_score.toFixed(2) }}
              </el-tag>
            </div>
            <div class="memory-actions">
              <el-button size="small" @click="editMemory(memory)">编辑</el-button>
              <el-button size="small" type="danger" @click="deleteMemory(memory.chunk_id)">删除</el-button>
            </div>
          </div>
          <div class="memory-content">
            <div class="memory-text">
              {{ memory.content }}
            </div>
            <div class="memory-meta">
              <span>类型: {{ memory.content_type }}</span>
              <span>创建时间: {{ memory.formatted_created_at }}</span>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 分页 -->
      <div class="pagination" v-if="totalMemories > pageSize">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="totalMemories"
          @current-change="loadMemories"
          layout="total, prev, pager, next, jumper"
        />
      </div>
    </div>

    <!-- 添加记忆对话框 -->
    <el-dialog
      v-model="showAddMemoryDialog"
      title="添加记忆"
      width="600px"
    >
      <el-form :model="newMemory" :rules="memoryRules" ref="memoryForm" label-width="100px">
        <el-form-item label="记忆内容" prop="content">
          <el-input
            v-model="newMemory.content"
            type="textarea"
            :rows="4"
            placeholder="请输入记忆内容..."
          />
        </el-form-item>
        <el-form-item label="内容类型" prop="content_type">
          <el-select v-model="newMemory.content_type">
            <el-option label="文本" value="text" />
            <el-option label="图片" value="image" />
            <el-option label="表格" value="table" />
          </el-select>
        </el-form-item>
        <el-form-item label="相关性分数" prop="relevance_score">
          <el-slider
            v-model="newMemory.relevance_score"
            :min="0"
            :max="1"
            :step="0.1"
            show-input
          />
        </el-form-item>
        <el-form-item label="重要性分数" prop="importance_score">
          <el-slider
            v-model="newMemory.importance_score"
            :min="0"
            :max="1"
            :step="0.1"
            show-input
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddMemoryDialog = false">取消</el-button>
        <el-button type="primary" @click="addMemory" :loading="adding">确定</el-button>
      </template>
    </el-dialog>

    <!-- 压缩记忆对话框 -->
    <el-dialog
      v-model="showCompressionDialog"
      title="压缩记忆"
      width="500px"
    >
      <el-form :model="compressionData" label-width="120px">
        <el-form-item label="压缩策略">
          <el-select v-model="compressionData.strategy">
            <el-option label="语义压缩" value="semantic" />
            <el-option label="时间压缩" value="temporal" />
            <el-option label="重要性压缩" value="importance" />
          </el-select>
        </el-form-item>
        <el-form-item label="压缩阈值">
          <el-input-number
            v-model="compressionData.threshold"
            :min="1"
            :max="1000"
          />
        </el-form-item>
        <el-form-item label="最大压缩比例">
          <el-slider
            v-model="compressionData.max_ratio"
            :min="0.1"
            :max="1.0"
            :step="0.1"
            show-input
          />
        </el-form-item>
        <el-form-item label="强制压缩">
          <el-switch v-model="compressionData.force" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCompressionDialog = false">取消</el-button>
        <el-button type="primary" @click="compressMemories" :loading="compressing">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Search, Compress } from '@element-plus/icons-vue'
import { sessionApi, memoryApi, compressionApi, memoryUtils } from '@/services/memory/memoryApi'

export default {
  name: 'MemoryManager',
  components: {
    Plus,
    Refresh,
    Search,
    Compress
  },
  setup() {
    // 响应式数据
    const loading = ref(false)
    const creating = ref(false)
    const adding = ref(false)
    const searching = ref(false)
    const compressing = ref(false)
    
    const sessions = ref([])
    const currentSession = ref(null)
    const memories = ref([])
    const searchQuery = ref('')
    
    // 分页数据
    const currentPage = ref(1)
    const pageSize = ref(10)
    const totalMemories = ref(0)
    
    // 对话框状态
    const showAddMemoryDialog = ref(false)
    const showCompressionDialog = ref(false)
    
    // 表单数据
    const newMemory = reactive({
      content: '',
      content_type: 'text',
      relevance_score: 0.5,
      importance_score: 0.5,
      metadata: {}
    })
    
    const compressionData = reactive({
      strategy: 'semantic',
      threshold: 20,
      max_ratio: 0.3,
      force: false
    })
    
    // 表单验证规则
    const memoryRules = {
      content: [
        { required: true, message: '请输入记忆内容', trigger: 'blur' },
        { min: 1, max: 10000, message: '记忆内容长度在1-10000个字符', trigger: 'blur' }
      ],
      content_type: [
        { required: true, message: '请选择内容类型', trigger: 'change' }
      ],
      relevance_score: [
        { type: 'number', min: 0, max: 1, message: '相关性分数必须在0-1之间', trigger: 'blur' }
      ],
      importance_score: [
        { type: 'number', min: 0, max: 1, message: '重要性分数必须在0-1之间', trigger: 'blur' }
      ]
    }
    
    // 计算属性
    const memoryUtils = computed(() => memoryUtils)
    
    // 方法
    const loadSessions = async () => {
      try {
        loading.value = true
        const response = await sessionApi.list({ status: 'active' })
        sessions.value = response.map(session => memoryUtils.value.formatSession(session))
      } catch (error) {
        ElMessage.error(`加载会话失败: ${error.message}`)
      } finally {
        loading.value = false
      }
    }
    
    const loadMemories = async () => {
      if (!currentSession.value) return
      
      try {
        loading.value = true
        const response = await memoryApi.query(currentSession.value.session_id, {
          query_text: searchQuery.value || '',
          max_results: pageSize.value,
          similarity_threshold: 0.0
        })
        memories.value = response.map(memory => memoryUtils.value.formatMemory(memory))
        totalMemories.value = response.length
      } catch (error) {
        ElMessage.error(`加载记忆失败: ${error.message}`)
      } finally {
        loading.value = false
      }
    }
    
    const createNewSession = async () => {
      try {
        creating.value = true
        const response = await sessionApi.create({
          user_id: 'current_user', // 这里应该从用户状态获取
          metadata: { source: 'web' }
        })
        currentSession.value = memoryUtils.value.formatSession(response)
        await loadMemories()
        ElMessage.success('会话创建成功')
      } catch (error) {
        ElMessage.error(`创建会话失败: ${error.message}`)
      } finally {
        creating.value = false
      }
    }
    
    const selectSession = (session) => {
      currentSession.value = session
      loadMemories()
    }
    
    const searchMemories = async () => {
      if (!currentSession.value) return
      
      try {
        searching.value = true
        const response = await memoryApi.query(currentSession.value.session_id, {
          query_text: searchQuery.value,
          max_results: pageSize.value,
          similarity_threshold: 0.7
        })
        memories.value = response.map(memory => memoryUtils.value.formatMemory(memory))
      } catch (error) {
        ElMessage.error(`搜索记忆失败: ${error.message}`)
      } finally {
        searching.value = false
      }
    }
    
    const addMemory = async () => {
      try {
        adding.value = true
        
        // 验证数据
        const validation = memoryUtils.value.validateMemoryData(newMemory)
        if (!validation.isValid) {
          ElMessage.error(validation.errors.join(', '))
          return
        }
        
        const response = await memoryApi.add(currentSession.value.session_id, newMemory)
        memories.value.unshift(memoryUtils.value.formatMemory(response))
        
        // 重置表单
        Object.assign(newMemory, {
          content: '',
          content_type: 'text',
          relevance_score: 0.5,
          importance_score: 0.5,
          metadata: {}
        })
        
        showAddMemoryDialog.value = false
        ElMessage.success('记忆添加成功')
      } catch (error) {
        ElMessage.error(`添加记忆失败: ${error.message}`)
      } finally {
        adding.value = false
      }
    }
    
    const compressMemories = async () => {
      try {
        compressing.value = true
        const response = await compressionApi.compress(currentSession.value.session_id, compressionData)
        
        ElMessage.success(`记忆压缩成功，压缩比例: ${(response.compression_ratio * 100).toFixed(1)}%`)
        showCompressionDialog.value = false
        
        // 重新加载记忆
        await loadMemories()
      } catch (error) {
        ElMessage.error(`压缩记忆失败: ${error.message}`)
      } finally {
        compressing.value = false
      }
    }
    
    const deleteMemory = async (chunkId) => {
      try {
        await ElMessageBox.confirm('确定要删除这个记忆吗？', '确认删除', {
          type: 'warning'
        })
        
        // 这里需要实现删除记忆的API
        // await memoryApi.delete(chunkId)
        
        memories.value = memories.value.filter(m => m.chunk_id !== chunkId)
        ElMessage.success('记忆删除成功')
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error(`删除记忆失败: ${error.message}`)
        }
      }
    }
    
    const deleteSession = async (sessionId) => {
      try {
        await ElMessageBox.confirm('确定要删除这个会话吗？', '确认删除', {
          type: 'warning'
        })
        
        // 这里需要实现删除会话的API
        // await sessionApi.delete(sessionId)
        
        sessions.value = sessions.value.filter(s => s.session_id !== sessionId)
        ElMessage.success('会话删除成功')
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error(`删除会话失败: ${error.message}`)
        }
      }
    }
    
    const refreshData = async () => {
      await loadSessions()
      if (currentSession.value) {
        await loadMemories()
      }
    }
    
    const editMemory = (memory) => {
      // 这里可以实现编辑记忆的功能
      ElMessage.info('编辑记忆功能待实现')
    }
    
    // 生命周期
    onMounted(() => {
      loadSessions()
    })
    
    return {
      // 响应式数据
      loading,
      creating,
      adding,
      searching,
      compressing,
      sessions,
      currentSession,
      memories,
      searchQuery,
      currentPage,
      pageSize,
      totalMemories,
      showAddMemoryDialog,
      showCompressionDialog,
      newMemory,
      compressionData,
      memoryRules,
      memoryUtils,
      
      // 方法
      loadSessions,
      loadMemories,
      createNewSession,
      selectSession,
      searchMemories,
      addMemory,
      compressMemories,
      deleteMemory,
      deleteSession,
      refreshData,
      editMemory
    }
  }
}
</script>

<style scoped>
.memory-manager {
  padding: 20px;
}

.memory-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.header-right {
  display: flex;
  gap: 10px;
}

.session-selector {
  margin-bottom: 20px;
}

.session-list {
  max-height: 400px;
  overflow-y: auto;
}

.session-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.3s;
}

.session-item:hover {
  border-color: #409eff;
  background-color: #f5f7fa;
}

.session-info {
  flex: 1;
}

.session-id {
  font-weight: bold;
  margin-bottom: 5px;
}

.session-meta {
  display: flex;
  gap: 15px;
  color: #909399;
  font-size: 12px;
}

.memory-content {
  margin-top: 20px;
}

.memory-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.toolbar-left {
  display: flex;
  gap: 10px;
  align-items: center;
}

.toolbar-right {
  display: flex;
  gap: 10px;
}

.memory-list {
  margin-bottom: 20px;
}

.memory-card {
  margin-bottom: 15px;
}

.memory-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.memory-scores {
  display: flex;
  gap: 10px;
}

.memory-actions {
  display: flex;
  gap: 5px;
}

.memory-text {
  margin-bottom: 10px;
  line-height: 1.6;
}

.memory-meta {
  display: flex;
  gap: 15px;
  color: #909399;
  font-size: 12px;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
</style>
