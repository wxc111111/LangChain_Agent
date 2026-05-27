<template>
  <div class="login-container">
    <form class="login-form" @submit.prevent="handleLogin">
      <h2>登录</h2>
      <div class="form-item">
        <input v-model="username" type="text" placeholder="用户名" required />
      </div>
      <div class="form-item">
        <input v-model="password" type="password" placeholder="密码" required />
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <button type="submit" :disabled="loading">
        {{ loading ? '登录中...' : '登录' }}
      </button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(username.value, password.value)
    router.push('/')
  } catch (e: any) {
    error.value = e.response?.data?.detail || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: #f0f2f5;
}
.login-form {
  background: #fff;
  padding: 40px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
  width: 360px;
}
.login-form h2 {
  text-align: center;
  margin-bottom: 24px;
}
.form-item {
  margin-bottom: 16px;
}
.form-item input {
  width: 100%;
  padding: 10px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
}
.error {
  color: #ff4d4f;
  font-size: 13px;
  margin-bottom: 12px;
}
button {
  width: 100%;
  padding: 10px;
  background: #1677ff;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
}
button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
