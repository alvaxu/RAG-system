/**
 * 记忆模块API服务
 * 
 * 基于RAG系统V3的API设计规范，提供记忆模块的前端API调用服务
 */

import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建axios实例
const memoryApi = axios.create({
  baseURL: '/api/memory',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
memoryApi.interceptors.request.use(
  (config) => {
    // 添加请求ID
    config.headers['X-Request-ID'] = generateRequestId()
    
    // 添加用户认证信息（如果需要）
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    
    return config
  },
  (error) => {
    console.error('记忆API请求拦截器错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
memoryApi.interceptors.response.use(
  (response) => {
    // 统一成功响应处理
    return response.data
  },
  (error) => {
    // 统一错误处理
    const errorCode = error.response?.headers?.['x-error-code'] || 'UNKNOWN_ERROR'
    const errorMessage = error.response?.data?.message || error.message || '请求失败'
    
    console.error('记忆API响应错误:', {
      code: errorCode,
      message: errorMessage,
      status: error.response?.status,
      data: error.response?.data
    })
    
    // 显示错误消息
    ElMessage.error(`记忆服务错误: ${errorMessage}`)
    
    return Promise.reject({
      code: errorCode,
      message: errorMessage,
      status: error.response?.status,
      details: error.response?.data?.details
    })
  }
)

/**
 * 生成请求ID
 * @returns {string} 请求ID
 */
function generateRequestId() {
  return 'req_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
}

/**
 * 会话管理API
 */
export const sessionApi = {
  /**
   * 创建会话
   * @param {Object} sessionData - 会话数据
   * @param {string} sessionData.user_id - 用户ID
   * @param {Object} sessionData.metadata - 会话元数据
   * @returns {Promise<Object>} 创建的会话信息
   */
  async create(sessionData) {
    try {
      const response = await memoryApi.post('/sessions', sessionData)
      return response
    } catch (error) {
      throw new Error(`创建会话失败: ${error.message}`)
    }
  },

  /**
   * 获取会话信息
   * @param {string} sessionId - 会话ID
   * @returns {Promise<Object>} 会话信息
   */
  async get(sessionId) {
    try {
      const response = await memoryApi.get(`/sessions/${sessionId}`)
      return response
    } catch (error) {
      throw new Error(`获取会话失败: ${error.message}`)
    }
  },

  /**
   * 列出会话
   * @param {Object} params - 查询参数
   * @param {string} params.user_id - 用户ID（可选）
   * @param {string} params.status - 会话状态
   * @param {number} params.limit - 返回数量限制
   * @returns {Promise<Array>} 会话列表
   */
  async list(params = {}) {
    try {
      const response = await memoryApi.get('/sessions', { params })
      return response
    } catch (error) {
      throw new Error(`列出会话失败: ${error.message}`)
    }
  }
}

/**
 * 记忆管理API
 */
export const memoryApi = {
  /**
   * 添加记忆
   * @param {string} sessionId - 会话ID
   * @param {Object} memoryData - 记忆数据
   * @param {string} memoryData.content - 记忆内容
   * @param {string} memoryData.content_type - 内容类型
   * @param {number} memoryData.relevance_score - 相关性分数
   * @param {number} memoryData.importance_score - 重要性分数
   * @param {Object} memoryData.metadata - 记忆元数据
   * @returns {Promise<Object>} 创建的记忆信息
   */
  async add(sessionId, memoryData) {
    try {
      const response = await memoryApi.post(`/sessions/${sessionId}/memories`, memoryData)
      return response
    } catch (error) {
      throw new Error(`添加记忆失败: ${error.message}`)
    }
  },

  /**
   * 查询记忆
   * @param {string} sessionId - 会话ID
   * @param {Object} queryData - 查询数据
   * @param {string} queryData.query_text - 查询文本
   * @param {number} queryData.max_results - 最大返回结果数
   * @param {number} queryData.similarity_threshold - 相似度阈值
   * @param {Array} queryData.content_types - 内容类型过滤
   * @param {Object} queryData.time_range - 时间范围过滤
   * @returns {Promise<Array>} 相关记忆列表
   */
  async query(sessionId, queryData) {
    try {
      const response = await memoryApi.post(`/sessions/${sessionId}/memories/query`, queryData)
      return response
    } catch (error) {
      throw new Error(`查询记忆失败: ${error.message}`)
    }
  }
}

/**
 * 压缩管理API
 */
export const compressionApi = {
  /**
   * 压缩会话记忆
   * @param {string} sessionId - 会话ID
   * @param {Object} compressionData - 压缩数据
   * @param {string} compressionData.strategy - 压缩策略
   * @param {number} compressionData.threshold - 压缩阈值
   * @param {number} compressionData.max_ratio - 最大压缩比例
   * @param {boolean} compressionData.force - 是否强制压缩
   * @returns {Promise<Object>} 压缩结果
   */
  async compress(sessionId, compressionData) {
    try {
      const response = await memoryApi.post(`/sessions/${sessionId}/compress`, compressionData)
      return response
    } catch (error) {
      throw new Error(`压缩记忆失败: ${error.message}`)
    }
  }
}

/**
 * 统计信息API
 */
export const statsApi = {
  /**
   * 获取记忆统计信息
   * @returns {Promise<Object>} 记忆统计信息
   */
  async get() {
    try {
      const response = await memoryApi.get('/stats')
      return response
    } catch (error) {
      throw new Error(`获取记忆统计失败: ${error.message}`)
    }
  }
}

/**
 * 记忆模块工具函数
 */
export const memoryUtils = {
  /**
   * 格式化会话数据
   * @param {Object} session - 会话数据
   * @returns {Object} 格式化后的会话数据
   */
  formatSession(session) {
    return {
      ...session,
      created_at: new Date(session.created_at),
      updated_at: new Date(session.updated_at),
      formatted_created_at: new Date(session.created_at).toLocaleString(),
      formatted_updated_at: new Date(session.updated_at).toLocaleString()
    }
  },

  /**
   * 格式化记忆数据
   * @param {Object} memory - 记忆数据
   * @returns {Object} 格式化后的记忆数据
   */
  formatMemory(memory) {
    return {
      ...memory,
      created_at: new Date(memory.created_at),
      formatted_created_at: new Date(memory.created_at).toLocaleString(),
      relevance_percentage: Math.round(memory.relevance_score * 100),
      importance_percentage: Math.round(memory.importance_score * 100)
    }
  },

  /**
   * 计算记忆相似度颜色
   * @param {number} score - 相似度分数
   * @returns {string} 颜色值
   */
  getSimilarityColor(score) {
    if (score >= 0.8) return '#67c23a' // 绿色
    if (score >= 0.6) return '#e6a23c' // 橙色
    if (score >= 0.4) return '#f56c6c' // 红色
    return '#909399' // 灰色
  },

  /**
   * 计算重要性颜色
   * @param {number} score - 重要性分数
   * @returns {string} 颜色值
   */
  getImportanceColor(score) {
    if (score >= 0.8) return '#409eff' // 蓝色
    if (score >= 0.6) return '#67c23a' // 绿色
    if (score >= 0.4) return '#e6a23c' // 橙色
    return '#909399' // 灰色
  },

  /**
   * 生成记忆摘要
   * @param {string} content - 记忆内容
   * @param {number} maxLength - 最大长度
   * @returns {string} 记忆摘要
   */
  generateSummary(content, maxLength = 100) {
    if (content.length <= maxLength) return content
    return content.substring(0, maxLength) + '...'
  },

  /**
   * 验证会话ID格式
   * @param {string} sessionId - 会话ID
   * @returns {boolean} 是否有效
   */
  isValidSessionId(sessionId) {
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
    return uuidRegex.test(sessionId)
  },

  /**
   * 验证记忆内容
   * @param {Object} memoryData - 记忆数据
   * @returns {Object} 验证结果
   */
  validateMemoryData(memoryData) {
    const errors = []
    
    if (!memoryData.content || memoryData.content.trim().length === 0) {
      errors.push('记忆内容不能为空')
    }
    
    if (memoryData.content && memoryData.content.length > 10000) {
      errors.push('记忆内容不能超过10000个字符')
    }
    
    if (memoryData.relevance_score < 0 || memoryData.relevance_score > 1) {
      errors.push('相关性分数必须在0-1之间')
    }
    
    if (memoryData.importance_score < 0 || memoryData.importance_score > 1) {
      errors.push('重要性分数必须在0-1之间')
    }
    
    const validContentTypes = ['text', 'image', 'table']
    if (memoryData.content_type && !validContentTypes.includes(memoryData.content_type)) {
      errors.push('内容类型必须是text、image或table之一')
    }
    
    return {
      isValid: errors.length === 0,
      errors
    }
  }
}

export default memoryApi
