<script setup lang="ts">
import { ref } from 'vue';
import Navbar from './components/Navbar.vue';
import GeneratePanel from './components/GeneratePanel.vue';
import TaskList from './components/TaskList.vue';

// 控制任务列表侧边栏的显示
const showTaskList = ref(false);

// 切换任务列表显示
const toggleTaskList = () => {
  showTaskList.value = !showTaskList.value;
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
    <TaskList v-if="showTaskList" @close="showTaskList = false" />

    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 顶部导航栏 -->
      <Navbar />
      
      <!-- 生成参数面板 -->
      <div class="generate-panel-container">
        <GeneratePanel />
      </div>
      
      <!-- 结果展示区域 -->
      <div class="result-container">
        <!-- 结果将在生成后显示 -->
      </div>
    </div>
  </div>
</template>

<style>
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

/* 全局样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  background-color: var(--bg-light);
  color: var(--text-primary);
  line-height: 1.6;
}

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
