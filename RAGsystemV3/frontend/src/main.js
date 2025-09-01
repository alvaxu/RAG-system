import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import Home from './views/Home.vue'
import Chat from './views/Chat.vue'
import Search from './views/Search.vue'

// 路由配置
const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { title: '首页' }
  },
  {
    path: '/chat',
    name: 'Chat',
    component: Chat,
    meta: { title: '智能问答' }
  },
  {
    path: '/search',
    name: 'Search',
    component: Search,
    meta: { title: '内容搜索' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 创建Vue应用
const app = createApp(App)

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 使用插件
app.use(router)
app.use(ElementPlus)

// 全局配置
app.config.globalProperties.$ELEMENT = {
  size: 'default',
  zIndex: 3000
}

// 挂载应用
app.mount('#app')
