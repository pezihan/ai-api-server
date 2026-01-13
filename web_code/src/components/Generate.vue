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
              <div v-if="isLoadingLora" class="lora-loading">
                <div class="loading-spinner"></div>
                <span>加载LoRA配置...</span>
              </div>
              <div v-else-if="loraError" class="lora-error">
                <span>{{ loraError }}</span>
                <button class="retry-btn" @click="loadLoraConfig">重试</button>
              </div>
              <div v-else-if="currentLoraList.length > 0" class="lora-list">
                <div class="dropdown-item" v-for="lora in currentLoraList" :key="lora.name" @click="toggleLora(lora.name)">
                  <span class="item-icon">
                    <svg v-if="isLoraSelected(lora.name)" width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                    <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                    </svg>
                  </span>
                  <span class="lora-name">{{ lora.name }}</span>
                  <div v-if="isLoraSelected(lora.name)" class="lora-strength-control" @click.stop>
                    <input type="number" :value="getLoraStrength(lora.name)" @input="updateLoraStrength(lora.name, $event)" min="0" max="2" step="0.1" class="strength-input" :disabled="isGenerating" @click.stop>
                  </div>
                </div>
              </div>
              <div v-else class="lora-empty">
                <span>当前生成类型暂无可用的LoRA模型</span>
              </div>
            </div>
          </div>
        </div>
        <div class="right-box">
          <button class="generate-btn" @click="generateImage" :disabled="isGenerating">
            <div class="button-content">
              <svg v-if="isGenerating" class="spin-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <path d="M12 6v6l4 2"></path>
              </svg>
              <span>{{ isGenerating ? '提交中...' : '提交' }}</span>
            </div>
          </button>
        </div>
      </div>
    </div>
  </div>
  
  
  <!-- 通知系统 -->
  <div class="notification-container">
    <div 
      v-for="notification in notifications" 
      :key="notification.id" 
      class="notification" 
      :class="notification.type"
    >
      <div class="notification-icon">
        <svg v-if="notification.type === 'success'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
          <polyline points="22 4 12 14.01 9 11.01"></polyline>
        </svg>
        <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="8" x2="12" y2="12"></line>
          <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
      </div>
      <div class="notification-message">{{ notification.message }}</div>
      <button class="notification-close" @click="removeNotification(notification.id)">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    </div>
  </div>
</template>

<script lang="ts">
import TaskList from './TaskList.vue'
import { post, postForm, getLoraConfig } from '../utils/api'

export default {
  name: 'Generate',
  components: {
    TaskList
  },
  mounted() {
    // 添加全局点击事件监听器，点击空白处关闭下拉菜单
    document.addEventListener('click', this.handleClickOutside)
    // 加载LoRA配置
    this.loadLoraConfig()
  },
  beforeUnmount() {
    // 移除全局点击事件监听器
    document.removeEventListener('click', this.handleClickOutside)
  },
  data() {
    return {
      generateCount: 1,
      generateType: '文生图',
      selectedLoras: [] as Array<{ name: string; strength: number }>,
      inferenceSteps: 9,
      generateSize: '竖',
      generateDuration: '5秒',
      selectedImage: null as string | null,
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
      sizes: [
        { label: '横', value: '横' },
        { label: '竖', value: '竖' },
        { label: '方', value: '方' }
      ],
      durations: [
        { label: '5秒', value: '5秒' },
        { label: '10秒', value: '10秒' },
        { label: '15秒', value: '15秒' }
      ],

      // 新增的API相关数据
      isGenerating: false,
      loraConfig: null as any,
      isLoadingLora: false,
      loraError: '',

      // LoRA类型映射
      loraTypeMap: {
        '文生图': 'z_image',
        '图生图': 'qwen_image_edit',
        '文生视频': 'wan_2_1_t2v',
        '图生视频': 'wan_2_2_i2v'
      },
      // 宽高比映射
      aspectRatioMap: {
        image: {
          vertical: { width: 544, height: 960 },
          horizontal: { width: 960, height: 544 },
          square: { width: 544, height: 544 }
        },
        video: {
          vertical: { width: 544, height: 960 },
          horizontal: { width: 960, height: 544 },
          square: { width: 544, height: 544 }
        }
      },
      // 生成参数
      formData: {
        seed: Math.floor(Math.random() * 1000000),
        width: 544,
        height: 960,
        num_frames: 81,
        video_duration: 5,
        aspect_ratio: 'vertical'
      },
      // 通知系统
      notifications: [] as Array<{
        id: number;
        type: 'success' | 'error';
        message: string;
        timestamp: number;
      }>
    }
  },
  computed: {
    // 根据当前生成类型获取对应的LoRA列表
    currentLoraList() {
      if (!this.loraConfig) return []
      const generateTypeKey = this.generateType as keyof typeof this.loraTypeMap
      const configKey = this.loraTypeMap[generateTypeKey]
      return this.loraConfig[configKey] || []
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
    handleClickOutside(event: MouseEvent) {
      const selectElements = (event.target as HTMLElement).closest('.custom-select')
      const taskListPanel = (event.target as HTMLElement).closest('.task-list-panel')
      const taskListBtn = (event.target as HTMLElement).closest('.task-list-btn')
      
      if (!selectElements) {
        // 点击的不是选择器内部，关闭所有下拉菜单
        Object.keys(this.dropdownOpen).forEach((key) => {
          this.dropdownOpen[key as keyof typeof this.dropdownOpen] = false
        })
      }
      
      if (!taskListPanel && !taskListBtn && this.showTaskList) {
        // 点击的不是任务列表内部或任务列表按钮，关闭任务列表
        this.showTaskList = false
      }
    },

    toggleDropdown(type: keyof typeof this.dropdownOpen, event: MouseEvent) {
      // 阻止事件冒泡，避免触发handleClickOutside
      event.stopPropagation()
      // 关闭所有下拉框
      Object.keys(this.dropdownOpen).forEach((key) => {
        this.dropdownOpen[key as keyof typeof this.dropdownOpen] = false
      })
      // 打开当前点击的下拉框
      this.dropdownOpen[type] = true
    },

    selectType(type: string) {
      this.generateType = type
      this.dropdownOpen.type = false
      // 清空LoRA选择
      this.selectedLoras = []
      // 根据生成类型更新默认步数
      this.updateDefaultSteps()
    },
    selectSize(size: string) {
      this.generateSize = size
      this.dropdownOpen.size = false
      // 更新宽高比
      this.updateAspectRatio()
    },
    selectDuration(duration: string) {
      this.generateDuration = duration
      this.dropdownOpen.duration = false
      // 更新视频时长和帧数
      this.updateVideoDuration()
    },
    updateDefaultSteps() {
      switch (this.generateType) {
        case '文生图':
          this.inferenceSteps = 9
          break
        case '图生图':
          this.inferenceSteps = 20
          break
        case '文生视频':
        case '图生视频':
          this.inferenceSteps = 4
          break
      }
    },
    updateAspectRatio() {
      let aspectRatio: 'horizontal' | 'vertical' | 'square' = 'horizontal'
      switch (this.generateSize) {
        case '横':
          aspectRatio = 'horizontal'
          break
        case '竖':
          aspectRatio = 'vertical'
          break
        case '方':
          aspectRatio = 'square'
          break
      }
      
      const isVideo = ['文生视频', '图生视频'].includes(this.generateType)
      const type = isVideo ? 'video' : 'image'
      
      this.formData.aspect_ratio = aspectRatio
      this.formData.width = this.aspectRatioMap[type][aspectRatio].width
      this.formData.height = this.aspectRatioMap[type][aspectRatio].height
    },
    updateVideoDuration() {
      const duration = parseInt(this.generateDuration) || 5
      this.formData.video_duration = duration
      
      switch (duration) {
        case 5:
          this.formData.num_frames = 81
          break
        case 10:
          this.formData.num_frames = 161
          break
        case 15:
          this.formData.num_frames = 241
          break
        default:
          this.formData.num_frames = 81
      }
    },
    toggleLora(loraName: string) {
      const existingIndex = this.selectedLoras.findIndex(item => item.name === loraName)
      if (existingIndex > -1) {
        this.selectedLoras.splice(existingIndex, 1)
      } else {
        this.selectedLoras.push({ name: loraName, strength: 1.0 })
      }
    },
    isLoraSelected(loraName: string) {
      return this.selectedLoras.some(item => item.name === loraName)
    },
    // 获取LoRA强度
    getLoraStrength(loraName: string) {
      const lora = this.selectedLoras.find(item => item.name === loraName)
      return lora ? lora.strength : 1.0
    },
    // 更新LoRA强度
    updateLoraStrength(loraName: string, event: Event) {
      const target = event.target as HTMLInputElement
      const strength = parseFloat(target.value)
      const lora = this.selectedLoras.find(item => item.name === loraName)
      if (lora) {
        lora.strength = strength
      }
    },
    // 获取LoRA配置
    async loadLoraConfig() {
      try {
        this.isLoadingLora = true
        this.loraError = ''
        
        const response = await getLoraConfig()
        if (response.success && response.data) {
          this.loraConfig = response.data
        } else {
          this.loraError = response.error || '获取LoRA配置失败'
        }
      } catch (error) {
        console.error('加载LoRA配置失败:', error)
        this.loraError = error instanceof Error ? error.message : '网络请求失败'
      } finally {
        this.isLoadingLora = false
      }
    },
    // 生成图片的逻辑
    async generateImage() {
      try {
        this.isGenerating = true
        
        const prompt = (this.$refs.promptInput as HTMLTextAreaElement)?.value
        if (!prompt) {
          this.addNotification('error', '请输入提示词')
          this.isGenerating = false
          return
        }
        
        // 更新宽高比和视频时长
        this.updateAspectRatio()
        this.updateVideoDuration()
        
        // 文生图
        if (this.generateType === '文生图') {
          const requestData = {
            prompt: prompt,
            negative_prompt: this.negativePrompt,
            seed: this.formData.seed,
            width: this.formData.width,
            height: this.formData.height,
            steps: this.inferenceSteps || 9,
            loras: this.selectedLoras
          }
          
          const response = await post('/image/text2img', requestData)
          
          if (response.success && response.data) {
            this.addNotification('success', `生成成功！任务ID: ${response.data.task_id}`)
            // 触发任务提交成功事件
            this.showTaskList = true
          } else {
            this.addNotification('error', `生成失败: ${response.error || '未知错误'}`)
          }
          return
        }
        
        // 图生图
        if (this.generateType === '图生图') {
          if (!this.selectedImage) {
            this.addNotification('error', '请上传参考图片')
            this.isGenerating = false
            return
          }
          
          // 准备图片文件
          const imageFile = this.dataURLtoFile(this.selectedImage, 'reference.jpg')
          
          // 先上传图片
          const formDataForUpload = new FormData()
          formDataForUpload.append('file', imageFile)
          
          // 发送上传请求
          const uploadResponse = await postForm('/upload/', formDataForUpload)
          
          if (!uploadResponse.success || !uploadResponse.data?.file_path) {
            this.addNotification('error', `图片上传失败: ${uploadResponse.error || '未知错误'}`)
            this.isGenerating = false
            return
          }
          
          // 准备图生图请求数据
          const requestData = {
            prompt: prompt,
            negative_prompt: this.negativePrompt,
            seed: this.formData.seed,
            width: this.formData.width,
            height: this.formData.height,
            steps: this.inferenceSteps || 20,
            image_path: uploadResponse.data.file_path,
            loras: this.selectedLoras
          }
          
          // 发送图生图请求
          const response = await post('/image/img2img', requestData)
          
          if (response.success && response.data) {
            this.addNotification('success', `生成成功！任务ID: ${response.data.task_id}`)
            // 触发任务提交成功事件
            this.showTaskList = true
          } else {
            this.addNotification('error', `生成失败: ${response.error || '未知错误'}`)
          }
          return
        }
        
        // 文生视频
        if (this.generateType === '文生视频') {
          const requestData = {
            prompt: prompt,
            negative_prompt: this.negativePrompt,
            seed: this.formData.seed,
            width: this.formData.width,
            height: this.formData.height,
            steps: this.inferenceSteps || 4,
            num_frames: this.formData.num_frames,
            loras: this.selectedLoras
          }
          
          // 发送请求
          const response = await post('/video/text2video', requestData)
          
          if (response.success && response.data) {
            this.addNotification('success', `生成成功！任务ID: ${response.data.task_id}`)
            // 触发任务提交成功事件
            this.showTaskList = true
          } else {
            this.addNotification('error', `生成失败: ${response.error || '未知错误'}`)
          }
          return
        }
        
        // 图生视频
        if (this.generateType === '图生视频') {
          if (!this.selectedImage) {
            this.addNotification('error', '请上传参考图片')
            this.isGenerating = false
            return
          }
          
          // 准备图片文件
          const imageFile = this.dataURLtoFile(this.selectedImage, 'reference.jpg')
          
          // 先上传图片
          const formDataForUpload = new FormData()
          formDataForUpload.append('file', imageFile)
          
          // 发送上传请求
          const uploadResponse = await postForm('/upload/', formDataForUpload)
          
          if (!uploadResponse.success || !uploadResponse.data?.file_path) {
            this.addNotification('error', `图片上传失败: ${uploadResponse.error || '未知错误'}`)
            this.isGenerating = false
            return
          }
          
          // 准备图生视频请求数据
          const requestData = {
            prompt: prompt,
            negative_prompt: this.negativePrompt,
            seed: this.formData.seed,
            width: this.formData.width,
            height: this.formData.height,
            steps: this.inferenceSteps || 4,
            num_frames: this.formData.num_frames,
            image_path: uploadResponse.data.file_path,
            loras: this.selectedLoras
          }
          
          // 发送图生视频请求
          const response = await post('/video/img2video', requestData)
          
          if (response.success && response.data) {
            this.addNotification('success', `生成成功！任务ID: ${response.data.task_id}`)
            // 触发任务提交成功事件
            this.showTaskList = true
          } else {
            this.addNotification('error', `生成失败: ${response.error || '未知错误'}`)
          }
          return
        }
        
      } catch (error) {
        console.error('生成失败:', error)
        this.addNotification('error', `生成失败: ${error instanceof Error ? error.message : '未知错误'}`)
      } finally {
        this.isGenerating = false
        // 生成完成后重置种子
        this.formData.seed = Math.floor(Math.random() * 1000000)
      }
    },
    // 将dataURL转换为File对象
    dataURLtoFile(dataurl: string, filename: string) {
      const arr = dataurl.split(',')
      const match = arr[0].match(/:(.*?);/)
      const mime = match ? match[1] : ''
      const bstr = atob(arr[1])
      let n = bstr.length
      const u8arr = new Uint8Array(n)
      
      while (n--) {
        u8arr[n] = bstr.charCodeAt(n)
      }
      
      return new File([u8arr], filename, { type: mime })
    },
    openFileSelector() {
      (this.$refs.fileInput as HTMLInputElement).click()
    },
    handleFileSelect(event: Event) {
      const file = (event.target as HTMLInputElement).files?.[0]
      if (file) {
        const reader = new FileReader()
        reader.onload = (e) => {
          this.selectedImage = e.target?.result as string | null
        }
        reader.readAsDataURL(file)
      }
    },
    deleteImage() {
      this.selectedImage = null as string | null
      (this.$refs.fileInput as HTMLInputElement).value = ''
    },
    toggleTaskList(event: MouseEvent) {
      event.stopPropagation()
      this.showTaskList = !this.showTaskList
    },
    // 通知系统方法
    addNotification(type: 'success' | 'error', message: string) {
      const id = Date.now()
      this.notifications.push({
        id,
        type,
        message,
        timestamp: id
      })
      
      // 3秒后自动移除通知
      setTimeout(() => {
        this.removeNotification(id)
      }, 3000)
    },
    removeNotification(id: number) {
      const index = this.notifications.findIndex(notification => notification.id === id)
      if (index > -1) {
        this.notifications.splice(index, 1)
      }
    },
    clearNotifications() {
      this.notifications = []
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
              
              .lora-name {
                flex: 1;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
              }
              
              .lora-strength-control {
                margin-left: auto;
                display: flex;
                align-items: center;
                
                .strength-input {
                  width: 60px;
                  padding: 4px 8px;
                  border: 1px solid #ddd;
                  border-radius: 4px;
                  font-size: 12px;
                  background-color: #fff;
                  transition: all 0.3s;
                  
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
                  
                  &:disabled {
                    opacity: 0.6;
                    cursor: not-allowed;
                  }
                }
              }
            }
            
            /* LoRA错误状态样式 */
            .lora-error {
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
              padding: 20px 16px;
              text-align: center;
              background-color: #fff2f0;
              border: 1px solid #ffccc7;
              border-radius: 8px;
              margin: 8px;
              
              span {
                display: block;
                color: #cf1322;
                font-size: 12px;
                margin-bottom: 12px;
                line-height: 1.4;
              }
              
              .retry-btn {
                padding: 6px 12px;
                background-color: #cf1322;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                cursor: pointer;
                transition: background-color 0.3s;
                
                &:hover {
                  background-color: #a8071a;
                }
                
                &:active {
                  background-color: #870012;
                }
              }
            }
            
            /* LoRA加载状态样式 */
            .lora-loading {
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
              padding: 20px 16px;
              gap: 10px;
              
              .loading-spinner {
                width: 20px;
                height: 20px;
                border: 2px solid #f3f3f3;
                border-top: 2px solid #3498db;
                border-radius: 50%;
                animation: spin 1s linear infinite;
              }
              
              span {
                font-size: 12px;
                color: #666;
              }
            }
            
            /* LoRA空状态样式 */
            .lora-empty {
              padding: 20px 16px;
              text-align: center;
              color: #999;
              font-size: 12px;
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
          min-width: 100px;
          
          .button-content {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
          }
          
          .spin-icon {
            width: 16px;
            height: 16px;
            animation: spin 1s linear infinite;
          }
          
          &:hover {
            background: #333;
          }
          
          &:disabled {
            background: #666;
            cursor: not-allowed;
          }
        }
        
        .regenerate-btn {
          padding: 8px 20px;
          border: 1px solid #ddd;
          border-radius: 8px;
          background: #fff;
          color: #000;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.3s;
          
          &:hover {
            border-color: #000;
            background: #f5f5f5;
          }
        }
      }
  }
}

.notification-container {
  position: fixed;
  top: 20px;
  right: 20px;
  left: 20px;
  z-index: 1000;
  max-width: 30%;
  overflow: hidden;
  margin: 0 auto;
}

.notification {
  display: flex;
  align-items: center;
  padding: 10px 14px;
  margin-bottom: 8px;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  animation: slideInMobile 0.3s ease-out forwards, fadeOutMobile 0.3s ease-in 2.7s forwards;
  transition: all 0.3s ease;
  min-width: auto;
  max-width: 100%;
  transform: translateY(-100%);
}
.notification.success {
  background-color: #f6ffed;
  border: 1px solid #b7eb8f;
  color: #389e0d;
}

.notification.error {
  background-color: #fff2f0;
  border: 1px solid #ffccc7;
  color: #cf1322;
}

.notification-icon {
  margin-right: 8px;
  flex-shrink: 0;
  width: 12px;
  height: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.notification-icon svg {
  width: 100%;
  height: 100%;
  stroke-width: 1.5;
}

.notification-message {
  flex: 1;
  font-size: 13px;
  line-height: 1.3;
  word-wrap: break-word;
}

.notification-close {
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px;
  margin-left: 6px;
  flex-shrink: 0;
  opacity: 0.6;
  transition: opacity 0.2s ease;
}

.notification-close:hover {
  opacity: 1;
}

.notification-close svg {
  width: 12px;
  height: 12px;
}

@keyframes slideInMobile {
    from {
      transform: translateY(-100%);
      opacity: 0;
    }
    to {
      transform: translateY(0);
      opacity: 1;
    }
  }

  @keyframes fadeOutMobile {
    from {
      opacity: 1;
      transform: translateY(0);
    }
    to {
      opacity: 0;
      transform: translateY(-20px);
    }
  }

  /* 加载动画 */
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

/* 响应式设计 */
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

  @keyframes slideInDesktop {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }

  @keyframes fadeOutDesktop {
    from {
      opacity: 1;
      transform: translateX(0);
    }
    to {
      opacity: 0;
      transform: translateX(20px);
    }
  }
  .notification-container {
    max-width: 100%;
  }
}
</style>
