import axios from 'axios'

const request = axios.create({
  baseURL: 'http://localhost:8002',
  timeout: 10000,
})

let isRefreshing = false
let pendingRequests: Array<(token: string) => void> = []

request.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

request.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      const refreshToken = localStorage.getItem('refresh_token')
      if (!refreshToken) {
        localStorage.clear()
        window.location.href = '/login'
        return Promise.reject(error)
      }

      if (!isRefreshing) {
        isRefreshing = true
        try {
          const resp = await axios.post('http://localhost:8000/api/auth/refresh', {
            refresh_token: refreshToken,
          })
          const newToken = resp.data.access_token
          localStorage.setItem('access_token', newToken)
          pendingRequests.forEach((cb) => cb(newToken))
          pendingRequests = []
          originalRequest.headers.Authorization = `Bearer ${newToken}`
          return request(originalRequest)
        } catch {
          localStorage.clear()
          window.location.href = '/login'
          return Promise.reject(error)
        } finally {
          isRefreshing = false
        }
      } else {
        return new Promise((resolve) => {
          pendingRequests.push((token: string) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            resolve(request(originalRequest))
          })
        })
      }
    }
    return Promise.reject(error)
  },
)

export default request
