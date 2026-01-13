<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { get, post, del, getApiBaseUrl } from '../utils/api';

// 定义任务结果类型
interface TaskResult {
  image_path?: string;
  video_path?: string;
  cover_path?: string;
  task_type: string;
}

// 定义任务类型
interface Task {
  task_id: string;
  task_type: string;
  status: string;
  created_at: number;
  updated_at: number;
  params: any;
  result?: TaskResult;
  error?: string;
  is_video?: boolean;
  render_start_time?: number;
  render_end_time?: number;
}

// 任务列表
const tasks = ref<Task[]>([]);
// 加载状态
const isLoading = ref(false);
// 选中的任务（用于显示错误详情）
const selectedTask = ref<Task | null>(null);
// 错误详情显示状态
const showErrorDetails = ref(false);
// 轮询定时器
let pollingTimer: number | null = null;
// 视频元素引用
const videoRefs = ref<Record<string, HTMLVideoElement | null>>({});
// 预览模态框相关
const showPreviewModal = ref(false);
const previewTask = ref<Task | null>(null);
const imageZoom = ref(1); // 图片缩放级别
const isDragging = ref(false); // 是否正在拖动
const dragStartX = ref(0); // 拖动起始X位置
const dragStartY = ref(0); // 拖动起始Y位置
const dragOffsetX = ref(0); // 拖动X偏移量
const dragOffsetY = ref(0); // 拖动Y偏移量

// 悬浮框状态
const showTooltip = ref(false);
const tooltipText = ref('');
const tooltipPosition = ref({ x: 0, y: 0 });

// 分页相关状态
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);
const totalPages = ref(0);

// 关闭任务列表
defineEmits<{
  (e: 'close'): void;
}>();

// 获取任务列表
const fetchTasks = async () => {
  try {
    isLoading.value = true;
    console.log('fetchTasks called, currentPage:', currentPage.value);
    console.log('Request URL:', `/task/list?page=${currentPage.value}&page_size=${pageSize.value}`);
    const response = await get<{total: number; page: number; page_size: number; tasks: Task[]}>(`/task/list?page=${currentPage.value}&page_size=${pageSize.value}`);
    
    console.log('API Response:', response);
    if (response.success && response.data) {
      console.log('Response data:', response.data);
      console.log('Response page:', response.data.page);
      // 更新分页状态
      total.value = response.data.total;
      console.log('Updating currentPage from response:', response.data.page);
      currentPage.value = response.data.page;
      console.log('After update, currentPage:', currentPage.value);
      pageSize.value = response.data.page_size;
      totalPages.value = Math.ceil(total.value / pageSize.value);
      console.log('totalPages:', totalPages.value);
      
      // 处理任务数据，添加视频标识
      tasks.value = response.data.tasks.map((task: any) => ({
        ...task,
        is_video: task.task_type.includes('video')
      }));
    }
  } catch (error) {
    console.error('获取任务列表失败:', error);
  } finally {
    isLoading.value = false;
  }
};

// 重试任务
const retryTask = async (taskId: string) => {
  try {
    // 找到任务
    const task = tasks.value.find(t => t.task_id === taskId);
    if (!task) return;

    // 更新任务状态为重试中
    task.status = 'retrying';

    // 发送重试请求
    const response = await post(`/task/${taskId}/retry`);

    if (response.success) {
      // 重新获取任务列表
      await fetchTasks();
    } else {
      // 恢复原始状态
      task.status = task.status === 'retrying' ? 'failed' : task.status;
      console.error('重试任务失败:', response.error);
    }
  } catch (error) {
    console.error('重试任务失败:', error);
    // 恢复原始状态
    const task = tasks.value.find(t => t.task_id === taskId);
    if (task) {
      task.status = task.status === 'retrying' ? 'failed' : task.status;
    }
  }
};

// 删除任务
const deleteTask = async (taskId: string) => {
  try {
    const response = await del(`/task/${taskId}`);

    if (response.success) {
      // 从列表中移除任务
      tasks.value = tasks.value.filter(t => t.task_id !== taskId);
    } else {
      console.error('删除任务失败:', response.error);
    }
  } catch (error) {
    console.error('删除任务失败:', error);
  }
};

// 查看错误详情
const viewErrorDetails = (task: Task) => {
  selectedTask.value = task;
  showErrorDetails.value = true;
};

// 关闭错误详情
const closeErrorDetails = () => {
  showErrorDetails.value = false;
  selectedTask.value = null;
};

// 打开预览模态框
const openPreviewModal = (task: Task) => {
  previewTask.value = task;
  showPreviewModal.value = true;
};

// 关闭预览模态框
const closePreviewModal = () => {
  showPreviewModal.value = false;
  previewTask.value = null;
  imageZoom.value = 1; // 重置缩放级别
  dragOffsetX.value = 0; // 重置拖动偏移
  dragOffsetY.value = 0;
};

// 图片缩放功能
const zoomIn = () => {
  if (imageZoom.value < 3) {
    imageZoom.value += 0.1;
  }
};

const zoomOut = () => {
  if (imageZoom.value > 0.5) {
    imageZoom.value -= 0.1;
  }
};

const resetZoom = () => {
  imageZoom.value = 1;
  dragOffsetX.value = 0; // 重置拖动偏移
  dragOffsetY.value = 0;
};

// 图片拖动功能
const startDrag = (event: MouseEvent) => {
  if (imageZoom.value > 1) { // 只有在缩放后才能拖动
    event.preventDefault();
    isDragging.value = true;
    dragStartX.value = event.clientX - dragOffsetX.value;
    dragStartY.value = event.clientY - dragOffsetY.value;
    
    // 添加全局鼠标事件监听器，确保拖动在整个文档上都能工作
    document.addEventListener('mousemove', drag);
    document.addEventListener('mouseup', endDrag);
    document.addEventListener('mouseleave', endDrag);
  }
};

const drag = (event: MouseEvent) => {
  if (isDragging.value) {
    event.preventDefault();
    dragOffsetX.value = event.clientX - dragStartX.value;
    dragOffsetY.value = event.clientY - dragStartY.value;
  }
};

const endDrag = () => {
  if (isDragging.value) {
    isDragging.value = false;
    // 移除全局鼠标事件监听器
    document.removeEventListener('mousemove', drag);
    document.removeEventListener('mouseup', endDrag);
    document.removeEventListener('mouseleave', endDrag);
  }
};

// 显示悬浮框
const showTooltipHandler = (event: MouseEvent, text: string) => {
  tooltipText.value = text;
  tooltipPosition.value = {
    x: event.clientX + 10,
    y: event.clientY + 10
  };
  showTooltip.value = true;
};

// 隐藏悬浮框
const hideTooltipHandler = () => {
  showTooltip.value = false;
};

// 更新悬浮框位置
const updateTooltipPosition = (event: MouseEvent) => {
  if (showTooltip.value) {
    tooltipPosition.value = {
      x: event.clientX + 10,
      y: event.clientY + 10
    };
  }
};

// 获取状态显示文本
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'pending': '等待中',
    'processing': '处理中',
    'completed': '已完成',
    'failed': '失败',
    'cancelled': '已取消',
    'retrying': '重试中'
  };
  return statusMap[status] || status;
};

// 获取状态样式类
const getStatusClass = (status: string) => {
  const statusClassMap: Record<string, string> = {
    'pending': 'status-pending',
    'processing': 'status-processing',
    'completed': 'status-completed',
    'failed': 'status-failed',
    'cancelled': 'status-cancelled',
    'retrying': 'status-retrying'
  };
  return statusClassMap[status] || '';
};

// 获取任务类型显示文本
const getTaskTypeText = (taskType: string) => {
  const typeMap: Record<string, string> = {
    'text2img': '文生图',
    'img2img': '图生图',
    'text2video': '文生视频',
    'img2video': '图生视频'
  };
  return typeMap[taskType] || taskType;
};

// 格式化时间
const formatTime = (timestamp: number) => {
  const date = new Date(timestamp * 1000);
  return date.toLocaleString('zh-CN');
};

// 计算渲染耗时（秒）
const getRenderTime = (task: Task) => {
  if (!task.render_start_time || !task.render_end_time) return null;
  if (task.render_start_time > task.render_end_time) return null;
  return (task.render_end_time - task.render_start_time).toFixed(2);
};

// 获取任务横竖方向
const getTaskOrientation = (task: Task) => {
  if (!task.params) return '';
  const width = task.params.width || 0;
  const height = task.params.height || 0;
  if (width > height) return '横';
  if (height > width) return '竖';
  return '方';
};

// 获取任务使用的LoRA模型
const getTaskLoras = (task: Task) => {
  if (!task.params) return [];
  if (task.params.loras) {
    return task.params.loras;
  }
  return task.params.lora_names || task.params.lora_ids || [];
};

// 拼接域名到文件路径
const getFullPath = (path?: string) => {
  if (!path) return '';
  // 使用API域名并移除/api前缀
  const domain = getApiBaseUrl().replace('/api', '');
  // 确保路径以/开头
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${domain}${normalizedPath}`;
};

// 分页相关函数
const goToPage = (page: number) => {
  console.log('goToPage called with page:', page);
  console.log('Current currentPage:', currentPage.value);
  console.log('totalPages:', totalPages.value);
  if (page >= 1 && page <= totalPages.value && page !== currentPage.value) {
    console.log('Updating currentPage to:', page);
    currentPage.value = page;
    console.log('After update, currentPage:', currentPage.value);
    fetchTasks();
  }
};

const handlePageSizeChange = () => {
  currentPage.value = 1;
  fetchTasks();
};

// 更新单个任务状态
const updateSingleTask = async (taskId: string) => {
  try {
    const response = await get<Task>(`/task/${taskId}`);
    if (response.success && response.data) {
      // 找到任务索引
      const taskIndex = tasks.value.findIndex(task => task.task_id === taskId);
      if (taskIndex !== -1) {
        // 更新任务信息
        tasks.value[taskIndex] = {
          ...tasks.value[taskIndex],
          ...response.data,
          is_video: response.data.task_type.includes('video')
        };
      }
    }
  } catch (error) {
    console.error(`更新任务 ${taskId} 失败:`, error);
  }
};

// 刷新任务列表（用于手动触发）
const refreshTasks = async () => {
  await fetchTasks();
};

// 导出方法供父组件调用
defineExpose({
  refreshTasks
});

// 开始轮询任务状态
const startPolling = () => {
  // 初始加载
  fetchTasks();
  // 每3秒轮询一次
  pollingTimer = window.setInterval(() => {
    // 只更新状态为pending或processing的任务
    const activeTasks = tasks.value.filter(task => 
      task.status === 'pending' || task.status === 'processing'
    );
    
    // 并行更新所有活跃任务
    activeTasks.forEach(task => {
      updateSingleTask(task.task_id);
    });
  }, 3000);
};

// 停止轮询
const stopPolling = () => {
  if (pollingTimer) {
    clearInterval(pollingTimer);
    pollingTimer = null;
  }
};

// 组件挂载时开始轮询
onMounted(() => {
  startPolling();
});

// 组件卸载时停止轮询
onUnmounted(() => {
  stopPolling();
});
</script>

<template>
  <div class="task-list-container">
    <!-- 任务列表头部 -->
    <div class="task-list-header">
      <h2 class="task-list-title">任务列表</h2>
      <button class="close-btn" @click="$emit('close')">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    </div>

    <!-- 任务列表内容 -->
    <div class="task-list-content">
      <!-- 加载状态 -->
      <div class="loading-container" v-if="isLoading">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>

      <!-- 空状态 -->
      <div class="empty-state" v-else-if="tasks.length === 0">
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
          <polyline points="14 2 14 8 20 8"></polyline>
          <line x1="16" y1="13" x2="8" y2="13"></line>
          <line x1="16" y1="17" x2="8" y2="17"></line>
          <polyline points="10 9 9 9 8 9"></polyline>
        </svg>
        <p>暂无任务</p>
      </div>

      <!-- 任务列表 -->
      <div class="tasks" v-else>
        <div class="task-item" v-for="task in tasks" :key="task.task_id">
          <!-- 任务基本信息 -->
          <div class="task-header">
            <div class="task-info">
            <div class="task-type">
              {{ getTaskTypeText(task.task_type) }}
              <span class="task-orientation" v-if="getTaskOrientation(task)">
                {{ getTaskOrientation(task) }}
              </span>
            </div>
            <div class="task-time">
              {{ formatTime(task.created_at) }}
            </div>
            <div class="render-time" v-if="getRenderTime(task)">
              渲染耗时: {{ getRenderTime(task) }}秒
            </div>
          </div>
            <div class="task-status" :class="getStatusClass(task.status)">
              {{ getStatusText(task.status) }}
            </div>
          </div>

          <!-- 任务结果展示 -->
          <div class="task-result">
            <!-- 未完成任务显示默认占位图 -->
            <div v-if="task.status !== 'completed'" class="task-placeholder">
              <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                <circle cx="8.5" cy="8.5" r="1.5"></circle>
                <polyline points="21 15 16 10 5 21"></polyline>
              </svg>
              <p>处理中...</p>
            </div>

            <!-- 图片任务结果 -->
            <div v-else-if="!task.is_video && task.result?.image_path" class="task-image">
              <img :src="getFullPath(task.result.image_path)" :alt="task.params.prompt" @click="openPreviewModal(task)" style="cursor: pointer;" />
            </div>

            <!-- 视频任务结果 -->
            <div v-else-if="task.is_video && task.result?.video_path" class="task-video">
              <div class="video-wrapper" @click="openPreviewModal(task)">
                <img v-if="task.result.cover_path" :src="getFullPath(task.result.cover_path)" :alt="task.params.prompt" class="video-cover" />
                <div class="video-play-btn">
                  <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polygon points="5 3 19 12 5 21 5 3"></polygon>
                  </svg>
                </div>
              </div>
              <video :ref="el => videoRefs[task.task_id] = el as HTMLVideoElement | null" :src="getFullPath(task.result.video_path)" controls style="display: none;"></video>
            </div>
          </div>

          <!-- 任务提示词 -->
          <div class="task-prompt-container">
            <div 
              class="task-prompt" 
              @mouseenter="(e) => showTooltipHandler(e, task.params.prompt)"
              @mouseleave="hideTooltipHandler"
              @mousemove="updateTooltipPosition"
            >
              {{ task.params.prompt }}
            </div>
            <!-- LoRA模型信息 -->
            <div class="task-loras" v-if="getTaskLoras(task).length > 0">
              <span class="loras-label">使用LoRA:</span>
              <span class="loras-list">
                <span v-for="(lora, index) in getTaskLoras(task)" :key="index" class="lora-item">
                  {{ typeof lora === 'string' ? lora : `${lora.name} (强度: ${lora.strength})` }}
                  <span v-if="index < getTaskLoras(task).length - 1">, </span>
                </span>
              </span>
            </div>
          </div>

          <!-- 任务操作 -->
          <div class="task-actions">
            <!-- 失败任务显示错误详情按钮 -->
            <button 
              class="action-btn error-btn" 
              @click="viewErrorDetails(task)"
              v-if="task.status === 'failed' && task.error"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
              </svg>
              错误详情
            </button>

            <!-- 重试按钮 -->
            <button 
              class="action-btn retry-btn" 
              @click="retryTask(task.task_id)"
              :disabled="task.status === 'processing' || task.status === 'pending' || task.status === 'retrying'"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="23 4 23 10 17 10"></polyline>
                <polyline points="1 20 1 14 7 14"></polyline>
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
              </svg>
              重试
            </button>

            <!-- 删除按钮 -->
            <button 
              class="action-btn delete-btn" 
              @click="deleteTask(task.task_id)"
              :disabled="task.status === 'processing' || task.status === 'pending'"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="3 6 5 6 21 6"></polyline>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                <line x1="10" y1="11" x2="10" y2="17"></line>
                <line x1="14" y1="11" x2="14" y2="17"></line>
              </svg>
              删除
            </button>
          </div>
        </div>
      </div>

      <!-- 分页控件 -->
      <div class="pagination" v-if="total > 0">
        <div class="pagination-info">
          共 {{ total }} 条记录，第 {{ currentPage }}/{{ totalPages }} 页
        </div>
        <div class="pagination-controls">
          <button 
            class="pagination-btn" 
            @click="goToPage(1)"
            :disabled="currentPage === 1"
          >
            首页
          </button>
          <button 
            class="pagination-btn" 
            @click="goToPage(currentPage - 1)"
            :disabled="currentPage === 1"
          >
            上一页
          </button>
          <button 
            class="pagination-btn" 
            @click="goToPage(currentPage + 1)"
            :disabled="currentPage === totalPages"
          >
            下一页
          </button>
          <button 
            class="pagination-btn" 
            @click="goToPage(totalPages)"
            :disabled="currentPage === totalPages"
          >
            末页
          </button>
          <select class="page-size-select" v-model="pageSize" @change="handlePageSizeChange">
            <option :value="5">5条/页</option>
            <option :value="10">10条/页</option>
            <option :value="20">20条/页</option>
            <option :value="50">50条/页</option>
          </select>
        </div>
      </div>
    </div>

    <!-- 错误详情弹窗 -->
    <div class="error-details-overlay" v-if="showErrorDetails && selectedTask" @click.stop>
      <div class="error-details-modal">
        <div class="error-details-header">
          <h3>任务错误详情</h3>
          <button class="close-btn" @click="closeErrorDetails">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <div class="error-details-content">
          <div class="error-task-info">
            <div class="error-task-id">任务ID: {{ selectedTask.task_id }}</div>
            <div class="error-task-type">{{ getTaskTypeText(selectedTask.task_type) }}</div>
          </div>
          <div class="error-message">
            <h4>错误信息:</h4>
            <pre>{{ selectedTask.error }}</pre>
          </div>
        </div>
        <div class="error-details-actions">
          <button class="close-details-btn" @click="closeErrorDetails">关闭</button>
        </div>
      </div>
    </div>

    <!-- 预览模态框 -->
    <div class="preview-overlay" v-if="showPreviewModal && previewTask" @click.stop>
      <div class="preview-modal">
        <button class="close-preview-btn" @click="closePreviewModal">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
        <div class="preview-content">
          <!-- 图片预览 -->
          <div v-if="!previewTask.is_video && previewTask.result?.image_path" class="preview-image">
            <img 
              :src="getFullPath(previewTask.result.image_path)" 
              :alt="previewTask.params.prompt" 
              :style="{ 
                transform: `translate(${dragOffsetX}px, ${dragOffsetY}px) scale(${imageZoom})`, 
                transition: isDragging ? 'none' : 'transform 0.2s ease' 
              }"
              @mousedown="startDrag"
            />
            <!-- 缩放控制 -->
            <div class="zoom-controls">
              <button class="zoom-btn" @click="zoomOut" title="缩小">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="8" y1="12" x2="16" y2="12"></line>
                </svg>
              </button>
              <span class="zoom-level">{{ Math.round(imageZoom * 100) }}%</span>
              <button class="zoom-btn" @click="zoomIn" title="放大">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="12" y1="8" x2="12" y2="16"></line>
                  <line x1="8" y1="12" x2="16" y2="12"></line>
                </svg>
              </button>
              <button class="zoom-btn" @click="resetZoom" title="重置">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path>
                  <path d="M3 3v5h5"></path>
                  <path d="M21 12a9 9 0 1 1-9-9 9.75 9.75 0 0 1 6.74 2.74L21 16"></path>
                  <path d="M16 16h5v5"></path>
                </svg>
              </button>
            </div>
          </div>
          <!-- 视频预览 -->
          <div v-else-if="previewTask.is_video && previewTask.result?.video_path" class="preview-video">
            <video :src="getFullPath(previewTask.result.video_path)" controls autoplay muted></video>
          </div>
        </div>
        <div class="preview-info">
          <div class="preview-prompt" :title="previewTask.params.prompt">
            <div class="prompt-content">{{ previewTask.params.prompt }}</div>
          </div>
          <div class="preview-meta">
            <span>{{ getTaskTypeText(previewTask.task_type) }}</span>
            <span>{{ formatTime(previewTask.created_at) }}</span>
            <span v-if="getRenderTime(previewTask)">渲染耗时: {{ getRenderTime(previewTask) }}秒</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 悬浮框 -->
    <div 
      v-if="showTooltip" 
      class="tooltip" 
      :style="{
        left: tooltipPosition.x + 'px',
        top: tooltipPosition.y + 'px'
      }"
    >
      {{ tooltipText }}
    </div>
  </div>
</template>

<style scoped>
:root {
  --primary-color: #000000;
  --primary-hover: #333333;
  --secondary-color: #666666;
  --secondary-hover: #444444;
  --success-color: #000000;
  --error-color: #000000;
  --warning-color: #000000;
  --bg-color: #ffffff;
  --bg-light: #f5f5f5;
  --border-color: #dddddd;
  --border-focus: #000000;
  --text-primary: #000000;
  --text-secondary: #666666;
  --text-helper: #999999;
  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.1);
  --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.2);
  --shadow-lg: 0 4px 16px rgba(0, 0, 0, 0.2);
  --radius-sm: 8px;
  --radius-md: 8px;
  --radius-lg: 8px;
  --radius-xl: 24px;
  --transition: all 0.3s ease;
}

.task-list-container {
  width: 100%;
  height: 100vh;
  background-color: #ffffff;
  box-shadow: -2px 0 20px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  position: relative;
  transition: var(--transition);
}

.task-list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: #ffffff;
  border-bottom: 1px solid var(--border-color);
  border-radius: 16px 0 0 0;
  border-bottom: 1px solid #f0f0f0;
}

.task-list-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  flex: 1;
  text-align: center;
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background-color: #ffffff;
  color: var(--text-primary);
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: var(--transition);
}

.close-btn:hover {
  background: var(--bg-light);
}

.task-list-content {
  flex: 1;
  overflow: hidden;
  padding: 0 24px 0px 24px;
  background: #ffffff;
  display: flex;
  flex-direction: column;
}

/* 加载状态 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  flex: 1;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 3px solid var(--bg-light);
  border-top: 3px solid var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  color: #999999;
  text-align: center;
  flex: 1;
  margin: 0;
}

.empty-state svg {
  margin-bottom: 24px;
  opacity: 0.3;
  width: 100px;
  height: 100px;
  color: #000000;
  transition: all 0.3s ease;
}

.empty-state:hover svg {
  opacity: 0.5;
  transform: scale(1.05);
}

/* 任务列表 */
.tasks {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  overflow-y: auto;
  flex: 1;
  padding-top: 24px;
  padding-bottom: 16px;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .tasks {
    grid-template-columns: 1fr;
    gap: 12px;
    padding-top: 16px;
    padding-bottom: 12px;
  }
  
  .task-list-content {
    padding: 0 16px 0px 16px;
  }
}

.task-item {
  padding: 24px;
  background-color: #f9f9f9;
  border-radius: 16px;
  border: 1px solid #e5e5e5;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.task-item:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  border-color: #000000;
  transform: translateY(-2px);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
  gap: 12px;
}

.task-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.task-type {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.task-orientation {
  font-size: 12px;
  font-weight: 400;
  color: var(--text-secondary);
  background: var(--bg-light);
  padding: 2px 8px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  white-space: nowrap;
}

.video-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background-color: var(--error-color);
  color: white;
  font-size: 12px;
  font-weight: 500;
  border-radius: var(--radius-sm);
  transition: var(--transition);
}

.task-time {
  font-size: 13px;
  color: var(--text-helper);
  font-family: monospace;
}

.render-time {
  font-size: 12px;
  color: var(--success-color);
  font-weight: 500;
  font-family: monospace;
}

.task-status {
  padding: 6px 14px;
  border-radius: var(--radius-full, 20px);
  font-size: 13px;
  font-weight: 600;
  text-align: center;
  white-space: nowrap;
  transition: var(--transition);
  box-shadow: var(--shadow-sm);
}

/* 状态样式 */
.task-status {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  display: inline-block;
}

.status-pending {
  color: #6c757d;
  border: 1px solid #dee2e6;
}

.status-processing {
  color: #1976d2;
  border: 1px solid #1976d2;
}

.status-completed {
  color: #2e7d32;
  border: 1px solid #2e7d32;
}

.status-failed {
  color: #c62828;
  border: 1px solid #c62828;
}

.status-cancelled {
  color: #616161;
  border: 1px solid #616161;
}

.status-retrying {
  color: #ef6c00;
  border: 1px solid #ef6c00;
}

.task-result {
  margin-bottom: 16px;
  border-radius: var(--radius-lg);
  overflow: hidden;
  background-color: var(--bg-light);
  position: relative;
  width: 100%;
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.task-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-helper);
}

.task-placeholder svg {
  margin-bottom: 12px;
  opacity: 0.6;
  color: var(--secondary-color);
}

.task-placeholder p {
  margin: 0;
  font-size: 14px;
}

.task-image {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  border-radius: var(--radius-md);
}

.task-image img {
  width: 100%;
  height: 100%;
  object-fit: cover; /* 等比例裁剪缩放 */
  display: block;
}

.task-video {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100%;
}

.video-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  cursor: pointer;
  border-radius: var(--radius-md);
  overflow: hidden;
}

.video-cover {
  width: 100%;
  height: 100%;
  object-fit: cover; /* 等比例裁剪缩放 */
  display: block;
}

.video-play-btn {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 60px;
  height: 60px;
  background-color: rgba(255, 255, 255, 0.8);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  opacity: 0.8;
}

.video-wrapper:hover .video-play-btn {
  opacity: 1;
  transform: translate(-50%, -50%) scale(1.1);
}

.task-prompt-container {
  position: relative;
  width: 100%;
  overflow: hidden;
  margin-bottom: 16px;
}

.task-loras {
  margin-top: 8px;
  font-size: 12px;
  color: var(--text-secondary);
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
}

.loras-label {
  font-weight: 600;
  color: var(--text-primary);
}

.loras-list {
  flex: 1;
  word-break: break-word;
}

.task-prompt {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
  word-break: break-word;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  display: box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  box-orient: vertical;
  cursor: pointer;
  box-sizing: border-box;
  padding: 0;
  margin: 0;
  max-height: 39px; /* 13px * 1.5 * 2 = 39px */
  min-height: 39px;
}

.tooltip {
  position: fixed;
  background-color: var(--bg-light);
  color: var(--text-primary);
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  max-width: 300px;
  word-wrap: break-word;
  z-index: 10000;
  box-shadow: var(--shadow-md);
  pointer-events: none;
  transition: opacity 0.2s ease;
  border: 1px solid var(--border-color);
  background: rgba(255, 255, 255);
  border-radius: 10px;
  box-shadow: 1px 1px 15px 1px #999999;
}

.task-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  flex-wrap: wrap;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: var(--transition);
  box-shadow: var(--shadow-sm);
  background: #ffffff;
  color: var(--text-primary);
}

.action-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.error-btn:hover:not(:disabled) {
  border-color: var(--primary-color);
  background: var(--bg-light);
}

.retry-btn:hover:not(:disabled) {
  border-color: var(--primary-color);
  background: var(--bg-light);
}

.delete-btn:hover:not(:disabled) {
  border-color: var(--primary-color);
  background: var(--bg-light);
}

/* 分页控件 */
.pagination {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 12px 0;
  gap: 6px;
  margin-top: 0;
  border-top: 1px solid #e5e5e5;
  flex-shrink: 0;
}

.pagination-info {
  font-size: 12px;
  color: var(--text-secondary);
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
}

.pagination-btn {
  padding: 6px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background-color: var(--bg-color);
  color: var(--text-primary);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: var(--transition);
  box-shadow: var(--shadow-sm);
}

.pagination-btn:hover:not(:disabled) {
  border-color: var(--primary-color);
  background: var(--bg-light);
}

.pagination-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.page-size-select {
  padding: 6px 10px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background-color: var(--bg-color);
  color: var(--text-primary);
  font-size: 12px;
  cursor: pointer;
  transition: var(--transition);
  box-shadow: var(--shadow-sm);
}

.page-size-select:hover {
  border-color: var(--primary-color);
  background: var(--bg-light);
}

/* 错误详情弹窗 */
.error-details-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.error-details-modal {
  background-color: var(--bg-color);
  border-radius: var(--radius-xl);
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  border: 1px solid var(--border-color);
  transition: var(--transition);
}

.error-details-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  border-bottom: 1px solid var(--border-color);
  background: #ffffff;
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
}

.error-details-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.error-details-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.error-task-info {
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border-color);
}

.error-task-id {
  font-size: 14px;
  color: var(--text-helper);
  margin-bottom: 8px;
  font-family: monospace;
}

.error-task-type {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.error-message {
  margin-bottom: 24px;
}

.error-message h4 {
  margin: 0 0 16px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.error-message pre {
  margin: 0;
  padding: 20px;
  background-color: var(--bg-light);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  font-size: 14px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 400px;
  overflow-y: auto;
  line-height: 1.6;
  color: var(--text-primary);
  box-shadow: var(--shadow-sm);
}

.error-details-actions {
  display: flex;
  justify-content: flex-end;
  padding: 16px 24px;
  border-top: 1px solid var(--border-color);
  gap: 12px;
}

.close-details-btn {
  padding: 10px 24px;
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 15px;
  font-weight: 500;
  transition: var(--transition);
  box-shadow: var(--shadow-sm);
}

.close-details-btn:hover {
  background-color: var(--primary-hover);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

/* 预览模态框 */
.preview-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(8px);
}

.preview-modal {
  background-color: var(--bg-color);
  border-radius: var(--radius-xl);
  width: 100%;
  max-width: 1000px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border-color);
  transition: var(--transition);
  overflow: hidden;
}

.close-preview-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 40px;
  height: 40px;
  background-color: rgba(0, 0, 0, 0.5);
  color: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: var(--transition);
  z-index: 10;
}

.close-preview-btn:hover {
  background-color: rgba(0, 0, 0, 0.8);
  transform: scale(1.1);
}

.preview-content {
  flex: 1;
  padding: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--bg-light);
  position: relative;
}

.preview-image {
  position: relative;
  width: 100%;
  max-width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  overflow: hidden;
}

.preview-image img {
  max-width: 100%;
  max-height: 60vh;
  object-fit: contain;
  border-radius: var(--radius-lg);
  cursor: zoom-in;
}

.preview-image img:active {
  cursor: grabbing;
}

/* 缩放控制 */
.zoom-controls {
  position: absolute;
  bottom: 30px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(0, 0, 0, 0.7);
  padding: 8px 16px;
  border-radius: 20px;
  color: white;
  z-index: 10;
}

.zoom-btn {
  background: transparent;
  border: none;
  color: white;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: background 0.2s;
}

.zoom-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.zoom-level {
  font-size: 14px;
  min-width: 50px;
  text-align: center;
}

.preview-video {
  width: 100%;
  max-width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-video video {
  max-width: 100%;
  max-height: 60vh;
  object-fit: contain;
  border-radius: var(--radius-lg);
  background-color: black;
}

.preview-info {
  padding: 24px;
  border-top: 1px solid var(--border-color);
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-hover) 100%);
  color: white;
  max-height: 180px;
  overflow-y: auto;
}

.preview-info::-webkit-scrollbar {
  width: 6px;
}

.preview-info::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

.preview-info::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 3px;
}

.preview-info::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
}

.preview-prompt {
  font-size: 16px;
  line-height: 1.6;
  margin-bottom: 16px;
  word-break: break-word;
}

.prompt-content {
  white-space: pre-wrap;
  word-wrap: break-word;
}

.preview-meta {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  font-size: 14px;
  opacity: 0.9;
}

.preview-meta span {
  display: flex;
  align-items: center;
  gap: 6px;
}
</style>