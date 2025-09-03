<template>
  <div class="image-gallery">
    <div class="gallery-header">
      <h3>🖼️ 相关图片</h3>
      <span class="image-count">{{ images.length }} 张图片</span>
    </div>
    
    <div class="gallery-grid">
      <div 
        v-for="(image, index) in images" 
        :key="index" 
        class="image-item"
        @click="openImageViewer(image, index)"
      >
        <div class="image-container">
          <img 
            :src="getImageUrl(image.image_path)" 
            :alt="image.caption || image.image_title || '图片'"
            class="gallery-image"
            @error="handleImageError"
            loading="lazy"
          />
          <div class="image-overlay">
            <div class="image-info">
              <div class="image-title">{{ image.image_title || '图片' }}</div>
              <div class="image-meta">
                <span class="source">{{ image.document_name }}</span>
                <span v-if="image.page_number > 0" class="page">第{{ image.page_number }}页</span>
                <span class="score">相关性: {{ (image.similarity_score * 100).toFixed(0) }}%</span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="image-caption">
          {{ truncateText(image.caption || image.content, 80) }}
        </div>
      </div>
    </div>
    
    <!-- 图片查看器模态框 -->
    <el-dialog
      v-model="viewerVisible"
      :title="currentImage?.image_title || '图片查看'"
      width="80%"
      class="image-viewer-dialog"
    >
      <div class="image-viewer">
        <div class="viewer-image-container">
          <img 
            :src="getImageUrl(currentImage?.image_path)" 
            :alt="currentImage?.caption || '图片'"
            class="viewer-image"
          />
        </div>
        <div class="viewer-info">
          <div class="viewer-meta">
            <div class="meta-item">
              <strong>文档：</strong>{{ currentImage?.document_name }}
            </div>
            <div v-if="currentImage?.page_number > 0" class="meta-item">
              <strong>页码：</strong>第{{ currentImage.page_number }}页
            </div>
            <div class="meta-item">
              <strong>相关性：</strong>{{ (currentImage?.similarity_score * 100).toFixed(0) }}%
            </div>
          </div>
          <div class="viewer-caption">
            <strong>图片说明：</strong>
            <p>{{ currentImage?.caption || currentImage?.content || '暂无说明' }}</p>
          </div>
        </div>
      </div>
      
      <template #footer>
        <div class="viewer-navigation">
          <el-button @click="prevImage" :disabled="currentIndex <= 0">上一张</el-button>
          <span class="image-counter">{{ currentIndex + 1 }} / {{ images.length }}</span>
          <el-button @click="nextImage" :disabled="currentIndex >= images.length - 1">下一张</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  images: {
    type: Array,
    default: () => []
  }
})

const viewerVisible = ref(false)
const currentIndex = ref(0)

const currentImage = computed(() => {
  return props.images[currentIndex.value] || null
})

const getImageUrl = (imagePath) => {
  if (!imagePath) return ''
  
  // 如果是相对路径，添加基础URL
  if (imagePath.startsWith('/') || imagePath.startsWith('./')) {
    return `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}${imagePath}`
  }
  
  // 如果是完整URL，直接返回
  return imagePath
}

const truncateText = (text, maxLength) => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

const openImageViewer = (image, index) => {
  currentIndex.value = index
  viewerVisible.value = true
}

const prevImage = () => {
  if (currentIndex.value > 0) {
    currentIndex.value--
  }
}

const nextImage = () => {
  if (currentIndex.value < props.images.length - 1) {
    currentIndex.value++
  }
}

const handleImageError = (event) => {
  console.warn('图片加载失败:', event.target.src)
  // 可以设置默认图片或显示错误提示
  event.target.style.display = 'none'
}
</script>

<style scoped>
.image-gallery {
  margin: 16px 0;
}

.gallery-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e0e0e0;
}

.gallery-header h3 {
  margin: 0;
  color: #333;
  font-size: 16px;
  font-weight: 600;
}

.image-count {
  color: #666;
  font-size: 14px;
}

.gallery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.image-item {
  cursor: pointer;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.image-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.image-container {
  position: relative;
  width: 100%;
  height: 150px;
  overflow: hidden;
}

.gallery-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.2s ease;
}

.image-item:hover .gallery-image {
  transform: scale(1.05);
}

.image-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.7));
  color: white;
  padding: 12px;
  transform: translateY(100%);
  transition: transform 0.2s ease;
}

.image-item:hover .image-overlay {
  transform: translateY(0);
}

.image-info {
  font-size: 12px;
}

.image-title {
  font-weight: 600;
  margin-bottom: 4px;
}

.image-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.image-meta span {
  opacity: 0.9;
}

.image-caption {
  padding: 12px;
  background: #f8f9fa;
  font-size: 12px;
  color: #666;
  line-height: 1.4;
}

/* 图片查看器样式 */
.image-viewer-dialog {
  .el-dialog__body {
    padding: 0;
  }
}

.image-viewer {
  display: flex;
  flex-direction: column;
  max-height: 70vh;
}

.viewer-image-container {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f5f5f5;
  padding: 20px;
}

.viewer-image {
  max-width: 100%;
  max-height: 50vh;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.viewer-info {
  padding: 20px;
  background: white;
  border-top: 1px solid #e0e0e0;
}

.viewer-meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.meta-item {
  font-size: 14px;
  color: #666;
}

.viewer-caption {
  font-size: 14px;
  line-height: 1.6;
}

.viewer-caption strong {
  color: #333;
}

.viewer-navigation {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
}

.image-counter {
  font-size: 14px;
  color: #666;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .gallery-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 12px;
  }
  
  .image-container {
    height: 120px;
  }
  
  .viewer-image-container {
    padding: 10px;
  }
  
  .viewer-image {
    max-height: 40vh;
  }
  
  .viewer-info {
    padding: 16px;
  }
  
  .viewer-meta {
    grid-template-columns: 1fr;
    gap: 8px;
  }
}
</style>
