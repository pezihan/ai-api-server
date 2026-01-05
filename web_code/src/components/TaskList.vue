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
// 预览模态框状态
const showPreviewModal = ref(false);
const previewTask = ref<Task | null>(null);

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
  // 重置到第一页以确保显示最新任务
  currentPage.value = 1;
  try {
    isLoading.value = true;
    const response = await get<{total: number; page: number; page_size: number; tasks: Task[]}>(`/task/list?page=${currentPage.value}&page_size=${pageSize.value}`);
    
    if (response.success && response.data) {
      // 更新分页状态
      total.value = response.data.total;
      currentPage.value = response.data.page;
      pageSize.value = response.data.page_size;
      totalPages.value = Math.ceil(total.value / pageSize.value);
      
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
  return (task.render_end_time - task.render_start_time).toFixed(2);
};

// 拼接域名到文件路径
const getFullPath = (path?: string) => {
  if (!path) return '';
  // 使用API域名
  const domain = getApiBaseUrl();
  // 确保路径以/开头
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${domain}${normalizedPath}`;
};

// 分页相关函数
const goToPage = (page: number) => {
  if (page >= 1 && page <= totalPages.value && page !== currentPage.value) {
    currentPage.value = page;
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
              <span class="video-indicator" v-if="task.is_video">
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polygon points="5 3 19 12 5 21 5 3"></polygon>
                </svg>
                视频
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
    <div class="error-details-overlay" v-if="showErrorDetails && selectedTask">
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
    <div class="preview-overlay" v-if="showPreviewModal && previewTask">
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
            <img :src="getFullPath(previewTask.result.image_path)" :alt="previewTask.params.prompt" />
          </div>
          <!-- 视频预览 -->
          <div v-else-if="previewTask.is_video && previewTask.result?.video_path" class="preview-video">
            <video :src="getFullPath(previewTask.result.video_path)" controls autoplay muted></video>
          </div>
        </div>
        <div class="preview-info">
          <div class="preview-prompt">{{ previewTask.params.prompt }}</div>
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

.task-list-container {
  width: 800px;
  height: 100vh;
  background-color: var(--bg-color);
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
  padding: 24px;
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-hover) 100%);
  border-bottom: none;
}

.task-list-title {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: white;
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  transition: var(--transition);
  backdrop-filter: blur(10px);
}

.close-btn:hover {
  background-color: rgba(255, 255, 255, 0.3);
  transform: scale(1.1);
}

.task-list-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

/* 加载状态 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
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
  padding: 80px 20px;
  color: var(--text-helper);
}

.empty-state svg {
  margin-bottom: 20px;
  opacity: 0.4;
  width: 80px;
  height: 80px;
  color: var(--secondary-color);
  transition: var(--transition);
}

.empty-state:hover svg {
  opacity: 0.6;
  transform: scale(1.05);
}

/* 任务列表 */
.tasks {
  column-count: 3;
  column-gap: 16px;
}

.task-item {
  padding: 20px;
  background-color: var(--bg-color);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  transition: var(--transition);
  box-shadow: var(--shadow-sm);
  break-inside: avoid;
  margin-bottom: 16px;
}

.task-item:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
  border-color: var(--primary-color);
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
.status-pending {
  background-color: #e0f2fe;
  color: #0369a1;
}

.status-processing {
  background-color: #dcfce7;
  color: #15803d;
}

.status-completed {
  background-color: #f0fdf4;
  color: #16a34a;
}

.status-failed {
  background-color: #fee2e2;
  color: #dc2626;
}

.status-cancelled {
  background-color: #f3f4f6;
  color: #6b7280;
}

.status-retrying {
  background-color: #fef3c7;
  color: #d97706;
}

.task-result {
  margin-bottom: 16px;
  border-radius: var(--radius-lg);
  overflow: hidden;
  background-color: var(--bg-light);
  position: relative;
  min-height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.task-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px 20px;
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

.task-image img {
  width: 100%;
  height: auto;
  display: block;
  border-radius: var(--radius-md);
}

.task-video {
  width: 100%;
  position: relative;
}

.video-wrapper {
  position: relative;
  width: 100%;
  cursor: pointer;
}

.video-cover {
  width: 100%;
  height: auto;
  display: block;
  border-radius: var(--radius-md);
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
  cursor: help;
  box-sizing: border-box;
  padding: 0;
  margin: 0;
  max-height: 39px; /* 13px * 1.5 * 2 = 39px */
  min-height: 39px;
}

.tooltip {
  position: fixed;
  background-color: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  max-width: 300px;
  word-wrap: break-word;
  z-index: 10000;
  box-shadow: var(--shadow-md);
  pointer-events: none;
  transition: opacity 0.2s ease;
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
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: var(--transition);
  box-shadow: var(--shadow-sm);
}

.action-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.error-btn {
  background-color: rgba(239, 68, 68, 0.1);
  color: var(--error-color);
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.error-btn:hover:not(:disabled) {
  background-color: rgba(239, 68, 68, 0.2);
  border-color: var(--error-color);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.15);
}

.retry-btn {
  background-color: rgba(99, 102, 241, 0.1);
  color: var(--primary-color);
  border: 1px solid rgba(99, 102, 241, 0.2);
}

.retry-btn:hover:not(:disabled) {
  background-color: rgba(99, 102, 241, 0.2);
  border-color: var(--primary-color);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15);
}

.delete-btn {
  background-color: rgba(107, 114, 128, 0.1);
  color: var(--secondary-color);
  border: 1px solid rgba(107, 114, 128, 0.2);
}

.delete-btn:hover:not(:disabled) {
  background-color: rgba(107, 114, 128, 0.2);
  border-color: var(--secondary-color);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(107, 114, 128, 0.15);
}

/* 分页控件 */
.pagination {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px 0;
  gap: 12px;
  margin-top: 16px;
  border-top: 1px solid var(--border-color);
}

.pagination-info {
  font-size: 14px;
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
  padding: 8px 16px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background-color: var(--bg-color);
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: var(--transition);
  box-shadow: var(--shadow-sm);
}

.pagination-btn:hover:not(:disabled) {
  background-color: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.pagination-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.page-size-select {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background-color: var(--bg-color);
  color: var(--text-primary);
  font-size: 14px;
  cursor: pointer;
  transition: var(--transition);
  box-shadow: var(--shadow-sm);
}

.page-size-select:hover {
  border-color: var(--primary-color);
  box-shadow: var(--shadow-md);
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
  padding: 24px;
  border-bottom: 1px solid var(--border-color);
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-hover) 100%);
  border-radius: var(--radius-xl) var(--radius-xl) 0 0;
}

.error-details-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: white;
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
  width: 90%;
  max-width: 900px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
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
  width: 100%;
  max-width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-image img {
  max-width: 100%;
  max-height: 60vh;
  object-fit: contain;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
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
  box-shadow: var(--shadow-lg);
  background-color: black;
}

.preview-info {
  padding: 24px;
  border-top: 1px solid var(--border-color);
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-hover) 100%);
  color: white;
}

.preview-prompt {
  font-size: 16px;
  line-height: 1.6;
  margin-bottom: 16px;
  word-break: break-word;
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