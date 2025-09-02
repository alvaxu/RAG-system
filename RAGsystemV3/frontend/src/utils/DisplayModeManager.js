/**
程序说明：

## 1. 展示模式管理器
- 管理展示模式的配置和逻辑
- 实现简化的内容分析算法
- 提供展示模式选择的基础规则

## 2. 与其他版本的不同点
- 新增了展示模式管理功能
- 使用简化的实现策略
- 先实现基础规则匹配，后续可优化
*/

/**
 * 展示模式管理器类
 */
export class DisplayModeManager {
  constructor() {
    this.config = {
      enabled: true,
      defaultMode: 'auto-detect',
      autoSelectionRules: {
        textThreshold: 0.7,
        imageThreshold: 0.6,
        tableThreshold: 0.5
      },
      fallbackMode: 'text-focused',
      simplifiedAnalysis: true
    }
  }

  /**
   * 根据查询类型获取推荐的展示模式
   * :param queryType: 查询类型
   * :return: 推荐的展示模式
   */
  getRecommendedMode(queryType) {
    const modeMap = {
      'text': 'text-focused',
      'image': 'image-focused',
      'table': 'table-focused',
      'hybrid': 'hybrid-layout',
      'smart': 'auto-detect'
    }
    
    return modeMap[queryType] || this.config.defaultMode
  }

  /**
   * 根据内容特征分析展示模式（简化版本）
   * :param content: 内容对象
   * :return: 推荐的展示模式
   */
  analyzeContentForDisplayMode(content) {
    if (!this.config.simplifiedAnalysis) {
      return this.config.fallbackMode
    }

    // 简化的内容分析
    const scores = this.calculateContentScores(content)
    
    // 根据分数选择展示模式
    if (scores.table > this.config.autoSelectionRules.tableThreshold) {
      return 'table-focused'
    } else if (scores.image > this.config.autoSelectionRules.imageThreshold) {
      return 'image-focused'
    } else if (scores.text > this.config.autoSelectionRules.textThreshold) {
      return 'text-focused'
    } else {
      return 'hybrid-layout'
    }
  }

  /**
   * 计算内容分数（简化版本）
   * :param content: 内容对象
   * :return: 各类型内容的分数
   */
  calculateContentScores(content) {
    const scores = {
      text: 0,
      image: 0,
      table: 0
    }

    if (!content) {
      return scores
    }

    // 简化的关键词匹配
    const textKeywords = ['文档', '文本', '内容', '描述', '说明']
    const imageKeywords = ['图片', '图像', '图表', '照片', '图']
    const tableKeywords = ['表格', '数据', '统计', '列表', '表']

    const contentText = JSON.stringify(content).toLowerCase()

    // 计算文本分数
    scores.text = this.calculateKeywordScore(contentText, textKeywords)
    
    // 计算图片分数
    scores.image = this.calculateKeywordScore(contentText, imageKeywords)
    
    // 计算表格分数
    scores.table = this.calculateKeywordScore(contentText, tableKeywords)

    return scores
  }

  /**
   * 计算关键词匹配分数
   * :param text: 文本内容
   * :param keywords: 关键词数组
   * :return: 匹配分数
   */
  calculateKeywordScore(text, keywords) {
    let score = 0
    let matchCount = 0

    keywords.forEach(keyword => {
      if (text.includes(keyword)) {
        matchCount++
        score += 1 / keywords.length
      }
    })

    // 如果有匹配，给予基础分数
    if (matchCount > 0) {
      score += 0.3
    }

    return Math.min(score, 1.0)
  }

  /**
   * 验证展示模式是否适用于查询类型
   * :param mode: 展示模式
   * :param queryType: 查询类型
   * :return: 是否适用
   */
  isModeCompatible(mode, queryType) {
    const compatibility = {
      'text-focused': ['text', 'smart'],
      'image-focused': ['image'],
      'table-focused': ['table'],
      'hybrid-layout': ['hybrid'],
      'auto-detect': ['smart', 'all']
    }

    return compatibility[mode]?.includes(queryType) || false
  }

  /**
   * 获取展示模式配置
   * :param mode: 展示模式
   * :return: 模式配置
   */
  getModeConfig(mode) {
    const configs = {
      'text-focused': {
        name: '文本优先',
        description: '以文本内容为主要展示方式',
        icon: 'Document',
        priority: 1
      },
      'image-focused': {
        name: '图片优先',
        description: '以图片内容为主要展示方式',
        icon: 'Picture',
        priority: 2
      },
      'table-focused': {
        name: '表格优先',
        description: '以表格内容为主要展示方式',
        icon: 'Grid',
        priority: 3
      },
      'hybrid-layout': {
        name: '混合布局',
        description: '综合展示多种内容类型',
        icon: 'Connection',
        priority: 4
      },
      'auto-detect': {
        name: '智能选择',
        description: '根据内容自动选择最佳展示模式',
        icon: 'MagicStick',
        priority: 0
      }
    }

    return configs[mode] || configs['auto-detect']
  }

  /**
   * 更新配置
   * :param newConfig: 新配置
   */
  updateConfig(newConfig) {
    this.config = { ...this.config, ...newConfig }
  }

  /**
   * 获取当前配置
   * :return: 当前配置
   */
  getConfig() {
    return { ...this.config }
  }
}

// 创建全局实例
export const displayModeManager = new DisplayModeManager()

// 导出工具函数
export function getRecommendedDisplayMode(queryType) {
  return displayModeManager.getRecommendedMode(queryType)
}

export function analyzeContentForDisplayMode(content) {
  return displayModeManager.analyzeContentForDisplayMode(content)
}

export function isDisplayModeCompatible(mode, queryType) {
  return displayModeManager.isModeCompatible(mode, queryType)
}
