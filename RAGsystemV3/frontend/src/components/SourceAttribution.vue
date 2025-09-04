<template>
  <div class="source-attribution">
    <div class="attribution-header">
      <h4>📚 来源信息</h4>
      <span class="source-count">{{ sources.length }} 个来源</span>
    </div>
    
    <div class="sources-list">
      <div 
        v-for="(source, index) in displayedSources" 
        :key="index"
        class="source-item"
      >
        <div class="source-meta">
          <div class="source-document">{{ source.document_name }}</div>
          <el-tag size="small" type="success">{{ getChunkTypeLabel(source.chunk_type) }}</el-tag>
          <span v-if="source.page_number > 0" class="source-page">
            第{{ source.page_number }}页
          </span>
          <span class="source-score">
            相关性: {{ (source.similarity_score * 100).toFixed(0) }}%
          </span>
        </div>
      </div>
    </div>
    
    <div v-if="sources.length > maxSources" class="show-more">
      <el-button 
        v-if="!showAllSources" 
        @click="showAllSources = true" 
        type="primary" 
        plain
        size="small"
      >
        显示剩余来源 ({{ sources.length - maxSources }} 个)
      </el-button>
      <el-button 
        v-else 
        @click="showAllSources = false" 
        type="info" 
        plain
        size="small"
      >
        收起来源
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
    default: 2
  }
})

const showAllSources = ref(false)

// 计算显示的来源列表
const displayedSources = computed(() => {
  if (showAllSources.value || props.sources.length <= props.maxSources) {
    return props.sources
  }
  return props.sources.slice(0, props.maxSources)
})

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


</script>

<style scoped>
.source-attribution {
  padding: 0;
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

.source-document {
  color: #333;
  font-size: 12px;
  font-weight: 500;
  word-wrap: break-word;
  line-height: 1.4;
  flex: 1;
  min-width: 0;
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
  

}
</style>
