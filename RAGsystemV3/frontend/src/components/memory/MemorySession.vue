<template>
  <div class="memory-session">
    <!-- 会话信息卡片 -->
    <el-card class="session-info-card" v-if="session">
      <template #header>
        <div class="session-header">
          <span class="session-title">会话信息</span>
          <div class="session-actions">
            <el-button size="small" @click="refreshSession">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-button size="small" type="danger" @click="deleteSession">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </div>
        </div>
      </template>
      
      <div class="session-details">
        <div class="detail-item">
          <label>会话ID:</label>
          <span class="session-id">{{ session.session_id.substring(0, 8) }}...</span>
        </div>
        <div class="detail-item">
          <label>用户ID:</label>
          <span>{{ session.user_id }}</span>
        </div>
        <div class="detail-item">
          <label>创建时间:</label>
          <span>{{ session.formatted_created_at }}</span>
        </div>
        <div class="detail-item">
          <label>更新时间:</label>
          <span>{{ session.formatted_updated_at }}</span>
        </div>
        <div class="detail-item">
          <label>记忆数量:</label>
          <el-tag type="info">{{ session.memory_count }}</el-tag>
        </div>
        <div class="detail-item">
          <label>最后查询:</label>
          <span class="last-query">{{ session.last_query || '无' }}</span>
        </div>
      </div>
    </el-card>

    <!-- 记忆统计 -->
    <el-card class="memory-stats-card">
      <template #header>
        <span>记忆统计</span>
      </template>
      
      <div class="stats-grid" v-if="stats">
        <div class="stat-item">
          <div class="stat-value">{{ stats.total_memories }}</div>
          <div class="stat-label">总记忆数</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ stats.active_sessions }}</div>
          <div class="stat-label">活跃会话</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ stats.avg_memories_per_session.toFixed(1) }}</div>
          <div class="stat-label">平均记忆数</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ stats.last_activity ? formatTime(stats.last_activity) : '无' }}</div>
          <div class="stat-label">最后活动</div>
        </div>
      </div>
    </el-card>

    <!-- 快速操作 -->
    <el-card class="quick-actions-card">
      <template #header>
        <span>快速操作</span>
      </template>
      
      <div class="action-buttons">
        <el-button type="primary" @click="showAddMemory = true">
          <el-icon><Plus /></el-icon>
          添加记忆
        </el-button>
        <el-button @click="showSearchMemory = true">
          <el-icon><Search /></el-icon>
          搜索记忆
        </el-button>
        <el-button @click="showCompression = true">
          <el-icon><Compress /></el-icon>
          压缩记忆
        </el-button>
        <el-button @click="exportMemories">
          <el-icon><Download /></el-icon>
          导出记忆
        </el-button>
      </div>
    </el-card>

    <!-- 添加记忆对话框 -->
    <el-dialog
      v-model="showAddMemory"
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
        <el-button @click="showAddMemory = false">取消</el-button>
        <el-button type="primary" @click="addMemory" :loading="adding">确定</el-button>
      </template>
    </el-dialog>

    <!-- 搜索记忆对话框 -->
    <el-dialog
      v-model="showSearchMemory"
      title="搜索记忆"
      width="700px"
    >
      <el-form :model="searchForm" label-width="100px">
        <el-form-item label="搜索文本">
          <el-input
            v-model="searchForm.query_text"
            placeholder="输入搜索关键词..."
          />
        </el-form-item>
        <el-form-item label="相似度阈值">
          <el-slider
            v-model="searchForm.similarity_threshold"
            :min="0"
            :max="1"
            :step="0.1"
            show-input
          />
        </el-form-item>
        <el-form-item label="内容类型">
          <el-checkbox-group v-model="searchForm.content_types">
            <el-checkbox label="text">文本</el-checkbox>
            <el-checkbox label="image">图片</el-checkbox>
            <el-checkbox label="table">表格</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="最大结果数">
          <el-input-number
            v-model="searchForm.max_results"
            :min="1"
            :max="100"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSearchMemory = false">取消</el-button>
        <el-button type="primary" @click="searchMemories" :loading="searching">搜索</el-button>
      </template>
    </el-dialog>

    <!-- 压缩记忆对话框 -->
    <el-dialog
      v-model="showCompression"
      title="压缩记忆"
      width="500px"
    >
      <el-form :model="compressionForm" label-width="120px">
        <el-form-item label="压缩策略">
          <el-select v-model="compressionForm.strategy">
            <el-option label="语义压缩" value="semantic" />
            <el-option label="时间压缩" value="temporal" />
            <el-option label="重要性压缩" value="importance" />
          </el-select>
        </el-form-item>
        <el-form-item label="压缩阈值">
          <el-input-number
            v-model="compressionForm.threshold"
            :min="1"
            :max="1000"
          />
        </el-form-item>
        <el-form-item label="最大压缩比例">
          <el-slider
            v-model="compressionForm.max_ratio"
            :min="0.1"
            :max="1.0"
            :step="0.1"
            show-input
          />
        </el-form-item>
        <el-form-item label="强制压缩">
          <el-switch v-model="compressionForm.force" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCompression = false">取消</el-button>
        <el-button type="primary" @click="compressMemories" :loading="compressing">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Refresh, Delete, Plus, Search, Compress, Download 
} from '@element-plus/icons-vue'
import { sessionApi, memoryApi, compressionApi, statsApi, memoryUtils } from '@/services/memory/memoryApi'

export default {
  name: 'MemorySession',
  components: {
    Refresh,
    Delete,
    Plus,
    Search,
    Compress,
    Download
  },
  props: {
    sessionId: {
      type: String,
      required: true
    }
  },
  setup(props) {
    // 响应式数据
    const session = ref(null)
    const stats = ref(null)
    const loading = ref(false)
    const adding = ref(false)
    const searching = ref(false)
    const compressing = ref(false)
    
    // 对话框状态
    const showAddMemory = ref(false)
    const showSearchMemory = ref(false)
    const showCompression = ref(false)
    
    // 表单数据
    const newMemory = reactive({
      content: '',
      content_type: 'text',
      relevance_score: 0.5,
      importance_score: 0.5,
      metadata: {}
    })
    
    const searchForm = reactive({
      query_text: '',
      similarity_threshold: 0.7,
      content_types: ['text'],
      max_results: 10
    })
    
    const compressionForm = reactive({
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
      ]
    }
    
    // 方法
    const loadSession = async () => {
      try {
        loading.value = true
        const response = await sessionApi.get(props.sessionId)
        session.value = memoryUtils.formatSession(response)
      } catch (error) {
        ElMessage.error(`加载会话失败: ${error.message}`)
      } finally {
        loading.value = false
      }
    }
    
    const loadStats = async () => {
      try {
        const response = await statsApi.get()
        stats.value = response
      } catch (error) {
        ElMessage.error(`加载统计信息失败: ${error.message}`)
      }
    }
    
    const refreshSession = async () => {
      await Promise.all([loadSession(), loadStats()])
      ElMessage.success('会话信息已刷新')
    }
    
    const addMemory = async () => {
      try {
        adding.value = true
        
        // 验证数据
        const validation = memoryUtils.validateMemoryData(newMemory)
        if (!validation.isValid) {
          ElMessage.error(validation.errors.join(', '))
          return
        }
        
        await memoryApi.add(props.sessionId, newMemory)
        
        // 重置表单
        Object.assign(newMemory, {
          content: '',
          content_type: 'text',
          relevance_score: 0.5,
          importance_score: 0.5,
          metadata: {}
        })
        
        showAddMemory.value = false
        ElMessage.success('记忆添加成功')
        
        // 刷新会话信息
        await loadSession()
      } catch (error) {
        ElMessage.error(`添加记忆失败: ${error.message}`)
      } finally {
        adding.value = false
      }
    }
    
    const searchMemories = async () => {
      try {
        searching.value = true
        const response = await memoryApi.query(props.sessionId, searchForm)
        
        // 触发搜索结果事件
        emit('search-results', response.map(memory => memoryUtils.formatMemory(memory)))
        
        showSearchMemory.value = false
        ElMessage.success(`找到 ${response.length} 条相关记忆`)
      } catch (error) {
        ElMessage.error(`搜索记忆失败: ${error.message}`)
      } finally {
        searching.value = false
      }
    }
    
    const compressMemories = async () => {
      try {
        compressing.value = true
        const response = await compressionApi.compress(props.sessionId, compressionForm)
        
        ElMessage.success(`记忆压缩成功，压缩比例: ${(response.compression_ratio * 100).toFixed(1)}%`)
        showCompression.value = false
        
        // 刷新会话信息
        await loadSession()
      } catch (error) {
        ElMessage.error(`压缩记忆失败: ${error.message}`)
      } finally {
        compressing.value = false
      }
    }
    
    const deleteSession = async () => {
      try {
        await ElMessageBox.confirm('确定要删除这个会话吗？删除后无法恢复！', '确认删除', {
          type: 'warning'
        })
        
        // 这里需要实现删除会话的API
        // await sessionApi.delete(props.sessionId)
        
        ElMessage.success('会话删除成功')
        emit('session-deleted', props.sessionId)
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error(`删除会话失败: ${error.message}`)
        }
      }
    }
    
    const exportMemories = async () => {
      try {
        // 这里可以实现导出记忆的功能
        ElMessage.info('导出记忆功能待实现')
      } catch (error) {
        ElMessage.error(`导出记忆失败: ${error.message}`)
      }
    }
    
    const formatTime = (timeString) => {
      return new Date(timeString).toLocaleString()
    }
    
    // 生命周期
    onMounted(() => {
      loadSession()
      loadStats()
    })
    
    return {
      // 响应式数据
      session,
      stats,
      loading,
      adding,
      searching,
      compressing,
      showAddMemory,
      showSearchMemory,
      showCompression,
      newMemory,
      searchForm,
      compressionForm,
      memoryRules,
      
      // 方法
      loadSession,
      loadStats,
      refreshSession,
      addMemory,
      searchMemories,
      compressMemories,
      deleteSession,
      exportMemories,
      formatTime
    }
  }
}
</script>

<style scoped>
.memory-session {
  padding: 20px;
}

.session-info-card,
.memory-stats-card,
.quick-actions-card {
  margin-bottom: 20px;
}

.session-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.session-title {
  font-weight: bold;
  font-size: 16px;
}

.session-actions {
  display: flex;
  gap: 10px;
}

.session-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.detail-item label {
  font-weight: bold;
  color: #606266;
  font-size: 12px;
}

.session-id {
  font-family: monospace;
  background-color: #f5f7fa;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
}

.last-query {
  font-style: italic;
  color: #909399;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 20px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}

.action-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.action-buttons .el-button {
  flex: 1;
  min-width: 120px;
}
</style>
