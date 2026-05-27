import request from '../utils/request'

export function getUsers(params: { page: number; size: number; search?: string }) {
  return request.get('/api/users', { params })
}

export function getUser(id: number) {
  return request.get(`/api/users/${id}`)
}

export function createUser(data: { username: string; password: string; role: string }) {
  return request.post('/api/users', data)
}
