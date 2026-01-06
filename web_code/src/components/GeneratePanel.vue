<script setup lang="ts">
import { ref, reactive, watch } from 'vue';
import { post, postForm } from '../utils/api';
import type { ApiResponse } from '../utils/api';

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
  height: 544,
  num_frames: 81,
  aspect_ratio: 'vertical' // vertical, horizontal, square
});

// 图片上传
const uploadedImage = ref<File | null>(null);
const imagePreviewUrl = ref('');

// 加载状态
const isGenerating = ref(false);
const generationMessage = ref('');

// 宽高比映射（根据生成类型）
const aspectRatioMap = {
  image: {
    vertical: { width: 544, height: 960 },
    horizontal: { width: 960, height: 544 },
    square: { width: 544, height: 544 }
  },
  video: {
    vertical: { width: 720, height: 1280 },
    horizontal: { width: 1280, height: 720 },
    square: { width: 720, height: 720 }
  }
};

// 监听生成模式变化，自动更新生成类型
watch(generateMode, (newMode) => {
  const selectedType = generateTypes.find(type => type.value === newMode);
  if (selectedType) {
    generateType.value = selectedType.type;
  }
});

// 监听生成类型变化，自动应用对应类型的宽高比
watch(generateType, () => {
  // 应用当前宽高比对应的宽高值
  const currentRatio = formData.aspect_ratio;
  formData.width = aspectRatioMap[generateType.value][currentRatio as keyof typeof aspectRatioMap[typeof generateType.value]].width;
  formData.height = aspectRatioMap[generateType.value][currentRatio as keyof typeof aspectRatioMap[typeof generateType.value]].height;
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
  formData.width = aspectRatioMap[generateType.value][ratio as keyof typeof aspectRatioMap[typeof generateType.value]].width;
  formData.height = aspectRatioMap[generateType.value][ratio as keyof typeof aspectRatioMap[typeof generateType.value]].height;
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
        height: formData.height
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
        image_path: uploadResponse.data.file_path
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
        num_frames: formData.num_frames
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
        image_path: uploadResponse.data.file_path
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

// 重新生成（使用相同参数）
const regenerate = () => {
  formData.seed = Math.floor(Math.random() * 1000000);
  submitGeneration();
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
            :title="`竖屏 (${aspectRatioMap[generateType][formData.aspect_ratio].width}x${aspectRatioMap[generateType][formData.aspect_ratio].height})`"
          >
            <div class="aspect-icon vertical"></div>
            <span>竖屏</span>
          </button>
          <button
            class="aspect-btn"
            :class="{ active: formData.aspect_ratio === 'horizontal' }"
            @click="changeAspectRatio('horizontal')"
            :disabled="isGenerating"
            :title="`横屏 (${aspectRatioMap[generateType][formData.aspect_ratio].width}x${aspectRatioMap[generateType][formData.aspect_ratio].height})`"
          >
            <div class="aspect-icon horizontal"></div>
            <span>横屏</span>
          </button>
          <button
            class="aspect-btn"
            :class="{ active: formData.aspect_ratio === 'square' }"
            @click="changeAspectRatio('square')"
            :disabled="isGenerating"
            :title="`方形 (${aspectRatioMap[generateType][formData.aspect_ratio].width}x${aspectRatioMap[generateType][formData.aspect_ratio].height})`"
          >
            <div class="aspect-icon square"></div>
            <span>方形</span>
          </button>
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
  cursor: pointer;
  transition: var(--transition);
  box-shadow: var(--shadow-md);
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