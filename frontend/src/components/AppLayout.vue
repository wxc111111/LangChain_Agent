<template>
  <div class="layout">
    <Sidebar />
    <div class="main">
      <header class="header">
        <span>{{ auth.user?.username }} ({{ auth.user?.role }})</span>
        <button @click="handleLogout">登出</button>
      </header>
      <div class="content">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import Sidebar from './Sidebar.vue'

const router = useRouter()
const auth = useAuthStore()

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.layout {
  display: flex;
}
.main {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.header {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 16px;
  padding: 12px 24px;
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
}
.header button {
  padding: 6px 16px;
  border: 1px solid #d9d9d9;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
}
.content {
  padding: 24px;
  background: #f0f2f5;
  flex: 1;
}
</style>
