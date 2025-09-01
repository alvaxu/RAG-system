/**
 * 常量定义
 */

// 查询类型
export const QUERY_TYPES = {
  TEXT: 'text',
  IMAGE: 'image',
  TABLE: 'table',
  HYBRID: 'hybrid',
  SMART: 'smart'
}

// 查询类型配置
export const QUERY_TYPE_CONFIG = {
  [QUERY_TYPES.TEXT]: {
    label: '文本查询',
    icon: 'Document',
    description: '查询文本内容',
    color: '#409EFF'
  },
  [QUERY_TYPES.IMAGE]: {
    label: '图片查询',
    icon: 'Picture',
    description: '查询图片内容',
    color: '#67C23A'
  },
  [QUERY_TYPES.TABLE]: {
    label: '表格查询',
    icon: 'Grid',
    description: '查询表格数据',
    color: '#E6A23C'
  },
  [QUERY_TYPES.HYBRID]: {
    label: '混合查询',
    icon: 'Connection',
    description: '跨类型内容查询',
    color: '#F56C6C'
  },
  [QUERY_TYPES.SMART]: {
    label: '智能查询',
    icon: 'MagicStick',
    description: '系统自动判断查询类型',
    color: '#909399'
  }
}

// 相似度分数等级
export const SIMILARITY_LEVELS = {
  HIGH: { min: 0.8, max: 1.0, label: '高', color: '#67C23A' },
  MEDIUM: { min: 0.6, max: 0.8, label: '中', color: '#E6A23C' },
  LOW: { min: 0.4, max: 0.6, label: '低', color: '#F56C6C' },
  VERY_LOW: { min: 0.0, max: 0.4, label: '很低', color: '#909399' }
}

// 置信度等级
export const CONFIDENCE_LEVELS = {
  HIGH: { label: '高', color: '#67C23A', icon: 'SuccessFilled' },
  MEDIUM: { label: '中', color: '#E6A23C', icon: 'WarningFilled' },
  LOW: { label: '低', color: '#F56C6C', icon: 'CircleCloseFilled' }
}

// 默认配置
export const DEFAULT_CONFIG = {
  MAX_RESULTS: 10,
  SIMILARITY_THRESHOLD: 0.5,
  QUERY_TIMEOUT: 30000,
  MAX_QUERY_LENGTH: 1000,
  MIN_QUERY_LENGTH: 2
}

// API端点
export const API_ENDPOINTS = {
  QUERY: '/api/v3/rag/query',
  STATUS: '/api/v3/rag/status',
  CONFIG: '/api/v3/rag/config',
  HEALTH: '/api/v3/rag/health'
}

// 本地存储键名
export const STORAGE_KEYS = {
  THEME: 'rag_theme',
  QUERY_HISTORY: 'rag_query_history',
  USER_PREFERENCES: 'rag_user_preferences',
  CHAT_HISTORY: 'rag_chat_history'
}

// 主题配置
export const THEMES = {
  LIGHT: 'light',
  DARK: 'dark'
}

// 语言配置
export const LANGUAGES = {
  ZH_CN: 'zh-CN',
  EN_US: 'en-US'
}

// 消息类型
export const MESSAGE_TYPES = {
  USER: 'user',
  ASSISTANT: 'assistant',
  SYSTEM: 'system',
  ERROR: 'error'
}

// 加载状态
export const LOADING_STATES = {
  IDLE: 'idle',
  LOADING: 'loading',
  SUCCESS: 'success',
  ERROR: 'error'
}

// 错误类型
export const ERROR_TYPES = {
  NETWORK: 'network',
  API: 'api',
  VALIDATION: 'validation',
  UNKNOWN: 'unknown'
}

// 响应式断点
export const BREAKPOINTS = {
  XS: 480,
  SM: 768,
  MD: 992,
  LG: 1200,
  XL: 1920
}

// 动画持续时间
export const ANIMATION_DURATION = {
  FAST: 150,
  NORMAL: 300,
  SLOW: 500
}

// 分页配置
export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 10,
  PAGE_SIZE_OPTIONS: [10, 20, 50, 100]
}

// 搜索建议
export const SEARCH_SUGGESTIONS = [
  '人工智能',
  '机器学习',
  '深度学习',
  '自然语言处理',
  '计算机视觉',
  '数据分析',
  '算法优化',
  '技术文档'
]

// 快捷键配置
export const SHORTCUTS = {
  SEND_QUERY: 'Enter',
  NEW_QUERY: 'Ctrl+N',
  CLEAR_HISTORY: 'Ctrl+L',
  TOGGLE_THEME: 'Ctrl+T',
  FOCUS_INPUT: 'Ctrl+K'
}

// 文件类型
export const FILE_TYPES = {
  PDF: 'pdf',
  DOC: 'doc',
  DOCX: 'docx',
  TXT: 'txt',
  MD: 'md',
  HTML: 'html',
  JSON: 'json',
  CSV: 'csv',
  XLSX: 'xlsx',
  PNG: 'png',
  JPG: 'jpg',
  JPEG: 'jpeg',
  GIF: 'gif',
  SVG: 'svg'
}

// 内容类型
export const CONTENT_TYPES = {
  TEXT: 'text',
  IMAGE: 'image',
  TABLE: 'table',
  DOCUMENT: 'document',
  CODE: 'code',
  UNKNOWN: 'unknown'
}

// 排序选项
export const SORT_OPTIONS = {
  RELEVANCE: { key: 'relevance', label: '相关性' },
  TIME: { key: 'time', label: '时间' },
  TYPE: { key: 'type', label: '类型' },
  SCORE: { key: 'score', label: '分数' }
}

// 过滤选项
export const FILTER_OPTIONS = {
  ALL: { key: 'all', label: '全部' },
  TEXT: { key: 'text', label: '文本' },
  IMAGE: { key: 'image', label: '图片' },
  TABLE: { key: 'table', label: '表格' },
  DOCUMENT: { key: 'document', label: '文档' }
}
