<!--
程序说明：

## 1. 展示模式选择器组件
- 实现单类查询的展示模式直接匹配
- 创建基础的展示模式配置
- 使用简化的内容分析算法

## 2. 与其他版本的不同点
- 新增了展示模式选择功能
- 使用简化的实现策略
- 先实现基础规则匹配，后续可优化
-->

<template>
  <div v-if="enabled" class="display-mode-selector">
    <div class="selector-header">
      <el-icon><View /></el-icon>
      <span>展示模式</span>
    </div>
    
    <div class="mode-options">
      <el-radio-group 
        v-model="selectedMode" 
        @change="handleModeChange"
        class="mode-radio-group"
      >
        <el-radio-button 
          v-for="mode in availableModes" 
          :key="mode.value"
          :label="mode.value"
          :disabled="mode.disabled"
        >
          <el-icon><component :is="mode.icon" /></el-icon>
          {{ mode.label }}
        </el-radio-button>
      </el-radio-group>
    </div>
    
    <div v-if="showDescription" class="mode-description">
      <el-text type="info" size="small">
        {{ getModeDescription(selectedMode) }}
      </el-text>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { 
  View, 
  Document, 
  Picture, 
  Grid, 
  Connection,
  MagicStick 
} from '@element-plus/icons-vue'

// 定义props
const props = defineProps({
  queryType: {
    type: String,
    default: 'smart'
  },
  enabled: {
    type: Boolean,
    default: true
  },
  showDescription: {
    type: Boolean,
    default: true
  }
})

// 定义emits
const emit = defineEmits(['mode-changed'])

// 响应式数据
const selectedMode = ref('auto-detect')

// 展示模式配置
const displayModes = {
  'text-focused': {
    label: '文本优先',
    icon: 'Document',
    description: '以文本内容为主要展示方式，适合文档查询',
    queryTypes: ['text', 'smart']
  },
  'image-focused': {
    label: '图片优先',
    icon: 'Picture',
    description: '以图片内容为主要展示方式，适合图片查询',
    queryTypes: ['image']
  },
  'table-focused': {
    label: '表格优先',
    icon: 'Grid',
    description: '以表格内容为主要展示方式，适合表格查询',
    queryTypes: ['table']
  },
  'hybrid-layout': {
    label: '混合布局',
    icon: 'Connection',
    description: '综合展示多种内容类型，适合混合查询',
    queryTypes: ['hybrid']
  },
  'auto-detect': {
    label: '智能选择',
    icon: 'MagicStick',
    description: '根据查询类型和内容自动选择最佳展示模式',
    queryTypes: ['smart', 'all']
  }
}

// 计算属性
const availableModes = computed(() => {
  const modes = []
  
  for (const [value, config] of Object.entries(displayModes)) {
    const isAvailable = config.queryTypes.includes(props.queryType) || 
                       config.queryTypes.includes('all')
    
    modes.push({
      value,
      label: config.label,
      icon: config.icon,
      disabled: !isAvailable
    })
  }
  
  return modes
})

/**
 * 获取模式描述
 * :param mode: 展示模式
 * :return: 模式描述
 */
const getModeDescription = (mode) => {
  return displayModes[mode]?.description || ''
}

/**
 * 处理模式变化
 * :param mode: 选中的展示模式
 */
const handleModeChange = (mode) => {
  emit('mode-changed', {
    mode,
    queryType: props.queryType,
    description: getModeDescription(mode)
  })
}

/**
 * 根据查询类型自动选择展示模式
 * :param queryType: 查询类型
 * :return: 推荐的展示模式
 */
const getRecommendedMode = (queryType) => {
  const modeMap = {
    'text': 'text-focused',
    'image': 'image-focused',
    'table': 'table-focused',
    'hybrid': 'hybrid-layout',
    'smart': 'auto-detect'
  }
  
  return modeMap[queryType] || 'auto-detect'
}

// 监听查询类型变化，自动选择展示模式
watch(() => props.queryType, (newType) => {
  const recommendedMode = getRecommendedMode(newType)
  selectedMode.value = recommendedMode
  handleModeChange(recommendedMode)
}, { immediate: true })

// 组件挂载时初始化
onMounted(() => {
  const recommendedMode = getRecommendedMode(props.queryType)
  selectedMode.value = recommendedMode
  handleModeChange(recommendedMode)
})
</script>

<style scoped>
.display-mode-selector {
  margin-bottom: 16px;
  padding: 12px;
  background: var(--el-bg-color-page);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
}

.selector-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.mode-options {
  margin-bottom: 8px;
}

.mode-radio-group {
  width: 100%;
}

.mode-radio-group :deep(.el-radio-button) {
  flex: 1;
}

.mode-radio-group :deep(.el-radio-button__inner) {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  width: 100%;
  padding: 8px 12px;
  font-size: 0.9rem;
}

.mode-description {
  padding: 8px 12px;
  background: var(--el-bg-color);
  border-radius: 4px;
  border-left: 3px solid var(--el-color-primary);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .display-mode-selector {
    padding: 8px;
  }
  
  .mode-radio-group :deep(.el-radio-button__inner) {
    padding: 6px 8px;
    font-size: 0.8rem;
  }
  
  .mode-radio-group :deep(.el-radio-button__inner .el-icon) {
    display: none;
  }
}
</style>
