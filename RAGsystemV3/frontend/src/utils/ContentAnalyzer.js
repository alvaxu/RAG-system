/**
程序说明：

## 1. 内容分析器（简化版本）
- 实现智能查询的展示逻辑
- 根据后端返回的实际查询类型直接匹配展示模式
- 实现混合查询的内容分析功能

## 2. 与其他版本的不同点
- 新增了智能查询展示逻辑
- 使用简化的内容分析算法
- 智能查询无需前端分析，直接使用后端结果
*/

/**
 * 内容分析器类（简化版本）
 */
export class ContentAnalyzer {
  constructor() {
    this.config = {
      simplifiedAnalysis: true,
      keywordThreshold: 0.3,
      contentThreshold: 0.5
    }
  }

  /**
   * 处理智能查询的展示逻辑
   * :param queryResult: 查询结果
   * :return: 推荐的展示模式
   */
  processSmartQueryDisplay(queryResult) {
    // 智能查询无需前端分析，直接使用后端返回的实际查询类型
    if (!queryResult || !queryResult.actualQueryType) {
      return 'auto-detect'
    }

    // 根据后端返回的实际查询类型直接匹配展示模式
    const modeMap = {
      'text': 'text-focused',
      'image': 'image-focused',
      'table': 'table-focused',
      'hybrid': 'hybrid-layout'
    }

    return modeMap[queryResult.actualQueryType] || 'auto-detect'
  }

  /**
   * 分析混合查询的LLM答案内容
   * :param llmAnswer: LLM答案内容
   * :return: 推荐的展示模式
   */
  analyzeHybridQueryContent(llmAnswer) {
    if (!this.config.simplifiedAnalysis) {
      return 'hybrid-layout'
    }

    if (!llmAnswer || typeof llmAnswer !== 'string') {
      return 'hybrid-layout'
    }

    // 简化的内容分析
    const contentScores = this.calculateContentScores(llmAnswer)
    
    // 根据内容特征确定展示模式
    if (contentScores.hasTable && contentScores.tableScore > this.config.contentThreshold) {
      return 'table-focused'
    } else if (contentScores.hasImage && contentScores.imageScore > this.config.contentThreshold) {
      return 'image-focused'
    } else if (contentScores.hasText && contentScores.textScore > this.config.contentThreshold) {
      return 'text-focused'
    } else {
      return 'hybrid-layout'
    }
  }

  /**
   * 计算内容分数（简化版本）
   * :param content: 内容文本
   * :return: 内容分数对象
   */
  calculateContentScores(content) {
    const scores = {
      hasText: false,
      hasImage: false,
      hasTable: false,
      textScore: 0,
      imageScore: 0,
      tableScore: 0
    }

    if (!content) {
      return scores
    }

    const contentLower = content.toLowerCase()

    // 简化的关键词匹配
    const textKeywords = ['文档', '文本', '内容', '描述', '说明', '分析', '总结']
    const imageKeywords = ['图片', '图像', '图表', '照片', '图', '可视化', '展示']
    const tableKeywords = ['表格', '数据', '统计', '列表', '表', '数字', '指标']

    // 计算文本分数
    scores.textScore = this.calculateKeywordScore(contentLower, textKeywords)
    scores.hasText = scores.textScore > this.config.keywordThreshold

    // 计算图片分数
    scores.imageScore = this.calculateKeywordScore(contentLower, imageKeywords)
    scores.hasImage = scores.imageScore > this.config.keywordThreshold

    // 计算表格分数
    scores.tableScore = this.calculateKeywordScore(contentLower, tableKeywords)
    scores.hasTable = scores.tableScore > this.config.keywordThreshold

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
      score += 0.2
    }

    return Math.min(score, 1.0)
  }

  /**
   * 检测内容类型
   * :param content: 内容对象
   * :return: 内容类型
   */
  detectContentType(content) {
    if (!content) {
      return 'unknown'
    }

    // 简化的类型检测
    if (content.content_type) {
      return content.content_type
    }

    if (content.type) {
      return content.type
    }

    // 基于内容特征检测
    const contentText = JSON.stringify(content).toLowerCase()
    
    if (contentText.includes('table') || contentText.includes('表格')) {
      return 'table'
    } else if (contentText.includes('image') || contentText.includes('图片')) {
      return 'image'
    } else {
      return 'text'
    }
  }

  /**
   * 获取内容摘要
   * :param content: 内容对象
   * :param maxLength: 最大长度
   * :return: 内容摘要
   */
  getContentSummary(content, maxLength = 200) {
    if (!content) {
      return ''
    }

    let summary = ''
    
    if (typeof content === 'string') {
      summary = content
    } else if (content.content_preview) {
      summary = content.content_preview
    } else if (content.text) {
      summary = content.text
    } else {
      summary = JSON.stringify(content)
    }

    if (summary.length <= maxLength) {
      return summary
    }

    return summary.substring(0, maxLength) + '...'
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
export const contentAnalyzer = new ContentAnalyzer()

// 导出工具函数
export function processSmartQueryDisplay(queryResult) {
  return contentAnalyzer.processSmartQueryDisplay(queryResult)
}

export function analyzeHybridQueryContent(llmAnswer) {
  return contentAnalyzer.analyzeHybridQueryContent(llmAnswer)
}

export function detectContentType(content) {
  return contentAnalyzer.detectContentType(content)
}

export function getContentSummary(content, maxLength) {
  return contentAnalyzer.getContentSummary(content, maxLength)
}
