<template>
  <div class="generate-container">
    <!-- <h2 class="generate-title">开启你的 <span class="generate-title-highlight">图片生成</span><span class="generate-title-arrow">▼</span> 即刻造梦！</h2> -->
  </div>
  <div class="generate-content-list">
    <div class="generate-content-input">
      <div v-if="['图生图', '图生视频'].includes(generateType)">
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
        <textarea ref="promptInput" placeholder="请描述你想生成的图片" rows="6"></textarea>
      </div>
    </div>
    <div class="generate-menu">
      <div class="left-box">
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
            {{ generateType }}
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
            {{ generateSize }}
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
            <span class="select-icon"></span>
            {{ generateDuration }}
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
        <div class="custom-select">
          <div class="select-header" @click="toggleDropdown('lora', $event)">
            <span class="select-icon">🎨</span>
            {{ selectedLoras.length > 0 ? `已选择 ${selectedLoras.length} 个` : '选择 Lora' }}
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
</template>

<script lang="ts">
export default {
  name: 'Generate',
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
        { label: 'lora3', value: 'lora3' }
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
      if (!selectElements) {
        // 点击的不是选择器内部，关闭所有下拉菜单
        Object.keys(this.dropdownOpen).forEach(key => {
          this.dropdownOpen[key] = false
        })
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
    }
  }
}
</script>

<style lang="scss" scoped>
.generate-container {
  text-align: center;
  margin-bottom: 24px;
  
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
  max-width: 60%;
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
            resize: vertical;
            font-family: inherit;
            line-height: 1.4;
          }
        }
      }
  
  .generate-menu {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .left-box {
          display: flex;
          align-items: center;
          gap: 8px;
      
      .custom-select {
        position: relative;
        margin-right: 8px;
        min-width: 120px;
        
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
          white-space: nowrap;
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
          
          .select-arrow {
            font-size: 10px;
            transition: transform 0.3s;
            margin-left: auto;
            
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
          margin-top: 4px;
          border: 1px solid #ddd;
          border-radius: 8px;
          background: #fff;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
          z-index: 100;
          
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
        border-radius: 16px;
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
  .generate-content-list {
    padding: 16px;
    
    .generate-menu {
      flex-direction: column;
      align-items: flex-start;
      gap: 12px;
      
      .left-box {
        flex-wrap: wrap;
      }
      
      .right-box {
        width: 100%;
        justify-content: space-between;
      }
    }
  }
}
</style>
