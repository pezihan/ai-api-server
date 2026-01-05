<script setup lang="ts">
// 简化后的导航栏组件
</script>

<template>
  <nav class="navbar">
    <div class="navbar-container">
      <h1 class="app-title">AI 生成平台</h1>
    </div>
  </nav>
</template>

<style scoped>
.navbar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 10px 0;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.navbar-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.app-title {
  font-size: 24px;
  font-weight: bold;
  margin: 0;
}
</style>