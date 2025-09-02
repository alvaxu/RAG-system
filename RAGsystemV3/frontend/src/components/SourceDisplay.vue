<!--
程序说明：

## 1. 来源信息显示组件
- 显示完整的元数据信息（文档名、页码、表格名、图片名等）
- 不显示chunk-id等技术标识
- 从M15元数据管理模块获取详细信息

## 2. 与其他版本的不同点
- 新增了表格标题和图片标题的显示
- 隐藏了chunk-id等技术标识
- 优化了来源信息的展示格式
-->

<template>
  <div v-if="sources && sources.length > 0" class="sources-section">
    <div class="sources-header">
      <el-icon><Link /></el-icon>
      <span>来源信息 ({{ sources.length }}个)</span>
    </div>
    <div class="sources-list">
      <div 
        v-for="(source, index) in sources" 
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
            <!-- 新增：表格标题显示 -->
            <span v-if="source.table_title" class="source-table-title">
              《{{ source.table_title }}》
            </span>
            <!-- 新增：图片标题显示 -->
            <span v-if="source.image_caption" class="source-image-caption">
              {{ source.image_caption }}
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
</template>

<script setup>
import { 
  formatSimilarityScore, 
  truncateText,
  getContentTypeLabel
} from '@/utils/helpers.js'

// 定义props
const props = defineProps({
  sources: {
    type: Array,
    default: () => []
  }
})

/**
 * 获取来源类型标签样式
 * :param type: 内容类型
 * :return: 标签类型
 */
const getSourceTypeTag = (type) => {
  const tagMap = {
    'text': '',
    'image': 'success',
    'table': 'warning',
    'document': 'info'
  }
  return tagMap[type] || ''
}

/**
 * 获取相关性分数标签样式
 * :param score: 相关性分数
 * :return: 标签类型
 */
const getScoreTagType = (score) => {
  if (score >= 0.8) return 'success'
  if (score >= 0.6) return 'warning'
  if (score >= 0.4) return 'danger'
  return 'info'
}
</script>

<style scoped>
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
  flex-wrap: wrap;
}

.source-document {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.source-page {
  color: var(--el-text-color-placeholder);
  font-size: 0.9rem;
}

/* 新增：表格标题样式 */
.source-table-title {
  color: var(--el-color-warning);
  font-weight: 500;
  font-size: 0.9rem;
}

/* 新增：图片标题样式 */
.source-image-caption {
  color: var(--el-color-success);
  font-weight: 500;
  font-size: 0.9rem;
}

.source-preview {
  color: var(--el-text-color-regular);
  font-size: 0.9rem;
  line-height: 1.4;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .source-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .source-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}
</style>
