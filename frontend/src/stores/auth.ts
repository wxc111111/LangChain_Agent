import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, logout as logoutApi, getMe } from '../api/auth'

interface User {
  id: number
  username: string
  role: string
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const isLoggedIn = computed(() => !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function login(username: string, password: string) {
    const resp = await loginApi(username, password)
    localStorage.setItem('access_token', resp.data.access_token)
    localStorage.setItem('refresh_token', resp.data.refresh_token)
    user.value = resp.data.user
  }

  async function fetchUser() {
    try {
      const resp = await getMe()
      user.value = resp.data
    } catch {
      user.value = null
      localStorage.clear()
    }
  }

  async function logout() {
    try {
      await logoutApi()
    } finally {
      user.value = null
      localStorage.clear()
    }
  }

  return { user, isLoggedIn, isAdmin, login, fetchUser, logout }
})
