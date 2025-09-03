<template>
  <div class="table-display">
    <div class="table-header">
      <h3>📊 相关表格</h3>
      <span class="table-count">{{ tables.length }} 个表格</span>
    </div>
    
    <div class="tables-list">
      <div 
        v-for="(table, index) in displayedTables" 
        :key="index" 
        class="table-item"
      >
        <div class="table-info">
          <div class="table-title">
            {{ table.table_title || `表格 ${index + 1}` }}
          </div>
          <div class="table-meta">
            <span class="source">{{ table.document_name }}</span>
            <span v-if="table.page_number > 0" class="page">第{{ table.page_number }}页</span>
            <span class="score">相关性: {{ (table.similarity_score * 100).toFixed(0) }}%</span>
          </div>
        </div>
        
        <div class="table-content">
          <div 
            v-if="table.table_html" 
            class="table-html"
            v-html="table.table_html"
          ></div>
          <div 
            v-else 
            class="table-text"
          >
            {{ table.content }}
          </div>
        </div>
        
        <div class="table-actions">
          <el-button 
            size="small" 
            @click="copyTableContent(table)"
            icon="CopyDocument"
          >
            复制内容
          </el-button>
          <el-button 
            size="small" 
            @click="downloadTable(table, index)"
            icon="Download"
          >
            下载
          </el-button>
        </div>
      </div>
    </div>
    
    <!-- 显示更多按钮 -->
    <div v-if="tables.length > maxDisplayCount" class="show-more">
      <el-button 
        v-if="!showAll" 
        @click="showAll = true" 
        type="primary" 
        plain
        size="small"
      >
        显示全部表格 ({{ tables.length - maxDisplayCount }} 个)
      </el-button>
      <el-button 
        v-else 
        @click="showAll = false" 
        type="info" 
        plain
        size="small"
      >
        收起表格
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  tables: {
    type: Array,
    default: () => []
  }
})

// 控制显示状态
const showAll = ref(false)
const maxDisplayCount = 2 // 默认显示2个表格

// 计算显示的表格列表
const displayedTables = computed(() => {
  if (showAll.value || props.tables.length <= maxDisplayCount) {
    return props.tables
  }
  return props.tables.slice(0, maxDisplayCount)
})

const copyTableContent = async (table) => {
  try {
    const content = table.table_html || table.content
    await navigator.clipboard.writeText(content)
    ElMessage.success('表格内容已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败，请手动复制')
  }
}

const downloadTable = (table, index) => {
  try {
    const content = table.table_html || table.content
    const title = table.table_title || `表格_${index + 1}`
    const filename = `${title}.html`
    
    const blob = new Blob([content], { type: 'text/html' })
    const url = URL.createObjectURL(blob)
    
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    
    ElMessage.success('表格已下载')
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败')
  }
}
</script>

<style scoped>
.table-display {
  margin: 16px 0;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e0e0e0;
}

.table-header h3 {
  margin: 0;
  color: #333;
  font-size: 16px;
  font-weight: 600;
}

.table-count {
  color: #666;
  font-size: 14px;
}

.tables-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.table-item {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  background: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.table-info {
  padding: 12px 16px;
  background: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
}

.table-title {
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
  font-size: 14px;
}

.table-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: #666;
  flex-wrap: wrap;
}

.table-meta span {
  display: flex;
  align-items: center;
}

.table-content {
  padding: 16px;
  overflow-x: auto;
}

.table-html {
  width: 100%;
}

.table-html :deep(table) {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  background: white;
}

.table-html :deep(table th) {
  background: #f5f5f5;
  border: 1px solid #ddd;
  padding: 8px 12px;
  text-align: left;
  font-weight: 600;
  color: #333;
}

.table-html :deep(table td) {
  border: 1px solid #ddd;
  padding: 8px 12px;
  color: #666;
}

.table-html :deep(table tr:nth-child(even)) {
  background: #f9f9f9;
}

.table-html :deep(table tr:hover) {
  background: #f0f8ff;
}

.table-text {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.4;
  color: #666;
  white-space: pre-wrap;
  background: #f8f9fa;
  padding: 12px;
  border-radius: 4px;
  border: 1px solid #e9ecef;
}

.table-actions {
  padding: 12px 16px;
  background: #f8f9fa;
  border-top: 1px solid #e0e0e0;
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .table-content {
    padding: 12px;
  }
  
  .table-html :deep(table) {
    font-size: 12px;
  }
  
  .table-html :deep(table th),
  .table-html :deep(table td) {
    padding: 6px 8px;
  }
  
  .table-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .table-actions {
    padding: 8px 12px;
    flex-direction: column;
  }
  
  .table-actions .el-button {
    width: 100%;
  }
}

/* 表格样式增强 */
.table-html :deep(.result-table) {
  border: 2px solid #409eff;
  border-radius: 8px;
  overflow: hidden;
}

.table-html :deep(.result-table th) {
  background: #409eff;
  color: white;
  border-color: #409eff;
}

.table-html :deep(.result-table td) {
  border-color: #e0e0e0;
}

.table-html :deep(.result-table tr:hover) {
  background: #f0f8ff;
}

/* 表格内容样式 */
.table-content {
  .table-content {
    font-size: 13px;
    line-height: 1.5;
    color: #666;
  }
}

.show-more {
  margin-top: 16px;
  text-align: center;
}
</style>
