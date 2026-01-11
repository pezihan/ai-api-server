<script setup lang="ts">
import { ref, reactive, watch, onMounted, computed } from 'vue';
import { post, postForm, getLoraConfig } from '../utils/api';
import type { ApiResponse, LoraConfigResponse, LoraConfig } from '../utils/api';

// 生成类型和模式（组件内部管理）
const generateType = ref('image'); // image 或 video
const generateMode = ref('text2img'); // text2img, img2img, text2video, img2video

// 生成类型映射
const generateTypes = [
  { label: '文生图', value: 'text2img', type: 'image' },
  { label: '图生图', value: 'img2img', type: 'image' },
  { label: '文生视频', value: 'text2video', type: 'video' },
  { label: '图生视频', value: 'img2video', type: 'video' }
];

// 生成参数
const formData = reactive({
  prompt: '',
  negative_prompt: '',
  seed: Math.floor(Math.random() * 1000000),
  width: 544,
  height: 960,
  num_frames: 81,
  video_duration: 5, // 视频时长（秒）
  aspect_ratio: 'vertical' // vertical, horizontal, square
});

// 图片上传
const uploadedImage = ref<File | null>(null);
const imagePreviewUrl = ref('');

// 加载状态
const isGenerating = ref(false);
const generationMessage = ref('');

// LoRA配置
const loraConfig = ref<LoraConfigResponse | null>(null);
const selectedLoras = ref<Array<{ name: string; strength: number }>>([]);
const isLoadingLora = ref(false);
const loraError = ref('');

// LoRA类型映射
const loraTypeMap = {
  text2img: 'z_image',
  img2img: 'qwen_image_edit',
  text2video: 'wan_2_1_t2v',
  img2video: 'wan_2_2_i2v'
};

// 宽高比映射（根据生成类型）
const aspectRatioMap = {
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
};

// 监听生成模式变化，自动更新生成类型
watch(generateMode, (newMode) => {
  selectedLoras.value = [];
  const selectedType = generateTypes.find(type => type.value === newMode);
  if (selectedType) {
    generateType.value = selectedType.type;
  }
});

// 监听生成类型变化，自动应用对应类型的宽高比
watch(generateType, () => {
  // 应用当前宽高比对应的宽高值
  const currentRatio = formData.aspect_ratio;
  formData.width = aspectRatioMap[generateType.value as 'image' | 'video'][currentRatio as 'vertical' | 'horizontal' | 'square'].width;
  formData.height = aspectRatioMap[generateType.value as 'image' | 'video'][currentRatio as 'vertical' | 'horizontal' | 'square'].height;
});

// 处理图片上传
const handleImageUpload = (event: Event) => {
  const input = event.target as HTMLInputElement;
  if (input.files && input.files[0]) {
    uploadedImage.value = input.files[0];
    // 创建预览URL
    imagePreviewUrl.value = URL.createObjectURL(uploadedImage.value);
  }
};

// 清除上传的图片
const clearUploadedImage = () => {
  uploadedImage.value = null;
  imagePreviewUrl.value = '';
};

// 切换宽高比
const changeAspectRatio = (ratio: string) => {
  formData.aspect_ratio = ratio;
  formData.width = aspectRatioMap[generateType.value as 'image' | 'video'][ratio as 'vertical' | 'horizontal' | 'square'].width;
  formData.height = aspectRatioMap[generateType.value as 'image' | 'video'][ratio as 'vertical' | 'horizontal' | 'square'].height;
};

// 切换视频时长
const changeVideoDuration = (duration: number) => {
  formData.video_duration = duration;
  // 根据时长设置对应帧数
  switch (duration) {
    case 5:
      formData.num_frames = 81;
      break;
    case 10:
      formData.num_frames = 161;
      break;
    case 15:
      formData.num_frames = 241;
      break;
  }
};

// 定义事件
const emit = defineEmits<{
  (e: 'task-submitted'): void;
}>();

// 提交生成请求
const submitGeneration = async () => {
  try {
    isGenerating.value = true;
    generationMessage.value = '正在生成...';

    // 文生图
      if (generateType.value === 'image' && generateMode.value === 'text2img') {
        // 准备请求数据
        const requestData = {
          prompt: formData.prompt,
          negative_prompt: formData.negative_prompt,
          seed: formData.seed,
          width: formData.width,
          height: formData.height,
          loras: selectedLoras.value
        };

      // 发送请求
      const response = await post<{ task_id: string }>('/image/text2img', requestData);

      if (response.success && response.data) {
        generationMessage.value = `生成成功！任务ID: ${response.data.task_id}`;
        // 触发任务提交成功事件
        emit('task-submitted');
      } else {
        generationMessage.value = `生成失败: ${response.error || '未知错误'}`;
      }
      return;
    }

    // 图生图
    if (generateType.value === 'image' && generateMode.value === 'img2img') {
      // 处理图片上传
      if (!uploadedImage.value) {
        generationMessage.value = '请上传参考图片';
        return;
      }

      // 先上传图片
      const formDataForUpload = new FormData();
      formDataForUpload.append('file', uploadedImage.value);

      // 发送上传请求
      const uploadResponse = await postForm<{ file_path: string }>('/upload/', formDataForUpload);

      if (!uploadResponse.success || !uploadResponse.data?.file_path) {
        generationMessage.value = `图片上传失败: ${uploadResponse.error || '未知错误'}`;
        return;
      }

      // 准备图生图请求数据
        const requestData = {
          prompt: formData.prompt,
          negative_prompt: formData.negative_prompt,
          seed: formData.seed,
          width: formData.width,
          height: formData.height,
          image_path: uploadResponse.data.file_path,
          loras: selectedLoras.value
        };

      // 发送图生图请求
      const response = await post<{ task_id: string }>('/image/img2img', requestData);

      if (response.success && response.data) {
        generationMessage.value = `生成成功！任务ID: ${response.data.task_id}`;
        // 触发任务提交成功事件
        emit('task-submitted');
      } else {
        generationMessage.value = `生成失败: ${response.error || '未知错误'}`;
      }
      return;
    }

    // 文生视频
      if (generateType.value === 'video' && generateMode.value === 'text2video') {
        // 准备请求数据
        const requestData = {
          prompt: formData.prompt,
          negative_prompt: formData.negative_prompt,
          seed: formData.seed,
          width: formData.width,
          height: formData.height,
          num_frames: formData.num_frames,
          loras: selectedLoras.value
        };

      // 发送请求
      const response = await post<{ task_id: string }>('/video/text2video', requestData);

      if (response.success && response.data) {
        generationMessage.value = `生成成功！任务ID: ${response.data.task_id}`;
        // 触发任务提交成功事件
        emit('task-submitted');
      } else {
        generationMessage.value = `生成失败: ${response.error || '未知错误'}`;
      }
      return;
    }

    // 图生视频
    if (generateType.value === 'video' && generateMode.value === 'img2video') {
      // 处理图片上传
      if (!uploadedImage.value) {
        generationMessage.value = '请上传参考图片';
        return;
      }

      // 先上传图片
      const formDataForUpload = new FormData();
      formDataForUpload.append('file', uploadedImage.value);

      // 发送上传请求
      const uploadResponse = await postForm<{ file_path: string }>('/upload/', formDataForUpload);

      if (!uploadResponse.success || !uploadResponse.data?.file_path) {
        generationMessage.value = `图片上传失败: ${uploadResponse.error || '未知错误'}`;
        return;
      }

      // 准备图生视频请求数据
        const requestData = {
          prompt: formData.prompt,
          negative_prompt: formData.negative_prompt,
          seed: formData.seed,
          width: formData.width,
          height: formData.height,
          num_frames: formData.num_frames,
          image_path: uploadResponse.data.file_path,
          loras: selectedLoras.value
        };

      // 发送图生视频请求
      const response = await post<{ task_id: string }>('/video/img2video', requestData);

      if (response.success && response.data) {
        generationMessage.value = `生成成功！任务ID: ${response.data.task_id}`;
        // 触发任务提交成功事件
        emit('task-submitted');
      } else {
        generationMessage.value = `生成失败: ${response.error || '未知错误'}`;
      }
      return;
    }

  } catch (error) {
    console.error('生成失败:', error);
    generationMessage.value = `生成失败: ${error instanceof Error ? error.message : '未知错误'}`;
  } finally {
    isGenerating.value = false;
  }
};

// 获取LoRA配置
const loadLoraConfig = async () => {
  try {
    isLoadingLora.value = true;
    loraError.value = '';
    
    const response = await getLoraConfig();
    if (response.success && response.data) {
      loraConfig.value = response.data;
    } else {
      loraError.value = response.error || '获取LoRA配置失败';
    }
  } catch (error) {
    console.error('加载LoRA配置失败:', error);
    loraError.value = error instanceof Error ? error.message : '网络请求失败';
  } finally {
    isLoadingLora.value = false;
  }
};

// 根据当前生成模式获取对应的LoRA列表
const currentLoraList = computed(() => {
  if (!loraConfig.value) return [];
  
  const configKey = loraTypeMap[generateMode.value as keyof typeof loraTypeMap];
  return loraConfig.value[configKey as keyof LoraConfigResponse] || [];
});

// 组件挂载时加载LoRA配置
onMounted(() => {
  loadLoraConfig();
});

// 重新生成（使用相同参数）
const regenerate = () => {
  formData.seed = Math.floor(Math.random() * 1000000);
  submitGeneration();
};

// 处理LoRA选择切换
const handleLoraToggle = (loraName: string) => {
  const existingIndex = selectedLoras.value.findIndex(item => item.name === loraName);
  if (existingIndex >= 0) {
    // 如果已存在，则移除
    selectedLoras.value.splice(existingIndex, 1);
  } else {
    // 如果不存在，则添加，默认强度为1.0
    selectedLoras.value.push({ name: loraName, strength: 1.0 });
  }
};

// 检查LoRA是否被选中
const isLoraSelected = (loraName: string) => {
  return selectedLoras.value.some(item => item.name === loraName);
};

// 获取LoRA强度
const getLoraStrength = (loraName: string) => {
  const lora = selectedLoras.value.find(item => item.name === loraName);
  return lora ? lora.strength : 1.0;
};

// 更新LoRA强度
const updateLoraStrength = (loraName: string, event: Event) => {
  const target = event.target as HTMLInputElement;
  const strength = parseFloat(target.value);
  const lora = selectedLoras.value.find(item => item.name === loraName);
  if (lora) {
    lora.strength = strength;
  }
};
</script>

<template>
  <div class="generate-panel">
    <div class="panel-content">
      <!-- 提示词输入 -->
      <div class="form-group">
        <div class="form-label-container">
          <label for="prompt" class="form-label">提示词</label>
          <span class="label-helper">详细描述您想要生成的内容</span>
        </div>
        <textarea
          id="prompt"
          v-model="formData.prompt"
          class="form-textarea"
          placeholder="例如：一只可爱的柴犬在草地上奔跑，阳光明媚，高质量，4K"
          rows="4"
          :disabled="isGenerating"
        ></textarea>
      </div>

      <!-- 生成类型选择 -->
      <div class="form-group">
        <div class="form-label-container">
          <label class="form-label">生成类型</label>
          <span class="label-helper">选择生成内容的类型</span>
        </div>
        <div class="generate-type-selector">
          <select
            v-model="generateMode"
            class="generate-type-select"
            :disabled="isGenerating"
          >
            <option
              v-for="type in generateTypes"
              :key="type.value"
              :value="type.value"
            >
              {{ type.label }}
            </option>
          </select>
        </div>
      </div>

      <!-- 反向提示词 -->
      <div class="form-group">
        <div class="form-label-container">
          <label for="negative_prompt" class="form-label">反向提示词</label>
          <span class="label-helper">输入不想在生成结果中出现的内容</span>
        </div>
        <textarea
          id="negative_prompt"
          v-model="formData.negative_prompt"
          class="form-textarea"
          placeholder="例如：模糊，低质量，变形，水印"
          rows="2"
          :disabled="isGenerating"
        ></textarea>
      </div>

      <!-- 图片上传（图生图/图生视频） -->
      <div class="form-group" v-if="generateMode === 'img2img' || generateMode === 'img2video'">
        <div class="form-label-container">
          <label class="form-label">参考图片</label>
          <span class="label-helper">上传一张参考图片</span>
        </div>
        <div class="image-upload-container">
          <input
            type="file"
            id="image_upload"
            accept="image/*"
            class="image-upload-input"
            @change="handleImageUpload"
            :disabled="isGenerating"
          />
          <label for="image_upload" class="image-upload-label" :disabled="isGenerating">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              <circle cx="8.5" cy="8.5" r="1.5"></circle>
              <polyline points="21 15 16 10 5 21"></polyline>
            </svg>
            <span>{{ uploadedImage ? uploadedImage.name : '点击上传图片或拖拽到此处' }}</span>
          </label>
          <button 
            class="clear-image-btn" 
            @click="clearUploadedImage" 
            v-if="uploadedImage"
            :disabled="isGenerating"
            title="清除图片"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <!-- 图片预览 -->
        <div class="image-preview" v-if="imagePreviewUrl">
          <div class="preview-wrapper">
            <img :src="imagePreviewUrl" alt="参考图片预览" />
          </div>
        </div>
      </div>

      <!-- 宽高比选择（除图生视频外） -->
      <div class="form-group" v-if="generateMode !== 'img2video'">
        <div class="form-label-container">
          <label class="form-label">{{ generateType === 'video' ? '视频比例' : '图片比例' }}</label>
          <span class="label-helper">选择生成{{ generateType === 'video' ? '视频' : '图片' }}的宽高比例</span>
        </div>
        <div class="aspect-buttons">
          <button
            class="aspect-btn"
            :class="{ active: formData.aspect_ratio === 'vertical' }"
            @click="changeAspectRatio('vertical')"
            :disabled="isGenerating"
            :title="`竖屏 (${aspectRatioMap[generateType as 'image' | 'video'][formData.aspect_ratio as 'vertical' | 'horizontal' | 'square'].width}x${aspectRatioMap[generateType as 'image' | 'video'][formData.aspect_ratio as 'vertical' | 'horizontal' | 'square'].height})`"
          >
            <div class="aspect-icon vertical"></div>
            <span>竖屏</span>
          </button>
          <button
            class="aspect-btn"
            :class="{ active: formData.aspect_ratio === 'horizontal' }"
            @click="changeAspectRatio('horizontal')"
            :disabled="isGenerating"
            :title="`横屏 (${aspectRatioMap[generateType as 'image' | 'video'][formData.aspect_ratio as 'vertical' | 'horizontal' | 'square'].width}x${aspectRatioMap[generateType as 'image' | 'video'][formData.aspect_ratio as 'vertical' | 'horizontal' | 'square'].height})`"
          >
            <div class="aspect-icon horizontal"></div>
            <span>横屏</span>
          </button>
          <button
            class="aspect-btn"
            :class="{ active: formData.aspect_ratio === 'square' }"
            @click="changeAspectRatio('square')"
            :disabled="isGenerating"
            :title="`方形 (${aspectRatioMap[generateType as 'image' | 'video'][formData.aspect_ratio as 'vertical' | 'horizontal' | 'square'].width}x${aspectRatioMap[generateType as 'image' | 'video'][formData.aspect_ratio as 'vertical' | 'horizontal' | 'square'].height})`"
          >
            <div class="aspect-icon square"></div>
            <span>方形</span>
          </button>
        </div>
      </div>

      <!-- 视频时长选择（仅视频生成） -->
      <div class="form-group" v-if="generateType === 'video'">
        <div class="form-label-container">
          <label class="form-label">视频时长</label>
          <span class="label-helper">选择生成视频的时长</span>
        </div>
        <div class="duration-buttons">
          <button
            class="duration-btn"
            :class="{ active: formData.video_duration === 5 }"
            @click="changeVideoDuration(5)"
            :disabled="isGenerating"
            :title="`5秒 (81帧)`"
          >
            <span>5秒</span>
          </button>
          <button
            class="duration-btn"
            :class="{ active: formData.video_duration === 10 }"
            @click="changeVideoDuration(10)"
            :disabled="isGenerating"
            :title="`10秒 (161帧)`"
          >
            <span>10秒</span>
          </button>
          <button
            class="duration-btn"
            :class="{ active: formData.video_duration === 15 }"
            @click="changeVideoDuration(15)"
            :disabled="isGenerating"
            :title="`15秒 (241帧)`"
          >
            <span>15秒</span>
          </button>
        </div>
      </div>

      <!-- LoRA选择 -->
      <div class="form-group">
        <div class="form-label-container">
          <label class="form-label">LoRA模型</label>
          <span class="label-helper">选择要应用的LoRA模型（可多选）</span>
        </div>
        <div class="lora-selection">
          <!-- LoRA加载状态 -->
          <div v-if="isLoadingLora" class="lora-loading">
            <div class="loading-spinner"></div>
            <span>加载LoRA配置...</span>
          </div>
          
          <!-- LoRA加载错误 -->
          <div v-else-if="loraError" class="lora-error">
            <span>{{ loraError }}</span>
            <button class="retry-btn" @click="loadLoraConfig" :disabled="isGenerating">
              重试
            </button>
          </div>
          
          <!-- LoRA列表 -->
          <div v-else-if="currentLoraList.length > 0" class="lora-list">
            <div
              v-for="lora in currentLoraList"
              :key="lora.name"
              class="lora-item"
            >
              <label class="lora-checkbox">
                <input
                  type="checkbox"
                  :value="lora.name"
                  @change="handleLoraToggle(lora.name)"
                  :checked="isLoraSelected(lora.name)"
                  :disabled="isGenerating"
                />
                <span class="checkbox-custom"></span>
                <div class="lora-info">
                  <span class="lora-name">{{ lora.name }}</span>
                  <div class="lora-strength-control" v-if="isLoraSelected(lora.name)">
                    <label for="strength-{{ lora.name }}">强度:</label>
                    <input
                      id="strength-{{ lora.name }}"
                      type="number"
                      :value="getLoraStrength(lora.name)"
                      @input="updateLoraStrength(lora.name, $event)"
                      min="0"
                      max="2"
                      step="0.1"
                      :disabled="isGenerating"
                      class="strength-input"
                    />
                  </div>
                </div>
              </label>
            </div>
          </div>
          
          <!-- 无LoRA模型 -->
          <div v-else class="lora-empty">
            <span>当前生成类型暂无可用的LoRA模型</span>
          </div>
        </div>
      </div>

      <!-- 生成按钮 -->
      <div class="generate-controls">
        <button
          class="generate-btn primary"
          @click="submitGeneration"
          :disabled="isGenerating || !formData.prompt"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" v-if="isGenerating" class="spin-icon">
            <circle cx="12" cy="12" r="10"></circle>
            <path d="M12 6v6l4 2"></path>
          </svg>
          <span>{{ isGenerating ? '生成中...' : '开始生成' }}</span>
        </button>

        <button
          class="generate-btn secondary"
          @click="regenerate"
          :disabled="isGenerating || !formData.prompt"
          title="使用新种子重新生成"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="23 4 23 10 17 10"></polyline>
            <polyline points="1 20 1 14 7 14"></polyline>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
          </svg>
          <span>重新生成</span>
        </button>
      </div>

      <!-- 生成状态信息 -->
      <div class="generation-status" v-if="generationMessage">
        <div class="status-icon" :class="{ 'success': generationMessage.includes('成功'), 'error': generationMessage.includes('失败') }">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" v-if="generationMessage.includes('成功')">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" v-else-if="generationMessage.includes('失败')">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="15" y1="9" x2="9" y2="15"></line>
            <line x1="9" y1="9" x2="15" y2="15"></line>
          </svg>
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" v-else>
            <circle cx="12" cy="12" r="10"></circle>
            <path d="M12 6v6l4 2"></path>
          </svg>
        </div>
        <span class="status-text">{{ generationMessage }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
:root {
  --primary-color: #6366f1;
  --primary-hover: #4f46e5;
  --secondary-color: #6b7280;
  --secondary-hover: #4b5563;
  --success-color: #10b981;
  --error-color: #ef4444;
  --warning-color: #f59e0b;
  --bg-color: #ffffff;
  --bg-light: #f8fafc;
  --border-color: #e2e8f0;
  --border-focus: #cbd5e1;
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --text-helper: #94a3b8;
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.generate-panel {
  background-color: var(--bg-color);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
  border: 1px solid var(--border-color);
  transition: var(--transition);
  margin: 0;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
}

.generate-panel:hover {
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  border-color: var(--primary-color);
}

/* 移除了顶部的panel-header样式 */

.panel-content {
  padding: 32px;
}

.form-group {
  margin-bottom: 28px;
}

.form-label-container {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 12px;
}

.form-label {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 16px;
  line-height: 1.5;
}

.label-helper {
  font-size: 13px;
  color: var(--text-helper);
  line-height: 1.4;
}

.form-textarea {
  width: 100%;
  padding: 20px 24px;
  border: 2px solid var(--border-color);
  border-radius: var(--radius-xl);
  font-size: 16px;
  resize: vertical;
  transition: var(--transition);
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  color: var(--text-primary);
  font-family: inherit;
  line-height: 1.6;
  box-shadow: var(--shadow-sm);
}

.form-textarea:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.2);
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
}

.form-textarea::placeholder {
  color: var(--text-helper);
  font-style: italic;
  opacity: 0.8;
}

.form-textarea:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
}

/* 图片上传 */
.image-upload-container {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
}

.image-upload-input {
  display: none;
}

.image-upload-label {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 32px;
  width: 100%;
  background-color: var(--bg-light);
  color: var(--text-secondary);
  border: 2px dashed var(--border-color);
  border-radius: var(--radius-lg);
  cursor: pointer;
  font-size: 16px;
  transition: var(--transition);
  text-align: center;
}

.image-upload-label:hover {
  background-color: rgba(99, 102, 241, 0.05);
  border-color: var(--primary-color);
  color: var(--primary-color);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.image-upload-label svg {
  width: 32px;
  height: 32px;
  opacity: 0.7;
  transition: var(--transition);
}

.image-upload-label:hover svg {
  opacity: 1;
  transform: scale(1.1);
}

.clear-image-btn {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background-color: var(--error-color);
  color: white;
  border: none;
  border-radius: 50%;
}

/* LoRA选择样式 */
.lora-selection {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border: 2px solid var(--border-color);
  border-radius: var(--radius-xl);
  padding: 20px;
  transition: var(--transition);
  max-height: 300px;
  overflow-y: auto;
}

.lora-selection:hover {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
}

.lora-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px 20px;
  color: var(--text-secondary);
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--border-color);
  border-top: 2px solid var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.lora-error {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  background-color: rgba(239, 68, 68, 0.1);
  border-left: 4px solid var(--error-color);
  border-radius: var(--radius-md);
  color: var(--error-color);
}

.retry-btn {
  padding: 8px 16px;
  background-color: var(--error-color);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-size: 14px;
  cursor: pointer;
  transition: var(--transition);
}

.retry-btn:hover:not(:disabled) {
  background-color: #dc2626;
  transform: translateY(-1px);
}

.retry-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.lora-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.lora-item {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  transition: var(--transition);
}

.lora-item:hover {
  border-color: var(--primary-color);
  background-color: rgba(99, 102, 241, 0.05);
}

.lora-checkbox {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 16px;
  cursor: pointer;
  transition: var(--transition);
}

.lora-checkbox input[type="checkbox"] {
  position: absolute;
  opacity: 0;
  cursor: pointer;
  height: 0;
  width: 0;
}

.checkbox-custom {
  position: relative;
  height: 20px;
  width: 20px;
  background-color: var(--bg-color);
  border: 2px solid var(--border-color);
  border-radius: var(--radius-sm);
  margin-right: 12px;
  transition: var(--transition);
}

.lora-checkbox:hover .checkbox-custom {
  border-color: var(--primary-color);
  background-color: rgba(99, 102, 241, 0.1);
}

.lora-checkbox input:checked ~ .checkbox-custom {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
}

.checkbox-custom:after {
  content: "";
  position: absolute;
  display: none;
  left: 6px;
  top: 2px;
  width: 4px;
  height: 8px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.lora-checkbox input:checked ~ .checkbox-custom:after {
  display: block;
}

.lora-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.lora-name {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 14px;
}

.lora-strength-control {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}

.lora-strength-control label {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
}

.strength-input {
  width: 60px;
  padding: 4px 8px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-size: 12px;
  background-color: var(--bg-color);
  transition: var(--transition);
}

.strength-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}

.strength-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background-color: var(--bg-light);
}

.lora-strength {
  font-size: 12px;
  color: var(--text-secondary);
  opacity: 0.8;
}

.lora-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: var(--text-secondary);
  font-style: italic;
  text-align: center;
}

/* 滚动条样式 */
.lora-selection::-webkit-scrollbar {
  width: 8px;
}

.lora-selection::-webkit-scrollbar-track {
  background: var(--bg-light);
  border-radius: var(--radius-md);
}

.lora-selection::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: var(--radius-md);
  transition: var(--transition);
}

.lora-selection::-webkit-scrollbar-thumb:hover {
  background: var(--text-secondary);
}

/* 禁用状态 */
.lora-checkbox input:disabled ~ .checkbox-custom {
  opacity: 0.5;
  cursor: not-allowed;
}

.lora-checkbox input:disabled ~ .lora-info {
  opacity: 0.6;
  cursor: not-allowed;
}

.clear-image-btn:hover {
  background-color: #dc2626;
  transform: translateY(-50%) scale(1.1);
  box-shadow: 0 10px 15px -3px rgba(239, 68, 68, 0.3);
}

.clear-image-btn:active {
  transform: translateY(-50%) scale(0.95);
}

.image-preview {
  margin-top: 16px;
  border-radius: var(--radius-lg);
  overflow: hidden;
  border: 1px solid var(--border-color);
  background-color: var(--bg-light);
  transition: var(--transition);
}

.image-preview:hover {
  box-shadow: var(--shadow-md);
}

.preview-wrapper {
  width: 100%;
  height: auto;
  max-height: 300px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-wrapper img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: var(--transition);
}

.preview-wrapper:hover img {
  transform: scale(1.05);
}

/* 生成类型选择器 */
.generate-type-selector {
  position: relative;
  width: 100%;
}

.generate-type-select {
  width: 100%;
  padding: 20px 28px;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  color: var(--text-primary);
  border: 2px solid var(--border-color);
  border-radius: var(--radius-xl);
  cursor: pointer;
  font-size: 18px;
  font-weight: 600;
  transition: var(--transition);
  appearance: none;
  background-image: url('data:image/svg+xml;charset=US-ASCII,<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="%236366f1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>');
  background-repeat: no-repeat;
  background-position: right 24px center;
  background-size: 22px;
  padding-right: 70px;
  box-shadow: var(--shadow-md);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.generate-type-select:hover:not(:disabled) {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border-color: var(--primary-color);
  box-shadow: 0 8px 20px rgba(99, 102, 241, 0.2);
  transform: translateY(-2px);
}

.generate-type-select:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.25);
}

.generate-type-select:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
}

/* 宽高比选择 */
.aspect-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.aspect-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 16px 20px;
  background-color: var(--bg-light);
  border: 2px solid var(--border-color);
  border-radius: var(--radius-lg);
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: var(--transition);
  flex: 1;
  min-width: 100px;
  color: var(--text-secondary);
}

.aspect-btn:hover:not(:disabled) {
  background-color: rgba(99, 102, 241, 0.05);
  border-color: var(--primary-color);
  color: var(--primary-color);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.aspect-btn.active {
  background-color: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
  box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.3);
}

.aspect-icon {
  width: 40px;
  height: 40px;
  border: 2px solid currentColor;
  border-radius: var(--radius-sm);
  position: relative;
  background-color: rgba(255, 255, 255, 0.1);
}

.aspect-icon.vertical {
  height: 56px;
  width: 32px;
}

.aspect-icon.horizontal {
  height: 32px;
  width: 56px;
}

.aspect-icon.square {
  height: 40px;
  width: 40px;
}

.aspect-btn.active .aspect-icon {
  background-color: rgba(255, 255, 255, 0.2);
  border-color: white;
}

/* 视频时长选择 */
.duration-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.duration-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px 20px;
  background-color: var(--bg-light);
  border: 2px solid var(--border-color);
  border-radius: var(--radius-lg);
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: var(--transition);
  flex: 1;
  min-width: 100px;
  color: var(--text-secondary);
}

.duration-btn:hover:not(:disabled) {
  background-color: rgba(99, 102, 241, 0.05);
  border-color: var(--primary-color);
  color: var(--primary-color);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.duration-btn.active {
  background-color: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
  box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.3);
}

/* 生成按钮 */
.generate-controls {
  display: flex;
  gap: 16px;
  margin-top: 32px;
  flex-wrap: wrap;
}

.generate-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 14px 28px;
  border: none;
  border-radius: var(--radius-lg);
  cursor: pointer;
  font-size: 16px;
  font-weight: 600;
  transition: var(--transition);
  flex: 1;
  min-width: 140px;
  position: relative;
  overflow: hidden;
}

.generate-btn.primary {
  background-color: var(--primary-color);
  color: white;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.generate-btn.primary:hover:not(:disabled) {
  background-color: var(--primary-hover);
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(99, 102, 241, 0.4);
}

.generate-btn.secondary {
  background-color: var(--bg-light);
  color: var(--text-secondary);
  border: 2px solid var(--border-color);
}

.generate-btn.secondary:hover:not(:disabled) {
  background-color: rgba(99, 102, 241, 0.05);
  border-color: var(--primary-color);
  color: var(--primary-color);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.generate-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.spin-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 生成状态 */
.generation-status {
  margin-top: 20px;
  padding: 16px 20px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  gap: 12px;
  background-color: var(--bg-light);
  border: 1px solid var(--border-color);
  transition: var(--transition);
}

.generation-status:hover {
  box-shadow: var(--shadow-sm);
}

.status-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: rgba(99, 102, 241, 0.1);
  color: var(--primary-color);
  flex-shrink: 0;
}

.status-icon.success {
  background-color: rgba(16, 185, 129, 0.1);
  color: var(--success-color);
}

.status-icon.error {
  background-color: rgba(239, 68, 68, 0.1);
  color: var(--error-color);
}

.status-text {
  flex: 1;
  font-size: 15px;
  color: var(--text-secondary);
  line-height: 1.5;
  font-weight: 500;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .panel-content {
    padding: 20px;
  }
  
  .panel-header {
    padding: 20px;
  }
  
  .mode-text {
    font-size: 18px;
  }
  
  .generate-controls {
    flex-direction: column;
  }
  
  .generate-btn {
    min-width: auto;
  }
  
  .aspect-buttons {
    flex-direction: column;
  }
  
  .aspect-btn {
    min-width: auto;
  }
}
</style>