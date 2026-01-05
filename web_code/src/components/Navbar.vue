<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const userInfo = ref<any>(null);
const isLoggedIn = ref(false);

// 初始化登录状态
const initLoginState = () => {
  const token = localStorage.getItem('authToken');
  if (token) {
    isLoggedIn.value = true;
    // 获取用户信息
    const savedUserInfo = localStorage.getItem('userInfo');
    if (savedUserInfo) {
      try {
        userInfo.value = JSON.parse(savedUserInfo);
      } catch (e) {
        console.error('解析用户信息失败:', e);
      }
    }
  }
};

// 登出功能
const handleLogout = () => {
  // 清除本地存储的token和用户信息
  localStorage.removeItem('authToken');
  localStorage.removeItem('userInfo');
  // 更新状态
  isLoggedIn.value = false;
  userInfo.value = null;
  // 重定向到登录页面
  router.push('/login');
};

// 页面加载时初始化登录状态
onMounted(() => {
  initLoginState();
});
</script>

<template>
  <nav class="navbar">
    <div class="navbar-container">
      <h1 class="app-title">AI 生成平台</h1>
      
      <!-- 用户信息和登出按钮 -->
      <div v-if="isLoggedIn" class="user-info">
        <span class="username">用户</span>
        <button class="logout-btn" @click="handleLogout">
          登出
        </button>
      </div>
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
  justify-content: space-between;
}

.app-title {
  font-size: 24px;
  font-weight: bold;
  margin: 0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.username {
  font-size: 16px;
  font-weight: 500;
}

.logout-btn {
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 6px;
  padding: 6px 16px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.logout-btn:hover {
  background-color: rgba(255, 255, 255, 0.3);
}
</style>