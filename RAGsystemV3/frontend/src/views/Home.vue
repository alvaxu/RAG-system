<template>
  <div class="home-container">
    <!-- 英雄区域 -->
    <section class="hero-section">
      <div class="hero-content">
        <div class="hero-text">
          <h1 class="hero-title">
            <el-icon class="title-icon"><ChatDotRound /></el-icon>
            RAG智能问答系统
          </h1>
          <p class="hero-subtitle">
            基于向量数据库的多模态智能问答平台，支持文本、图片、表格等多种内容类型的智能检索和问答
          </p>
          <div class="hero-actions">
            <el-button 
              type="primary" 
              size="large" 
              @click="goToChat"
              class="action-button"
            >
              <el-icon><ChatDotRound /></el-icon>
              开始智能问答
            </el-button>
          </div>
        </div>
        <div class="hero-image">
          <div class="feature-cards">
            <div class="feature-card" v-for="feature in features" :key="feature.id">
              <el-icon class="feature-icon" :style="{ color: feature.color }">
                <component :is="feature.icon" />
              </el-icon>
              <h3>{{ feature.title }}</h3>
              <p>{{ feature.description }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 功能特性区域 -->
    <section class="features-section">
      <div class="section-header">
        <h2>核心功能特性</h2>
        <p>强大的AI驱动功能，为您提供智能化的内容检索和问答体验</p>
      </div>
      <div class="features-grid">
        <div class="feature-item" v-for="feature in detailedFeatures" :key="feature.id">
          <div class="feature-icon-wrapper">
            <el-icon class="feature-icon" :style="{ color: feature.color }">
              <component :is="feature.icon" />
            </el-icon>
          </div>
          <h3>{{ feature.title }}</h3>
          <p>{{ feature.description }}</p>
          <ul class="feature-list">
            <li v-for="item in feature.items" :key="item">{{ item }}</li>
          </ul>
        </div>
      </div>
    </section>

    <!-- 使用统计区域 -->
    <section class="stats-section" v-if="systemStats">
      <div class="section-header">
        <h2>系统统计</h2>
        <p>实时系统运行状态和性能指标</p>
      </div>
      <div class="stats-grid">
        <div class="stat-item">
          <div class="stat-value">{{ systemStats.totalQueries || 0 }}</div>
          <div class="stat-label">总查询次数</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ systemStats.totalDocuments || 0 }}</div>
          <div class="stat-label">文档数量</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ systemStats.averageResponseTime || 0 }}ms</div>
          <div class="stat-label">平均响应时间</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ systemStats.successRate || 0 }}%</div>
          <div class="stat-label">成功率</div>
        </div>
      </div>
    </section>

    <!-- 快速开始区域 -->
    <section class="quick-start-section">
      <div class="section-header">
        <h2>快速开始</h2>
        <p>选择您需要的功能，立即开始使用</p>
      </div>
      <div class="quick-start-grid">
        <div class="quick-start-item" @click="goToChat">
          <el-icon class="quick-start-icon"><ChatDotRound /></el-icon>
          <h3>智能问答</h3>
          <p>与AI助手对话，获取智能回答。支持文本、图片、表格等多种查询类型</p>
          <el-button type="primary" plain>开始对话</el-button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import ragAPI from '@/services/api.js'
import { QUERY_TYPE_CONFIG } from '@/utils/constants.js'

const router = useRouter()

// 响应式数据
const systemStats = ref(null)

// 功能特性数据
const features = ref([
  {
    id: 1,
    title: '多模态查询',
    description: '支持文本、图片、表格等多种内容类型',
    icon: 'Connection',
    color: '#409EFF'
  },
  {
    id: 2,
    title: '智能问答',
    description: '基于大语言模型的智能对话',
    icon: 'ChatDotRound',
    color: '#67C23A'
  },
  {
    id: 3,
    title: '向量搜索',
    description: '高效的语义相似度搜索',
    icon: 'Search',
    color: '#E6A23C'
  }
])

const detailedFeatures = ref([
  {
    id: 1,
    title: '智能查询处理',
    description: '自动识别查询类型，提供精准的检索结果',
    icon: 'MagicStick',
    color: '#409EFF',
    items: [
      '自动查询类型识别',
      '多模态内容检索',
      '智能结果排序',
      '上下文理解'
    ]
  },
  {
    id: 2,
    title: '向量数据库',
    description: '基于先进向量技术的语义搜索',
    icon: 'DataBoard',
    color: '#67C23A',
    items: [
      '高维向量存储',
      '语义相似度计算',
      '快速检索算法',
      '多语言支持'
    ]
  },
  {
    id: 3,
    title: '大语言模型',
    description: '集成先进的大语言模型，提供智能回答',
    icon: 'ChatDotRound',
    color: '#E6A23C',
    items: [
      '自然语言理解',
      '智能回答生成',
      '上下文记忆',
      '多轮对话'
    ]
  },
  {
    id: 4,
    title: '结果溯源',
    description: '完整的答案来源追踪和可信度评估',
    icon: 'Link',
    color: '#F56C6C',
    items: [
      '来源文档追踪',
      '置信度评估',
      '相关性评分',
      '详细溯源信息'
    ]
  }
])

// 方法
const goToChat = () => {
  router.push('/chat')
}

const loadSystemStats = async () => {
  try {
    const stats = await ragAPI.getSystemStatus()
    systemStats.value = stats
  } catch (error) {
    console.error('获取系统统计失败:', error)
    // 不显示错误消息，因为这是非关键功能
  }
}

// 生命周期
onMounted(() => {
  loadSystemStats()
})
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

/* 英雄区域 */
.hero-section {
  padding: 80px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.hero-content {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 60px;
  align-items: center;
}

.hero-title {
  font-size: 3rem;
  font-weight: 700;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.title-icon {
  font-size: 3.5rem;
}

.hero-subtitle {
  font-size: 1.2rem;
  line-height: 1.6;
  margin-bottom: 40px;
  opacity: 0.9;
}

.hero-actions {
  display: flex;
  gap: 20px;
}

.action-button {
  padding: 16px 32px;
  font-size: 1.1rem;
  border-radius: 8px;
}

.hero-image {
  display: flex;
  justify-content: center;
  align-items: center;
}

.feature-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.feature-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 24px;
  text-align: center;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.feature-card .feature-icon {
  font-size: 2.5rem;
  margin-bottom: 16px;
}

.feature-card h3 {
  font-size: 1.2rem;
  margin-bottom: 12px;
  font-weight: 600;
}

.feature-card p {
  font-size: 0.9rem;
  opacity: 0.8;
  line-height: 1.4;
}

/* 功能特性区域 */
.features-section {
  padding: 80px 20px;
  background: white;
}

.section-header {
  text-align: center;
  margin-bottom: 60px;
}

.section-header h2 {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 16px;
  color: #2c3e50;
}

.section-header p {
  font-size: 1.1rem;
  color: #7f8c8d;
  max-width: 600px;
  margin: 0 auto;
}

.features-grid {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 40px;
}

.feature-item {
  text-align: center;
  padding: 40px 20px;
  border-radius: 16px;
  background: #f8f9fa;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.feature-item:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
}

.feature-icon-wrapper {
  width: 80px;
  height: 80px;
  margin: 0 auto 24px;
  background: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.feature-icon {
  font-size: 2.5rem;
}

.feature-item h3 {
  font-size: 1.4rem;
  font-weight: 600;
  margin-bottom: 16px;
  color: #2c3e50;
}

.feature-item p {
  color: #7f8c8d;
  margin-bottom: 24px;
  line-height: 1.6;
}

.feature-list {
  list-style: none;
  padding: 0;
  text-align: left;
}

.feature-list li {
  padding: 8px 0;
  color: #5a6c7d;
  position: relative;
  padding-left: 20px;
}

.feature-list li::before {
  content: '✓';
  position: absolute;
  left: 0;
  color: #67C23A;
  font-weight: bold;
}

/* 统计区域 */
.stats-section {
  padding: 80px 20px;
  background: #f8f9fa;
}

.stats-grid {
  max-width: 800px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 40px;
}

.stat-item {
  text-align: center;
  padding: 40px 20px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.stat-value {
  font-size: 2.5rem;
  font-weight: 700;
  color: #409EFF;
  margin-bottom: 8px;
}

.stat-label {
  color: #7f8c8d;
  font-size: 1rem;
}

/* 快速开始区域 */
.quick-start-section {
  padding: 80px 20px;
  background: white;
}

.quick-start-grid {
  max-width: 800px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 40px;
}

.quick-start-item {
  text-align: center;
  padding: 60px 40px;
  border: 2px solid #e9ecef;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.quick-start-item:hover {
  border-color: #409EFF;
  transform: translateY(-4px);
  box-shadow: 0 16px 32px rgba(64, 158, 255, 0.2);
}

.quick-start-icon {
  font-size: 4rem;
  color: #409EFF;
  margin-bottom: 24px;
}

.quick-start-item h3 {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 16px;
  color: #2c3e50;
}

.quick-start-item p {
  color: #7f8c8d;
  margin-bottom: 32px;
  line-height: 1.6;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .hero-content {
    grid-template-columns: 1fr;
    gap: 40px;
    text-align: center;
  }
  
  .hero-title {
    font-size: 2.5rem;
  }
  
  .hero-actions {
    justify-content: center;
    flex-wrap: wrap;
  }
  
  .feature-cards {
    grid-template-columns: 1fr;
  }
  
  .features-grid {
    grid-template-columns: 1fr;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .quick-start-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .hero-section {
    padding: 60px 16px;
  }
  
  .hero-title {
    font-size: 2rem;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
