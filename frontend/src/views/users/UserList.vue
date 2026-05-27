<template>
  <div class="user-list">
    <div class="toolbar">
      <input v-model="search" placeholder="搜索用户名" @input="onSearch" />
      <router-link to="/users/create" class="btn-primary">创建用户</router-link>
    </div>
    <div class="card">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>用户名</th>
            <th>角色</th>
            <th>状态</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.id }}</td>
            <td>{{ user.username }}</td>
            <td>{{ user.role === 'admin' ? '管理员' : '普通用户' }}</td>
            <td>{{ user.is_active ? '启用' : '禁用' }}</td>
            <td>{{ formatDate(user.created_at) }}</td>
            <td>
              <router-link :to="`/users/${user.id}`">详情</router-link>
            </td>
          </tr>
        </tbody>
      </table>
      <div class="pagination">
        <button :disabled="page <= 1" @click="page--; fetchUsers()">上一页</button>
        <span>第 {{ page }} 页 / 共 {{ Math.ceil(total / size) }} 页</span>
        <button :disabled="page >= Math.ceil(total / size)" @click="page++; fetchUsers()">下一页</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getUsers } from '../../api/users'

interface User {
  id: number
  username: string
  role: string
  is_active: boolean
  created_at: string | null
}

const users = ref<User[]>([])
const total = ref(0)
const page = ref(1)
const size = ref(20)
const search = ref('')
let timer: ReturnType<typeof setTimeout>

function fetchUsers() {
  getUsers({ page: page.value, size: size.value, search: search.value }).then((resp) => {
    users.value = resp.data.items
    total.value = resp.data.total
  })
}

function onSearch() {
  clearTimeout(timer)
  timer = setTimeout(() => {
    page.value = 1
    fetchUsers()
  }, 300)
}

function formatDate(d: string | null) {
  return d ? new Date(d).toLocaleDateString() : '-'
}

onMounted(fetchUsers)
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}
.toolbar input {
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  width: 240px;
}
.btn-primary {
  padding: 8px 20px;
  background: #1677ff;
  color: #fff;
  border-radius: 4px;
  text-decoration: none;
}
.card {
  background: #fff;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
table {
  width: 100%;
  border-collapse: collapse;
}
th, td {
  text-align: left;
  padding: 10px 12px;
  border-bottom: 1px solid #e8e8e8;
}
th {
  background: #fafafa;
}
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 16px;
}
.pagination button {
  padding: 6px 12px;
  border: 1px solid #d9d9d9;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
}
</style>
