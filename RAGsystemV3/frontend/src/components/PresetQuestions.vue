<!--
程序说明：

## 1. 预设问题组件
- 显示各种查询类型的预设问题
- 基于数据库实际内容生成的问题
- 用户点击预设问题可以自动填充查询

## 2. 与其他版本的不同点
- 新增了预设问题功能
- 支持5种查询类型的预设问题
- 基于中芯国际文档内容生成
-->

<template>
  <div v-if="questions && questions.length > 0" class="preset-questions">
    <div class="preset-header">
      <el-icon><Lightbulb /></el-icon>
      <span>推荐问题</span>
      <el-tag size="small" type="info">{{ questions.length }}个</el-tag>
    </div>
    
    <div class="questions-list">
      <div 
        v-for="question in questions" 
        :key="question.question_id"
        class="question-item"
        @click="selectQuestion(question)"
      >
        <div class="question-content">
          <div class="question-text">{{ question.question_text }}</div>
          <div class="question-meta">
            <el-tag 
              size="small" 
              :type="getQuestionTypeTag(question.question_type)"
            >
              {{ getQuestionTypeLabel(question.question_type) }}
            </el-tag>
            <span class="confidence">
              置信度: {{ (question.confidence * 100).toFixed(0) }}%
            </span>
          </div>
        </div>
        <div class="question-action">
          <el-icon><ArrowRight /></el-icon>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import ragAPI from '@/services/api.js'

// 定义props
const props = defineProps({
  queryType: {
    type: String,
    default: 'all'
  }
})

// 定义emits
const emit = defineEmits(['question-selected'])

// 响应式数据
const questions = ref([])
const loading = ref(false)

/**
 * 获取预设问题
 * :param queryType: 查询类型
 */
const fetchPresetQuestions = async (queryType) => {
  try {
    loading.value = true
    const response = await ragAPI.getPresetQuestions(queryType)
    questions.value = response.questions || []
  } catch (error) {
    console.error('获取预设问题失败:', error)
    questions.value = []
  } finally {
    loading.value = false
  }
}

/**
 * 选择预设问题
 * :param question: 选中的问题
 */
const selectQuestion = (question) => {
  emit('question-selected', question.question_text)
}

/**
 * 获取问题类型标签样式
 * :param type: 问题类型
 * :return: 标签类型
 */
const getQuestionTypeTag = (type) => {
  const tagMap = {
    'static': '',
    'dynamic': 'success',
    'ai_generated': 'warning'
  }
  return tagMap[type] || ''
}

/**
 * 获取问题类型标签文本
 * :param type: 问题类型
 * :return: 标签文本
 */
const getQuestionTypeLabel = (type) => {
  const labelMap = {
    'static': '静态',
    'dynamic': '动态',
    'ai_generated': 'AI生成'
  }
  return labelMap[type] || type
}

// 监听查询类型变化
watch(() => props.queryType, (newType) => {
  fetchPresetQuestions(newType)
}, { immediate: true })

// 组件挂载时获取预设问题
onMounted(() => {
  fetchPresetQuestions(props.queryType)
})
</script>

<style scoped>
.preset-questions {
  margin-bottom: 20px;
  padding: 16px;
  background: var(--el-bg-color-page);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
}

.preset-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.questions-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.question-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: white;
  border-radius: 6px;
  border: 1px solid var(--el-border-color-lighter);
  cursor: pointer;
  transition: all 0.2s ease;
}

.question-item:hover {
  border-color: var(--el-color-primary);
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
  transform: translateY(-1px);
}

.question-content {
  flex: 1;
  min-width: 0;
}

.question-text {
  font-size: 0.9rem;
  color: var(--el-text-color-primary);
  line-height: 1.4;
  margin-bottom: 6px;
  word-wrap: break-word;
}

.question-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.confidence {
  font-size: 0.8rem;
  color: var(--el-text-color-placeholder);
}

.question-action {
  color: var(--el-text-color-placeholder);
  transition: color 0.2s ease;
}

.question-item:hover .question-action {
  color: var(--el-color-primary);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .preset-questions {
    padding: 12px;
  }
  
  .question-item {
    padding: 10px;
  }
  
  .question-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}
</style>
