<template>
  <div class="user-create">
    <h3>创建用户</h3>
    <div class="card">
      <form @submit.prevent="handleCreate">
        <div class="form-item">
          <label>用户名</label>
          <input v-model="form.username" required placeholder="请输入用户名" />
        </div>
        <div class="form-item">
          <label>密码</label>
          <input v-model="form.password" type="password" required placeholder="请输入密码" />
        </div>
        <div class="form-item">
          <label>角色</label>
          <select v-model="form.role">
            <option value="user">普通用户</option>
            <option value="admin">管理员</option>
          </select>
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <div class="actions">
          <button type="submit" :disabled="loading">创建</button>
          <router-link to="/users" class="btn-cancel">取消</router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { createUser } from '../../api/users'

const router = useRouter()
const form = ref({ username: '', password: '', role: 'user' })
const error = ref('')
const loading = ref(false)

async function handleCreate() {
  error.value = ''
  loading.value = true
  try {
    await createUser(form.value)
    router.push('/users')
  } catch (e: any) {
    error.value = e.response?.data?.detail || '创建失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
h3 { margin-bottom: 16px; }
.card {
  background: #fff;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  max-width: 480px;
}
.form-item {
  margin-bottom: 16px;
}
.form-item label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
}
.form-item input, .form-item select {
  width: 100%;
  padding: 8px 12px;
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
.actions {
  display: flex;
  gap: 12px;
}
.actions button {
  padding: 8px 24px;
  background: #1677ff;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.btn-cancel {
  padding: 8px 24px;
  border: 1px solid #d9d9d9;
  background: #fff;
  border-radius: 4px;
  text-decoration: none;
  color: #333;
  line-height: 1.6;
}
</style>
