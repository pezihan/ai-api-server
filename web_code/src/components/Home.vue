<script setup lang="ts">
import { ref } from 'vue';
import Navbar from './Navbar.vue';
import GeneratePanel from './GeneratePanel.vue';
import TaskList from './TaskList.vue';

// 控制任务列表侧边栏的显示
const showTaskList = ref(false);
// 任务列表组件引用
const taskListRef = ref<InstanceType<typeof TaskList> | null>(null);

// 切换任务列表显示
const toggleTaskList = () => {
  showTaskList.value = !showTaskList.value;
};

// 处理任务提交成功事件，刷新任务列表
const handleTaskSubmitted = () => {
  if (taskListRef.value) {
    // 如果任务列表已显示，直接刷新
    if (showTaskList.value) {
      taskListRef.value.refreshTasks();
    } else {
      // 如果任务列表未显示，先显示再刷新
      showTaskList.value = true;
      // 延迟刷新，确保组件已挂载
      setTimeout(() => {
        if (taskListRef.value) {
          taskListRef.value.refreshTasks();
        }
      }, 100);
    }
  }
};
</script>

<template>
  <div class="app-container">
    <!-- 左侧任务列表按钮 -->
    <button class="task-list-btn" @click="toggleTaskList">
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
        <polyline points="14 2 14 8 20 8"></polyline>
        <line x1="16" y1="13" x2="8" y2="13"></line>
        <line x1="16" y1="17" x2="8" y2="17"></line>
        <polyline points="10 9 9 9 8 9"></polyline>
      </svg>
      <span>任务列表</span>
    </button>

    <!-- 任务列表侧边栏 -->
    <TaskList v-if="showTaskList" ref="taskListRef" @close="showTaskList = false" />

    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 顶部导航栏 -->
      <Navbar />
      
      <!-- 生成参数面板 -->
      <div class="generate-panel-container">
        <GeneratePanel @task-submitted="handleTaskSubmitted" />
      </div>
      
      <!-- 结果展示区域 -->
      <div class="result-container">
        <!-- 结果将在生成后显示 -->
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 应用容器 */
.app-container {
  display: flex;
  height: 100vh;
  position: relative;
  overflow: hidden;
}

/* 任务列表按钮 */
.task-list-btn {
  position: fixed;
  left: 20px;
  top: 20px;
  z-index: 1000;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-hover) 100%);
  color: white;
  border: none;
  border-radius: var(--radius-lg);
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  box-shadow: var(--shadow-lg);
  transition: var(--transition);
  backdrop-filter: blur(10px);
}

.task-list-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 20px 25px -5px rgba(99, 102, 241, 0.3);
}

/* 主内容区域 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  margin-left: 0;
  transition: margin-left 0.3s ease;
  padding: 24px 0;
}

/* 生成面板容器 */
.generate-panel-container {
  padding: 0 24px;
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
}

/* 结果展示区域 */
.result-container {
  padding: 24px;
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
}
</style>