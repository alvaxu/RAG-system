<template>
  <div class="display-mode-selector">
    <!-- 查询类型指示器 -->
    <div class="query-type-indicator">
      <span class="type-icon">{{ currentQueryType.icon }}</span>
      <span class="type-name">{{ currentQueryType.name }}</span>
      <span class="type-desc">{{ currentQueryType.description }}</span>
    </div>
    
    <!-- 展示模式状态 -->
    <div class="display-mode-status">
      <span class="mode-label">当前展示模式：</span>
      <span class="mode-value">{{ currentDisplayMode.name }}</span>
      <span class="mode-desc">{{ currentDisplayMode.description }}</span>
    </div>
    
    <!-- 智能分析结果（仅智能和混合查询显示） -->
    <div v-if="showAnalysis && contentAnalysis" class="intelligence-analysis">
      <h4>🤖 智能分析结果</h4>
      <div class="analysis-content">
        <div class="analysis-item">
          <span class="item-label">检测到的内容类型：</span>
          <span class="item-value">{{ contentAnalysis.content_types?.join('、') || '未知' }}</span>
        </div>
        <div class="analysis-item">
          <span class="item-label">推荐展示模式：</span>
          <span class="item-value">{{ getDisplayModeName(displayMode) }}</span>
        </div>
        <div class="analysis-item">
          <span class="item-label">置信度：</span>
          <span class="item-value">{{ (confidence * 100).toFixed(0) }}%</span>
        </div>
        <div v-if="contentAnalysis.analysis_reason" class="analysis-item">
          <span class="item-label">分析原因：</span>
          <span class="item-value">{{ contentAnalysis.analysis_reason }}</span>
        </div>
      </div>
    </div>
    
    <!-- 手动模式选择（可选） -->
    <div v-if="allowManualSelection" class="manual-selection">
      <h4>🎛️ 手动选择展示模式</h4>
      <el-radio-group v-model="selectedMode" @change="handleModeChange">
        <el-radio-button 
          v-for="mode in availableModes" 
          :key="mode.id" 
          :label="mode.id"
        >
          {{ mode.icon }} {{ mode.name }}
        </el-radio-button>
      </el-radio-group>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  queryType: {
    type: String,
    default: 'text'
  },
  displayMode: {
    type: String,
    default: 'text-focused'
  },
  contentAnalysis: {
    type: Object,
    default: null
  },
  confidence: {
    type: Number,
    default: 0.5
  },
  allowManualSelection: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['display-mode-change'])

const selectedMode = ref(props.displayMode)

// 查询类型配置
const queryTypes = {
  'text': {
    name: '文本查询',
    icon: '📝',
    description: '查询文本内容',
    displayMode: 'text-focused'
  },
  'image': {
    name: '图片查询',
    icon: '🖼️',
    description: '查询图片内容',
    displayMode: 'image-focused'
  },
  'table': {
    name: '表格查询',
    icon: '📊',
    description: '查询表格数据',
    displayMode: 'table-focused'
  },
  'smart': {
    name: '智能查询',
    icon: '🤖',
    description: '系统自动判断查询类型',
    displayMode: 'auto-detect'
  },
  'hybrid': {
    name: '混合查询',
    icon: '🔀',
    description: '跨类型内容查询',
    displayMode: 'hybrid-layout'
  }
}

// 展示模式配置
const displayModes = {
  'text-focused': {
    id: 'text-focused',
    name: '文本优先',
    icon: '📝',
    description: '适合文本内容为主的查询'
  },
  'image-focused': {
    id: 'image-focused',
    name: '图片优先',
    icon: '🖼️',
    description: '适合图片内容为主的查询'
  },
  'table-focused': {
    id: 'table-focused',
    name: '表格优先',
    icon: '📊',
    description: '适合表格数据为主的查询'
  },
  'hybrid-layout': {
    id: 'hybrid-layout',
    name: '混合布局',
    icon: '🔀',
    description: '适合多种内容类型的查询'
  },
  'auto-detect': {
    id: 'auto-detect',
    name: '智能检测',
    icon: '🤖',
    description: '系统自动选择最佳展示模式'
  }
}

// 当前查询类型
const currentQueryType = computed(() => {
  return queryTypes[props.queryType] || queryTypes.smart
})

// 当前展示模式
const currentDisplayMode = computed(() => {
  return displayModes[props.displayMode] || displayModes['text-focused']
})

// 是否显示分析结果
const showAnalysis = computed(() => {
  return props.queryType === 'smart' || props.queryType === 'hybrid'
})

// 可用展示模式
const availableModes = computed(() => {
  if (props.queryType === 'text') {
    return [displayModes['text-focused']]
  } else if (props.queryType === 'image') {
    return [displayModes['image-focused']]
  } else if (props.queryType === 'table') {
    return [displayModes['table-focused']]
  } else {
    return Object.values(displayModes)
  }
})

// 获取展示模式名称
const getDisplayModeName = (modeId) => {
  return displayModes[modeId]?.name || modeId
}

// 处理模式变更
const handleModeChange = (newMode) => {
  emit('display-mode-change', newMode)
}

// 监听props变化
watch(() => props.displayMode, (newMode) => {
  selectedMode.value = newMode
})
</script>

<style scoped>
.display-mode-selector {
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  margin: 16px 0;
}

.query-type-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e0e0e0;
}

.type-icon {
  font-size: 20px;
}

.type-name {
  font-weight: 600;
  color: #333;
  font-size: 16px;
}

.type-desc {
  color: #666;
  font-size: 14px;
  margin-left: auto;
}

.display-mode-status {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.mode-label {
  color: #666;
  font-size: 14px;
}

.mode-value {
  font-weight: 600;
  color: #409eff;
  font-size: 14px;
}

.mode-desc {
  color: #666;
  font-size: 12px;
  margin-left: auto;
}

.intelligence-analysis {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 16px;
}

.intelligence-analysis h4 {
  margin: 0 0 12px 0;
  color: #333;
  font-size: 14px;
  font-weight: 600;
}

.analysis-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.analysis-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.item-label {
  color: #666;
  min-width: 120px;
}

.item-value {
  color: #333;
  font-weight: 500;
}

.manual-selection {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 12px;
}

.manual-selection h4 {
  margin: 0 0 12px 0;
  color: #333;
  font-size: 14px;
  font-weight: 600;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .display-mode-selector {
    padding: 12px;
  }
  
  .query-type-indicator {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .type-desc {
    margin-left: 0;
  }
  
  .display-mode-status {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .mode-desc {
    margin-left: 0;
  }
  
  .analysis-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .item-label {
    min-width: auto;
  }
}
</style>