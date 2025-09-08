<template>
  <div class="memory-list">
    <!-- 搜索和过滤工具栏 -->
    <div class="memory-toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="searchQuery"
          placeholder="搜索记忆内容..."
          @keyup.enter="handleSearch"
          clearable
          style="width: 300px;"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="handleSearch" :loading="searching">
          搜索
        </el-button>
        <el-button @click="handleReset">
          重置
        </el-button>
      </div>
      
      <div class="toolbar-right">
        <el-select v-model="contentTypeFilter" placeholder="内容类型" clearable style="width: 120px;">
          <el-option label="全部" value="" />
          <el-option label="文本" value="text" />
          <el-option label="图片" value="image" />
          <el-option label="表格" value="table" />
        </el-select>
        
        <el-select v-model="sortBy" placeholder="排序方式" style="width: 120px;">
          <el-option label="相关性" value="relevance" />
          <el-option label="重要性" value="importance" />
          <el-option label="时间" value="time" />
        </el-select>
        
        <el-button @click="handleRefresh" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 记忆列表 -->
    <div class="memory-items" v-loading="loading">
      <div v-if="memories.length === 0 && !loading" class="empty-state">
        <el-empty description="暂无记忆数据" />
      </div>
      
      <div v-else>
        <div 
          v-for="memory in paginatedMemories" 
          :key="memory.chunk_id"
          class="memory-item"
          @click="selectMemory(memory)"
          :class="{ 'selected': selectedMemory?.chunk_id === memory.chunk_id }"
        >
          <!-- 记忆头部 -->
          <div class="memory-header">
            <div class="memory-scores">
              <el-tag 
                :color="getSimilarityColor(memory.relevance_score)"
                size="small"
                effect="dark"
              >
                相关性: {{ memory.relevance_score.toFixed(2) }}
              </el-tag>
              <el-tag 
                :color="getImportanceColor(memory.importance_score)"
                size="small"
                effect="dark"
              >
                重要性: {{ memory.importance_score.toFixed(2) }}
              </el-tag>
            </div>
            
            <div class="memory-actions">
              <el-button size="small" @click.stop="editMemory(memory)">
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
              <el-button size="small" type="danger" @click.stop="deleteMemory(memory.chunk_id)">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </div>
          </div>
          
          <!-- 记忆内容 -->
          <div class="memory-content">
            <div class="memory-text">
              {{ memory.content }}
            </div>
            
            <!-- 记忆元数据 -->
            <div class="memory-meta">
              <div class="meta-left">
                <el-tag size="small" type="info">{{ memory.content_type }}</el-tag>
                <span class="created-time">{{ memory.formatted_created_at }}</span>
              </div>
              <div class="meta-right">
                <span class="chunk-id">ID: {{ memory.chunk_id.substring(0, 8) }}...</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination" v-if="totalMemories > pageSize">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="totalMemories"
        @current-change="handlePageChange"
        layout="total, prev, pager, next, jumper"
        :page-sizes="[10, 20, 50, 100]"
        @size-change="handleSizeChange"
      />
    </div>

    <!-- 记忆详情对话框 -->
    <el-dialog
      v-model="showMemoryDetail"
      :title="`记忆详情 - ${selectedMemory?.chunk_id.substring(0, 8)}...`"
      width="800px"
    >
      <div v-if="selectedMemory" class="memory-detail">
        <div class="detail-section">
          <h4>基本信息</h4>
          <div class="detail-grid">
            <div class="detail-item">
              <label>记忆ID:</label>
              <span>{{ selectedMemory.chunk_id }}</span>
            </div>
            <div class="detail-item">
              <label>会话ID:</label>
              <span>{{ selectedMemory.session_id }}</span>
            </div>
            <div class="detail-item">
              <label>内容类型:</label>
              <el-tag>{{ selectedMemory.content_type }}</el-tag>
            </div>
            <div class="detail-item">
              <label>创建时间:</label>
              <span>{{ selectedMemory.formatted_created_at }}</span>
            </div>
          </div>
        </div>
        
        <div class="detail-section">
          <h4>评分信息</h4>
          <div class="score-display">
            <div class="score-item">
              <label>相关性分数:</label>
              <div class="score-bar">
                <el-progress 
                  :percentage="selectedMemory.relevance_percentage"
                  :color="getSimilarityColor(selectedMemory.relevance_score)"
                />
              </div>
            </div>
            <div class="score-item">
              <label>重要性分数:</label>
              <div class="score-bar">
                <el-progress 
                  :percentage="selectedMemory.importance_percentage"
                  :color="getImportanceColor(selectedMemory.importance_score)"
                />
              </div>
            </div>
          </div>
        </div>
        
        <div class="detail-section">
          <h4>记忆内容</h4>
          <div class="content-display">
            {{ selectedMemory.content }}
          </div>
        </div>
        
        <div class="detail-section" v-if="selectedMemory.metadata && Object.keys(selectedMemory.metadata).length > 0">
          <h4>元数据</h4>
          <div class="metadata-display">
            <pre>{{ JSON.stringify(selectedMemory.metadata, null, 2) }}</pre>
          </div>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="showMemoryDetail = false">关闭</el-button>
        <el-button type="primary" @click="editMemory(selectedMemory)">编辑</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Edit, Delete } from '@element-plus/icons-vue'
import { memoryApi, memoryUtils } from '@/services/memory/memoryApi'

export default {
  name: 'MemoryList',
  components: {
    Search,
    Refresh,
    Edit,
    Delete
  },
  props: {
    sessionId: {
      type: String,
      required: true
    },
    memories: {
      type: Array,
      default: () => []
    }
  },
  emits: ['memory-selected', 'memory-updated', 'memory-deleted'],
  setup(props, { emit }) {
    // 响应式数据
    const loading = ref(false)
    const searching = ref(false)
    const searchQuery = ref('')
    const contentTypeFilter = ref('')
    const sortBy = ref('relevance')
    const selectedMemory = ref(null)
    const showMemoryDetail = ref(false)
    
    // 分页数据
    const currentPage = ref(1)
    const pageSize = ref(10)
    
    // 计算属性
    const filteredMemories = computed(() => {
      let filtered = [...props.memories]
      
      // 内容类型过滤
      if (contentTypeFilter.value) {
        filtered = filtered.filter(memory => memory.content_type === contentTypeFilter.value)
      }
      
      // 搜索过滤
      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase()
        filtered = filtered.filter(memory => 
          memory.content.toLowerCase().includes(query)
        )
      }
      
      // 排序
      filtered.sort((a, b) => {
        switch (sortBy.value) {
          case 'relevance':
            return b.relevance_score - a.relevance_score
          case 'importance':
            return b.importance_score - a.importance_score
          case 'time':
            return new Date(b.created_at) - new Date(a.created_at)
          default:
            return 0
        }
      })
      
      return filtered
    })
    
    const paginatedMemories = computed(() => {
      const start = (currentPage.value - 1) * pageSize.value
      const end = start + pageSize.value
      return filteredMemories.value.slice(start, end)
    })
    
    const totalMemories = computed(() => filteredMemories.value.length)
    
    // 方法
    const handleSearch = async () => {
      if (!props.sessionId) return
      
      try {
        searching.value = true
        const response = await memoryApi.query(props.sessionId, {
          query_text: searchQuery.value,
          max_results: 100,
          similarity_threshold: 0.7,
          content_types: contentTypeFilter.value ? [contentTypeFilter.value] : ['text', 'image', 'table']
        })
        
        // 更新父组件的记忆列表
        emit('memory-updated', response.map(memory => memoryUtils.formatMemory(memory)))
        
        ElMessage.success(`找到 ${response.length} 条相关记忆`)
      } catch (error) {
        ElMessage.error(`搜索记忆失败: ${error.message}`)
      } finally {
        searching.value = false
      }
    }
    
    const handleReset = () => {
      searchQuery.value = ''
      contentTypeFilter.value = ''
      sortBy.value = 'relevance'
      currentPage.value = 1
    }
    
    const handleRefresh = async () => {
      await handleSearch()
    }
    
    const selectMemory = (memory) => {
      selectedMemory.value = memory
      showMemoryDetail.value = true
      emit('memory-selected', memory)
    }
    
    const editMemory = (memory) => {
      // 这里可以实现编辑记忆的功能
      ElMessage.info('编辑记忆功能待实现')
    }
    
    const deleteMemory = async (chunkId) => {
      try {
        await ElMessageBox.confirm('确定要删除这个记忆吗？', '确认删除', {
          type: 'warning'
        })
        
        // 这里需要实现删除记忆的API
        // await memoryApi.delete(chunkId)
        
        emit('memory-deleted', chunkId)
        ElMessage.success('记忆删除成功')
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error(`删除记忆失败: ${error.message}`)
        }
      }
    }
    
    const handlePageChange = (page) => {
      currentPage.value = page
    }
    
    const handleSizeChange = (size) => {
      pageSize.value = size
      currentPage.value = 1
    }
    
    const getSimilarityColor = (score) => {
      return memoryUtils.getSimilarityColor(score)
    }
    
    const getImportanceColor = (score) => {
      return memoryUtils.getImportanceColor(score)
    }
    
    // 监听搜索查询变化
    watch(searchQuery, () => {
      if (searchQuery.value === '') {
        handleReset()
      }
    })
    
    // 监听内容类型过滤变化
    watch(contentTypeFilter, () => {
      currentPage.value = 1
    })
    
    // 监听排序方式变化
    watch(sortBy, () => {
      currentPage.value = 1
    })
    
    return {
      // 响应式数据
      loading,
      searching,
      searchQuery,
      contentTypeFilter,
      sortBy,
      selectedMemory,
      showMemoryDetail,
      currentPage,
      pageSize,
      
      // 计算属性
      filteredMemories,
      paginatedMemories,
      totalMemories,
      
      // 方法
      handleSearch,
      handleReset,
      handleRefresh,
      selectMemory,
      editMemory,
      deleteMemory,
      handlePageChange,
      handleSizeChange,
      getSimilarityColor,
      getImportanceColor
    }
  }
}
</script>

<style scoped>
.memory-list {
  padding: 20px;
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
  align-items: center;
}

.memory-items {
  min-height: 400px;
}

.memory-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 15px;
  cursor: pointer;
  transition: all 0.3s;
}

.memory-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.memory-item.selected {
  border-color: #409eff;
  background-color: #f0f9ff;
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

.memory-content {
  margin-bottom: 10px;
}

.memory-text {
  line-height: 1.6;
  margin-bottom: 10px;
  color: #303133;
}

.memory-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #909399;
}

.meta-left {
  display: flex;
  gap: 10px;
  align-items: center;
}

.created-time {
  font-style: italic;
}

.chunk-id {
  font-family: monospace;
  background-color: #f5f7fa;
  padding: 2px 6px;
  border-radius: 4px;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.empty-state {
  text-align: center;
  padding: 40px;
}

.memory-detail {
  max-height: 600px;
  overflow-y: auto;
}

.detail-section {
  margin-bottom: 20px;
}

.detail-section h4 {
  margin-bottom: 10px;
  color: #303133;
  border-bottom: 1px solid #e4e7ed;
  padding-bottom: 5px;
}

.detail-grid {
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

.score-display {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.score-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.score-item label {
  font-weight: bold;
  color: #606266;
}

.score-bar {
  width: 100%;
}

.content-display {
  background-color: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.metadata-display {
  background-color: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
  max-height: 200px;
  overflow-y: auto;
}
</style>
