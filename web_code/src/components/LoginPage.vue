<script setup lang="ts">
import { ref, reactive } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { post } from '../utils/api';

const router = useRouter();
const route = useRoute();

// 登录表单数据
const loginForm = reactive({
  password: ''
});

// 加载状态
const loading = ref(false);

// 错误信息
const error = ref('');

// 表单验证
const validateForm = (): boolean => {
  if (!loginForm.password) {
    error.value = '请输入密码';
    return false;
  }
  return true;
};

// 登录处理
const handleLogin = async () => {
  // 验证表单
  if (!validateForm()) return;
  
  try {
    loading.value = true;
    error.value = '';
    
    // 调用登录API
    const response = await post('/auth/login', {
      password: loginForm.password
    });
    
    if (response.success && response.data?.token) {
      // 保存token到会话存储
      sessionStorage.setItem('authToken', response.data.token);
      // 跳转回之前的页面或首页
      const redirectPath = route.query.redirect as string || '/';
      router.push(redirectPath);
    } else {
      error.value = response.error || '登录失败，请检查密码';
    }
  } catch (err) {
    error.value = '登录失败，请稍后重试';
    console.error('登录错误:', err);
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="login-container">
    <img src="@/assets/image/login-bak.png" alt="logo" class="login-bak">
    <div class="login-card">
      <div class="login-header">
        <p class="login-subtitle">请登录</p>
      </div>
      
      <form @submit.prevent="handleLogin" class="login-form">
        <!-- 错误信息 -->
        <div v-if="error" class="error-message">
          {{ error }}
        </div>
        
        <!-- 密码输入 -->
        <div class="form-group">
          <label for="password" class="form-label">密码</label>
          <input
            id="password"
            v-model="loginForm.password"
            type="password"
            class="form-input"
            placeholder="请输入密码"
            :disabled="loading"
            autocomplete="current-password"
          />
        </div>
        
        <!-- 登录按钮 -->
        <button
          type="submit"
          class="login-button"
          :disabled="loading"
        >
          <span v-if="loading" class="loading-spinner"></span>
          <span>{{ loading ? '登录中...' : '登录' }}</span>
        </button>
      </form>
      
      <div class="login-footer">
        
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 20px;
  position: relative;
}
.login-bak {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  object-fit: cover;
}

.login-card {
  position: relative;
  z-index: 100;
  background: rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(18px);
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  width: 100%;
  max-width: 500px;
  padding: 40px 30px;
  animation: slideUp 0.5s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.app-title {
  font-size: 28px;
  font-weight: bold;
  background: linear-gradient(135deg, #509ef3 0%, #2960df 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 8px 0;
}

.login-subtitle {
  color: #565656;
  font-size: 18px;
  margin: 0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.error-message {
  background-color: #fee2e2;
  color: #dc2626;
  padding: 12px;
  border-radius: 8px;
  font-size: 14px;
  text-align: center;
  border: 1px solid #fecaca;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.form-input {
  padding: 12px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  font-size: 16px;
  transition: border-color 0.3s ease;
}

.form-input:focus {
  outline: none;
  border-color: #000;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-input:disabled {
  background-color: #f9fafb;
  cursor: not-allowed;
}

.login-button {
  background: #000;
  color: white;
  border: none;
  border-radius: 10px;
  padding: 14px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.login-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
}

.login-button:active:not(:disabled) {
  transform: translateY(0);
}

.login-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.loading-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.login-footer {
  margin-top: 30px;
  text-align: center;
}

.login-footer p {
  color: #9ca3af;
  font-size: 14px;
  margin: 0;
}
</style>