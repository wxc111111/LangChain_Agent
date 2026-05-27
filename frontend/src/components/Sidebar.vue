<template>
  <div class="sidebar">
    <div class="logo">Agent智能助手</div>
    <nav>
      <router-link to="/">首页</router-link>
      <router-link to="/agent">AI助手</router-link>
      <router-link v-if="auth.isAdmin" to="/users">用户管理</router-link>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '../stores/auth'
const auth = useAuthStore()
</script>

<style scoped>
.sidebar {
  width: 200px;
  background: #001529;
  color: #fff;
  min-height: 100vh;
  padding-top: 16px;
}
.logo {
  padding: 16px 24px;
  font-size: 18px;
  font-weight: bold;
  border-bottom: 1px solid rgba(255,255,255,0.1);
  margin-bottom: 8px;
}
nav a {
  display: block;
  padding: 12px 24px;
  color: rgba(255,255,255,0.65);
  text-decoration: none;
}
nav a:hover, nav a.router-link-active {
  color: #fff;
  background: rgba(255,255,255,0.08);
}
</style>
