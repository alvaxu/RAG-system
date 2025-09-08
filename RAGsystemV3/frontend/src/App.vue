<template>
  <div id="app" class="app-container">
    <!-- 顶部导航栏 -->
    <el-header class="app-header">
      <div class="header-content">
        <div class="logo">
          <el-icon class="logo-icon"><ChatDotRound /></el-icon>
          <span class="logo-text">{{ getPageTitle() }}</span>
        </div>
        <div class="nav-buttons">
          <el-button 
            :type="route.path === '/' ? 'primary' : 'text'" 
            @click="router.push('/')"
            class="nav-button"
          >
            <el-icon><House /></el-icon>
            <span>首页</span>
          </el-button>
          <el-button 
            :type="route.path === '/chat' ? 'primary' : 'text'" 
            @click="router.push('/chat')"
            class="nav-button"
          >
            <el-icon><ChatDotRound /></el-icon>
            <span>智能问答</span>
          </el-button>
          <el-button 
            :type="route.path === '/memory' ? 'primary' : 'text'" 
            @click="router.push('/memory')"
            class="nav-button"
          >
            <el-icon><Memo /></el-icon>
            <span>记忆管理</span>
          </el-button>
        </div>
        <div class="header-actions">
          <el-switch
            v-model="isDarkMode"
            class="theme-switch"
            inline-prompt
            active-text="暗"
            inactive-text="亮"
            @change="toggleTheme"
          />
        </div>
      </div>
    </el-header>

    <!-- 主要内容区域 -->
    <el-main class="app-main">
      <router-view />
    </el-main>

    <!-- 底部信息 -->
    <el-footer class="app-footer">
      <div class="footer-content">
        <p>&copy; 2025 RAG智能问答系统 V3.0 - 基于向量数据库的多模态智能问答平台</p>
      </div>
    </el-footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ChatDotRound, House, Memo } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

// 响应式数据
const isDarkMode = ref(false)

// 计算属性
const activeIndex = computed(() => route.path)

// 方法
const handleMenuSelect = (index) => {
  router.push(index)
}

const toggleTheme = (value) => {
  if (value) {
    document.documentElement.classList.add('dark')
    ElMessage.success('已切换到暗色主题')
  } else {
    document.documentElement.classList.remove('dark')
    ElMessage.success('已切换到亮色主题')
  }
}

const getPageTitle = () => {
  if (route.path === '/chat') {
    return '智能问答'
  }
  return 'RAG系统'
}

// 生命周期
onMounted(() => {
  // 检查本地存储的主题设置
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme === 'dark') {
    isDarkMode.value = true
    document.documentElement.classList.add('dark')
  }
})
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--el-bg-color);
}

.app-header {
  background-color: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  padding: 0;
  height: 50px;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 16px;
  font-weight: 500;
  color: #6c757d;
}

.logo-icon {
  font-size: 18px;
}

.logo-text {
  white-space: nowrap;
}

.nav-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-button {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  font-size: 14px;
  border: none;
  background: transparent;
}

.nav-button:hover {
  background-color: #f0f0f0;
}

.nav-button.el-button--primary {
  background-color: #409eff;
  color: white;
}

.nav-button.el-button--primary:hover {
  background-color: #337ecc;
}



.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.theme-switch {
  --el-switch-on-color: var(--el-color-primary);
}

.app-main {
  flex: 1;
  padding: 0;
  background-color: var(--el-bg-color-page);
  overflow: hidden;
}

.app-footer {
  background-color: var(--el-bg-color);
  border-top: 1px solid var(--el-border-color);
  padding: 16px 0;
  height: auto;
}

.footer-content {
  text-align: center;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-content {
    padding: 0 16px;
  }
  
  .logo-text {
    display: none;
  }
  
  .header-menu {
    flex: none;
  }
  
  .header-menu .el-menu-item span {
    display: none;
  }
}

/* 暗色主题 */
.dark {
  color-scheme: dark;
}

.dark .app-container {
  background-color: #1a1a1a;
}

.dark .app-header {
  background-color: #1a1a1a;
  border-bottom-color: #333;
}

.dark .app-main {
  background-color: #141414;
}

.dark .app-footer {
  background-color: #1a1a1a;
  border-top-color: #333;
}
</style>
