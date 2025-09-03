<template>
  <div class="source-attribution">
    <div class="attribution-header">
      <h4>📚 来源信息</h4>
      <span class="source-count">{{ sources.length }} 个来源</span>
    </div>
    
    <div class="sources-list">
      <div 
        v-for="(source, index) in sources.slice(0, maxSources)" 
        :key="index"
        class="source-item"
      >
        <div class="source-meta">
          <el-tag size="small" type="info">{{ source.document_name }}</el-tag>
          <el-tag size="small" type="success">{{ getChunkTypeLabel(source.chunk_type) }}</el-tag>
          <span v-if="source.page_number > 0" class="source-page">
            第{{ source.page_number }}页
          </span>
          <span class="source-score">
            相关性: {{ (source.similarity_score * 100).toFixed(0) }}%
          </span>
        </div>
        
        <div class="source-preview">
          {{ truncateText(source.content, 100) }}
        </div>
        
        <!-- 图片预览 -->
        <div v-if="source.chunk_type === 'image' && source.image_path" class="image-preview">
          <img 
            :src="getImageUrl(source.image_path)" 
            :alt="source.caption || '图片'"
            class="preview-image"
            @error="handleImageError"
          />
        </div>
        
        <!-- 表格预览 -->
        <div v-if="source.chunk_type === 'table' && source.table_html" class="table-preview">
          <div class="table-preview-content" v-html="source.table_html"></div>
        </div>
      </div>
    </div>
    
    <div v-if="sources.length > maxSources" class="show-more">
      <el-button size="small" @click="showAllSources = !showAllSources">
        {{ showAllSources ? '收起' : `显示全部 ${sources.length} 个来源` }}
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  sources: {
    type: Array,
    default: () => []
  },
  maxSources: {
    type: Number,
    default: 5
  }
})

const showAllSources = ref(false)

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

const truncateText = (text, maxLength) => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

const getImageUrl = (imagePath) => {
  if (!imagePath) return ''
  
  // 如果是相对路径，添加基础URL
  if (imagePath.startsWith('/') || imagePath.startsWith('./')) {
    return `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}${imagePath}`
  }
  
  // 如果是完整URL，直接返回
  return imagePath
}

const handleImageError = (event) => {
  console.warn('图片加载失败:', event.target.src)
  event.target.style.display = 'none'
}
</script>

<style scoped>
.source-attribution {
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
}

.attribution-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e0e0e0;
}

.attribution-header h4 {
  margin: 0;
  color: #333;
  font-size: 14px;
  font-weight: 600;
}

.source-count {
  color: #666;
  font-size: 12px;
}

.sources-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.source-item {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 12px;
}

.source-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
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
  margin-bottom: 8px;
}

.image-preview {
  margin-top: 8px;
}

.preview-image {
  width: 100%;
  max-width: 200px;
  height: auto;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
}

.table-preview {
  margin-top: 8px;
  overflow-x: auto;
}

.table-preview-content {
  font-size: 11px;
}

.table-preview-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
}

.table-preview-content :deep(table th) {
  background: #f5f5f5;
  border: 1px solid #ddd;
  padding: 4px 6px;
  text-align: left;
  font-weight: 600;
  color: #333;
}

.table-preview-content :deep(table td) {
  border: 1px solid #ddd;
  padding: 4px 6px;
  color: #666;
}

.show-more {
  margin-top: 12px;
  text-align: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .source-attribution {
    padding: 12px;
  }
  
  .source-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .preview-image {
    max-width: 150px;
  }
}
</style>
