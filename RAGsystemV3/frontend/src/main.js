import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import Home from './views/Home.vue'
import Chat from './views/Chat.vue'
import MemoryView from './views/MemoryView.vue'

// 添加调试信息
console.log('Vue应用开始初始化...')

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
    path: '/memory',
    name: 'Memory',
    component: MemoryView,
    meta: { title: '记忆管理' }
  }
]

console.log('路由配置完成')

const router = createRouter({
  history: createWebHistory(),
  routes
})

console.log('路由器创建完成')

// 创建Vue应用
const app = createApp(App)

console.log('Vue应用创建完成')

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

console.log('Element Plus图标注册完成')

// 使用插件
app.use(router)
app.use(ElementPlus)

console.log('插件注册完成')

// 全局配置
app.config.globalProperties.$ELEMENT = {
  size: 'default',
  zIndex: 3000
}

console.log('全局配置完成')

// 挂载应用
app.mount('#app')

console.log('Vue应用挂载完成')
