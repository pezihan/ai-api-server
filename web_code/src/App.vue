<script setup lang="ts">
</script>

<template>
  <router-view />
</template>

<style>
:root {
  --primary-color: #509ef3;
  --primary-hover: #2960df;
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

/* 主内容区域 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  margin-left: 0;
  transition: margin-left 0.3s ease;
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
