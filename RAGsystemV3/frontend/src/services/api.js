import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建axios实例
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加认证token等
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('API请求错误:', error)
    
    if (error.response) {
      const { status, data } = error.response
      let message = '请求失败'
      
      switch (status) {
        case 400:
          message = data.message || '请求参数错误'
          break
        case 401:
          message = '未授权，请重新登录'
          break
        case 403:
          message = '权限不足'
          break
        case 404:
          message = '请求的资源不存在'
          break
        case 500:
          message = '服务器内部错误'
          break
        default:
          message = data.message || `请求失败 (${status})`
      }
      
      ElMessage.error(message)
    } else if (error.request) {
      ElMessage.error('网络连接失败，请检查网络')
    } else {
      ElMessage.error('请求配置错误')
    }
    
    return Promise.reject(error)
  }
)

// RAG API服务类
class RAGAPIService {
  /**
   * 发送智能查询
   * @param {Object} queryData - 查询数据
   * @returns {Promise} API响应
   */
  async sendQuery(queryData) {
    try {
      const response = await api.post('/api/v3/rag/query', queryData)
      return response
    } catch (error) {
      throw error
    }
  }

  /**
   * 发送文本查询
   * @param {string} query - 查询文本
   * @param {Object} options - 查询选项
   * @returns {Promise} API响应
   */
  async sendTextQuery(query, options = {}) {
    const queryData = {
      query,
      query_type: 'text',
      max_results: options.maxResults || 10,
      similarity_threshold: options.similarityThreshold || 0.5,
      ...options
    }
    return this.sendQuery(queryData)
  }

  /**
   * 发送图片查询
   * @param {string} query - 查询文本
   * @param {Object} options - 查询选项
   * @returns {Promise} API响应
   */
  async sendImageQuery(query, options = {}) {
    const queryData = {
      query,
      query_type: 'image',
      max_results: options.maxResults || 10,
      similarity_threshold: options.similarityThreshold || 0.5,
      ...options
    }
    return this.sendQuery(queryData)
  }

  /**
   * 发送表格查询
   * @param {string} query - 查询文本
   * @param {Object} options - 查询选项
   * @returns {Promise} API响应
   */
  async sendTableQuery(query, options = {}) {
    const queryData = {
      query,
      query_type: 'table',
      max_results: options.maxResults || 10,
      similarity_threshold: options.similarityThreshold || 0.5,
      ...options
    }
    return this.sendQuery(queryData)
  }

  /**
   * 发送混合查询
   * @param {string} query - 查询文本
   * @param {Object} options - 查询选项
   * @returns {Promise} API响应
   */
  async sendHybridQuery(query, options = {}) {
    const queryData = {
      query,
      query_type: 'hybrid',
      max_results: options.maxResults || 10,
      similarity_threshold: options.similarityThreshold || 0.5,
      ...options
    }
    return this.sendQuery(queryData)
  }

  /**
   * 发送智能查询（自动判断类型）
   * @param {string} query - 查询文本
   * @param {Object} options - 查询选项
   * @returns {Promise} API响应
   */
  async sendSmartQuery(query, options = {}) {
    const queryData = {
      query,
      query_type: 'smart',
      max_results: options.maxResults || 10,
      similarity_threshold: options.similarityThreshold || 0.5,
      ...options
    }
    return this.sendQuery(queryData)
  }

  /**
   * 获取系统状态
   * @returns {Promise} API响应
   */
  async getSystemStatus() {
    try {
      const response = await api.get('/api/v3/rag/status')
      return response
    } catch (error) {
      throw error
    }
  }

  /**
   * 获取配置信息
   * @returns {Promise} API响应
   */
  async getConfig() {
    try {
      const response = await api.get('/api/v3/rag/config')
      return response
    } catch (error) {
      throw error
    }
  }

  /**
   * 健康检查
   * @returns {Promise} API响应
   */
  async healthCheck() {
    try {
      const response = await api.get('/api/v3/rag/health')
      return response
    } catch (error) {
      throw error
    }
  }
}

// 创建API服务实例
const ragAPI = new RAGAPIService()

export default ragAPI
export { RAGAPIService }
