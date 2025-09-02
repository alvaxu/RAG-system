/**
程序说明：

## 1. 配置管理器
- 实现前端默认配置策略
- 添加后端配置获取API
- 实现配置降级机制

## 2. 与其他版本的不同点
- 新增了配置管理功能
- 前端默认配置为主，后端API作为增强
- 配置获取失败时自动使用前端默认配置
*/

/**
 * 配置管理器类
 */
export class ConfigManager {
  constructor() {
    this.config = {
      // 前端默认配置
      displayMode: {
        enabled: true,
        defaultMode: 'auto-detect',
        autoSelectionRules: {
          textThreshold: 0.7,
          imageThreshold: 0.6,
          tableThreshold: 0.5
        },
        fallbackMode: 'text-focused',
        simplifiedAnalysis: true
      },
      presetQuestions: {
        enabled: true,
        defaultLimit: 10,
        autoLoad: true
      },
      sourceDisplay: {
        enabled: true,
        showChunkId: false,
        showTechnicalInfo: false
      }
    }
    
    this.backendConfig = null
    this.lastFetchTime = null
    this.cacheDuration = 5 * 60 * 1000 // 5分钟缓存
  }

  /**
   * 获取展示模式配置
   * :param forceRefresh: 是否强制刷新
   * :return: 展示模式配置
   */
  async getDisplayModeConfig(forceRefresh = false) {
    try {
      // 检查缓存
      if (!forceRefresh && this.isConfigCacheValid()) {
        return this.mergeConfigs('displayMode')
      }

      // 尝试从后端获取配置
      const backendConfig = await this.fetchBackendConfig()
      if (backendConfig) {
        this.backendConfig = backendConfig
        this.lastFetchTime = Date.now()
        return this.mergeConfigs('displayMode')
      }
    } catch (error) {
      console.warn('获取后端配置失败，使用前端默认配置:', error)
    }

    // 降级到前端默认配置
    return this.config.displayMode
  }

  /**
   * 获取预设问题配置
   * :return: 预设问题配置
   */
  getPresetQuestionsConfig() {
    return this.config.presetQuestions
  }

  /**
   * 获取来源显示配置
   * :return: 来源显示配置
   */
  getSourceDisplayConfig() {
    return this.config.sourceDisplay
  }

  /**
   * 获取完整配置
   * :return: 完整配置对象
   */
  getFullConfig() {
    return {
      ...this.config,
      backendConfig: this.backendConfig,
      lastFetchTime: this.lastFetchTime
    }
  }

  /**
   * 更新配置
   * :param section: 配置节
   * :param newConfig: 新配置
   */
  updateConfig(section, newConfig) {
    if (this.config[section]) {
      this.config[section] = { ...this.config[section], ...newConfig }
    }
  }

  /**
   * 重置配置到默认值
   */
  resetConfig() {
    this.config = {
      displayMode: {
        enabled: true,
        defaultMode: 'auto-detect',
        autoSelectionRules: {
          textThreshold: 0.7,
          imageThreshold: 0.6,
          tableThreshold: 0.5
        },
        fallbackMode: 'text-focused',
        simplifiedAnalysis: true
      },
      presetQuestions: {
        enabled: true,
        defaultLimit: 10,
        autoLoad: true
      },
      sourceDisplay: {
        enabled: true,
        showChunkId: false,
        showTechnicalInfo: false
      }
    }
    this.backendConfig = null
    this.lastFetchTime = null
  }

  /**
   * 从后端获取配置
   * :return: 后端配置
   */
  async fetchBackendConfig() {
    try {
      // 这里应该调用实际的API
      // const response = await ragAPI.getDisplayModeConfig()
      // return response.config
      
      // 模拟API调用
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve({
            displayMode: {
              enabled: true,
              defaultMode: 'auto-detect',
              autoSelectionRules: {
                textThreshold: 0.8,
                imageThreshold: 0.7,
                tableThreshold: 0.6
              },
              fallbackMode: 'text-focused',
              simplifiedAnalysis: true
            }
          })
        }, 100)
      })
    } catch (error) {
      console.error('获取后端配置失败:', error)
      return null
    }
  }

  /**
   * 检查配置缓存是否有效
   * :return: 缓存是否有效
   */
  isConfigCacheValid() {
    if (!this.lastFetchTime || !this.backendConfig) {
      return false
    }
    
    const now = Date.now()
    return (now - this.lastFetchTime) < this.cacheDuration
  }

  /**
   * 合并前端和后端配置
   * :param section: 配置节
   * :return: 合并后的配置
   */
  mergeConfigs(section) {
    const frontendConfig = this.config[section]
    const backendConfig = this.backendConfig?.[section]
    
    if (!backendConfig) {
      return frontendConfig
    }
    
    // 合并配置，后端配置优先
    return {
      ...frontendConfig,
      ...backendConfig
    }
  }

  /**
   * 验证配置有效性
   * :param config: 配置对象
   * :return: 验证结果
   */
  validateConfig(config) {
    const errors = []
    
    if (!config) {
      errors.push('配置不能为空')
      return { isValid: false, errors }
    }
    
    // 验证展示模式配置
    if (config.displayMode) {
      const dm = config.displayMode
      if (dm.enabled && typeof dm.enabled !== 'boolean') {
        errors.push('displayMode.enabled 必须是布尔值')
      }
      if (dm.defaultMode && typeof dm.defaultMode !== 'string') {
        errors.push('displayMode.defaultMode 必须是字符串')
      }
    }
    
    return {
      isValid: errors.length === 0,
      errors
    }
  }

  /**
   * 保存配置到本地存储
   */
  saveConfigToStorage() {
    try {
      const configToSave = {
        ...this.config,
        lastSaved: Date.now()
      }
      localStorage.setItem('rag_system_config', JSON.stringify(configToSave))
    } catch (error) {
      console.error('保存配置到本地存储失败:', error)
    }
  }

  /**
   * 从本地存储加载配置
   */
  loadConfigFromStorage() {
    try {
      const savedConfig = localStorage.getItem('rag_system_config')
      if (savedConfig) {
        const parsedConfig = JSON.parse(savedConfig)
        this.config = { ...this.config, ...parsedConfig }
        return true
      }
    } catch (error) {
      console.error('从本地存储加载配置失败:', error)
    }
    return false
  }
}

// 创建全局实例
export const configManager = new ConfigManager()

// 导出工具函数
export async function getDisplayModeConfig(forceRefresh = false) {
  return await configManager.getDisplayModeConfig(forceRefresh)
}

export function getPresetQuestionsConfig() {
  return configManager.getPresetQuestionsConfig()
}

export function getSourceDisplayConfig() {
  return configManager.getSourceDisplayConfig()
}

export function updateConfig(section, newConfig) {
  configManager.updateConfig(section, newConfig)
}

export function resetConfig() {
  configManager.resetConfig()
}
