<!--
程序说明：

## 1. 混合布局展示组件
- 实现混合查询的内容分析功能
- 分析LLM答案内容，确定展示模式
- 实现混合布局展示组件

## 2. 与其他版本的不同点
- 新增了混合查询展示功能
- 使用简化的分析算法
- 根据内容特征智能选择展示模式
-->

<template>
  <div class="hybrid-layout-display">
    <div class="content-analysis">
      <div class="analysis-header">
        <el-icon><Connection /></el-icon>
        <span>混合内容分析</span>
        <el-tag size="small" :type="getAnalysisTagType(analysisResult.confidence)">
          置信度: {{ (analysisResult.confidence * 100).toFixed(0) }}%
        </el-tag>
      </div>
      
      <div class="analysis-content">
        <div class="content-scores">
          <div 
            v-for="(score, type) in analysisResult.scores" 
            :key="type"
            class="score-item"
          >
            <el-tag 
              size="small" 
              :type="getScoreTagType(score)"
              :class="{ 'active': score > 0.5 }"
            >
              {{ getContentTypeLabel(type) }}: {{ (score * 100).toFixed(0) }}%
            </el-tag>
          </div>
        </div>
        
        <div class="recommended-mode">
          <span>推荐展示模式: </span>
          <el-tag :type="getModeTagType(recommendedMode)">
            {{ getModeLabel(recommendedMode) }}
          </el-tag>
        </div>
      </div>
    </div>

    <div class="content-display">
      <!-- 文本内容 -->
      <div v-if="analysisResult.scores.text > 0.3" class="text-content">
        <div class="content-header">
          <el-icon><Document /></el-icon>
          <span>文本内容</span>
        </div>
        <div class="content-body">
          <div v-html="formattedTextContent"></div>
        </div>
      </div>

      <!-- 表格内容 -->
      <div v-if="analysisResult.scores.table > 0.3" class="table-content">
        <div class="content-header">
          <el-icon><Grid /></el-icon>
          <span>表格内容</span>
        </div>
        <div class="content-body">
          <div v-html="formattedTableContent"></div>
        </div>
      </div>

      <!-- 图片内容 -->
      <div v-if="analysisResult.scores.image > 0.3" class="image-content">
        <div class="content-header">
          <el-icon><Picture /></el-icon>
          <span>图片内容</span>
        </div>
        <div class="content-body">
          <div v-html="formattedImageContent"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { analyzeHybridQueryContent } from '@/utils/ContentAnalyzer.js'
import { getContentTypeLabel } from '@/utils/helpers.js'

// 定义props
const props = defineProps({
  content: {
    type: String,
    required: true
  },
  sources: {
    type: Array,
    default: () => []
  }
})

// 响应式数据
const analysisResult = ref({
  scores: {
    text: 0,
    image: 0,
    table: 0
  },
  confidence: 0,
  recommendedMode: 'hybrid-layout'
})

// 计算属性
const recommendedMode = computed(() => {
  return analysisResult.value.recommendedMode
})

const formattedTextContent = computed(() => {
  // 简化的文本格式化
  return props.content.replace(/\n/g, '<br>')
})

const formattedTableContent = computed(() => {
  // 简化的表格格式化
  if (props.content.includes('|') || props.content.includes('表格')) {
    return '<div class="table-placeholder">表格内容已识别，具体展示待实现</div>'
  }
  return ''
})

const formattedImageContent = computed(() => {
  // 简化的图片格式化
  if (props.content.includes('图片') || props.content.includes('图')) {
    return '<div class="image-placeholder">图片内容已识别，具体展示待实现</div>'
  }
  return ''
})

/**
 * 分析内容
 */
const analyzeContent = () => {
  try {
    const recommendedMode = analyzeHybridQueryContent(props.content)
    
    // 简化的内容分析
    const contentLower = props.content.toLowerCase()
    const scores = {
      text: calculateScore(contentLower, ['文档', '文本', '内容', '描述', '说明']),
      image: calculateScore(contentLower, ['图片', '图像', '图表', '照片', '图']),
      table: calculateScore(contentLower, ['表格', '数据', '统计', '列表', '表'])
    }
    
    const confidence = Math.max(...Object.values(scores))
    
    analysisResult.value = {
      scores,
      confidence,
      recommendedMode
    }
  } catch (error) {
    console.error('内容分析失败:', error)
    analysisResult.value = {
      scores: { text: 0.5, image: 0, table: 0 },
      confidence: 0.5,
      recommendedMode: 'hybrid-layout'
    }
  }
}

/**
 * 计算内容分数
 * :param text: 文本内容
 * :param keywords: 关键词数组
 * :return: 分数
 */
const calculateScore = (text, keywords) => {
  let score = 0
  keywords.forEach(keyword => {
    if (text.includes(keyword)) {
      score += 1 / keywords.length
    }
  })
  return Math.min(score, 1.0)
}

/**
 * 获取分析结果标签类型
 * :param confidence: 置信度
 * :return: 标签类型
 */
const getAnalysisTagType = (confidence) => {
  if (confidence >= 0.8) return 'success'
  if (confidence >= 0.6) return 'warning'
  return 'info'
}

/**
 * 获取分数标签类型
 * :param score: 分数
 * :return: 标签类型
 */
const getScoreTagType = (score) => {
  if (score >= 0.7) return 'success'
  if (score >= 0.4) return 'warning'
  return 'info'
}

/**
 * 获取模式标签类型
 * :param mode: 展示模式
 * :return: 标签类型
 */
const getModeTagType = (mode) => {
  const typeMap = {
    'text-focused': '',
    'image-focused': 'success',
    'table-focused': 'warning',
    'hybrid-layout': 'info'
  }
  return typeMap[mode] || 'info'
}

/**
 * 获取模式标签文本
 * :param mode: 展示模式
 * :return: 标签文本
 */
const getModeLabel = (mode) => {
  const labelMap = {
    'text-focused': '文本优先',
    'image-focused': '图片优先',
    'table-focused': '表格优先',
    'hybrid-layout': '混合布局'
  }
  return labelMap[mode] || mode
}

// 监听内容变化
watch(() => props.content, () => {
  analyzeContent()
}, { immediate: true })
</script>

<style scoped>
.hybrid-layout-display {
  margin-top: 16px;
}

.content-analysis {
  margin-bottom: 16px;
  padding: 12px;
  background: var(--el-bg-color-page);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
}

.analysis-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.analysis-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.content-scores {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.score-item .el-tag.active {
  font-weight: 600;
}

.recommended-mode {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  color: var(--el-text-color-regular);
}

.content-display {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.text-content,
.table-content,
.image-content {
  padding: 12px;
  background: white;
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
}

.content-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.content-body {
  line-height: 1.6;
  color: var(--el-text-color-regular);
}

.table-placeholder,
.image-placeholder {
  padding: 20px;
  text-align: center;
  color: var(--el-text-color-placeholder);
  background: var(--el-bg-color-page);
  border-radius: 4px;
  border: 2px dashed var(--el-border-color);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .content-scores {
    flex-direction: column;
  }
  
  .recommended-mode {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
