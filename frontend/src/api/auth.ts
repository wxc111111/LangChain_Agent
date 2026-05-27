import request from '../utils/request'

export function login(username: string, password: string) {
  return request.post('/api/auth/login', { username, password })
}

export function refreshToken(refresh_token: string) {
  return request.post('/api/auth/refresh', { refresh_token })
}

export function logout() {
  return request.post('/api/auth/logout')
}

export function getMe() {
  return request.get('/api/auth/me')
}
