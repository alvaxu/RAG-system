/**
程序说明：

## 1. 元数据处理工具
- 处理从M15元数据管理模块获取的详细信息
- 提取文档名、页码、表格标题、图片标题等元数据
- 过滤掉chunk-id等技术标识

## 2. 与其他版本的不同点
- 新增了表格标题和图片标题的提取
- 隐藏了chunk-id等技术标识
- 优化了元数据的处理逻辑
*/

/**
 * 处理来源信息，提取完整的元数据
 * :param sources: 原始来源信息数组
 * :return: 处理后的来源信息数组
 */
export function processSourceMetadata(sources) {
  if (!sources || !Array.isArray(sources)) {
    return []
  }

  return sources.map(source => {
    const processedSource = { ...source }
    
    // 提取文档信息
    processedSource.document_name = extractDocumentName(source)
    processedSource.page_number = extractPageNumber(source)
    
    // 提取表格信息
    if (source.content_type === 'table') {
      processedSource.table_title = extractTableTitle(source)
    }
    
    // 提取图片信息
    if (source.content_type === 'image') {
      processedSource.image_caption = extractImageCaption(source)
    }
    
    // 移除技术标识
    processedSource = removeTechnicalIdentifiers(processedSource)
    
    return processedSource
  })
}

/**
 * 提取文档名称
 * :param source: 来源信息对象
 * :return: 文档名称
 */
function extractDocumentName(source) {
  // 优先使用document_name字段
  if (source.document_name) {
    return source.document_name
  }
  
  // 从metadata中提取
  if (source.metadata && source.metadata.document_name) {
    return source.metadata.document_name
  }
  
  // 从file_path中提取文件名
  if (source.file_path) {
    const fileName = source.file_path.split('/').pop()
    return fileName.replace(/\.[^/.]+$/, '') // 移除文件扩展名
  }
  
  return '未知文档'
}

/**
 * 提取页码信息
 * :param source: 来源信息对象
 * :return: 页码
 */
function extractPageNumber(source) {
  // 优先使用page_number字段
  if (source.page_number && source.page_number > 0) {
    return source.page_number
  }
  
  // 从metadata中提取
  if (source.metadata && source.metadata.page_number) {
    return source.metadata.page_number
  }
  
  // 从chunk_id中提取页码（如果包含）
  if (source.chunk_id) {
    const pageMatch = source.chunk_id.match(/page[_-]?(\d+)/i)
    if (pageMatch) {
      return parseInt(pageMatch[1])
    }
  }
  
  return 0
}

/**
 * 提取表格标题
 * :param source: 来源信息对象
 * :return: 表格标题
 */
function extractTableTitle(source) {
  // 优先使用table.title字段
  if (source.table && source.table.title) {
    return source.table.title
  }
  
  // 从metadata中提取
  if (source.metadata && source.metadata.table_title) {
    return source.metadata.table_title
  }
  
  // 从content_preview中提取表格标题
  if (source.content_preview) {
    const titleMatch = source.content_preview.match(/^(.+?)(?:\n|$)/)
    if (titleMatch && titleMatch[1].length < 50) {
      return titleMatch[1].trim()
    }
  }
  
  return null
}

/**
 * 提取图片标题/说明
 * :param source: 来源信息对象
 * :return: 图片标题/说明
 */
function extractImageCaption(source) {
  // 优先使用image.caption字段
  if (source.image && source.image.caption) {
    return source.image.caption
  }
  
  // 从metadata中提取
  if (source.metadata && source.metadata.image_caption) {
    return source.metadata.image_caption
  }
  
  // 从alt_text中提取
  if (source.alt_text) {
    return source.alt_text
  }
  
  // 从file_path中提取文件名作为标题
  if (source.file_path) {
    const fileName = source.file_path.split('/').pop()
    return fileName.replace(/\.[^/.]+$/, '') // 移除文件扩展名
  }
  
  return null
}

/**
 * 移除技术标识
 * :param source: 来源信息对象
 * :return: 处理后的来源信息对象
 */
function removeTechnicalIdentifiers(source) {
  const processedSource = { ...source }
  
  // 移除chunk_id等技术标识
  delete processedSource.chunk_id
  delete processedSource.vector_id
  delete processedSource.embedding_id
  
  // 移除内部技术字段
  delete processedSource.internal_id
  delete processedSource.technical_metadata
  
  return processedSource
}

/**
 * 格式化来源信息用于显示
 * :param source: 来源信息对象
 * :return: 格式化后的显示信息
 */
export function formatSourceForDisplay(source) {
  const parts = []
  
  // 添加文档名
  if (source.document_name) {
    parts.push(source.document_name)
  }
  
  // 添加页码
  if (source.page_number > 0) {
    parts.push(`第${source.page_number}页`)
  }
  
  // 添加表格标题
  if (source.table_title) {
    parts.push(`《${source.table_title}》`)
  }
  
  // 添加图片标题
  if (source.image_caption) {
    parts.push(source.image_caption)
  }
  
  return parts.join(' - ')
}

/**
 * 验证元数据完整性
 * :param source: 来源信息对象
 * :return: 验证结果
 */
export function validateSourceMetadata(source) {
  const issues = []
  
  // 检查必要字段
  if (!source.document_name) {
    issues.push('缺少文档名称')
  }
  
  if (source.content_type === 'table' && !source.table_title) {
    issues.push('表格缺少标题')
  }
  
  if (source.content_type === 'image' && !source.image_caption) {
    issues.push('图片缺少标题/说明')
  }
  
  return {
    isValid: issues.length === 0,
    issues: issues
  }
}

/**
 * 获取来源信息的摘要
 * :param sources: 来源信息数组
 * :return: 摘要信息
 */
export function getSourceSummary(sources) {
  if (!sources || sources.length === 0) {
    return {
      total: 0,
      byType: {},
      documents: new Set()
    }
  }
  
  const summary = {
    total: sources.length,
    byType: {},
    documents: new Set()
  }
  
  sources.forEach(source => {
    // 统计类型
    const type = source.content_type || 'unknown'
    summary.byType[type] = (summary.byType[type] || 0) + 1
    
    // 统计文档
    if (source.document_name) {
      summary.documents.add(source.document_name)
    }
  })
  
  return {
    ...summary,
    documentCount: summary.documents.size
  }
}
