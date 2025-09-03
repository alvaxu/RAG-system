<template>
  <div class="markdown-renderer">
    <div 
      class="markdown-content"
      v-html="renderedMarkdown"
    ></div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { marked } from 'marked'

const props = defineProps({
  content: {
    type: String,
    default: ''
  },
  options: {
    type: Object,
    default: () => ({})
  }
})

// 配置marked选项
const markdownOptions = {
  breaks: true, // 支持换行
  gfm: true, // GitHub风格Markdown
  sanitize: false, // 允许HTML（需要谨慎使用）
  ...props.options
}

// 渲染Markdown内容
const renderedMarkdown = computed(() => {
  if (!props.content) return ''
  
  try {
    return marked(props.content, markdownOptions)
  } catch (error) {
    console.error('Markdown渲染失败:', error)
    return `<p>Markdown渲染失败: ${error.message}</p>`
  }
})
</script>

<style scoped>
.markdown-renderer {
  line-height: 1.6;
  color: #333;
}

.markdown-content {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

/* Markdown内容样式 */
.markdown-content :deep(h1) {
  font-size: 24px;
  font-weight: 700;
  margin: 24px 0 16px 0;
  color: #1a1a1a;
  border-bottom: 2px solid #e0e0e0;
  padding-bottom: 8px;
}

.markdown-content :deep(h2) {
  font-size: 20px;
  font-weight: 600;
  margin: 20px 0 12px 0;
  color: #1a1a1a;
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 6px;
}

.markdown-content :deep(h3) {
  font-size: 18px;
  font-weight: 600;
  margin: 16px 0 10px 0;
  color: #1a1a1a;
}

.markdown-content :deep(h4) {
  font-size: 16px;
  font-weight: 600;
  margin: 14px 0 8px 0;
  color: #1a1a1a;
}

.markdown-content :deep(h5) {
  font-size: 14px;
  font-weight: 600;
  margin: 12px 0 6px 0;
  color: #1a1a1a;
}

.markdown-content :deep(h6) {
  font-size: 13px;
  font-weight: 600;
  margin: 10px 0 4px 0;
  color: #666;
}

.markdown-content :deep(p) {
  margin: 12px 0;
  line-height: 1.6;
}

.markdown-content :deep(strong) {
  font-weight: 600;
  color: #1a1a1a;
}

.markdown-content :deep(em) {
  font-style: italic;
  color: #555;
}

.markdown-content :deep(code) {
  background: #f5f5f5;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 2px 6px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: #d63384;
}

.markdown-content :deep(pre) {
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  overflow-x: auto;
  margin: 16px 0;
}

.markdown-content :deep(pre code) {
  background: none;
  border: none;
  padding: 0;
  color: #333;
  font-size: 14px;
}

.markdown-content :deep(blockquote) {
  border-left: 4px solid #409eff;
  background: #f0f8ff;
  margin: 16px 0;
  padding: 12px 16px;
  color: #555;
  font-style: italic;
}

.markdown-content :deep(ul) {
  margin: 12px 0;
  padding-left: 24px;
}

.markdown-content :deep(ol) {
  margin: 12px 0;
  padding-left: 24px;
}

.markdown-content :deep(li) {
  margin: 4px 0;
  line-height: 1.5;
}

.markdown-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0;
  font-size: 14px;
}

.markdown-content :deep(table th) {
  background: #f5f5f5;
  border: 1px solid #ddd;
  padding: 8px 12px;
  text-align: left;
  font-weight: 600;
  color: #333;
}

.markdown-content :deep(table td) {
  border: 1px solid #ddd;
  padding: 8px 12px;
  color: #666;
}

.markdown-content :deep(table tr:nth-child(even)) {
  background: #f9f9f9;
}

.markdown-content :deep(table tr:hover) {
  background: #f0f8ff;
}

.markdown-content :deep(a) {
  color: #409eff;
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: border-color 0.2s ease;
}

.markdown-content :deep(a:hover) {
  border-bottom-color: #409eff;
}

.markdown-content :deep(hr) {
  border: none;
  border-top: 2px solid #e0e0e0;
  margin: 24px 0;
}

.markdown-content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin: 16px 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .markdown-content :deep(h1) {
    font-size: 20px;
  }
  
  .markdown-content :deep(h2) {
    font-size: 18px;
  }
  
  .markdown-content :deep(h3) {
    font-size: 16px;
  }
  
  .markdown-content :deep(pre) {
    padding: 12px;
    font-size: 13px;
  }
  
  .markdown-content :deep(table) {
    font-size: 12px;
  }
  
  .markdown-content :deep(table th),
  .markdown-content :deep(table td) {
    padding: 6px 8px;
  }
}
</style>
