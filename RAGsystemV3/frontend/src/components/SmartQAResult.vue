<template>
  <div class="smart-qa-result">
    <!-- 展示模式选择器 -->
    <DisplayModeSelector
      :query-type="queryType"
      :display-mode="displayMode"
      :content-analysis="contentAnalysis"
      :confidence="confidence"
      :allow-manual-selection="false"
      @display-mode-change="handleDisplayModeChange"
    />
    
    <!-- 根据展示模式动态显示内容 -->
    <div class="result-content">
      <!-- 文本优先模式 -->
      <div v-if="displayMode === 'text-focused'" class="text-focused-display">
        <div class="text-content">
          <!-- 1. 来源信息 -->
          <div class="source-section">
            <SourceAttribution :sources="sources" />
          </div>
          
          <!-- 2. 相关文本内容 -->
          <div v-if="textResults.length > 0" class="text-results">
            <h3>📝 相关文本内容</h3>
            <div v-for="result in displayedTextResults" :key="result.chunk_id" class="text-result">
              <div class="text-preview">
                <MarkdownRenderer :content="result.content" />
              </div>
              <div class="text-meta">
                <span class="source">{{ result.document_name }}</span>
                <span class="page">第{{ result.page_number }}页</span>
                <span class="score">相关性: {{ (result.similarity_score * 100).toFixed(0) }}%</span>
              </div>
            </div>
            
            <!-- 显示更多按钮 -->
            <div v-if="textResults.length > maxTextDisplayCount" class="show-more">
              <el-button 
                v-if="!showAllText" 
                @click="showAllText = true" 
                type="primary" 
                plain
                size="small"
              >
                显示剩余文本 ({{ textResults.length - maxTextDisplayCount }} 个)
              </el-button>
              <el-button 
                v-else 
                @click="showAllText = false" 
                type="info" 
                plain
                size="small"
              >
                收起文本
              </el-button>
            </div>
          </div>
          
          <!-- 3. LLM答案 -->
          <div class="llm-answer">
            <MarkdownRenderer :content="llmAnswer" />
          </div>
        </div>
      </div>
      
      <!-- 图片优先模式 -->
      <div v-else-if="displayMode === 'image-focused'" class="image-focused-display">
        <div class="image-content">
          <!-- 1. 来源信息 -->
          <div class="source-section">
            <SourceAttribution :sources="sources" />
          </div>
          
          <!-- 2. 相关图片 -->
          <div v-if="imageResults.length > 0" class="image-gallery">
            <ImageGallery :images="imageResults" />
          </div>
          
          <!-- 3. LLM答案 -->
          <div class="llm-answer">
            <MarkdownRenderer :content="llmAnswer" />
          </div>
        </div>
      </div>
      
      <!-- 表格优先模式 -->
      <div v-else-if="displayMode === 'table-focused'" class="table-focused-display">
        <div class="table-content">
          <!-- 1. 来源信息 -->
          <div class="source-section">
            <SourceAttribution :sources="sources" />
          </div>
          
          <!-- 2. 相关表格 -->
          <div v-if="tableResults.length > 0" class="table-results">
            <TableDisplay :tables="tableResults" />
          </div>
          
          <!-- 3. LLM答案 -->
          <div class="llm-answer">
            <MarkdownRenderer :content="llmAnswer" />
          </div>
        </div>
      </div>
      
      <!-- 混合布局模式 -->
      <div v-else-if="displayMode === 'hybrid-layout'" class="hybrid-layout-display">
        <div class="main-content">
          <!-- 1. 来源信息 -->
          <div class="source-section">
            <SourceAttribution :sources="sources" />
          </div>
          
          <!-- 2. 相关内容 -->
          <div class="content-grid">
            <div v-if="hasImages" class="image-section">
              <ImageGallery :images="imageResults" />
            </div>
            
            <div v-if="hasTables" class="table-section">
              <TableDisplay :tables="tableResults" />
            </div>
            
            <div v-if="hasText" class="text-section">
              <div class="text-results">
                <h3>📝 相关文本内容</h3>
                <div v-for="result in textResults" :key="result.chunk_id" class="text-result">
                  <div class="text-preview">
                    <MarkdownRenderer :content="result.content" />
                  </div>
                  <div class="text-meta">
                    <span class="source">{{ result.document_name }}</span>
                    <span class="page">第{{ result.page_number }}页</span>
                    <span class="score">相关性: {{ (result.similarity_score * 100).toFixed(0) }}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 3. LLM答案 -->
          <div class="llm-answer">
            <MarkdownRenderer :content="llmAnswer" />
          </div>
        </div>
      </div>
      
      <!-- 默认模式（智能检测） -->
      <div v-else class="auto-detect-display">
        <div class="main-content">
          <!-- 1. 来源信息 -->
          <div class="source-section">
            <SourceAttribution :sources="sources" />
          </div>
          
          <!-- 2. 相关内容 -->
          <div class="auto-results">
            <div v-if="imageResults.length > 0" class="auto-image-section">
              <ImageGallery :images="imageResults" />
            </div>
            
            <div v-if="tableResults.length > 0" class="auto-table-section">
              <TableDisplay :tables="tableResults" />
            </div>
            
            <div v-if="textResults.length > 0" class="auto-text-section">
              <div class="text-results">
                <h3>📝 相关文本内容</h3>
                <div v-for="result in displayedTextResults" :key="result.chunk_id" class="text-result">
                  <div class="text-preview">
                    <MarkdownRenderer :content="result.content" />
                  </div>
                  <div class="text-meta">
                    <span class="source">{{ result.document_name }}</span>
                    <span class="page">第{{ result.page_number }}页</span>
                    <span class="score">相关性: {{ (result.similarity_score * 100).toFixed(0) }}%</span>
                  </div>
                </div>
                
                <!-- 显示更多按钮 -->
                <div v-if="textResults.length > maxTextDisplayCount" class="show-more">
                  <el-button 
                    v-if="!showAllText" 
                    @click="showAllText = true" 
                    type="primary" 
                    plain
                    size="small"
                  >
                    显示剩余文本 ({{ textResults.length - maxTextDisplayCount }} 个)
                  </el-button>
                  <el-button 
                    v-else 
                    @click="showAllText = false" 
                    type="info" 
                    plain
                    size="small"
                  >
                    收起文本
                  </el-button>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 3. LLM答案 -->
          <div class="llm-answer">
            <MarkdownRenderer :content="llmAnswer" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import DisplayModeSelector from './DisplayModeSelector.vue'
import ImageGallery from './ImageGallery.vue'
import TableDisplay from './TableDisplay.vue'
import MarkdownRenderer from './MarkdownRenderer.vue'
import SourceAttribution from './SourceAttribution.vue'

const props = defineProps({
  queryType: {
    type: String,
    default: 'text'
  },
  displayMode: {
    type: String,
    default: 'text-focused'
  },
  llmAnswer: {
    type: String,
    default: ''
  },
  sources: {
    type: Array,
    default: () => []
  },
  contentAnalysis: {
    type: Object,
    default: null
  },
  confidence: {
    type: Number,
    default: 0.5
  }
})

const emit = defineEmits(['display-mode-change'])

// 按类型分组结果
const imageResults = computed(() => {
  return props.sources.filter(source => source.chunk_type === 'image')
})

const tableResults = computed(() => {
  return props.sources.filter(source => source.chunk_type === 'table')
})

const textResults = computed(() => {
  return props.sources.filter(source => source.chunk_type === 'text')
})

// 检查是否有特定类型的内容
const hasImages = computed(() => imageResults.value.length > 0)
const hasTables = computed(() => tableResults.value.length > 0)
const hasText = computed(() => textResults.value.length > 0)

// 控制文本显示状态
const showAllText = ref(false)
const maxTextDisplayCount = 2 // 默认显示2个文本

// 计算显示的文本列表
const displayedTextResults = computed(() => {
  if (showAllText.value || textResults.value.length <= maxTextDisplayCount) {
    return textResults.value
  }
  return textResults.value.slice(0, maxTextDisplayCount)
})

// 处理展示模式变更
const handleDisplayModeChange = (newMode) => {
  emit('display-mode-change', newMode)
}
</script>

<style scoped>
.smart-qa-result {
  width: 100%;
}

.result-content {
  margin-top: 16px;
}

/* 文本优先模式 */
.text-focused-display {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.text-content {
  width: 100%;
}

.llm-answer {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.text-results h3 {
  margin: 0 0 16px 0;
  color: #333;
  font-size: 16px;
  font-weight: 600;
}

.text-result {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.text-preview {
  margin-bottom: 12px;
  line-height: 1.6;
}

.text-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: #666;
  flex-wrap: nowrap;
}

.text-meta span {
  display: flex;
  align-items: center;
  white-space: nowrap;
}

.text-meta .source {
  flex: 1;
  min-width: 0;
  white-space: normal;
  word-wrap: break-word;
}

/* 图片优先模式 */
.image-focused-display {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.image-content {
  width: 100%;
}

/* 表格优先模式 */
.table-focused-display {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.table-content {
  width: 100%;
}

/* 混合布局模式 */
.hybrid-layout-display {
  display: flex;
  gap: 20px;
}

.main-content {
  flex: 1;
}

.content-grid {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.image-section,
.table-section,
.text-section {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* 自动检测模式 */
.auto-detect-display {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.auto-detect-display .main-content {
  width: 100%;
}

.source-section {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.auto-results {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.auto-image-section,
.auto-table-section,
.auto-text-section {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.side-content {
  width: 300px;
  flex-shrink: 0;
}

.show-more {
  margin-top: 16px;
  text-align: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .text-focused-display,
  .hybrid-layout-display {
    flex-direction: column;
  }
  
  .side-content {
    width: 100%;
  }
  
  .text-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}
</style>
