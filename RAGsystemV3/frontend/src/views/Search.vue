<template>
  <div class="search-container">
    <!-- 搜索头部 -->
    <div class="search-header">
      <div class="header-content">
        <div class="header-left">
          <el-icon class="header-icon"><Search /></el-icon>
          <h1>内容搜索</h1>
        </div>
        <div class="header-right">
          <el-button @click="clearResults" size="small" plain>
            <el-icon><Delete /></el-icon>
            清空结果
          </el-button>
        </div>
      </div>
    </div>

    <!-- 搜索输入区域 -->
    <div class="search-input-section">
      <div class="input-container">
        <div class="search-input-wrapper">
          <el-input
            v-model="searchQuery"
            placeholder="输入搜索关键词..."
            size="large"
            @keydown.enter="performSearch"
            :loading="isSearching"
            class="search-input"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
            <template #append>
              <el-button 
                type="primary" 
                @click="performSearch"
                :loading="isSearching"
                :disabled="!searchQuery.trim()"
              >
                搜索
              </el-button>
            </template>
          </el-input>
        </div>
        
        <!-- 搜索选项 -->
        <div class="search-options">
          <div class="option-group">
            <label class="option-label">内容类型:</label>
            <el-select v-model="selectedContentType" placeholder="选择内容类型" size="small">
              <el-option
                v-for="option in contentTypeOptions"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              >
                <el-icon><component :is="option.icon" /></el-icon>
                <span style="margin-left: 8px">{{ option.label }}</span>
              </el-option>
            </el-select>
          </div>
          
          <div class="option-group">
            <label class="option-label">结果数量:</label>
            <el-select v-model="maxResults" size="small">
              <el-option label="10" :value="10" />
              <el-option label="20" :value="20" />
              <el-option label="50" :value="50" />
              <el-option label="100" :value="100" />
            </el-select>
          </div>
          
          <div class="option-group">
            <label class="option-label">相似度阈值:</label>
            <div class="threshold-control">
              <el-slider
                v-model="similarityThreshold"
                :min="0"
                :max="1"
                :step="0.1"
                :format-tooltip="formatThresholdTooltip"
                style="width: 120px"
              />
              <span class="threshold-value">{{ similarityThreshold }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 搜索结果区域 -->
    <div class="search-results-section" v-if="hasSearched">
      <!-- 结果统计 -->
      <div class="results-header">
        <div class="results-info">
          <h2>搜索结果</h2>
          <div class="results-stats">
            <span>找到 {{ searchResults.length }} 个结果</span>
            <span v-if="searchTime > 0">搜索耗时: {{ searchTime }}ms</span>
            <span v-if="averageSimilarity > 0">平均相似度: {{ formatSimilarityScore(averageSimilarity) }}</span>
          </div>
        </div>
        <div class="results-actions">
          <el-button-group>
            <el-button 
              :type="sortBy === 'relevance' ? 'primary' : ''"
              @click="sortResults('relevance')"
              size="small"
            >
              按相关性排序
            </el-button>
            <el-button 
              :type="sortBy === 'score' ? 'primary' : ''"
              @click="sortResults('score')"
              size="small"
            >
              按分数排序
            </el-button>
            <el-button 
              :type="sortBy === 'type' ? 'primary' : ''"
              @click="sortResults('type')"
              size="small"
            >
              按类型排序
            </el-button>
          </el-button-group>
        </div>
      </div>

      <!-- 结果列表 -->
      <div class="results-list" v-if="searchResults.length > 0">
        <div 
          v-for="(result, index) in paginatedResults" 
          :key="result.chunk_id"
          class="result-item"
          :class="`result-${result.chunk_type}`"
        >
          <div class="result-header">
            <div class="result-meta">
              <span class="result-rank">#{{ (currentPage - 1) * pageSize + index + 1 }}</span>
              <el-tag 
                :type="getContentTypeTag(result.chunk_type)"
                size="small"
                class="result-type-tag"
              >
                <el-icon><component :is="getContentTypeIcon(result.chunk_type)" /></el-icon>
                {{ getContentTypeLabel(result.chunk_type) }}
              </el-tag>
              <span class="result-document">{{ result.document_name }}</span>
              <span v-if="result.page_number > 0" class="result-page">
                第{{ result.page_number }}页
              </span>
            </div>
            <div class="result-score">
              <el-tag 
                :type="getScoreTagType(result.similarity_score)"
                size="small"
                class="score-tag"
              >
                相似度: {{ formatSimilarityScore(result.similarity_score) }}
              </el-tag>
            </div>
          </div>
          
          <div class="result-content">
            <!-- 图片内容 -->
            <div v-if="result.chunk_type === 'image'" class="image-content">
              <div class="image-wrapper">
                <img 
                  :src="result.image_url || '/placeholder-image.png'" 
                  :alt="result.description || '图片内容'"
                  class="result-image"
                  @error="handleImageError"
                />
              </div>
              <div class="image-description">
                <h4>图片描述</h4>
                <p>{{ result.description || '暂无描述' }}</p>
              </div>
            </div>
            
            <!-- 文本内容 -->
            <div v-else class="text-content">
              <div class="content-text" v-html="highlightKeywords(result.content, searchQuery)"></div>
            </div>
          </div>
          
          <div class="result-actions">
            <el-button 
              @click="viewDetails(result)" 
              size="small" 
              type="primary" 
              plain
            >
              <el-icon><View /></el-icon>
              查看详情
            </el-button>
            <el-button 
              @click="copyContent(result)" 
              size="small" 
              plain
            >
              <el-icon><CopyDocument /></el-icon>
              复制内容
            </el-button>
            <el-button 
              @click="addToCollection(result)" 
              size="small" 
              plain
            >
              <el-icon><Star /></el-icon>
              收藏
            </el-button>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div class="pagination-wrapper" v-if="totalPages > 1">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="searchResults.length"
          layout="total, prev, pager, next, jumper"
          @current-change="handlePageChange"
        />
      </div>

      <!-- 无结果提示 -->
      <div v-else class="no-results">
        <div class="no-results-content">
          <el-icon class="no-results-icon"><Search /></el-icon>
          <h3>未找到相关结果</h3>
          <p>请尝试调整搜索关键词或降低相似度阈值</p>
          <div class="search-suggestions">
            <h4>搜索建议:</h4>
            <div class="suggestion-tags">
              <el-tag 
                v-for="suggestion in searchSuggestions" 
                :key="suggestion"
                @click="useSuggestion(suggestion)"
                class="suggestion-tag"
                effect="plain"
              >
                {{ suggestion }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 搜索建议 -->
    <div class="search-suggestions-section" v-if="searchSuggestions.length > 0 && !hasSearched">
      <h3>热门搜索</h3>
      <div class="suggestions-grid">
        <el-tag 
          v-for="suggestion in searchSuggestions" 
          :key="suggestion"
          @click="useSuggestion(suggestion)"
          class="suggestion-tag"
          effect="plain"
        >
          {{ suggestion }}
        </el-tag>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import ragAPI from '@/services/api.js'
import { 
  FILTER_OPTIONS, 
  SORT_OPTIONS,
  SEARCH_SUGGESTIONS,
  PAGINATION 
} from '@/utils/constants.js'
import { 
  formatSimilarityScore, 
  getContentTypeLabel,
  getContentTypeIcon,
  highlightKeyword,
  copyToClipboard,
  debounce 
} from '@/utils/helpers.js'

// 响应式数据
const searchQuery = ref('')
const searchResults = ref([])
const isSearching = ref(false)
const hasSearched = ref(false)
const searchTime = ref(0)
const selectedContentType = ref('all')
const maxResults = ref(20)
const similarityThreshold = ref(0.5)
const sortBy = ref('relevance')
const currentPage = ref(1)
const pageSize = ref(PAGINATION.DEFAULT_PAGE_SIZE)
const searchSuggestions = ref(SEARCH_SUGGESTIONS)

// 内容类型选项
const contentTypeOptions = computed(() => [
  { value: 'all', label: '全部', icon: 'Grid' },
  { value: 'text', label: '文本', icon: 'Document' },
  { value: 'image', label: '图片', icon: 'Picture' },
  { value: 'table', label: '表格', icon: 'Grid' },
  { value: 'document', label: '文档', icon: 'Document' }
])

// 计算属性
const averageSimilarity = computed(() => {
  if (searchResults.value.length === 0) return 0
  const total = searchResults.value.reduce((sum, result) => sum + result.similarity_score, 0)
  return total / searchResults.value.length
})

const sortedResults = computed(() => {
  const results = [...searchResults.value]
  
  switch (sortBy.value) {
    case 'score':
      return results.sort((a, b) => b.similarity_score - a.similarity_score)
    case 'type':
      return results.sort((a, b) => a.chunk_type.localeCompare(b.chunk_type))
    case 'relevance':
    default:
      return results.sort((a, b) => b.similarity_score - a.similarity_score)
  }
})

const totalPages = computed(() => {
  return Math.ceil(sortedResults.value.length / pageSize.value)
})

const paginatedResults = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return sortedResults.value.slice(start, end)
})

// 方法
const performSearch = async () => {
  if (!searchQuery.value.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }

  isSearching.value = true
  hasSearched.value = true
  const startTime = Date.now()

  try {
    // 构建查询参数
    const queryParams = {
      query: searchQuery.value,
      query_type: 'search',
      max_results: maxResults.value,
      similarity_threshold: similarityThreshold.value
    }

    // 如果选择了特定内容类型，添加到查询参数
    if (selectedContentType.value !== 'all') {
      queryParams.content_type = selectedContentType.value
    }

    // 发送搜索请求
    const response = await ragAPI.sendQuery(queryParams)
    
    searchResults.value = response.results || []
    searchTime.value = Date.now() - startTime
    
    // 重置分页
    currentPage.value = 1
    
    if (searchResults.value.length === 0) {
      ElMessage.info('未找到相关结果，请尝试其他关键词')
    } else {
      ElMessage.success(`找到 ${searchResults.value.length} 个相关结果`)
    }

  } catch (error) {
    console.error('搜索失败:', error)
    searchResults.value = []
    searchTime.value = 0
    ElMessage.error('搜索失败，请稍后重试')
  } finally {
    isSearching.value = false
  }
}

const clearResults = () => {
  searchResults.value = []
  hasSearched.value = false
  searchTime.value = 0
  currentPage.value = 1
}

const sortResults = (sortType) => {
  sortBy.value = sortType
  currentPage.value = 1
}

const handlePageChange = (page) => {
  currentPage.value = page
  // 滚动到顶部
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const useSuggestion = (suggestion) => {
  searchQuery.value = suggestion
  performSearch()
}

const viewDetails = (result) => {
  ElMessage.info('查看详情功能开发中...')
  console.log('查看详情:', result)
}

const copyContent = async (result) => {
  const content = result.content || result.description || ''
  const success = await copyToClipboard(content)
  if (success) {
    ElMessage.success('内容已复制到剪贴板')
  } else {
    ElMessage.error('复制失败')
  }
}

const addToCollection = (result) => {
  ElMessage.info('收藏功能开发中...')
  console.log('添加到收藏:', result)
}

const handleImageError = (event) => {
  event.target.src = '/placeholder-image.png'
}

const formatThresholdTooltip = (value) => {
  return `${value}`
}

// 工具函数
const getContentTypeTag = (type) => {
  const tagMap = {
    'text': '',
    'image': 'success',
    'table': 'warning',
    'document': 'info'
  }
  return tagMap[type] || ''
}

const getScoreTagType = (score) => {
  if (score >= 0.8) return 'success'
  if (score >= 0.6) return 'warning'
  if (score >= 0.4) return 'danger'
  return 'info'
}

const highlightKeywords = (text, keywords) => {
  if (!text || !keywords) return text
  
  const keywordList = keywords.split(' ').filter(k => k.trim())
  let highlightedText = text
  
  keywordList.forEach(keyword => {
    if (keyword.trim()) {
      highlightedText = highlightKeyword(highlightedText, keyword.trim(), 'highlight-keyword')
    }
  })
  
  return highlightedText
}

// 生命周期
onMounted(() => {
  // 可以在这里加载搜索历史或其他初始化操作
})
</script>

<style scoped>
.search-container {
  min-height: 100vh;
  background-color: var(--el-bg-color-page);
}

/* 搜索头部 */
.search-header {
  background: white;
  border-bottom: 1px solid var(--el-border-color);
  padding: 16px 20px;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon {
  font-size: 24px;
  color: var(--el-color-primary);
}

.header-left h1 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

/* 搜索输入区域 */
.search-input-section {
  background: white;
  padding: 40px 20px;
  border-bottom: 1px solid var(--el-border-color);
}

.input-container {
  max-width: 1200px;
  margin: 0 auto;
}

.search-input-wrapper {
  margin-bottom: 24px;
}

.search-input {
  max-width: 800px;
  margin: 0 auto;
}

.search-options {
  display: flex;
  gap: 32px;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
}

.option-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.option-label {
  font-weight: 600;
  color: var(--el-text-color-primary);
  white-space: nowrap;
}

.threshold-control {
  display: flex;
  align-items: center;
  gap: 12px;
}

.threshold-value {
  min-width: 30px;
  text-align: center;
  font-weight: 600;
  color: var(--el-color-primary);
}

/* 搜索结果区域 */
.search-results-section {
  padding: 20px;
}

.results-header {
  max-width: 1200px;
  margin: 0 auto 24px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
}

.results-info h2 {
  margin: 0 0 8px 0;
  color: var(--el-text-color-primary);
}

.results-stats {
  display: flex;
  gap: 20px;
  color: var(--el-text-color-regular);
  font-size: 0.9rem;
}

.results-actions {
  flex-shrink: 0;
}

/* 结果列表 */
.results-list {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.result-item {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.result-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.result-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.result-rank {
  font-weight: 700;
  color: var(--el-color-primary);
  font-size: 1.1rem;
}

.result-type-tag {
  margin: 0;
}

.result-document {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.result-page {
  color: var(--el-text-color-placeholder);
  font-size: 0.9rem;
}

.result-score {
  flex-shrink: 0;
}

.score-tag {
  margin: 0;
}

/* 结果内容 */
.result-content {
  margin-bottom: 20px;
}

.image-content {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.image-wrapper {
  flex-shrink: 0;
}

.result-image {
  max-width: 200px;
  max-height: 150px;
  border-radius: 8px;
  object-fit: cover;
  border: 1px solid var(--el-border-color-lighter);
}

.image-description h4 {
  margin: 0 0 8px 0;
  color: var(--el-text-color-primary);
}

.image-description p {
  margin: 0;
  color: var(--el-text-color-regular);
  line-height: 1.5;
}

.text-content {
  line-height: 1.6;
  color: var(--el-text-color-primary);
}

.content-text {
  word-wrap: break-word;
}

/* 高亮关键词 */
:deep(.highlight-keyword) {
  background-color: var(--el-color-warning-light-9);
  color: var(--el-color-warning);
  padding: 2px 4px;
  border-radius: 3px;
  font-weight: 600;
}

/* 结果操作 */
.result-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

/* 分页 */
.pagination-wrapper {
  max-width: 1200px;
  margin: 40px auto 0;
  display: flex;
  justify-content: center;
}

/* 无结果提示 */
.no-results {
  max-width: 1200px;
  margin: 0 auto;
  text-align: center;
  padding: 80px 20px;
}

.no-results-content {
  background: white;
  border-radius: 16px;
  padding: 60px 40px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.no-results-icon {
  font-size: 4rem;
  color: var(--el-text-color-placeholder);
  margin-bottom: 24px;
}

.no-results h3 {
  margin: 0 0 16px 0;
  color: var(--el-text-color-primary);
}

.no-results p {
  margin: 0 0 32px 0;
  color: var(--el-text-color-regular);
  line-height: 1.6;
}

.search-suggestions h4 {
  margin: 0 0 16px 0;
  color: var(--el-text-color-primary);
}

.suggestion-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.suggestion-tag {
  cursor: pointer;
  transition: all 0.2s ease;
}

.suggestion-tag:hover {
  background-color: var(--el-color-primary);
  color: white;
}

/* 搜索建议区域 */
.search-suggestions-section {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
  text-align: center;
}

.search-suggestions-section h3 {
  margin: 0 0 24px 0;
  color: var(--el-text-color-primary);
}

.suggestions-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .search-header {
    padding: 12px 16px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .search-input-section {
    padding: 24px 16px;
  }
  
  .search-options {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .option-group {
    justify-content: space-between;
  }
  
  .results-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .results-stats {
    flex-direction: column;
    gap: 8px;
  }
  
  .results-actions {
    align-self: center;
  }
  
  .result-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .result-meta {
    flex-wrap: wrap;
  }
  
  .image-content {
    flex-direction: column;
  }
  
  .result-image {
    max-width: 100%;
    max-height: 200px;
  }
  
  .result-actions {
    justify-content: center;
  }
  
  .no-results-content {
    padding: 40px 20px;
  }
}
</style>
