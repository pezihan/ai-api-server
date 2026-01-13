<template>
  <div class="generate-wrapper">
    <!-- 任务列表面板 -->
    <transition name="slide">
      <div v-if="showTaskList" class="task-list-panel">
        <TaskList @close="showTaskList = false" />
      </div>
    </transition>
    <div class="generate-container">
      <h2 class="generate-title">开启你的 <span class="generate-title-highlight">{{ generateType }}</span></h2>
    </div>
    <div class="generate-content-list">
    <div class="generate-content-input">
      <div v-if="['图生图', '图生视频'].includes(generateType)" style="margin-right: 20px;">
        <div v-if="!selectedImage" class="file-select">
          <img @click="openFileSelector" src="../assets/image/tool_generate_add.png" alt="添加图片"/>
        </div>
        <div v-else class="selected-image">
          <img :src="selectedImage" alt="已选择的图片"/>
          <button class="delete-image" @click="deleteImage">×</button>
        </div>
      </div>
      <input type="file" ref="fileInput" style="display: none" accept="image/*" @change="handleFileSelect">
      <div class="input-wrapper">
        <textarea ref="promptInput" placeholder="发挥你的想象力，描述你想要的画面吧！比如：一只可爱的小猫在阳光下玩耍" rows="3"></textarea>
        <div class="negative-prompt">
          <textarea v-model="negativePrompt" placeholder="告诉我们你不喜欢什么，比如：模糊、变形、低质量" rows="3"></textarea>
        </div>
      </div>
    </div>
    <div class="generate-menu">
      <div class="left-box">
        <!-- 任务列表按钮 -->
        <button class="task-list-btn" @click="toggleTaskList($event)" title="任务列表" style="pointer-events: auto;">
          <svg viewBox="0 0 24 24" fill="none">
            <line x1="3" y1="12" x2="21" y2="12"></line>
            <line x1="3" y1="6" x2="21" y2="6"></line>
            <line x1="3" y1="18" x2="21" y2="18"></line>
          </svg>
        </button>
        <!-- 渲染类型 -->
        <div class="custom-select">
          <div class="select-header" @click="toggleDropdown('type', $event)">
            <span class="select-icon">
              <svg v-if="generateType === '文生图'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                <circle cx="8.5" cy="8.5" r="1.5"></circle>
                <polyline points="21 15 16 10 5 21"></polyline>
              </svg>
              <svg v-else-if="generateType === '图生图'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                <circle cx="8.5" cy="8.5" r="1.5"></circle>
                <polyline points="21 15 16 10 5 21"></polyline>
                <path d="M16 17l5-5-5-5"></path>
              </svg>
              <svg v-else-if="generateType === '文生视频'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="23 7 16 12 23 17 23 7"></polygon>
                <rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect>
              </svg>
              <svg v-else-if="generateType === '图生视频'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="23 7 16 12 23 17 23 7"></polygon>
                <rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect>
                <circle cx="5.5" cy="10.5" r="1.5"></circle>
                <polyline points="10 6 10 14"></polyline>
              </svg>
            </span>
            <span class="select-text">{{ generateType }}</span>
            <span class="select-arrow" :class="{ 'rotated': dropdownOpen.type }">▼</span>
          </div>
          <div class="select-dropdown" v-if="dropdownOpen.type">
            <div class="dropdown-item" v-for="type in generateTypes" :key="type.value" @click="selectType(type.value)">
              <span class="item-icon" v-if="type.value === '文生图'">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                  <circle cx="8.5" cy="8.5" r="1.5"></circle>
                  <polyline points="21 15 16 10 5 21"></polyline>
                </svg>
              </span>
              <span class="item-icon" v-else-if="type.value === '图生图'">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                  <circle cx="8.5" cy="8.5" r="1.5"></circle>
                  <polyline points="21 15 16 10 5 21"></polyline>
                  <path d="M16 17l5-5-5-5"></path>
                </svg>
              </span>
              <span class="item-icon" v-else-if="type.value === '文生视频'">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polygon points="23 7 16 12 23 17 23 7"></polygon>
                  <rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect>
                </svg>
              </span>
              <span class="item-icon" v-else-if="type.value === '图生视频'">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polygon points="23 7 16 12 23 17 23 7"></polygon>
                  <rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect>
                  <circle cx="5.5" cy="10.5" r="1.5"></circle>
                  <polyline points="10 6 10 14"></polyline>
                </svg>
              </span>
              {{ type.label }}
            </div>
          </div>
        </div>
        
        <!-- 横竖方选择 -->
        <div class="custom-select">
          <div class="select-header" @click="toggleDropdown('size', $event)">
            <span class="select-icon size-icon">
              <svg v-if="generateSize === '横'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="6" width="18" height="12" rx="0" ry="0"></rect>
              </svg>
              <svg v-else-if="generateSize === '竖'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="6" y="3" width="12" height="18" rx="0" ry="0"></rect>
              </svg>
              <svg v-else-if="generateSize === '方'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="0" ry="0"></rect>
              </svg>
            </span>
            <span class="select-text">{{ generateSize }}</span>
            <span class="select-arrow" :class="{ 'rotated': dropdownOpen.size }">▼</span>
          </div>
          <div class="select-dropdown" v-if="dropdownOpen.size">
            <div class="dropdown-item" v-for="size in sizes" :key="size.value" @click="selectSize(size.value)">
              <span class="item-icon size-icon" v-if="size.value === '横'">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="3" y="6" width="18" height="12" rx="0" ry="0"></rect>
                </svg>
              </span>
              <span class="item-icon size-icon" v-else-if="size.value === '竖'">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="6" y="3" width="12" height="18" rx="0" ry="0"></rect>
                </svg>
              </span>
              <span class="item-icon size-icon" v-else-if="size.value === '方'">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="3" y="3" width="18" height="18" rx="0" ry="0"></rect>
                </svg>
              </span>
              {{ size.label }}
            </div>
          </div>
        </div>
        
        <!-- 时长选择 -->
        <div class="custom-select">
          <div class="select-header" @click="toggleDropdown('duration', $event)">
            <span class="select-icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12 6 12 12 16 14"></polyline>
              </svg>
            </span>
            <span class="select-text">{{ generateDuration }}</span>
            <span class="select-arrow" :class="{ 'rotated': dropdownOpen.duration }">▼</span>
          </div>
          <div class="select-dropdown" v-if="dropdownOpen.duration">
            <div class="dropdown-item" v-for="duration in durations" :key="duration.value" @click="selectDuration(duration.value)">
              <span class="item-icon"></span>
              {{ duration.label }}
            </div>
          </div>
        </div>
        
        <!-- 推理步数 -->
        <div class="step-input-box">
          <input type="number" v-model="inferenceSteps" placeholder="推理步数" class="step-input">
        </div>
        
        <!-- lora选择 -->
        <div class="custom-select lora-select">
          <div class="select-header" @click="toggleDropdown('lora', $event)">
            <span class="select-icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="3"></circle>
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
              </svg>
            </span>
            <span class="select-text">{{ selectedLoras.length > 0 ? `已选择 ${selectedLoras.length} 个` : '选择 Lora' }}</span>
            <span class="select-arrow" :class="{ 'rotated': dropdownOpen.lora }">▼</span>
          </div>
          <div class="select-dropdown" v-if="dropdownOpen.lora">
            <div class="dropdown-item" v-for="lora in loras" :key="lora.value" @click="toggleLora(lora.value)">
              <span class="item-icon">
                <svg v-if="selectedLoras.includes(lora.value)" width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                </svg>
              </span>
              {{ lora.label }}
            </div>
          </div>
        </div>
      </div>
      <div class="right-box">
        <button class="generate-btn" @click="generateImage">生成</button>
      </div>
    </div>
      </div>
  </div>
</template>

<script lang="ts">
import TaskList from './TaskList.vue'

export default {
  name: 'Generate',
  components: {
    TaskList
  },
  mounted() {
    // 添加全局点击事件监听器，点击空白处关闭下拉菜单
    document.addEventListener('click', this.handleClickOutside)
  },
  beforeUnmount() {
    // 移除全局点击事件监听器
    document.removeEventListener('click', this.handleClickOutside)
  },
  data() {
    return {
      generateCount: 1,
      generateType: '文生图',
      selectedLoras: [],
      inferenceSteps: '',
      generateSize: '横',
      generateDuration: '5秒',
      selectedImage: null,
        negativePrompt: '',
        showTaskList: false,
      dropdownOpen: {
        type: false,
        lora: false,
        size: false,
        duration: false
      },
      generateTypes: [
        { label: '文生图', value: '文生图' },
        { label: '图生图', value: '图生图' },
        { label: '文生视频', value: '文生视频' },
        { label: '图生视频', value: '图生视频' }
      ],
      loras: [
        { label: 'lora1', value: 'lora1' },
        { label: 'lora2', value: 'lora2' },
        { label: 'lora3', value: 'lora3' },
        { label: 'lora3', value: 'lora3' },
        { label: 'lora3asdasdasdasasdasdasdasddasdasdasdasdasdasd', value: 'lora3asdasdasdasdasdasdasdasdasdasd' },
        { label: 'lora3', value: 'lora3' },
        { label: 'lora3', value: 'lora3' },
        { label: 'lora3', value: 'lora3' },
        { label: 'lora3', value: 'lora3' },
      ],
      sizes: [
        { label: '横', value: '横' },
        { label: '竖', value: '竖' },
        { label: '方', value: '方' }
      ],
      durations: [
        { label: '5秒', value: '5秒' },
        { label: '10秒', value: '10秒' },
        { label: '15秒', value: '15秒' }
      ]
    }
  },
  methods: {
    incrementCount() {
      if (this.generateCount < 10) {
        this.generateCount++
      }
    },
    decrementCount() {
      if (this.generateCount > 1) {
        this.generateCount--
      }
    },
    // 处理点击空白处的事件
    handleClickOutside(event) {
      const selectElements = event.target.closest('.custom-select')
      const taskListPanel = event.target.closest('.task-list-panel')
      const taskListBtn = event.target.closest('.task-list-btn')
      
      if (!selectElements) {
        // 点击的不是选择器内部，关闭所有下拉菜单
        Object.keys(this.dropdownOpen).forEach(key => {
          this.dropdownOpen[key] = false
        })
      }
      
      if (!taskListPanel && !taskListBtn && this.showTaskList) {
        // 点击的不是任务列表内部或任务列表按钮，关闭任务列表
        this.showTaskList = false
      }
    },
    toggleDropdown(type, event) {
      // 阻止事件冒泡，避免触发handleClickOutside
      event.stopPropagation()
      // 关闭所有下拉框
      Object.keys(this.dropdownOpen).forEach(key => {
        this.dropdownOpen[key] = false
      })
      // 打开当前点击的下拉框
      this.dropdownOpen[type] = true
    },
    selectType(type) {
      this.generateType = type
      this.dropdownOpen.type = false
    },
    toggleLora(lora) {
      const index = this.selectedLoras.indexOf(lora)
      if (index > -1) {
        this.selectedLoras.splice(index, 1)
      } else {
        this.selectedLoras.push(lora)
      }
    },
    selectSize(size) {
      this.generateSize = size
      this.dropdownOpen.size = false
    },
    selectDuration(duration) {
      this.generateDuration = duration
      this.dropdownOpen.duration = false
    },
    generateImage() {
      // 生成图片的逻辑
      console.log('生成图片', {
        prompt: this.$refs.promptInput?.value,
        negativePrompt: this.negativePrompt,
        type: this.generateType,
        lora: this.selectedLoras,
        steps: this.inferenceSteps,
        size: this.generateSize,
        duration: this.generateDuration,
        count: this.generateCount,
        image: this.selectedImage
      })
    },
    openFileSelector() {
      this.$refs.fileInput.click()
    },
    handleFileSelect(event) {
      const file = event.target.files[0]
      if (file) {
        const reader = new FileReader()
        reader.onload = (e) => {
          this.selectedImage = e.target.result
        }
        reader.readAsDataURL(file)
      }
    },
    deleteImage() {
      this.selectedImage = null
      this.$refs.fileInput.value = ''
      },
      toggleTaskList(event) {
        event.stopPropagation()
        this.showTaskList = !this.showTaskList
      }
  }
}
</script>

<style lang="scss" scoped>
.generate-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 80vh;
  padding: 20px;
  box-sizing: border-box;
  position: relative;
}

.task-list-panel {
  position: fixed;
  top: 0;
  right: 0;
  width: 680px;
  height: 100vh;
  background: #fff;
  border-radius: 16px 0 0 16px;
  box-shadow: -8px 0 24px rgba(0, 0, 0, 0.15);
  z-index: 200;
  overflow: hidden;
}

/* 动画效果 */
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}

.slide-enter-from {
  transform: translateX(100%);
}

.slide-leave-to {
  transform: translateX(100%);
}

.generate-container {
  text-align: center;
  margin-bottom: 50px;
  
  .generate-title {
    font-size: 24px;
    font-weight: 600;
    color: #000;
    
    .generate-title-highlight {
      color: #000;
    }
    
    .generate-title-arrow {
      font-size: 12px;
      margin-left: 4px;
      color: #000;
    }
  }
}

.generate-content-list {
  width: 70%;
  margin: 0 auto;
  background: #ffffff;
  border-radius: 24px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: box-shadow 0.3s ease;
  
  &:hover {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  }
  
  .generate-content-input {
        display: flex;
        align-items: flex-start;
        margin-bottom: 20px;
        >div {
          width: 10%;
        }
        .file-select {
          width: 100%;
          height: auto;
          border-radius: 8px;
          background: #e0e0e0;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-right: 12px;
          margin-top: 4px;
          cursor: pointer;
          aspect-ratio: 1;
          img {
            width: 100%;
          }
        }
        
        .selected-image {
          position: relative;
          width: 100%;
          border-radius: 8px;
          margin-right: 12px;
          margin-top: 4px;
          aspect-ratio: 1;
          img {
            width: 100%;
            height: 100%;
            object-fit: cover;
          }
          
          .delete-image {
            position: absolute;
            top: -8px;
            right: -8px;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #000;
            color: #fff;
            border: none;
            font-size: 14px;
            font-weight: bold;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
          }
        }
        
        .input-wrapper {
          flex: 1;
          
          textarea {
            width: 100%;
            min-height: 120px;
            border: none;
            border-radius: 8px;
            padding: 12px 16px;
            font-size: 14px;
            outline: none;
            resize: none;
            font-family: inherit;
            line-height: 1.4;
            background-color: #f5f5f5;
          }
          
          .negative-prompt {
            margin-top: 12px;
            
            textarea {
              width: 100%;
              min-height: 80px;
              border: none;
              border-radius: 8px;
              padding: 12px 16px;
              font-size: 14px;
              outline: none;
              resize: none;
              font-family: inherit;
              line-height: 1.4;
              background-color: #f5f5f5;
            }
          }
        }
      }
  
  .generate-menu {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    
    .left-box {
          display: flex;
          align-items: center;
          gap: 8px;
          flex-wrap: wrap;
          justify-content: flex-start;
      
      .task-list-btn {
        width: 36px;
        height: 36px;
        border: 1px solid #ddd;
        border-radius: 8px;
        background: #fff;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s;
        
        &:hover {
          border-color: #000;
          background: #f5f5f5;
        }
        
        svg {
          width: 16px;
          height: 16px;
          stroke: currentColor;
          stroke-width: 2;
          stroke-linecap: round;
          stroke-linejoin: round;
        }
      }
      
      .custom-select {
        position: relative;
        margin-right: 8px;
        min-width: 120px;
        
        &.lora-select {
          min-width: 220px;
          
          .select-header {
            .select-text {
              flex: 1;
              overflow: hidden;
              text-overflow: ellipsis;
              white-space: nowrap;
            }
          }
        }
        
        .select-header {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 16px;
          border: 1px solid #ddd;
          border-radius: 8px;
          font-size: 12px;
          color: #000;
          cursor: pointer;
          background: #fff;
          transition: all 0.3s;
          height: 36px;
          box-sizing: border-box;
          
          &:hover {
            border-color: #000;
            background: #f5f5f5;
          }
          
          .select-icon {
            font-size: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
          }
          
          .select-text {
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }
          
          .select-arrow {
            font-size: 10px;
            transition: transform 0.3s;
            margin-left: 8px;
            
            &.rotated {
              transform: rotate(180deg);
            }
          }
        }
        
        .select-dropdown {
          position: absolute;
          top: 100%;
          left: 0;
          min-width: 100%;
          max-height: 160px;
          margin-top: 4px;
          border: 1px solid #ddd;
          border-radius: 8px;
          background: #fff;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
          z-index: 100;
          overflow-y: auto;
          
          .dropdown-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 10px 16px;
            font-size: 12px;
            color: #000;
            cursor: pointer;
            transition: all 0.3s;
            
            &:hover {
              background: #f5f5f5;
            }
            
            &:first-child {
              border-top-left-radius: 8px;
              border-top-right-radius: 8px;
            }
            
            &:last-child {
              border-bottom-left-radius: 8px;
              border-bottom-right-radius: 8px;
            }
            
            .item-icon {
              font-size: 14px;
              display: flex;
              align-items: center;
              justify-content: center;
            }
          }
        }
      }
      
      .step-input-box {
        margin-right: 8px;
        
        .step-input {
          padding: 10px 12px;
          border: 1px solid #ddd;
          border-radius: 8px;
          font-size: 12px;
          color: #000;
          background: #fff;
          transition: all 0.3s;
          outline: none;
          width: 100px;
          height: 36px;
          box-sizing: border-box;
          
          /* 隐藏上下按钮 */
          -moz-appearance: textfield;
          
          &::-webkit-inner-spin-button,
          &::-webkit-outer-spin-button {
            -webkit-appearance: none;
            margin: 0;
          }
          
          &:hover {
            border-color: #000;
          }
          
          &:focus {
            border-color: #000;
          }
        }
      }
    }
    
    .right-box {
      display: flex;
      align-items: center;
      gap: 16px;
      flex-wrap: wrap;
      justify-content: flex-end;
      
      .generate-count {
        display: flex;
        align-items: center;
        gap: 8px;
        
        .count {
          font-size: 14px;
          color: #000;
        }
        
        .count-controls {
          display: flex;
          flex-direction: column;
          gap: 2px;
          
          button {
            width: 16px;
            height: 12px;
            border: none;
            background: none;
            font-size: 10px;
            color: #000;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            
            &:hover {
              color: #000;
            }
          }
        }
      }
      
      .generate-btn {
        padding: 8px 20px;
        border: none;
        border-radius: 8px;
        background: #000;
        color: #fff;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: background 0.3s;
        
        &:hover {
          background: #333;
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .generate-container {
    margin-bottom: 30px;
    
    .generate-title {
      font-size: 20px;
    }
  }
  
  .generate-content-list {
    width: 100%;
    padding: 16px;
    box-shadow: none;
    border-radius: 8px;
    
    &:hover {
      box-shadow: none;
    }
    
    .generate-content-input {
      flex-direction: column;
      
      >div {
        width: 100%;
        margin-right: 0;
        margin-bottom: 12px;
      }
      
      .file-select,
      .selected-image {
        margin-right: 0;
        width: 100px;
        margin: 0 auto 12px;
      }
    }
    
    .generate-menu {
      flex-direction: column;
      align-items: flex-start;
      gap: 12px;
      
      .left-box {
        flex-wrap: wrap;
        width: 100%;
      }
      
      .right-box {
        width: 100%;
        justify-content: space-between;
      }
    }
  }
  
  .task-list-panel {
    width: 100%;
    border-radius: 0;
  }
}
</style>
