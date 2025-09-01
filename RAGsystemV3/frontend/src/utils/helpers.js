/**
 * 工具函数集合
 */

/**
 * 格式化时间戳
 * @param {number|string|Date} timestamp - 时间戳
 * @param {string} format - 格式类型
 * @returns {string} 格式化后的时间字符串
 */
export function formatTimestamp(timestamp, format = 'default') {
  if (!timestamp) return ''
  
  const date = new Date(timestamp)
  if (isNaN(date.getTime())) return ''
  
  const now = new Date()
  const diff = now - date
  
  // 小于1分钟
  if (diff < 60000) {
    return '刚刚'
  }
  
  // 小于1小时
  if (diff < 3600000) {
    const minutes = Math.floor(diff / 60000)
    return `${minutes}分钟前`
  }
  
  // 小于1天
  if (diff < 86400000) {
    const hours = Math.floor(diff / 3600000)
    return `${hours}小时前`
  }
  
  // 小于7天
  if (diff < 604800000) {
    const days = Math.floor(diff / 86400000)
    return `${days}天前`
  }
  
  // 超过7天，显示具体日期
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/**
 * 格式化相似度分数
 * @param {number} score - 相似度分数
 * @param {number} decimals - 小数位数
 * @returns {string} 格式化后的分数
 */
export function formatSimilarityScore(score, decimals = 3) {
  if (typeof score !== 'number' || isNaN(score)) return '0.000'
  return score.toFixed(decimals)
}

/**
 * 获取相似度分数的颜色类名
 * @param {number} score - 相似度分数
 * @returns {string} CSS类名
 */
export function getScoreColorClass(score) {
  if (score >= 0.8) return 'score-high'
  if (score >= 0.6) return 'score-medium'
  if (score >= 0.4) return 'score-low'
  return 'score-very-low'
}

/**
 * 截断文本
 * @param {string} text - 原始文本
 * @param {number} maxLength - 最大长度
 * @param {string} suffix - 后缀
 * @returns {string} 截断后的文本
 */
export function truncateText(text, maxLength = 100, suffix = '...') {
  if (!text || typeof text !== 'string') return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + suffix
}

/**
 * 高亮关键词
 * @param {string} text - 原始文本
 * @param {string} keyword - 关键词
 * @param {string} className - 高亮样式类名
 * @returns {string} 高亮后的HTML
 */
export function highlightKeyword(text, keyword, className = 'highlight') {
  if (!text || !keyword) return text
  
  const regex = new RegExp(`(${keyword})`, 'gi')
  return text.replace(regex, `<span class="${className}">$1</span>`)
}

/**
 * 复制文本到剪贴板
 * @param {string} text - 要复制的文本
 * @returns {Promise<boolean>} 是否成功
 */
export async function copyToClipboard(text) {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
      return true
    } else {
      // 降级方案
      const textArea = document.createElement('textarea')
      textArea.value = text
      textArea.style.position = 'fixed'
      textArea.style.left = '-999999px'
      textArea.style.top = '-999999px'
      document.body.appendChild(textArea)
      textArea.focus()
      textArea.select()
      const result = document.execCommand('copy')
      textArea.remove()
      return result
    }
  } catch (error) {
    console.error('复制失败:', error)
    return false
  }
}

/**
 * 防抖函数
 * @param {Function} func - 要防抖的函数
 * @param {number} delay - 延迟时间
 * @returns {Function} 防抖后的函数
 */
export function debounce(func, delay = 300) {
  let timeoutId
  return function (...args) {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => func.apply(this, args), delay)
  }
}

/**
 * 节流函数
 * @param {Function} func - 要节流的函数
 * @param {number} delay - 延迟时间
 * @returns {Function} 节流后的函数
 */
export function throttle(func, delay = 300) {
  let lastCall = 0
  return function (...args) {
    const now = Date.now()
    if (now - lastCall >= delay) {
      lastCall = now
      return func.apply(this, args)
    }
  }
}

/**
 * 生成唯一ID
 * @param {string} prefix - 前缀
 * @returns {string} 唯一ID
 */
export function generateId(prefix = 'id') {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

/**
 * 验证查询文本
 * @param {string} query - 查询文本
 * @returns {Object} 验证结果
 */
export function validateQuery(query) {
  if (!query || typeof query !== 'string') {
    return { valid: false, message: '请输入查询内容' }
  }
  
  const trimmedQuery = query.trim()
  if (trimmedQuery.length === 0) {
    return { valid: false, message: '查询内容不能为空' }
  }
  
  if (trimmedQuery.length < 2) {
    return { valid: false, message: '查询内容至少需要2个字符' }
  }
  
  if (trimmedQuery.length > 1000) {
    return { valid: false, message: '查询内容不能超过1000个字符' }
  }
  
  return { valid: true, message: '' }
}

/**
 * 获取内容类型标签
 * @param {string} type - 内容类型
 * @returns {string} 类型标签
 */
export function getContentTypeLabel(type) {
  const typeMap = {
    'text': '文本',
    'image': '图片',
    'table': '表格',
    'document': '文档',
    'unknown': '未知'
  }
  return typeMap[type] || type
}

/**
 * 获取内容类型图标
 * @param {string} type - 内容类型
 * @returns {string} 图标名称
 */
export function getContentTypeIcon(type) {
  const iconMap = {
    'text': 'Document',
    'image': 'Picture',
    'table': 'Grid',
    'document': 'Document',
    'unknown': 'QuestionFilled'
  }
  return iconMap[type] || 'QuestionFilled'
}

/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 * @returns {string} 格式化后的大小
 */
export function formatFileSize(bytes) {
  if (bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 检查是否为移动设备
 * @returns {boolean} 是否为移动设备
 */
export function isMobile() {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
}

/**
 * 获取浏览器信息
 * @returns {Object} 浏览器信息
 */
export function getBrowserInfo() {
  const ua = navigator.userAgent
  const browsers = {
    chrome: /Chrome/.test(ua) && /Google Inc/.test(navigator.vendor),
    firefox: /Firefox/.test(ua),
    safari: /Safari/.test(ua) && /Apple Computer/.test(navigator.vendor),
    edge: /Edge/.test(ua),
    ie: /Trident/.test(ua)
  }
  
  const browser = Object.keys(browsers).find(key => browsers[key]) || 'unknown'
  
  return {
    browser,
    isMobile: isMobile(),
    userAgent: ua
  }
}
