<template>
  <div class="smart-qa-result">
    <!-- 思考状态显示 -->
    <div v-if="isThinking" class="thinking-display">
      <div class="thinking-content">
        <div class="thinking-text">
          <span class="typing-text">正在思考中</span>
          <span class="cursor">█</span>
        </div>
      </div>
    </div>
    
    <!-- 正常结果展示 -->
    <div v-else class="result-content">
      <!-- 默认状态：只显示LLM答案 -->
      <div v-if="!props.showDetails" class="simplified-display">
        <!-- LLM答案 -->
        <div class="llm-answer-simple">
          <MarkdownRenderer :content="llmAnswer" />
        </div>
      </div>
      
      <!-- 展开状态：显示所有详细信息 -->
      <div v-else class="detailed-display">
        <!-- 详细信息内容 -->
        <transition name="slide-down">
          <div class="detailed-content">
            <!-- 来源信息 -->
            <div class="source-section">
              <SourceAttribution :sources="sources" />
            </div>
            
            <!-- 相关内容区域 -->
            <div class="content-sections">
              <!-- 相关文本内容 -->
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
              
              <!-- 相关图片内容 -->
              <div v-if="imageResults.length > 0" class="image-results">
                <h3>🖼️ 相关图片内容</h3>
                <ImageGallery :images="imageResults" />
              </div>
              
              <!-- 相关表格内容 -->
              <div v-if="tableResults.length > 0" class="table-results">
                <h3>📊 相关表格内容</h3>
                <TableDisplay :tables="tableResults" />
              </div>
            </div>
            
            <!-- LLM答案 -->
            <div class="llm-answer">
              <h3>🤖 AI回答</h3>
              <MarkdownRenderer :content="llmAnswer" />
            </div>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { View, Hide } from '@element-plus/icons-vue'
import ImageGallery from './ImageGallery.vue'
import TableDisplay from './TableDisplay.vue'
import MarkdownRenderer from './MarkdownRenderer.vue'
import SourceAttribution from './SourceAttribution.vue'

const props = defineProps({
  queryType: {
    type: String,
    default: 'text'
  },
  llmAnswer: {
    type: String,
    default: ''
  },
  sources: {
    type: Array,
    default: () => []
  },
  showDetails: {
    type: Boolean,
    default: false
  },
  isThinking: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['toggle-details'])

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
</script>

<style scoped>
.smart-qa-result {
  width: 100%;
}

/* 思考状态样式 */
.thinking-display {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60px;
}

.thinking-content {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.thinking-text {
  display: flex;
  align-items: center;
  font-size: 16px;
  color: #666;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.typing-text {
  margin-right: 2px;
}

.cursor {
  animation: blink 1s infinite;
  color: #409eff;
  font-weight: bold;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.result-content {
  margin-top: 16px;
}

/* 简化显示模式 */
.simplified-display {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.llm-answer-simple {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  font-size: 16px;
  line-height: 1.6;
}

/* 详细显示模式 */
.detailed-display {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detailed-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.content-sections {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 来源信息 */
.source-section {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* 文本结果 */
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

/* 图片和表格结果 */
.image-results h3,
.table-results h3 {
  margin: 0 0 16px 0;
  color: #333;
  font-size: 16px;
  font-weight: 600;
}

.image-results,
.table-results {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* LLM答案 */
.llm-answer {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.llm-answer h3 {
  margin: 0 0 16px 0;
  color: #333;
  font-size: 16px;
  font-weight: 600;
}

.show-more {
  margin-top: 16px;
  text-align: center;
}

/* 动画效果 */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .text-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .details-button-container,
  .collapse-button-container {
    justify-content: center;
  }
}
</style>
