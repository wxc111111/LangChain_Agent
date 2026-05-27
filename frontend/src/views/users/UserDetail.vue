<template>
  <div class="user-detail">
    <h3>用户详情</h3>
    <div class="card" v-if="user">
      <div class="field"><span class="label">ID:</span> {{ user.id }}</div>
      <div class="field"><span class="label">用户名:</span> {{ user.username }}</div>
      <div class="field"><span class="label">角色:</span> {{ user.role === 'admin' ? '管理员' : '普通用户' }}</div>
      <div class="field"><span class="label">状态:</span> {{ user.is_active ? '启用' : '禁用' }}</div>
      <div class="field"><span class="label">创建时间:</span> {{ formatDate(user.created_at) }}</div>
    </div>
    <p v-else>加载中...</p>
    <router-link to="/users" class="back-link">返回用户列表</router-link>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getUser } from '../../api/users'

const route = useRoute()
const user = ref<any>(null)

onMounted(async () => {
  try {
    const resp = await getUser(Number(route.params.id))
    user.value = resp.data
  } catch {
    user.value = null
  }
})

function formatDate(d: string | null) {
  return d ? new Date(d).toLocaleDateString() : '-'
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
.field {
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
}
.label {
  font-weight: 500;
  margin-right: 8px;
  color: #666;
}
.back-link {
  display: inline-block;
  margin-top: 16px;
  color: #1677ff;
}
</style>
