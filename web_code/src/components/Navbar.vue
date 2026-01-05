<script setup lang="ts">
import { ref } from 'vue';

// 生成类型：image 或 video
const generateType = ref('image');

// 具体生成模式
const generateMode = ref('text2img'); // text2img, img2img, text2video, img2video

// 切换生成类型
const changeGenerateType = (type: string) => {
  generateType.value = type;
  // 根据类型重置模式
  if (type === 'image') {
    generateMode.value = 'text2img';
  } else {
    generateMode.value = 'text2video';
  }
};

// 切换生成模式
const changeGenerateMode = (mode: string) => {
  generateMode.value = mode;
};

// 暴露给父组件的数据
defineExpose({
  generateType,
  generateMode
});
</script>

<template>
  <nav class="navbar">
    <div class="navbar-container">
      <h1 class="app-title">AI 生成平台</h1>
      
      <div class="nav-tabs">
        <!-- 图片生成选项 -->
        <div class="nav-tab-group">
          <button 
            class="nav-tab" 
            :class="{ active: generateType === 'image' }"
            @click="changeGenerateType('image')"
          >
            图片生成
          </button>
          <div class="sub-tabs" v-if="generateType === 'image'">
            <button 
              class="sub-tab" 
              :class="{ active: generateMode === 'text2img' }"
              @click="changeGenerateMode('text2img')"
            >
              文生图
            </button>
            <button 
              class="sub-tab" 
              :class="{ active: generateMode === 'img2img' }"
              @click="changeGenerateMode('img2img')"
            >
              图生图
            </button>
          </div>
        </div>
        
        <!-- 视频生成选项 -->
        <div class="nav-tab-group">
          <button 
            class="nav-tab" 
            :class="{ active: generateType === 'video' }"
            @click="changeGenerateType('video')"
          >
            视频生成
          </button>
          <div class="sub-tabs" v-if="generateType === 'video'">
            <button 
              class="sub-tab" 
              :class="{ active: generateMode === 'text2video' }"
              @click="changeGenerateMode('text2video')"
            >
              文生视频
            </button>
            <button 
              class="sub-tab" 
              :class="{ active: generateMode === 'img2video' }"
              @click="changeGenerateMode('img2video')"
            >
              图生视频
            </button>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>

<style scoped>
.navbar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 10px 0;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.navbar-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.app-title {
  font-size: 24px;
  font-weight: bold;
  margin: 0;
}

.nav-tabs {
  display: flex;
  gap: 20px;
}

.nav-tab-group {
  position: relative;
}

.nav-tab {
  background: transparent;
  color: white;
  border: none;
  padding: 10px 16px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.nav-tab:hover {
  background: rgba(255, 255, 255, 0.1);
}

.nav-tab.active {
  background: rgba(255, 255, 255, 0.2);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.sub-tabs {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  z-index: 100;
}

.sub-tab {
  background: transparent;
  color: #333;
  border: none;
  padding: 10px 16px;
  font-size: 14px;
  text-align: left;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 120px;
}

.sub-tab:hover {
  background: #f5f5f5;
}

.sub-tab.active {
  background: #667eea;
  color: white;
}
</style>