<template>
  <div class="home">
    <h2>欢迎, {{ auth.user?.username }}</h2>
    <div class="card">
      <p>角色: {{ auth.user?.role === 'admin' ? '管理员' : '普通用户' }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '../stores/auth'
const auth = useAuthStore()
</script>

<style scoped>
.home h2 { margin-bottom: 16px; }
.card {
  background: #fff;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
</style>
