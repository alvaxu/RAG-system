# RAG智能问答系统前端

基于Vue.js 3.x + Element Plus的现代化前端界面，为RAG智能问答系统提供用户友好的交互体验。

## 🚀 功能特性

### 核心功能
- **智能问答** - 支持多种查询类型的智能对话
- **内容搜索** - 高效的向量搜索和结果展示
- **多模态支持** - 文本、图片、表格等多种内容类型
- **实时交互** - 流畅的用户体验和响应式设计

### 技术特性
- **Vue 3 Composition API** - 现代化的Vue开发体验
- **Element Plus** - 企业级UI组件库
- **Vite构建** - 快速的开发和构建体验
- **TypeScript支持** - 类型安全的开发
- **响应式设计** - 适配各种设备尺寸
- **暗色主题** - 支持明暗主题切换

## 📦 技术栈

- **框架**: Vue 3.3.8
- **构建工具**: Vite 4.5.0
- **UI组件库**: Element Plus 2.4.2
- **路由**: Vue Router 4.2.5
- **HTTP客户端**: Axios 1.5.0
- **图标**: Element Plus Icons
- **样式**: SCSS + CSS Variables

## 🛠️ 开发环境

### 环境要求
- Node.js >= 16.0.0
- npm >= 8.0.0 或 yarn >= 1.22.0

### 安装依赖
```bash
# 使用npm
npm install

# 使用yarn
yarn install

# 使用pnpm
pnpm install
```

### 开发服务器
```bash
# 启动开发服务器
npm run dev

# 指定端口启动
npm run dev -- --port 3001
```

### 构建生产版本
```bash
# 构建生产版本
npm run build

# 预览生产版本
npm run preview
```

### 代码检查
```bash
# 运行ESLint检查
npm run lint

# 自动修复ESLint问题
npm run lint -- --fix
```

## 📁 项目结构

```
frontend/
├── public/                 # 静态资源
│   └── index.html         # HTML模板
├── src/                   # 源代码
│   ├── assets/           # 静态资源
│   │   └── styles/       # 样式文件
│   ├── components/       # 可复用组件
│   ├── services/         # API服务
│   │   └── api.js        # API接口封装
│   ├── utils/            # 工具函数
│   │   ├── constants.js  # 常量定义
│   │   └── helpers.js    # 辅助函数
│   ├── views/            # 页面组件
│   │   ├── Home.vue      # 首页
│   │   ├── Chat.vue      # 聊天页面
│   │   └── Search.vue    # 搜索页面
│   ├── App.vue           # 根组件
│   └── main.js           # 应用入口
├── package.json          # 项目配置
├── vite.config.js        # Vite配置
└── README.md            # 项目文档
```

## 🎨 页面功能

### 首页 (Home)
- 系统介绍和功能展示
- 快速开始引导
- 系统统计信息
- 响应式设计

### 智能问答 (Chat)
- 多种查询类型支持
- 实时对话交互
- 来源信息展示
- 溯源信息显示
- 聊天历史管理

### 内容搜索 (Search)
- 高级搜索选项
- 结果排序和过滤
- 分页展示
- 内容类型筛选
- 相似度阈值调节

## 🔧 配置说明

### 环境变量
创建 `.env` 文件配置环境变量：

```env
# API基础URL
VITE_API_BASE_URL=http://localhost:8000

# 应用配置
VITE_APP_TITLE=RAG智能问答系统
VITE_APP_VERSION=3.0.0

# 功能开关
VITE_ENABLE_MOCK=false
VITE_ENABLE_DARK_MODE=true
```

### API配置
API服务配置在 `src/services/api.js` 中：

```javascript
// 创建axios实例
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
})
```

### 主题配置
主题配置在 `src/assets/styles/variables.scss` 中：

```scss
// 主色调
$primary-color: #409EFF;
$success-color: #67C23A;
$warning-color: #E6A23C;
$danger-color: #F56C6C;
```

## 📱 响应式设计

### 断点设置
- **XS**: < 480px (手机)
- **SM**: 480px - 768px (平板)
- **MD**: 768px - 992px (小桌面)
- **LG**: 992px - 1200px (桌面)
- **XL**: > 1200px (大桌面)

### 适配策略
- 移动端优先设计
- 弹性布局和网格系统
- 触摸友好的交互
- 优化的加载性能

## 🎯 开发指南

### 组件开发
1. 使用Vue 3 Composition API
2. 遵循Element Plus设计规范
3. 保持组件的单一职责
4. 添加适当的TypeScript类型

### 样式开发
1. 使用SCSS预处理器
2. 遵循BEM命名规范
3. 使用CSS变量实现主题切换
4. 保持响应式设计

### API集成
1. 统一使用 `src/services/api.js`
2. 添加适当的错误处理
3. 实现请求和响应拦截
4. 支持请求取消和重试

## 🚀 部署指南

### 构建优化
```bash
# 分析构建包大小
npm run build -- --analyze

# 构建并生成报告
npm run build -- --report
```

### 部署配置
1. 配置生产环境API地址
2. 设置CDN资源路径
3. 配置反向代理
4. 启用Gzip压缩

### Docker部署
```dockerfile
FROM node:16-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 🐛 问题排查

### 常见问题

1. **API连接失败**
   - 检查后端服务是否启动
   - 确认API地址配置正确
   - 检查网络连接和防火墙

2. **构建失败**
   - 清除node_modules重新安装
   - 检查Node.js版本兼容性
   - 查看详细错误信息

3. **样式问题**
   - 检查Element Plus版本兼容性
   - 确认SCSS编译正常
   - 验证CSS变量定义

### 调试工具
- Vue DevTools浏览器扩展
- Element Plus官方文档
- Vite开发工具
- 浏览器开发者工具

## 📄 许可证

MIT License

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 📞 支持

如有问题或建议，请通过以下方式联系：

- 提交Issue
- 发送邮件
- 查看文档

---

**RAG智能问答系统前端** - 让AI问答更简单、更智能！
